"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { hackathonApi } from "../api";
import type { DuplicateReview, DuplicateReviewListing } from "../types";
import { getApiErrorMessage } from "@/lib/utils";

function RecordSummary({ label, record }: { label: string; record: DuplicateReview["manual"] }) {
  return <div className="min-w-0 rounded-lg border border-slate-200 bg-white p-3"><p className="text-[11px] font-semibold uppercase text-slate-500">{label}</p>
    <p className="mt-1 wrap-break-word font-medium text-slate-900">{record.title || record.name}</p>
    <p className="mt-1 break-all text-xs text-slate-500">{record.project_url || record.event_url || record.repository_url || "No primary URL"}</p>
    {record.is_public != null && <p className="mt-1 text-xs text-slate-600">{record.is_public ? "Published" : "Private"}</p>}
  </div>;
}

export function DuplicateReviewPanel({ refreshKey = 0 }: { refreshKey?: number }) {
  const [listing, setListing] = useState<DuplicateReviewListing | null>(null);
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const serial = useRef(0);
  const invalidateRequests = useCallback(() => { serial.current += 1; }, []);
  const load = useCallback(async () => {
    const current = ++serial.current;
    const data = await hackathonApi.duplicateReviews(page);
    if (current === serial.current) { setListing(data); setError(""); setLoading(false); }
  }, [page]);
  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => { void load().catch((cause) => { if (active) { setError(getApiErrorMessage(cause, "Could not load duplicate reviews.")); setLoading(false); } }); }, 0);
    return () => { active = false; invalidateRequests(); window.clearTimeout(timer); };
  }, [load, refreshKey, invalidateRequests]);

  const decide = async (row: DuplicateReview, decision: DuplicateReview["decision"]) => {
    const key = `${row.record_type}-${row.manual.id}-${row.imported.id}`;
    if (busy) return;
    setBusy(key); setError("");
    try {
      if (row.id) await hackathonApi.updateDuplicateReview(row.id, decision);
      else await hackathonApi.createDuplicateReview({ record_type: row.record_type, manual_id: row.manual.id,
        imported_id: row.imported.id, decision });
      await load();
    } catch (cause) { setError(getApiErrorMessage(cause, "Could not save duplicate review.")); }
    finally { setBusy(""); }
  };

  const candidateIds = new Set(listing?.candidates.map((row) => row.id).filter(Boolean));
  const rows = [...(listing?.candidates ?? []), ...(listing?.reviews.results ?? []).filter((row) => !candidateIds.has(row.id))];
  return <section aria-labelledby="duplicate-review-heading" className="rounded-xl border border-slate-200 p-4">
    <h3 id="duplicate-review-heading" className="font-semibold">Possible duplicate review</h3>
    <p className="mt-1 text-xs text-slate-600">URL matches are suggestions. Marking records related does not merge, delete, publish, or verify either record.</p>
    {error && <p role="alert" className="mt-2 text-xs text-rose-700">{error} <button type="button" onClick={() => void load()} className="font-semibold underline">Retry</button></p>}
    {loading ? <p role="status" className="mt-3 text-sm text-slate-500">Loading reviews…</p> : rows.length === 0 ?
      <p className="mt-3 text-sm text-slate-500">No possible matches or saved reviews yet.</p> :
      <div className="mt-3 space-y-3">{rows.map((row) => { const key = `${row.record_type}-${row.manual.id}-${row.imported.id}`; return <article key={key} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
        <div className="flex flex-wrap justify-between gap-2"><p className="text-xs font-semibold capitalize text-violet-700">{row.record_type} · {row.reason}</p>
          <p className="text-xs text-slate-600">Review: {row.decision}</p></div>
        <div className="mt-2 grid gap-2 sm:grid-cols-2"><RecordSummary label="Manual" record={row.manual} /><RecordSummary label="Devpost import" record={row.imported} /></div>
        <div className="mt-3 flex flex-wrap gap-2">{([ ["related", "Mark related"], ["distinct", "Mark distinct"], ["unresolved", "Leave unresolved"] ] as const).map(([value, label]) =>
          <button key={value} type="button" disabled={!!busy || row.decision === value} onClick={() => void decide(row, value)}
            className="rounded-lg border border-violet-200 px-3 py-1.5 text-xs font-semibold text-violet-700 disabled:opacity-40">{busy === key ? "Saving…" : label}</button>)}</div>
      </article>; })}</div>}
    {listing && (listing.reviews.next || listing.reviews.previous) && <div className="mt-3 flex items-center justify-between text-xs"><button type="button" disabled={!listing.reviews.previous || !!busy} onClick={() => setPage((current) => current - 1)}>Previous reviews</button>
      <span>Saved reviews page {page}</span><button type="button" disabled={!listing.reviews.next || !!busy} onClick={() => setPage((current) => current + 1)}>Next reviews</button></div>}
  </section>;
}
