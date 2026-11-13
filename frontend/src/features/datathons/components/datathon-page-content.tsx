"use client";

import { useCallback, useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { isAxiosError } from "axios";
import { useRouter } from "next/navigation";
import { AlertCircle, BarChart3, Clock3, Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { connectPlatformAccount, deletePlatformAccount, listPlatformAccounts, updatePlatformAccount } from "@/features/platforms/api";
import type { PlatformAccount } from "@/features/platforms/types";
import { useAuth } from "@/hooks/use-auth";
import type { User } from "@/features/auth/types";
import { getApiErrorMessage } from "@/lib/utils";
import { getKaggleCapabilities, getKaggleOverview, getKaggleSyncStatus, requestKaggleSync } from "../api";
import { formatRank, formatTier, formatTimestamp } from "../formatters";
import type { KaggleCapabilitiesResponse, KaggleCollectionRunStatus, KaggleOverviewResponse, KaggleSyncStatusResponse } from "../types";
import { KaggleAccountPanel } from "./kaggle-account-panel";
import { KaggleManualEditor } from "./kaggle-manual-editor";
import { KaggleTierIcon } from "./kaggle-tier-icon";
import { KaggleTrackCard } from "./kaggle-track-card";

type Tab = "overview" | "kaggle";
const activeStatuses: KaggleCollectionRunStatus[] = ["queued", "running", "retrying"];

function Shell({ children }: { children: ReactNode }) {
  return <main className="min-h-screen bg-slate-50 text-slate-900"><div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-x-clip lg:grid-cols-[300px_minmax(0,1fr)]"><aside className="hidden bg-white p-5 sm:p-6 lg:sticky lg:top-0 lg:block lg:h-dvh lg:self-start lg:overflow-y-auto lg:overscroll-y-contain lg:[scrollbar-width:thin] lg:border-r lg:border-slate-200"><DashboardSidebar activeItem="datathon" /></aside><div className="min-w-0 bg-slate-50"><DashboardMobileNav activeItem="datathon" />{children}</div></div></main>;
}

function Header({ tab, setTab }: { tab: Tab; setTab: (tab: Tab) => void }) {
  function onTabKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    const target = event.key === "ArrowLeft" || event.key === "Home" ? "overview" : event.key === "ArrowRight" || event.key === "End" ? "kaggle" : null;
    if (!target) return;
    event.preventDefault();
    setTab(target);
    document.getElementById(`datathon-tab-${target}`)?.focus();
  }
  return <header className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8"><div className="flex items-center gap-3"><h1 className="text-[25px] font-semibold leading-tight text-slate-950 sm:text-[28px]">Datathon / Data Science</h1><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-[#E8F8FE] text-[#087EA4] ring-1 ring-sky-100"><BarChart3 className="size-5" /></span></div><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">Track your Kaggle rankings, tiers, and medals with manual entries for your linked account.</p><div role="tablist" aria-label="Datathon views" className="mt-5 inline-flex rounded-xl border border-slate-200 bg-white p-1 shadow-sm">{(["overview", "kaggle"] as const).map((item) => <button key={item} id={`datathon-tab-${item}`} type="button" role="tab" aria-controls={`datathon-panel-${item}`} aria-selected={tab === item} tabIndex={tab === item ? 0 : -1} onClick={() => setTab(item)} onKeyDown={onTabKeyDown} className={`h-9 rounded-lg px-4 text-xs font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#20BEFF] ${tab === item ? "bg-[#20BEFF] text-slate-950 font-bold shadow-sm" : "text-slate-600 hover:bg-slate-50"}`}>{item === "overview" ? "Overview" : "Kaggle"}</button>)}</div></header>;
}

function LoadingCards() {
  return <div className="animate-pulse space-y-5" role="status" aria-label="Loading Datathon dashboard"><div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }, (_, i) => <div key={i} className="h-28 rounded-2xl border border-slate-200 bg-white" />)}</div><div className="h-52 rounded-2xl border border-slate-200 bg-white" /><span className="sr-only">Loading Datathon dashboard</span></div>;
}

