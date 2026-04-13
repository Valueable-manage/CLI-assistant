/**
 * 输入框 - 支持文件附件 + 语音输入
 */
import { useState, useRef, useEffect } from "react";
import { useVoiceInput } from "../../hooks/useSpeech";

const ACCEPT = ".txt,.md,.csv,.docx,.xlsx,.pdf,image/*";

interface Props {
  onSubmit: (content: string, files?: File[]) => void;
  onStop?: () => void;
  loading?: boolean;
  disabled?: boolean;
  placeholder?: string;
  fillValue?: string; // 外部触发填充（来自 Prompt 模板）
}

export function InputBox({ onSubmit, onStop, loading, disabled, placeholder = "给个人助手发消息", fillValue }: Props) {
  const [value, setValue] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // 语音识别：识别完成后追加到输入框
  const { listening, supported: voiceSupported, start: startVoice, stop: stopVoice } = useVoiceInput(
    (text) => setValue((prev) => (prev ? prev + " " + text : text))
  );

  // 当外部传入 fillValue 时，填充到输入框并聚焦
  useEffect(() => {
    if (fillValue !== undefined && fillValue !== "") {
      setValue(fillValue);
      textareaRef.current?.focus();
    }
  }, [fillValue]);

  // 自动调整高度
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  }, [value]);

  const handleSubmit = () => {
    if ((!value.trim() && files.length === 0) || disabled) return;
    onSubmit(value.trim(), files.length > 0 ? files : undefined);
    setValue("");
    setFiles([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? []);
    setFiles((prev) => [...prev, ...selected]);
    e.target.value = "";
  };

  const removeFile = (idx: number) =>
    setFiles((prev) => prev.filter((_, i) => i !== idx));

  const isImage = (f: File) => f.type.startsWith("image/");

  return (
    <div className="input-box">
      {/* 文件预览区 */}
      {files.length > 0 && (
        <div className="input-box__files">
          {files.map((f, i) => (
            <div key={i} className="input-box__file-tag">
              {isImage(f) ? (
                <img src={URL.createObjectURL(f)} alt={f.name} className="input-box__file-thumb" />
              ) : (
                <span className="input-box__file-icon">📄</span>
              )}
              <span className="input-box__file-name">{f.name}</span>
              <button className="input-box__file-rm" onClick={() => removeFile(i)}>×</button>
            </div>
          ))}
        </div>
      )}

      <div className="input-box__row">
        {/* 附件按钮 */}
        <button
          className="input-box__attach"
          onClick={() => fileRef.current?.click()}
          disabled={disabled}
          title="添加附件"
          type="button"
        >
          +
        </button>
        <input
          ref={fileRef}
          type="file"
          accept={ACCEPT}
          multiple
          style={{ display: "none" }}
          onChange={handleFileChange}
        />

        {/* 文字输入 */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="input-box__input"
        />

        {/* 麦克风按钮（浏览器支持时才显示） */}
        {voiceSupported && (
          <button
            className={`input-box__mic${listening ? " input-box__mic--active" : ""}`}
            onClick={listening ? stopVoice : startVoice}
            disabled={disabled || loading}
            title={listening ? "点击结束录音" : "点击开始录音"}
            type="button"
          >
            {listening ? "🔴" : "🎤"}
          </button>
        )}

        {/* 发送/终止按钮 */}
        <button
          onClick={loading ? onStop : handleSubmit}
          disabled={!loading && (disabled || (!value.trim() && files.length === 0))}
          className={`input-box__btn${loading ? " input-box__btn--stop" : ""}`}
          type="button"
          title={loading ? "停止生成" : "发送"}
        >
          {loading ? "■" : "↑"}
        </button>
      </div>
    </div>
  );
}
