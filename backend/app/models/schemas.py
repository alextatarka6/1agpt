from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    model: str | None = None
    stream: bool = True
    show_thinking: bool = False


class ChatResponse(BaseModel):
    reply: str
    context_chunks_used: int


class FileLoadRequest(BaseModel):
    path: str


class FileLoadResponse(BaseModel):
    filename: str
    chunks: int


class ModelSetRequest(BaseModel):
    model: str


class ModelSetResponse(BaseModel):
    model: str


class HistoryMessage(BaseModel):
    role: str
    content: str


class HistoryResponse(BaseModel):
    history: list[HistoryMessage]
    turns: int


class StatusResponse(BaseModel):
    model: str
    file_loaded: bool
    filename: str | None
    lore_mode: bool
    history_turns: int


class ClearHistoryResponse(BaseModel):
    cleared: bool


class UploadFileResponse(BaseModel):
    filename: str
    chunks: int
