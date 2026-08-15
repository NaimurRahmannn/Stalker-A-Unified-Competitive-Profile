import { AlertTriangle, CheckCircle2, Clock3, Database } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import type { AtCoderSyncState } from "../types";

function sourceLabel(status: AtCoderSyncState["rating"]["status"], cached: boolean) {
  if (status === "success") return "Up to date";
  if (status === "skipped_fresh") return "Already fresh";
  if (cached) return "Cached";
  if (status === "never") return "Not synced";
  if (status === "disabled") return "Unavailable";
  return "Refresh failed";
}

export function AtCoderSyncHealth({ sync }: { sync: AtCoderSyncState | null }) {
  if (!sync || sync.status === "never_synced") return null;
  const incomplete = !sync.submissions.progress.stats_complete;
  const blocked = sync.submissions.progress.status === "blocked" || sync.submissions.progress.error_code === "saturated_timestamp_boundary";
  const warning = sync.status === "partial" || sync.status === "failed" || incomplete;
  return (
    <section aria-live="polite" className={`rounded-2xl border p-5 ${warning ? "border-amber-200 bg-amber-50/70" : "border-emerald-200 bg-emerald-50/60"}`}>
      <div className="flex items-start gap-3">
        {warning ? <AlertTriangle className="mt-0.5 size-5 shrink-0 text-amber-600" /> : <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-600" />}
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold text-slate-950">{blocked ? "Historical indexing needs attention" : sync.status === "partial" ? "Some AtCoder data could not be refreshed" : incomplete ? "Historical submissions are still being indexed" : "AtCoder data is up to date"}</h2>
          <p className="mt-1 text-xs leading-5 text-slate-600">{blocked ? "Part of your historical submission data could not be indexed automatically. Your existing synchronized data is still available." : sync.status === "partial" || sync.status === "failed" ? "Previously synchronized data is still being shown where it is available." : incomplete ? "Problem-solving totals are currently incomplete and are labeled as indexed counts." : "Rating and submission sources completed successfully."}</p>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            <div className="flex items-center justify-between rounded-xl bg-white/80 px-3 py-2 text-xs"><span className="inline-flex items-center gap-2 text-slate-600"><Clock3 className="size-4" />Rating</span><span className="font-semibold text-slate-900">{sourceLabel(sync.rating.status, sync.rating.using_cached_data)}{sync.rating.updated_at ? ` · ${formatRelativeTime(sync.rating.updated_at)}` : ""}</span></div>
            <div className="flex items-center justify-between rounded-xl bg-white/80 px-3 py-2 text-xs"><span className="inline-flex items-center gap-2 text-slate-600"><Database className="size-4" />Submissions</span><span className="font-semibold text-slate-900">{sourceLabel(sync.submissions.status, sync.submissions.using_cached_data)}{sync.submissions.updated_at ? ` · ${formatRelativeTime(sync.submissions.updated_at)}` : ""}</span></div>
          </div>
        </div>
      </div>
    </section>
  );
}
