from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator, cast

from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from groq.types.chat import ChatCompletionMessageParam
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag import store

app = FastAPI(title="Groq RAG Chat")

_client = Groq(api_key=os.environ["GROQ_API_KEY"])
_history: list[dict[str, str]] = []
_model: str = "llama-3.3-70b-versatile"


# ── models ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    model: str | None = None
    stream: bool = True


class FileLoadRequest(BaseModel):
    path: str


class ModelSetRequest(BaseModel):
    model: str


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_system_prompt(context_chunks: list[str]) -> str:
    people_rule = (
        "Never invent, assume, or infer facts about any specific person. "
        "If you do not have explicit information about someone, say you don't know rather than guessing."
    )
    if not context_chunks:
        return (
            f"You are a helpful assistant. {people_rule} "
            "Answer directly without prefacing or explaining your response."
        )
    context_text = "\n\n---\n\n".join(context_chunks)
    return (
        "You are a helpful assistant. Use ONLY the following context when answering questions about people — "
        "do not supplement it with anything from your training data about specific individuals. "
        f"{people_rule} "
        "Never mention the context, the file, or that you are using any external information. "
        "Never preface your response by explaining what you are about to do. Just answer directly.\n\n"
        f"{context_text}"
    )


async def _stream_groq(messages: list[dict]) -> AsyncGenerator[str, None]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    full_response: list[str] = []

    def _producer() -> None:
        stream = _client.chat.completions.create(
            model=_model,
            messages=cast(list[ChatCompletionMessageParam], messages),
            stream=True,
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                loop.call_soon_threadsafe(queue.put_nowait, token)
        loop.call_soon_threadsafe(queue.put_nowait, None)

    loop.run_in_executor(None, _producer)

    while True:
        token = await queue.get()
        if token is None:
            break
        full_response.append(token)
        yield token

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
        return StreamingResponse(
            _stream_groq(messages),
            media_type="text/plain",
        )

    response = _client.chat.completions.create(
        model=_model,
        messages=cast(list[ChatCompletionMessageParam], messages),
    )
    reply = response.choices[0].message.content or ""
    _history.append({"role": "assistant", "content": reply})
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
