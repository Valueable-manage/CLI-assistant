/**
 * 左侧会话列表 - Claude 风格
 * 功能：新建对话、删除对话、搜索历史对话
 */
import { useEffect, useState, useRef } from "react";
import { fetchSessions, deleteSession, searchSessions } from "../../api/client";
import type { SessionInfo, SearchResult } from "../../api/client";
import { KnowledgePanel } from "../KnowledgePanel";

interface Props {
  currentId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  refreshKey: number;
}

export function Sidebar({ currentId, onSelect, onNew, refreshKey }: Props) {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [showKnowledge, setShowKnowledge] = useState(false);

  // 搜索状态
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 加载全部会话列表
  useEffect(() => {
    fetchSessions().then(setSessions);
  }, [refreshKey]);

  // 输入变化时防抖搜索（300ms）
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!query.trim()) {
      setSearchResults([]);
      setSearching(false);
      return;
    }

    setSearching(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await searchSessions(query.trim());
        setSearchResults(results);
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
    setSearchResults((prev) => prev.filter((s) => s.id !== id));
    if (id === currentId) onNew();
  };

  // 搜索模式时展示搜索结果，否则展示全部列表
  const isSearching = query.trim().length > 0;
  const displayList: SearchResult[] = isSearching ? searchResults : (sessions as SearchResult[]);

  return (
    <>
      <aside className="sidebar">
        <button className="sidebar__new-btn" onClick={onNew}>
          <span>✦</span> 新对话
        </button>

        {/* 搜索框 */}
        <div className="sidebar__search">
          <input
            className="sidebar__search-input"
            type="text"
            placeholder="搜索历史对话..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button
              className="sidebar__search-clear"
              onClick={() => setQuery("")}
              title="清除搜索"
            >
              ×
            </button>
          )}
        </div>

        {/* 会话列表 */}
        <div className="sidebar__list">
          {isSearching && searching && (
            <div className="sidebar__search-tip">搜索中...</div>
          )}
          {isSearching && !searching && displayList.length === 0 && (
            <div className="sidebar__search-tip">没有找到相关对话</div>
          )}
          {displayList.map((s) => (
            <div
              key={s.id}
              className={`sidebar__item ${s.id === currentId ? "sidebar__item--active" : ""}`}
              onClick={() => { onSelect(s.id); setQuery(""); }}
            >
              <div className="sidebar__item-body">
                <span className="sidebar__item-title">{s.title}</span>
                {"snippet" in s && s.snippet && (
                  <span className="sidebar__item-snippet">{s.snippet}</span>
                )}
              </div>
              <button
                className="sidebar__item-del"
                onClick={(e) => handleDelete(e, s.id)}
                title="删除"
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <button className="sidebar__knowledge-btn" onClick={() => setShowKnowledge(true)}>
          📚 知识库
        </button>
      </aside>
      {showKnowledge && <KnowledgePanel onClose={() => setShowKnowledge(false)} />}
    </>
  );
}
