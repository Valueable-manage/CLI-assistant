/**
 * Claude 风格聊天区
 * 功能：流式对话 + Prompt 模板快捷填充 + 对话导出 Markdown
 */
import { useEffect, useRef, useState, useCallback } from "react";
import { MessageList } from "../Chat/MessageList";
import { InputBox } from "../Chat/InputBox";
import { PromptTemplates } from "../Chat/PromptTemplates";
import { useChat } from "../../hooks/useChat";
import type { Message } from "../../types";

type Props = { sessionId: string; model?: string | null };

/** 将 messages 数组转为 Markdown 字符串 */
function exportToMarkdown(messages: Message[]): string {
  const lines: string[] = [`# 对话导出\n`, `> 导出时间：${new Date().toLocaleString("zh-CN")}\n`];
  for (const msg of messages) {
    const role = msg.role === "user" ? "**用户**" : "**助手**";
    lines.push(`\n---\n\n${role}\n\n${msg.content}`);
  }
  return lines.join("\n");
}

/** 触发浏览器下载文件 */
function downloadFile(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function QwenChat({ sessionId, model }: Props) {
  const {
    messages, loading, status, sendMessage, stop,
    voiceMode, setVoiceMode, speaking, ttsSupported, cancelTTS,
    researchMode, setResearchMode,
  } = useChat(sessionId, model);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [fillValue, setFillValue] = useState("");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  // 模板点击 → 填充 InputBox
  // 用时间戳作为 key 确保同一模板连续点击也能触发 useEffect
  const handleTemplateSelect = useCallback((prompt: string) => {
    setFillValue(prompt + "\u200b"); // 零宽字符保证每次都是新值
    // 再下一帧还原，避免 fillValue 停留导致重复触发
    setTimeout(() => setFillValue(prompt), 0);
  }, []);

  // 导出当前对话为 Markdown
  const handleExport = useCallback(() => {
    if (messages.length === 0) return;
    const md = exportToMarkdown(messages);
    const filename = `对话_${new Date().toISOString().slice(0, 10)}.md`;
    downloadFile(md, filename);
  }, [messages]);

  return (
    <div className="claude-chat">
      <div className="claude-chat__messages">
        {messages.length === 0 ? (
          <div className="claude-chat__welcome">
            <span className="claude-chat__welcome-icon">✦</span>
            <p>有什么我可以帮你的？</p>
          </div>
        ) : (
          <MessageList messages={messages} />
        )}
        {status && (
          <div className="agent-status">
            <span className="agent-status__dot" />
            {status}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="claude-chat__input">
        {/* 工具栏：始终显示，导出按钮在有消息时才可用 */}
        <div className="claude-chat__toolbar">
          {messages.length > 0 && (
            <button
              className="export-btn"
              onClick={handleExport}
              title="导出对话为 Markdown"
              type="button"
            >
              ↓ 导出对话
            </button>
          )}

          {/* 深度研究模式开关 - 始终显示 */}
          <button
            className={`research-mode-btn${researchMode ? " research-mode-btn--on" : ""}`}
            onClick={() => setResearchMode((v) => !v)}
            title={researchMode ? "关闭深度研究模式" : "开启深度研究模式（多Agent并行搜索）"}
            type="button"
          >
            {researchMode ? "🔬 研究模式" : "🔍 普通模式"}
          </button>

          {ttsSupported && (
            <>
              <button
                className={`voice-mode-btn${voiceMode ? " voice-mode-btn--on" : ""}`}
                onClick={() => { setVoiceMode((v) => !v); if (speaking) cancelTTS(); }}
                title={voiceMode ? "关闭语音播报" : "开启语音播报"}
                type="button"
              >
                {voiceMode ? "🔊 语音开" : "🔇 语音关"}
              </button>
              {speaking && (
                <button
                  className="voice-stop-btn"
                  onClick={cancelTTS}
                  title="停止朗读"
                  type="button"
                >
                  ⏹ 停止朗读
                </button>
              )}
            </>
          )}
        </div>

        {/* 无消息时显示 Prompt 模板 */}
        {messages.length === 0 && (
          <PromptTemplates onSelect={handleTemplateSelect} />
        )}

        <InputBox
          onSubmit={sendMessage}
          onStop={stop}
          loading={loading}
          placeholder="给个人助手发消息"
          fillValue={fillValue}
        />
      </div>
    </div>
  );
}