function OverviewCards({ overview }: { overview: KaggleOverviewResponse }) {
  const collected = overview.last_successful_at !== null;
  const manual = overview.manual_tracks ?? { competitions: null, code: null, datasets: null };
  const display = (track: "competitions" | "code" | "datasets") => manual[track] ?? overview.tracks[track];
  const available = (track: "competitions" | "code" | "datasets") => !!manual[track] || collected;
  const rankValue = (track: "competitions" | "code" | "datasets") => available(track) ? formatRank(display(track).global_rank, display(track).rank_status, true) : "Not entered";
  const anyManual = Object.values(manual).some(Boolean);
  const rows = [
    { label: "Competition global rank", value: rankValue("competitions"), manual: !!manual.competitions },
    { label: "Competition tier", value: available("competitions") ? formatTier(display("competitions").tier) : "Not entered", manual: !!manual.competitions, tier: display("competitions").tier },
    { label: "Code global rank", value: rankValue("code"), manual: !!manual.code },
    { label: "Dataset global rank", value: rankValue("datasets"), manual: !!manual.datasets },
  ];
  return <><div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">{rows.map((row) => <article key={row.label} className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-sky-200 hover:shadow-md"><p className="text-xs font-medium text-slate-500">{row.label}</p><p className="mt-3 flex items-center gap-2 break-words text-2xl font-semibold text-slate-950">{row.tier && <KaggleTierIcon tier={row.tier} className="size-7 shrink-0" />}{row.value}</p>{row.manual && <p className="mt-2 text-xs font-medium text-[#087EA4]">Self reported</p>}</article>)}</div><div className="mt-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h2 className="text-lg font-semibold text-slate-950">Kaggle overview</h2>{anyManual && <p className="mt-2 text-sm text-slate-600">Your manual entries are self reported and unverified. Edit them in the Kaggle tab.</p>}{collected && <p className="mt-2 text-xs text-slate-500">Collected rankings may not reflect recent Kaggle changes. Last collected: {formatTimestamp(overview.last_successful_at)}.</p>}{!collected && !anyManual && <p className="mt-2 text-sm text-slate-600">Your Kaggle profile is linked. Enter your rankings in the Kaggle tab to get started.</p>}{overview.collection_status === "failed" && <p className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">The latest collection attempt failed. Previously cached statistics remain visible.</p>}</div></>;
}

export function syncErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 429) {
      const seconds = (error.response?.data as { retry_after_seconds?: unknown } | undefined)?.retry_after_seconds;
      return typeof seconds === "number" && seconds > 0 ? `Sync cooldown is active. Try again in ${Math.ceil(seconds)} seconds.` : "Sync cooldown is active. Try again later.";
    }
    if (status === 503) return "Kaggle collection is unavailable right now.";
    if (status === 404) return "Link a Kaggle account before syncing.";
    if (status === 409) return "The Kaggle account link needs correction. Try reconnecting it.";
    if (status === 401 || status === 403) return "Your session cannot request this sync. Please sign in again.";
    if (status === 400) return "This sync request could not be accepted.";
  }
  return "Could not request Kaggle collection. Please try again.";
}

