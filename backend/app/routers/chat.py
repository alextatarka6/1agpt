from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

from app.dependencies import get_openai_client
from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm import build_system_prompt, stream_response
from app.state import app_state
from rag import store

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, client: AsyncOpenAI = Depends(get_openai_client)):
    if req.model:
        app_state.model = req.model

    context_chunks = store.retrieve(req.message)
    system_prompt = build_system_prompt(context_chunks)

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend(app_state.history)
    messages.append({"role": "user", "content": req.message})

    app_state.history.append({"role": "user", "content": req.message})

    if req.stream:
        return StreamingResponse(
            stream_response(client, app_state.model, messages, app_state.history, req.show_thinking),
            media_type="text/plain",
        )

    reply = "".join([c async for c in stream_response(client, app_state.model, messages, app_state.history, req.show_thinking)])
    return ChatResponse(reply=reply, context_chunks_used=len(context_chunks))
