/**
 * 知识库管理面板 - 支持文件上传和文本粘贴
 */
import { useState, useEffect, useRef } from "react";

const API = "/api/knowledge";
const ACCEPT = ".txt,.md,.csv,.docx,.xlsx,.pdf";

export function KnowledgePanel({ onClose }: { onClose: () => void }) {
  const [text, setText] = useState("");
  const [source, setSource] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [status, setStatus] = useState("");
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadSources = () =>
    fetch(`${API}/sources`).then((r) => r.json()).then((d) => setSources(d.sources));

  useEffect(() => { loadSources(); }, []);

  const handleAddText = async () => {
    if (!text.trim()) return;
    setStatus("正在处理...");
    const res = await fetch(`${API}/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.trim(), source: source.trim() }),
    });
    const data = await res.json();
    setStatus(`已添加，切成了 ${data.chunks} 个片段`);
    setText(""); setSource("");
    loadSources();
  };

  const handleUpload = async (file: File) => {
    setStatus(`正在解析 ${file.name}...`);
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/upload`, { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) { setStatus(`失败：${data.detail}`); return; }
    setStatus(`${file.name} 已添加，切成了 ${data.chunks} 个片段`);
    loadSources();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleUpload(file);
  };

  const handleDelete = async (src: string) => {
    await fetch(`${API}/sources/${encodeURIComponent(src)}`, { method: "DELETE" });
    setSources((prev) => prev.filter((s) => s !== src));
    setStatus("");
  };

  return (
    <div className="kp-overlay" onClick={onClose}>
      <div className="kp-panel" onClick={(e) => e.stopPropagation()}>
        <div className="kp-header">
          <span>知识库管理</span>
          <button className="kp-close" onClick={onClose}>×</button>
        </div>

        {/* 文件上传区 */}
        <div className="kp-section">
          <label className="kp-label">上传文件</label>
          <div
            className={`kp-dropzone ${dragging ? "kp-dropzone--active" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
          >
            <span className="kp-dropzone-icon">📄</span>
            <span>拖拽文件到这里，或点击选择</span>
            <span className="kp-dropzone-hint">支持 TXT · MD · CSV · DOCX · XLSX · PDF</span>
          </div>
          <input ref={fileRef} type="file" accept={ACCEPT} style={{ display: "none" }} onChange={handleFileChange} />
        </div>

        {/* 文本粘贴区 */}
        <div className="kp-section">
          <label className="kp-label">或直接粘贴文本</label>
          <input className="kp-input" placeholder="来源名称（选填）" value={source} onChange={(e) => setSource(e.target.value)} />
          <textarea className="kp-textarea" placeholder="粘贴你的笔记、文章、文档内容..." value={text} onChange={(e) => setText(e.target.value)} rows={6} />
          <button className="kp-btn" onClick={handleAddText} disabled={!text.trim()}>添加到知识库</button>
        </div>

        {status && <div className="kp-section"><p className="kp-status">{status}</p></div>}

        {/* 已有文档 */}
        {sources.length > 0 && (
          <div className="kp-section">
            <label className="kp-label">已有文档（{sources.length} 个）</label>
            <div className="kp-sources">
              {sources.map((s) => (
                <div key={s} className="kp-source-item">
                  <span>{s || "（无来源）"}</span>
                  <button onClick={() => handleDelete(s)}>删除</button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
