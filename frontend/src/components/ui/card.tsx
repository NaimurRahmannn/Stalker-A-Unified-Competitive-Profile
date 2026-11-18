import type { HTMLAttributes, ReactNode } from "react";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  variant?: "default" | "subtle" | "elevated" | "interactive";
  children: ReactNode;
};

export function Card({ variant = "default", className = "", children, ...props }: CardProps) {
  return <div {...props} className={`ui-card ${variant === "default" ? "" : `ui-card-${variant}`} ${className}`.trim()}>{children}</div>;
}
