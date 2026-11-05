"use client";

import type { ReactNode } from "react";
import type { Project } from "../types";
import { VisibilityControl } from "./visibility-control";

function safeHref(value: string): string | null {
  if (!value) return null;
  try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? value : null; }
  catch { return null; }
}

function ProjectLink({ href, label }: { href: string; label: string }) {
  const safe = safeHref(href);
  return safe ? <a href={safe} target="_blank" rel="noopener noreferrer" className="text-xs font-semibold text-violet-700 underline underline-offset-2">{label}</a> : null;
}

export function ProjectManagementCard({ project, onSaved, onEdit, onDelete, deleting, children }: {
  project: Project; onSaved: () => Promise<void>; onEdit: () => void; onDelete: () => void; deleting: boolean; children?: ReactNode;
}) {
  const manual = project.source === "manual";
  const updated = project.updated_at ? new Date(project.updated_at) : null;
  return <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0 flex-1 space-y-2">
        <div className="flex flex-wrap items-center gap-2"><h3 className="min-w-0 wrap-break-word font-semibold text-slate-950">{project.title}</h3>
          <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${manual ? "bg-slate-100 text-slate-700" : "bg-indigo-50 text-indigo-700"}`}>{manual ? "Manual" : "Devpost import"}</span>
          <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${project.is_public ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>{project.is_public ? "Published" : "Private"}</span>
        </div>
        {project.description && <p className="line-clamp-2 wrap-break-word text-sm text-slate-600">{project.description}</p>}
        {project.technologies.length > 0 && <ul aria-label="Technologies" className="flex flex-wrap gap-1.5">{project.technologies.slice(0, 12).map((item, index) => <li key={`${index}-${item}`} className="rounded-full bg-violet-50 px-2 py-0.5 text-xs text-violet-800">{item}</li>)}{project.technologies.length > 12 && <li className="text-xs text-slate-500">+{project.technologies.length - 12} more</li>}</ul>}
        <div className="flex flex-wrap gap-x-4 gap-y-1"><ProjectLink href={project.project_url} label={manual ? "Project website" : "Devpost project"} />
          <ProjectLink href={project.repository_url} label="Repository" /><ProjectLink href={project.demo_url} label="Live demo" /></div>
        <p className="text-xs text-slate-500">{project.related_hackathon_count ?? 0} related hackathon{project.related_hackathon_count === 1 ? "" : "s"}{updated && !Number.isNaN(updated.getTime()) ? ` · Updated ${updated.toLocaleDateString()}` : ""}</p>
      </div>
      <div className="flex flex-wrap items-start gap-3 text-xs font-semibold">
        <VisibilityControl kind="project" id={project.id} isPublic={project.is_public} onSaved={onSaved} />
        <button type="button" disabled={!manual} onClick={onEdit} className="text-violet-700 disabled:opacity-40">Edit</button>
        <button type="button" disabled={!manual || deleting} onClick={onDelete} className="text-rose-600 disabled:opacity-40">{deleting ? "Deleting…" : "Delete"}</button>
      </div>
    </div>
    {children}
  </article>;
}
