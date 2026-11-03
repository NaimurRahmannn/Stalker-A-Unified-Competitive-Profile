"use client";

import { useEffect, useState } from "react";
import { ExternalLink, Trophy } from "lucide-react";
import { getApiErrorMessage } from "@/lib/utils";
import { getPublicHackathonPortfolio } from "../../api";
import type {
  PublicHackathonAchievement, PublicHackathonPortfolio as Portfolio,
  PublicHackathonProject, PublicPage,
} from "../../types";

type Collection = "projects" | "participations" | "achievements" | "submissions";
type Pages = Record<Collection, number>;
const firstPages: Pages = { projects: 1, participations: 1, achievements: 1, submissions: 1 };

function externalHref(value: string | null): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? value : null;
  } catch { return null; }
}

function ExternalLinkItem({ href, children }: { href: string | null; children: React.ReactNode }) {
  const safe = externalHref(href);
  return safe ? <a href={safe} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-violet-700 underline underline-offset-2 hover:text-violet-900">{children}<ExternalLink className="size-3" aria-hidden="true" /></a> : null;
}

function PagesControl({ page, data, onPage, disabled }: { page: number; data: PublicPage<unknown>; onPage: (page: number) => void; disabled: boolean }) {
  if (!data.next && !data.previous) return null;
  return <div className="mt-4 flex items-center justify-between gap-3 text-xs text-slate-600">
    <button type="button" disabled={disabled || !data.previous} onClick={() => onPage(page - 1)} className="rounded-lg border border-slate-200 px-3 py-2 disabled:opacity-40">Previous</button>
    <span>Page {page}</span>
    <button type="button" disabled={disabled || !data.next} onClick={() => onPage(page + 1)} className="rounded-lg border border-slate-200 px-3 py-2 disabled:opacity-40">Next</button>
  </div>;
}

