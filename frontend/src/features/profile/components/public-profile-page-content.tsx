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
import { PublicProfileFooter } from "./public-profile-footer";
import { PublicProfileNavbar } from "./public-profile-navbar";
import { PublicHackathonPortfolio } from "./hackathons/public-hackathon-portfolio";

function Block({ className = "" }: { className?: string }) { return <div className={`animate-pulse rounded-lg bg-slate-200 ${className}`} />; }
function PublicProfileLoading() {
  return (
    <div className="min-h-screen bg-white text-slate-900">
      <PublicProfileNavbar />
      <div className="relative h-36 overflow-hidden bg-[#a0b4b7] px-5 pt-3.5 sm:h-44 sm:pt-4 md:h-48">
        <div className="mx-auto max-w-310 sm:px-3">
          <Block className="h-4 w-40 bg-white/30" />
        </div>
      </div>
      <div className="mx-auto max-w-310 px-5 pb-9 sm:px-8">
        <div className="flex flex-wrap items-end gap-5">
          <Block className="-mt-14 size-28 rounded-full border-4 border-white bg-slate-300 sm:-mt-17 sm:size-34" />
          <div className="pb-2">
            <Block className="h-8 w-54" />
            <Block className="mt-3 h-4 w-28" />
          </div>
        </div>
        <div className="mt-9 grid grid-cols-2 gap-7 border-y border-slate-200 py-6 sm:grid-cols-4">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i}>
              <Block className="h-3 w-3/5" />
              <Block className="mt-3 h-8 w-20" />
            </div>
          ))}
        </div>
      </div>
      <main className="mx-auto max-w-310 px-5 py-12 sm:px-8">
        <Block className="h-7 w-60" />
        <div className="mt-8 space-y-5 border-t border-slate-200">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="flex items-center gap-5 border-b border-slate-200 py-5">
              <Block className="size-10 shrink-0" />
              <Block className="h-5 w-36" />
              <Block className="ml-auto h-5 w-20" />
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

function ProfileError({ notFound, message, onRetry }: { notFound: boolean; message: string; onRetry: () => void }) {
  const Icon = notFound ? SearchX : AlertCircle;
  return <div className="flex min-h-screen flex-col bg-white"><PublicProfileNavbar /><main className="grid flex-1 place-items-center px-5 py-20"><div className="w-full max-w-lg text-center"><Icon className="mx-auto size-10 text-[#1769b0]" /><h1 className="mt-5 text-2xl font-bold text-[#102c46]">{notFound ? "Profile not found" : "Could not load profile"}</h1><p className="mt-3 text-sm leading-6 text-slate-500">{notFound ? "The profile you’re looking for doesn’t exist or is no longer public." : message}</p>{!notFound ? <button type="button" onClick={onRetry} className="mt-6 h-10 rounded-lg bg-[#1769b0] px-5 text-sm font-semibold text-white hover:bg-[#125994]">Try again</button> : null}</div></main><PublicProfileFooter /></div>;
}

export function PublicProfilePageContent({ username }: { username: string }) {
  const [profile, setProfile] = useState<PublicProfileResponse | null>(null);
  const [loadedUsername, setLoadedUsername] = useState<string | null>(null);
  const [error, setError] = useState<{ message: string; notFound: boolean } | null>(null);
  const [failedUsername, setFailedUsername] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const invalidUsername = !username.trim();
  useEffect(() => {
    let cancelled = false;
    if (invalidUsername) return;
    void getPublicProfile(username).then((data) => { if (!cancelled) { setProfile(data); setLoadedUsername(username); setError(null); setFailedUsername(null); } }).catch((requestError: unknown) => { if (!cancelled) { setFailedUsername(username); setError({ message: getApiErrorMessage(requestError, "The profile service is unavailable."), notFound: requestError instanceof AxiosError && requestError.response?.status === 404 }); } });
    return () => { cancelled = true; };
  }, [invalidUsername, username, version]);
  const view = useMemo(() => profile && loadedUsername === username ? buildPublicProfileViewModel(profile) : null, [profile, loadedUsername, username]);
  const currentError = failedUsername === username ? error : null;
  if (invalidUsername) return <ProfileError notFound message="A username is required." onRetry={() => undefined} />;
  if (!view && !currentError) return <PublicProfileLoading />;
  if (!view && currentError) return <ProfileError {...currentError} onRetry={() => { setError(null); setVersion((value) => value + 1); }} />;
  if (!view) return null;
  return (
    <div className="min-h-screen bg-white text-slate-900">
      <PublicProfileNavbar />
      <ProfileHero
        hero={view.hero}
        metrics={view.summaryMetrics}
        onProfileUpdated={() => setVersion((v) => v + 1)}
      />
      <main className="mx-auto max-w-310 px-5 sm:px-8">
        <PlatformsOverview platforms={view.platforms} />
        <CompetitiveProgrammingSection
          platforms={view.competitivePlatforms}
          metrics={view.competitiveMetrics}
          performance={view.performance}
        />
        <DomainProfileCards cards={view.domainCards} />
        <PublicHackathonPortfolio key={username} username={username} />
      </main>
      <PublicProfileFooter />
    </div>
  );
}
