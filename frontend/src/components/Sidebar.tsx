import { MessageSquarePlus, Trash2, ChevronDown } from "lucide-react";
import type { Thread, AppStatus } from "../types";
import { AVAILABLE_MODELS } from "../types";

interface Props {
  threads: Thread[];
  activeThreadId: string | null;
  viewingThread: Thread | null;
  model: string;
  status: AppStatus | null;
  onNewChat: () => void;
  onSelectThread: (thread: Thread) => void;
  onDeleteThread: (id: string) => void;
  onModelChange: (model: string) => void;
}

function timeAgo(ts: number): string {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export default function Sidebar({
  threads,
  viewingThread,
  model,
  status,
  onNewChat,
  onSelectThread,
  onDeleteThread,
  onModelChange,
}: Props) {
  const modelLabel =
    AVAILABLE_MODELS.find((m) => m.id === model)?.label ?? model;

  return (
    <aside className="w-64 flex-shrink-0 bg-sidebar flex flex-col h-full">
      {/* Header */}
      <div className="px-3 pt-3 pb-2">
        <div className="flex items-center gap-2 px-2 py-1.5 mb-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#19c37d] to-[#0fa868] flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-bold">1a</span>
          </div>
          <span className="text-white font-semibold text-sm tracking-tight">1AGPT</span>
        </div>

        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-[#2a2a2a] hover:text-white transition-colors text-sm font-medium"
        >
          <MessageSquarePlus size={16} strokeWidth={1.8} />
          New chat
        </button>
      </div>

      {/* Thread list */}
      <nav className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
        {threads.length === 0 && (
          <p className="text-xs text-gray-600 px-3 py-4 text-center">
            No past conversations yet
          </p>
        )}
        {threads.map((thread) => {
          const isActive = viewingThread?.id === thread.id;
          return (
            <div
              key={thread.id}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm ${
                isActive
                  ? "bg-[#2f2f2f] text-white"
                  : "text-gray-400 hover:bg-[#2a2a2a] hover:text-gray-200"
              }`}
              onClick={() => onSelectThread(thread)}
            >
              <span className="flex-1 truncate leading-snug">{thread.title}</span>
              <span className="text-[10px] text-gray-600 flex-shrink-0 group-hover:hidden">
                {timeAgo(thread.updatedAt)}
              </span>
              <button
                className="hidden group-hover:flex flex-shrink-0 text-gray-500 hover:text-red-400 transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteThread(thread.id);
                }}
              >
                <Trash2 size={13} />
              </button>
            </div>
          );
        })}
      </nav>

      {/* Footer: model selector + status */}
      <div className="px-3 pb-3 border-t border-[#2a2a2a] pt-3 space-y-2">
        {/* Model selector */}
        <div className="relative">
          <select
            value={model}
            onChange={(e) => onModelChange(e.target.value)}
            className="w-full appearance-none bg-[#2a2a2a] text-gray-300 text-xs px-3 py-2 pr-7 rounded-lg border border-[#3d3d3d] focus:outline-none focus:border-[#555] cursor-pointer hover:bg-[#333] transition-colors"
          >
            {AVAILABLE_MODELS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
          <ChevronDown
            size={12}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none"
          />
        </div>

        {/* Status indicators */}
        {status && (
          <div className="px-1 space-y-1">
            <div className="flex items-center gap-2">
              <div
                className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  status.file_loaded ? "bg-green-500" : "bg-gray-600"
                }`}
              />
              <span className="text-[11px] text-gray-500 truncate">
                {status.file_loaded
                  ? `${status.filename}${status.lore_mode ? " · lore" : ""}`
                  : "No file loaded"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0" />
              <span className="text-[11px] text-gray-500 truncate">
                {modelLabel}
              </span>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
