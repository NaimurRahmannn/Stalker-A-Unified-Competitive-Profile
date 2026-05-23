import Image from "next/image";
import {
  Activity,
  Award,
  BarChart3,
  CalendarDays,
  ChevronDown,
  ChevronRight,
  Code2,
  Globe2,
  LayoutGrid,
  Link2,
  Settings,
  ShieldCheck,
  Target,
  Trophy,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

type Accent = "green" | "blue" | "purple" | "orange" | "slate";

type SidebarItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  accent: Accent;
  active?: boolean;
  chevron?: boolean;
};

const accentStyles: Record<Accent, { icon: string; iconBg: string }> = {
  green: {
    icon: "text-emerald-600",
    iconBg: "bg-emerald-50",
  },
  blue: {
    icon: "text-blue-600",
    iconBg: "bg-blue-50",
  },
  purple: {
    icon: "text-violet-600",
    iconBg: "bg-violet-50",
  },
  orange: {
    icon: "text-orange-600",
    iconBg: "bg-orange-50",
  },
  slate: {
    icon: "text-slate-500",
    iconBg: "bg-transparent",
  },
};

const domainItems: SidebarItem[] = [
  {
    label: "Competitive Programming",
    href: "#",
    icon: Code2,
    accent: "green",
    chevron: true,
  },
  {
    label: "CTF / Cybersecurity",
    href: "#",
    icon: ShieldCheck,
    accent: "blue",
    chevron: true,
  },
  {
    label: "Hackathon",
    href: "#",
    icon: Trophy,
    accent: "purple",
    chevron: true,
  },
  {
    label: "Datathon / Data Science",
    href: "#",
    icon: BarChart3,
    accent: "orange",
    chevron: true,
  },
];

const platformItems: SidebarItem[] = [
  { label: "Platforms", href: "#", icon: Link2, accent: "slate" },
  { label: "Achievements", href: "#", icon: Award, accent: "slate" },
  { label: "Activity", href: "#", icon: Activity, accent: "slate" },
  { label: "Goals", href: "#", icon: Target, accent: "slate" },
  { label: "Contests", href: "#", icon: CalendarDays, accent: "slate" },
  { label: "Public Profile", href: "#", icon: Globe2, accent: "slate" },
  { label: "Settings", href: "#", icon: Settings, accent: "slate" },
];

function SidebarLink({ item }: { item: SidebarItem }) {
  const Icon = item.icon;
  const accent = accentStyles[item.accent];

  return (
    <a
      href={item.href}
      className={`group flex min-h-12 items-center gap-3 rounded-xl border-l-[3px] px-3 py-2 text-sm font-medium transition ${
        item.active
          ? "border-emerald-500 bg-emerald-50/70 text-slate-950 shadow-[0_10px_24px_rgba(15,23,42,0.03)]"
          : "border-transparent text-slate-700 hover:bg-slate-50 hover:text-slate-950"
      }`}
    >
      <span
        className={`grid size-8 shrink-0 place-items-center rounded-lg ${
          item.active ? "bg-white text-emerald-600" : accent.iconBg
        } ${item.active ? "" : accent.icon}`}
      >
        <Icon className="size-4" />
      </span>
      <span className="min-w-0 flex-1 truncate">{item.label}</span>
      {item.chevron ? (
        <ChevronRight className="size-4 shrink-0 text-slate-400 transition group-hover:translate-x-0.5" />
      ) : null}
    </a>
  );
}

function SidebarSection({
  title,
  items,
}: {
  title: string;
  items: SidebarItem[];
}) {
  return (
    <div>
      <p className="px-3 text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
        {title}
      </p>
      <div className="mt-3 grid gap-2">
        {items.map((item) => (
          <SidebarLink key={item.label} item={item} />
        ))}
      </div>
    </div>
  );
}

export function DashboardSidebar() {
  return (
    <div className="flex h-full min-h-0 flex-col lg:min-h-[calc(100vh-3rem)]">
      <div className="px-1 pb-8 pt-2">
        <Image
          src="/images/stalker_main_logo_lockup_transparent_generated.png"
          alt="STALKER - Tech Progress. Tracked."
          width={224}
          height={85}
          priority
          className="h-auto w-55 max-w-full object-contain"
        />
      </div>

      <nav className="grid gap-6" aria-label="Dashboard navigation">
        <div>
          <SidebarLink
            item={{
              label: "Overview",
              href: "/dashboard",
              icon: LayoutGrid,
              accent: "green",
              active: true,
            }}
          />
        </div>

        <SidebarSection title="Domains" items={domainItems} />
        <SidebarSection title="Platform" items={platformItems} />
      </nav>

      <div className="mt-auto rounded-2xl border border-slate-200 bg-white p-3 shadow-[0_12px_30px_rgba(15,23,42,0.04)]">
        <div className="flex items-center gap-3">
          <div className="grid size-12 shrink-0 place-items-center rounded-full bg-emerald-50 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-100">
            NR
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-950">
              Naimur Rahman
            </p>
            <p className="mt-0.5 truncate text-xs text-slate-500">@naimur</p>
          </div>
          <ChevronDown className="size-4 shrink-0 text-slate-400" />
        </div>
      </div>
    </div>
  );
}
