export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface Thread {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

export interface AppStatus {
  model: string;
  file_loaded: boolean;
  filename: string | null;
  lore_mode: boolean;
  history_turns: number;
}

export const AVAILABLE_MODELS = [
  { id: "deepseek/deepseek-r1-distill-qwen-32b", label: "DeepSeek R1" },
  { id: "openai/gpt-4o", label: "GPT-4o" },
  { id: "anthropic/claude-3.5-sonnet", label: "Claude 3.5 Sonnet" },
] as const;
