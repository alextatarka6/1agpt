# 1AGPT

RAG-augmented chat powered by OpenRouter (DeepSeek R1 / GPT-4o / Claude), with a ChatGPT-inspired React frontend.

## Project structure

```
1agpt/
├── backend/               ← FastAPI backend
│   ├── app/
│   │   ├── main.py        ← FastAPI app (lifespan, CORS, routers)
│   │   ├── config.py      ← Pydantic settings (reads .env)
│   │   ├── state.py       ← In-memory state (history, model)
│   │   ├── dependencies.py← Depends factories
│   │   ├── models/schemas.py  ← Pydantic v2 request/response models
│   │   ├── routers/
│   │   │   ├── chat.py    ← POST /chat (streaming)
│   │   │   ├── files.py   ← POST /load-file, POST /upload-file
│   │   │   └── system.py  ← /status, /history, /set-model
│   │   └── services/llm.py← Prompt building + streaming generator
│   ├── rag.py             ← RAG store (lore + plain text)
│   ├── .env               ← API keys (not committed)
│   └── requirements.txt
├── frontend/              ← React + TypeScript + Tailwind
│   ├── src/
│   │   ├── App.tsx
│   │   ├── types.ts
│   │   ├── api/client.ts
│   │   ├── hooks/useChat.ts
│   │   └── components/
│   │       ├── Sidebar.tsx
│   │       ├── ChatArea.tsx
│   │       ├── Message.tsx
│   │       ├── InputBar.tsx
│   │       └── Toast.tsx
│   ├── vite.config.ts
│   └── package.json
├── main.py                ← Original single-file backend (preserved)
└── rag.py
```

## Prerequisites

- Python 3.11+
- Node.js 18+ (v22 recommended — use `nvm use 22` if you have nvm)
- An [OpenRouter](https://openrouter.ai) API key

## Setup

### 1. Environment

Create `backend/.env`:

```
OPEN_ROUTER_API_KEY=sk-or-v1-...
```

The frontend proxies to `http://localhost:8000` by default. Override by setting `VITE_API_URL` in `frontend/.env.local` if needed.

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

OpenAPI docs: **http://localhost:8000/docs**

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Stream or non-stream RAG-augmented chat |
| `POST` | `/upload-file` | Upload a `.txt`, `.md`, or `.json` lore file |
| `POST` | `/load-file` | Load a file from the server filesystem |
| `POST` | `/set-model` | Switch the active LLM model |
| `GET`  | `/history` | Get conversation history |
| `DELETE` | `/history` | Clear conversation history |
| `GET`  | `/status` | Model, file, and history status |

## Available models (via OpenRouter)

| Label | Model ID |
|-------|----------|
| DeepSeek R1 | `deepseek/deepseek-r1-distill-qwen-32b` |
| GPT-4o | `openai/gpt-4o` |
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` |

## Frontend features

- **Streaming responses** via `ReadableStream` — tokens appear as they arrive
- **Markdown rendering** with syntax-highlighted code blocks (One Dark theme)
- **Conversation threads** persisted in `localStorage`
- **File upload** via paperclip for RAG context injection
- **Model switcher** in the sidebar
- **Stop generation** button mid-stream
- **Dark theme** matching ChatGPT's palette (#212121 / #2f2f2f / #171717)

## CLI (original)

The original CLI still works against the old `main.py`:

```bash
uvicorn main:app --reload   # terminal 1
python cli.py --file lore.json  # terminal 2
```