export function KaggleRunPanel({ capabilities, run, account, syncing, pollError, onSync }: {
  capabilities: KaggleCapabilitiesResponse | null; run: KaggleSyncStatusResponse | null;
  account: PlatformAccount; syncing: boolean; pollError: string | null; onSync: () => void;
}) {
  const status = run?.status ?? "not_started";
  const messages: Record<KaggleCollectionRunStatus, string> = {
    not_started: "No collection has been requested.", queued: "Waiting for collection worker.", running: "Collecting profile statistics.", retrying: "Collection temporarily failed. A retry is scheduled.", succeeded: "Statistics collection completed.", failed: "Collection failed. Previously cached data is still available.", cancelled: "Collection was cancelled.",
  };
  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="kaggle-sync-heading"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><h2 id="kaggle-sync-heading" className="text-lg font-semibold text-slate-950">Collection status</h2><p className="mt-1 text-sm text-slate-600">{messages[status]}</p>{run?.status === "retrying" && run.next_attempt_at && <p className="mt-1 text-xs text-slate-500">Next retry: {formatTimestamp(run.next_attempt_at)}</p>}{run?.run_id && <p className="mt-1 text-xs text-slate-500">Run #{run.run_id} · {status}</p>}</div>{capabilities?.can_request_sync ? <button type="button" onClick={onSync} disabled={syncing || activeStatuses.includes(status)} className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-[#20BEFF] px-4 text-sm font-semibold text-slate-950 shadow-sm hover:bg-[#1bb0ee] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#20BEFF] disabled:cursor-not-allowed disabled:opacity-50">{syncing ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}Sync Kaggle Statistics</button> : null}</div>{!capabilities?.can_request_sync && <div className="mt-4 rounded-xl border border-sky-100 bg-[#E8F8FE]/70 p-4 text-sm text-sky-950"><p className="font-semibold text-slate-950">Kaggle synchronization is not available yet.</p><p className="mt-1 text-slate-600">Your Kaggle account is linked, but automatic ranking collection is not currently enabled. Existing cached statistics remain available.</p></div>}{pollError && <p role="alert" className="mt-3 text-sm text-red-700">{pollError}</p>}<p className="mt-3 text-xs text-slate-500">Linked as @{account.handle}. A queued run does not mean rankings are updated.</p></section>;
}

export function DatathonPageContent() {
  const router = useRouter();
  const { user, isLoading: authLoading, logout } = useAuth();
  const [tab, setTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [account, setAccount] = useState<PlatformAccount | null>(null);
  const [overview, setOverview] = useState<KaggleOverviewResponse | null>(null);
  const [capabilities, setCapabilities] = useState<KaggleCapabilitiesResponse | null>(null);
  const [run, setRun] = useState<KaggleSyncStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [pollStopped, setPollStopped] = useState(false);
  const [loadedOwnerId, setLoadedOwnerId] = useState<User["id"] | null>(null);
  const generation = useRef(0);
  const ownerId = useRef<User["id"] | null>(null);
  const identity = useRef<string | null>(null);
  const pollCount = useRef(0);
  const pollFailures = useRef(0);
  const syncLock = useRef(false);
  const mutationLock = useRef(false);

  const handleExpiredSession = useCallback((requestError: unknown) => {
    if (isAxiosError(requestError) && requestError.response?.status === 401) {
      logout();
      router.replace("/login");
      return true;
    }
    return false;
  }, [logout, router]);

  const loadData = useCallback(async (requestedOwnerId: User["id"]) => {
    const version = ++generation.current;
    if (ownerId.current !== requestedOwnerId) {
      ownerId.current = requestedOwnerId;
      identity.current = null;
      syncLock.current = false;
      setSyncing(false);
      setAccount(null);
      setOverview(null);
      setRun(null);
      setCapabilities(null);
      setLoadedOwnerId(requestedOwnerId);
    }
    setLoading(true);
    setError(null);
    try {
      const [accountsResult, abilityResult] = await Promise.allSettled([listPlatformAccounts(), getKaggleCapabilities()]);
      if (version !== generation.current) return;
      if (accountsResult.status === "rejected") throw accountsResult.reason;
      const accounts = accountsResult.value;
      if (abilityResult.status === "fulfilled") setCapabilities(abilityResult.value);
      else {
        if (handleExpiredSession(abilityResult.reason)) return;
        setCapabilities(null);
        setError("Could not check whether Kaggle collection is available.");
      }
      const linked = accounts.find((item) => item.platform === "kaggle") ?? null;
      const key = linked ? `${linked.id}:${linked.handle}` : null;
      if (key !== identity.current) {
        identity.current = key;
        setOverview(null);
        setRun(null);
        setPollError(null);
        setPollStopped(false);
        pollCount.current = 0;
        pollFailures.current = 0;
      }
      setAccount(linked);
      if (!linked) return;
      const results = await Promise.allSettled([getKaggleOverview(), getKaggleSyncStatus()]);
      if (version !== generation.current || identity.current !== key) return;
      if (results[0].status === "fulfilled") setOverview(results[0].value);
      else {
        if (handleExpiredSession(results[0].reason)) return;
        setError(getApiErrorMessage(results[0].reason, "Could not load cached Kaggle rankings."));
      }
      if (results[1].status === "fulfilled") setRun(results[1].value);
      else {
        if (handleExpiredSession(results[1].reason)) return;
        setError((current) => current ?? "Could not load Kaggle collection status.");
      }
    } catch (loadError) {
      if (version === generation.current && !handleExpiredSession(loadError)) setError(getApiErrorMessage(loadError, "Could not load your Kaggle account."));
    } finally {
      if (version === generation.current) setLoading(false);
    }
  }, [handleExpiredSession]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      generation.current++;
      identity.current = null;
      router.replace("/login");
      return;
    }
    const timer = window.setTimeout(() => void loadData(user.id), 0);
    const activeGeneration = generation;
    return () => { window.clearTimeout(timer); activeGeneration.current++; };
  }, [authLoading, user?.id, router, loadData, user]);

  async function mutateAccount(operation: () => Promise<void>, success: string) {
    if (mutationLock.current || !user) return;
    mutationLock.current = true;
    setBusy(true);
    generation.current++;
    identity.current = null;
    syncLock.current = false;
    setSyncing(false);
    setOverview(null);
    setRun(null);
    setPollError(null);
    setPollStopped(false);
    try {
      await operation();
      await loadData(user.id);
      toast.success(success);
    } catch (mutationError) {
      if (handleExpiredSession(mutationError)) throw mutationError;
      const message = getApiErrorMessage(mutationError, "Could not change the Kaggle account.");
      toast.error(message);
      await loadData(user.id);
      setError(message);
      throw mutationError;
    } finally {
      mutationLock.current = false;
      setBusy(false);
    }
  }

  const accountKey = account ? `${account.id}:${account.handle}` : null;
  useEffect(() => {
    if (!accountKey || !run || !activeStatuses.includes(run.status) || pollStopped || authLoading || !user) return;
    const version = generation.current;
    const expectedRun = run.run_id;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      if (cancelled || version !== generation.current || identity.current !== accountKey) return;
      if (document.hidden) { setRun((current) => current ? { ...current } : current); return; }
      if (++pollCount.current > 120) { setPollStopped(true); setPollError("Collection is taking longer than expected. Reload this page to check again."); return; }
      try {
        const next = await getKaggleSyncStatus();
        if (cancelled || version !== generation.current || identity.current !== accountKey) return;
        if (next.run_id !== expectedRun) { setPollStopped(true); setPollError("A newer collection run was found. Reload this page to see its status."); return; }
        pollFailures.current = 0;
        setRun(next);
        if (next.status === "succeeded") {
          const fresh = await getKaggleOverview();
          if (!cancelled && version === generation.current && identity.current === accountKey) setOverview(fresh);
        }
      } catch (statusError) {
        if (cancelled || version !== generation.current || identity.current !== accountKey) return;
        if (handleExpiredSession(statusError)) return;
        if (++pollFailures.current >= 3) { setPollStopped(true); setPollError("Could not check collection status. Reload this page to try again."); }
        else setRun((current) => current ? { ...current } : current);
      }
    }, 5000);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [accountKey, run, pollStopped, authLoading, user, handleExpiredSession]);

  async function handleSync() {
    if (!account || !capabilities?.can_request_sync || syncLock.current || (run && activeStatuses.includes(run.status))) return;
    syncLock.current = true;
    setSyncing(true);
    setPollError(null);
    const version = generation.current;
    const key = accountKey;
    try {
      const response = await requestKaggleSync();
      if (version !== generation.current || identity.current !== key) return;
      pollCount.current = 0;
      pollFailures.current = 0;
      setPollStopped(false);
      setRun({ run_id: response.run_id, username: response.username, status: response.status, queued_at: response.queued_at });
      toast.info(response.deduplicated ? "An existing Kaggle collection run is still active." : "Kaggle collection was queued.");
    } catch (syncError) {
      if (version !== generation.current || identity.current !== key) return;
      if (handleExpiredSession(syncError)) return;
      const message = syncErrorMessage(syncError);
      setPollError(message);
      toast.error(message);
    } finally {
      if (version === generation.current) {
        syncLock.current = false;
        setSyncing(false);
      }
    }
  }

  if (authLoading || !user || loadedOwnerId !== user.id) return <Shell><Header tab={tab} setTab={setTab} /><div className="p-5 sm:p-6 lg:p-8"><LoadingCards /></div></Shell>;
  return <Shell><Header tab={tab} setTab={setTab} /><div className="space-y-5 p-5 sm:p-6 lg:p-8">{error && <div role="alert" className="flex flex-col gap-3 rounded-2xl border border-red-100 bg-red-50/70 px-4 py-3 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between"><span className="inline-flex items-center gap-2"><AlertCircle className="size-4 shrink-0" />{error}{overview ? " Cached statistics remain visible below." : ""}</span><button type="button" onClick={() => void loadData(user.id)} className="inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-red-200 bg-white px-3 text-xs font-semibold focus-visible:outline-2 focus-visible:outline-red-600"><RefreshCw className="size-4" />Retry</button></div>}{loading && !account && !error ? <LoadingCards /> : <><KaggleAccountPanel account={account} lastSuccessfulAt={overview?.last_successful_at ?? null} busy={busy} onConnect={(handle) => mutateAccount(async () => { await connectPlatformAccount({ platform: "kaggle", handle }); }, "Kaggle account linked. Add your rankings in the Kaggle tab.")} onChange={(handle) => mutateAccount(async () => { if (account) await updatePlatformAccount(account.id, handle); }, "Kaggle username updated.")} onDisconnect={async () => { if (!account || !window.confirm(`Disconnect Kaggle account @${account.handle}?`)) return; await mutateAccount(async () => { await deletePlatformAccount(account.id); }, "Kaggle account disconnected."); }} />{account ? <><div id="datathon-panel-overview" role="tabpanel" aria-labelledby="datathon-tab-overview" hidden={tab !== "overview"}>{overview ? <OverviewCards overview={overview} /> : loading ? <LoadingCards /> : <p className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">Kaggle ranking data is unavailable. Try again.</p>}</div><div id="datathon-panel-kaggle" role="tabpanel" aria-labelledby="datathon-tab-kaggle" hidden={tab !== "kaggle"} className="space-y-5">{overview && <KaggleManualEditor overview={overview} onChanged={async () => { setOverview(await getKaggleOverview()); }} />}{capabilities?.can_request_sync && <KaggleRunPanel capabilities={capabilities} run={run} account={account} syncing={syncing} pollError={pollError} onSync={() => void handleSync()} />}{overview ? <section aria-labelledby="kaggle-ranking-heading"><div className="mb-3 flex flex-wrap items-center justify-between gap-2"><h2 id="kaggle-ranking-heading" className="text-lg font-semibold text-slate-950">Kaggle ranking tracks</h2>{overview.last_successful_at && <p className="inline-flex items-center gap-1 text-xs text-slate-500"><Clock3 className="size-3.5" />Last successful collection: {formatTimestamp(overview.last_successful_at)}</p>}</div>{overview.collection_status === "failed" && <p className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">The latest collection attempt failed. Previously cached statistics remain visible.</p>}<div className="grid grid-cols-1 gap-4 md:grid-cols-2 2xl:grid-cols-3">{(["competitions", "code", "datasets"] as const).map((track) => <KaggleTrackCard key={track} track={track} statistics={overview.manual_tracks?.[track] ?? overview.tracks[track]} collected={!!overview.manual_tracks?.[track] || overview.last_successful_at !== null} manual={!!overview.manual_tracks?.[track]} />)}</div></section> : loading ? <LoadingCards /> : null}</div></> : <p className="rounded-2xl border border-sky-100 bg-[#E8F8FE]/70 p-4 text-sm text-slate-800">Connect a Kaggle account to enter and view your Competition, Code, and Dataset rankings.</p>}</>}</div></Shell>;
}
