"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { isAxiosError } from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertCircle, BarChart3, Code2, RefreshCw, Target, Trophy } from "lucide-react";
import { toast } from "sonner";
import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { syncPlatformAccount } from "@/features/platforms/api";
import { useAuth } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/utils";
import { getCodeforcesAnalytics } from "../api";
import type { CodeforcesAnalyticsResponse } from "../types";
import { CodeforcesGrowthSummary } from "./codeforces-growth-summary";
import { CodeforcesPerformanceCard } from "./codeforces-performance-card";
import { RatingProgressChart } from "./rating-progress-chart";
import { RecentCodeforcesActivity } from "./recent-codeforces-activity";

function DashboardShell({ children }: { children: ReactNode }) {
  return <main className="min-h-screen bg-slate-50 text-slate-900"><div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)]"><aside className="hidden bg-white p-5 sm:p-6 lg:block lg:border-r lg:border-slate-200"><DashboardSidebar activeItem="competitive-programming" /></aside><div className="min-w-0 bg-slate-50"><DashboardMobileNav activeItem="competitive-programming" />{children}</div></div></main>;
}

function PageHeader() {
  return <header><div className="flex items-center gap-3"><h1 className="text-[25px] font-semibold leading-tight text-slate-950 sm:text-[28px]">Competitive Programming</h1><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100"><Code2 className="size-5" /></span></div><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">Real Codeforces rating, contest, problem-solving, and submission analytics.</p></header>;
}

function LoadingState() {
  return <DashboardShell><section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8"><PageHeader /></section><div className="animate-pulse p-5 sm:p-6 lg:p-8"><div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-25 rounded-2xl border border-slate-200 bg-white" />)}</div><div className="mt-6 h-62 rounded-2xl border border-slate-200 bg-white" /><div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]"><div className="h-90 rounded-2xl border border-slate-200 bg-white" /><div className="h-72 rounded-2xl border border-slate-200 bg-white" /></div></div></DashboardShell>;
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <DashboardShell><section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8"><PageHeader /></section><div className="p-5 sm:p-6 lg:p-8"><div className="rounded-2xl border border-red-100 bg-white px-6 py-14 text-center shadow-sm"><span className="mx-auto grid size-12 place-items-center rounded-2xl bg-red-50 text-red-600"><AlertCircle className="size-6" /></span><h2 className="mt-4 text-base font-semibold text-slate-950">Could not load Codeforces analytics</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">{message}</p><button type="button" onClick={onRetry} className="mt-5 inline-flex h-10 items-center gap-2 rounded-xl bg-emerald-600 px-4 text-xs font-semibold text-white hover:bg-emerald-700"><RefreshCw className="size-4" />Try again</button></div></div></DashboardShell>;
}

function EmptyState() {
  return <DashboardShell><section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8"><PageHeader /></section><div className="p-5 sm:p-6 lg:p-8"><div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-18 text-center shadow-sm"><span className="mx-auto grid size-14 place-items-center rounded-2xl bg-emerald-50 text-emerald-600"><Code2 className="size-7" /></span><h2 className="mt-5 text-lg font-semibold text-slate-950">Connect Codeforces to begin</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">Add your Codeforces handle, then sync it to load real rating history, solved problems, contests, and recent submissions.</p><Link href="/platforms" className="mt-6 inline-flex h-10 items-center rounded-xl bg-emerald-600 px-5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700">Connect Codeforces</Link></div></div></DashboardShell>;
}

const metricConfig = [
  { key: "solved", label: "Problems Solved", Icon: Target, style: "bg-emerald-50 text-emerald-600" },
  { key: "contests", label: "Contests", Icon: BarChart3, style: "bg-blue-50 text-blue-600" },
  { key: "rating", label: "Current Rating", Icon: Code2, style: "bg-violet-50 text-violet-600" },
  { key: "max", label: "Max Rating", Icon: Trophy, style: "bg-orange-50 text-orange-600" },
] as const;

