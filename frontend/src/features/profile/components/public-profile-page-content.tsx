"use client";

import { useEffect, useMemo, useState } from "react";
import { AxiosError } from "axios";
import { AlertCircle, SearchX } from "lucide-react";
import { getPublicProfile } from "../api";
import type { PublicProfileResponse } from "../types";
import { buildPublicProfileViewModel } from "../view-model";
import { getApiErrorMessage } from "@/lib/utils";
import { CompetitiveProgrammingSection } from "./competitive-programming-section";
import { DomainProfileCards } from "./domain-profile-cards";
import { PlatformsOverview } from "./platforms-overview";
import { ProfileHero } from "./profile-hero";
import { ProfileRecentSections } from "./profile-recent-sections";
import { PublicProfileFooter } from "./public-profile-footer";
import { PublicProfileNavbar } from "./public-profile-navbar";

function Block({ className = "" }: { className?: string }) { return <div className={`animate-pulse rounded-lg bg-slate-200 ${className}`} />; }
function PublicProfileLoading() {
  return <div className="min-h-screen bg-slate-50 text-slate-900"><PublicProfileNavbar /><div className="border-b border-slate-100 bg-white"><div className="mx-auto grid max-w-310 gap-8 px-5 py-10 sm:px-8 lg:grid-cols-[1fr_535px]"><div className="flex items-center gap-6"><Block className="size-42 shrink-0 rounded-full" /><div className="flex-1"><Block className="h-7 w-52" /><Block className="mt-3 h-4 w-28" /><Block className="mt-6 h-4 w-full max-w-80" /><Block className="mt-2 h-4 w-64" /></div></div><div><div className="mb-8 ml-auto flex w-62 gap-3"><Block className="h-10 flex-1" /><Block className="h-10 flex-1" /></div><div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{Array.from({ length: 4 }, (_, i) => <Block key={i} className="h-39" />)}</div></div></div></div><main className="mx-auto max-w-310 space-y-4 px-5 py-7 sm:px-8"><div className="rounded-xl border border-slate-200 bg-white p-5"><Block className="h-5 w-40" /><div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">{Array.from({ length: 6 }, (_, i) => <Block key={i} className="h-49" />)}</div></div><div className="grid gap-4 lg:grid-cols-[3fr_1fr]"><Block className="h-150 bg-white ring-1 ring-slate-200" /><Block className="h-112 bg-white ring-1 ring-slate-200" /></div></main></div>;
}

function ProfileError({ notFound, message, onRetry }: { notFound: boolean; message: string; onRetry: () => void }) {
  const Icon = notFound ? SearchX : AlertCircle;
  return <div className="flex min-h-screen flex-col bg-slate-50"><PublicProfileNavbar /><main className="grid flex-1 place-items-center px-5 py-20"><div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white px-8 py-14 text-center shadow-sm"><span className="mx-auto grid size-13 place-items-center rounded-2xl bg-emerald-50 text-emerald-600"><Icon className="size-6" /></span><h1 className="mt-5 text-xl font-bold text-slate-950">{notFound ? "Profile not found" : "Could not load profile"}</h1><p className="mt-2 text-sm leading-6 text-slate-500">{notFound ? "The profile you’re looking for doesn’t exist or is no longer public." : message}</p>{!notFound ? <button type="button" onClick={onRetry} className="mt-6 h-10 rounded-lg bg-emerald-600 px-5 text-xs font-semibold text-white hover:bg-emerald-700">Try again</button> : null}</div></main><PublicProfileFooter /></div>;
}

export function PublicProfilePageContent({ username }: { username: string }) {
  const [profile, setProfile] = useState<PublicProfileResponse | null>(null);
  const [error, setError] = useState<{ message: string; notFound: boolean } | null>(null);
  const [version, setVersion] = useState(0);
  const invalidUsername = !username.trim();
  useEffect(() => {
    let cancelled = false;
    if (invalidUsername) return;
    void getPublicProfile(username).then((data) => { if (!cancelled) { setProfile(data); setError(null); } }).catch((requestError: unknown) => { if (!cancelled) setError({ message: getApiErrorMessage(requestError, "The profile service is unavailable."), notFound: requestError instanceof AxiosError && requestError.response?.status === 404 }); });
    return () => { cancelled = true; };
  }, [invalidUsername, username, version]);
  const view = useMemo(() => profile ? buildPublicProfileViewModel(profile) : null, [profile]);
  if (invalidUsername) return <ProfileError notFound message="A username is required." onRetry={() => undefined} />;
  if (!view && !error) return <PublicProfileLoading />;
  if (!view && error) return <ProfileError {...error} onRetry={() => { setError(null); setVersion((value) => value + 1); }} />;
  if (!view) return null;
  return <div className="min-h-screen bg-slate-50 text-slate-900"><PublicProfileNavbar /><ProfileHero hero={view.hero} metrics={view.summaryMetrics} /><main className="mx-auto max-w-310 space-y-4 px-5 py-7 sm:px-8"><PlatformsOverview platforms={view.platforms} /><CompetitiveProgrammingSection platforms={view.competitivePlatforms} metrics={view.competitiveMetrics} performance={view.performance} /><DomainProfileCards cards={view.domainCards} /><ProfileRecentSections /></main><PublicProfileFooter /></div>;
}
