import {
  Bell,
} from "lucide-react";
import type { ReactNode } from "react";
import { PublicProfileActions } from "./public-profile-actions";

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
  platformSummary,
  username,
}: {
  displayName: string;
  platformSummary: string;
  username?: string;
}) {
  return (
    <header className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
      <div className="min-w-0">
        <h1 className="text-[25px] font-semibold leading-tight tracking-normal text-slate-950 sm:text-[28px]">
          Good morning, {displayName}{" "}
          <span aria-hidden="true">{"\uD83D\uDC4B"}</span>
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600 sm:text-base">
          {platformSummary}
        </p>
      </div>

      <div className="flex w-full min-w-0 flex-wrap items-center gap-3 xl:w-auto xl:justify-end">
        {username ? <PublicProfileActions username={username} /> : null}

        <div className="hidden items-center gap-2 lg:flex">
          <HeaderIconButton label="Notifications">
            <Bell className="size-5" />
          </HeaderIconButton>
        </div>
      </div>
    </header>
  );
}
