import { CheckCircle2, CircleX, History } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import type { CodeforcesRecentActivityEntry } from "../types";

function verdictLabel(verdict: string) {
  return verdict === "OK" ? "Accepted" : verdict.toLowerCase().replaceAll("_", " ");
}

export function RecentCodeforcesActivity({ activity }: { activity: CodeforcesRecentActivityEntry[] }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between gap-3"><div className="flex items-center gap-2"><History className="size-4.5 text-blue-600" /><h2 className="text-sm font-semibold text-slate-950">Recent Activity</h2></div>{activity.length ? <span className="text-[11px] font-medium text-slate-500">Latest {activity.length}</span> : null}</div>
      {activity.length ? <div className="mt-4 divide-y divide-slate-100">{activity.map((item, index) => { const accepted = item.verdict === "OK"; const Icon = accepted ? CheckCircle2 : CircleX; return (
        <article key={`${item.submission_id ?? "submission"}-${item.submitted_at}-${index}`} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
          <span className={`mt-0.5 grid size-8 shrink-0 place-items-center rounded-xl ${accepted ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-500"}`}><Icon className="size-4" /></span>
          <div className="min-w-0 flex-1"><div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1"><h3 className="min-w-0 truncate text-xs font-semibold text-slate-900">{item.problem_index ? `${item.problem_index}. ` : ""}{item.problem_name}</h3><time dateTime={item.submitted_at} className="shrink-0 text-[10px] text-slate-500">{formatRelativeTime(item.submitted_at)}</time></div><div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-slate-500"><span className={accepted ? "font-semibold text-emerald-600" : "font-semibold text-red-500"}>{verdictLabel(item.verdict)}</span>{item.problem_rating !== null ? <span>Rating {item.problem_rating}</span> : null}{item.language ? <span>{item.language}</span> : null}</div></div>
        </article>
      ); })}</div> : <div className="mt-4 grid min-h-44 place-items-center rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-6 text-center"><div><p className="text-sm font-semibold text-slate-800">No recent submissions</p><p className="mt-1 text-xs leading-5 text-slate-500">Recent accepted solutions and unsuccessful attempts will appear after syncing.</p></div></div>}
    </section>
  );
}
