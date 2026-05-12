from __future__ import annotations

import re
from typing import AsyncGenerator, cast


def _build_bpe_decoder() -> dict[str, int]:
    bs = (
        list(range(ord("!"), ord("~") + 1))
        + list(range(ord("¡"), ord("¬") + 1))
        + list(range(ord("®"), ord("ÿ") + 1))
    )
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return {chr(c): b for b, c in zip(bs, cs)}


_BPE_DECODER = _build_bpe_decoder()
_BPE_SPECIAL = frozenset(chr(c) for c in range(256, 324))


def _decode_bpe(text: str) -> str:
    """Convert GPT-2/Qwen BPE token chars (Ġ→space, Ċ→newline, …) back to UTF-8."""
    if not any(c in _BPE_SPECIAL for c in text):
        return text
    try:
        return bytes([_BPE_DECODER[c] for c in text]).decode("utf-8", errors="replace")
    except KeyError:
        return text

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

_HUMOR_BLOCK = """\
Read the context and conversation tone before responding — then choose your humor style.

Styles available:
- Dry wit: understate the obvious, deliver observations flatly, let the reader connect the dots
- Absurdist: follow the logic of a situation to a ridiculous conclusion, commit to the bit fully
- Roast: affectionate but pointed, punch at the person or their choices — never at bystanders

How to pick:
- Technical topic or understated situation → dry wit
- Philosophical tangent, weird premise, or nonsensical request → absurdist
- Someone describing their own achievement, opinion, or clearly inviting it → roast
- Mixed signals → layer or blend styles

Rules:
- Never announce which style you're using. Just use it.
- Be funny first, helpful second.
- Never invent, assume, or infer facts about specific people not described in the context.
- Never mention the context, file, or any external information source.
- Never preface your response by explaining what you are about to do.
- Spell everything correctly and naturally. The context entries may have typos, odd casing, or shorthand — ignore that and write normally.
- Never combine words. Always put a space between each word.\
"""


def build_system_prompt(context_chunks: list[str]) -> str:
    if not context_chunks:
        return f"You are a witty assistant.\n\n{_HUMOR_BLOCK}"
    context_text = "\n\n---\n\n".join(context_chunks)
    return (
        "You are a witty assistant. Use ONLY the following context when answering questions "
        "about people — do not supplement it with anything from your training data about "
        f"specific individuals.\n\n{_HUMOR_BLOCK}\n\nContext:\n{context_text}"
    )


def _strip_thinking(text: str) -> tuple[str, str]:
    """Remove completed <think>…</think> blocks; hold back any open one."""
    text = _THINK_RE.sub("", text)
    idx = text.find("<think>")
    if idx != -1:
        return text[:idx].lstrip(), text[idx:]
    return text.lstrip(), ""


async def stream_response(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict],
    history: list[dict[str, str]],
    show_thinking: bool = False,
) -> AsyncGenerator[str, None]:
    full_response: list[str] = []
    leftover = ""

    stream: AsyncStream[ChatCompletionChunk] = await client.chat.completions.create(
        model=model,
        messages=cast(list[ChatCompletionMessageParam], messages),
        stream=True,
    )

    async for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        if not token:
            continue
        if show_thinking:
            decoded = _decode_bpe(token)
            full_response.append(decoded)
            yield decoded
        else:
            leftover += token
            clean, leftover = _strip_thinking(leftover)
            if clean:
                decoded = _decode_bpe(clean)
                full_response.append(decoded)
                yield decoded

    if not show_thinking and leftover and not leftover.lstrip().startswith("<think>"):
        decoded = _decode_bpe(leftover)
        full_response.append(decoded)
        yield decoded

    history.append({"role": "assistant", "content": "".join(full_response)})
