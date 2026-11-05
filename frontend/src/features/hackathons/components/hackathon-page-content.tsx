"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { useAuth } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/utils";
import { hackathonApi } from "../api";
import type { Event, EventFilters, Overview, Page, Project, ProjectFilters } from "../types";
import { HackathonEntryForm } from "./hackathon-entry-form";
import { Editor, HackathonDetail } from "./hackathon-detail";
import { DevpostIntegration } from "./devpost-integration";
import { EventDiscoveryFilters, ProjectDiscoveryFilters, initialEventFilters, initialProjectFilters } from "./discovery-filters";
import { ProjectManagementCard } from "./project-management-card";

export function HackathonPageContent() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [events, setEvents] = useState<Page<Event> | null>(null);
  const [projects, setProjects] = useState<Page<Project> | null>(null);
  const [eventPage, setEventPage] = useState(1);
  const [projectPage, setProjectPage] = useState(1);
  const [eventFilters, setEventFilters] = useState<EventFilters>(initialEventFilters);
  const [projectFilters, setProjectFilters] = useState<ProjectFilters>(initialProjectFilters);
  const [selected, setSelected] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  const [editingProject, setEditingProject] = useState<number | null>(null);
  const [deletingProject, setDeletingProject] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState("");
  const requestSerial = useRef(0);
  const invalidateRequests = useCallback(() => { requestSerial.current += 1; }, []);

  const refresh = useCallback(async () => {
    const serial = ++requestSerial.current;
    setFetching(true);
    try {
      const [summary, eventData, projectData] = await Promise.all([
        hackathonApi.overview(), hackathonApi.events(eventPage, "", eventFilters),
        hackathonApi.projects(projectPage, 20, "", projectFilters),
      ]);
      if (serial === requestSerial.current) {
        setOverview(summary); setEvents(eventData); setProjects(projectData); setError("");
      }
    } catch (cause) {
      if (serial === requestSerial.current) setError(getApiErrorMessage(cause, "Could not load hackathons."));
    } finally {
      if (serial === requestSerial.current) { setFetching(false); setLoading(false); }
    }
  }, [eventPage, eventFilters, projectPage, projectFilters]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) { router.replace("/login"); return; }
    const timer = window.setTimeout(() => void refresh(), 0);
    return () => { window.clearTimeout(timer); invalidateRequests(); };
  }, [authLoading, user, router, refresh, invalidateRequests]);

  const changeEventFilters = (next: EventFilters) => { setEventFilters(next); setEventPage(1); setSelected(null); };
  const changeProjectFilters = (next: ProjectFilters) => { setProjectFilters(next); setProjectPage(1); };
  const selectedEvent = events?.results.find((event) => event.id === selected) ?? null;

  const deleteProject = async (id: number) => {
    if (deletingProject || !window.confirm("Delete this project? All of its hackathon submissions will also be deleted.")) return;
    setDeletingProject(id);
    try { await hackathonApi.remove("projects", id); toast.success("Project deleted"); await refresh(); }
    catch (cause) { toast.error(getApiErrorMessage(cause, "Could not delete project.")); }
    finally { setDeletingProject(null); }
  };

  return <main className="min-h-screen bg-slate-50 text-slate-900"><div className="mx-auto grid min-h-screen w-full grid-cols-1 lg:grid-cols-[300px_minmax(0,1fr)]">
    <aside className="hidden bg-white p-5 lg:block lg:border-r lg:border-slate-200"><DashboardSidebar activeItem="hackathon" /></aside>
    <div className="min-w-0"><DashboardMobileNav activeItem="hackathon" /><div className="mx-auto max-w-7xl space-y-6 p-5 sm:p-6 lg:p-8">
      <header className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-[28px] font-semibold text-slate-950">Hackathons</h1>
        <p className="mt-1 text-sm text-slate-600 sm:text-base">Track your hackathon participation, projects, and achievements.</p></div>
        <button type="button" onClick={() => setAdding(true)} disabled={!user} className="rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-violet-700 disabled:opacity-50">Add Hackathon</button></header>
      {authLoading || !user || loading ? <div role="status" className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading hackathons…</div> : <>
        {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error} <button type="button" onClick={() => void refresh()} className="ml-2 font-semibold underline">Retry</button></div>}
        {fetching && <p role="status" className="text-xs text-violet-700">Updating results…</p>}
        <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">{([
          ["Hackathons attended", overview?.hackathons_attended], ["Projects submitted", overview?.projects_submitted],
          ["Achievements recorded", overview?.achievements_recorded], ["Placements recorded", overview?.placements_recorded],
        ] as const).map(([name, count]) => <div key={name} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5"><p className="text-xs font-medium text-slate-500">{name}</p><p className="mt-2 text-2xl font-semibold text-slate-950">{count ?? "—"}</p></div>)}</div>
        <DevpostIntegration onImported={refresh} />
        {adding && <HackathonEntryForm onCancel={() => setAdding(false)} onSaved={async () => { setAdding(false); setEventPage(1); await refresh(); toast.success("Hackathon saved"); }} />}
        <section aria-labelledby="events-heading"><h2 id="events-heading" className="text-lg font-semibold">Your hackathons</h2>
          <EventDiscoveryFilters filters={eventFilters} onChange={changeEventFilters} onReset={() => changeEventFilters(initialEventFilters)} />
          <p className="mt-3 text-xs text-slate-500">{events?.count ?? 0} matching hackathon{events?.count === 1 ? "" : "s"}</p>
          {events?.count === 0 ? <div className="mt-3 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">No hackathons match these filters.</div> :
            <div className="mt-3 grid gap-3 md:grid-cols-2">{events?.results.map((event) => <article key={event.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex justify-between gap-3"><div><h3 className="font-semibold text-slate-950">{event.name} <span className="ml-2 text-xs font-normal text-slate-500">{event.source === "devpost" ? "Devpost import" : "Manual"}</span></h3>
                <p className="mt-1 text-xs text-slate-500">{event.organizer || "Organizer not set"} · {event.start_date || "Date not set"} · {event.format.replaceAll("_", " ")}</p></div>
                <span className="h-fit rounded-full bg-violet-50 px-2.5 py-1 text-xs text-violet-700">{event.participation?.status || "No participation"}</span></div>
              <p className="mt-3 text-xs text-slate-500">{event.submissions.length} project submission{event.submissions.length === 1 ? "" : "s"} · {event.achievements.length} achievement{event.achievements.length === 1 ? "" : "s"}</p>
              <button type="button" onClick={() => setSelected(selected === event.id ? null : event.id)} className="mt-4 text-sm font-semibold text-violet-700">{selected === event.id ? "Hide details" : "View & manage"}</button>
            </article>)}</div>}
          <div className="mt-3 flex items-center justify-between text-sm"><button type="button" disabled={!events?.previous || fetching} onClick={() => { setSelected(null); setEventPage((page) => page - 1); }} className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40">Previous</button>
            <span>Page {eventPage} · {events?.count ?? 0} hackathons</span><button type="button" disabled={!events?.next || fetching} onClick={() => { setSelected(null); setEventPage((page) => page + 1); }} className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40">Next</button></div>
        </section>
        {selectedEvent && <HackathonDetail event={selectedEvent} projects={projects?.results ?? []} refresh={refresh} onDeleted={() => setSelected(null)} />}
        <section aria-labelledby="projects-heading" className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h2 id="projects-heading" className="text-lg font-semibold">Your projects</h2>
          <p className="mt-1 text-xs text-slate-500">Projects can be reused in multiple hackathons. Publishing a project does not publish its participation.</p>
          <ProjectDiscoveryFilters filters={projectFilters} onChange={changeProjectFilters} onReset={() => changeProjectFilters(initialProjectFilters)} />
          <p className="mt-3 text-xs text-slate-500">{projects?.count ?? 0} matching project{projects?.count === 1 ? "" : "s"}</p>
          {projects?.count === 0 ? <p className="mt-4 text-sm text-slate-500">No projects match these filters.</p> : <div className="mt-4 space-y-3">{projects?.results.map((project) =>
            <ProjectManagementCard key={project.id} project={project} onSaved={refresh} onEdit={() => setEditingProject(project.id)} onDelete={() => void deleteProject(project.id)} deleting={deletingProject === project.id}>
              {editingProject === project.id && <Editor resource="projects" record={project as unknown as Record<string, unknown>} onCancel={() => setEditingProject(null)} onSaved={async () => { setEditingProject(null); await refresh(); }} />}
            </ProjectManagementCard>)}</div>}
          <div className="mt-3 flex items-center justify-between text-sm"><button type="button" disabled={!projects?.previous || fetching} onClick={() => setProjectPage((page) => page - 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40">Previous</button>
            <span>Page {projectPage} · {projects?.count ?? 0} projects</span><button type="button" disabled={!projects?.next || fetching} onClick={() => setProjectPage((page) => page + 1)} className="rounded-lg border border-slate-200 px-3 py-1.5 disabled:opacity-40">Next</button></div>
        </section>
      </>}
    </div></div></div></main>;
}
