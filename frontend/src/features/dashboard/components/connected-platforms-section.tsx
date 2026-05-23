import Image from "next/image";
import { connectedPlatforms, platformLogoSrc } from "../data";
import type { ConnectedPlatform } from "../types";
import { SectionCard } from "./section-card";

function PlatformMark({ mark }: { mark: ConnectedPlatform["mark"] }) {
  const logoSize =
    mark === "codeforces" || mark === "github" ? "size-8" : "size-9";

  return (
    <span className="grid size-11 place-items-center rounded-2xl bg-slate-50">
      <Image
        src={platformLogoSrc[mark]}
        alt=""
        width={40}
        height={40}
        className={`${logoSize} object-contain`}
      />
    </span>
  );
}

function PlatformMiniCard({ platform }: { platform: ConnectedPlatform }) {
  const badgeClass =
    platform.status === "Verified"
      ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
      : "bg-orange-50 text-orange-700 ring-1 ring-orange-200";

  return (
    <article className="flex min-h-34 flex-col items-center justify-between rounded-2xl border border-slate-200 bg-white p-3 text-center shadow-[0_10px_26px_rgba(15,23,42,0.035)] transition hover:-translate-y-0.5 hover:shadow-[0_14px_32px_rgba(15,23,42,0.07)]">
      <PlatformMark mark={platform.mark} />
      <div className="min-w-0">
        <p className="truncate text-xs font-semibold text-slate-950">
          {platform.name}
        </p>
        <p className="mt-1 truncate text-[10px] font-medium text-slate-500">
          {platform.handle}
        </p>
      </div>
      <span
        className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${badgeClass}`}
      >
        {platform.status}
      </span>
    </article>
  );
}

function AddPlatformCard() {
  return (
    <button
      type="button"
      className="flex min-h-34 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-blue-200 bg-blue-50/40 p-3 text-center text-blue-700 transition hover:bg-blue-50"
    >
      <span className="grid size-10 place-items-center rounded-xl border border-blue-200 bg-white">
        <span className="text-2xl font-light leading-none">+</span>
      </span>
      <span className="text-xs font-semibold">Add Platform</span>
    </button>
  );
}

export function ConnectedPlatformsSection() {
  return (
    <SectionCard title="Connected Platforms">
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
        {connectedPlatforms.map((platform) => (
          <PlatformMiniCard key={platform.name} platform={platform} />
        ))}
        <AddPlatformCard />
      </div>
    </SectionCard>
  );
}
