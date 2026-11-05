"use client";

import type { EventFilters, ProjectFilters } from "../types";

export const initialProjectFilters: ProjectFilters = { search: "", source: "", visibility: "", technology: "", ordering: "newest" };
export const initialEventFilters: EventFilters = { name: "", status: "", year: "", event_format: "", source: "", ordering: "newest" };

const inputClass = "min-w-0 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-200";

function SelectField({ label, value, options, onChange }: { label: string; value: string; options: Array<[string, string]>; onChange: (value: string) => void }) {
  return <label className="flex min-w-0 flex-col gap-1 text-xs font-semibold text-slate-600">{label}
    <select aria-label={label} className={inputClass} value={value} onChange={(event) => onChange(event.target.value)}>
      {options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}
    </select>
  </label>;
}

export function ProjectDiscoveryFilters({ filters, onChange, onReset }: {
  filters: ProjectFilters; onChange: (value: ProjectFilters) => void; onReset: () => void;
}) {
  const change = (key: keyof ProjectFilters, value: string) => onChange({ ...filters, [key]: value });
  return <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3" aria-label="Project filters">
    <label className="flex min-w-0 flex-col gap-1 text-xs font-semibold text-slate-600">Search projects
      <input className={inputClass} value={filters.search} onChange={(event) => change("search", event.target.value)} maxLength={100} placeholder="Title or description" />
    </label>
    <SelectField label="Project source" value={filters.source} options={[["", "All sources"], ["manual", "Manual"], ["devpost", "Devpost"]]} onChange={(value) => change("source", value)} />
    <SelectField label="Project visibility" value={filters.visibility} options={[["", "All visibility"], ["public", "Published"], ["private", "Private"]]} onChange={(value) => change("visibility", value)} />
    <label className="flex min-w-0 flex-col gap-1 text-xs font-semibold text-slate-600">Technology
      <input className={inputClass} value={filters.technology} onChange={(event) => change("technology", event.target.value)} maxLength={100} placeholder="Exact technology name" />
    </label>
    <SelectField label="Sort projects" value={filters.ordering} options={[["newest", "Newest created"], ["oldest", "Oldest created"],
      ["recently_updated", "Recently updated"], ["title_asc", "Title A–Z"], ["title_desc", "Title Z–A"]]} onChange={(value) => change("ordering", value)} />
    <button type="button" onClick={onReset} className="self-end rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Reset project filters</button>
  </div>;
}

export function EventDiscoveryFilters({ filters, onChange, onReset }: {
  filters: EventFilters; onChange: (value: EventFilters) => void; onReset: () => void;
}) {
  const change = (key: keyof EventFilters, value: string) => onChange({ ...filters, [key]: value });
  return <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3" aria-label="Hackathon filters">
    <label className="flex min-w-0 flex-col gap-1 text-xs font-semibold text-slate-600">Search hackathons
      <input className={inputClass} value={filters.name} onChange={(event) => change("name", event.target.value)} maxLength={100} placeholder="Event name" />
    </label>
    <SelectField label="Participation status" value={filters.status} options={[["", "All statuses"], ["registered", "Registered"],
      ["attended", "Attended"], ["submitted", "Submitted"]]} onChange={(value) => change("status", value)} />
    <label className="flex min-w-0 flex-col gap-1 text-xs font-semibold text-slate-600">Event year
      <input className={inputClass} type="number" min="1" max="9999" value={filters.year} onChange={(event) => change("year", event.target.value)} placeholder="Any year" />
    </label>
    <SelectField label="Event format" value={filters.event_format} options={[["", "All formats"], ["online", "Online"],
      ["in_person", "In person"], ["hybrid", "Hybrid"], ["unknown", "Unknown"]]} onChange={(value) => change("event_format", value)} />
    <SelectField label="Event source" value={filters.source} options={[["", "All sources"], ["manual", "Manual"], ["devpost", "Devpost"]]} onChange={(value) => change("source", value)} />
    <SelectField label="Sort hackathons" value={filters.ordering} options={[["newest", "Newest recorded"], ["oldest", "Oldest recorded"],
      ["date_newest", "Event date newest"], ["date_oldest", "Event date oldest"], ["name_asc", "Name A–Z"]]} onChange={(value) => change("ordering", value)} />
    <button type="button" onClick={onReset} className="self-end rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">Reset hackathon filters</button>
  </div>;
}
