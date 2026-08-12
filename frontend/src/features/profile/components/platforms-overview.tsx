import { ExternalLink, Plus } from "lucide-react";
import type { PublicPlatformView } from "../view-model";
import { ProfilePlatformLogo } from "./profile-platform-logo";

function PlatformCard({ platform }: { platform: PublicPlatformView }) {
  const content = (
    <>
      <div className="flex items-start gap-3">
        <ProfilePlatformLogo mark={platform.mark} slug={platform.slug} name={platform.name} size="lg" />
        <div className="min-w-0 flex-1"><h3 className="truncate text-xs font-semibold text-slate-950">{platform.name}</h3><p className="mt-1 truncate text-[10px] text-slate-500">{platform.handle}</p></div>
        {platform.profileUrl ? <ExternalLink className="size-3.5 shrink-0 text-slate-400" /> : null}
      </div>
      <div className="mt-8 flex items-end gap-3"><strong className={`text-xl font-bold ${platform.hasDetailedStats ? "text-emerald-600" : "text-slate-400"}`}>{platform.rating}</strong><div className="pb-0.5"><p className="text-[10px] font-semibold text-slate-800">Rating</p><p className="mt-0.5 max-w-20 truncate text-[9px] capitalize text-slate-500">{platform.rank}</p></div></div>
      <div className="mt-auto flex items-center justify-between pt-6"><strong className="text-lg font-semibold text-slate-900">{platform.solved}</strong>{platform.isVerified ? <span className="rounded bg-emerald-50 px-2 py-1 text-[9px] font-semibold text-emerald-700">Verified</span> : <span className="rounded bg-slate-100 px-2 py-1 text-[9px] font-semibold text-slate-500">Unverified</span>}</div>
    </>
  );
  const className = "flex min-h-49 flex-col rounded-xl border border-slate-200 bg-white p-4 text-left transition hover:border-emerald-200 hover:shadow-sm";
  return platform.profileUrl ? <a href={platform.profileUrl} target="_blank" rel="noreferrer" className={className}>{content}</a> : <article className={className}>{content}</article>;
}

export function PlatformsOverview({ platforms }: { platforms: PublicPlatformView[] }) {
  return (
    <section aria-labelledby="platforms-heading" className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_10px_32px_rgba(15,23,42,.03)]">
      <h2 id="platforms-heading" className="text-[15px] font-semibold text-slate-950">Platforms Overview</h2>
      <div className="mt-5 grid grid-cols-1 gap-3 min-[460px]:grid-cols-2 md:grid-cols-3 xl:grid-cols-6">
        {platforms.map((platform) => <PlatformCard key={platform.id} platform={platform} />)}
        <div className="flex min-h-49 flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50/40 p-4 text-center"><Plus className="size-6 text-slate-500" /><p className="mt-4 text-xs font-medium text-slate-700">More Platforms</p><p className="mt-1 text-[10px] text-slate-500">Coming Soon</p></div>
      </div>
    </section>
  );
}
