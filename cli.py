#!/usr/bin/env python3
"""
CLI client for the Groq RAG Chat backend.

Usage:
    python cli.py                               # connect to localhost:8000
    python cli.py --host http://localhost:8000
    python cli.py --model llama-3.3-70b-versatile
    python cli.py --file /path/to/doc.txt       # load a file at startup

Commands (type during chat):
    /load <path>   load a local file into the backend
    /status        show model, file, history info
    /clear         clear conversation history
    /model <name>  switch Groq model
    /quit          exit

Available Groq models (free tier):
    llama-3.3-70b-versatile   (default, best quality)
    llama3-8b-8192            (fastest)
    mixtral-8x7b-32768        (long context)
"""

import argparse
import sys

import httpx

DEFAULT_HOST = "http://localhost:8000"


def stream_chat(client: httpx.Client, host: str, message: str) -> str:
    full = []
    with client.stream("POST", f"{host}/chat", json={"message": message, "stream": True}, timeout=120) as r:
        r.raise_for_status()
        for chunk in r.iter_text():
            print(chunk, end="", flush=True)
            full.append(chunk)
    print()
    return "".join(full)


def load_file(client: httpx.Client, host: str, path: str) -> None:
    r = client.post(f"{host}/load-file", json={"path": path}, timeout=30)
    r.raise_for_status()
    data = r.json()
    print(f"[loaded '{data['filename']}' — {data['chunks']} chunks]")


def print_status(client: httpx.Client, host: str) -> None:
    r = client.get(f"{host}/status", timeout=10)
    r.raise_for_status()
    d = r.json()
    mode = "lore" if d.get("lore_mode") else "text"
    print(
        f"[model={d['model']}  file={d['filename'] or 'none'}  "
        f"mode={mode}  history={d['history_turns']} turns]"
    )


def clear_history(client: httpx.Client, host: str) -> None:
    r = client.delete(f"{host}/history", timeout=10)
    r.raise_for_status()
    print("[history cleared]")


def set_model(client: httpx.Client, host: str, model: str) -> None:
    r = client.post(f"{host}/set-model", json={"model": model}, timeout=10)
    r.raise_for_status()
    print(f"[model set to {model}]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Groq RAG Chat CLI")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Backend URL")
    parser.add_argument("--model", default=None, help="Groq model name")
    parser.add_argument("--file", default=None, help="File to load at startup")
    args = parser.parse_args()

    host = args.host.rstrip("/")

    with httpx.Client() as client:
        try:
            client.get(f"{host}/status", timeout=5).raise_for_status()
        except Exception:
            print(f"[error] Cannot reach backend at {host}. Is it running?", file=sys.stderr)
            sys.exit(1)

        if args.model:
            set_model(client, host, args.model)

        if args.file:
            try:
                load_file(client, host, args.file)
            except Exception as e:
                print(f"[warn] Could not load file: {e}")

        print_status(client, host)
        print("Type /help for commands, /quit to exit.\n")

        while True:
            try:
                user_input = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[bye]")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                parts = user_input.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd in ("/quit", "/exit", "/q"):
                    print("[bye]")
                    break
                elif cmd == "/load":
                    if not arg:
                        print("[usage] /load <path>")
                    else:
                        try:
                            load_file(client, host, arg)
                        except Exception as e:
                            print(f"[error] {e}")
                elif cmd == "/status":
                    print_status(client, host)
                elif cmd == "/clear":
                    clear_history(client, host)
                elif cmd == "/model":
                    if not arg:
                        print("[usage] /model <name>")
                    else:
                        set_model(client, host, arg)
                elif cmd == "/help":
                    print(__doc__)
                else:
                    print(f"[unknown command] {cmd}")
                continue

            print("bot> ", end="", flush=True)
            try:
                stream_chat(client, host, user_input)
            except httpx.HTTPStatusError as e:
                print(f"\n[error] {e.response.status_code}: {e.response.text}")
            except Exception as e:
                print(f"\n[error] {e}")


if __name__ == "__main__":
    main()
