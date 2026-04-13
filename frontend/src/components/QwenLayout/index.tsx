/**
 * 主布局 - 侧边栏 + 聊天区
 */
import { useState, useCallback } from "react";
import { Header } from "./Header";
import { QwenChat } from "./QwenChat";
import { Sidebar } from "../Sidebar";

function newSessionId(): string {
  return crypto.randomUUID();
}

export function QwenLayout() {
  const [model, setModel] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>(newSessionId);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleNew = useCallback(() => {
    setSessionId(newSessionId());
    setRefreshKey((k) => k + 1);
  }, []);

  const handleSelect = useCallback((id: string) => {
    setSessionId(id);
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <div className="claude-layout">
      <Sidebar
        currentId={sessionId}
        onSelect={handleSelect}
        onNew={handleNew}
        refreshKey={refreshKey}
      />
      <div className="claude-body">
        <Header model={model} onModelChange={setModel} />
        <main className="claude-main">
          <QwenChat
            key={sessionId}
            sessionId={sessionId}
            model={model}
          />
        </main>
      </div>
    </div>
  );
}
