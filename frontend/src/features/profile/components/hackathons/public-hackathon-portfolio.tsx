"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, Trophy } from "lucide-react";
import Link from "next/link";
import { getApiErrorMessage } from "@/lib/utils";
import { verificationLabel } from "@/features/hackathons/verification";
import { getPublicHackathonPortfolio } from "../../api";
import type {
  PublicHackathonPortfolio as Portfolio,
  PublicHackathonProject,
  PublicPage,
} from "../../types";
import { safeExternalUrl } from "./safe-external-url";

type Collection = "projects" | "participations" | "achievements" | "submissions";
type Pages = Record<Collection, number>;
const firstPages: Pages = { projects: 1, participations: 1, achievements: 1, submissions: 1 };

function ExternalLinkItem({ href, children }: { href: string | null; children: React.ReactNode }) {
  const safe = safeExternalUrl(href);
  return safe ? <a href={safe} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-[#1769b0] hover:underline">{children}<ArrowUpRight aria-hidden="true" className="size-3.5" /></a> : null;
}

function PagesControl({ page, data, onPage, disabled }: { page: number; data: PublicPage<unknown>; onPage: (page: number) => void; disabled: boolean }) {
  if (!data.next && !data.previous) return null;
  return (
    <nav aria-label="Portfolio pages" className="mt-5 flex items-center justify-between gap-3 text-xs text-slate-600">
      <button type="button" disabled={disabled || !data.previous} onClick={() => onPage(page - 1)} className="rounded-lg border border-slate-300 px-3 py-2 hover:bg-slate-50 disabled:opacity-40">Previous</button>
      <span>Page {page}</span>
      <button type="button" disabled={disabled || !data.next} onClick={() => onPage(page + 1)} className="rounded-lg border border-slate-300 px-3 py-2 hover:bg-slate-50 disabled:opacity-40">Next</button>
    </nav>
  );
}

function ProjectRow({ project, username }: { project: PublicHackathonProject; username: string }) {
  const [imageFailed, setImageFailed] = useState(false);
  const image = safeExternalUrl(project.image_url);
  return (
    <article className="grid gap-5 py-6 sm:grid-cols-[176px_minmax(0,1fr)] sm:gap-7">
      <div className="flex h-35 items-center justify-center overflow-hidden rounded-lg bg-[#edf3f8] sm:h-28">
        {image && !imageFailed ? (
          // Remote user-provided images have no configured Next.js optimization host.
          // eslint-disable-next-line @next/next/no-img-element
          <img src={image} alt="" loading="lazy" onError={() => setImageFailed(true)} className="size-full object-cover" />
        ) : <Trophy aria-hidden="true" className="size-8 text-[#85a9c9]" />}
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-[#1769b0]">{project.source === "devpost" ? "Devpost project" : "Project"}</p>
        <h4 className="mt-1 wrap-break-word text-lg font-semibold text-[#102c46]"><Link href={`/profile/${encodeURIComponent(username)}/hackathons/projects/${project.id}`} className="hover:text-[#1769b0] hover:underline">{project.title}</Link></h4>
        {project.description ? <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">{project.description}</p> : null}
        {project.technologies.length ? <p className="mt-2 text-xs text-slate-500">{project.technologies.join(" · ")}</p> : null}
        {project.associations.length ? <p className="mt-2 text-xs text-slate-500">Submitted to {project.associations.map((row) => row.event_name).join(", ")}</p> : null}
        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2">
          <ExternalLinkItem href={project.project_url}>Project website</ExternalLinkItem>
          <ExternalLinkItem href={project.repository_url}>Repository</ExternalLinkItem>
          <ExternalLinkItem href={project.demo_url}>Live demo</ExternalLinkItem>
          <ExternalLinkItem href={project.video_url}>Video</ExternalLinkItem>
        </div>
      </div>
    </article>
  );
}

export function PublicHackathonPortfolioContent({ portfolio, pages, onPage, username, loading = false }: {
  portfolio: Portfolio; pages: Pages; username: string; onPage: (collection: Collection, page: number) => void; loading?: boolean;
}) {
  const { summary, projects, participations, achievements, submissions } = portfolio;
  const noRecords = Object.values(summary).every((value) => value === 0);
  const counts = [
    ["Published projects", summary.published_projects],
    ["Participations", summary.public_participations],
    ["Achievements", summary.public_achievements],
    ["Verified", summary.verified_achievements],
  ] as const;

  return (
    <section aria-labelledby="public-hackathons-title" className="border-t border-slate-200 py-12 sm:py-14">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.17em] text-[#1769b0]">04 / Work</p>
          <h2 id="public-hackathons-title" className="mt-2 text-2xl font-bold tracking-tight text-[#102c46] sm:text-[28px]">Hackathon portfolio</h2>
          <p className="mt-2 text-sm text-slate-500">Projects, participation, and achievements shared publicly.</p>
        </div>
        {loading ? <span role="status" className="text-xs text-[#1769b0]">Updating portfolio…</span> : null}
      </div>

      {noRecords ? <p className="mt-8 border-t border-slate-200 py-7 text-sm text-slate-500">No Hackathon work has been published yet.</p> : (
        <dl className="mt-8 grid grid-cols-2 gap-x-8 gap-y-5 border-y border-slate-200 py-5 sm:grid-cols-4">
          {counts.map(([label, count]) => <div key={label}><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 text-2xl font-bold text-[#102c46]">{count}</dd></div>)}
        </dl>
      )}

      {projects.count > 0 ? <div className="mt-10"><h3 className="text-lg font-semibold text-[#102c46]">Featured projects</h3><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{projects.results.map((project) => <ProjectRow key={project.id} project={project} username={username} />)}</div><PagesControl page={pages.projects} data={projects} disabled={loading} onPage={(page) => onPage("projects", page)} /></div> : null}

      {participations.count > 0 ? <div className="mt-10"><h3 className="text-lg font-semibold text-[#102c46]">Public participation</h3><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{participations.results.map((participation) => <article key={participation.id} className="flex flex-wrap items-start justify-between gap-4 py-5"><div><h4 className="font-semibold text-[#102c46]">{participation.event.name}</h4><p className="mt-1 text-xs text-slate-500">{[participation.event.organizer, participation.event.start_date, participation.event.end_date && participation.event.end_date !== participation.event.start_date ? `to ${participation.event.end_date}` : null].filter(Boolean).join(" · ")}</p><p className="mt-2 text-sm capitalize text-slate-600">{participation.event.format.replaceAll("_", " ")} · {participation.status}{participation.team_name ? ` · ${participation.team_name}` : ""}{participation.role ? ` · ${participation.role}` : ""}</p></div><ExternalLinkItem href={participation.event.event_url}>Event website</ExternalLinkItem></article>)}</div><PagesControl page={pages.participations} data={participations} disabled={loading} onPage={(page) => onPage("participations", page)} /></div> : null}

      {achievements.count > 0 ? <div className="mt-10"><h3 className="text-lg font-semibold text-[#102c46]">Achievements</h3><div className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{achievements.results.map((achievement) => <article key={achievement.id} className="flex flex-wrap items-start justify-between gap-3 py-5"><div><h4 className="font-semibold text-[#102c46]">{achievement.title}</h4><p className="mt-1 text-xs capitalize text-slate-500">{achievement.achievement_type.replaceAll("_", " ")}{achievement.rank != null ? ` · Rank ${achievement.rank}` : ""}{achievement.total_participants != null ? ` of ${achievement.total_participants}` : ""}</p>{achievement.description ? <p className="mt-2 text-sm text-slate-600">{achievement.description}</p> : null}</div><span className={`text-xs font-semibold ${achievement.verification_status === "verified" ? "text-emerald-700" : "text-slate-500"}`}>{verificationLabel[achievement.verification_status]}</span></article>)}</div><PagesControl page={pages.achievements} data={achievements} disabled={loading} onPage={(page) => onPage("achievements", page)} /></div> : null}

      {submissions.count > 0 ? <div className="mt-10"><h3 className="text-lg font-semibold text-[#102c46]">Submitted work</h3><ul className="mt-4 divide-y divide-slate-200 border-y border-slate-200">{submissions.results.map((submission) => <li key={submission.id} className="flex flex-wrap items-center justify-between gap-3 py-4 text-sm"><span className="text-slate-700">{submission.project_title} · {submission.event_name}</span><ExternalLinkItem href={submission.submission_url}>View submission</ExternalLinkItem></li>)}</ul><PagesControl page={pages.submissions} data={submissions} disabled={loading} onPage={(page) => onPage("submissions", page)} /></div> : null}
    </section>
  );
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

  if (!portfolio && loading) return <section aria-label="Hackathon portfolio" role="status" className="border-t border-slate-200 py-12 text-sm text-slate-500">Loading hackathon portfolio…</section>;
  if (!portfolio) return <section aria-label="Hackathon portfolio" className="border-t border-slate-200 py-12"><p role="alert" className="text-sm text-rose-700">{error}</p><button type="button" onClick={retry} className="mt-3 text-sm font-semibold text-[#1769b0] underline">Retry portfolio</button></section>;
  return <div>{error ? <div role="alert" className="border-t border-rose-200 py-4 text-sm text-rose-700">{error} <button type="button" onClick={retry} className="font-semibold underline">Retry</button></div> : null}<PublicHackathonPortfolioContent portfolio={portfolio} pages={pages} username={username} onPage={onPage} loading={loading} /></div>;
}
