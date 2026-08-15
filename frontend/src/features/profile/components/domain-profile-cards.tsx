import { BarChart3, ExternalLink, ShieldCheck, Trophy } from "lucide-react";
import type { DomainCardView } from "../view-model";
import { ProfilePlatformLogo } from "./profile-platform-logo";

const domainStyle = {
  ctf: { Icon: ShieldCheck, icon: "bg-blue-50 text-blue-600", border: "border-blue-200 text-blue-600" },
  hackathon: { Icon: Trophy, icon: "bg-violet-50 text-violet-600", border: "border-violet-200 text-violet-600" },
  datathon: { Icon: BarChart3, icon: "bg-orange-50 text-orange-600", border: "border-orange-200 text-orange-600" },
};

export function DomainProfileCards({ cards }: { cards: DomainCardView[] }) {
  return <section aria-label="Specialized profiles" className="grid gap-4 lg:grid-cols-3">{cards.map((card) => { const style = domainStyle[card.key]; const Icon = style.Icon; return (
    <article key={card.key} className="flex min-h-57 flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-[0_10px_32px_rgba(15,23,42,.03)]">
      <div className="flex items-center gap-3"><span className={`grid size-8 place-items-center rounded-lg ${style.icon}`}><Icon className="size-4" /></span><div><h2 className="text-xs font-semibold text-slate-950">{card.title}</h2><p className="sr-only">{card.subtitle}</p></div></div>
      <div className="mt-4 space-y-3">{card.accounts.length ? card.accounts.map((account) => <div key={account.id} className="flex items-center gap-3 border-b border-slate-100 pb-3 last:border-0"><ProfilePlatformLogo mark={account.mark} name={account.name} size="sm" /><div className="min-w-0 flex-1"><p className="truncate text-[11px] font-semibold text-slate-900">{account.name}</p><p className="mt-0.5 truncate text-[9px] text-slate-500">{account.handle}</p></div>{account.handleValid ? <span className="rounded bg-emerald-50 px-2 py-1 text-[8px] font-semibold text-emerald-700">Handle valid</span> : <span className="text-[8px] text-slate-400">Not validated</span>}</div>) : <div className="rounded-lg bg-slate-50 px-4 py-5 text-center"><p className="text-[11px] font-medium text-slate-600">No connected accounts yet</p><p className="mt-1 text-[9px] text-slate-400">Public statistics are unavailable</p></div>}</div>
      <div className="mt-auto grid grid-cols-3 gap-2 pt-4 text-center">{["Rating", "Events", "Awards"].map((label) => <div key={label}><strong className="block text-sm text-slate-400">—</strong><span className="text-[8px] text-slate-400">{label}</span></div>)}</div>
      {card.accounts[0]?.profileUrl ? <a href={card.accounts[0].profileUrl} target="_blank" rel="noreferrer" className={`mt-4 inline-flex h-8 items-center justify-center gap-2 rounded-lg border text-[9px] font-semibold ${style.border}`}>View {card.accounts[0].name} Profile <ExternalLink className="size-3" /></a> : <button type="button" disabled className={`mt-4 h-8 cursor-not-allowed rounded-lg border text-[9px] font-semibold opacity-60 ${style.border}`}>Profile unavailable</button>}
    </article>
  ); })}</section>;
}
