/**
 * 聊天 Hook - 流式输出 + 工具状态 + 终止 + 文件上传
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { streamChat, streamResearch, fetchMessages } from "../api/client";
import type { Message } from "../types";
import { useTTS } from "./useSpeech";

function toUiMessages(records: { role: string; content: string }[]): Message[] {
  return records.map((r, i) => ({
    id: `db-${i}`,
    role: r.role as "user" | "assistant",
    content: r.content,
  }));
}

export function useChat(sessionId: string, model?: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [voiceMode, setVoiceMode] = useState(false);     // 语音播报开关
  const [researchMode, setResearchMode] = useState(false); // 深度研究模式
  const abortRef = useRef<AbortController | null>(null);
  const { speak, cancel: cancelTTS, speaking, supported: ttsSupported } = useTTS();

  useEffect(() => {
    setMessages([]);
    setStatus("");
    fetchMessages(sessionId).then((records) => {
      setMessages(toUiMessages(records));
    });
  }, [sessionId]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const sendMessage = useCallback(async (content: string, files?: File[]) => {
    if ((!content.trim() && (!files || files.length === 0)) || loading) return;

    const controller = new AbortController();
    abortRef.current = controller;

    // 用户消息展示：文字 + 文件名列表
    const fileNames = files?.map((f) => f.name) ?? [];
    const displayContent = [
      content,
      fileNames.length ? `📎 ${fileNames.join("、")}` : "",
    ].filter(Boolean).join("\n");

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: displayContent };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setStatus("");

    const assistantMsg: Message = { id: crypto.randomUUID(), role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const onChunk = (chunk: string) => {
        setStatus("");
        setMessages((prev) =>
          prev.map((m) => m.id === assistantMsg.id ? { ...m, content: m.content + chunk } : m)
        );
      };
      const onStatus = (s: string) => setStatus(s);

      if (researchMode) {
        await streamResearch(sessionId, content, onChunk, onStatus, model, controller.signal);
      } else {
        await streamChat(sessionId, content, onChunk, onStatus, model, controller.signal, files);
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        setMessages((prev) =>
          prev.map((m) => m.id === assistantMsg.id && m.content === ""
            ? { ...m, content: "已停止" }
            : m)
        );
      } else {
        setMessages((prev) =>
          prev.map((m) => m.id === assistantMsg.id
            ? { ...m, content: `出错了：${(err as Error).message}` }
            : m)
        );
      }
    } finally {
      setLoading(false);
      setStatus("");
      abortRef.current = null;
    }

    // 语音模式：回复完成后朗读最新 assistant 消息
    if (voiceMode) {
      setMessages((prev) => {
        const last = [...prev].reverse().find((m) => m.role === "assistant");
        if (last?.content) speak(last.content);
        return prev;
      });
    }
  }, [sessionId, model, loading, voiceMode, speak, researchMode]);

  return {
    messages, loading, status, sendMessage, stop,
    voiceMode, setVoiceMode,
    speaking, ttsSupported, cancelTTS,
    researchMode, setResearchMode,
  };
}
