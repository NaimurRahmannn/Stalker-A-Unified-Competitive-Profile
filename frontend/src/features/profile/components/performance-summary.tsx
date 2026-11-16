import type { PerformanceSummaryView } from "../view-model";

export function PerformanceSummary({ performance }: { performance: PerformanceSummaryView }) {
  return (
    <dl className="flex flex-wrap gap-x-8 gap-y-3 text-xs">
      <div><dt className="text-slate-500">Last active</dt><dd className="mt-1 font-semibold text-[#102c46]">{performance.lastActive}</dd></div>
      <div><dt className="text-slate-500">Member since</dt><dd className="mt-1 font-semibold text-[#102c46]">{performance.memberSince}</dd></div>
    </dl>
  );
}
