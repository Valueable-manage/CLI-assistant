/**
 * Prompt 快捷模板 — 显示在输入框上方，点击自动填充输入框
 */

interface Template {
  label: string;
  prompt: string;
}

const TEMPLATES: Template[] = [
  { label: "📝 帮我总结", prompt: "请帮我总结以下内容：\n\n" },
  { label: "🌐 翻译成英文", prompt: "请将以下内容翻译成英文：\n\n" },
  { label: "🐍 写 Python 脚本", prompt: "请帮我写一个 Python 脚本，功能是：" },
  { label: "🔍 解释代码", prompt: "请解释以下代码的作用和原理：\n\n```\n\n```" },
  { label: "🐛 帮我 Debug", prompt: "我遇到了一个报错，请帮我分析原因和解决方法：\n\n错误信息：\n" },
  { label: "💡 头脑风暴", prompt: "请帮我头脑风暴以下主题的思路和方案：\n\n" },
];

interface Props {
  onSelect: (prompt: string) => void;
}

export function PromptTemplates({ onSelect }: Props) {
  return (
    <div className="prompt-templates">
      {TEMPLATES.map((t) => (
        <button
          key={t.label}
          className="prompt-templates__btn"
          onClick={() => onSelect(t.prompt)}
          type="button"
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
