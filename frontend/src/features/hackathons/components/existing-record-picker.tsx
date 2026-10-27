"use client";

import { useEffect, useState } from "react";
import { hackathonApi } from "../api";
import type { Event, Page, Project } from "../types";
import { getApiErrorMessage } from "@/lib/utils";

type Pickable = Event | Project;
const label = (item: Pickable) => "name" in item ? item.name : item.title;

export function ExistingRecordPicker({ kind, value, selectedItem, onSelect, error }: { kind: "event" | "project"; value: string; selectedItem: Pickable | null; onSelect: (item: Pickable | null) => void; error?: string }) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [results, setResults] = useState<Page<Pickable> | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(async () => {
      setLoading(true);
      try {
        const data = kind === "event" ? await hackathonApi.events(page, query) : await hackathonApi.projects(page, 20, query);
        if (active) { setResults(data); setLoadError(""); }
      } catch (cause) {
        if (active) { setLoadError(getApiErrorMessage(cause, "Could not load records.")); setResults(null); }
      } finally { if (active) setLoading(false); }
    }, 200);
    return () => { active = false; window.clearTimeout(timer); };
  }, [kind, page, query, retry]);

  const options = results?.results ?? [];
  const savedSelection = selectedItem && String(selectedItem.id) === value && !options.some((item) => String(item.id) === value) ? selectedItem : null;
  return <div className="space-y-2">
    <label className="block text-xs font-semibold text-slate-600">Search {kind === "event" ? "hackathons" : "projects"}<input value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder={kind === "event" ? "Search by name" : "Search by title"} className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm" /></label>
    <label className="block text-xs font-semibold text-slate-600">Existing {kind}<select value={value} onChange={(event) => { const item = options.find((candidate) => String(candidate.id) === event.target.value) ?? (savedSelection && String(savedSelection.id) === event.target.value ? savedSelection : null); onSelect(item); }} className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"><option value="">Select a {kind}</option>{savedSelection && <option value={savedSelection.id}>{label(savedSelection)} (selected)</option>}{options.map((item) => <option key={item.id} value={item.id}>{label(item)}</option>)}</select></label>
    {selectedItem && value && <p className="text-xs text-violet-700">Selected: {label(selectedItem)}</p>}
    {loading && <p role="status" className="text-xs text-slate-500">Loading {kind}s…</p>}
    {!loading && !loadError && results?.count === 0 && <p className="text-xs text-slate-500">No matching {kind}s.</p>}
    {loadError && <p role="alert" className="text-xs text-rose-700">{loadError} <button type="button" onClick={() => setRetry((current) => current + 1)} className="underline">Retry</button></p>}
    <div className="flex items-center justify-between text-xs"><button type="button" disabled={!results?.previous || loading} onClick={() => setPage((current) => current - 1)} className="rounded-lg border border-slate-200 px-2.5 py-1 disabled:opacity-40">Previous</button><span>Page {page} · {results?.count ?? 0} results</span><button type="button" disabled={!results?.next || loading} onClick={() => setPage((current) => current + 1)} className="rounded-lg border border-slate-200 px-2.5 py-1 disabled:opacity-40">Next</button></div>
    {error && <p className="text-xs text-rose-600">{error}</p>}
  </div>;
}
