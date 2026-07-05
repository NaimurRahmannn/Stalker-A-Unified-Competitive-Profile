"use client";

import Link from "next/link";
import { Copy, ExternalLink } from "lucide-react";
import { toast } from "sonner";

interface PublicProfileActionsProps {
  username: string;
}

export function PublicProfileActions({ username }: PublicProfileActionsProps) {
  const safeUsername = username.trim();

  if (!safeUsername) {
    return null;
  }

  const encodedUsername = encodeURIComponent(safeUsername);
  const profilePath = `/profile/${encodedUsername}`;

  const copyProfileLink = async () => {
    if (
      typeof window === "undefined" ||
      typeof navigator === "undefined" ||
      !navigator.clipboard?.writeText
    ) {
      toast.error("Could not copy profile link");
      return;
    }

    try {
      const profileUrl = `${window.location.origin}${profilePath}`;
      await navigator.clipboard.writeText(profileUrl);
      toast.success("Public profile link copied");
    } catch {
      toast.error("Could not copy profile link");
    }
  };

  return (
    <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
      <Link
        href={profilePath}
        className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 text-[13px] font-semibold text-emerald-700 shadow-sm transition hover:bg-emerald-100"
      >
        <ExternalLink className="size-4" />
        View Public Profile
      </Link>

      <button
        type="button"
        onClick={copyProfileLink}
        className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-[13px] font-semibold text-slate-900 shadow-sm transition hover:bg-slate-50"
      >
        <Copy className="size-4 text-blue-600" />
        Copy Profile Link
      </button>
    </div>
  );
}
