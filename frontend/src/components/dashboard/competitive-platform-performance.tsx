import Image from "next/image";
import { ArrowRight, Flame } from "lucide-react";

type PlatformStatus = "Verified" | "Unverified";

type PlatformStat = {
  label: string;
  value: string;
  valueClassName?: string;
};

type CompetitivePlatform = {
  name: string;
  status: PlatformStatus;
  lastSynced: string;
  logoSrc: string;
  logoClassName: string;
  statRows: PlatformStat[][];
  streak: string;
  streakDots: boolean[];
};

const platformPerformance: CompetitivePlatform[] = [
  {
    name: "Codeforces",
    status: "Verified",
    lastSynced: "Last synced 2h ago",
    logoSrc: "/images/codeforces_logo.png",
    logoClassName: "size-10",
    statRows: [
      [
        {
          label: "Rating",
          value: "1,842",
          valueClassName: "text-blue-600",
        },
        { label: "Max Rating", value: "1,942" },
      ],
      [
        { label: "Solved", value: "1,256" },
        { label: "Contests", value: "42" },
        { label: "Rank", value: "Expert" },
      ],
    ],
    streak: "21 day streak",
    streakDots: [true, true, true, true, true, true, true, true, false, false],
  },
  {
    name: "LeetCode",
    status: "Verified",
    lastSynced: "Last synced 2h ago",
    logoSrc: "/images/leetcode_logo.png",
    logoClassName: "size-11",
    statRows: [
      [
        {
          label: "Solved",
          value: "1,487",
          valueClassName: "text-emerald-600",
        },
        { label: "Ranking", value: "Top 9.43%" },
      ],
      [
        {
          label: "Easy",
          value: "512",
          valueClassName: "text-emerald-600",
        },
        {
          label: "Medium",
          value: "756",
          valueClassName: "text-orange-500",
        },
        {
          label: "Hard",
          value: "219",
          valueClassName: "text-red-500",
        },
      ],
    ],
    streak: "34 day streak",
    streakDots: [true, true, true, true, true, true, true, true, true, false],
  },
  {
    name: "AtCoder",
    status: "Verified",
    lastSynced: "Last synced 3h ago",
    logoSrc: "/images/atcoder_logo.png",
    logoClassName: "size-11",
    statRows: [
      [
        {
          label: "Rating",
          value: "1,624",
          valueClassName: "text-violet-600",
        },
        { label: "Max Rating", value: "1,824" },
      ],
      [
        { label: "Solved", value: "642" },
        { label: "Contests", value: "31" },
      ],
    ],
    streak: "17 day streak",
    streakDots: [true, true, true, true, true, true, true, false, false, false],
  },
  {
    name: "CodeChef",
    status: "Unverified",
    lastSynced: "Last synced 1d ago",
    logoSrc: "/images/codechef_logo.png",
    logoClassName: "size-12",
    statRows: [
      [
        {
          label: "Stars",
          value: "3 \u2605",
          valueClassName: "text-orange-500",
        },
        { label: "Highest Rating", value: "1712" },
      ],
      [
        { label: "Solved", value: "461" },
        { label: "Contests", value: "19" },
      ],
    ],
    streak: "11 day streak",
    streakDots: [true, true, true, true, true, false, false, false, false, false],
  },
];

const weekdayLabels = ["M", "T", "W", "T", "F", "S", "S"];

function StatusBadge({ status }: { status: PlatformStatus }) {
  const className =
    status === "Verified"
      ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
      : "bg-orange-50 text-orange-700 ring-1 ring-orange-200";

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-[10px] font-semibold leading-none ${className}`}
    >
      {status}
    </span>
  );
}

function PlatformStatGrid({ rows }: { rows: PlatformStat[][] }) {
  return (
    <div className="mt-5 grid gap-4">
      {rows.map((row, index) => (
        <div
          className={`grid gap-3 ${row.length === 3 ? "grid-cols-3" : "grid-cols-2"}`}
          key={index}
        >
          {row.map((stat) => (
            <div className="min-w-0" key={`${stat.label}-${stat.value}`}>
              <p className="truncate text-[11px] font-medium text-slate-500">
                {stat.label}
              </p>
              <p
                className={`mt-1 truncate text-xl font-semibold leading-tight tracking-normal text-slate-950 ${stat.valueClassName ?? ""}`}
              >
                {stat.value}
              </p>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function StreakDots({ dots }: { dots: boolean[] }) {
  return (
    <div className="mt-3">
      <div className="grid grid-cols-10 gap-2">
        {dots.map((active, index) => (
          <span
            aria-hidden="true"
            className={`size-3 rounded-full ${
              active ? "bg-emerald-500" : "bg-slate-200"
            }`}
            key={`${active ? "active" : "inactive"}-${index}`}
          />
        ))}
      </div>
      <div className="mt-2 grid max-w-45 grid-cols-7 text-center text-[10px] font-medium text-slate-500">
        {weekdayLabels.map((label, index) => (
          <span key={`${label}-${index}`}>{label}</span>
        ))}
      </div>
    </div>
  );
}

function CompetitivePlatformCard({
  platform,
}: {
  platform: CompetitivePlatform;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_26px_rgba(15,23,42,0.035)] transition hover:-translate-y-0.5 hover:shadow-[0_16px_34px_rgba(15,23,42,0.07)]">
      <div className="flex items-start gap-3">
        <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-slate-50">
          <Image
            src={platform.logoSrc}
            alt={`${platform.name} logo`}
            width={48}
            height={48}
            className={`${platform.logoClassName} object-contain`}
          />
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 items-center gap-2">
            <h3 className="truncate text-sm font-semibold text-slate-950">
              {platform.name}
            </h3>
            <StatusBadge status={platform.status} />
          </div>
          <p className="mt-1 truncate text-[11px] font-medium text-slate-500">
            {platform.lastSynced}
          </p>
        </div>
      </div>

      <PlatformStatGrid rows={platform.statRows} />

      <div className="mt-5 border-t border-slate-100 pt-4">
        <div className="flex items-center gap-2">
          <Flame className="size-4 text-orange-500" />
          <p className="text-xs font-semibold text-slate-800">
            {platform.streak}
          </p>
        </div>
        <StreakDots dots={platform.streakDots} />
      </div>
    </article>
  );
}

export function CompetitivePlatformPerformance() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-sm font-semibold text-slate-950">
          Platform Performance
        </h2>
        <button
          type="button"
          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 transition hover:text-blue-800"
        >
          View All Platforms
          <ArrowRight className="size-3.5" />
        </button>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2 min-[1500px]:grid-cols-4">
        {platformPerformance.map((platform) => (
          <CompetitivePlatformCard key={platform.name} platform={platform} />
        ))}
      </div>
    </section>
  );
}
