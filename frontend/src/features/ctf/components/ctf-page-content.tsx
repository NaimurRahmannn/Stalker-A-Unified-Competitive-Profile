"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, RefreshCw, ShieldCheck } from "lucide-react";
import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { listPlatformAccounts, syncPlatformAccount } from "@/features/platforms/api";
import type { PlatformAccount } from "@/features/platforms/types";
import { useAuth } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/utils";
import { CTFOverview } from "./ctf-overview";
import { CTFtimeAnalyticsView } from "./ctftime-analytics-view";

type Tab = "overview" | "ctftime";

function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="hidden bg-white p-5 sm:p-6 lg:block lg:border-r lg:border-slate-200">
          <DashboardSidebar activeItem="ctf" />
        </aside>
        <div className="min-w-0 bg-slate-50">
          <DashboardMobileNav activeItem="ctf" />
          {children}
        </div>
      </div>
    </main>
  );
}

function PageHeader({ tab, onTabChange }: { tab: Tab; onTabChange: (tab: Tab) => void }) {
  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "overview", label: "Overview" },
    { id: "ctftime", label: "CTFtime" },
  ];
  return (
    <header>
      <div className="flex items-center gap-3">
        <h1 className="text-[25px] font-semibold leading-tight text-slate-950 sm:text-[28px]">CTF / Cybersecurity</h1>
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-600 ring-1 ring-blue-100"><ShieldCheck className="size-5" /></span>
      </div>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
        Track your CTFtime team profile and yearly rankings from data cached by STALKER.
      </p>
      <div role="tablist" aria-label="CTF platform" className="mt-5 inline-flex rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
        {tabs.map((item) => (
          <button key={item.id} type="button" role="tab" aria-selected={tab === item.id} onClick={() => onTabChange(item.id)} className={`h-9 rounded-lg px-4 text-xs font-semibold transition ${tab === item.id ? "bg-emerald-600 text-white" : "text-slate-600 hover:bg-slate-50"}`}>
            {item.label}
          </button>
        ))}
      </div>
    </header>
  );
}

function LoadingState({ tab, onTabChange }: { tab: Tab; onTabChange: (tab: Tab) => void }) {
  return (
    <DashboardShell>
      <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8"><PageHeader tab={tab} onTabChange={onTabChange} /></section>
      <div className="animate-pulse p-5 sm:p-6 lg:p-8">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {Array.from({ length: 4 }, (_, index) => <div key={index} className="h-25 rounded-2xl border border-slate-200 bg-white" />)}
        </div>
        <div className="mt-6 h-62 rounded-2xl border border-slate-200 bg-white" />
        <div className="mt-6 h-90 rounded-2xl border border-slate-200 bg-white" />
      </div>
    </DashboardShell>
  );
}

export function CTFPageContent() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [tab, setTab] = useState<Tab>("overview");
  const [account, setAccount] = useState<PlatformAccount | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  const loadAccount = useCallback(async () => {
    setIsLoading(true);
    try {
      const accounts = await listPlatformAccounts();
      const ctftime = accounts.find((item) => item.platform === "ctftime") ?? null;
      setAccount(ctftime);
      setCooldownSeconds(ctftime?.sync_cooldown_seconds ?? 0);
      setError(null);
      setSyncError(null);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Could not load your CTFtime team."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthLoading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    const timeout = window.setTimeout(() => void loadAccount(), 0);
    return () => window.clearTimeout(timeout);
  }, [isAuthLoading, loadAccount, router, user]);

  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const interval = window.setInterval(() => setCooldownSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(interval);
  }, [cooldownSeconds]);

  const handleSync = async () => {
    if (!account || isSyncing || cooldownSeconds > 0 || (!account.can_sync && account.sync_cooldown_seconds === 0)) return;
    setIsSyncing(true);
    setSyncError(null);
    try {
      const updated = await syncPlatformAccount(account.id);
      setAccount(updated);
      setCooldownSeconds(updated.sync_cooldown_seconds);
    } catch (syncFailure) {
      setSyncError(getApiErrorMessage(syncFailure, "Could not sync this CTFtime team."));
      try {
        const accounts = await listPlatformAccounts();
        const refreshed = accounts.find((item) => item.platform === "ctftime") ?? null;
        setAccount(refreshed);
        setCooldownSeconds(refreshed?.sync_cooldown_seconds ?? 0);
      } catch {
        // Keep the last team data and show the sync error.
      }
    } finally {
      setIsSyncing(false);
    }
  };

  if (isAuthLoading || (isLoading && !account && !error) || !user) {
    return <LoadingState tab={tab} onTabChange={setTab} />;
  }

  return (
    <DashboardShell>
      <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8"><PageHeader tab={tab} onTabChange={setTab} /></section>
      <div className="p-5 sm:p-6 lg:p-8">
        {error ? (
          <div role="alert" className="mb-5 flex flex-col gap-3 rounded-2xl border border-red-100 bg-red-50/70 px-4 py-3 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between">
            <span className="inline-flex items-center gap-2 font-medium"><AlertCircle className="size-4" />{error}{account ? " Cached data remains visible below." : ""}</span>
            <button type="button" onClick={() => void loadAccount()} className="inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-red-200 bg-white px-3 text-xs font-semibold"><RefreshCw className="size-4" />Retry</button>
          </div>
        ) : null}
        {syncError ? <p role="alert" className="mb-5 rounded-2xl border border-red-100 bg-red-50/70 px-4 py-3 text-sm text-red-700">{syncError}</p> : null}
        {account?.ctftime_sync_state?.status === "failed" && !syncError ? (
          <p className="mb-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">The last sync failed: {account.ctftime_sync_state.failure_reason.replaceAll("_", " ")}.</p>
        ) : null}
        {error && !account ? (
          <div className="rounded-2xl border border-slate-200 bg-white px-6 py-14 text-center"><p className="text-sm font-semibold text-slate-900">Analytics are unavailable</p><p className="mt-2 text-xs text-slate-500">Try again to load this view.</p></div>
        ) : tab === "overview" ? (
          <CTFOverview account={account} onView={() => setTab("ctftime")} />
        ) : (
          <CTFtimeAnalyticsView account={account} onSync={() => void handleSync()} isSyncing={isSyncing} cooldownSeconds={cooldownSeconds} />
        )}
      </div>
    </DashboardShell>
  );
}
