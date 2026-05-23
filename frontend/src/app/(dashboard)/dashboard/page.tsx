import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";

type PlaceholderPanelProps = {
  title: string;
  description: string;
  className?: string;
};

function PlaceholderPanel({
  title,
  description,
  className = "",
}: PlaceholderPanelProps) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}
    >
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-3 text-base font-semibold text-slate-900">
        {description}
      </p>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto grid min-h-screen w-full grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)] xl:grid-cols-[300px_minmax(0,1fr)_340px]">
        <aside className="border-b border-slate-200 bg-white p-5 sm:p-6 lg:border-b-0 lg:border-r">
          <DashboardSidebar />
        </aside>

        <section className="min-w-0 p-5 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-6xl">
            <p className="text-sm font-medium text-slate-500">STALKER</p>
            <h1 className="mt-2 text-2xl font-semibold tracking-normal text-slate-950 sm:text-3xl">
              Overview Dashboard
            </h1>

            <PlaceholderPanel
              title="Main Content"
              description="Main dashboard content will be built section by section."
              className="mt-6 min-h-72"
            />
          </div>
        </section>

        <aside className="border-t border-slate-200 bg-white/70 p-5 sm:p-6 lg:col-start-2 lg:border-l xl:col-start-auto xl:border-t-0">
          <PlaceholderPanel
            title="Right Widgets"
            description="Profile, streak, and next-step widgets will live here."
            className="min-h-48 xl:min-h-[calc(100vh-3rem)]"
          />
        </aside>
      </div>
    </main>
  );
}
