"use client";

import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";

export function PublicProfileNavbar() {
  const { user, isLoading } = useAuth();
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-17 max-w-310 items-center justify-between gap-4 px-5 sm:px-8">
        <Link href="/" aria-label="STALKER home" className="shrink-0"><Image src="/images/stalker_main_logo_lockup_transparent_generated.png" alt="STALKER" width={148} height={56} className="h-9 w-auto object-contain" preload /></Link>
        <nav aria-label="Profile navigation" className="flex items-center gap-5 text-sm font-medium text-slate-600 sm:gap-7">
          <Link href="/" className="transition hover:text-[#1769b0]">Explore</Link>
          {!isLoading ? <Link href={user ? "/dashboard" : "/login"} className="rounded-lg border border-slate-300 px-3.5 py-2 font-semibold text-[#102c46] transition hover:border-[#1769b0] hover:text-[#1769b0]">{user ? "Dashboard" : "Sign in"}</Link> : null}
        </nav>
      </div>
    </header>
  );
}
