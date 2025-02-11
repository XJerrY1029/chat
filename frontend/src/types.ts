export interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: number;
  file?: {
    name: string;
    summary?: string;
  };
}