import { CheckCircle2, CircleX, History, TrendingUp } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import type { CompetitiveActivity } from "../types";

function verdictLabel(verdict: string | null) {
  if (!verdict) return null;
  if (verdict === "OK" || verdict === "AC") return "Accepted";
  return verdict.replaceAll("_", " ");
}

export function CompetitiveActivityList({
  activity,
  title = "Recent Activity",
  showPlatform = false,
}: {
  activity: CompetitiveActivity[];
  title?: string;
  showPlatform?: boolean;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2"><History className="size-4.5 text-blue-600" /><h2 className="text-sm font-semibold text-slate-950">{title}</h2></div>
        {activity.length ? <span className="text-[11px] font-medium text-slate-500">Latest {activity.length}</span> : null}
      </div>
      {activity.length ? (
        <div className="mt-4 divide-y divide-slate-100">
          {activity.map((item) => {
            const Icon = item.type === "rating_change" ? TrendingUp : item.accepted ? CheckCircle2 : CircleX;
            const positive = item.type === "rating_change" ? (item.ratingChange ?? 0) >= 0 : item.accepted;
            return (
              <article key={item.id} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                {showPlatform ? <span className="mt-1 inline-flex h-6 min-w-7 items-center justify-center rounded-md bg-slate-100 px-1 text-[9px] font-bold text-slate-600">{item.platform === "codeforces" ? "CF" : "AC"}</span> : null}
                <span className={`mt-0.5 grid size-8 shrink-0 place-items-center rounded-xl ${positive ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-500"}`}><Icon className="size-4" /></span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1"><h3 className="min-w-0 truncate text-xs font-semibold text-slate-900">{item.title}</h3><time dateTime={item.occurredAt} className="shrink-0 text-[10px] text-slate-500">{formatRelativeTime(item.occurredAt)}</time></div>
                  <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-slate-500">{item.verdict ? <span className={positive ? "font-semibold text-emerald-600" : "font-semibold text-red-500"}>{verdictLabel(item.verdict)}</span> : null}{item.ratingChange !== null ? <span className="font-semibold text-emerald-600">{item.ratingChange >= 0 ? "+" : ""}{item.ratingChange} rating</span> : null}{item.subtitle ? <span>{item.subtitle}</span> : null}</div>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="mt-4 grid min-h-44 place-items-center rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-6 text-center"><div><p className="text-sm font-semibold text-slate-800">No recent activity</p><p className="mt-1 text-xs leading-5 text-slate-500">Recent submissions will appear after syncing.</p></div></div>
      )}
    </section>
  );
}
