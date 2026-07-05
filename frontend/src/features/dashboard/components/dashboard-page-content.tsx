"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle } from "lucide-react";
import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { getDashboard, type DashboardResponse } from "@/features/dashboard/api";
import { buildDashboardViewModel } from "@/features/dashboard/view-model";
import { getApiErrorMessage } from "@/lib/utils";
import { ConnectedPlatformsSection } from "./connected-platforms-section";
import { DashboardTopHeader } from "./dashboard-top-header";
import { MetricCardsSection } from "./metric-cards-section";
import { RecentAchievementsSection } from "./recent-achievements-section";
import { RightWidgetsPanel } from "./right-widgets-panel";
import { TechnicalJourneySection } from "./technical-journey-section";

function DashboardHeaderSkeleton() {
  return (
    <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8">
      <div className="animate-pulse">
        <div className="h-8 w-64 rounded-lg bg-slate-200" />
        <div className="mt-3 h-5 w-full max-w-md rounded-lg bg-slate-200" />
      </div>
    </section>
  );
}

function MetricCardsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }, (_, index) => (
        <div
          key={index}
          className="h-24 animate-pulse rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_12px_30px_rgba(15,23,42,0.035)]"
        >
          <div className="h-10 w-10 rounded-xl bg-slate-200" />
          <div className="mt-3 h-4 w-24 rounded bg-slate-200" />
        </div>
      ))}
    </div>
  );
}

function CardsSkeleton({ count }: { count: number }) {
  return (
    <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 min-[1600px]:grid-cols-4">
      {Array.from({ length: count }, (_, index) => (
        <div
          key={index}
          className="h-72 animate-pulse rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_16px_38px_rgba(15,23,42,0.045)]"
        >
          <div className="h-10 w-10 rounded-xl bg-slate-200" />
          <div className="mt-8 h-7 w-28 rounded bg-slate-200" />
          <div className="mt-4 h-4 w-36 rounded bg-slate-200" />
          <div className="mt-8 h-13 rounded-xl bg-slate-100" />
        </div>
      ))}
    </div>
  );
}

function SectionSkeleton() {
  return (
    <div className="mt-6 h-52 animate-pulse rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <div className="h-5 w-40 rounded bg-slate-200" />
      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
        {Array.from({ length: 4 }, (_, index) => (
          <div key={index} className="h-28 rounded-2xl bg-slate-100" />
        ))}
      </div>
    </div>
  );
}

function DashboardLoadingState() {
  return (
    <>
      <DashboardHeaderSkeleton />
      <div className="grid min-w-0 grid-cols-1 gap-6 p-5 sm:p-6 lg:p-8 xl:grid-cols-[minmax(0,1fr)_340px]">
        <section className="min-w-0">
          <MetricCardsSkeleton />
          <section className="mt-7">
            <div className="h-5 w-44 animate-pulse rounded bg-slate-200" />
            <CardsSkeleton count={4} />
          </section>
          <SectionSkeleton />
          <SectionSkeleton />
        </section>
        <aside className="hidden min-w-0 border-t border-slate-200 pt-6 xl:block xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
          <div className="grid gap-4">
            {Array.from({ length: 3 }, (_, index) => (
              <div
                key={index}
                className="h-52 animate-pulse rounded-2xl border border-slate-200 bg-white"
              />
            ))}
          </div>
        </aside>
      </div>
    </>
  );
}

function DashboardErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="rounded-2xl border border-red-100 bg-red-50/70 px-5 py-12 text-center shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <span className="mx-auto grid size-12 place-items-center rounded-2xl bg-white text-red-600">
        <AlertCircle className="size-6" />
      </span>
      <p className="mt-4 text-sm font-semibold text-red-700">
        Could not load dashboard data
      </p>
      <p className="mx-auto mt-2 max-w-md text-xs font-medium leading-5 text-red-600">
        {message}
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 inline-flex h-10 items-center justify-center rounded-xl border border-red-200 bg-white px-4 text-[13px] font-semibold text-red-700 shadow-sm transition hover:bg-red-50"
      >
        Try again
      </button>
    </div>
  );
}

function RefreshErrorBanner({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="mb-4 flex flex-col gap-3 rounded-2xl border border-red-100 bg-red-50/70 px-4 py-3 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between">
      <span className="font-medium">{message}</span>
      <button
        type="button"
        onClick={onRetry}
        className="inline-flex h-9 shrink-0 items-center justify-center rounded-xl border border-red-200 bg-white px-3 text-xs font-semibold text-red-700 transition hover:bg-red-50"
      >
        Retry
      </button>
    </div>
  );
}

export function DashboardPageContent() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const data = await getDashboard();

        if (cancelled) {
          return;
        }

        setDashboard(data);
      } catch (err) {
        if (cancelled) {
          return;
        }

        setError(getApiErrorMessage(err, "Failed to load your dashboard."));
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [requestVersion]);

  const retry = () => {
    setIsLoading(true);
    setError(null);
    setRequestVersion((version) => version + 1);
  };

  const viewModel = useMemo(
    () => (dashboard ? buildDashboardViewModel(dashboard) : null),
    [dashboard],
  );

  return (
    <div className="min-w-0 bg-slate-50">
      <DashboardMobileNav activeItem="overview" />

      {!viewModel && isLoading ? (
        <DashboardLoadingState />
      ) : !viewModel && error ? (
        <>
          <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8">
            <DashboardTopHeader
              displayName="there"
              isRefreshing={isLoading}
              onRefresh={retry}
              platformSummary="Dashboard data is not available yet."
            />
          </section>
          <div className="p-5 sm:p-6 lg:p-8">
            <DashboardErrorState message={error} onRetry={retry} />
          </div>
        </>
      ) : viewModel ? (
        <>
          <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8">
            <DashboardTopHeader
              displayName={viewModel.displayName}
              isRefreshing={isLoading}
              onRefresh={retry}
              platformSummary={viewModel.platformSummary}
            />
          </section>

          <div className="grid min-w-0 grid-cols-1 gap-6 p-5 sm:p-6 lg:p-8 xl:grid-cols-[minmax(0,1fr)_340px]">
            <section className="min-w-0">
              {error ? <RefreshErrorBanner message={error} onRetry={retry} /> : null}

              <MetricCardsSection metrics={viewModel.metrics} />

              <TechnicalJourneySection items={viewModel.journeyItems} />

              <div className="mt-6">
                <ConnectedPlatformsSection
                  platforms={viewModel.connectedPlatforms}
                />
              </div>

              <RecentAchievementsSection />
            </section>

            <aside className="hidden min-w-0 border-t border-slate-200 pt-6 xl:block xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
              <RightWidgetsPanel
                nextSteps={viewModel.nextSteps}
                profileChecklist={viewModel.profileChecklist}
                profileProgress={viewModel.profileProgress}
              />
            </aside>
          </div>
        </>
      ) : null}
    </div>
  );
}
