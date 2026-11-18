"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { Menu, X } from "lucide-react";
import {
  DashboardSidebar,
  type DashboardSidebarActiveItem,
} from "./dashboard-sidebar";

export function DashboardMobileNav({
  activeItem = "overview",
}: {
  activeItem?: DashboardSidebarActiveItem;
}) {
  const [open, setOpen] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const openerRef = useRef<HTMLButtonElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = Array.from(dialogRef.current.querySelectorAll<HTMLElement>("a[href]:not([tabindex='-1']), button:not([disabled]):not([tabindex='-1']), [tabindex]:not([tabindex='-1'])"));
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };

    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    const opener = openerRef.current;

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
      opener?.focus();
    };
  }, [open]);

  return (
    <div className="lg:hidden">
      <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur supports-backdrop-filter:bg-white/80 sm:px-6">
        <div className="flex items-center gap-2">
          <button ref={openerRef} type="button" aria-label="Open menu" aria-expanded={open} onClick={() => setOpen(true)} className="grid size-10 shrink-0 place-items-center rounded-lg text-slate-500 hover:bg-surface-muted hover:text-foreground"><Menu className="size-5" /></button>
          <Image
            src="/images/stalker_main_logo_lockup_transparent_generated.png"
            alt="STALKER - Tech Progress. Tracked."
            width={140}
            height={53}
            priority
            className="h-8 w-auto max-w-full object-contain"
          />
        </div>

      </header>

      {open ? (
        <div ref={dialogRef} className="fixed inset-0 z-50" role="dialog" aria-label="Navigation menu" aria-modal="true">
          <button
            type="button"
            aria-label="Close menu"
            tabIndex={-1}
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-slate-950/40 backdrop-blur-sm"
          />

          <div className="absolute inset-y-0 left-0 flex w-75 max-w-[85vw] flex-col overflow-y-auto border-r border-slate-200 bg-white p-5 shadow-lg sm:p-6">
            <button
              ref={closeRef}
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
