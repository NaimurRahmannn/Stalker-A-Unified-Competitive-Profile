"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { useAuth } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/utils";
import { hackathonApi } from "../api";
import type { Event, Overview, Page, Project } from "../types";
import { HackathonEntryForm } from "./hackathon-entry-form";
import { Editor, HackathonDetail } from "./hackathon-detail";

export function HackathonPageContent() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [events, setEvents] = useState<Page<Event> | null>(null);
  const [projects, setProjects] = useState<Page<Project> | null>(null);
  const [eventPage, setEventPage] = useState(1);
  const [projectPage, setProjectPage] = useState(1);
  const [selected, setSelected] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  const [editingProject, setEditingProject] = useState<number | null>(null);
  const [deletingProject, setDeletingProject] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [summary, eventData, projectData] = await Promise.all([hackathonApi.overview(), hackathonApi.events(eventPage), hackathonApi.projects(projectPage)]);
      setOverview(summary); setEvents(eventData); setProjects(projectData); setError("");
    } catch (err) { setError(getApiErrorMessage(err, "Could not load hackathons.")); }
    finally { setLoading(false); }
  }, [eventPage, projectPage]);

  useEffect(() => { if (authLoading) return; if (!user) { router.replace("/login"); return; } const timer = window.setTimeout(() => void refresh(), 0); return () => window.clearTimeout(timer); }, [authLoading, user, router, refresh]);
  const selectedEvent = events?.results.find((event) => event.id === selected) ?? null;
  const deleteProject = async (id: number) => {
    if (deletingProject || !window.confirm("Delete this project? All of its hackathon submissions will also be deleted.")) return;
    setDeletingProject(id);
    try { await hackathonApi.remove("projects", id); toast.success("Project deleted"); await refresh(); }
    catch (err) { toast.error(getApiErrorMessage(err, "Could not delete project.")); }
    finally { setDeletingProject(null); }
  };

  return <main className="min-h-screen bg-slate-50 text-slate-900"><div className="mx-auto grid min-h-screen w-full grid-cols-1 lg:grid-cols-[300px_minmax(0,1fr)]"><aside className="hidden bg-white p-5 lg:block lg:border-r lg:border-slate-200"><DashboardSidebar activeItem="hackathon" /></aside><div className="min-w-0"><DashboardMobileNav activeItem="hackathon" /><div className="mx-auto max-w-7xl space-y-6 p-5 sm:p-6 lg:p-8">
    <header className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-[28px] font-semibold text-slate-950">Hackathons</h1><p className="mt-1 text-sm text-slate-600 sm:text-base">Track your hackathon participation, projects, and achievements.</p></div><button onClick={() => setAdding(true)} disabled={!user} className="rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-violet-700 disabled:opacity-50">Add Hackathon</button></header>
    {authLoading || !user || loading ? <div role="status" className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading hackathons…</div> : <>
      {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error} <button onClick={() => void refresh()} className="ml-2 font-semibold underline">Retry</button></div>}
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">{([ ["Hackathons attended", overview?.hackathons_attended], ["Projects submitted", overview?.projects_submitted], ["Achievements recorded", overview?.achievements_recorded], ["Placements recorded", overview?.placements_recorded] ] as const).map(([name, count]) => <div key={name} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5"><p className="text-xs font-medium text-slate-500">{name}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{count ?? "—"}</p></div>)}</div>
      {adding && <HackathonEntryForm events={events?.results ?? []} projects={projects?.results ?? []} onCancel={() => setAdding(false)} onSaved={async () => { setAdding(false); setEventPage(1); await refresh(); toast.success("Hackathon saved"); }} />}
      <section><h2 className="mb-3 text-lg font-semibold">Your hackathons</h2>{events?.count === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">No hackathons recorded yet. Add your first one above.</div> : <div className="grid gap-3 md:grid-cols-2">{events?.results.map((event) => <article key={event.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex justify-between gap-3"><div><h3 className="font-semibold text-slate-950">{event.name}</h3><p className="mt-1 text-xs text-slate-500">{event.organizer || "Organizer not set"} · {event.start_date || "Date not set"} · {event.format.replaceAll("_", " ")}</p></div><span className="h-fit rounded-full bg-violet-50 px-2.5 py-1 text-xs text-violet-700">{event.participation?.status || "No participation"}</span></div><p className="mt-3 text-xs text-slate-500">{event.submissions.length} project submission{event.submissions.length === 1 ? "" : "s"} · {event.achievements.length} achievement{event.achievements.length === 1 ? "" : "s"}</p><button onClick={() => setSelected(selected === event.id ? null : event.id)} className="mt-4 text-sm font-semibold text-violet-700">{selected === event.id ? "Hide details" : "View & manage"}</button></article>)}</div>}
        <div className="mt-3 flex items-center justify-between text-sm"><button disabled={!events?.previous} onClick={() => setEventPage((page) => page - 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40">Previous</button><span>Page {eventPage} · {events?.count ?? 0} hackathons</span><button disabled={!events?.next} onClick={() => { setSelected(null); setEventPage((page) => page + 1); }} className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40">Next</button></div>
      </section>
      {selectedEvent && <HackathonDetail event={selectedEvent} projects={projects?.results ?? []} refresh={refresh} onDeleted={() => setSelected(null)} />}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h2 className="text-lg font-semibold">Your projects</h2><p className="mt-1 text-xs text-slate-500">Projects can be reused in multiple hackathons. New projects stay private by default.</p>{projects?.count === 0 ? <p className="mt-4 text-sm text-slate-500">No projects yet.</p> : <div className="mt-4 space-y-3">{projects?.results.map((project) => <div key={project.id} className="rounded-xl border border-slate-200 p-4"><div className="flex flex-wrap justify-between gap-3"><div><p className="font-medium">{project.title}</p><p className="text-xs text-slate-500">{project.technologies.join(", ") || "No technologies listed"} · {project.is_public ? "Public" : "Private"}</p></div><div className="flex gap-3 text-xs font-semibold"><button disabled={project.source !== "manual"} onClick={() => setEditingProject(project.id)} className="text-violet-700 disabled:opacity-40">Edit</button><button disabled={project.source !== "manual" || !!deletingProject} onClick={() => void deleteProject(project.id)} className="text-rose-600 disabled:opacity-40">{deletingProject === project.id ? "Deleting…" : "Delete"}</button></div></div>{editingProject === project.id && <Editor resource="projects" record={project as unknown as Record<string, unknown>} onCancel={() => setEditingProject(null)} onSaved={async () => { setEditingProject(null); await refresh(); }} />}</div>)}</div>}<div className="mt-3 flex items-center justify-between text-sm"><button disabled={!projects?.previous} onClick={() => setProjectPage((page) => page - 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40">Previous</button><span>Page {projectPage} · {projects?.count ?? 0} projects</span><button disabled={!projects?.next} onClick={() => setProjectPage((page) => page + 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40">Next</button></div></section>
    </>}
  </div></div></div></main>;
}
