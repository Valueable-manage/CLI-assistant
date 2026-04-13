/**
 * 前端类型定义
 */

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}
