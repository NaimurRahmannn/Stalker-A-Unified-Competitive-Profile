import type { ReactNode } from "react";
import { dashboardCardSurface } from "../styles";

export function WidgetCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className={`${dashboardCardSurface} p-5`}>
      <h2 className="border-b border-slate-200/70 pb-3 text-sm font-semibold text-slate-950">{title}</h2>
      {children}
    </section>
  );
}
