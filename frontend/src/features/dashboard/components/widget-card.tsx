import type { ReactNode } from "react";

export function WidgetCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
      {children}
    </section>
  );
}
