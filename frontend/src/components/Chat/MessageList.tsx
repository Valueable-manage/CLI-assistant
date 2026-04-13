/**
 * 消息列表 - 展示对话历史
 */
import { Message } from "./Message";
import type { Message as MessageType } from "../../types";

interface Props {
  messages: MessageType[];
}

export function MessageList({ messages }: Props) {
  return (
    <div className="message-list">
      {messages.map((msg) => (
        <Message key={msg.id} message={msg} />
      ))}
    </div>
  );
}
