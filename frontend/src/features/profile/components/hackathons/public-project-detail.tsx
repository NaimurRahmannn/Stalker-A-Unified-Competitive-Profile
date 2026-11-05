"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AxiosError } from "axios";
import { Trophy } from "lucide-react";
import { getApiErrorMessage } from "@/lib/utils";
import { verificationLabel } from "@/features/hackathons/verification";
import { getPublicHackathonProject } from "../../api";
import type { PublicHackathonProjectDetail } from "../../types";
import { safeExternalUrl } from "./safe-external-url";

function External({ href, children }: { href: string | null; children: React.ReactNode }) {
  const safe = safeExternalUrl(href);
  return safe ? <a href={safe} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold text-violet-700 underline underline-offset-2">{children}</a> : null;
}

export function PublicProjectDetailContent({ detail, username }: { detail: PublicHackathonProjectDetail; username: string }) {
  const { project, submissions, achievements } = detail;
  const [imageFailed, setImageFailed] = useState(false);
  const image = safeExternalUrl(project.image_url);
  return <main className="min-h-screen bg-slate-50 px-5 py-8 text-slate-900 sm:px-8">
    <div className="mx-auto max-w-5xl space-y-6">
      <Link href={`/profile/${encodeURIComponent(username)}`} className="text-sm font-semibold text-violet-700 underline">Back to {username}&apos;s profile</Link>
      <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex h-64 items-center justify-center bg-gradient-to-br from-violet-100 via-indigo-50 to-slate-100">
          {image && !imageFailed ? <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={image} alt="" className="h-full w-full object-cover" onError={() => setImageFailed(true)} />
          </> : <Trophy className="size-14 text-violet-300" aria-hidden="true" />}
        </div>
        <div className="space-y-5 p-6 sm:p-8">
          <div><p className="text-xs font-semibold uppercase tracking-wide text-violet-700">{project.source === "devpost" ? "Devpost import" : "Manual project"}</p>
            <h1 className="mt-1 wrap-break-word text-2xl font-bold text-slate-950 sm:text-3xl">{project.title}</h1></div>
          {project.description ? <p className="whitespace-pre-wrap wrap-break-word text-sm leading-7 text-slate-700">{project.description}</p> :
            <p className="text-sm text-slate-500">No description provided.</p>}
          {project.technologies.length > 0 && <ul aria-label="Technologies" className="flex flex-wrap gap-2">{project.technologies.map((item, index) =>
            <li key={`${index}-${item}`} className="rounded-full bg-violet-50 px-3 py-1 text-xs font-medium text-violet-800">{item}</li>)}</ul>}
          <div className="flex flex-wrap gap-4"><External href={project.project_url}>{project.source === "devpost" ? "Devpost project" : "Project website"}</External>
            <External href={project.repository_url}>Repository</External><External href={project.demo_url}>Live demo</External>
            <External href={project.video_url}>Video</External></div>
        </div>
      </article>
      <section aria-labelledby="project-submissions" className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 id="project-submissions" className="text-lg font-semibold">Public hackathon submissions</h2>
        {detail.submission_count > 20 && <p className="mt-1 text-xs text-slate-500">Showing the latest 20 of {detail.submission_count} submissions.</p>}
        {submissions.length ? <ul className="mt-4 space-y-3">{submissions.map((row) => <li key={row.id} className="rounded-xl border border-slate-100 p-4">
          <p className="font-medium">{row.event_name}</p><div className="mt-2 flex flex-wrap gap-4"><External href={row.event_url}>Event website</External>
            <External href={row.submission_url}>Submission</External></div></li>)}</ul> :
          <p className="mt-3 text-sm text-slate-500">No submitted work has been shared for this project.</p>}
      </section>
      <section aria-labelledby="project-achievements" className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 id="project-achievements" className="text-lg font-semibold">Public achievements</h2>
        {detail.achievement_count > 20 && <p className="mt-1 text-xs text-slate-500">Showing the latest 20 of {detail.achievement_count} achievements.</p>}
        {achievements.length ? <ul className="mt-4 space-y-3">{achievements.map((row) => <li key={row.id} className="rounded-xl border border-slate-100 p-4">
          <div className="flex flex-wrap items-start justify-between gap-2"><h3 className="font-medium">{row.title}</h3>
            <span className={`rounded-full px-2 py-1 text-xs font-semibold ${row.verification_status === "verified" ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-700"}`}>{verificationLabel[row.verification_status]}</span></div>
          <p className="mt-1 text-xs capitalize text-slate-500">{row.achievement_type.replaceAll("_", " ")}{row.rank != null ? ` · Rank ${row.rank}` : ""}</p>
          {row.description && <p className="mt-2 text-sm text-slate-600">{row.description}</p>}</li>)}</ul> :
          <p className="mt-3 text-sm text-slate-500">No achievements have been shared for this project.</p>}
      </section>
    </div>
  </main>;
}

export function PublicProjectDetail({ username, projectId }: { username: string; projectId: number }) {
  const [detail, setDetail] = useState<PublicHackathonProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let active = true;
    void getPublicHackathonProject(username, projectId).then((data) => { if (active) { setDetail(data); setError(""); setNotFound(false); } })
      .catch((cause: unknown) => { if (active) { setNotFound(cause instanceof AxiosError && cause.response?.status === 404); setError(getApiErrorMessage(cause, "Could not load project.")); } })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [username, projectId, version]);
  if (loading && !detail) return <main role="status" className="min-h-screen bg-slate-50 p-8 text-sm text-slate-600">Loading project…</main>;
  if (!detail) return <main className="min-h-screen bg-slate-50 p-8"><div className="mx-auto max-w-xl rounded-2xl border border-slate-200 bg-white p-8">
    <h1 className="text-xl font-semibold">{notFound ? "Project not found" : "Could not load project"}</h1>
    <p role="alert" className="mt-2 text-sm text-slate-600">{notFound ? "This project is unavailable or private." : error}</p>
    {!notFound && <button type="button" onClick={() => { setLoading(true); setVersion((value) => value + 1); }} className="mt-4 text-sm font-semibold text-violet-700 underline">Retry</button>}
    <Link href={`/profile/${encodeURIComponent(username)}`} className="ml-4 text-sm font-semibold text-violet-700 underline">Back to profile</Link>
  </div></main>;
  return <PublicProjectDetailContent detail={detail} username={username} />;
}
