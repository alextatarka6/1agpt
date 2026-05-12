import { useRef, useState, useEffect, useCallback } from "react";
import { ArrowUp, Square, Paperclip, X } from "lucide-react";
import { uploadFile } from "../api/client";

interface Props {
  onSend: (message: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled: boolean;
  onToast: (msg: string, type: "error" | "success") => void;
}

export default function InputBar({ onSend, onStop, isStreaming, disabled, onToast }: Props) {
  const [value, setValue] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }, [value, isStreaming, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadFile(file);
      setUploadedFile(result.filename);
      onToast(`Loaded "${result.filename}" (${result.chunks} chunks)`, "success");
    } catch (err) {
      onToast((err as Error).message || "Upload failed", "error");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const canSend = value.trim().length > 0 && !isStreaming && !disabled;

  return (
    <div className="flex-shrink-0 bg-[#212121] px-4 pb-4 pt-2">
      <div className="max-w-3xl mx-auto">
        {/* Viewing past thread notice */}
        {disabled && (
          <div className="text-center text-xs text-gray-500 mb-2">
            Viewing a past conversation.{" "}
            <button className="text-gray-400 hover:text-white underline" onClick={() => window.location.reload()}>
              Start a new chat
            </button>{" "}
            to continue.
          </div>
        )}

        {/* Uploaded file badge */}
        {uploadedFile && (
          <div className="flex items-center gap-1.5 mb-2">
            <span className="text-xs bg-[#2f2f2f] text-gray-400 px-2.5 py-1 rounded-full flex items-center gap-1.5">
              <Paperclip size={11} />
              {uploadedFile}
              <button
                onClick={() => setUploadedFile(null)}
                className="text-gray-600 hover:text-gray-300 transition-colors ml-0.5"
              >
                <X size={11} />
              </button>
            </span>
          </div>
        )}

        {/* Input wrapper */}
        <div
          className={`flex items-end gap-2 bg-[#2f2f2f] rounded-2xl px-4 py-3 border transition-colors ${
            disabled
              ? "border-transparent opacity-50 pointer-events-none"
              : "border-transparent focus-within:border-[#555]"
          }`}
        >
          {/* File upload button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading || disabled}
            className="flex-shrink-0 text-gray-500 hover:text-gray-300 transition-colors mb-0.5 disabled:opacity-50"
          >
            {uploading ? (
              <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Paperclip size={18} strokeWidth={1.8} />
            )}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".txt,.md,.json"
            onChange={handleFileChange}
          />

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message 1AGPT"
            rows={1}
            disabled={disabled}
            className="flex-1 bg-transparent text-white text-sm placeholder-gray-500 resize-none outline-none leading-relaxed min-h-[24px] max-h-[200px] py-0.5"
          />

          {/* Send / Stop button */}
          {isStreaming ? (
            <button
              onClick={onStop}
              className="flex-shrink-0 w-8 h-8 bg-white rounded-full flex items-center justify-center hover:bg-gray-200 transition-colors mb-0.5"
            >
              <Square size={12} fill="black" className="text-black" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!canSend}
              className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors mb-0.5 disabled:opacity-30 disabled:cursor-not-allowed bg-white hover:bg-gray-200 disabled:bg-[#555]"
            >
              <ArrowUp size={16} strokeWidth={2.5} className="text-black" />
            </button>
          )}
        </div>

        <p className="text-center text-[11px] text-gray-600 mt-2">
          1AGPT can make mistakes. Check important info.
        </p>
      </div>
    </div>
  );
}
