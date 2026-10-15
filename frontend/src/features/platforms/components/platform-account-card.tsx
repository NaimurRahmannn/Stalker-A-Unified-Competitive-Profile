"use client";

import { useEffect, useState, type ReactNode } from "react";
import Image from "next/image";
import {
  ExternalLink,
  Loader2,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import type { PlatformAccount } from "@/features/platforms/types";
import { formatPlatformName, formatRelativeTime } from "@/lib/utils";

type PlatformAccountCardProps = {
  account: PlatformAccount;
  onSync: (id: number) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
};

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/70 px-3 py-2">
      <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-slate-500">{label}</p>
      <p className="mt-0.5 truncate text-sm font-semibold capitalize text-slate-950">{value}</p>
    </div>
  );
}

function ProviderStats({ account }: { account: PlatformAccount }) {
  if (account.platform === "codeforces" && account.codeforces_stats) {
    const stats = account.codeforces_stats;
    return (
      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <StatTile label="Rating" value={stats.rating === null ? "Unrated" : String(stats.rating)} />
        <StatTile label="Max rating" value={stats.max_rating === null ? "Unrated" : String(stats.max_rating)} />
        <StatTile label="Rank" value={stats.rank ?? "Unranked"} />
        <StatTile label="Solved" value={String(stats.solved_count)} />
      </div>
    );
  }

  if (account.platform === "atcoder" && account.atcoder_stats) {
    const stats = account.atcoder_stats;
    return (
      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <StatTile label="Current rating" value={stats.current_rating === null ? "Unrated" : String(stats.current_rating)} />
        <StatTile label="Max rating" value={stats.max_rating === null ? "Unrated" : String(stats.max_rating)} />
        <StatTile label="Color" value={stats.rating_color ?? "Unrated"} />
        <StatTile label="Solved" value={`${stats.solved_count}${stats.submission_backfill_complete ? "" : " indexed"}`} />
      </div>
    );
  }

  if (account.platform === "leetcode" && account.leetcode_stats) {
    const stats = account.leetcode_stats;
    return (
      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <StatTile label="Total solved" value={String(stats.solved_total)} />
        <StatTile label="Easy / Med / Hard" value={`${stats.solved_easy} / ${stats.solved_medium} / ${stats.solved_hard}`} />
        <StatTile label="Contest rating" value={stats.current_contest_rating === null ? "Unrated" : String(Math.round(stats.current_contest_rating))} />
        <StatTile label="Contests" value={String(stats.attended_contest_count)} />
      </div>
    );
  }

  if (account.platform === "ctftime" && account.ctf_team_profile) {
    const profile = account.ctf_team_profile;
    const latest = profile.yearly_rankings[0];
    return (
      <div className="mt-4">
        <p className="text-sm font-semibold text-slate-900">
          {profile.name}{profile.country ? ` · ${profile.country}` : ""}
        </p>
        {latest ? (
          <>
            <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
              <StatTile label={`${latest.year} rating`} value={latest.rating_points.toFixed(2)} />
              <StatTile label="Global rank" value={latest.global_rank === null ? "Unranked" : `#${latest.global_rank}`} />
              <StatTile label="Country rank" value={latest.country_rank === null ? "Unranked" : `#${latest.country_rank}`} />
              <StatTile label="Ranked years" value={String(profile.yearly_rankings.length)} />
            </div>
            <details className="mt-3 rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-700">
              <summary className="cursor-pointer font-semibold">Yearly rankings</summary>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full min-w-105 text-left">
                  <thead className="text-[10px] uppercase text-slate-500">
                    <tr><th className="pb-2">Year</th><th className="pb-2">Global</th><th className="pb-2">Country</th><th className="pb-2">Rating</th><th className="pb-2">Organizer</th></tr>
                  </thead>
                  <tbody>
                    {profile.yearly_rankings.map((ranking) => (
                      <tr key={ranking.year} className="border-t border-slate-100">
                        <td className="py-2 font-medium">{ranking.year}</td>
                        <td className="py-2">{ranking.global_rank === null ? "—" : `#${ranking.global_rank}`}</td>
                        <td className="py-2">{ranking.country_rank === null ? "—" : `#${ranking.country_rank}`}</td>
                        <td className="py-2">{ranking.rating_points.toFixed(2)}</td>
                        <td className="py-2">{ranking.organizer_points.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </>
        ) : (
          <p className="mt-2 text-xs text-slate-500">No yearly ranking is available for this team yet.</p>
        )}
      </div>
    );
  }

  return (
    <p className="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/70 px-3 py-2.5 text-xs font-medium text-slate-500">
      {account.platform === "ctftime"
        ? "This team has not been synced yet. Run a sync to load its profile and rankings."
        : `${formatPlatformName(account.platform)} is connected but has not been synced yet. Run a sync to validate the handle and load real stats.`}
    </p>
  );
}

function StatusBadge({ valid, children }: { valid: boolean; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold ${valid ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200" : "bg-orange-50 text-orange-700 ring-1 ring-orange-200"}`}>
      {valid ? <ShieldCheck className="size-3.5" /> : <ShieldAlert className="size-3.5" />}
      {children}
    </span>
  );
}

export function PlatformAccountCard({ account, onSync, onDelete }: PlatformAccountCardProps) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(account.sync_cooldown_seconds);

  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const intervalId = window.setInterval(
      () => setCooldownSeconds((value) => Math.max(0, value - 1)),
      1000,
    );
    return () => window.clearInterval(intervalId);
  }, [cooldownSeconds]);

  const isBusy = isSyncing || isDeleting;
  const isSyncDisabled = isBusy || cooldownSeconds > 0 || (!account.can_sync && account.sync_cooldown_seconds === 0);
  const syncLabel = isSyncing
    ? "Syncing..."
    : cooldownSeconds > 0
      ? `Try again in ${cooldownSeconds}s`
      : !account.can_sync && account.sync_cooldown_seconds === 0
        ? "Sync unavailable"
        : "Sync";
  const platformName = formatPlatformName(account.platform);
  const logo = account.platform === "atcoder" ? "/images/atcoder_logo.png" : account.platform === "leetcode" ? "/images/leetcode_logo.png" : account.platform === "ctftime" ? "/images/ctf_time.png" : "/images/codeforces_logo.png";
  const displayHandle = account.platform === "ctftime" ? `Team #${account.handle}` : `@${account.handle}`;

  const handleSync = async () => {
    if (isSyncDisabled) return;
    setIsSyncing(true);
    try { await onSync(account.id); } finally { setIsSyncing(false); }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Remove ${displayHandle} from ${platformName}?`)) return;
    setIsDeleting(true);
    try { await onDelete(account.id); } finally { setIsDeleting(false); }
  };

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.035)] transition hover:shadow-[0_14px_32px_rgba(15,23,42,0.06)] sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-slate-50 ring-1 ring-slate-100">
            <Image src={logo} alt={`${platformName} logo`} width={34} height={34} className="size-8 object-contain" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-950">{platformName}</p>
            {account.profile_url ? (
              <a href={account.profile_url} target="_blank" rel="noreferrer" className="mt-0.5 inline-flex items-center gap-1 truncate text-xs font-medium text-blue-700 hover:text-blue-800">
                {displayHandle}<ExternalLink className="size-3" />
              </a>
            ) : <p className="mt-0.5 truncate text-xs font-medium text-slate-500">{displayHandle}</p>}
          </div>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <StatusBadge valid={account.handle_validated}>{account.platform === "ctftime" ? (account.handle_validated ? "Team found" : "Team not validated") : (account.handle_validated ? "Handle valid" : "Handle not validated")}</StatusBadge>
          {account.platform !== "ctftime" ? <StatusBadge valid={account.ownership_verified}>{account.ownership_verified ? "Ownership verified" : "Ownership not verified"}</StatusBadge> : null}
        </div>
      </div>

      <p className="mt-3 text-xs font-medium text-slate-500">
        {account.last_synced_at ? `Last synced ${formatRelativeTime(account.last_synced_at)}` : "Never synced"}
      </p>
      <ProviderStats account={account} />
      {account.platform === "ctftime" && account.ctftime_sync_state?.status === "failed" ? (
        <p className="mt-3 rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-xs text-red-700">
          Last sync failed: {account.ctftime_sync_state.failure_reason.replaceAll("_", " ")}.
        </p>
      ) : null}

      <div className="mt-4 flex items-center gap-2">
        <button type="button" onClick={handleSync} disabled={isSyncDisabled} className="inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-[13px] font-semibold text-slate-900 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60">
          {isSyncing ? <Loader2 className="size-4 animate-spin text-blue-600" /> : <RefreshCw className="size-4 text-blue-600" />}
          {syncLabel}
        </button>
        <button type="button" onClick={handleDelete} disabled={isBusy} className="inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-red-100 bg-white px-3 text-[13px] font-semibold text-red-600 shadow-sm transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60">
          {isDeleting ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
          {isDeleting ? "Removing..." : "Delete"}
        </button>
      </div>
    </article>
  );
}
