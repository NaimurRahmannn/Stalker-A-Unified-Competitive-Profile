"use client";

import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { hackathonApi } from "../api";
import { achievementPayload, blankAchievement, blankEntry, entrySchema, type EntryFormValues } from "../schemas";
import type { Event, Project } from "../types";
import { getApiErrorMessage } from "@/lib/utils";
import { useState } from "react";

const input = "mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100";
const label = "block text-xs font-semibold text-slate-600";

export function HackathonEntryForm({ events, projects, onSaved, onCancel }: { events: Event[]; projects: Project[]; onSaved: () => Promise<void>; onCancel: () => void }) {
  const [serverError, setServerError] = useState("");
  const { register, handleSubmit, control, reset, setValue, formState: { errors, isSubmitting } } = useForm<EntryFormValues>({ resolver: zodResolver(entrySchema), defaultValues: blankEntry() });
  const { fields, append, remove } = useFieldArray({ control, name: "achievements" });
  const eventMode = useWatch({ control, name: "eventMode" });
  const projectMode = useWatch({ control, name: "projectMode" });
  const values = useWatch({ control });

  const save = handleSubmit(async (value) => {
    setServerError("");
    const payload: Record<string, unknown> = {
      participation: { status: value.status, team_name: value.team_name, role: value.role },
      achievements: value.achievements.map((item) => ({ ...achievementPayload(item), link_submission: value.projectMode !== "none" && item.link_submission })),
    };
    if (value.eventMode === "existing") payload.event_id = Number(value.eventId);
    else payload.event = { name: value.name.trim(), organizer: value.organizer, description: value.description, event_url: value.event_url, start_date: value.start_date || null, end_date: value.end_date || null, format: value.format };
    if (value.projectMode !== "none") {
      if (value.projectMode === "existing") payload.project_id = Number(value.projectId);
      else payload.project = { title: value.title.trim(), description: value.project_description, repository_url: value.repository_url, demo_url: value.demo_url, video_url: value.video_url, image_url: value.image_url, technologies: value.technologies.split(",").map((item) => item.trim()).filter(Boolean) };
      payload.submission = { status: value.submission_status, submission_url: value.submission_url, submitted_at: value.submitted_at ? new Date(value.submitted_at).toISOString() : null };
    }
    try {
      await hackathonApi.entries(payload);
      reset(blankEntry());
      await onSaved();
    } catch (error) { setServerError(getApiErrorMessage(error, "Could not save hackathon.")); }
  });

  return <form onSubmit={save} noValidate className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
    <div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Add Hackathon</h2><button type="button" onClick={onCancel} className="text-sm text-slate-500 hover:text-slate-900">Close</button></div>
    <section className="space-y-3"><h3 className="font-semibold text-violet-700">1. Hackathon details</h3>
      <label className={label}>Entry type<select className={input} {...register("eventMode")}><option value="new">New hackathon</option><option value="existing">Existing hackathon</option></select></label>
      {eventMode === "existing" ? <label className={label}>Hackathon<select className={input} {...register("eventId", { onChange: (change) => { const selected = events.find((event) => event.id === Number(change.target.value)); if (selected?.participation) { setValue("status", selected.participation.status); setValue("team_name", selected.participation.team_name); setValue("role", selected.participation.role); } } })}><option value="">Select a hackathon</option>{events.map((event) => <option key={event.id} value={event.id}>{event.name}</option>)}</select><Error text={errors.eventId?.message} /></label> : <div className="grid gap-3 sm:grid-cols-2">
        <Field title="Hackathon name" error={errors.name?.message}><input className={input} {...register("name")} /></Field>
        <Field title="Organizer"><input className={input} {...register("organizer")} /></Field>
        <Field title="Description"><textarea className={input} rows={2} {...register("description")} /></Field>
        <Field title="Event URL" error={errors.event_url?.message}><input type="url" className={input} {...register("event_url")} /></Field>
        <Field title="Start date"><input type="date" className={input} {...register("start_date")} /></Field>
        <Field title="End date" error={errors.end_date?.message}><input type="date" className={input} {...register("end_date")} /></Field>
        <Field title="Format"><select className={input} {...register("format")}><option value="unknown">Unknown</option><option value="online">Online</option><option value="in_person">In person</option><option value="hybrid">Hybrid</option></select></Field>
      </div>}
    </section>
    <section className="space-y-3 border-t border-slate-100 pt-5"><h3 className="font-semibold text-violet-700">2. Participation</h3><p className="text-xs text-slate-500">Participation and submission statuses are independent. Registered does not count as attended.</p>
      <div className="grid gap-3 sm:grid-cols-3"><Field title="Status"><select className={input} {...register("status")}><option value="registered">Registered</option><option value="attended">Attended</option><option value="submitted">Submitted</option></select></Field><Field title="Team name"><input className={input} {...register("team_name")} /></Field><Field title="Role"><input className={input} {...register("role")} /></Field></div>
    </section>
    <section className="space-y-3 border-t border-slate-100 pt-5"><h3 className="font-semibold text-violet-700">3. Project & submission (optional)</h3>
      <Field title="Project"><select className={input} {...register("projectMode")}><option value="none">No project</option><option value="new">Create a project</option><option value="existing">Use an existing project</option></select></Field>
      {projectMode === "existing" && <Field title="Existing project" error={errors.projectId?.message}><select className={input} {...register("projectId")}><option value="">Select a project</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}</select></Field>}
      {projectMode === "new" && <div className="grid gap-3 sm:grid-cols-2"><Field title="Project title" error={errors.title?.message}><input className={input} {...register("title")} /></Field><Field title="Technologies (comma separated)"><input className={input} {...register("technologies")} /></Field><Field title="Description"><textarea className={input} rows={2} {...register("project_description")} /></Field>{(["repository_url", "demo_url", "video_url", "image_url"] as const).map((key) => <Field key={key} title={key.replaceAll("_", " ")} error={errors[key]?.message}><input type="url" className={input} {...register(key)} /></Field>)}</div>}
      {projectMode !== "none" && <div className="grid gap-3 sm:grid-cols-3"><Field title="Submission status"><select className={input} {...register("submission_status")}><option value="draft">Draft</option><option value="submitted">Submitted</option><option value="withdrawn">Withdrawn</option></select></Field><Field title="Submission URL" error={errors.submission_url?.message}><input type="url" className={input} {...register("submission_url")} /></Field><Field title="Submitted at"><input type="datetime-local" className={input} {...register("submitted_at")} /></Field></div>}
    </section>
    <section className="space-y-3 border-t border-slate-100 pt-5"><div className="flex items-center justify-between"><h3 className="font-semibold text-violet-700">4. Achievements (optional)</h3><button type="button" onClick={() => append(blankAchievement())} className="rounded-lg border border-violet-200 px-3 py-1.5 text-xs font-semibold text-violet-700">Add achievement</button></div>
      {fields.map((field, index) => <div key={field.id} className="grid gap-3 rounded-xl border border-slate-200 p-4 sm:grid-cols-2"><Field title="Type"><select className={input} {...register(`achievements.${index}.achievement_type`)}><option value="placement">Placement</option><option value="award">Award</option><option value="finalist">Finalist</option><option value="participation">Participation</option><option value="other">Other</option></select></Field><Field title="Title" error={errors.achievements?.[index]?.title?.message}><input className={input} {...register(`achievements.${index}.title`)} /></Field><Field title="Rank" error={errors.achievements?.[index]?.rank?.message}><input type="number" min="1" className={input} {...register(`achievements.${index}.rank`)} /></Field><Field title="Total participants" error={errors.achievements?.[index]?.total_participants?.message}><input type="number" min="1" className={input} {...register(`achievements.${index}.total_participants`)} /></Field><Field title="Description"><textarea className={input} rows={2} {...register(`achievements.${index}.description`)} /></Field><Field title="Evidence URL" error={errors.achievements?.[index]?.evidence_url?.message}><input type="url" className={input} {...register(`achievements.${index}.evidence_url`)} /></Field>{projectMode !== "none" && <label className="text-xs text-slate-600"><input type="checkbox" {...register(`achievements.${index}.link_submission`)} /> Link to this submission</label>}<button type="button" onClick={() => remove(index)} className="text-left text-xs font-semibold text-rose-600">Remove achievement</button></div>)}
    </section>
    <section className="border-t border-slate-100 pt-5"><h3 className="font-semibold text-violet-700">5. Review & save</h3><p className="mt-1 text-sm text-slate-600">{eventMode === "new" ? values.name || "New hackathon" : "Existing hackathon"} · {values.status} · {projectMode === "none" ? "No project" : "Project and submission"} · {fields.length} achievement{fields.length === 1 ? "" : "s"}</p></section>
    {serverError && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{serverError}</p>}
    <div className="flex gap-3"><button disabled={isSubmitting} className="rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{isSubmitting ? "Saving…" : "Save hackathon"}</button><button type="button" onClick={onCancel} className="rounded-xl border border-slate-200 px-5 py-2.5 text-sm">Cancel</button></div>
  </form>;
}

export function Field({ title, error, children }: { title: string; error?: string; children: React.ReactNode }) { return <label className={label}>{title}{children}<Error text={error} /></label>; }
function Error({ text }: { text?: string }) { return text ? <span className="mt-1 block text-xs text-rose-600">{text}</span> : null; }
export const fieldClass = input;
