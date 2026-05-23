import Image from "next/image";
import { ArrowRight, Check } from "lucide-react";
import type { CSSProperties } from "react";
import { nextSteps, profileChecklist, streakItems } from "../data";
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

function ProfileCompletionCard() {
  return (
    <WidgetCard title="Profile Completion">
      <div className="mt-4 grid gap-4 sm:grid-cols-[124px_minmax(0,1fr)] sm:items-center xl:grid-cols-1 min-[1750px]:grid-cols-[124px_minmax(0,1fr)]">
        <ProgressRing progress={72} />
        <div className="grid gap-2.5">
          {profileChecklist.map((item) => (
            <ChecklistRow key={item.label} item={item} />
          ))}
        </div>
      </div>

      <button
        type="button"
        className="mt-4 inline-flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-lime-400 px-4 text-xs font-semibold text-slate-950 shadow-[0_12px_24px_rgba(132,204,22,0.25)] transition hover:bg-lime-300"
      >
        Complete Your Profile
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

function NextStepsCard() {
  return (
    <WidgetCard title="Next Steps">
      <div className="mt-4 divide-y divide-slate-100">
        {nextSteps.map((step) => (
          <NextStepRow key={step.title} step={step} />
        ))}
      </div>

      <button
        type="button"
        className="mt-3 inline-flex h-9 w-full items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-white text-xs font-semibold text-emerald-700 transition hover:bg-emerald-50"
      >
        View All Steps
        <ArrowRight className="size-3.5" />
      </button>
    </WidgetCard>
  );
}

function StreakSummaryCard() {
  return (
    <WidgetCard title="Streak Summary">
      <div className="mt-4 grid grid-cols-4 gap-2">
        {streakItems.map((item) => {
          const Icon = item.icon;
          const accent = widgetAccentStyles[item.accent];

          return (
            <article
              className="min-w-0 rounded-2xl border border-slate-100 bg-slate-50/60 p-2.5 text-center"
              key={item.label}
            >
              <span
                className={`mx-auto grid size-9 place-items-center rounded-xl ${accent.iconBg} ${accent.icon}`}
              >
                <Icon className="size-4" />
              </span>
              <p className="mt-2 text-xl font-semibold leading-none text-slate-950">
                {item.value}
              </p>
              <p className="mt-1 text-[10px] font-medium text-slate-500">
                days
              </p>
              <p className="mt-2 truncate text-[10px] font-medium text-slate-600">
                {item.label}
              </p>
            </article>
          );
        })}
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

export function RightWidgetsPanel() {
  return (
    <div className="grid gap-4">
      <ProfileCompletionCard />
      <NextStepsCard />
      <StreakSummaryCard />
      <QuoteCard />
    </div>
  );
}
