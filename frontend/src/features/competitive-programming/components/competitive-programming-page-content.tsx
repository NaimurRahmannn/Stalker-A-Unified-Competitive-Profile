"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { isAxiosError } from "axios";
import { useRouter } from "next/navigation";
import { AlertCircle, Code2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { syncPlatformAccount } from "@/features/platforms/api";
import { useAuth } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/utils";
import { getAtCoderAnalytics, getCodeforcesAnalytics, getCompetitiveProgrammingOverview } from "../api";
import type { AtCoderAnalyticsResponse, CodeforcesAnalyticsResponse, CompetitiveOverviewResponse } from "../types";
import { AtCoderAnalyticsView } from "./atcoder-analytics-view";
import { CodeforcesAnalyticsView } from "./codeforces-analytics-view";
import { CompetitiveOverview } from "./competitive-overview";

type Tab = "overview" | "codeforces" | "atcoder";

function DashboardShell({ children }: { children: ReactNode }) {
  return <main className="min-h-screen bg-slate-50 text-slate-900"><div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)]"><aside className="hidden bg-white p-5 sm:p-6 lg:block lg:border-r lg:border-slate-200"><DashboardSidebar activeItem="competitive-programming" /></aside><div className="min-w-0 bg-slate-50"><DashboardMobileNav activeItem="competitive-programming" />{children}</div></div></main>;
}

