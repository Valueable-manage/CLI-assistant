/**
 * 单条消息 - Claude 风格
 */
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message as MessageType } from "../../types";

interface Props {
  message: MessageType;
}

export function Message({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`msg msg--${message.role}`}>
      <div className="msg__avatar">
        {isUser ? "U" : "A"}
      </div>
      <div className="msg__body">
        {isUser ? (
          <span>{message.content}</span>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}
