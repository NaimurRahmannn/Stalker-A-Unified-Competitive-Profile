"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { isAxiosError } from "axios";
import {
  AlertCircle,
  ArrowLeft,
  Building2,
  Code2,
  ExternalLink,
  Link2,
  MapPin,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { platformLogoSrc } from "@/features/dashboard/data";
import { journeyAccentStyles } from "@/features/dashboard/styles";
import type { PlatformMark } from "@/features/dashboard/types";
import { getPublicProfile } from "@/features/profile/api";
import type { PublicProfileResponse } from "@/features/profile/types";
import {
  buildPublicProfileViewModel,
  type CodeforcesSummaryView,
  type ProfileDomainPlaceholder,
  type ProfileHeroView,
  type ProfileStatView,
  type PublicPlatformView,
  type PublicProfileViewModel,
} from "@/features/profile/view-model";
import { getApiErrorMessage } from "@/lib/utils";

type LoadStatus = "loading" | "success" | "error" | "not_found";

function LoadingState() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto w-full max-w-6xl px-5 py-6 sm:px-6 lg:px-8">
        <div className="h-10 w-40 animate-pulse rounded-xl bg-slate-200" />
        <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_16px_38px_rgba(15,23,42,0.045)] sm:p-6">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
            <div className="size-22 animate-pulse rounded-3xl bg-slate-200" />
            <div className="min-w-0 flex-1">
              <div className="h-8 w-56 animate-pulse rounded-lg bg-slate-200" />
              <div className="mt-3 h-4 w-32 animate-pulse rounded bg-slate-200" />
              <div className="mt-5 h-4 w-full max-w-xl animate-pulse rounded bg-slate-100" />
            </div>
          </div>
        </section>
        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="grid gap-6">
            {Array.from({ length: 3 }, (_, index) => (
              <div
                key={index}
                className="h-56 animate-pulse rounded-2xl border border-slate-200 bg-white shadow-[0_14px_34px_rgba(15,23,42,0.04)]"
              />
            ))}
          </div>
          <div className="h-96 animate-pulse rounded-2xl border border-slate-200 bg-white shadow-[0_14px_34px_rgba(15,23,42,0.04)]" />
        </div>
      </div>
    </main>
  );
}

function StateCard({
  title,
  message,
  actionLabel,
  onRetry,
}: {
  title: string;
  message: string;
  actionLabel?: string;
  onRetry?: () => void;
}) {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 px-5 py-10">
      <section className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-[0_16px_38px_rgba(15,23,42,0.045)]">
        <span className="mx-auto grid size-12 place-items-center rounded-2xl bg-slate-50 text-slate-500">
          <AlertCircle className="size-6" />
        </span>
        <h1 className="mt-4 text-xl font-semibold text-slate-950">{title}</h1>
        <p className="mx-auto mt-2 max-w-sm text-sm font-medium leading-6 text-slate-500">
          {message}
        </p>
        <div className="mt-5 flex flex-col justify-center gap-2 sm:flex-row">
          <Link
            href="/"
            className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-[13px] font-semibold text-slate-900 shadow-sm transition hover:bg-slate-50"
          >
            <ArrowLeft className="size-4" />
            Home
          </Link>
          {onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-4 text-[13px] font-semibold text-blue-700 transition hover:bg-blue-100"
            >
              <RefreshCw className="size-4" />
              {actionLabel ?? "Try again"}
            </button>
          ) : null}
        </div>
      </section>
    </main>
  );
}

function Avatar({ hero }: { hero: ProfileHeroView }) {
  if (hero.avatarUrl) {
    return (
      <span
        aria-label={`${hero.displayName} avatar`}
        className="block size-22 shrink-0 rounded-3xl border border-slate-200 bg-slate-100 bg-cover bg-center shadow-inner"
        role="img"
        style={{ backgroundImage: `url("${hero.avatarUrl}")` }}
      />
    );
  }

  return (
    <span className="grid size-22 shrink-0 place-items-center rounded-3xl bg-emerald-50 text-2xl font-semibold text-emerald-700 ring-1 ring-emerald-100">
      {hero.initials}
    </span>
  );
}

