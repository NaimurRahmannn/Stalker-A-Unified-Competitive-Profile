import Image from "next/image";
import { RefreshCw } from "lucide-react";
import { dashboardCardSurface } from "../styles";
import { ClistEventsCard } from "./clist-events-card";
import { WidgetCard } from "./widget-card";

function StreakSummaryCard() {
  return (
    <WidgetCard title="Streak Summary">
      <div className="mt-4 rounded-2xl border border-dashed border-slate-200 bg-slate-50/70 px-4 py-8 text-center">
        <span className="mx-auto grid size-11 place-items-center rounded-2xl bg-white text-slate-400">
          <RefreshCw className="size-5" />
        </span>
        <p className="mt-3 text-sm font-semibold text-slate-950">
          Streak tracking coming soon
        </p>
        <p className="mt-1 text-xs font-medium leading-5 text-slate-500">
          No streak endpoint is available yet.
        </p>
      </div>
    </WidgetCard>
  );
}

function QuoteCard() {
  return (
    <article className={`${dashboardCardSurface} overflow-hidden p-1`}>
      <Image
        src="/images/stalker_right_bg.png"
        alt="Stalker quote"
        width={2140}
        height={634}
        className="h-25 w-full rounded-[18px] object-cover"
      />
    </article>
  );
}

export function RightWidgetsPanel() {
  return (
    <div className="grid gap-4">
      <ClistEventsCard />
      <StreakSummaryCard />
      <QuoteCard />
    </div>
  );
}
