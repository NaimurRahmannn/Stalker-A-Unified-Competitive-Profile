import type { PerformanceSummaryView } from "../view-model";

const skills = ["Problem Solving", "Consistency", "Contest Performance", "Algorithms", "Data Structures"];
const points = [[110, 22], [194, 83], [162, 178], [58, 178], [26, 83]];

export function PerformanceSummary({ performance }: { performance: PerformanceSummaryView }) {
  return (
    <aside aria-labelledby="performance-heading" className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_10px_32px_rgba(15,23,42,.03)]">
      <h2 id="performance-heading" className="text-[15px] font-semibold text-slate-950">Performance Summary</h2>
      <div className="mx-auto mt-5 max-w-65">
        <svg viewBox="0 0 220 210" role="img" aria-label="Skill data is not yet available" className="h-auto w-full overflow-visible">
          {[1, .75, .5, .25].map((scale) => <polygon key={scale} points={points.map(([x, y]) => `${110 + (x - 110) * scale},${110 + (y - 110) * scale}`).join(" ")} fill="none" stroke="#dbe5e1" strokeWidth="1" />)}
          {points.map(([x, y], index) => <line key={skills[index]} x1="110" y1="110" x2={x} y2={y} stroke="#e2e8f0" />)}
          <polygon points="110,72 146,98 132,143 83,143 69,98" fill="rgba(16,185,129,.08)" stroke="#94a3b8" strokeDasharray="4 4" strokeWidth="1.5" />
          <text x="110" y="10" textAnchor="middle" className="fill-slate-500 text-[7px]">Problem Solving</text>
          <text x="211" y="82" textAnchor="end" className="fill-slate-500 text-[7px]">Consistency</text>
          <text x="202" y="197" textAnchor="end" className="fill-slate-500 text-[7px]">Contest Performance</text>
          <text x="28" y="197" textAnchor="start" className="fill-slate-500 text-[7px]">Algorithms</text>
          <text x="3" y="82" className="fill-slate-500 text-[7px]">Data Structures</text>
          <text x="110" y="113" textAnchor="middle" className="fill-slate-400 text-[9px] font-semibold">Unavailable</text>
        </svg>
      </div>
      <div className="mt-2 space-y-3 border-t border-slate-100 pt-4">{skills.map((skill) => <div key={skill} className="flex items-center justify-between text-[11px]"><span className="text-slate-600">{skill}</span><span className="font-semibold text-slate-500">—/100</span></div>)}</div>
      <dl className="mt-5 space-y-3 border-t border-slate-100 pt-4 text-[11px]"><div className="flex justify-between gap-4"><dt className="text-slate-500">Last Active</dt><dd className="font-semibold text-slate-800">{performance.lastActive}</dd></div><div className="flex justify-between gap-4"><dt className="text-slate-500">Member Since</dt><dd className="font-semibold text-slate-800">{performance.memberSince}</dd></div></dl>
    </aside>
  );
}
