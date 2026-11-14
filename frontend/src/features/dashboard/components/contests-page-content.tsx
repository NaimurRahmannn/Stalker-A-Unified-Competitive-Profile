"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, CalendarDays, Clock3, ExternalLink, Search } from "lucide-react";
import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { useAuth } from "@/hooks/use-auth";
import { getDashboardEvents, type DashboardEvent } from "../api";

type ContestFilter = "all" | "live" | "upcoming";

function eventPhase(event: DashboardEvent, now: number): "live" | "upcoming" | "ended" {
  if (Date.parse(event.end) <= now) return "ended";
  return Date.parse(event.start) <= now ? "live" : "upcoming";
}

function formatStart(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  }).format(new Date(value));
}

function formatDuration(event: DashboardEvent) {
  const minutes = Math.max(0, Math.round((Date.parse(event.end) - Date.parse(event.start)) / 60_000));
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const remainingMinutes = minutes % 60;
  if (days) return `${days}d ${hours}h`;
  if (hours) return `${hours}h ${remainingMinutes}m`;
  return `${remainingMinutes}m`;
}

function formatTimeLeft(event: DashboardEvent, now: number) {
  const phase = eventPhase(event, now);
  if (phase === "ended") return "Ended";
  const milliseconds = Date.parse(phase === "live" ? event.end : event.start) - now;
  const minutes = Math.ceil(milliseconds / 60_000);
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  if (days) return `${days}d ${hours}h`;
  if (hours) return `${hours}h ${minutes % 60}m`;
  return `${Math.max(1, minutes)}m`;
}