function ProjectCard({ project }: { project: PublicHackathonProject }) {
  const [imageFailed, setImageFailed] = useState(false);
  const image = externalHref(project.image_url);
  return <article className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div className="relative flex h-36 items-center justify-center overflow-hidden bg-gradient-to-br from-violet-100 via-indigo-50 to-slate-100">
      {image && !imageFailed ? <>
        {/* Remote user-provided images have no configured Next.js optimization host. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={image} alt="" loading="lazy" onError={() => setImageFailed(true)} className="h-full w-full object-cover" />
      </> : <Trophy className="size-10 text-violet-300" aria-hidden="true" />}
    </div>
    <div className="space-y-3 p-5">
      <div><span className="text-[10px] font-semibold uppercase tracking-wide text-violet-700">{project.source === "devpost" ? "Devpost import" : "Manual project"}</span><h3 className="mt-1 wrap-break-word text-base font-semibold text-slate-950">{project.title}</h3></div>
      {project.description && <p className="line-clamp-3 wrap-break-word text-sm text-slate-600">{project.description}</p>}
      {project.technologies.length > 0 && <ul aria-label="Technologies" className="flex flex-wrap gap-1.5">{project.technologies.map((technology, index) => <li key={`${index}-${technology}`} className="rounded-full bg-violet-50 px-2.5 py-1 text-[11px] text-violet-800">{technology}</li>)}</ul>}
      {project.associations.length > 0 && <p className="text-xs text-slate-600">Recent public submissions: {project.associations.map((row) => row.event_name).join(", ")}</p>}
      <div className="flex flex-wrap gap-x-4 gap-y-2">
        <ExternalLinkItem href={project.project_url}>{project.source === "devpost" ? "Devpost project" : "Project website"}</ExternalLinkItem>
        <ExternalLinkItem href={project.repository_url}>Repository</ExternalLinkItem>
        <ExternalLinkItem href={project.demo_url}>Live demo</ExternalLinkItem>
        <ExternalLinkItem href={project.video_url}>Video</ExternalLinkItem>
      </div>
    </div>
  </article>;
}

const verificationLabel: Record<PublicHackathonAchievement["verification_status"], string> = {
  verified: "Verified", evidence_provided: "Evidence provided", self_reported: "Self-reported",
};

export function PublicHackathonPortfolioContent({ portfolio, pages, onPage, loading = false }: {
  portfolio: Portfolio; pages: Pages; onPage: (collection: Collection, page: number) => void; loading?: boolean;
}) {
  const { summary, projects, participations, achievements, submissions } = portfolio;
  const noRecords = Object.values(summary).every((value) => value === 0);
  return <section aria-labelledby="public-hackathons-title" className="space-y-5">
    <div className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-2"><div><h2 id="public-hackathons-title" className="text-lg font-semibold text-slate-950">Hackathon portfolio</h2><p className="mt-1 text-xs text-slate-500">Only projects and participation shared by this person appear here.</p></div>{loading && <span role="status" className="text-xs text-violet-700">Updating portfolio…</span>}</div>
      {noRecords ? <p className="mt-5 rounded-xl bg-slate-50 p-5 text-sm text-slate-600">No Hackathon work has been published yet.</p> : <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">{([
        ["Published projects", summary.published_projects], ["Public participations", summary.public_participations],
        ["Achievements", summary.public_achievements], ["Verified achievements", summary.verified_achievements],
      ] as const).map(([label, count]) => <div key={label} className="rounded-xl bg-violet-50 p-3"><strong className="block text-xl text-violet-900">{count}</strong><span className="text-xs text-violet-700">{label}</span></div>)}</div>}
    </div>
    {projects.count > 0 && <div><h3 className="mb-3 text-base font-semibold text-slate-950">Featured projects</h3><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{projects.results.map((project) => <ProjectCard key={project.id} project={project} />)}</div><PagesControl page={pages.projects} data={projects} disabled={loading} onPage={(page) => onPage("projects", page)} /></div>}
    {participations.count > 0 && <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h3 className="text-base font-semibold text-slate-950">Public participation</h3><div className="mt-3 grid gap-3 md:grid-cols-2">{participations.results.map((participation) => <article key={participation.id} className="min-w-0 rounded-xl border border-slate-200 p-4"><h4 className="wrap-break-word font-semibold text-slate-900">{participation.event.name}</h4><p className="mt-1 text-xs text-slate-500">{[participation.event.organizer, participation.event.start_date, participation.event.end_date && participation.event.end_date !== participation.event.start_date ? `to ${participation.event.end_date}` : null].filter(Boolean).join(" · ")}</p><p className="mt-2 text-sm capitalize text-slate-700">{participation.event.format.replaceAll("_", " ")} · {participation.status}</p>{(participation.team_name || participation.role) && <p className="mt-1 text-xs text-slate-600">{[participation.team_name, participation.role].filter(Boolean).join(" · ")}</p>}<ExternalLinkItem href={participation.event.event_url}>Event website</ExternalLinkItem></article>)}</div><PagesControl page={pages.participations} data={participations} disabled={loading} onPage={(page) => onPage("participations", page)} /></div>}
    {achievements.count > 0 && <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h3 className="text-base font-semibold text-slate-950">Achievements</h3><div className="mt-3 grid gap-3 md:grid-cols-2">{achievements.results.map((achievement) => <article key={achievement.id} className="min-w-0 rounded-xl border border-slate-200 p-4"><div className="flex flex-wrap items-start justify-between gap-2"><h4 className="wrap-break-word font-semibold text-slate-900">{achievement.title}</h4><span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${achievement.verification_status === "verified" ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-700"}`}>{verificationLabel[achievement.verification_status]}</span></div><p className="mt-1 text-xs capitalize text-slate-500">{achievement.achievement_type.replaceAll("_", " ")}{achievement.rank != null ? ` · Rank ${achievement.rank}` : ""}{achievement.total_participants != null ? ` of ${achievement.total_participants}` : ""}</p>{achievement.description && <p className="mt-2 text-sm text-slate-600">{achievement.description}</p>}</article>)}</div><PagesControl page={pages.achievements} data={achievements} disabled={loading} onPage={(page) => onPage("achievements", page)} /></div>}
    {submissions.count > 0 && <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h3 className="text-base font-semibold text-slate-950">Submitted work</h3><ul className="mt-3 space-y-2">{submissions.results.map((submission) => <li key={submission.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-100 p-3 text-sm"><span className="wrap-break-word text-slate-700">{submission.project_title} · {submission.event_name}</span><ExternalLinkItem href={submission.submission_url}>Submission</ExternalLinkItem></li>)}</ul><PagesControl page={pages.submissions} data={submissions} disabled={loading} onPage={(page) => onPage("submissions", page)} /></div>}
  </section>;
}

export function PublicHackathonPortfolio({ username }: { username: string }) {
  const [pages, setPages] = useState<Pages>(firstPages);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let active = true;
    void getPublicHackathonPortfolio(username, pages).then((data) => { if (active) { setPortfolio(data); setError(""); } })
      .catch((cause) => { if (active) setError(getApiErrorMessage(cause, "Could not load Hackathon portfolio.")); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [username, pages, version]);
  const onPage = (collection: Collection, page: number) => { setLoading(true); setPages((current) => ({ ...current, [collection]: page })); };
  const retry = () => { setLoading(true); setError(""); setVersion((value) => value + 1); };
  if (!portfolio && loading) return <section aria-label="Hackathon portfolio" role="status" className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Loading Hackathon portfolio…</section>;
  if (!portfolio) return <section aria-label="Hackathon portfolio" className="rounded-2xl border border-rose-200 bg-white p-6"><p role="alert" className="text-sm text-rose-700">{error}</p><button type="button" onClick={retry} className="mt-3 text-sm font-semibold text-violet-700 underline">Retry portfolio</button></section>;
  return <div>{error && <div role="alert" className="mb-3 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error} <button type="button" onClick={retry} className="font-semibold underline">Retry</button></div>}<PublicHackathonPortfolioContent portfolio={portfolio} pages={pages} onPage={onPage} loading={loading} /></div>;
}
