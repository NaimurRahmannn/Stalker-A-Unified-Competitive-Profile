"use client";

import { useCallback, useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { toast } from "sonner";
import { connectPlatformAccount, deletePlatformAccount, listPlatformAccounts, updatePlatformAccount } from "@/features/platforms/api";
import type { PlatformAccount } from "@/features/platforms/types";
import { getApiErrorMessage } from "@/lib/utils";
import { hackathonApi } from "../api";
import { devpostAccountSchema, devpostImportSchema } from "../schemas";
import type { DevpostImportDocument, DevpostImportRun, DevpostPreview, Page } from "../types";

const accountFormSchema = z.object({ reference: devpostAccountSchema });
type AccountValues = z.infer<typeof accountFormSchema>;
const sizeLimit = 1_048_576;

function exampleDocument(handle: string): DevpostImportDocument {
  return {
    format_version: 1,
    profile_url: `https://devpost.com/${handle}`,
    projects: [{
      project_url: "https://devpost.com/software/smart-city-ai",
      title: "Smart City AI",
      description: "AI-powered city monitoring system",
      repository_url: "https://github.com/example/smart-city-ai",
      technologies: ["Python", "React"],
      submissions: [{ hackathon_name: "Global AI Hackathon", hackathon_url: "https://global-ai-hackathon.devpost.com/", status: "submitted" }],
    }],
  };
}

export function DevpostIntegration({ onImported }: { onImported: () => Promise<void> }) {
  const [account, setAccount] = useState<PlatformAccount | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [documentText, setDocumentText] = useState("");
  const [document, setDocument] = useState<DevpostImportDocument | null>(null);
  const [preview, setPreview] = useState<DevpostPreview | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [result, setResult] = useState<DevpostImportRun | null>(null);
  const [history, setHistory] = useState<Page<DevpostImportRun> | null>(null);
  const [historyPage, setHistoryPage] = useState(1);
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<AccountValues>({
    resolver: zodResolver(accountFormSchema), defaultValues: { reference: "" },
  });

  const loadAccount = useCallback(async () => {
    const accounts = await listPlatformAccounts();
    const linked = accounts.find((item) => item.platform === "devpost") ?? null;
    setAccount(linked);
    reset({ reference: linked?.handle ?? "" });
  }, [reset]);

  const loadHistory = useCallback(async () => {
    setHistory(await hackathonApi.devpostHistory(historyPage));
  }, [historyPage]);

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      void Promise.all([loadAccount(), loadHistory()]).catch((err) => {
        if (active) setError(getApiErrorMessage(err, "Could not load Devpost integration."));
      }).finally(() => { if (active) setLoading(false); });
    }, 0);
    return () => { active = false; window.clearTimeout(timer); };
  }, [loadAccount, loadHistory]);

  const clearPreview = () => { setPreview(null); setDocument(null); setConfirmed(false); setResult(null); };
  const saveAccount = handleSubmit(async ({ reference }) => {
    setBusy(true); setError("");
    try {
      if (account) {
        if (reference.trim().toLowerCase() === account.handle && account.profile_url === `https://devpost.com/${account.handle}`) return;
        if (reference.trim().toLowerCase() !== account.handle && !window.confirm("Changing your linked Devpost account invalidates pending previews. Historical imports and achievements stay intact. Continue?")) return;
        await updatePlatformAccount(account.id, reference);
        toast.success("Devpost profile changed");
      } else {
        await connectPlatformAccount({ platform: "devpost", handle: reference });
        toast.success("Devpost profile linked");
      }
      clearPreview(); await loadAccount();
    } catch (err) { setError(getApiErrorMessage(err, "Could not save Devpost profile.")); }
    finally { setBusy(false); }
  });

  const unlink = async () => {
    if (!account || !window.confirm("Unlink Devpost? Historical imported records and achievements will remain.")) return;
    setBusy(true); setError("");
    try { await deletePlatformAccount(account.id); clearPreview(); await loadAccount(); toast.success("Devpost profile unlinked"); }
    catch (err) { setError(getApiErrorMessage(err, "Could not unlink Devpost profile.")); }
    finally { setBusy(false); }
  };

  const selectFile = async (file: File | undefined) => {
    if (!file) return;
    clearPreview(); setError("");
    if (file.size > sizeLimit) { setError("JSON files must be at most 1 MB."); return; }
    try { setDocumentText(await file.text()); }
    catch { setError("Could not read the JSON file."); }
  };

  const previewImport = async () => {
    if (!account) return;
    clearPreview(); setError("");
    if (new TextEncoder().encode(documentText).length > sizeLimit) { setError("JSON must be at most 1 MB."); return; }
    let parsed: unknown;
    try { parsed = JSON.parse(documentText); }
    catch { setError("Enter valid JSON before previewing."); return; }
    const checked = devpostImportSchema.safeParse(parsed);
    if (!checked.success) { setError(checked.error.issues[0]?.message ?? "Invalid import document."); return; }
    setBusy(true);
    try {
      const normalized = checked.data as DevpostImportDocument;
      const plan = await hackathonApi.previewDevpost(normalized);
      setDocument(normalized); setPreview(plan);
    } catch (err) { setError(getApiErrorMessage(err, "Could not preview import.")); }
    finally { setBusy(false); }
  };

  const applyImport = async () => {
    if (!document || !preview || !confirmed) return;
    setBusy(true); setError("");
    try {
      const run = await hackathonApi.applyDevpost(document, preview.preview_token);
      setResult(run); setPreview(null); setConfirmed(false);
      setHistoryPage(1); await Promise.all([onImported(), hackathonApi.devpostHistory(1).then(setHistory)]);
      toast.success("Devpost data imported");
    } catch (err) { setError(getApiErrorMessage(err, "Import could not be applied. Preview again.")); setPreview(null); setConfirmed(false); await loadHistory(); }
    finally { setBusy(false); }
  };

  return <section className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="devpost-heading">
    <div><h2 id="devpost-heading" className="text-lg font-semibold text-slate-950">Devpost Integration</h2>
      <p className="mt-1 text-sm text-slate-600">Link a profile and import your own structured JSON. Linking and uploaded data do not verify ownership or achievements. Automatic Devpost fetching is unavailable.</p></div>
    {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
    {loading ? <p role="status" className="text-sm text-slate-500">Loading Devpost integration…</p> : <>
      <div className="rounded-xl border border-slate-200 p-4">
        <h3 className="font-semibold">Profile connection</h3>
        {account && <p className="mt-2 text-sm text-slate-600">Linked: <a className="font-medium text-violet-700 underline" href={account.profile_url} target="_blank" rel="noreferrer">{account.profile_url}</a> · {account.ownership_verified ? "Ownership verified" : "Ownership not verified"}</p>}
        <form onSubmit={saveAccount} className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-start" noValidate>
          <div className="min-w-0 flex-1"><label htmlFor="devpost-reference" className="text-xs font-semibold text-slate-600">Devpost username or profile URL</label>
            <input id="devpost-reference" {...register("reference")} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="example_user or https://devpost.com/example_user" />
            {errors.reference && <p className="mt-1 text-xs text-rose-700">{errors.reference.message}</p>}</div>
          <button disabled={busy || isSubmitting} className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 sm:mt-5">{account ? "Change profile" : "Link profile"}</button>
          {account && <button type="button" disabled={busy} onClick={() => void unlink()} className="rounded-lg border border-slate-300 px-4 py-2 text-sm disabled:opacity-50 sm:mt-5">Unlink</button>}
        </form>
        {account && <p className="mt-2 text-xs text-amber-800">Changing this handle invalidates pending previews. Historical records and manual achievements remain unchanged.</p>}
      </div>
      {account && <div className="rounded-xl border border-slate-200 p-4">
        <h3 className="font-semibold">Import data</h3>
        <p className="mt-1 text-xs text-slate-600">Use the STALKER JSON v1 format, not an official Devpost export. Maximum 1 MB, 100 projects, and 20 submissions per project. Project-only entries are welcome.</p>
        <div className="mt-3 flex flex-wrap gap-3"><label className="cursor-pointer rounded-lg border border-slate-300 px-3 py-2 text-sm">Choose JSON file<input type="file" accept=".json,application/json" className="sr-only" onChange={(event) => void selectFile(event.target.files?.[0])} /></label>
          <button type="button" onClick={() => { clearPreview(); setDocumentText(JSON.stringify(exampleDocument(account.handle), null, 2)); }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">Load schema example</button></div>
        <label htmlFor="devpost-json" className="mt-3 block text-xs font-semibold text-slate-600">JSON document</label>
        <textarea id="devpost-json" value={documentText} maxLength={sizeLimit} onChange={(event) => { clearPreview(); setDocumentText(event.target.value); }} rows={10} spellCheck={false} className="mt-1 w-full rounded-lg border border-slate-300 p-3 font-mono text-xs" placeholder="Paste STALKER JSON v1 here or choose a file" />
        <button type="button" disabled={busy || !documentText.trim()} onClick={() => void previewImport()} className="mt-3 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Working…" : "Preview import"}</button>
      </div>}
      {preview && <div className="rounded-xl border border-violet-200 bg-violet-50 p-4">
        <h3 className="font-semibold">Import preview</h3>
        <p className="mt-1 text-sm">{preview.projects_detected} projects · {preview.hackathons_detected} hackathons · {preview.participations_detected} participations · {preview.submissions_detected} submissions · {preview.new_records} new · {preview.existing_matches} existing · {preview.protected_records} protected</p>
        {preview.potential_manual_duplicates > 0 && <p className="mt-2 text-xs text-amber-800">{preview.potential_manual_duplicates} possible manual matches will remain separate and untouched.</p>}
        {preview.conflicts.length > 0 && <div className="mt-2 text-xs text-rose-700"><p>{preview.conflicts.length} conflicting records must be resolved before importing.</p>{preview.conflicts.slice(0, 5).map((conflict, index) => <p key={index} className="break-all">{conflict.project_url || conflict.event_url}</p>)}</div>}
        <div className="mt-3 max-h-64 space-y-2 overflow-y-auto">{preview.projects.map((project) => <div key={project.project_url} className="rounded-lg border border-violet-100 bg-white p-3 text-sm"><p className="font-medium">{project.title} · {project.action}</p><p className="break-all text-xs text-slate-500">{project.project_url}</p>{project.possible_manual_project_ids.length > 0 && <p className="text-xs text-amber-800">Possible manual project IDs: {project.possible_manual_project_ids.join(", ")}</p>}{project.submissions.map((submission) => <p key={submission.event_url} className="mt-1 text-xs text-slate-600">{submission.event_name}: event {submission.event_action}, participation {submission.participation_action}, submission {submission.action}{submission.possible_manual_event_ids.length > 0 ? ` · possible manual event IDs: ${submission.possible_manual_event_ids.join(", ")}` : ""}</p>)}</div>)}</div>
        <label className="mt-3 flex items-start gap-2 text-xs text-slate-700"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} className="mt-0.5" />I reviewed these changes and want to import this user-provided data.</label>
        <button type="button" disabled={busy || !confirmed || preview.conflicts.length > 0} onClick={() => void applyImport()} className="mt-3 rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Confirm import</button>
      </div>}
      {result && <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900"><h3 className="font-semibold">Import completed</h3><p>{result.created_count} created · {result.updated_count} updated · {result.skipped_count} skipped</p><p>{result.result.events_created ?? 0} hackathons, {result.result.participations_created ?? 0} participations, and {result.result.submissions_created ?? 0} submissions created.</p>{result.result.warnings?.map((warning, index) => <p key={`${index}-${warning}`} className="mt-1 text-xs">{warning}</p>)}</div>}
      <div className="rounded-xl border border-slate-200 p-4"><h3 className="font-semibold">Import history</h3>
        {history?.count ? <div className="mt-3 space-y-2">{history.results.map((run) => <div key={run.id} className="rounded-lg border border-slate-100 p-3 text-xs"><p className="font-medium">{run.status} · {run.profile_handle} · {new Date(run.started_at).toLocaleString()}</p><p>{run.projects_processed} projects · {run.created_count} created · {run.updated_count} updated · {run.skipped_count} skipped · {run.error_count} errors</p>{run.result.error && <p className="text-rose-700">{run.result.error}</p>}</div>)}</div> : <p className="mt-2 text-sm text-slate-500">No imports yet.</p>}
        <div className="mt-3 flex items-center justify-between text-xs"><button disabled={!history?.previous} onClick={() => setHistoryPage((page) => page - 1)} className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40">Previous</button><span>Page {historyPage}</span><button disabled={!history?.next} onClick={() => setHistoryPage((page) => page + 1)} className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40">Next</button></div>
      </div>
    </>}
  </section>;
}
