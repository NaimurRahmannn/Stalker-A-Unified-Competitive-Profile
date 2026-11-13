"use client";

import { useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { deleteKaggleManualTrack, saveKaggleManualTrack } from "../api";
import { getApiErrorMessage } from "@/lib/utils";
import type { KaggleManualTrackInput, KaggleOverviewResponse, KaggleRankStatus, KaggleTrack } from "../types";
import { trackLabels } from "./kaggle-track-card";
import { KAGGLE_TIERS, KaggleTierIcon } from "./kaggle-tier-icon";

const tracks: KaggleTrack[] = ["competitions", "code", "datasets"];
type Field = "global_rank" | "highest_rank" | "points" | "gold_medals" | "silver_medals" | "bronze_medals";
type Draft = Record<Field, string> & { rank_status: KaggleRankStatus; tier: string };
const blank: Draft = {
  rank_status: "ranked", global_rank: "", highest_rank: "", tier: "", points: "",
  gold_medals: "", silver_medals: "", bronze_medals: "",
};

function fromOverview(overview: KaggleOverviewResponse, track: KaggleTrack): Draft {
  const row = overview.manual_tracks?.[track];
  if (!row) return { ...blank };
  return {
    rank_status: row.rank_status, global_rank: String(row.global_rank ?? ""),
    highest_rank: String(row.highest_rank ?? ""), tier: row.tier ?? "", points: String(row.points ?? ""),
    gold_medals: String(row.gold_medals ?? ""), silver_medals: String(row.silver_medals ?? ""),
    bronze_medals: String(row.bronze_medals ?? ""),
  };
}

function optionalNumber(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

export function KaggleManualEditor({ overview, onChanged }: {
  overview: KaggleOverviewResponse;
  onChanged: () => Promise<void>;
}) {
  const [track, setTrack] = useState<KaggleTrack>("competitions");
  const [draft, setDraft] = useState<Draft>(() => fromOverview(overview, "competitions"));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const existing = overview.manual_tracks?.[track] ?? null;

  function setField(field: Field, value: string) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setError(null);
    const payload: KaggleManualTrackInput = {
      rank_status: draft.rank_status,
      global_rank: draft.rank_status === "ranked" ? optionalNumber(draft.global_rank) : null,
      highest_rank: optionalNumber(draft.highest_rank),
      tier: draft.rank_status === "unranked" ? null : draft.tier || null,
      points: draft.rank_status === "unranked" ? null : draft.points.trim() || null,
      gold_medals: optionalNumber(draft.gold_medals),
      silver_medals: optionalNumber(draft.silver_medals),
      bronze_medals: optionalNumber(draft.bronze_medals),
    };
    if (payload.rank_status === "ranked" && (!Number.isInteger(payload.global_rank) || !payload.global_rank || payload.global_rank < 1)) {
      setError("Enter a positive global rank for a ranked track.");
      return;
    }
    setBusy(true);
    try {
      await saveKaggleManualTrack(track, payload);
      await onChanged();
      toast.success(`${trackLabels[track]} statistics saved as self reported.`);
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "Could not save your Kaggle statistics."));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (busy || !existing) return;
    setBusy(true);
    setError(null);
    try {
      await deleteKaggleManualTrack(track);
      await onChanged();
      setDraft({ ...blank });
      toast.success(`${trackLabels[track]} self reported statistics removed.`);
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Could not remove your Kaggle statistics."));
    } finally {
      setBusy(false);
    }
  }

  const field = (name: Field, label: string, step = "1") => <label className="block min-w-0 text-xs font-medium text-slate-700" key={name}>
    {label}<input type="number" min={name.includes("medals") || name === "points" ? "0" : "1"} step={step} value={draft[name]}
      onChange={(event) => setField(name, event.target.value)} disabled={busy}
      className="mt-1 h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-200 disabled:opacity-60" />
  </label>;

  return <section className="rounded-2xl border border-sky-200/80 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="manual-kaggle-heading">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 id="manual-kaggle-heading" className="text-lg font-semibold text-slate-950">Enter your Kaggle statistics</h2><p className="mt-1 max-w-2xl text-sm text-slate-600">Add each track manually. These figures are self reported and are not verified against Kaggle. You can update or remove them anytime.</p></div><span className="rounded-full bg-[#E8F8FE] px-3 py-1 text-xs font-semibold text-[#087EA4] ring-1 ring-sky-200/60">Manual entry</span></div>
    <form onSubmit={(event) => void save(event)} className="mt-5 space-y-4">
      <div className="grid gap-4 sm:grid-cols-2"><label className="block text-xs font-medium text-slate-700">Track<select value={track} onChange={(event) => { const next = event.target.value as KaggleTrack; setTrack(next); setDraft(fromOverview(overview, next)); setError(null); }} disabled={busy} className="mt-1 h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-200">{tracks.map((item) => <option value={item} key={item}>{trackLabels[item]}</option>)}</select></label><label className="block text-xs font-medium text-slate-700">Ranking status<select value={draft.rank_status} onChange={(event) => setDraft((current) => ({ ...current, rank_status: event.target.value as KaggleRankStatus }))} disabled={busy} className="mt-1 h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-200"><option value="ranked">Ranked</option><option value="unranked">Unranked</option><option value="unknown">Unknown</option></select></label></div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{draft.rank_status === "ranked" && field("global_rank", "Current global rank")}{field("highest_rank", "Highest global rank")}{draft.rank_status !== "unranked" && <label className="block text-xs font-medium text-slate-700">Tier<div className="mt-1 flex items-center gap-2"><select value={draft.tier} onChange={(event) => setDraft((current) => ({ ...current, tier: event.target.value }))} disabled={busy} className="h-10 min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-200"><option value="">Not available</option>{KAGGLE_TIERS.map((tier) => <option value={tier} key={tier}>{tier}</option>)}</select>{draft.tier && <KaggleTierIcon tier={draft.tier} className="size-8 shrink-0" />}</div></label>}{draft.rank_status !== "unranked" && field("points", "Ranking points", "0.0001")}{field("gold_medals", "Gold medals")}{field("silver_medals", "Silver medals")}{field("bronze_medals", "Bronze medals")}</div>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <div className="flex flex-wrap items-center gap-3"><button type="submit" disabled={busy} className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-[#20BEFF] px-5 text-sm font-semibold text-slate-950 shadow-sm hover:bg-[#1bb0ee] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#20BEFF] disabled:opacity-50">{busy && <Loader2 className="size-4 animate-spin" />}Save {trackLabels[track]}</button>{existing && <button type="button" onClick={() => void remove()} disabled={busy} className="h-10 rounded-xl border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50">Remove entry</button>}</div>
    </form>
  </section>;
}
