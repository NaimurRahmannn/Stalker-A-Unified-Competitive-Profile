import { Activity, ArrowRight, Award } from "lucide-react";

const sections = [
  { title: "Recent Achievements", message: "No public achievements yet", description: "Achievements will appear here when they become available.", Icon: Award, color: "text-violet-600 bg-violet-50", action: "View All Achievements" },
  { title: "Recent Activity", message: "No recent public activity yet", description: "Public platform activity will appear here when supported.", Icon: Activity, color: "text-blue-600 bg-blue-50", action: "View All Activity" },
];

export function ProfileRecentSections() {
  return <section aria-label="Recent profile updates" className="grid gap-4 lg:grid-cols-2">{sections.map(({ title, message, description, Icon, color, action }) => (
    <article key={title} className="flex min-h-59 flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-[0_10px_32px_rgba(15,23,42,.03)]">
      <div className="flex items-center gap-3"><Icon className="size-5 text-violet-600" /><h2 className="text-xs font-semibold text-slate-950">{title}</h2></div>
      <div className="my-4 flex flex-1 items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-5 py-7 text-center"><div><span className={`mx-auto grid size-10 place-items-center rounded-xl ${color}`}><Icon className="size-5" /></span><p className="mt-3 text-xs font-semibold text-slate-700">{message}</p><p className="mt-1 text-[10px] text-slate-500">{description}</p></div></div>
      <button type="button" disabled className="inline-flex h-8 cursor-not-allowed items-center justify-center gap-2 rounded-lg border border-emerald-200 text-[9px] font-semibold text-emerald-600 opacity-60">{action}<ArrowRight className="size-3" /></button>
    </article>
  ))}</section>;
}
