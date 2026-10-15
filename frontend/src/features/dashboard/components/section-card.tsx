import { ArrowRight } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { dashboardCardSurface } from "../styles";

export function SectionCard({
  title,
  children,
  actionHref,
  actionLabel = "View All",
  showAction = true,
}: {
  title: string;
  children: ReactNode;
  actionHref?: string;
  actionLabel?: string;
  showAction?: boolean;
}) {
  return (
    <section className={`${dashboardCardSurface} p-5`}>
      <div className="flex items-center justify-between gap-4 border-b border-slate-200/70 pb-3">
        <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
        {showAction ? (
          actionHref ? (
            <Link
              href={actionHref}
              className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 transition hover:text-blue-800"
            >
              {actionLabel}
              <ArrowRight className="size-3.5" />
            </Link>
          ) : (
            <button
              type="button"
              className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 transition hover:text-blue-800"
            >
              {actionLabel}
              <ArrowRight className="size-3.5" />
            </button>
          )
        ) : null}
      </div>
      {children}
    </section>
  );
}
