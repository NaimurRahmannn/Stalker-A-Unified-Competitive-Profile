import {
  Bell,
  RefreshCw,
  Search,
  Sun,
} from "lucide-react";
import type { ReactNode } from "react";

function HeaderIconButton({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className="relative grid size-11 shrink-0 place-items-center rounded-xl text-slate-500 transition hover:bg-white hover:text-slate-900"
    >
      {children}
    </button>
  );
}

export function DashboardTopHeader({
  displayName,
  isRefreshing,
  onRefresh,
  platformSummary,
}: {
  displayName: string;
  isRefreshing: boolean;
  onRefresh: () => void;
  platformSummary: string;
}) {
  return (
    <header className="flex flex-col gap-5 min-[1180px]:flex-row min-[1180px]:items-start min-[1180px]:justify-between">
      <div className="min-w-0">
        <h1 className="text-[25px] font-semibold leading-tight tracking-normal text-slate-950 sm:text-[28px]">
          Good morning, {displayName}{" "}
          <span aria-hidden="true">{"\uD83D\uDC4B"}</span>
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600 sm:text-base">
          {platformSummary}
        </p>
      </div>

      <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center min-[1180px]:w-auto">
        <label className="relative block w-full sm:min-w-80 min-[1180px]:w-101.25">
          <span className="sr-only">Search anything</span>
          <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            placeholder="Search anything..."
            className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-16 text-[13px] text-slate-800 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-emerald-300 focus:ring-4 focus:ring-emerald-100"
          />
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium leading-none text-slate-500">
            {"\u2318"} K
          </span>
        </label>

        <button
          type="button"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-[13px] font-semibold text-slate-900 shadow-sm transition hover:bg-slate-50"
        >
          <RefreshCw
            className={`size-4 text-blue-600 ${
              isRefreshing ? "animate-spin" : ""
            }`}
          />
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </button>

        <div className="hidden items-center gap-2 lg:flex">
          <HeaderIconButton label="Notifications">
            <Bell className="size-5" />
          </HeaderIconButton>
          <HeaderIconButton label="Theme">
            <Sun className="size-5" />
          </HeaderIconButton>
        </div>
      </div>
    </header>
  );
}
