import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { formatDashboardPlatformName, platformLogoSrc } from "../data";
import { journeyAccentStyles } from "../styles";
import type { JourneyItem } from "../types";
import { Sparkline } from "./sparkline";

function PlatformBadges({ item }: { item: JourneyItem }) {
  if (!item.platformMarks?.length) {
    return <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[9px] font-semibold uppercase tracking-[0.1em] text-slate-500 shadow-sm">Planned</span>;
  }

  return (
    <div className="flex items-center gap-1.5" aria-label="Supported platforms">
      {item.platformMarks.map((mark) => (
        <span key={mark} title={formatDashboardPlatformName(mark)} className="grid size-8 place-items-center rounded-lg border border-slate-200 bg-white shadow-[0_3px_9px_rgba(15,23,42,0.08)] transition duration-300 group-hover:-translate-y-0.5">
          <Image src={platformLogoSrc[mark]} alt={`${formatDashboardPlatformName(mark)} logo`} width={23} height={23} className="size-5.5 object-contain" />
        </span>
      ))}
    </div>
  );
}

function JourneyCard({ item }: { item: JourneyItem }) {
  const Icon = item.icon;
  const accent = journeyAccentStyles[item.accent];
  const hasSparkline = item.sparkline && item.sparkline.length > 1;
  const actionLabel = item.actionLabel ?? "View Details";
  const actionClass = `inline-flex h-10 w-full items-center justify-center gap-2 rounded-xl border text-xs font-semibold shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-md ${accent.button} ${accent.buttonText}`;

  return (
    <article className="group relative flex h-full min-h-96 flex-col overflow-hidden rounded-[22px] border border-slate-200/80 bg-[linear-gradient(155deg,#ffffff_0%,#f8fafc_100%)] p-5 shadow-[0_16px_42px_rgba(15,23,42,0.055)] transition duration-300 hover:-translate-y-1 hover:border-slate-300 hover:shadow-[0_24px_55px_rgba(15,23,42,0.11)]">
      <span aria-hidden="true" className={`absolute inset-x-0 top-0 h-1 ${accent.rail}`} />

      <div className="flex min-h-13 items-center gap-3">
        <span className={`grid size-11 shrink-0 place-items-center rounded-2xl border border-white shadow-[0_5px_12px_rgba(15,23,42,0.08)] ${accent.iconBg} ${accent.icon}`}>
          <Icon className="size-5" />
        </span>
        <div className="min-w-0">
          <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-slate-400">Your domain</p>
          <h3 className="mt-0.5 text-sm font-semibold leading-5 text-slate-950">{item.title}</h3>
        </div>
      </div>

      <div className="mt-4 flex min-h-11 items-center justify-between gap-3 border-b border-slate-200/70 pb-3">
        <span className="text-[9px] font-semibold uppercase tracking-[0.14em] text-slate-500">Platforms</span>
        <PlatformBadges item={item} />
      </div>

      <div className="mt-5 min-h-22">
        <p className={`font-semibold leading-tight tracking-tight ${accent.value} ${item.isPlaceholder ? "text-xl" : "text-3xl"}`}>
          {item.value}
        </p>
        <p className="mt-2 text-xs font-medium text-slate-700">{item.label}</p>
        {item.note ? <p className="mt-2 line-clamp-2 text-[11px] leading-5 text-slate-500">{item.note}</p> : null}
      </div>

      {item.stats.length > 0 ? (
        <div className="mt-4 grid grid-cols-2 gap-2">
          {item.stats.map((stat) => (
            <div key={stat.label} className={`min-w-0 rounded-xl border bg-white/80 px-3 py-2.5 shadow-[0_3px_10px_rgba(15,23,42,0.025)] ${accent.border}`}>
              <p className="truncate text-base font-semibold leading-none text-slate-950">{stat.value}</p>
              <p className="mt-1.5 truncate text-[10px] font-medium text-slate-500">{stat.label}</p>
            </div>
          ))}
        </div>
      ) : null}

      <div className="mt-auto pt-4">
        {hasSparkline ? (
          <Sparkline points={item.sparkline ?? []} stroke={accent.stroke} />
        ) : (
          <div className="flex min-h-13 items-center gap-2.5 rounded-xl border border-slate-200/80 bg-white/75 px-3 text-[11px] leading-4 text-slate-500 shadow-inner">
            <span aria-hidden="true" className={`size-1.5 shrink-0 rounded-full ${accent.rail}`} />
            <span>{item.trendLabel ?? "Trend data is not available yet."}</span>
          </div>
        )}

        {item.actionHref && !item.isActionDisabled ? (
          <Link href={item.actionHref} className={`${actionClass} mt-4`}>
            {actionLabel}<ArrowRight className="size-3.5 transition group-hover:translate-x-0.5" />
          </Link>
        ) : (
          <button type="button" disabled={item.isActionDisabled} className={`${actionClass} mt-4 ${item.isActionDisabled ? "cursor-not-allowed opacity-60 hover:translate-y-0 hover:shadow-sm" : ""}`}>
            {actionLabel}<ArrowRight className="size-3.5" />
          </button>
        )}
      </div>
    </article>
  );
}

export function TechnicalJourneySection({ items }: { items: JourneyItem[] }) {
  return (
    <section className="mt-7">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Progress by domain</p>
          <h2 className="mt-1 text-base font-semibold text-slate-950">Your Technical Journey</h2>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 min-[1600px]:grid-cols-4">
        {items.map((item) => <JourneyCard key={item.title} item={item} />)}
      </div>
    </section>
  );
}
