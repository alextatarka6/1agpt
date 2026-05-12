# CLAUDE.md — 1AGPT project context

## Architecture overview

Full-stack RAG chat app with a FastAPI backend and React/TypeScript frontend.

**Backend** (`backend/`) — FastAPI, structured as:
- `app/main.py` — app factory, lifespan, CORS, router mounts
- `app/config.py` — Pydantic `BaseSettings`, reads `backend/.env`
- `app/state.py` — in-memory conversation history + active model
- `app/dependencies.py` — FastAPI `Depends` factories
- `app/models/schemas.py` — Pydantic v2 request/response models
- `app/routers/chat.py` — `POST /chat` (SSE streaming)
- `app/routers/files.py` — `POST /upload-file`, `POST /load-file`
- `app/routers/system.py` — `/status`, `/history`, `/set-model`
- `app/services/llm.py` — prompt assembly + streaming generator
- `rag.py` — RAG store: loads `lore.json` or plain `.txt`/`.md`

**Frontend** (`frontend/`) — Vite + React 18 + TypeScript + Tailwind:
- `src/App.tsx` — root component, layout
- `src/hooks/useChat.ts` — streaming fetch logic, conversation state
- `src/api/client.ts` — typed API wrappers
- `src/components/` — Sidebar, ChatArea, Message, InputBar, Toast

**Legacy** — `main.py` and `rag.py` in root are the original single-file backend; `cli.py` is the original CLI. Keep them; they still work.

## LLM / API

- Provider: [OpenRouter](https://openrouter.ai) (`OPEN_ROUTER_API_KEY` in `backend/.env`)
- Default model: `deepseek/deepseek-r1-distill-qwen-32b`
- Other supported: `openai/gpt-4o`, `anthropic/claude-3.5-sonnet`
- Streaming uses SSE; the frontend reads via `ReadableStream`

## Environment / secrets

- `backend/.env` — holds `OPEN_ROUTER_API_KEY` (and optionally `GROQ_API_KEY`). Never commit this file.
- `frontend/.env.local` — optional, set `VITE_API_URL` to override the default `http://localhost:8000`.

## Running locally

```bash
# backend
cd backend && uvicorn app.main:app --reload

# frontend (separate terminal)
cd frontend && npm run dev
```

Backend OpenAPI: http://localhost:8000/docs  
Frontend: http://localhost:5173

## Key conventions

- Pydantic v2 models throughout (use `model_validate`, not `.parse_*`)
- All streaming responses are SSE — don't switch to websockets without discussion
- RAG context is injected into the system prompt, not appended to messages
- The humor / personality layer lives in `app/services/llm.py` — keep it there
- Dark theme tokens: bg `#212121` / surface `#2f2f2f` / sidebar `#171717`
