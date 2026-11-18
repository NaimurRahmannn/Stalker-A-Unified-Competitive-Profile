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
    <div className="flex w-full flex-col gap-2 sm:w-auto sm:min-w-max sm:flex-row sm:items-center">
      <Link
        href={profilePath}
        className="ui-button ui-button-primary shrink-0 text-[13px]"
      >
        <ExternalLink className="size-4" />
        View Public Profile
      </Link>

      <button
        type="button"
        onClick={copyProfileLink}
        className="ui-button ui-button-secondary shrink-0 text-[13px]"
      >
        <Copy className="size-4" />
        Copy Profile Link
      </button>
    </div>
  );
}
