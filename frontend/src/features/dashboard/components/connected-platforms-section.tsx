import Image from "next/image";
import Link from "next/link";
import { Link2 } from "lucide-react";
import { platformLogoSrc } from "../data";
import type { ConnectedPlatform } from "../types";
import { SectionCard } from "./section-card";

function PlatformMark({ mark }: { mark: ConnectedPlatform["mark"] }) {
  if (!mark) {
    return (
      <span className="grid size-11 place-items-center rounded-2xl bg-slate-50 text-slate-500">
        <Link2 className="size-5" />
      </span>
    );
  }

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
        {platform.profileUrl ? (
          <a
            href={platform.profileUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-1 block truncate text-[10px] font-medium text-blue-700 transition hover:text-blue-800"
          >
            {platform.handle}
          </a>
        ) : (
          <p className="mt-1 truncate text-[10px] font-medium text-slate-500">
            {platform.handle}
          </p>
        )}
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
    <Link
      href="/platforms"
      className="flex min-h-34 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-blue-200 bg-blue-50/40 p-3 text-center text-blue-700 transition hover:bg-blue-50"
    >
      <span className="grid size-10 place-items-center rounded-xl border border-blue-200 bg-white">
        <span className="text-2xl font-light leading-none">+</span>
      </span>
      <span className="text-xs font-semibold">Add Platform</span>
    </Link>
  );
}

function EmptyPlatformsState() {
  return (
    <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 px-4 py-8 text-center">
      <span className="mx-auto grid size-11 place-items-center rounded-2xl bg-white text-slate-400">
        <Link2 className="size-5" />
      </span>
      <p className="mt-3 text-sm font-semibold text-slate-950">
        No platforms connected yet
      </p>
      <p className="mt-1 text-xs font-medium text-slate-500">
        Connect Codeforces to start pulling real dashboard stats.
      </p>
    </div>
  );
}

export function ConnectedPlatformsSection({
  platforms,
}: {
  platforms: ConnectedPlatform[];
}) {
  return (
    <SectionCard
      title="Connected Platforms"
      actionHref="/platforms"
      actionLabel="Manage"
    >
      {platforms.length === 0 ? <EmptyPlatformsState /> : null}
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
        {platforms.map((platform) => (
          <PlatformMiniCard key={platform.id} platform={platform} />
        ))}
        <AddPlatformCard />
      </div>
    </SectionCard>
  );
}
