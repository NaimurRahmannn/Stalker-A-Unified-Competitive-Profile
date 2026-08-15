import Image from "next/image";
import Link from "next/link";
import { ArrowRight, BarChart3, CheckCircle2, Layers3, Target } from "lucide-react";
import type { CompetitiveOverviewResponse, CompetitivePlatformSummary } from "../types";
import { overviewActivity } from "../adapters";
import { CompetitiveActivityList } from "./competitive-activity-list";

const number = new Intl.NumberFormat("en");

function SummaryMetric({ label, value, note, icon: Icon, style }: { label: string; value: string; note?: string; icon: typeof Target; style: string }) {
  return <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.035)]"><div className="flex min-h-16 items-center gap-4"><span className={`grid size-12 shrink-0 place-items-center rounded-2xl ${style}`}><Icon className="size-5" /></span><div className="min-w-0"><strong className="block truncate text-2xl font-semibold text-slate-950">{value}</strong><span className="mt-1 block text-xs font-medium text-slate-600">{label}</span>{note ? <span className="mt-0.5 block text-[9px] text-amber-700">{note}</span> : null}</div></div></article>;
}

function PlatformCard({ platform, onView }: { platform: CompetitivePlatformSummary; onView: () => void }) {
  const name = platform.platform === "codeforces" ? "Codeforces" : "AtCoder";
  const logo = platform.platform === "codeforces" ? "/images/codeforces_logo.png" : "/images/atcoder_logo.png";
  if (!platform.connected) {
    return <article className="flex min-h-54 flex-col rounded-2xl border border-dashed border-slate-300 bg-white p-5"><div className="flex items-center gap-3"><span className="grid size-11 place-items-center rounded-2xl bg-slate-50"><Image src={logo} alt={`${name} logo`} width={32} height={32} className="size-8 object-contain" /></span><h3 className="font-semibold text-slate-950">{name}</h3></div><p className="mt-5 text-sm font-medium text-slate-700">Not connected</p><p className="mt-1 text-xs leading-5 text-slate-500">Connect {name} to include it in your competitive profile.</p><Link href="/platforms" className="mt-auto inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-emerald-200 text-xs font-semibold text-emerald-700 hover:bg-emerald-50">Connect {name}<ArrowRight className="size-3.5" /></Link></article>;
  }
  const solved = platform.solved_count === null ? "Not synced" : `${number.format(platform.solved_count)}${platform.solved_count_complete ? " solved" : "+ indexed"}`;
  return <article className="flex min-h-54 flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_30px_rgba(15,23,42,0.035)]"><div className="flex items-center gap-3"><span className="grid size-11 place-items-center rounded-2xl bg-slate-50"><Image src={logo} alt={`${name} logo`} width={32} height={32} className="size-8 object-contain" /></span><div><h3 className="font-semibold text-slate-950">{name}</h3><p className="text-[10px] text-slate-500">@{platform.handle}</p></div></div><div className="mt-5"><p className="text-2xl font-semibold capitalize text-slate-950">{platform.rating === null ? "Unrated" : number.format(platform.rating)}{platform.rank ? <span className="text-sm font-medium text-slate-500"> · {platform.rank}</span> : null}</p><p className="mt-2 text-xs font-medium text-slate-600">{solved}</p><p className="mt-1 text-xs text-slate-500">{platform.contest_count ?? "—"} {platform.contest_label.toLowerCase()}</p></div><button type="button" onClick={onView} className="mt-auto inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-emerald-200 text-xs font-semibold text-emerald-700 hover:bg-emerald-50">View analytics<ArrowRight className="size-3.5" /></button></article>;
}

export function CompetitiveOverview({ overview, onSelectPlatform }: { overview: CompetitiveOverviewResponse; onSelectPlatform: (platform: "codeforces" | "atcoder") => void }) {
  const summary = overview.summary;
  const hasIncompleteSolved = !summary.solved_count_complete;
  return <>
    {summary.active_platforms === 0 ? <div className="mb-6 rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center"><h2 className="text-lg font-semibold text-slate-950">Build your competitive programming profile</h2><p className="mx-auto mt-2 max-w-lg text-sm text-slate-500">Connect Codeforces or AtCoder to bring your real competitive progress into one place.</p><Link href="/platforms" className="mt-5 inline-flex h-10 items-center rounded-xl bg-emerald-600 px-5 text-xs font-semibold text-white">Connect a platform</Link></div> : null}
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <SummaryMetric label={hasIncompleteSolved ? "Known Problems Solved" : "Problems Solved"} value={`${number.format(summary.solved_count)}${hasIncompleteSolved ? "+" : ""}`} note={hasIncompleteSolved ? "AtCoder history still indexing" : undefined} icon={Target} style="bg-emerald-50 text-emerald-600" />
      <SummaryMetric label="Tracked Contest Participations" value={number.format(summary.contest_count)} icon={BarChart3} style="bg-blue-50 text-blue-600" />
      <SummaryMetric label="Active Platforms" value={number.format(summary.active_platforms)} icon={Layers3} style="bg-violet-50 text-violet-600" />
      <SummaryMetric label={summary.accepted_submission_count_complete ? "Accepted Submissions" : "Known Accepted Submissions"} value={`${number.format(summary.accepted_submission_count)}${summary.accepted_submission_count_complete ? "" : "+"}`} icon={CheckCircle2} style="bg-orange-50 text-orange-600" />
    </div>
    <section className="mt-6"><h2 className="text-sm font-semibold text-slate-950">Platform Performance</h2><div className="mt-3 grid gap-4 md:grid-cols-2">{overview.platforms.map((platform) => <PlatformCard key={platform.platform} platform={platform} onView={() => onSelectPlatform(platform.platform)} />)}</div></section>
    <div className="mt-6"><CompetitiveActivityList title="Recent Competitive Activity" activity={overviewActivity(overview)} showPlatform /></div>
  </>;
}