function PageHeader({ tab, onTabChange }: { tab: Tab; onTabChange: (tab: Tab) => void }) {
  const tabs: Array<{ id: Tab; label: string }> = [{ id: "overview", label: "Overview" }, { id: "codeforces", label: "Codeforces" }, { id: "atcoder", label: "AtCoder" }];
  return <header><div className="flex items-center gap-3"><h1 className="text-[25px] font-semibold leading-tight text-slate-950 sm:text-[28px]">Competitive Programming</h1><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100"><Code2 className="size-5" /></span></div><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">Track real Codeforces and AtCoder progress from data cached by STALKER.</p><div role="tablist" aria-label="Competitive programming platform" className="mt-5 inline-flex rounded-xl border border-slate-200 bg-white p-1 shadow-sm">{tabs.map((item) => <button key={item.id} type="button" role="tab" aria-selected={tab === item.id} onClick={() => onTabChange(item.id)} className={`h-9 rounded-lg px-4 text-xs font-semibold transition ${tab === item.id ? "bg-emerald-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}>{item.label}</button>)}</div></header>;
}

function LoadingState({ tab, onTabChange }: { tab: Tab; onTabChange: (tab: Tab) => void }) {
  return <DashboardShell><section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8"><PageHeader tab={tab} onTabChange={onTabChange} /></section><div className="animate-pulse p-5 sm:p-6 lg:p-8"><div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-25 rounded-2xl border border-slate-200 bg-white" />)}</div><div className="mt-6 h-62 rounded-2xl border border-slate-200 bg-white" /><div className="mt-6 h-90 rounded-2xl border border-slate-200 bg-white" /></div></DashboardShell>;
}

function retryAfterSeconds(error: unknown) {
  if (!isAxiosError(error) || error.response?.status !== 429) return null;
  const value = (error.response.data as { retry_after_seconds?: unknown } | undefined)?.retry_after_seconds;
  return typeof value === "number" && value > 0 ? Math.ceil(value) : null;
}

export function CompetitiveProgrammingPageContent() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [tab, setTab] = useState<Tab>("overview");
  const [overview, setOverview] = useState<CompetitiveOverviewResponse | null>(null);
  const [codeforces, setCodeforces] = useState<CodeforcesAnalyticsResponse | null>(null);
  const [atcoder, setAtCoder] = useState<AtCoderAnalyticsResponse | null>(null);
  const [errors, setErrors] = useState<Partial<Record<Tab, string>>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [syncing, setSyncing] = useState<Tab | null>(null);
  const [cooldowns, setCooldowns] = useState<Record<Exclude<Tab, "overview">, number>>({ codeforces: 0, atcoder: 0 });

  const loadAnalytics = useCallback(async () => {
    const results = await Promise.allSettled([getCompetitiveProgrammingOverview(), getCodeforcesAnalytics(), getAtCoderAnalytics()]);
    setOverview((current) => results[0].status === "fulfilled" ? results[0].value : current);
    setCodeforces((current) => {
      if (results[1].status === "fulfilled") return results[1].value;
      return current;
    });
    setAtCoder((current) => {
      if (results[2].status === "fulfilled") return results[2].value;
      return current;
    });
    setErrors({
      ...(results[0].status === "rejected" ? { overview: getApiErrorMessage(results[0].reason, "Could not load the competitive overview.") } : {}),
      ...(results[1].status === "rejected" ? { codeforces: getApiErrorMessage(results[1].reason, "Could not load Codeforces analytics.") } : {}),
      ...(results[2].status === "rejected" ? { atcoder: getApiErrorMessage(results[2].reason, "Could not load AtCoder analytics.") } : {}),
    });
    const codeforcesResult = results[1];
    const atcoderResult = results[2];
    if (codeforcesResult.status === "fulfilled") {
      const seconds = codeforcesResult.value.account?.sync_cooldown_seconds ?? 0;
      setCooldowns((value) => ({ ...value, codeforces: seconds }));
    }
    if (atcoderResult.status === "fulfilled") {
      const seconds = atcoderResult.value.account?.sync_cooldown_remaining_seconds ?? 0;
      setCooldowns((value) => ({ ...value, atcoder: seconds }));
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (isAuthLoading) return;
    if (!user) { router.replace("/login"); return; }
    const timeout = window.setTimeout(() => void loadAnalytics(), 0);
    return () => window.clearTimeout(timeout);
  }, [isAuthLoading, loadAnalytics, router, user]);

  useEffect(() => {
    if (!Object.values(cooldowns).some((value) => value > 0)) return;
    const interval = window.setInterval(() => setCooldowns((value) => ({ codeforces: Math.max(0, value.codeforces - 1), atcoder: Math.max(0, value.atcoder - 1) })), 1000);
    return () => window.clearInterval(interval);
  }, [cooldowns]);

  const handleSync = async (platform: Exclude<Tab, "overview">) => {
    const account = platform === "codeforces" ? codeforces?.account : atcoder?.account;
    if (!account || syncing || cooldowns[platform] > 0) return;
    setSyncing(platform);
    try {
      const result = await syncPlatformAccount(account.id);
      if (platform === "atcoder" && result.status === "partial") toast.warning("AtCoder partially updated. Cached data is still being shown for one source.");
      else if (platform === "atcoder" && result.sources && Object.values(result.sources).every((source) => source.status === "skipped_fresh")) toast.info("Your AtCoder data is already fresh.");
      else toast.success(`${platform === "atcoder" ? "AtCoder" : "Codeforces"} analytics updated.`);
      await loadAnalytics();
    } catch (syncError) {
      const retry = retryAfterSeconds(syncError);
      if (retry) setCooldowns((value) => ({ ...value, [platform]: retry }));
      toast.error(getApiErrorMessage(syncError, `Could not sync ${platform === "atcoder" ? "AtCoder" : "Codeforces"}. Please try again.`));
      await loadAnalytics();
    } finally { setSyncing(null); }
  };

  if (isAuthLoading || isLoading || !user) return <LoadingState tab={tab} onTabChange={setTab} />;
  const data = tab === "overview" ? overview : tab === "codeforces" ? codeforces : atcoder;
  const error = errors[tab];

  return <DashboardShell><section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8"><PageHeader tab={tab} onTabChange={setTab} /></section><div className="p-5 sm:p-6 lg:p-8">{error ? <div className="mb-5 flex flex-col gap-3 rounded-2xl border border-red-100 bg-red-50/70 px-4 py-3 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between"><span className="inline-flex items-center gap-2 font-medium"><AlertCircle className="size-4" />{error}{data ? " Cached data remains visible below." : ""}</span><button type="button" onClick={() => void loadAnalytics()} className="inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-red-200 bg-white px-3 text-xs font-semibold"><RefreshCw className="size-4" />Retry</button></div> : null}{tab === "overview" && overview ? <CompetitiveOverview overview={overview} onSelectPlatform={setTab} /> : null}{tab === "codeforces" && codeforces ? <CodeforcesAnalyticsView analytics={codeforces} onSync={() => void handleSync("codeforces")} isSyncing={syncing === "codeforces"} cooldownSeconds={cooldowns.codeforces} /> : null}{tab === "atcoder" && atcoder ? <AtCoderAnalyticsView analytics={atcoder} onSync={() => void handleSync("atcoder")} isSyncing={syncing === "atcoder"} cooldownSeconds={cooldowns.atcoder} /> : null}{!data ? <div className="rounded-2xl border border-slate-200 bg-white px-6 py-14 text-center"><p className="text-sm font-semibold text-slate-900">Analytics are unavailable</p><p className="mt-2 text-xs text-slate-500">Try again to load this view.</p></div> : null}</div></DashboardShell>;
}
