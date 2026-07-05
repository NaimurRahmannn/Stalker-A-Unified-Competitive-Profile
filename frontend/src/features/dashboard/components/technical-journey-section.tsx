import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { journeyAccentStyles } from "../styles";
import type { JourneyItem } from "../types";
import { Sparkline } from "./sparkline";

function JourneyCard({ item }: { item: JourneyItem }) {
  const Icon = item.icon;
  const accent = journeyAccentStyles[item.accent];
  const hasSparkline = item.sparkline && item.sparkline.length > 1;
  const actionLabel = item.actionLabel ?? "View Details";
  const actionClass = `mt-4 inline-flex h-9 w-full items-center justify-center gap-2 rounded-xl border text-xs font-semibold transition ${accent.button} ${accent.buttonText}`;

  return (
    <article
      className={`rounded-2xl border bg-white p-4 shadow-[0_16px_38px_rgba(15,23,42,0.045)] ${accent.border}`}
    >
      <div className="flex items-center gap-3">
        <span
          className={`grid size-10 shrink-0 place-items-center rounded-xl ${accent.iconBg} ${accent.icon}`}
        >
          <Icon className="size-5" />
        </span>
        <h3 className="min-w-0 truncate text-sm font-semibold text-slate-950">
          {item.title}
        </h3>
      </div>

      <div className="mt-6">
        <p
          className={`font-semibold leading-tight ${accent.value} ${
            item.isPlaceholder ? "text-xl" : "text-3xl"
          }`}
        >
          {item.value}
        </p>
        <p className="mt-2 text-xs font-medium text-slate-600">{item.label}</p>
        {item.note ? (
          <p className="mt-2 line-clamp-2 text-[11px] font-medium leading-5 text-slate-500">
            {item.note}
          </p>
        ) : null}
      </div>

      {item.stats.length > 0 ? (
        <div className="mt-6 grid grid-cols-2 gap-3">
          {item.stats.map((stat) => (
            <div key={stat.label}>
              <p className="text-base font-semibold leading-none text-slate-950">
                {stat.value}
              </p>
              <p className="mt-1.5 text-[11px] font-medium text-slate-500">
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      ) : null}

      {hasSparkline ? (
        <Sparkline points={item.sparkline ?? []} stroke={accent.stroke} />
      ) : (
        <div className="mt-5 flex h-13 items-center rounded-xl border border-dashed border-slate-200 bg-slate-50/70 px-3 text-[11px] font-medium leading-5 text-slate-500">
          {item.trendLabel ?? "Trend data is not available yet."}
        </div>
      )}

      {item.actionHref && !item.isActionDisabled ? (
        <Link href={item.actionHref} className={actionClass}>
          {actionLabel}
          <ArrowRight className="size-3.5" />
        </Link>
      ) : (
        <button
          type="button"
          disabled={item.isActionDisabled}
          className={`${actionClass} ${
            item.isActionDisabled ? "cursor-not-allowed opacity-70" : ""
          }`}
        >
          {actionLabel}
          <ArrowRight className="size-3.5" />
        </button>
      )}
    </article>
  );
}

export function TechnicalJourneySection({ items }: { items: JourneyItem[] }) {
  return (
    <section className="mt-7">
      <h2 className="text-base font-semibold text-slate-950">
        Your Technical Journey
      </h2>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 min-[1600px]:grid-cols-4">
        {items.map((item) => (
          <JourneyCard key={item.title} item={item} />
        ))}
      </div>
    </section>
  );
}
