from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.schemas import FileLoadRequest, FileLoadResponse, UploadFileResponse
from rag import store

router = APIRouter(tags=["files"])


@router.post("/load-file", response_model=FileLoadResponse)
async def load_file(req: FileLoadRequest):
    try:
        chunks = store.load(req.path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {req.path}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return FileLoadResponse(filename=store.filename, chunks=chunks)


@router.post("/upload-file", response_model=UploadFileResponse, status_code=201)
async def upload_file(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="replace")
    chunks = store.load_text(file.filename or "upload", content)
    return UploadFileResponse(filename=store.filename, chunks=chunks)
