import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { Code2 } from "lucide-react";
import type { ReactNode } from "react";

function PlaceholderCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <h2 className="text-sm font-semibold text-slate-950">{title}</h2>
      <div className="mt-3 text-sm leading-6 text-slate-600">{children}</div>
    </section>
  );
}

export default function CompetitiveProgrammingPage() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-white p-5 sm:p-6 lg:border-b-0 lg:border-r">
          <DashboardSidebar activeItem="competitive-programming" />
        </aside>

        <div className="min-w-0 bg-slate-50">
          <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8">
            <div className="flex min-w-0 flex-col gap-2">
              <div className="flex min-w-0 items-center gap-3">
                <h1 className="truncate text-[25px] font-semibold leading-tight tracking-normal text-slate-950 sm:text-[28px]">
                  Competitive Programming
                </h1>
                <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100">
                  <Code2 className="size-5" />
                </span>
              </div>
              <p className="max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
                Track your ratings, solved problems, contests, and platform
                streaks across coding platforms.
              </p>
            </div>
          </section>

          <div className="grid min-w-0 grid-cols-1 gap-6 p-5 sm:p-6 lg:p-8 xl:grid-cols-[minmax(0,1fr)_340px]">
            <section className="min-w-0">
              <PlaceholderCard title="Main Competitive Content">
                Metric cards will be built in the next part.
              </PlaceholderCard>
            </section>

            <aside className="min-w-0 border-t border-slate-200 pt-6 xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
              <PlaceholderCard title="Competitive Widgets">
                Profile completion, next steps, and solving streak widgets will
                live here.
              </PlaceholderCard>
            </aside>
          </div>
        </div>
      </div>
    </main>
  );
}
