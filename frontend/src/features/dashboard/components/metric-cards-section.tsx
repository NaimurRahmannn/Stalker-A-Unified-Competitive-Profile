import { dashboardCardSurface, metricAccentStyles } from "../styles";
import type { MetricItem } from "../types";

function MetricCard({ metric }: { metric: MetricItem }) {
  const Icon = metric.icon;
  const accent = metricAccentStyles[metric.accent];

  return (
    <article className={`${dashboardCardSurface} overflow-hidden px-4 py-4 transition duration-300 hover:-translate-y-0.5 hover:shadow-[0_22px_48px_rgba(15,23,42,0.09)]`}>
      <div className="flex min-h-14 items-center gap-3">
        <span
          className={`grid size-11 shrink-0 place-items-center rounded-2xl border border-white shadow-[0_5px_12px_rgba(15,23,42,0.07)] ${accent.iconBg} ${accent.icon}`}
        >
          <Icon className="size-5" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-xl font-semibold leading-tight tracking-normal text-slate-950">
            {metric.value}
          </p>
          <p className="mt-1 truncate text-xs font-medium text-slate-600">
            {metric.label}
          </p>
        </div>
      </div>
      <div className={`mt-3 h-0.5 rounded-full ${accent.barBg}`} />
    </article>
  );
}

export function MetricCardsSection({ metrics }: { metrics: MetricItem[] }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <MetricCard key={metric.label} metric={metric} />
      ))}
    </div>
  );
}
