import { useState, useEffect, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import InputBar from "./components/InputBar";
import Toast from "./components/Toast";
import { useChat } from "./hooks/useChat";
import { clearHistory, setModel as setModelApi, getStatus } from "./api/client";
import type { Thread, AppStatus } from "./types";

function loadThreads(): Thread[] {
  try {
    return JSON.parse(localStorage.getItem("1agpt-threads") ?? "[]");
  } catch {
    return [];
  }
}

function saveThreads(threads: Thread[]) {
  localStorage.setItem("1agpt-threads", JSON.stringify(threads));
}

interface ToastState {
  message: string;
  type: "error" | "success";
}

export default function App() {
  const chat = useChat();
  const [threads, setThreads] = useState<Thread[]>(loadThreads);
  const [viewingThread, setViewingThread] = useState<Thread | null>(null);
  const [model, setModel] = useState("deepseek/deepseek-r1-distill-qwen-32b");
  const [status, setStatus] = useState<AppStatus | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [toast, setToast] = useState<ToastState | null>(null);

  // Persist threads whenever they change
  useEffect(() => {
    saveThreads(threads);
  }, [threads]);

  // Fetch backend status on mount
  useEffect(() => {
    getStatus()
      .then((s) => {
        setStatus(s);
        setModel(s.model);
      })
      .catch(() => {});
  }, []);

  // Refresh status after each completed turn
  useEffect(() => {
    if (!chat.isStreaming) {
      getStatus()
        .then(setStatus)
        .catch(() => {});
    }
  }, [chat.isStreaming]);

  const showToast = useCallback((message: string, type: "error" | "success") => {
    setToast({ message, type });
  }, []);

  const persistCurrentChat = useCallback(() => {
    if (chat.messages.length === 0 || viewingThread) return;
    const thread: Thread = {
      id: crypto.randomUUID(),
      title: chat.messages[0].content.slice(0, 60).trim() || "New conversation",
      messages: [...chat.messages],
      createdAt: chat.messages[0].timestamp,
      updatedAt: Date.now(),
    };
    setThreads((prev) => [thread, ...prev]);
  }, [chat.messages, viewingThread]);

  const handleNewChat = useCallback(async () => {
    persistCurrentChat();
    chat.clear();
    setViewingThread(null);
    try {
      await clearHistory();
    } catch {
      showToast("Could not reach backend — history may not be cleared", "error");
    }
  }, [chat, persistCurrentChat, showToast]);

  const handleSelectThread = useCallback(
    (thread: Thread) => {
      persistCurrentChat();
      chat.clear();
      setViewingThread(thread);
    },
    [chat, persistCurrentChat],
  );

  const handleModelChange = useCallback(
    async (newModel: string) => {
      setModel(newModel);
      try {
        await setModelApi(newModel);
      } catch {
        showToast("Failed to update model on backend", "error");
      }
    },
    [showToast],
  );

  const displayMessages = viewingThread ? viewingThread.messages : chat.messages;

  return (
    <div className="flex h-screen overflow-hidden bg-surface text-white font-sans">
      {/* Sidebar */}
      {sidebarOpen && (
        <Sidebar
          threads={threads}
          activeThreadId={null}
          viewingThread={viewingThread}
          model={model}
          status={status}
          onNewChat={handleNewChat}
          onSelectThread={handleSelectThread}
          onDeleteThread={(id) =>
            setThreads((prev) => prev.filter((t) => t.id !== id))
          }
          onModelChange={handleModelChange}
        />
      )}

      {/* Main */}
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        <ChatArea
          messages={displayMessages}
          isStreaming={chat.isStreaming}
          viewingThread={viewingThread}
          status={status}
          onToggleSidebar={() => setSidebarOpen((v) => !v)}
        />
        <InputBar
          onSend={chat.send}
          onStop={chat.stop}
          isStreaming={chat.isStreaming}
          disabled={!!viewingThread}
          onToast={showToast}
        />
      </div>

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
