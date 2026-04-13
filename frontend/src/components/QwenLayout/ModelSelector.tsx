/**
 * 模型选择器 - 从后端 API 拉取模型列表，单一事实来源
 */
import { useState, useEffect, useRef } from "react";
import { fetchModels, type ModelInfo } from "../../api/client";

type Props = {
  value: string | null;
  onChange: (id: string) => void;
};

export function ModelSelector({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [defaultId, setDefaultId] = useState<string>("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let mounted = true;
    fetchModels()
      .then(({ models: m, default: d }) => {
        if (!mounted) return;
        setModels(m);
        setDefaultId(d);
        if (!value && d) onChange(d);
      })
      .catch(() => {
        if (!mounted) return;
        setModels([{ id: "qwen3.5-plus", name: "Qwen3.5-Plus" }]);
        setDefaultId("qwen3.5-plus");
      });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const currentId = value ?? defaultId;
  const current = models.find((m) => m.id === currentId) ?? models[0];

  return (
    <div className="model-selector" ref={ref}>
      <button
        type="button"
        className="model-selector__trigger"
        onClick={() => setOpen(!open)}
      >
        <span className="model-selector__icon">◆</span>
        <span className="model-selector__name">{current?.name ?? "加载中..."}</span>
        <span className="model-selector__chevron">▼</span>
      </button>
      {open && (
        <div className="model-selector__dropdown">
          {models.map((m) => (
            <div
              key={m.id}
              className="model-selector__item"
              onClick={() => {
                onChange(m.id);
                setOpen(false);
              }}
            >
              {m.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
