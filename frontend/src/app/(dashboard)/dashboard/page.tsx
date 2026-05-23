import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { DashboardPageContent } from "@/features/dashboard/components/dashboard-page-content";

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-white p-5 sm:p-6 lg:border-b-0 lg:border-r">
          <DashboardSidebar />
        </aside>

        <DashboardPageContent />
      </div>
    </main>
  );
}
