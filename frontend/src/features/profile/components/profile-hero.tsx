"use client";

/* eslint-disable @next/next/no-img-element */
import Link from "next/link";
import { BriefcaseBusiness, Building2, Check, CodeXml, MapPin, Share2 } from "lucide-react";
import { toast } from "sonner";
import { metricAccentStyles } from "@/features/dashboard/styles";
import { useAuth } from "@/hooks/use-auth";
import type { ProfileHeroView, ProfileMetricView } from "../view-model";

async function shareProfile() {
  try {
    if (navigator.share) { await navigator.share({ title: document.title, url: window.location.href }); return; }
    await navigator.clipboard.writeText(window.location.href); toast.success("Profile link copied");
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return;
    try { await navigator.clipboard.writeText(window.location.href); toast.success("Profile link copied"); } catch { toast.error("Could not share this profile"); }
  }
}

export function ProfileHero({ hero, metrics }: { hero: ProfileHeroView; metrics: ProfileMetricView[] }) {
  const { user } = useAuth();
  const isOwner = user?.username.toLowerCase() === hero.username.toLowerCase();
  return (
    <section className="relative overflow-hidden border-b border-slate-100 bg-[radial-gradient(circle_at_86%_70%,rgba(167,243,208,0.22),transparent_24%),linear-gradient(135deg,#fff_0%,#fbfdff_62%,#f5fffb_100%)]">
      <div aria-hidden="true" className="absolute inset-0 opacity-30 [background-image:repeating-radial-gradient(ellipse_at_62%_40%,transparent_0,transparent_12px,rgba(148,163,184,.13)_13px,transparent_14px)]" />
      <div className="relative mx-auto grid max-w-310 gap-8 px-5 py-10 sm:px-8 lg:grid-cols-[minmax(0,1fr)_535px] lg:items-center lg:py-11">
        <div className="flex min-w-0 flex-col items-center gap-6 text-center sm:flex-row sm:text-left">
          <div className="grid size-39 shrink-0 place-items-center overflow-hidden rounded-full bg-emerald-50 text-4xl font-bold text-emerald-700 ring-4 ring-white shadow-sm sm:size-48 lg:size-46">{hero.avatarUrl ? <img src={hero.avatarUrl} alt={`${hero.displayName}'s avatar`} className="h-full w-full object-cover" /> : <span aria-label={`${hero.displayName} initials`}>{hero.initials}</span>}</div>
          <div className="min-w-0">
            <div className="flex items-center justify-center gap-2 sm:justify-start"><h1 className="truncate text-[26px] font-bold tracking-tight text-slate-950">{hero.displayName}</h1><span title="Public profile" className="grid size-6 shrink-0 place-items-center rounded-full bg-emerald-600 text-white"><Check className="size-4 stroke-3" /></span></div>
            <p className="mt-1 text-sm font-medium text-slate-600">@{hero.username}</p>
            {hero.bio ? <p className="mt-4 max-w-105 text-[13px] leading-6 text-slate-700">{hero.bio}</p> : null}
            <div className="mt-4 flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs text-slate-600 sm:justify-start">{hero.country ? <span className="inline-flex items-center gap-2"><MapPin className="size-4" />{hero.country}</span> : null}{hero.institution ? <span className="inline-flex items-center gap-2"><Building2 className="size-4" />{hero.institution}</span> : null}</div>
            {hero.socialLinks.length ? <div className="mt-4 flex flex-wrap justify-center gap-x-6 gap-y-2 sm:justify-start">{hero.socialLinks.map((link) => { const Icon = link.kind === "github" ? CodeXml : BriefcaseBusiness; return <a key={link.kind} href={link.href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-xs text-slate-600 hover:text-emerald-700"><Icon className="size-4" />{link.label}</a>; })}</div> : null}
          </div>
        </div>
        <div className="min-w-0">
          <div className="mb-9 flex flex-wrap justify-center gap-3 lg:justify-end"><button type="button" onClick={() => void shareProfile()} className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-5 text-xs font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"><Share2 className="size-4" />Share Profile</button>{isOwner ? <Link href="/dashboard" className="inline-flex h-10 items-center gap-2 rounded-lg bg-emerald-600 px-5 text-xs font-semibold text-white shadow-[0_8px_20px_rgba(5,150,105,.2)] transition hover:bg-emerald-700"><Share2 className="size-4" />View Dashboard</Link> : null}</div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{metrics.map((metric) => { const Icon = metric.icon; const style = metricAccentStyles[metric.accent]; return <div key={metric.label} className="flex min-h-39 flex-col items-center justify-center rounded-xl border border-slate-200/80 bg-white/90 px-3 py-4 text-center shadow-[0_8px_28px_rgba(15,23,42,.04)]"><span className={`grid size-9 place-items-center rounded-xl ${style.iconBg} ${style.icon}`}><Icon className="size-5" /></span><strong className="mt-3 text-xl font-bold text-slate-950">{metric.value}</strong><span className="mt-2 text-[11px] font-medium leading-5 text-slate-600">{metric.label}</span></div>; })}</div>
        </div>
      </div>
    </section>
  );
}