function SummaryMetrics({ analytics }: { analytics: CodeforcesAnalyticsResponse }) {
  const stats = analytics.stats;
  const values = { solved: stats ? String(stats.solved_count) : "—", contests: stats ? String(stats.contest_count) : "—", rating: stats ? (stats.rating === null ? "Unrated" : String(stats.rating)) : "—", max: stats ? (stats.max_rating === null ? "Unrated" : String(stats.max_rating)) : "—" };
  return <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{metricConfig.map(({ key, label, Icon, style }) => <article key={key} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.035)]"><div className="flex min-h-16 items-center gap-4"><span className={`grid size-12 shrink-0 place-items-center rounded-2xl ${style}`}><Icon className="size-5" /></span><div className="min-w-0"><strong className="block truncate text-2xl font-semibold text-slate-950">{values[key]}</strong><span className="mt-1 block truncate text-xs font-medium text-slate-600">{label}</span></div></div></article>)}</div>;
}

function retryAfterSeconds(error: unknown) {
  if (!isAxiosError(error) || error.response?.status !== 429) return null;
  const value = (error.response.data as { retry_after_seconds?: unknown } | undefined)?.retry_after_seconds;
  return typeof value === "number" && value > 0 ? Math.ceil(value) : null;
}

export function CompetitiveProgrammingPageContent() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [analytics, setAnalytics] = useState<CodeforcesAnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getCodeforcesAnalytics();
      setAnalytics(data);
      setCooldownSeconds(data.account?.sync_cooldown_seconds ?? 0);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "The analytics service is unavailable."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthLoading) return;
    if (!user) { router.replace("/login"); return; }
    let cancelled = false;
    void getCodeforcesAnalytics().then((data) => { if (!cancelled) { setAnalytics(data); setCooldownSeconds(data.account?.sync_cooldown_seconds ?? 0); setError(null); } }).catch((requestError: unknown) => { if (!cancelled) setError(getApiErrorMessage(requestError, "The analytics service is unavailable.")); }).finally(() => { if (!cancelled) setIsLoading(false); });
    return () => { cancelled = true; };
  }, [isAuthLoading, router, user]);

  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const interval = window.setInterval(() => setCooldownSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(interval);
  }, [cooldownSeconds]);

  const handleSync = async () => {
    const account = analytics?.account;
    if (!account || isSyncing || cooldownSeconds > 0) return;
    setIsSyncing(true);
    try {
      await syncPlatformAccount(account.id);
      toast.success("Codeforces analytics updated");
      const data = await getCodeforcesAnalytics();
      setAnalytics(data);
      setCooldownSeconds(data.account?.sync_cooldown_seconds ?? 0);
    } catch (syncError) {
      const retry = retryAfterSeconds(syncError);
      if (retry) setCooldownSeconds(retry);
      toast.error(getApiErrorMessage(syncError, "Could not sync Codeforces. Please try again."));
    } finally {
      setIsSyncing(false);
    }
  };

  if (isAuthLoading || isLoading) return <LoadingState />;
  if (!user) return <LoadingState />;
  if (error || !analytics) return <ErrorState message={error ?? "No analytics response was returned."} onRetry={() => void loadAnalytics()} />;
  if (!analytics.account) return <EmptyState />;

  return <DashboardShell><section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8"><PageHeader /></section><div className="p-5 sm:p-6 lg:p-8"><SummaryMetrics analytics={analytics} /><div className="mt-6"><CodeforcesPerformanceCard account={analytics.account} stats={analytics.stats} onSync={() => void handleSync()} isSyncing={isSyncing} cooldownSeconds={cooldownSeconds} /></div><div className="mt-6 grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_340px]"><div className="min-w-0 space-y-6"><RatingProgressChart history={analytics.rating_history} /><RecentCodeforcesActivity activity={analytics.recent_activity} /></div><CodeforcesGrowthSummary account={analytics.account} snapshots={analytics.snapshots} historyCount={analytics.rating_history.length} /></div></div></DashboardShell>;
}
