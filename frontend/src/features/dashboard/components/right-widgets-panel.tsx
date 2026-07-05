import Image from "next/image";
import { ArrowRight, Check, RefreshCw } from "lucide-react";
import type { CSSProperties } from "react";
import { widgetAccentStyles } from "../styles";
import type { ChecklistItem, NextStep } from "../types";
import { WidgetCard } from "./widget-card";

function ProgressRing({ progress }: { progress: number }) {
  const style: CSSProperties = {
    background: `conic-gradient(#76c943 ${progress * 3.6}deg, #eef2ef 0deg)`,
  };

  return (
    <div
      aria-label={`${progress}% profile completion`}
      className="grid size-31 shrink-0 place-items-center rounded-full"
      role="img"
      style={style}
    >
      <div className="grid size-24 place-items-center rounded-full bg-white shadow-inner">
        <span className="text-2xl font-semibold text-slate-950">
          {progress}%
        </span>
      </div>
    </div>
  );
}

function ChecklistRow({ item }: { item: ChecklistItem }) {
  return (
    <div className="flex items-center gap-2.5 text-xs font-medium text-slate-600">
      <span
        className={`grid size-4.5 shrink-0 place-items-center rounded-md border ${
          item.done
            ? "border-emerald-500 bg-emerald-500 text-white"
            : "border-slate-300 bg-white text-transparent"
        }`}
      >
        <Check className="size-3" />
      </span>
      <span>{item.label}</span>
    </div>
  );
}

function ProfileCompletionCard({
  checklist,
  progress,
}: {
  checklist: ChecklistItem[];
  progress: number;
}) {
  return (
    <WidgetCard title="Profile Completion">
      <div className="mt-4 grid gap-4 sm:grid-cols-[124px_minmax(0,1fr)] sm:items-center xl:grid-cols-1 min-[1750px]:grid-cols-[124px_minmax(0,1fr)]">
        <ProgressRing progress={progress} />
        <div className="grid gap-2.5">
          {checklist.map((item) => (
            <ChecklistRow key={item.label} item={item} />
          ))}
        </div>
      </div>

      <button
        type="button"
        disabled
        className="mt-4 inline-flex h-10 w-full cursor-not-allowed items-center justify-center gap-2 rounded-xl bg-slate-100 px-4 text-xs font-semibold text-slate-500"
      >
        Profile Editing Coming Soon
        <ArrowRight className="size-3.5" />
      </button>
    </WidgetCard>
  );
}

function NextStepRow({ step }: { step: NextStep }) {
  const Icon = step.icon;
  const accent = widgetAccentStyles[step.accent];

  return (
    <article className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
      <span
        className={`grid size-9 shrink-0 place-items-center rounded-xl ${accent.iconBg} ${accent.icon}`}
      >
        <Icon className="size-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-semibold text-slate-950">
          {step.title}
        </p>
        <p className="mt-1 truncate text-[11px] font-medium text-slate-500">
          {step.subtitle}
        </p>
      </div>
      <ArrowRight className="size-4 shrink-0 text-slate-400" />
    </article>
  );
}

function NextStepsCard({ steps }: { steps: NextStep[] }) {
  return (
    <WidgetCard title="Next Steps">
      {steps.length > 0 ? (
        <div className="mt-4 divide-y divide-slate-100">
          {steps.map((step) => (
            <NextStepRow key={step.title} step={step} />
          ))}
        </div>
      ) : (
        <div className="mt-4 rounded-2xl border border-dashed border-slate-200 bg-slate-50/70 px-4 py-8 text-center">
          <p className="text-sm font-semibold text-slate-950">
            No next steps right now
          </p>
          <p className="mt-1 text-xs font-medium leading-5 text-slate-500">
            You are caught up with the profile and platform data available here.
          </p>
        </div>
      )}
    </WidgetCard>
  );
}

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
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <Image
        src="/images/stalker_right_bg.png"
        alt="Stalker quote"
        width={2140}
        height={634}
        className="h-25 w-full object-cover"
      />
    </article>
  );
}

export function RightWidgetsPanel({
  nextSteps,
  profileChecklist,
  profileProgress,
}: {
  nextSteps: NextStep[];
  profileChecklist: ChecklistItem[];
  profileProgress: number;
}) {
  return (
    <div className="grid gap-4">
      <ProfileCompletionCard
        checklist={profileChecklist}
        progress={profileProgress}
      />
      <NextStepsCard steps={nextSteps} />
      <StreakSummaryCard />
      <QuoteCard />
    </div>
  );
}
