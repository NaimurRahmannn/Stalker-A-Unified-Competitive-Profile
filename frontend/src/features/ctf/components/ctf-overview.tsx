import Image from "next/image";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { PlatformAccount } from "@/features/platforms/types";

export function CTFOverview({ account, onView }: { account: PlatformAccount | null; onView: () => void }) {
  const profile = account?.ctf_team_profile;
  const latest = profile ? [...profile.yearly_rankings].sort((a, b) => b.year - a.year)[0] : null;

  return (
    <>
      {!account ? (
        <div className="mb-6 rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center">
          <h2 className="text-lg font-semibold text-slate-950">Build your CTF profile</h2>
          <p className="mx-auto mt-2 max-w-lg text-sm text-slate-500">
            Connect a CTFtime team to bring its public rankings into your profile.
          </p>
          <Link href="/platforms" className="mt-5 inline-flex h-10 items-center rounded-xl bg-emerald-600 px-5 text-xs font-semibold text-white hover:bg-emerald-700">
            Connect a team
          </Link>
        </div>
      ) : null}

      <section>
        <h2 className="text-sm font-semibold text-slate-950">Platform Performance</h2>
        <div className="mt-3 grid gap-4 md:grid-cols-2">
          {!account ? (
            <article className="flex min-h-54 flex-col rounded-2xl border border-dashed border-slate-300 bg-white p-5">
              <div className="flex items-center gap-3">
                <span className="grid size-11 place-items-center rounded-2xl bg-slate-50">
                  <Image src="/images/ctf_time.png" alt="CTFtime logo" width={32} height={32} className="size-8 object-contain" />
                </span>
                <h3 className="font-semibold text-slate-950">CTFtime</h3>
              </div>
              <p className="mt-5 text-sm font-medium text-slate-700">Not connected</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">Add your team ID to track yearly rankings.</p>
              <Link href="/platforms" className="mt-auto inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-emerald-200 text-xs font-semibold text-emerald-700 hover:bg-emerald-50">
                Connect CTFtime <ArrowRight className="size-3.5" />
              </Link>
            </article>
          ) : (
            <article className="flex min-h-54 flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_30px_rgba(15,23,42,0.035)]">
              <div className="flex items-center gap-3">
                <span className="grid size-11 place-items-center rounded-2xl bg-slate-50">
                  <Image src="/images/ctf_time.png" alt="CTFtime logo" width={32} height={32} className="size-8 object-contain" />
                </span>
                <div className="min-w-0">
                  <h3 className="font-semibold text-slate-950">CTFtime</h3>
                  <p className="truncate text-[10px] text-slate-500">Team #{account.handle}</p>
                </div>
              </div>
              <div className="mt-5">
                <p className="truncate text-2xl font-semibold text-slate-950">
                  {latest ? latest.rating_points.toFixed(2) : profile ? "Unranked" : "Not synced"}
                  {latest?.global_rank != null ? <span className="text-sm font-medium text-slate-500"> · #{latest.global_rank} global</span> : null}
                </p>
                <p className="mt-2 truncate text-xs font-medium text-slate-600">{profile?.name ?? "Sync to load team details"}</p>
                <p className="mt-1 text-xs text-slate-500">{profile ? `${profile.yearly_rankings.length} ranked ${profile.yearly_rankings.length === 1 ? "year" : "years"}` : "Yearly rankings unavailable until first sync"}</p>
              </div>
              <button type="button" onClick={onView} className="mt-auto inline-flex h-9 items-center justify-center gap-2 rounded-xl border border-emerald-200 text-xs font-semibold text-emerald-700 hover:bg-emerald-50">
                View analytics <ArrowRight className="size-3.5" />
              </button>
            </article>
          )}
        </div>
      </section>
    </>
  );
}