function StatusBadge({ live }: { live: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${live ? "bg-emerald-50 text-emerald-700" : "bg-blue-50 text-blue-700"}`}>
      <span className={`size-1.5 rounded-full ${live ? "bg-emerald-500" : "bg-blue-500"}`} />
      {live ? "Live" : "Upcoming"}
    </span>
  );
}

function ContestLink({ event }: { event: DashboardEvent }) {
  return (
    <a
      href={event.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group inline-flex min-w-0 items-start gap-1.5 font-semibold leading-5 text-slate-900 hover:text-emerald-700 focus-visible:rounded focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500"
    >
      <span className="min-w-0 break-words">{event.title}</span>
      <ExternalLink aria-hidden="true" className="mt-0.5 size-3.5 shrink-0 text-slate-400 group-hover:text-emerald-600" />
    </a>
  );
}

function ContestTable({ events, now }: { events: DashboardEvent[]; now: number }) {
  return (
    <div className="hidden overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_12px_30px_rgba(15,23,42,0.035)] xl:block">
      <table className="w-full table-fixed text-left text-sm">
        <caption className="sr-only">Live and upcoming contests across platforms</caption>
        <colgroup>
          <col className="w-[190px]" />
          <col className="w-[120px]" />
          <col className="w-[105px]" />
          <col />
          <col className="w-[170px]" />
        </colgroup>
        <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          <tr>
            <th scope="col" className="px-5 py-3.5">Start time</th>
            <th scope="col" className="px-3 py-3.5">Time left</th>
            <th scope="col" className="px-3 py-3.5">Duration</th>
            <th scope="col" className="px-3 py-3.5">Contest</th>
            <th scope="col" className="px-5 py-3.5">Platform</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {events.map((event) => {
            const live = eventPhase(event, now) === "live";
            return (
              <tr key={event.id} className={`align-top transition hover:bg-slate-50/80 ${live ? "bg-emerald-50/30" : ""}`}>
                <td className="px-5 py-4 font-medium text-slate-700"><time dateTime={event.start}>{formatStart(event.start)}</time></td>
                <td className={`px-3 py-4 font-semibold tabular-nums ${live ? "text-emerald-700" : "text-slate-700"}`}>
                  <span className="block text-[10px] font-medium uppercase tracking-wide text-slate-400">{live ? "Ends in" : "Starts in"}</span>
                  {formatTimeLeft(event, now)}
                </td>
                <td className="px-3 py-4 tabular-nums text-slate-600">{formatDuration(event)}</td>
                <td className="px-3 py-4">
                  <ContestLink event={event} />
                  <div className="mt-1.5"><StatusBadge live={live} /></div>
                </td>
                <td className="break-words px-5 py-4 text-xs font-semibold text-slate-600">{event.platform}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ContestMobileList({ events, now }: { events: DashboardEvent[]; now: number }) {
  return (
    <div className="grid gap-3 xl:hidden">
      {events.map((event) => {
        const live = eventPhase(event, now) === "live";
        return (
          <article key={event.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_25px_rgba(15,23,42,0.035)] sm:p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="break-all text-xs font-semibold text-slate-500">{event.platform}</span>
              <StatusBadge live={live} />
            </div>
            <h3 className="mt-3 text-sm sm:text-base"><ContestLink event={event} /></h3>
            <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-100 pt-3 text-xs sm:grid-cols-3">
              <div className="col-span-2 sm:col-span-1"><dt className="text-slate-500">Starts</dt><dd className="mt-1 font-semibold text-slate-800"><time dateTime={event.start}>{formatStart(event.start)}</time></dd></div>
              <div><dt className="text-slate-500">{live ? "Ends in" : "Starts in"}</dt><dd className="mt-1 font-semibold tabular-nums text-emerald-700">{formatTimeLeft(event, now)}</dd></div>
              <div><dt className="text-slate-500">Duration</dt><dd className="mt-1 font-semibold tabular-nums text-slate-800">{formatDuration(event)}</dd></div>
            </dl>
          </article>
        );
      })}
    </div>
  );
}

export function ContestsPageContent() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [events, setEvents] = useState<DashboardEvent[]>([]);
  const [nextPage, setNextPage] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(false);
  const [loadMoreError, setLoadMoreError] = useState(false);
  const [retryVersion, setRetryVersion] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const [query, setQuery] = useState("");
  const [platform, setPlatform] = useState("");
  const [filter, setFilter] = useState<ContestFilter>("all");
  const requestVersion = useRef(0);
  const loadInFlight = useRef(false);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    const version = ++requestVersion.current;
    void getDashboardEvents(1).then(
      (response) => {
        if (version !== requestVersion.current) return;
        setEvents(response.events);
        setNextPage(response.next_page);
        setError(false);
        setLoading(false);
      },
      () => {
        if (version !== requestVersion.current) return;
        setError(true);
        setLoading(false);
      },
    );
    return () => { requestVersion.current += 1; };
  }, [authLoading, user, router, retryVersion]);

  async function loadMore() {
    if (nextPage === null || loadInFlight.current) return;
    loadInFlight.current = true;
    setLoadingMore(true);
    setLoadMoreError(false);
    const version = requestVersion.current;
    try {
      const response = await getDashboardEvents(nextPage);
      if (version !== requestVersion.current) return;
      setEvents((current) => {
        const seen = new Set(current.map((event) => event.id));
        return [...current, ...response.events.filter((event) => !seen.has(event.id))];
      });
      setNextPage(response.next_page);
    } catch {
      if (version === requestVersion.current) setLoadMoreError(true);
    } finally {
      loadInFlight.current = false;
      if (version === requestVersion.current) setLoadingMore(false);
    }
  }

  const activeEvents = useMemo(() => events.filter((event) => eventPhase(event, now) !== "ended"), [events, now]);
  const platforms = useMemo(() => [...new Set(activeEvents.map((event) => event.platform))].sort((a, b) => a.localeCompare(b)), [activeEvents]);
  const liveCount = activeEvents.filter((event) => eventPhase(event, now) === "live").length;
  const search = query.trim().toLocaleLowerCase();
  const visibleEvents = activeEvents.filter((event) =>
    (filter === "all" || eventPhase(event, now) === filter)
    && (!platform || event.platform === platform)
    && (!search || `${event.title} ${event.platform}`.toLocaleLowerCase().includes(search)),
  );
  const hasFilters = Boolean(query || platform || filter !== "all");

  return (
    <div className="min-w-0 bg-slate-50">
      <DashboardMobileNav activeItem="contests" />
      <div className="mx-auto max-w-7xl space-y-6 p-5 sm:p-6 lg:p-8">
        <header className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 via-white to-white p-5 sm:p-7">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-emerald-700">Contest schedule</p>
              <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">All contests</h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Live and upcoming contests across platforms, in your local timezone.</p>
            </div>
            <span className="inline-flex items-center gap-2 rounded-xl border border-emerald-100 bg-white px-3 py-2 text-xs font-semibold text-emerald-800 shadow-sm">
              <CalendarDays aria-hidden="true" className="size-4" />
              Data from CLIST
            </span>
          </div>
          {!loading && !error && user ? (
            <div className="mt-6 flex flex-wrap gap-2 border-t border-emerald-100 pt-4 text-xs font-semibold">
              <span className="rounded-lg bg-white px-3 py-2 text-emerald-700 ring-1 ring-emerald-100">{liveCount} live now</span>
              <span className="rounded-lg bg-white px-3 py-2 text-blue-700 ring-1 ring-blue-100">{activeEvents.length - liveCount} upcoming</span>
              <span className="rounded-lg bg-white px-3 py-2 text-slate-600 ring-1 ring-slate-200">{events.length} loaded</span>
            </div>
          ) : null}
        </header>

        <section aria-labelledby="contest-list-heading">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
            <div>
              <h2 id="contest-list-heading" className="text-lg font-semibold text-slate-950">Browse contests</h2>
              <p className="mt-1 text-xs text-slate-500">Search and filters apply to the contests you have loaded.</p>
            </div>
            {!loading && !error ? <p className="text-xs font-medium text-slate-500">Showing {visibleEvents.length} of {activeEvents.length} loaded contests</p> : null}
          </div>

          {!loading && !error && events.length > 0 ? (
            <div className="mb-4 grid gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm sm:p-4 lg:grid-cols-[minmax(0,1fr)_auto_auto] lg:items-center">
              <label className="relative block min-w-0">
                <span className="sr-only">Search loaded contests</span>
                <Search aria-hidden="true" className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search loaded contests" className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100" />
              </label>
              <div aria-label="Contest status" className="flex rounded-xl bg-slate-100 p-1">
                {(["all", "live", "upcoming"] as const).map((value) => (
                  <button key={value} type="button" aria-pressed={filter === value} onClick={() => setFilter(value)} className={`flex-1 rounded-lg px-3 py-1.5 text-xs font-semibold capitalize transition lg:flex-none ${filter === value ? "bg-white text-emerald-700 shadow-sm" : "text-slate-500 hover:text-slate-800"}`}>
                    {value}
                  </button>
                ))}
              </div>
              <label className="block min-w-0">
                <span className="sr-only">Filter loaded contests by platform</span>
                <select value={platform} onChange={(event) => setPlatform(event.target.value)} className="h-10 w-full max-w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-medium text-slate-700 outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 lg:w-44">
                  <option value="">All platforms</option>
                  {platforms.map((name) => <option key={name} value={name}>{name}</option>)}
                </select>
              </label>
            </div>
          ) : null}

          {authLoading || !user || loading ? (
            <div aria-label="Loading contests" role="status" className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
              {Array.from({ length: 5 }, (_, index) => <div key={index} className="h-18 animate-pulse border-b border-slate-100 p-4 last:border-b-0"><div className="h-4 w-2/3 rounded bg-slate-100" /><div className="mt-3 h-3 w-1/3 rounded bg-slate-100" /></div>)}
            </div>
          ) : error ? (
            <div role="alert" className="rounded-2xl border border-slate-200 bg-white px-6 py-12 text-center">
              <p className="text-sm font-semibold text-slate-900">Contests are unavailable right now.</p>
              <button type="button" onClick={() => { setLoading(true); setRetryVersion((version) => version + 1); }} className="mt-4 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">Try again</button>
            </div>
          ) : visibleEvents.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center text-sm text-slate-600">
              <Clock3 aria-hidden="true" className="mx-auto mb-3 size-6 text-slate-400" />
              {hasFilters ? "No loaded contests match your filters." : "No live or upcoming contests are available right now."}
              {hasFilters ? <button type="button" onClick={() => { setQuery(""); setPlatform(""); setFilter("all"); }} className="ml-2 font-semibold text-emerald-700 hover:underline">Clear filters</button> : null}
            </div>
          ) : (
            <>
              <ContestTable events={visibleEvents} now={now} />
              <ContestMobileList events={visibleEvents} now={now} />
            </>
          )}

          {!loading && !error && user ? (
            <>
              {loadMoreError ? <p role="alert" className="mt-5 text-center text-sm text-rose-700">Could not load more contests. Try again.</p> : null}
              {nextPage !== null ? (
                <div className="mt-6 flex justify-center">
                  <button type="button" onClick={() => void loadMore()} disabled={loadingMore} className="inline-flex items-center gap-2 rounded-xl border border-emerald-200 bg-white px-5 py-2.5 text-sm font-semibold text-emerald-700 shadow-sm hover:bg-emerald-50 disabled:cursor-wait disabled:opacity-60">
                    {loadingMore ? "Loading contests..." : "Load more contests"}
                    {!loadingMore ? <ArrowRight aria-hidden="true" className="size-4" /> : null}
                  </button>
                </div>
              ) : null}
            </>
          ) : null}
        </section>
      </div>
    </div>
  );
}
