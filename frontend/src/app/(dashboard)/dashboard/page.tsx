import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import {
  BarChart3,
  Bell,
  RefreshCw,
  Search,
  ShieldCheck,
  Sun,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type MetricAccent = "green" | "blue" | "purple" | "orange";

type MetricItem = {
  label: string;
  value: string;
  icon: LucideIcon;
  accent: MetricAccent;
};

const metricAccentStyles: Record<
  MetricAccent,
  { icon: string; iconBg: string; barBg: string }
> = {
  green: {
    icon: "text-emerald-600",
    iconBg: "bg-emerald-50",
    barBg: "bg-emerald-50",
  },
  blue: {
    icon: "text-blue-600",
    iconBg: "bg-blue-50",
    barBg: "bg-blue-50",
  },
  purple: {
    icon: "text-violet-600",
    iconBg: "bg-violet-50",
    barBg: "bg-violet-50",
  },
  orange: {
    icon: "text-orange-600",
    iconBg: "bg-orange-50",
    barBg: "bg-orange-50",
  },
};

const metricItems: MetricItem[] = [
  {
    label: "Platforms Connected",
    value: "10",
    icon: Users,
    accent: "green",
  },
  {
    label: "Verified",
    value: "6",
    icon: ShieldCheck,
    accent: "blue",
  },
  {
    label: "Last Synced",
    value: "2h ago",
    icon: RefreshCw,
    accent: "purple",
  },
  {
    label: "Profile Completion",
    value: "72%",
    icon: BarChart3,
    accent: "orange",
  },
];

type PlaceholderPanelProps = {
  title: string;
  description: string;
  className?: string;
};

function PlaceholderPanel({
  title,
  description,
  className = "",
}: PlaceholderPanelProps) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}
    >
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-3 text-base font-semibold text-slate-900">
        {description}
      </p>
    </div>
  );
}

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

function DashboardTopHeader() {
  return (
    <header className="flex flex-col gap-5 min-[1180px]:flex-row min-[1180px]:items-start min-[1180px]:justify-between">
      <div className="min-w-0">
        <h1 className="text-[25px] font-semibold leading-tight tracking-normal text-slate-950 sm:text-[28px]">
          Good morning, Naimur <span aria-hidden="true">{"\uD83D\uDC4B"}</span>
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600 sm:text-base">
          Track your progress across 4 domains and 10+ platforms.
        </p>
      </div>

      <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center min-[1180px]:w-auto">
        <label className="relative block w-full sm:min-w-80 min-[1180px]:w-101.25">
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
    <article className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-[0_12px_30px_rgba(15,23,42,0.035)]">
      <div className="flex min-h-14 items-center gap-3">
        <span
          className={`grid size-10 shrink-0 place-items-center rounded-xl ${accent.iconBg} ${accent.icon}`}
        >
          <Icon className="size-5" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-xl font-semibold leading-tight tracking-normal text-slate-950">
            {metric.value}
          </p>
          <p className="mt-1 truncate text-xs font-medium text-slate-600">
            {metric.label}
          </p>
        </div>
      </div>
      <div className={`mt-2.5 h-0.5 rounded-full ${accent.barBg}`} />
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

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-white p-5 sm:p-6 lg:border-b-0 lg:border-r">
          <DashboardSidebar />
        </aside>

        <div className="min-w-0 bg-slate-50">
          <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8">
            <DashboardTopHeader />
          </section>

          <div className="grid min-w-0 grid-cols-1 gap-6 p-5 sm:p-6 lg:p-8 xl:grid-cols-[minmax(0,1fr)_340px]">
            <section className="min-w-0">
              <MetricCardsSection />

              <PlaceholderPanel
                title="Main Content"
                description="Technical Journey cards will be built in the next part."
                className="mt-6 min-h-72"
              />
            </section>

            <aside className="min-w-0 border-t border-slate-200 pt-6 xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
              <PlaceholderPanel
                title="Right Widgets"
                description="Profile, streak, and next-step widgets will live here."
                className="min-h-48"
              />
            </aside>
          </div>
        </div>
      </div>
    </main>
  );
}
