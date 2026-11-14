import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { ContestsPageContent } from "@/features/dashboard/components/contests-page-content";

export default function ContestsPage() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-x-clip lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="hidden bg-white p-5 sm:p-6 lg:sticky lg:top-0 lg:block lg:h-dvh lg:self-start lg:overflow-y-auto lg:overscroll-y-contain lg:[scrollbar-width:thin] lg:border-r lg:border-slate-200">
          <DashboardSidebar activeItem="contests" />
        </aside>
        <ContestsPageContent />
      </div>
    </main>
  );
}
