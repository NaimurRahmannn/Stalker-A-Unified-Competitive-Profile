import type { HTMLAttributes, ReactNode } from "react";

type StatusBadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: "success" | "warning" | "error" | "info" | "neutral";
  children: ReactNode;
};

export function StatusBadge({ tone = "neutral", className = "", children, ...props }: StatusBadgeProps) {
  return <span {...props} className={`ui-badge ui-badge-${tone} ${className}`.trim()}>{children}</span>;
}
