import Image from "next/image";
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import {
  ArrowRight,
  BarChart3,
  Bell,
  Code2,
  RefreshCw,
  Search,
  ShieldCheck,
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

type JourneyItem = {
  title: string;
  value: string;
  label: string;
  icon: LucideIcon;
  accent: MetricAccent;
  stats: Array<{
    value: string;
    label: string;
  }>;
  sparkline: number[];
};

type PlatformStatus = "Verified" | "Unverified";

type ConnectedPlatform = {
  name: string;
  handle: string;
  status: PlatformStatus;
  mark: "codeforces" | "leetcode" | "atcoder" | "codechef" | "github" | "kaggle";
};

const journeyAccentStyles: Record<
  MetricAccent,
  {
    border: string;
    icon: string;
    iconBg: string;
    value: string;
    button: string;
    buttonText: string;
    stroke: string;
  }
> = {
  green: {
    border: "border-emerald-100",
    icon: "text-emerald-600",
    iconBg: "bg-emerald-50",
    value: "text-emerald-600",
    button: "border-emerald-200 bg-emerald-50/50 hover:bg-emerald-50",
    buttonText: "text-emerald-700",
    stroke: "#059669",
  },
  blue: {
    border: "border-blue-100",
    icon: "text-blue-600",
    iconBg: "bg-blue-50",
    value: "text-blue-600",
    button: "border-blue-200 bg-blue-50/50 hover:bg-blue-50",
    buttonText: "text-blue-700",
    stroke: "#2563eb",
  },
  purple: {
    border: "border-violet-100",
    icon: "text-violet-600",
    iconBg: "bg-violet-50",
    value: "text-violet-600",
    button: "border-violet-200 bg-violet-50/50 hover:bg-violet-50",
    buttonText: "text-violet-700",
    stroke: "#7c3aed",
  },
  orange: {
    border: "border-orange-100",
    icon: "text-orange-600",
    iconBg: "bg-orange-50",
    value: "text-orange-600",
    button: "border-orange-200 bg-orange-50/50 hover:bg-orange-50",
    buttonText: "text-orange-700",
    stroke: "#f97316",
  },
};

const journeyItems: JourneyItem[] = [
  {
    title: "Competitive Programming",
    value: "450",
    label: "Problems Solved",
    icon: Code2,
    accent: "green",
    stats: [
      { value: "4", label: "Platforms" },
      { value: "21", label: "Day Streak" },
    ],
    sparkline: [18, 22, 20, 27, 24, 33, 29, 38, 42, 36, 45, 40, 44, 54, 48, 58, 51, 57],
  },
  {
    title: "CTF / Cybersecurity",
    value: "162",
    label: "Flags Captured",
    icon: ShieldCheck,
    accent: "blue",
    stats: [
      { value: "3", label: "Platforms" },
      { value: "14", label: "Day Streak" },
    ],
    sparkline: [12, 13, 11, 18, 27, 22, 31, 26, 18, 21, 24, 34, 30, 44, 37, 41, 43, 51],
  },
  {
    title: "Hackathon",
    value: "12",
    label: "Hackathons Joined",
    icon: Trophy,
    accent: "purple",
    stats: [
      { value: "5", label: "Projects" },
      { value: "2", label: "Wins" },
    ],
    sparkline: [14, 19, 17, 26, 23, 24, 36, 28, 24, 31, 29, 37, 40, 47, 41, 51, 44, 48],
  },
  {
    title: "Datathon / Data Science",
    value: "6",
    label: "Competitions Joined",
    icon: BarChart3,
    accent: "orange",
    stats: [
      { value: "2", label: "Medals" },
      { value: "3", label: "Notebooks" },
    ],
    sparkline: [16, 24, 21, 31, 28, 40, 29, 25, 33, 28, 35, 42, 39, 48, 32, 44, 36, 49],
  },
];

const connectedPlatforms: ConnectedPlatform[] = [
  {
    name: "Codeforces",
    handle: "@tourist_",
    status: "Verified",
    mark: "codeforces",
  },
  {
    name: "LeetCode",
    handle: "@naimur_rahman",
    status: "Verified",
    mark: "leetcode",
  },
  {
    name: "AtCoder",
    handle: "@naimur_rahman",
    status: "Verified",
    mark: "atcoder",
  },
  {
    name: "CodeChef",
    handle: "@naimur_rahman",
    status: "Unverified",
    mark: "codechef",
  },
  {
    name: "GitHub",
    handle: "@naimur_rahman",
    status: "Verified",
    mark: "github",
  },
  {
    name: "Kaggle",
    handle: "@naimur_rahman",
    status: "Unverified",
    mark: "kaggle",
  },
];

const platformLogoSrc: Record<ConnectedPlatform["mark"], string> = {
  atcoder: "/images/atcoder_logo.png",
  codechef: "/images/codechef_logo.png",
  codeforces: "/images/codeforces_logo.png",
  github: "/images/github_logo.png",
  kaggle: "/images/kaggle_logo.png",
  leetcode: "/images/leetcode_logo.png",
};

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

function Sparkline({
  points,
  stroke,
}: {
  points: number[];
  stroke: string;
}) {
  const width = 180;
  const height = 52;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const polylinePoints = points
    .map((point, index) => {
      const x = (index / (points.length - 1)) * width;
      const y = height - ((point - min) / range) * (height - 8) - 4;

      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="mt-5 h-13 w-full overflow-hidden" aria-hidden="true">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full">
        <polyline
          points={polylinePoints}
          fill="none"
          stroke={stroke}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2.4"
        />
      </svg>
    </div>
  );
}

function JourneyCard({ item }: { item: JourneyItem }) {
  const Icon = item.icon;
  const accent = journeyAccentStyles[item.accent];

  return (
    <article
      className={`rounded-2xl border bg-white p-4 shadow-[0_16px_38px_rgba(15,23,42,0.045)] ${accent.border}`}
    >
      <div className="flex items-center gap-3">
        <span
          className={`grid size-10 shrink-0 place-items-center rounded-xl ${accent.iconBg} ${accent.icon}`}
        >
          <Icon className="size-5" />
        </span>
        <h3 className="min-w-0 truncate text-sm font-semibold text-slate-950">
          {item.title}
        </h3>
      </div>

      <div className="mt-6">
        <p className={`text-3xl font-semibold leading-none ${accent.value}`}>
          {item.value}
        </p>
        <p className="mt-2 text-xs font-medium text-slate-600">{item.label}</p>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3">
        {item.stats.map((stat) => (
          <div key={stat.label}>
            <p className="text-base font-semibold leading-none text-slate-950">
              {stat.value}
            </p>
            <p className="mt-1.5 text-[11px] font-medium text-slate-500">
              {stat.label}
            </p>
          </div>
        ))}
      </div>

      <Sparkline points={item.sparkline} stroke={accent.stroke} />

      <button
        type="button"
        className={`mt-4 inline-flex h-9 w-full items-center justify-center gap-2 rounded-xl border text-xs font-semibold transition ${accent.button} ${accent.buttonText}`}
      >
        View Details
        <ArrowRight className="size-3.5" />
      </button>
    </article>
  );
}

function TechnicalJourneySection() {
  return (
    <section className="mt-7">
      <h2 className="text-base font-semibold text-slate-950">
        Your Technical Journey
      </h2>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 min-[1600px]:grid-cols-4">
        {journeyItems.map((item) => (
          <JourneyCard key={item.title} item={item} />
        ))}
      </div>
    </section>
  );
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
        <button
          type="button"
          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 transition hover:text-blue-800"
        >
          View All
          <ArrowRight className="size-3.5" />
        </button>
      </div>
      {children}
    </section>
  );
}

function PlatformMark({ mark }: { mark: ConnectedPlatform["mark"] }) {
  const logoSize = mark === "codeforces" || mark === "github" ? "size-8" : "size-9";

  return (
    <span className="grid size-11 place-items-center rounded-2xl bg-slate-50">
      <Image
        src={platformLogoSrc[mark]}
        alt=""
        width={40}
        height={40}
        className={`${logoSize} object-contain`}
      />
    </span>
  );
}

function PlatformMiniCard({ platform }: { platform: ConnectedPlatform }) {
  const badgeClass =
    platform.status === "Verified"
      ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
      : "bg-orange-50 text-orange-700 ring-1 ring-orange-200";

  return (
    <article className="flex min-h-34 flex-col items-center justify-between rounded-2xl border border-slate-200 bg-white p-3 text-center shadow-[0_10px_26px_rgba(15,23,42,0.035)] transition hover:-translate-y-0.5 hover:shadow-[0_14px_32px_rgba(15,23,42,0.07)]">
      <PlatformMark mark={platform.mark} />
      <div className="min-w-0">
        <p className="truncate text-xs font-semibold text-slate-950">
          {platform.name}
        </p>
        <p className="mt-1 truncate text-[10px] font-medium text-slate-500">
          {platform.handle}
        </p>
      </div>
      <span
        className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${badgeClass}`}
      >
        {platform.status}
      </span>
    </article>
  );
}

function AddPlatformCard() {
  return (
    <button
      type="button"
      className="flex min-h-34 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-blue-200 bg-blue-50/40 p-3 text-center text-blue-700 transition hover:bg-blue-50"
    >
      <span className="grid size-10 place-items-center rounded-xl border border-blue-200 bg-white">
        <span className="text-2xl font-light leading-none">+</span>
      </span>
      <span className="text-xs font-semibold">Add Platform</span>
    </button>
  );
}

function ConnectedPlatformsSection() {
  return (
    <SectionCard title="Connected Platforms">
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
        {connectedPlatforms.map((platform) => (
          <PlatformMiniCard key={platform.name} platform={platform} />
        ))}
        <AddPlatformCard />
      </div>
    </SectionCard>
  );
}

function ConnectedPlatformsRow() {
  return (
    <div className="mt-6">
      <ConnectedPlatformsSection />
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

              <TechnicalJourneySection />

              <ConnectedPlatformsRow />

              <PlaceholderPanel
                title="Main Content"
                description="Recent Achievements will be built in the next part."
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
