import { ArrowUpRight, BarChart3, ShieldCheck, Trophy } from "lucide-react";
import type { DomainCardView } from "../view-model";
import { ProfilePlatformLogo } from "./profile-platform-logo";

const domainStyle = {
  ctf: { Icon: ShieldCheck, color: "text-blue-600" },
  hackathon: { Icon: Trophy, color: "text-violet-600" },
  datathon: { Icon: BarChart3, color: "text-cyan-700" },
};

export function DomainProfileCards({ cards }: { cards: DomainCardView[] }) {
  return (
    <section aria-labelledby="domains-heading" className="border-t border-slate-200 py-12 sm:py-14">
      <p className="text-[11px] font-bold uppercase tracking-[0.17em] text-[#1769b0]">03 / Specializations</p>
      <h2 id="domains-heading" className="mt-2 text-2xl font-bold tracking-tight text-[#102c46] sm:text-[28px]">Beyond the leaderboard</h2>
      <p className="mt-2 text-sm text-slate-500">A wider view of this person&apos;s technical work.</p>
      <div className="mt-9 grid gap-8 lg:grid-cols-3 lg:gap-0">
        {cards.map((card) => {
          const style = domainStyle[card.key];
          const Icon = style.Icon;
          const metrics = card.metrics ?? (card.key === "ctf" && card.accounts[0]
            ? [{ label: "Rating", value: card.accounts[0].rating }, { label: "Global rank", value: card.accounts[0].rank }, { label: "Years", value: card.accounts[0].contests }]
            : [{ label: "Rating", value: "—" }, { label: "Events", value: "—" }, { label: "Awards", value: "—" }]);
          return (
            <article key={card.key} className="border-t border-slate-200 pt-6 lg:border-l lg:border-t-0 lg:px-8 lg:pt-0 lg:first:border-l-0 lg:first:pl-0 lg:last:pr-0">
              <div className="flex items-center gap-3"><Icon aria-hidden="true" className={`size-5 ${style.color}`} /><h3 className="text-lg font-semibold text-[#102c46]">{card.title}</h3></div>
              <p className="mt-2 min-h-10 text-xs leading-5 text-slate-500">{card.subtitle}</p>
              <div className="mt-4 min-h-20 space-y-3">
                {card.accounts.length ? card.accounts.map((account) => <div key={account.id} className="flex items-center gap-3"><ProfilePlatformLogo mark={account.mark} name={account.name} size="sm" /><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-800">{account.name}</p><p className="truncate text-xs text-slate-500">{account.handle}</p></div></div>) : <p className="text-sm text-slate-400">No public account connected</p>}
              </div>
              <dl className="mt-5 grid grid-cols-3 gap-3 border-t border-slate-200 pt-4">
                {metrics.map(({ label, value }) => <div key={label} className="min-w-0"><dt className="text-[11px] text-slate-500">{label}</dt><dd className="mt-1 truncate text-sm font-semibold text-[#102c46]">{value}</dd></div>)}
              </dl>
              {card.accounts[0]?.profileUrl ? <a href={card.accounts[0].profileUrl} target="_blank" rel="noreferrer" className="mt-5 inline-flex items-center gap-1 text-xs font-semibold text-[#1769b0] hover:underline">View {card.accounts[0].name} Profile<ArrowUpRight aria-hidden="true" className="size-4" /></a> : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
