"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { hackathonApi } from "../api";
import { achievementPayload, achievementSchema, blankAchievement, type AchievementFormValues } from "../schemas";
import type { Achievement, Event, Project, Submission } from "../types";
import { getApiErrorMessage } from "@/lib/utils";
import { fromLocalDateTimeInput, toLocalDateTimeInput } from "../datetime";
import { Field, fieldClass } from "./hackathon-entry-form";

type Resource = "events" | "projects" | "participations" | "submissions" | "achievements";
type Editing = { resource: Resource; id: number } | null;
const format = (value: string) => value.replaceAll("_", " ");
const date = (value: string | null) => value ? new Date(value + (value.length === 10 ? "T00:00:00" : "")).toLocaleDateString() : "Date not set";

export function Editor({ resource, record, onSaved, onCancel, submissionOptions = [] }: { resource: Resource; record: Record<string, unknown>; onSaved: () => Promise<void>; onCancel: () => void; submissionOptions?: Submission[] }) {
  const keys: Record<Resource, string[]> = {
    events: ["name", "organizer", "description", "event_url", "start_date", "end_date", "format"],
    projects: ["title", "description", "repository_url", "demo_url", "video_url", "image_url", "technologies", "is_public"],
    participations: ["status", "team_name", "role", "is_public"],
    submissions: ["status", "submission_url", "submitted_at"],
    achievements: ["achievement_type", "title", "rank", "total_participants", "description", "evidence_url", "submission"],
  };
  const [initialValues] = useState<Record<string, string>>(() => Object.fromEntries(keys[resource].map((key) => [key, key === "submitted_at" ? toLocalDateTimeInput(record[key] as string | null) : Array.isArray(record[key]) ? (record[key] as string[]).join(", ") : record[key] == null ? "" : String(record[key])])));
  const [values, setValues] = useState<Record<string, string>>(initialValues);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const save = async (event: React.FormEvent) => {
    event.preventDefault(); if (busy) return;
    setError("");
    const changed = Object.keys(values).filter((key) => values[key] !== initialValues[key]);
    if (changed.length === 0) { onCancel(); return; }
    const payload: Record<string, unknown> = Object.fromEntries(changed.map((key) => [key, values[key]]));
    if (resource === "events") {
      if (!values.name.trim()) { setError("Hackathon name is required."); return; }
      if (values.start_date && values.end_date && values.end_date < values.start_date) { setError("End date cannot precede start date."); return; }
      if ("start_date" in payload) payload.start_date = values.start_date || null;
      if ("end_date" in payload) payload.end_date = values.end_date || null;
    }
    if (resource === "projects") { if (!values.title.trim()) { setError("Project title is required."); return; } if ("technologies" in payload) payload.technologies = values.technologies.split(",").map((part) => part.trim()).filter(Boolean); if ("is_public" in payload) payload.is_public = values.is_public === "true"; }
    if (resource === "participations" && "is_public" in payload) payload.is_public = values.is_public === "true";
    if (resource === "submissions" && "submitted_at" in payload) {
      try { payload.submitted_at = fromLocalDateTimeInput(values.submitted_at); }
      catch (cause) { setError(cause instanceof Error ? cause.message : "Invalid submission date and time."); return; }
    }
    if (resource === "achievements") {
      const parsed = achievementSchema.safeParse({ ...values, link_submission: false });
      if (!parsed.success) { setError(parsed.error.issues[0]?.message || "Invalid achievement."); return; }
      const normalized = achievementPayload(parsed.data);
      for (const key of changed) if (key in normalized) payload[key] = normalized[key as keyof typeof normalized];
      if ("submission" in payload) payload.submission = values.submission ? Number(values.submission) : null;
    }
    for (const key of ["event_url", "repository_url", "demo_url", "video_url", "image_url", "submission_url", "evidence_url"]) {
      if (typeof payload[key] === "string" && payload[key]) { try { const url = new URL(payload[key]); if (!["http:", "https:"].includes(url.protocol)) throw new Error(); } catch { setError(`${format(key)} must be an http(s) URL.`); return; } }
    }
    setBusy(true);
    try {
      const id = Number(record.id);
      if (resource === "events") await hackathonApi.patchEvent(id, payload);
      if (resource === "projects") await hackathonApi.patchProject(id, payload);
      if (resource === "participations") await hackathonApi.patchParticipation(id, payload);
      if (resource === "submissions") await hackathonApi.patchSubmission(id, payload);
      if (resource === "achievements") await hackathonApi.patchAchievement(id, payload);
      toast.success("Changes saved"); await onSaved();
    } catch (err) { setError(getApiErrorMessage(err, "Could not save changes.")); } finally { setBusy(false); }
  };
  return <form onSubmit={save} className="mt-3 grid gap-3 rounded-xl border border-violet-200 bg-violet-50/50 p-4 sm:grid-cols-2">
    {keys[resource].map((key) => <Field key={key} title={format(key)}>{key === "submission" ? <select className={fieldClass} value={values[key]} onChange={(e) => setValues({ ...values, [key]: e.target.value })}><option value="">No linked submission</option>{submissionOptions.map((item) => <option key={item.id} value={item.id}>{item.project_title}</option>)}</select> : ["format", "status", "achievement_type", "is_public"].includes(key) ? <select className={fieldClass} value={values[key]} onChange={(e) => setValues({ ...values, [key]: e.target.value })}>{(key === "format" ? ["unknown", "online", "in_person", "hybrid"] : key === "is_public" ? ["false", "true"] : key === "achievement_type" ? ["placement", "award", "finalist", "participation", "other"] : resource === "participations" ? ["registered", "attended", "submitted"] : ["draft", "submitted", "withdrawn"]).map((option) => <option key={option} value={option}>{format(option)}</option>)}</select> : <input className={fieldClass} type={key.endsWith("_date") ? "date" : key === "submitted_at" ? "datetime-local" : ["rank", "total_participants"].includes(key) ? "number" : "text"} step={key === "submitted_at" ? 1 : undefined} value={values[key]} onChange={(e) => setValues({ ...values, [key]: e.target.value })} />}</Field>)}
    {error && <p role="alert" className="sm:col-span-2 text-sm text-rose-700">{error}</p>}
    <div className="flex gap-2 sm:col-span-2"><button disabled={busy} className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Saving…" : "Save changes"}</button><button type="button" onClick={onCancel} className="rounded-lg border border-slate-200 px-4 py-2 text-sm">Cancel</button></div>
  </form>;
}

