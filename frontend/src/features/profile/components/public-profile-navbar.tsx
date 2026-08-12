"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Menu, Search, X } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

const navigation = ["Explore", "Leaderboards", "Compare", "Blog"];

export function PublicProfileNavbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, isLoading } = useAuth();
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-18 max-w-310 items-center justify-between gap-6 px-5 sm:px-8">
        <Link href="/" aria-label="STALKER home" className="shrink-0"><Image src="/images/stalker_main_logo_lockup_transparent_generated.png" alt="STALKER" width={148} height={56} className="h-10 w-auto object-contain" preload /></Link>
        <nav aria-label="Primary navigation" className="hidden items-center gap-11 lg:flex">{navigation.map((item) => <span key={item} className="cursor-default text-[13px] font-semibold text-slate-900">{item}</span>)}</nav>
        <div className="ml-auto hidden items-center gap-4 sm:flex">
          <label className="flex h-10 w-64 items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 shadow-sm focus-within:border-emerald-300"><Search className="size-4 text-slate-400" /><span className="sr-only">Search users and platforms</span><input type="search" placeholder="Search users, platforms..." className="min-w-0 flex-1 bg-transparent text-xs text-slate-800 outline-none placeholder:text-slate-400" /></label>
          {!isLoading && user ? <Link href="/dashboard" className="inline-flex h-10 items-center rounded-lg border border-slate-200 px-5 text-xs font-semibold text-slate-900 shadow-sm hover:bg-slate-50">Dashboard</Link> : <Link href="/login" className="inline-flex h-10 items-center rounded-lg border border-slate-200 px-5 text-xs font-semibold text-slate-900 shadow-sm hover:bg-slate-50">Sign in</Link>}
        </div>
        <button type="button" aria-label={menuOpen ? "Close navigation" : "Open navigation"} aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)} className="grid size-10 place-items-center rounded-lg border border-slate-200 text-slate-700 sm:hidden">{menuOpen ? <X className="size-5" /> : <Menu className="size-5" />}</button>
      </div>
      {menuOpen ? <nav aria-label="Mobile navigation" className="border-t border-slate-100 bg-white px-5 py-4 sm:hidden"><div className="mx-auto grid max-w-310 gap-1">{navigation.map((item) => <span key={item} className="rounded-lg px-3 py-2 text-sm font-medium text-slate-700">{item}</span>)}<Link href={user ? "/dashboard" : "/login"} className="mt-2 rounded-lg bg-emerald-600 px-3 py-2.5 text-center text-sm font-semibold text-white">{user ? "Dashboard" : "Sign in"}</Link></div></nav> : null}
    </header>
  );
}
