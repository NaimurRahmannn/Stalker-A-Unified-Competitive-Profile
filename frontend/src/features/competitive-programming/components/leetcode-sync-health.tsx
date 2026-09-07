import { AlertTriangle, CheckCircle2, Clock3, Loader2 } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import type { LeetCodeAnalyticsSync } from "../types";

function statusLabel(sync: LeetCodeAnalyticsSync) {
  if (sync.status === "success") return "Up to date";
  if (sync.status === "running") return "Syncing…";
  if (sync.status === "pending") return "Sync queued";
  if (sync.using_cached_data) return "Cached";
  return "Refresh failed";
}

export function LeetCodeSyncHealth({ sync }: { sync: LeetCodeAnalyticsSync | null }) {
  if (!sync || sync.status === "never_synced") return null;

  const warning = sync.status === "failed" || (sync.status === "success" && sync.using_cached_data);
  const running = sync.status === "running" || sync.status === "pending";

  return (
    <section aria-live="polite" className={`rounded-2xl border p-5 ${warning ? "border-amber-200 bg-amber-50/70" : running ? "border-blue-200 bg-blue-50/70" : "border-emerald-200 bg-emerald-50/60"}`}>
      <div className="flex items-start gap-3">
        {warning ? <AlertTriangle className="mt-0.5 size-5 shrink-0 text-amber-600" /> : running ? <Loader2 className="mt-0.5 size-5 shrink-0 animate-spin text-blue-600" /> : <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-600" />}
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold text-slate-950">
            {sync.status === "failed"
              ? "LeetCode data could not be refreshed"
              : running
                ? "LeetCode sync is in progress"
                : "LeetCode data is up to date"}
          </h2>
          <p className="mt-1 text-xs leading-5 text-slate-600">
            {sync.status === "failed"
              ? "Previously synchronized data is still being shown where it is available."
              : running
                ? "Your LeetCode data will be updated shortly."
                : "Profile, problem, and contest data completed successfully."}
          </p>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            <div className="flex items-center justify-between rounded-xl bg-white/80 px-3 py-2 text-xs">
              <span className="inline-flex items-center gap-2 text-slate-600"><Clock3 className="size-4" />Status</span>
              <span className="font-semibold text-slate-900">{statusLabel(sync)}</span>
            </div>
            <div className="flex items-center justify-between rounded-xl bg-white/80 px-3 py-2 text-xs">
              <span className="inline-flex items-center gap-2 text-slate-600"><Clock3 className="size-4" />Last synced</span>
              <span className="font-semibold text-slate-900">{sync.successful_at ? formatRelativeTime(sync.successful_at) : "Never"}</span>
            </div>
          </div>
          {sync.error_code ? (
            <p className="mt-3 text-[10px] text-amber-700">Error: {sync.error_code}</p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
