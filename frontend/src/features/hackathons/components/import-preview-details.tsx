import type { DevpostPreview, ImportFieldChange } from "../types";

function valueText(value: ImportFieldChange["before"]): string {
  if (value == null || value === "") return "(empty)";
  return Array.isArray(value) ? value.join(", ") : value;
}

function Changes({ rows }: { rows: ImportFieldChange[] }) {
  if (!rows.length) return null;
  return <ul className="mt-2 space-y-1 text-xs text-slate-600">{rows.map((row) => <li key={row.field} className="wrap-break-word">
    <strong className="capitalize">{row.field.replaceAll("_", " ")}:</strong> {valueText(row.before)} → {valueText(row.after)}{row.truncated ? " (preview shortened)" : ""}
  </li>)}</ul>;
}

export function ImportPreviewDetails({ preview }: { preview: DevpostPreview }) {
  const counts = preview.action_counts;
  return <div>
    <p className="mt-1 text-sm">{preview.projects_detected} projects · {preview.hackathons_detected} hackathons · {preview.submissions_detected} submissions</p>
    <p className="mt-1 text-xs text-slate-700">{counts.create} new · {counts.update} updated · {counts.unchanged} unchanged · {counts.protected} protected · {counts.conflict} conflicts</p>
    {preview.potential_manual_duplicates > 0 && <p className="mt-2 text-xs text-amber-800">{preview.potential_manual_duplicates} possible manual matches are suggestions. Import keeps records separate.</p>}
    {preview.conflicts.length > 0 && <div role="alert" className="mt-2 text-xs text-rose-700"><p>{preview.conflicts.length} conflicts block import. Review the source identities and preview again after resolving them.</p>
      {preview.conflicts.slice(0, 5).map((row, index) => <p key={`${index}-${row.project_url}-${row.event_url}`} className="break-all">{row.project_url || row.event_url}</p>)}</div>}
    <div className="mt-3 max-h-80 space-y-2 overflow-y-auto">{preview.projects.map((project) => <details key={project.project_url} className="rounded-lg border border-violet-100 bg-white p-3 text-sm" open={preview.projects.length === 1}>
      <summary className="cursor-pointer font-semibold">{project.title} · {project.action}</summary>
      <p className="mt-1 break-all text-xs text-slate-500">{project.project_url}</p>
      {project.reason && <p className="mt-1 text-xs text-amber-800">{project.reason}</p>}
      <Changes rows={project.changes} />
      {project.possible_manual_projects?.map((manual) => <div key={manual.id} className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-900">
        Possible manual project: {manual.title} (#{manual.id}) · {manual.reason}
      </div>)}
      {project.submissions.map((submission) => <div key={submission.event_url} className="mt-2 border-t border-slate-100 pt-2 text-xs text-slate-600">
        <p className="font-medium">{submission.event_name}: event {submission.event_action}, participation {submission.participation_action}, submission {submission.action}</p>
        {submission.event_reason && <p className="text-amber-800">{submission.event_reason}</p>}
        {submission.reason && <p className="text-amber-800">{submission.reason}</p>}
        <Changes rows={submission.event_changes ?? []} /><Changes rows={submission.changes ?? []} />
        {submission.possible_manual_events?.map((manual) => <p key={manual.id} className="mt-1 text-amber-800">Possible manual event: {manual.name} (#{manual.id}) · {manual.reason}</p>)}
      </div>)}
    </details>)}</div>
  </div>;
}
