"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Loader2, Link2 } from "lucide-react";
import {
  connectPlatformAccount,
  deletePlatformAccount,
  listPlatformAccounts,
  syncPlatformAccount,
} from "@/features/platforms/api";
import type { ConnectPlatformFormValues } from "@/features/platforms/schemas";
import type { PlatformAccount } from "@/features/platforms/types";
import { useAuth } from "@/hooks/use-auth";
import { formatPlatformName, getApiErrorMessage } from "@/lib/utils";
import { ConnectPlatformForm } from "./connect-platform-form";
import { PlatformAccountCard } from "./platform-account-card";

const DEFAULT_PLATFORM = "codeforces";

export function PlatformsManager() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applyAccounts = useCallback(async () => {
    if (!user) {
      setAccounts([]);
      setError(null);
      setIsLoading(false);
      return;
    }

    try {
      const data = await listPlatformAccounts();
      setAccounts(data);
      setError(null);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to load your platforms."));
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    if (!user) {
      router.replace("/login");
      return;
    }

    let cancelled = false;

    void (async () => {
      setIsLoading(true);

      try {
        const data = await listPlatformAccounts();
        if (cancelled) return;
        setAccounts(data);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(getApiErrorMessage(err, "Failed to load your platforms."));
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isAuthLoading, router, user]);

  const reloadAccounts = useCallback(() => {
    if (!user) {
      router.replace("/login");
      return;
    }

    setIsLoading(true);
    setError(null);
    void applyAccounts();
  }, [applyAccounts, router, user]);

  const handleConnect = useCallback(
    async (values: ConnectPlatformFormValues): Promise<boolean> => {
      if (isAuthLoading) {
        return false;
      }

      if (!user) {
        toast.error("Please sign in to connect a platform.");
        router.replace("/login");
        return false;
      }

      try {
        const account = await connectPlatformAccount({
          platform: DEFAULT_PLATFORM,
          handle: values.handle,
        });

        setAccounts((prev) => [account, ...prev]);
        toast.success(
          `Connected @${account.handle} on ${formatPlatformName(account.platform)}.`,
        );

        return true;
      } catch (err) {
        toast.error(getApiErrorMessage(err, "Could not connect that handle."));

        return false;
      }
    },
    [isAuthLoading, router, user],
  );

  const handleSync = useCallback(async (id: number) => {
    if (!user) {
      toast.error("Please sign in to sync a platform.");
      router.replace("/login");
      return;
    }

    try {
      const updated = await syncPlatformAccount(id);
      setAccounts((prev) =>
        prev.map((account) => (account.id === id ? updated : account)),
      );
      toast.success(`Synced @${updated.handle}.`);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Sync failed. Please try again."));
    }
  }, [router, user]);

  const handleDelete = useCallback(async (id: number) => {
    if (!user) {
      toast.error("Please sign in to remove a platform.");
      router.replace("/login");
      return;
    }

    try {
      await deletePlatformAccount(id);
      setAccounts((prev) => prev.filter((account) => account.id !== id));
      toast.success("Platform removed.");
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not remove that platform."));
    }
  }, [router, user]);

  return (
    <div className="flex flex-col gap-6">
      <ConnectPlatformForm onConnect={handleConnect} />

      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-950">
          Connected accounts
        </h2>

        {isLoading ? (
          <div className="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-10 text-sm font-medium text-slate-500 shadow-[0_12px_30px_rgba(15,23,42,0.035)]">
            <Loader2 className="size-4 animate-spin text-blue-600" />
            Loading your platforms...
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-red-100 bg-red-50/60 px-4 py-8 text-center shadow-[0_12px_30px_rgba(15,23,42,0.035)]">
            <p className="text-sm font-semibold text-red-700">{error}</p>
            <button
              type="button"
              onClick={reloadAccounts}
              className="mt-3 inline-flex h-9 items-center justify-center rounded-xl border border-red-200 bg-white px-4 text-[13px] font-semibold text-red-700 shadow-sm transition hover:bg-red-50"
            >
              Try again
            </button>
          </div>
        ) : accounts.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-12 text-center shadow-[0_12px_30px_rgba(15,23,42,0.035)]">
            <span className="mx-auto grid size-12 place-items-center rounded-2xl bg-slate-50 text-slate-400">
              <Link2 className="size-6" />
            </span>
            <p className="mt-3 text-sm font-semibold text-slate-950">
              No platforms connected yet
            </p>
            <p className="mt-1 text-xs font-medium text-slate-500">
              Add a Codeforces handle above to get started.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {accounts.map((account) => (
              <PlatformAccountCard
                key={account.id}
                account={account}
                onSync={handleSync}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
