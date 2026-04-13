/**
 * 顶部栏 - Claude 风格
 */
import { ModelSelector } from "./ModelSelector";

type Props = {
  model: string | null;
  onModelChange: (id: string) => void;
};

export function Header({ model, onModelChange }: Props) {
  return (
    <header className="claude-header">
      <div className="claude-header__left">
        <span className="claude-header__logo">✦</span>
        <span className="claude-header__title">个人助手</span>
      </div>
      <div className="claude-header__right">
        <ModelSelector value={model} onChange={onModelChange} />
      </div>
    </header>
  );
}
