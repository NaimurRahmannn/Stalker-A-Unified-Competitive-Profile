import { recentAchievements } from "../data";
import { achievementAccentStyles } from "../styles";
import type { RecentAchievement } from "../types";
import { SectionCard } from "./section-card";

function AchievementCard({ achievement }: { achievement: RecentAchievement }) {
  const Icon = achievement.icon;
  const accent = achievementAccentStyles[achievement.accent];

  return (
    <article
      className={`flex min-h-28 flex-col rounded-2xl border border-slate-200 bg-white p-3 shadow-[0_10px_24px_rgba(15,23,42,0.03)] transition hover:-translate-y-0.5 hover:shadow-[0_14px_30px_rgba(15,23,42,0.06)] ${accent.border}`}
    >
      <div className="flex items-start gap-2.5">
        <span
          className={`grid size-9 shrink-0 place-items-center rounded-xl ${accent.iconBg} ${accent.icon}`}
        >
          <Icon className="size-4.5" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold text-slate-950">
            {achievement.platform}
          </p>
          <p className="mt-0.5 truncate text-[11px] font-medium text-slate-600">
            {achievement.title}
          </p>
        </div>
      </div>

      <div className="mt-3 min-h-5">
        {achievement.badge ? (
          <span
            className={`inline-flex max-w-full rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${accent.badge}`}
          >
            <span className="truncate">{achievement.badge}</span>
          </span>
        ) : null}
        {achievement.description ? (
          <p className="line-clamp-1 text-[11px] font-medium leading-5 text-slate-600">
            {achievement.description}
          </p>
        ) : null}
      </div>

      <p className="mt-auto pt-2 text-[10px] font-medium text-slate-500">
        {achievement.time}
      </p>
    </article>
  );
}

export function RecentAchievementsSection() {
  return (
    <div className="mt-6">
      <SectionCard title="Recent Achievements">
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {recentAchievements.map((achievement) => (
            <AchievementCard
              key={`${achievement.platform}-${achievement.title}`}
              achievement={achievement}
            />
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
