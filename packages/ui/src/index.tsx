import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

const cx = (...parts: Array<string | false | null | undefined>) => parts.filter(Boolean).join(" ");

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "icon";
}

export function Button({ variant = "secondary", size = "md", className, type = "button", ...rest }: ButtonProps) {
  return <button type={type} className={cx("dm-btn", `dm-btn--${variant}`, `dm-btn--${size}`, className)} {...rest} />;
}

export interface PanelProps extends Omit<HTMLAttributes<HTMLElement>, "title"> {
  title?: ReactNode;
  actions?: ReactNode;
}

export function Panel({ title, actions, className, children, ...rest }: PanelProps) {
  return (
    <section className={cx("dm-panel", className)} {...rest}>
      {(title || actions) && (
        <header className="dm-panel__header">
          {title && <h2 className="dm-panel__title">{title}</h2>}
          {actions}
        </header>
      )}
      <div className="dm-panel__body">{children}</div>
    </section>
  );
}

export interface SegmentedOption<T extends string> {
  value: T;
  label: ReactNode;
}

export interface SegmentedControlProps<T extends string> {
  label: string;
  value: T;
  options: SegmentedOption<T>[];
  onChange: (value: T) => void;
}

export function SegmentedControl<T extends string>({ label, value, options, onChange }: SegmentedControlProps<T>) {
  return (
    <div role="radiogroup" aria-label={label} className="dm-segmented">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={o.value === value}
          className={cx("dm-segmented__item", o.value === value && "is-active")}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Toolbar({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div role="toolbar" className={cx("dm-toolbar", className)} {...rest} />;
}

export function Badge({ tone = "neutral", className, ...rest }: HTMLAttributes<HTMLSpanElement> & { tone?: "neutral" | "success" | "warning" }) {
  return <span className={cx("dm-badge", `dm-badge--${tone}`, className)} {...rest} />;
}
