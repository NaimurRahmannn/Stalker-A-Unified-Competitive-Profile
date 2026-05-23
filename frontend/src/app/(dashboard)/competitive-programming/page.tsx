import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { CompetitivePlatformPerformance } from "@/components/dashboard/competitive-platform-performance";
import {
  BarChart3,
  Bell,
  Cloud,
  Code2,
  RefreshCw,
  Search,
  Sun,
  Trophy,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type MetricAccent = "green" | "blue" | "purple" | "orange";

type MetricItem = {
  label: string;
  value: string;
  subtext: string;
  icon: LucideIcon;
  accent: MetricAccent;
  positive?: boolean;
};

const metricItems: MetricItem[] = [
  {
    label: "Total Problems Solved",
    value: "3,846",
    subtext: "\u2191 128 this month",
    icon: Users,
    accent: "green",
    positive: true,
  },
  {
    label: "Total Contests Joined",
    value: "78",
    subtext: "\u2191 6 this month",
    icon: Cloud,
    accent: "blue",
    positive: true,
  },
  {
    label: "Highest Rating",
    value: "1,842",
    subtext: "Codeforces",
    icon: Trophy,
    accent: "purple",
  },
  {
    label: "Active Platforms",
    value: "4",
    subtext: "All verified",
    icon: BarChart3,
    accent: "orange",
  },
];

const metricAccentStyles: Record<
  MetricAccent,
  { icon: string; iconBg: string }
> = {
  green: {
    icon: "text-emerald-600",
    iconBg: "bg-emerald-50",
  },
  blue: {
    icon: "text-blue-600",
    iconBg: "bg-blue-50",
  },
  purple: {
    icon: "text-violet-600",
    iconBg: "bg-violet-50",
  },
  orange: {
    icon: "text-orange-600",
    iconBg: "bg-orange-50",
  },
};

function HeaderIconButton({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className="relative grid size-11 shrink-0 place-items-center rounded-xl text-slate-500 transition hover:bg-white hover:text-slate-900"
    >
      {children}
    </button>
  );
}

function CompetitiveProgrammingHeader() {
  return (
    <header className="flex flex-col gap-5 min-[1180px]:flex-row min-[1180px]:items-start min-[1180px]:justify-between">
      <div className="min-w-0">
        <div className="flex min-w-0 items-center gap-3">
          <h1 className="truncate text-[25px] font-semibold leading-tight tracking-normal text-slate-950 sm:text-[28px]">
            Competitive Programming
          </h1>
          <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100">
            <Code2 className="size-5" />
          </span>
        </div>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
          Track your ratings, solved problems, contests, and platform streaks
          across coding platforms.
        </p>
      </div>

      <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center min-[1180px]:w-auto">
        <label className="relative block w-full sm:min-w-80 min-[1180px]:w-82.5">
          <span className="sr-only">Search anything</span>
          <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            placeholder="Search anything..."
            className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-16 text-[13px] text-slate-800 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-emerald-300 focus:ring-4 focus:ring-emerald-100"
          />
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium leading-none text-slate-500">
            {"\u2318"} K
          </span>
        </label>

        <button
          type="button"
          className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-[13px] font-semibold text-slate-900 shadow-sm transition hover:bg-slate-50"
        >
          <RefreshCw className="size-4 text-blue-600" />
          Sync All
        </button>

        <div className="flex items-center gap-2">
          <HeaderIconButton label="Notifications">
            <Bell className="size-5" />
            <span className="absolute right-1.5 top-1 grid size-4 place-items-center rounded-full bg-red-500 text-[10px] font-semibold leading-none text-white ring-2 ring-slate-50">
              3
            </span>
          </HeaderIconButton>
          <HeaderIconButton label="Theme">
            <Sun className="size-5" />
          </HeaderIconButton>
        </div>
      </div>
    </header>
  );
}

function MetricCard({ metric }: { metric: MetricItem }) {
  const Icon = metric.icon;
  const accent = metricAccentStyles[metric.accent];

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.035)]">
      <div className="flex min-h-16 items-center gap-4">
        <span
          className={`grid size-13 shrink-0 place-items-center rounded-2xl ${accent.iconBg} ${accent.icon}`}
        >
          <Icon className="size-6" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-2xl font-semibold leading-tight tracking-normal text-slate-950">
            {metric.value}
          </p>
          <p className="mt-1 truncate text-xs font-medium text-slate-600">
            {metric.label}
          </p>
          <p
            className={`mt-1 truncate text-[11px] font-medium ${
              metric.positive ? "text-emerald-600" : "text-slate-500"
            }`}
          >
            {metric.subtext}
          </p>
        </div>
      </div>
    </article>
  );
}

function MetricCardsSection() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {metricItems.map((metric) => (
        <MetricCard key={metric.label} metric={metric} />
      ))}
    </div>
  );
}

function PlaceholderCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
      <div className="mt-3 text-sm leading-6 text-slate-600">{children}</div>
    </section>
  );
}

export default function CompetitiveProgrammingPage() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-white p-5 sm:p-6 lg:border-b-0 lg:border-r">
          <DashboardSidebar activeItem="competitive-programming" />
        </aside>

        <div className="min-w-0 bg-slate-50">
          <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8">
            <CompetitiveProgrammingHeader />
          </section>

          <div className="grid min-w-0 grid-cols-1 gap-6 p-5 sm:p-6 lg:p-8 xl:grid-cols-[minmax(0,1fr)_340px]">
            <section className="min-w-0">
              <MetricCardsSection />

              <div className="mt-6">
                <CompetitivePlatformPerformance />
              </div>

              <div className="mt-6">
                <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
                  <p className="text-sm font-medium leading-6 text-slate-600">
                    Rating Progress and Recent Activity will be built in the
                    next part.
                  </p>
                </section>
              </div>
            </section>

            <aside className="min-w-0 border-t border-slate-200 pt-6 xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
              <PlaceholderCard title="Competitive Widgets">
                Profile completion, next steps, and solving streak widgets will
                live here.
              </PlaceholderCard>
            </aside>
          </div>
        </div>
      </div>
    </main>
  );
}
