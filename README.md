# 1agpt

A FastAPI backend + CLI for conversational chat powered by Groq, with retrieval-augmented generation (RAG) over a local lore file.

## How it works

Each message searches the loaded file for relevant entries and injects them into the model's context before generating a response. For structured lore JSON files, retrieval is scored using trigger phrases, people names, aliases, and tags — not just keyword overlap.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

## Running

**Terminal 1 — start the backend:**
```bash
uvicorn main:app --reload
```

**Terminal 2 — start the CLI:**
```bash
python cli.py --file /path/to/lore.json
```

## CLI commands

| Command | Description |
|---|---|
| `/load <path>` | Load a file into the backend |
| `/model <name>` | Switch Groq model |
| `/status` | Show current model, file, and history info |
| `/clear` | Clear conversation history |
| `/help` | Show help |
| `/quit` | Exit |

## Models

Default: `llama-3.3-70b-versatile`

Other free-tier Groq options:
- `llama3-8b-8192` — fastest
- `mixtral-8x7b-32768` — longest context window

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Send a message (streams by default) |
| `POST` | `/load-file` | Load a file by server-side path |
| `POST` | `/upload-file` | Upload a file directly |
| `POST` | `/set-model` | Switch model |
| `GET` | `/history` | Get conversation history |
| `DELETE` | `/history` | Clear conversation history |
| `GET` | `/status` | Show current state |
