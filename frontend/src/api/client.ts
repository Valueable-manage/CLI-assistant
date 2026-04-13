/**
 * API 客户端 - 对接 FastAPI
 */
const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export type ModelInfo = { id: string; name: string };
export type MessageRecord = { role: "user" | "assistant"; content: string };
export type SessionInfo = { id: string; title: string; updated_at: string };

export async function fetchModels(): Promise<{ models: ModelInfo[]; default: string }> {
  const res = await fetch(`${API_BASE}/models`);
  if (!res.ok) throw new Error(`服务器错误: ${res.status}`);
  return res.json();
}

export async function fetchSessions(): Promise<SessionInfo[]> {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) throw new Error(`服务器错误: ${res.status}`);
  const data = await res.json();
  return data.sessions;
}

export async function fetchMessages(sessionId: string): Promise<MessageRecord[]> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error(`服务器错误: ${res.status}`);
  const data = await res.json();
  return data.messages;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/sessions/${sessionId}`, { method: "DELETE" });
}

export type SearchResult = SessionInfo & { snippet?: string };

export async function searchSessions(q: string): Promise<SearchResult[]> {
  const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
  if (!res.ok) throw new Error(`服务器错误: ${res.status}`);
  const data = await res.json();
  return data.sessions;
}

export async function streamResearch(
  sessionId: string,
  message: string,
  onChunk: (chunk: string) => void,
  onStatus: (status: string) => void,
  model?: string | null,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, model: model ?? undefined }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `服务器错误: ${res.status}`);
  }
  if (!res.body) throw new Error("无响应内容");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const ev = JSON.parse(line);
        if (ev.t === "chunk") onChunk(ev.v);
        else if (ev.t === "status") onStatus(ev.v);
      } catch { /* 忽略 */ }
    }
  }
}

export async function streamChat(
  sessionId: string,
  message: string,
  onChunk: (chunk: string) => void,
  onStatus: (status: string) => void,
  model?: string | null,
  signal?: AbortSignal,
  files?: File[],
): Promise<void> {
  let res: Response;

  if (files && files.length > 0) {
    const form = new FormData();
    form.append("session_id", sessionId);
    form.append("message", message ?? "");
    if (model) form.append("model", model);
    files.forEach((f) => form.append("files", f));
    res = await fetch(`${API_BASE}/chat/with-files`, { method: "POST", body: form, signal });
  } else {
    res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message, model: model ?? undefined }),
      signal,
    });
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `服务器错误: ${res.status}`);
  }
  if (!res.body) throw new Error("无响应内容");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    // 按行解析 NDJSON
    const lines = buf.split("\n");
    buf = lines.pop() ?? "";           // 最后一行可能不完整，留到下次
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const ev = JSON.parse(line);
        if (ev.t === "chunk") onChunk(ev.v);
        else if (ev.t === "status") onStatus(ev.v);
      } catch { /* 忽略解析失败的行 */ }
    }
  }
}
