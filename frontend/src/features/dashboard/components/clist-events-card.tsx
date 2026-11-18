"use client";

import { ArrowRight, CalendarDays, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getDashboardEvents, type DashboardEvent } from "../api";

function formatEventTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function EventRow({ event }: { event: DashboardEvent }) {
  return (
    <a
      href={event.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group block border-b border-slate-100 py-3.5 last:border-b-0 hover:text-emerald-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500"
    >
      <div className="flex items-start justify-between gap-3">
        <span className="min-w-0 text-xs font-semibold leading-5 text-slate-900 group-hover:text-emerald-800">
          {event.title}
        </span>
        <ExternalLink aria-hidden="true" className="mt-0.5 size-3.5 shrink-0 text-slate-400" />
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] font-medium text-slate-500">
        <span className="max-w-full truncate text-slate-700">{event.platform}</span>
        <span aria-hidden="true">·</span>
        <span className={event.ongoing ? "text-emerald-700" : undefined}>
          {event.ongoing ? "Live · Ends " : "Starts "}
          {formatEventTime(event.ongoing ? event.end : event.start)}
        </span>
      </div>
    </a>
  );
}

export function ClistEventsCard() {
  const [events, setEvents] = useState<DashboardEvent[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    void getDashboardEvents().then(
      (response) => {
        if (!cancelled) {
          setEvents(response.events);
          setState("ready");
        }
      },
      () => {
        if (!cancelled) setState("error");
      },
    );
    return () => { cancelled = true; };
  }, [requestVersion]);

  return (
    <section aria-labelledby="sidebar-contests-heading" className="min-w-0">
      <div className="flex items-center justify-between gap-2 border-b border-slate-200 pb-3">
        <h2 id="sidebar-contests-heading" className="text-sm font-semibold text-slate-950">Live & upcoming contests</h2>
        <CalendarDays aria-hidden="true" className="size-4 shrink-0 text-emerald-600" />
      </div>
      <div className="mt-3 flex items-center justify-between gap-2 text-[11px] font-medium text-slate-500">
        <span className="inline-flex items-center gap-1.5">
          Events across platforms
        </span>
        <span>via CLIST</span>
      </div>

      {state === "loading" ? (
        <div aria-label="Loading contests" className="mt-4 grid gap-2" role="status">
          {[0, 1, 2].map((index) => (
            <div key={index} className="h-19 animate-pulse rounded-xl bg-slate-100" />
          ))}
        </div>
      ) : state === "error" ? (
        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-5 text-center">
          <p className="text-xs font-medium text-slate-600">Contests are unavailable right now.</p>
          <button
            type="button"
            onClick={() => { setState("loading"); setRequestVersion((value) => value + 1); }}
            className="mt-3 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50"
          >
            Try again
          </button>
        </div>
      ) : events.length === 0 ? (
        <p className="mt-4 rounded-xl bg-slate-50 px-4 py-6 text-center text-xs text-slate-600">
          No upcoming contests found.
        </p>
      ) : (
        <div aria-label="Upcoming contests" className="mt-3 max-h-[560px] overflow-y-auto pr-1">
          {events.slice(0, 30).map((event) => <EventRow key={event.id} event={event} />)}
        </div>
      )}

      <Link
        href="/contests"
        className="mt-4 inline-flex w-full items-center justify-between gap-2 border-t border-slate-200 pt-4 text-xs font-semibold text-emerald-700 hover:text-emerald-800 hover:underline"
      >
        View all contests
        <ArrowRight aria-hidden="true" className="size-3.5" />
      </Link>
    </section>
  );
}