function AchievementAdd({ participationId, submissions, onSaved }: { participationId: number; submissions: Submission[]; onSaved: () => Promise<void> }) {
  const [error, setError] = useState("");
  const [submissionId, setSubmissionId] = useState("");
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<AchievementFormValues>({ resolver: zodResolver(achievementSchema), defaultValues: blankAchievement() });
  const save = handleSubmit(async (value) => { setError(""); try { await hackathonApi.addAchievement({ participation: participationId, submission: submissionId ? Number(submissionId) : null, ...achievementPayload(value) }); toast.success("Achievement added"); reset(blankAchievement()); setSubmissionId(""); await onSaved(); } catch (err) { setError(getApiErrorMessage(err)); } });
  return <form onSubmit={save} className="mt-3 grid gap-3 rounded-xl border border-slate-200 p-4 sm:grid-cols-2" noValidate><h4 className="font-semibold sm:col-span-2">Add achievement</h4>
    <Field title="Type"><select className={fieldClass} {...register("achievement_type")}><option value="placement">Placement</option><option value="award">Award</option><option value="finalist">Finalist</option><option value="participation">Participation</option><option value="other">Other</option></select></Field>
    <Field title="Title" error={errors.title?.message}><input className={fieldClass} {...register("title")} /></Field>
    <Field title="Rank" error={errors.rank?.message}><input type="number" min="1" className={fieldClass} {...register("rank")} /></Field>
    <Field title="Total participants" error={errors.total_participants?.message}><input type="number" min="1" className={fieldClass} {...register("total_participants")} /></Field>
    <Field title="Description"><textarea className={fieldClass} {...register("description")} /></Field>
    <Field title="Evidence URL" error={errors.evidence_url?.message}><input type="url" className={fieldClass} {...register("evidence_url")} /></Field>
    <Field title="Linked submission (optional)"><select className={fieldClass} value={submissionId} onChange={(e) => setSubmissionId(e.target.value)}><option value="">No linked submission</option>{submissions.map((item) => <option key={item.id} value={item.id}>{item.project_title}</option>)}</select></Field>
    {error && <p role="alert" className="sm:col-span-2 text-sm text-rose-700">{error}</p>}<button disabled={isSubmitting} className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{isSubmitting ? "Saving…" : "Add achievement"}</button>
  </form>;
}

