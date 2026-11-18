import { RefreshCw } from "lucide-react";
import { ClistEventsCard } from "./clist-events-card";

function StreakSummary() {
  return (
    <section aria-labelledby="streak-summary-heading" className="border-t border-slate-200 pt-6">
      <div className="flex items-center gap-2">
        <RefreshCw aria-hidden="true" className="size-4 text-slate-400" />
        <h2 id="streak-summary-heading" className="text-sm font-semibold text-slate-950">Streak Summary</h2>
      </div>
      <p className="mt-3 text-xs font-semibold text-slate-700">Streak tracking coming soon</p>
      <p className="mt-1 text-xs leading-5 text-slate-500">No streak endpoint is available yet.</p>
    </section>
  );
}

export function RightWidgetsPanel() {
  return (
    <div className="w-full space-y-8">
      <ClistEventsCard />
      <StreakSummary />
    </div>
  );
}
