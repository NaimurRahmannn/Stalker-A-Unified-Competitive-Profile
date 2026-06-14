import { DashboardMobileNav } from "@/components/layout/dashboard-mobile-nav";
import { ConnectedPlatformsSection } from "./connected-platforms-section";
import { DashboardTopHeader } from "./dashboard-top-header";
import { MetricCardsSection } from "./metric-cards-section";
import { RecentAchievementsSection } from "./recent-achievements-section";
import { RightWidgetsPanel } from "./right-widgets-panel";
import { TechnicalJourneySection } from "./technical-journey-section";

export function DashboardPageContent() {
  return (
    <div className="min-w-0 bg-slate-50">
      <DashboardMobileNav activeItem="overview" />

      <section className="px-5 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8">
        <DashboardTopHeader />
      </section>

      <div className="grid min-w-0 grid-cols-1 gap-6 p-5 sm:p-6 lg:p-8 xl:grid-cols-[minmax(0,1fr)_340px]">
        <section className="min-w-0">
          <MetricCardsSection />

          <TechnicalJourneySection />

          <div className="mt-6">
            <ConnectedPlatformsSection />
          </div>

          <RecentAchievementsSection />
        </section>

        <aside className="hidden min-w-0 border-t border-slate-200 pt-6 xl:block xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
          <RightWidgetsPanel />
        </aside>
      </div>
    </div>
  );
}