function ProfileHero({ hero }: { hero: ProfileHeroView }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_16px_38px_rgba(15,23,42,0.045)] sm:p-6">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <Avatar hero={hero} />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-emerald-600">
            Public profile
          </p>
          <h1 className="mt-2 truncate text-3xl font-semibold leading-tight tracking-normal text-slate-950">
            {hero.displayName}
          </h1>
          <p className="mt-1 text-sm font-medium text-slate-500">
            @{hero.username}
          </p>
          {hero.bio ? (
            <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600">
              {hero.bio}
            </p>
          ) : null}
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {hero.country ? (
          <span className="inline-flex h-9 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 text-xs font-semibold text-slate-700">
            <MapPin className="size-4 text-emerald-600" />
            {hero.country}
          </span>
        ) : null}
        {hero.institution ? (
          <span className="inline-flex h-9 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 text-xs font-semibold text-slate-700">
            <Building2 className="size-4 text-blue-600" />
            {hero.institution}
          </span>
        ) : null}
        {hero.socialLinks.map((link) => {
          const Icon = link.icon;

          return (
            <a
              key={link.label}
              href={link.href}
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-9 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
            >
              <Icon className="size-4 text-slate-600" />
              {link.label}
              <ExternalLink className="size-3.5 text-slate-400" />
            </a>
          );
        })}
      </div>
    </section>
  );
}

function SectionShell({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_14px_34px_rgba(15,23,42,0.04)] sm:p-5">
      <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
      {children}
    </section>
  );
}

function StatTile({ stat }: { stat: ProfileStatView }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/70 px-3 py-3">
      <p className="text-[11px] font-medium uppercase tracking-[0.04em] text-slate-500">
        {stat.label}
      </p>
      <p className="mt-1 truncate text-base font-semibold text-slate-950">
        {stat.value}
      </p>
    </div>
  );
}

