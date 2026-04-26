#!/usr/bin/env python3
"""
CLI client for the OpenRouter RAG Chat backend.

Usage:
    python cli.py                               # connect to localhost:8000
    python cli.py --host http://localhost:8000
    python cli.py --model deepseek/deepseek-r1-distill-qwen-32b
    python cli.py --file /path/to/doc.txt       # load a file at startup
    python cli.py --thinking                    # show model reasoning

Commands (type during chat):
    /load <path>   load a local file into the backend
    /status        show model, file, history info
    /clear         clear conversation history
    /model <name>  switch model
    /quit          exit
"""

import argparse
import sys

import httpx

DEFAULT_HOST = "http://localhost:8000"


_DIM = "\033[2m\033[3m"
_RESET = "\033[0m"


def _format_thinking(text: str, in_think: bool) -> tuple[str, bool]:
    out = []
    while text:
        if not in_think:
            idx = text.find("<think>")
            if idx == -1:
                out.append(text)
                text = ""
            else:
                out.append(text[:idx])
                out.append(f"\n{_DIM}")
                in_think = True
                text = text[idx + 7:]
        else:
            idx = text.find("</think>")
            if idx == -1:
                out.append(text)
                text = ""
            else:
                out.append(text[:idx])
                out.append(f"{_RESET}\n")
                in_think = False
                text = text[idx + 8:]
    return "".join(out), in_think


def stream_chat(client: httpx.Client, host: str, message: str, show_thinking: bool = False) -> str:
    full = []
    in_think = False
    payload = {"message": message, "stream": True, "show_thinking": show_thinking}
    with client.stream("POST", f"{host}/chat", json=payload, timeout=120) as r:
        r.raise_for_status()
        for chunk in r.iter_text():
            full.append(chunk)
            if show_thinking:
                formatted, in_think = _format_thinking(chunk, in_think)
                print(formatted, end="", flush=True)
            else:
                print(chunk, end="", flush=True)
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
    parser = argparse.ArgumentParser(description="OpenRouter RAG Chat CLI")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Backend URL")
    parser.add_argument("--model", default=None, help="Model name")
    parser.add_argument("--file", default=None, help="File to load at startup")
    parser.add_argument("--thinking", action="store_true", help="Show model reasoning")
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
                stream_chat(client, host, user_input, args.thinking)
            except httpx.HTTPStatusError as e:
                print(f"\n[error] {e.response.status_code}: {e.response.text}")
            except Exception as e:
                print(f"\n[error] {e}")


if __name__ == "__main__":
    main()
