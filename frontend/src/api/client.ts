import type { AppStatus } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function sendMessage(
  message: string,
  signal?: AbortSignal,
): Promise<ReadableStreamDefaultReader<Uint8Array>> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, stream: true }),
    signal,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.body!.getReader();
}

export async function clearHistory(): Promise<void> {
  await fetch(`${BASE_URL}/history`, { method: "DELETE" });
}

export async function setModel(model: string): Promise<void> {
  await fetch(`${BASE_URL}/set-model`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model }),
  });
}

export async function getStatus(): Promise<AppStatus> {
  const res = await fetch(`${BASE_URL}/status`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
}

export async function uploadFile(
  file: File,
): Promise<{ filename: string; chunks: number }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/upload-file`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Upload failed: ${text}`);
  }
  return res.json();
}
