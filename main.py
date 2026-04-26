from __future__ import annotations

import os
import re
from typing import AsyncGenerator, cast

from dotenv import load_dotenv
load_dotenv()

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag import store

app = FastAPI(title="OpenRouter RAG Chat")

_client = AsyncOpenAI(
    api_key=os.environ["OPEN_ROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)
_history: list[dict[str, str]] = []
_model: str = "deepseek/deepseek-r1-distill-qwen-32b"

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


# ── models ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    model: str | None = None
    stream: bool = True
    show_thinking: bool = False


class FileLoadRequest(BaseModel):
    path: str


class ModelSetRequest(BaseModel):
    model: str


# ── helpers ───────────────────────────────────────────────────────────────────

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


def _build_system_prompt(context_chunks: list[str]) -> str:
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


async def _stream(messages: list[dict], show_thinking: bool = False) -> AsyncGenerator[str, None]:
    full_response: list[str] = []
    leftover = ""

    stream: AsyncStream[ChatCompletionChunk] = await _client.chat.completions.create(
        model=_model,
        messages=cast(list[ChatCompletionMessageParam], messages),
        stream=True,
    )

    async for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        if not token:
            continue
        if show_thinking:
            full_response.append(token)
            yield token
        else:
            leftover += token
            clean, leftover = _strip_thinking(leftover)
            if clean:
                full_response.append(clean)
                yield clean

    if not show_thinking and leftover and not leftover.lstrip().startswith("<think>"):
        full_response.append(leftover)
        yield leftover

    _history.append({"role": "assistant", "content": "".join(full_response)})


# ── routes ────────────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat(req: ChatRequest):
    global _model
    if req.model:
        _model = req.model

    context_chunks = store.retrieve(req.message)
    system_prompt = _build_system_prompt(context_chunks)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(_history)
    messages.append({"role": "user", "content": req.message})

    _history.append({"role": "user", "content": req.message})

    if req.stream:
        return StreamingResponse(_stream(messages, req.show_thinking), media_type="text/plain")

    reply = "".join([c async for c in _stream(messages, req.show_thinking)])
    return {"reply": reply, "context_chunks_used": len(context_chunks)}


@app.post("/load-file")
async def load_file(req: FileLoadRequest):
    try:
        chunks = store.load(req.path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {req.path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"filename": store.filename, "chunks": chunks}


@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="replace")
    chunks = store.load_text(file.filename or "upload", content)
    return {"filename": store.filename, "chunks": chunks}


@app.post("/set-model")
async def set_model(req: ModelSetRequest):
    global _model
    _model = req.model
    return {"model": _model}


@app.get("/history")
async def get_history():
    return {"history": _history, "turns": len(_history)}


@app.delete("/history")
async def clear_history():
    _history.clear()
    return {"cleared": True}


@app.get("/status")
async def status():
    return {
        "model": _model,
        "file_loaded": store.loaded,
        "filename": store.filename,
        "lore_mode": store.is_lore,
        "history_turns": len(_history),
    }