function CodeforcesSummary({ summary }: { summary: CodeforcesSummaryView }) {
  const isSynced = summary.state === "synced";

  return (
    <SectionShell title={summary.title}>
      <div className="mt-4 flex flex-col gap-4 rounded-2xl border border-emerald-100 bg-emerald-50/30 p-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-white text-emerald-600 ring-1 ring-emerald-100">
            <Code2 className="size-5" />
          </span>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-950">
              {summary.description}
            </p>
            {summary.handle ? (
              summary.profileUrl ? (
                <a
                  href={summary.profileUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-blue-700 transition hover:text-blue-800"
                >
                  {summary.handle}
                  <ExternalLink className="size-3.5" />
                </a>
              ) : (
                <p className="mt-1 text-xs font-medium text-slate-500">
                  {summary.handle}
                </p>
              )
            ) : null}
          </div>
        </div>
        <span
          className={`inline-flex h-8 shrink-0 items-center justify-center rounded-full px-3 text-xs font-semibold ${
            isSynced
              ? "bg-emerald-100 text-emerald-700"
              : "bg-slate-100 text-slate-600"
          }`}
        >
          {isSynced ? "Live stats" : "No stats yet"}
        </span>
      </div>

      {summary.primaryStats.length > 0 ? (
        <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {summary.primaryStats.map((stat) => (
            <StatTile key={stat.label} stat={stat} />
          ))}
        </div>
      ) : null}

      {summary.detailStats.length > 0 ? (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {summary.detailStats.map((stat) => (
            <StatTile key={stat.label} stat={stat} />
          ))}
        </div>
      ) : null}
    </SectionShell>
  );
}

function PlatformMark({ mark }: { mark: PlatformMark | null }) {
  if (!mark) {
    return (
      <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-slate-50 text-slate-500">
        <Link2 className="size-5" />
      </span>
    );
  }

  const logoSize =
    mark === "codeforces" || mark === "github" ? "size-8" : "size-9";

  return (
    <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-slate-50">
      <Image
        src={platformLogoSrc[mark]}
        alt=""
        width={40}
        height={40}
        className={`${logoSize} object-contain`}
      />
    </span>
  );
}

function PlatformCard({ platform }: { platform: PublicPlatformView }) {
  const badgeClass =
    platform.status === "Verified"
      ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
      : "bg-orange-50 text-orange-700 ring-1 ring-orange-200";

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_26px_rgba(15,23,42,0.035)]">
      <div className="flex items-start gap-3">
        <PlatformMark mark={platform.mark} />
        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-950">
                {platform.name}
              </p>
              {platform.profileUrl ? (
                <a
                  href={platform.profileUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex max-w-full items-center gap-1 truncate text-xs font-semibold text-blue-700 transition hover:text-blue-800"
                >
                  <span className="truncate">{platform.handle}</span>
                  <ExternalLink className="size-3.5 shrink-0" />
                </a>
              ) : (
                <p className="mt-1 truncate text-xs font-medium text-slate-500">
                  {platform.handle}
                </p>
              )}
            </div>
            <span
              className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold ${badgeClass}`}
            >
              {platform.status === "Verified" ? (
                <ShieldCheck className="size-3.5" />
              ) : (
                <ShieldAlert className="size-3.5" />
              )}
              {platform.status}
            </span>
          </div>
          <p className="mt-3 text-xs font-medium text-slate-500">
            Last synced: {platform.lastSyncedLabel}
          </p>
        </div>
      </div>
    </article>
  );
}

function ConnectedPlatforms({ platforms }: { platforms: PublicPlatformView[] }) {
  return (
    <SectionShell title="Connected Platforms">
      {platforms.length > 0 ? (
        <div className="mt-4 grid gap-3">
          {platforms.map((platform) => (
            <PlatformCard key={platform.id} platform={platform} />
          ))}
        </div>
      ) : (
        <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 px-4 py-10 text-center">
          <span className="mx-auto grid size-12 place-items-center rounded-2xl bg-white text-slate-400">
            <Link2 className="size-5" />
          </span>
          <p className="mt-3 text-sm font-semibold text-slate-950">
            No platforms connected yet
          </p>
          <p className="mt-1 text-xs font-medium text-slate-500">
            Public platform accounts will appear here after connection.
          </p>
        </div>
      )}
    </SectionShell>
  );
}

function DomainPlaceholderCard({
  placeholder,
}: {
  placeholder: ProfileDomainPlaceholder;
}) {
  const Icon = placeholder.icon;
  const accent = journeyAccentStyles[placeholder.accent];

  return (
    <article
      className={`rounded-2xl border bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.035)] ${accent.border}`}
    >
      <span
        className={`grid size-10 place-items-center rounded-xl ${accent.iconBg} ${accent.icon}`}
      >
        <Icon className="size-5" />
      </span>
      <p className="mt-5 text-sm font-semibold text-slate-950">
        {placeholder.title}
      </p>
      <p className={`mt-2 text-xl font-semibold ${accent.value}`}>
        Coming soon
      </p>
      <p className="mt-1 text-xs font-medium leading-5 text-slate-500">
        {placeholder.label}. No public stats available yet.
      </p>
    </article>
  );
}

function DomainPlaceholders({
  placeholders,
}: {
  placeholders: ProfileDomainPlaceholder[];
}) {
  return (
    <SectionShell title="Other Domains">
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {placeholders.map((placeholder) => (
          <DomainPlaceholderCard
            key={placeholder.title}
            placeholder={placeholder}
          />
        ))}
      </div>
    </SectionShell>
  );
}

function ProfileContent({ viewModel }: { viewModel: PublicProfileViewModel }) {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <div className="mx-auto w-full max-w-6xl px-5 py-6 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between gap-4">
          <Link
            href="/"
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-900 shadow-sm transition hover:bg-slate-50"
          >
            <ArrowLeft className="size-4 text-slate-500" />
            STALKER
          </Link>
          <span className="hidden text-xs font-semibold uppercase tracking-[0.08em] text-slate-400 sm:inline">
            Shareable technical profile
          </span>
        </header>

        <div className="mt-6">
          <ProfileHero hero={viewModel.hero} />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="grid min-w-0 gap-6">
            <CodeforcesSummary summary={viewModel.codeforces} />
            <DomainPlaceholders
              placeholders={viewModel.domainPlaceholders}
            />
          </div>
          <aside className="min-w-0">
            <ConnectedPlatforms platforms={viewModel.platforms} />
          </aside>
        </div>
      </div>
    </main>
  );
}

export function PublicProfilePageContent({ username }: { username: string }) {
  const [profile, setProfile] = useState<PublicProfileResponse | null>(null);
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const data = await getPublicProfile(username);

        if (cancelled) {
          return;
        }

        setProfile(data);
        setStatus("success");
      } catch (err) {
        if (cancelled) {
          return;
        }

        setProfile(null);

        if (isAxiosError(err) && err.response?.status === 404) {
          setStatus("not_found");
          return;
        }

        setErrorMessage(
          getApiErrorMessage(err, "Failed to load this public profile."),
        );
        setStatus("error");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [requestVersion, username]);

  const retry = () => {
    setProfile(null);
    setErrorMessage("");
    setStatus("loading");
    setRequestVersion((version) => version + 1);
  };

  const viewModel = useMemo(
    () => (profile ? buildPublicProfileViewModel(profile) : null),
    [profile],
  );

  if (status === "loading") {
    return <LoadingState />;
  }

  if (status === "not_found") {
    return (
      <StateCard
        title="Profile not found"
        message="That username does not match a public Stalker profile."
      />
    );
  }

  if (status === "error") {
    return (
      <StateCard
        title="Could not load profile"
        message={errorMessage}
        actionLabel="Retry"
        onRetry={retry}
      />
    );
  }

  if (!viewModel) {
    return (
      <StateCard
        title="Profile unavailable"
        message="The profile response was empty. Please try again."
        actionLabel="Retry"
        onRetry={retry}
      />
    );
  }

  return <ProfileContent viewModel={viewModel} />;
}
