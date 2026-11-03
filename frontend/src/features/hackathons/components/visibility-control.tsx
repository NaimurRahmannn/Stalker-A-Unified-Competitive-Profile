"use client";

import { useState } from "react";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/lib/utils";
import { hackathonApi } from "../api";

export function VisibilityControl({ kind, id, isPublic, onSaved }: {
  kind: "project" | "participation";
  id: number;
  isPublic: boolean;
  onSaved: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const change = async () => {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      if (kind === "project") await hackathonApi.projectVisibility(id, !isPublic);
      else await hackathonApi.participationVisibility(id, !isPublic);
      await onSaved();
      toast.success(isPublic ? "Removed from public profile" : "Published to public profile");
    } catch (cause) {
      const message = getApiErrorMessage(cause, "Could not change visibility.");
      setError(message);
      toast.error(message);
    } finally { setBusy(false); }
  };
  return <div className="flex flex-col items-start gap-1">
    <button type="button" disabled={busy} onClick={() => void change()}
      aria-label={`${isPublic ? "Unpublish" : "Publish"} ${kind}`}
      className="rounded-lg border border-violet-200 px-3 py-1.5 text-xs font-semibold text-violet-700 hover:bg-violet-50 disabled:opacity-50">
      {busy ? "Saving visibility…" : isPublic ? "Remove from profile" : "Publish to profile"}
    </button>
    {error && <span role="alert" className="text-xs text-rose-700">{error}</span>}
  </div>;
}
