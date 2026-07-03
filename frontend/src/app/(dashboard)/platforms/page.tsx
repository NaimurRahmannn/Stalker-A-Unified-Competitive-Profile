import { Link2 } from "lucide-react";
import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { PlatformsManager } from "@/features/platforms/components/platforms-manager";

function PlatformsHeader() {
  return (
    <header className="min-w-0">
      <div className="flex min-w-0 items-center gap-3">
        <h1 className="truncate text-[25px] font-semibold leading-tight tracking-normal text-slate-950 sm:text-[28px]">
          Platforms
        </h1>
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-600 ring-1 ring-blue-100">
          <Link2 className="size-5" />
        </span>
      </div>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
        Connect your platform handles and sync real stats into your STALKER
        profile.
      </p>
    </header>
  );
}

export default function PlatformsPage() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="hidden bg-white p-5 sm:p-6 lg:block lg:border-r lg:border-slate-200">
          <DashboardSidebar activeItem="platforms" />
        </aside>

        <div className="min-w-0 bg-slate-50">
          <DashboardMobileNav activeItem="platforms" />

          <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8">
            <PlatformsHeader />
          </section>

          <div className="p-5 sm:p-6 lg:p-8">
            <div className="mx-auto max-w-3xl">
              <PlatformsManager />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
