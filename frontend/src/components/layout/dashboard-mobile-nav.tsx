"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Bell, Menu, Sun, X } from "lucide-react";
import {
  DashboardSidebar,
  type DashboardSidebarActiveItem,
} from "./dashboard-sidebar";

function MobileIconButton({
  label,
  onClick,
  children,
}: {
  label: string;
  onClick?: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      className="relative grid size-10 shrink-0 place-items-center rounded-xl text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
    >
      {children}
    </button>
  );
}

export function DashboardMobileNav({
  activeItem = "overview",
}: {
  activeItem?: DashboardSidebarActiveItem;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <div className="lg:hidden">
      <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur supports-backdrop-filter:bg-white/80 sm:px-6">
        <div className="flex items-center gap-2">
          <MobileIconButton label="Open menu" onClick={() => setOpen(true)}>
            <Menu className="size-5" />
          </MobileIconButton>
          <Image
            src="/images/stalker_main_logo_lockup_transparent_generated.png"
            alt="STALKER - Tech Progress. Tracked."
            width={140}
            height={53}
            priority
            className="h-8 w-auto max-w-full object-contain"
          />
        </div>

        <div className="flex items-center gap-1">
          <MobileIconButton label="Notifications">
            <Bell className="size-5" />
            <span className="absolute right-1 top-0.5 grid size-4 place-items-center rounded-full bg-red-500 text-[10px] font-semibold leading-none text-white ring-2 ring-white">
              3
            </span>
          </MobileIconButton>
          <MobileIconButton label="Theme">
            <Sun className="size-5" />
          </MobileIconButton>
        </div>
      </header>

      {open ? (
        <div className="fixed inset-0 z-50" role="dialog" aria-modal="true">
          <button
            type="button"
            aria-label="Close menu"
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-slate-950/40 backdrop-blur-sm"
          />

          <div className="absolute inset-y-0 left-0 flex w-75 max-w-[85vw] flex-col overflow-y-auto border-r border-slate-200 bg-white p-5 shadow-2xl sm:p-6">
            <button
              type="button"
              aria-label="Close menu"
              onClick={() => setOpen(false)}
              className="absolute right-4 top-4 grid size-9 place-items-center rounded-xl text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
            >
              <X className="size-5" />
            </button>

            <div onClick={() => setOpen(false)}>
              <DashboardSidebar activeItem={activeItem} />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
