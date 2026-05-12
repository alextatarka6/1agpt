import { useEffect } from "react";
import { X, CheckCircle, AlertCircle } from "lucide-react";

interface Props {
  message: string;
  type: "error" | "success";
  onClose: () => void;
}

export default function Toast({ message, type, onClose }: Props) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);

  return (
    <div
      className={`fixed bottom-6 right-6 flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl text-sm z-50 max-w-sm animate-in ${
        type === "error"
          ? "bg-[#3d1a1a] border border-red-800/50 text-red-300"
          : "bg-[#1a3d2a] border border-green-800/50 text-green-300"
      }`}
    >
      {type === "error" ? (
        <AlertCircle size={16} className="flex-shrink-0" />
      ) : (
        <CheckCircle size={16} className="flex-shrink-0" />
      )}
      <span className="flex-1">{message}</span>
      <button
        onClick={onClose}
        className="flex-shrink-0 text-current opacity-60 hover:opacity-100 transition-opacity"
      >
        <X size={14} />
      </button>
    </div>
  );
}
