from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from app.config import settings
from app.routers import chat, files, system
from rag import store

_DEFAULT_LORE = Path(__file__).resolve().parents[2] / "lore.json"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.openai_client = AsyncOpenAI(
        api_key=settings.open_router_api_key,
        base_url=settings.openrouter_base_url,
    )
    if _DEFAULT_LORE.exists():
        store.load(str(_DEFAULT_LORE))
    yield
    await app.state.openai_client.close()


app = FastAPI(
    title="1AGPT — OpenRouter RAG Chat",
    version="2.0.0",
    description="RAG-augmented chat backend powered by OpenRouter.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(files.router)
app.include_router(system.router)
