import { Award } from "lucide-react";
import { SectionCard } from "./section-card";

export function RecentAchievementsSection() {
  return (
    <div className="mt-6">
      <SectionCard title="Recent Achievements" showAction={false}>
        <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 px-4 py-10 text-center">
          <span className="mx-auto grid size-12 place-items-center rounded-2xl bg-white text-slate-400">
            <Award className="size-5" />
          </span>
          <p className="mt-3 text-sm font-semibold text-slate-950">
            No recent achievements yet
          </p>
          <p className="mt-1 text-xs font-medium text-slate-500">
            Connect and sync a platform to see activity here.
          </p>
        </div>
      </SectionCard>
    </div>
  );
}