export function HackathonDetail({ event, projects, refresh, onDeleted }: { event: Event; projects: Project[]; refresh: () => Promise<void>; onDeleted: () => void }) {
  const [editing, setEditing] = useState<Editing>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [error, setError] = useState("");
  const projectMap = new Map(projects.map((project) => [project.id, project]));
  const verifiedAchievements = event.achievements.filter((item) => item.verification_status === "verified");
  const hasVerifiedAchievement = verifiedAchievements.length > 0;
  const verifiedSubmissionIds = new Set(verifiedAchievements.map((item) => item.submission).filter((id): id is number => id !== null));
  const verifiedProjectIds = new Set(event.submissions.filter((item) => verifiedSubmissionIds.has(item.id)).map((item) => item.project));
  const remove = async (resource: Resource, id: number, consequence: string) => {
    if (deleting || !window.confirm(`Delete this ${resource.slice(0, -1)}? ${consequence}`)) return;
    setDeleting(`${resource}-${id}`); setError("");
    try { await hackathonApi.remove(resource, id); toast.success("Record deleted"); await refresh(); if (resource === "events") onDeleted(); }
    catch (err) { setError(getApiErrorMessage(err, "Could not delete record.")); }
    finally { setDeleting(null); }
  };
  const controls = (resource: Resource, id: number, record: Record<string, unknown>, consequence: string, canEdit = true) => <div className="flex gap-3 text-xs font-semibold"><button disabled={!canEdit} onClick={() => setEditing({ resource, id })} className="text-violet-700 disabled:opacity-40">Edit</button><button disabled={!canEdit || !!deleting} onClick={() => remove(resource, id, consequence)} className="text-rose-600 disabled:opacity-40">{deleting === `${resource}-${id}` ? "Deleting…" : "Delete"}</button>{editing?.resource === resource && editing.id === id && <span className="sr-only">Editing {String(record.id)}</span>}</div>;
  const editor = (resource: Resource, id: number, record: Record<string, unknown>) => editing?.resource === resource && editing.id === id ? <Editor resource={resource} record={record} submissionOptions={event.submissions} onSaved={async () => { setEditing(null); await refresh(); }} onCancel={() => setEditing(null)} /> : null;
  return <article className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-semibold text-slate-950">{event.name}</h2><p className="mt-1 text-sm text-slate-500">{event.organizer || "Organizer not set"} · {date(event.start_date)}{event.end_date ? ` – ${date(event.end_date)}` : ""} · {format(event.format)}</p>{hasVerifiedAchievement && <p className="mt-1 text-xs text-violet-700">Verified achievements protect related details from edits.</p>}{event.description && <p className="mt-2 text-sm text-slate-700">{event.description}</p>}{event.event_url && <a href={event.event_url} target="_blank" rel="noopener noreferrer" className="text-sm text-violet-700 underline">Event website</a>}</div>{controls("events", event.id, event as unknown as Record<string, unknown>, "Its participation, submissions, and achievements will also be deleted.", event.source === "manual" && !hasVerifiedAchievement)}</div>
    {editor("events", event.id, event as unknown as Record<string, unknown>)}
    {event.participation && <section className="border-t border-slate-100 pt-4"><div className="flex justify-between gap-3"><div><h3 className="font-semibold">Participation</h3><p className="text-sm text-slate-600">{format(event.participation.status)}{event.participation.team_name ? ` · ${event.participation.team_name}` : ""}{event.participation.role ? ` · ${event.participation.role}` : ""}</p></div>{controls("participations", event.participation.id, event.participation as unknown as Record<string, unknown>, "Its achievements will also be deleted.", !hasVerifiedAchievement)}</div>{editor("participations", event.participation.id, event.participation as unknown as Record<string, unknown>)}</section>}
    <section className="border-t border-slate-100 pt-4"><h3 className="font-semibold">Projects & submissions</h3>{event.submissions.length === 0 ? <p className="mt-2 text-sm text-slate-500">No projects submitted yet.</p> : <div className="mt-3 space-y-3">{event.submissions.map((submission: Submission) => { const project = projectMap.get(submission.project); return <div key={submission.id} className="rounded-xl border border-slate-200 p-4"><div className="flex justify-between gap-3"><div><p className="font-medium">{submission.project_title}</p><p className="text-xs text-slate-500">{format(submission.status)}</p>{submission.submission_url && <a href={submission.submission_url} target="_blank" rel="noopener noreferrer" className="text-xs text-violet-700 underline">Submission link</a>}</div>{controls("submissions", submission.id, submission as unknown as Record<string, unknown>, "Achievements linked to it will retain their participation and lose the submission link.", submission.source === "manual" && !verifiedSubmissionIds.has(submission.id))}</div>{editor("submissions", submission.id, submission as unknown as Record<string, unknown>)}{project && <div className="mt-3 border-t border-slate-100 pt-3"><div className="flex justify-between gap-3"><p className="text-sm text-slate-600">Project details · {project.technologies.join(", ") || "No technologies listed"}</p>{controls("projects", project.id, project as unknown as Record<string, unknown>, "All submissions of this project across hackathons will be deleted.", project.source === "manual" && !verifiedProjectIds.has(project.id))}</div>{editor("projects", project.id, project as unknown as Record<string, unknown>)}</div>}</div>; })}</div>}</section>
    <section className="border-t border-slate-100 pt-4"><h3 className="font-semibold">Achievements</h3>{event.achievements.length === 0 && <p className="mt-2 text-sm text-slate-500">No achievements recorded yet.</p>}{event.achievements.map((achievement: Achievement) => <div key={achievement.id} className="mt-3 rounded-xl border border-slate-200 p-4"><div className="flex justify-between gap-3"><div><p className="font-medium">{achievement.title}{achievement.rank != null ? ` · Rank ${achievement.rank}` : ""}</p><p className="text-xs text-slate-500">{format(achievement.achievement_type)} · {achievement.verification_status === "verified" ? "Verified" : "Self-reported"}{achievement.total_participants ? ` · ${achievement.total_participants} participants` : ""}</p>{achievement.description && <p className="mt-1 text-sm text-slate-600">{achievement.description}</p>}{achievement.evidence_url && <a href={achievement.evidence_url} target="_blank" rel="noopener noreferrer" className="text-xs text-violet-700 underline">Evidence</a>}</div>{controls("achievements", achievement.id, achievement as unknown as Record<string, unknown>, "This achievement will be permanently removed.", achievement.verification_status !== "verified")}</div>{editor("achievements", achievement.id, achievement as unknown as Record<string, unknown>)}</div>)}{event.participation && <AchievementAdd participationId={event.participation.id} submissions={event.submissions} onSaved={refresh} />}</section>
    {error && <p role="alert" className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
  </article>;
}
