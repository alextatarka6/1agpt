from fastapi import APIRouter

from app.models.schemas import (
    ClearHistoryResponse,
    HistoryMessage,
    HistoryResponse,
    ModelSetRequest,
    ModelSetResponse,
    StatusResponse,
)
from app.state import app_state
from rag import store

router = APIRouter(tags=["system"])


@router.post("/set-model", response_model=ModelSetResponse)
async def set_model(req: ModelSetRequest):
    app_state.model = req.model
    return ModelSetResponse(model=app_state.model)


@router.get("/history", response_model=HistoryResponse)
async def get_history():
    return HistoryResponse(
        history=[HistoryMessage(**msg) for msg in app_state.history],
        turns=len(app_state.history),
    )


@router.delete("/history", response_model=ClearHistoryResponse)
async def clear_history():
    app_state.history.clear()
    return ClearHistoryResponse(cleared=True)


@router.get("/status", response_model=StatusResponse)
async def status():
    return StatusResponse(
        model=app_state.model,
        file_loaded=store.loaded,
        filename=store.filename,
        lore_mode=store.is_lore,
        history_turns=len(app_state.history),
    )
