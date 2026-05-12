import { useEffect, useRef } from "react";
import { PanelLeftOpen } from "lucide-react";
import Message from "./Message";
import type { Message as MessageType, Thread, AppStatus } from "../types";

interface Props {
  messages: MessageType[];
  isStreaming: boolean;
  viewingThread: Thread | null;
  status: AppStatus | null;
  onToggleSidebar: () => void;
}

export default function ChatArea({
  messages,
  isStreaming,
  viewingThread,
  status,
  onToggleSidebar,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const lastMessageId = messages.at(-1)?.id;

  return (
    <div className="flex flex-col flex-1 overflow-hidden relative">
      {/* Top bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-[#2a2a2a] flex-shrink-0">
        <button
          onClick={onToggleSidebar}
          className="text-gray-500 hover:text-gray-300 transition-colors p-1 -ml-1 rounded"
        >
          <PanelLeftOpen size={18} />
        </button>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          {viewingThread ? (
            <span className="text-gray-300 font-medium truncate max-w-xs">
              {viewingThread.title}
            </span>
          ) : (
            <span className="text-gray-500">
              {status
                ? `${status.model.split("/").pop()} · ${status.history_turns} turns`
                : "1AGPT"}
            </span>
          )}
          {viewingThread && (
            <span className="text-xs bg-[#2f2f2f] text-gray-500 px-2 py-0.5 rounded-full">
              read-only
            </span>
          )}
        </div>
      </div>

      {/* Messages */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-6 px-4">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#19c37d] to-[#0fa868] flex items-center justify-center">
              <span className="text-white font-bold text-lg">1a</span>
            </div>
            <div className="text-center space-y-1">
              <h1 className="text-2xl font-semibold text-white">How can I help you today?</h1>
              <p className="text-sm text-gray-500">
                Powered by OpenRouter · RAG-augmented
              </p>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto w-full py-4 space-y-1">
            {messages.map((msg) => (
              <Message
                key={msg.id}
                message={msg}
                isStreaming={isStreaming && msg.id === lastMessageId && msg.role === "assistant"}
              />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}
