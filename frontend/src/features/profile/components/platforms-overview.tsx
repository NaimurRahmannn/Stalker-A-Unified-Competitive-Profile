import { ArrowUpRight } from "lucide-react";
import type { PublicPlatformView } from "../view-model";
import { ProfilePlatformLogo } from "./profile-platform-logo";

function PlatformRow({ platform }: { platform: PublicPlatformView }) {
  const content = (
    <>
      <div className="flex min-w-0 items-center gap-4">
        <ProfilePlatformLogo mark={platform.mark} slug={platform.slug} name={platform.name} size="lg" />
        <div className="min-w-0">
          <h3 className="flex items-center gap-2 truncate text-sm font-semibold text-[#102c46] sm:text-base">
            {platform.name}
            {platform.profileUrl ? <ArrowUpRight aria-hidden="true" className="size-4 shrink-0 text-slate-400" /> : null}
          </h3>
          <p className="mt-0.5 truncate text-xs text-slate-500">{platform.handle}</p>
        </div>
      </div>
      <dl className="grid grid-cols-3 gap-3 lg:col-span-3 lg:gap-7">
        <div className="min-w-0"><dt className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{platform.ratingLabel ?? "Rating"}</dt><dd className="mt-1 truncate text-sm font-semibold text-[#102c46]">{platform.rating}</dd></div>
        <div className="min-w-0"><dt className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Activity</dt><dd className="mt-1 truncate text-sm font-semibold text-[#102c46]">{platform.solved}</dd></div>
        <div className="min-w-0"><dt className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Connection</dt><dd className={`mt-1 flex items-center gap-1.5 text-xs font-medium ${platform.handleValid ? "text-emerald-700" : "text-slate-500"}`}><span className={`size-1.5 shrink-0 rounded-full ${platform.handleValid ? "bg-emerald-500" : "bg-slate-400"}`} />{platform.handleValid ? "Validated" : "Not validated"}</dd></div>
      </dl>
    </>
  );
  const className = "grid gap-4 border-b border-slate-200 py-5 transition-colors last:border-b-0 lg:grid-cols-4 lg:items-center lg:gap-8";
  return platform.profileUrl ? (
    <a href={platform.profileUrl} target="_blank" rel="noreferrer" className={`${className} hover:bg-sky-50/50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1769b0]`}>{content}</a>
  ) : (
    <article className={className}>{content}</article>
  );
}

export function PlatformsOverview({ platforms }: { platforms: PublicPlatformView[] }) {
  return (
    <section aria-labelledby="platforms-heading" className="py-12 sm:py-14">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.17em] text-[#1769b0]">01 / Connections</p>
          <h2 id="platforms-heading" className="mt-2 text-2xl font-bold tracking-tight text-[#102c46] sm:text-[28px]">Connected platforms</h2>
          <p className="mt-2 text-sm text-slate-500">Accounts and activity linked to this profile.</p>
        </div>
        <span className="text-sm font-medium text-slate-500">{platforms.length} {platforms.length === 1 ? "platform" : "platforms"}</span>
      </div>
      <div className="mt-7 border-t border-slate-300">
        {platforms.length ? platforms.map((platform) => <PlatformRow key={platform.id} platform={platform} />) : <p className="py-8 text-sm text-slate-500">No platforms connected yet.</p>}
      </div>
    </section>
  );
}
