"use client";

import { useState } from "react";
import {
  Code2,
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
      <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-slate-500">
        {label}
      </p>
      <p className="mt-0.5 truncate text-sm font-semibold text-slate-950">
        {value}
      </p>
    </div>
  );
}

export function PlatformAccountCard({
  account,
  onSync,
  onDelete,
}: PlatformAccountCardProps) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const stats = account.codeforces_stats;
  const isBusy = isSyncing || isDeleting;

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      await onSync(account.id);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleDelete = async () => {
    const confirmed = window.confirm(
      `Remove @${account.handle} from ${formatPlatformName(account.platform)}?`,
    );

    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    try {
      await onDelete(account.id);
    } finally {
      setIsDeleting(false);
    }
  };

  const verifiedBadge = account.is_verified
    ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
    : "bg-orange-50 text-orange-700 ring-1 ring-orange-200";

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.035)] transition hover:shadow-[0_14px_32px_rgba(15,23,42,0.06)] sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100">
            <Code2 className="size-5" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-950">
              {formatPlatformName(account.platform)}
            </p>
            {account.profile_url ? (
              <a
                href={account.profile_url}
                target="_blank"
                rel="noreferrer"
                className="mt-0.5 inline-flex items-center gap-1 truncate text-xs font-medium text-blue-700 transition hover:text-blue-800"
              >
                @{account.handle}
                <ExternalLink className="size-3" />
              </a>
            ) : (
              <p className="mt-0.5 truncate text-xs font-medium text-slate-500">
                @{account.handle}
              </p>
            )}
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold ${verifiedBadge}`}
        >
          {account.is_verified ? (
            <ShieldCheck className="size-3.5" />
          ) : (
            <ShieldAlert className="size-3.5" />
          )}
          {account.is_verified ? "Verified" : "Unverified"}
        </span>
      </div>

      <p className="mt-3 text-xs font-medium text-slate-500">
        {account.last_synced_at
          ? `Last synced ${formatRelativeTime(account.last_synced_at)}`
          : "Never synced"}
      </p>

      {stats ? (
        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <StatTile
            label="Rating"
            value={stats.rating !== null ? String(stats.rating) : "Unrated"}
          />
          <StatTile
            label="Max rating"
            value={
              stats.max_rating !== null ? String(stats.max_rating) : "Unrated"
            }
          />
          <StatTile label="Rank" value={stats.rank ?? "Unranked"} />
          <StatTile label="Solved" value={String(stats.solved_count)} />
        </div>
      ) : (
        <p className="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/70 px-3 py-2.5 text-xs font-medium text-slate-500">
          No stats yet. Run a sync to pull data from Codeforces.
        </p>
      )}

      <div className="mt-4 flex items-center gap-2">
        <button
          type="button"
          onClick={handleSync}
          disabled={isBusy}
          className="inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-[13px] font-semibold text-slate-900 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSyncing ? (
            <Loader2 className="size-4 animate-spin text-blue-600" />
          ) : (
            <RefreshCw className="size-4 text-blue-600" />
          )}
          {isSyncing ? "Syncing..." : "Sync"}
        </button>

        <button
          type="button"
          onClick={handleDelete}
          disabled={isBusy}
          className="inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-red-100 bg-white px-3 text-[13px] font-semibold text-red-600 shadow-sm transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isDeleting ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Trash2 className="size-4" />
          )}
          {isDeleting ? "Removing..." : "Delete"}
        </button>
      </div>
    </article>
  );
}
