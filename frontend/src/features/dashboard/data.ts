import {
  Award,
  BarChart3,
  Box,
  Cloud,
  Code2,
  Link2,
  RefreshCw,
  ShieldCheck,
  Target,
  Trophy,
  Users,
} from "lucide-react";
import type {
  ChecklistItem,
  ConnectedPlatform,
  JourneyItem,
  MetricItem,
  NextStep,
  RecentAchievement,
  StreakItem,
} from "./types";

export const metricItems: MetricItem[] = [
  {
    label: "Platforms Connected",
    value: "10",
    icon: Users,
    accent: "green",
  },
  {
    label: "Verified",
    value: "6",
    icon: ShieldCheck,
    accent: "blue",
  },
  {
    label: "Last Synced",
    value: "2h ago",
    icon: RefreshCw,
    accent: "purple",
  },
  {
    label: "Profile Completion",
    value: "72%",
    icon: BarChart3,
    accent: "orange",
  },
];

export const journeyItems: JourneyItem[] = [
  {
    title: "Competitive Programming",
    value: "450",
    label: "Problems Solved",
    icon: Code2,
    accent: "green",
    stats: [
      { value: "4", label: "Platforms" },
      { value: "21", label: "Day Streak" },
    ],
    sparkline: [
      18, 22, 20, 27, 24, 33, 29, 38, 42, 36, 45, 40, 44, 54, 48, 58, 51, 57,
    ],
  },
  {
    title: "CTF / Cybersecurity",
    value: "162",
    label: "Flags Captured",
    icon: ShieldCheck,
    accent: "blue",
    stats: [
      { value: "3", label: "Platforms" },
      { value: "14", label: "Day Streak" },
    ],
    sparkline: [
      12, 13, 11, 18, 27, 22, 31, 26, 18, 21, 24, 34, 30, 44, 37, 41, 43, 51,
    ],
  },
  {
    title: "Hackathon",
    value: "12",
    label: "Hackathons Joined",
    icon: Trophy,
    accent: "purple",
    stats: [
      { value: "5", label: "Projects" },
      { value: "2", label: "Wins" },
    ],
    sparkline: [
      14, 19, 17, 26, 23, 24, 36, 28, 24, 31, 29, 37, 40, 47, 41, 51, 44, 48,
    ],
  },
  {
    title: "Datathon / Data Science",
    value: "6",
    label: "Competitions Joined",
    icon: BarChart3,
    accent: "orange",
    stats: [
      { value: "2", label: "Medals" },
      { value: "3", label: "Notebooks" },
    ],
    sparkline: [
      16, 24, 21, 31, 28, 40, 29, 25, 33, 28, 35, 42, 39, 48, 32, 44, 36, 49,
    ],
  },
];

export const connectedPlatforms: ConnectedPlatform[] = [
  {
    name: "Codeforces",
    handle: "@tourist_",
    status: "Verified",
    mark: "codeforces",
  },
  {
    name: "LeetCode",
    handle: "@naimur_rahman",
    status: "Verified",
    mark: "leetcode",
  },
  {
    name: "AtCoder",
    handle: "@naimur_rahman",
    status: "Verified",
    mark: "atcoder",
  },
  {
    name: "CodeChef",
    handle: "@naimur_rahman",
    status: "Unverified",
    mark: "codechef",
  },
  {
    name: "GitHub",
    handle: "@naimur_rahman",
    status: "Verified",
    mark: "github",
  },
  {
    name: "Kaggle",
    handle: "@naimur_rahman",
    status: "Unverified",
    mark: "kaggle",
  },
];

export const platformLogoSrc: Record<ConnectedPlatform["mark"], string> = {
  atcoder: "/images/atcoder_logo.png",
  codechef: "/images/codechef_logo.png",
  codeforces: "/images/codeforces_logo.png",
  github: "/images/github_logo.png",
  kaggle: "/images/kaggle_logo.png",
  leetcode: "/images/leetcode_logo.png",
};

export const recentAchievements: RecentAchievement[] = [
  {
    platform: "Hack The Box",
    title: "First Machine",
    time: "2 days ago",
    icon: Box,
    accent: "green",
    badge: "Completed",
  },
  {
    platform: "Codeforces",
    title: "New Rating Milestone",
    time: "3 days ago",
    icon: Code2,
    accent: "blue",
    badge: "1372",
  },
  {
    platform: "Devpost",
    title: "Project Submitted",
    time: "5 days ago",
    icon: Trophy,
    accent: "purple",
    description: "AI Study Buddy",
  },
  {
    platform: "Kaggle",
    title: "Competition Joined",
    time: "1 week ago",
    icon: BarChart3,
    accent: "orange",
    description: "Google Analytics Dashboard",
  },
];

export const profileChecklist: ChecklistItem[] = [
  { label: "Add full name", done: true },
  { label: "Add bio", done: true },
  { label: "Connect platforms", done: true },
  { label: "Verify platforms", done: true },
  { label: "Add social links", done: false },
  { label: "Add avatar", done: false },
];

export const nextSteps: NextStep[] = [
  {
    title: "Verify your Kaggle handle",
    subtitle: "Make your profile public",
    icon: Cloud,
    accent: "blue",
  },
  {
    title: "Add social links",
    subtitle: "Improve your profile credibility",
    icon: Link2,
    accent: "cyan",
  },
  {
    title: "Explore Achievements",
    subtitle: "Unlock badges and milestones",
    icon: Award,
    accent: "slate",
  },
  {
    title: "Set your goals",
    subtitle: "Track your progress better",
    icon: Target,
    accent: "blue",
  },
];

export const streakItems: StreakItem[] = [
  {
    label: "CP Streak",
    value: "21",
    icon: Code2,
    accent: "green",
  },
  {
    label: "CTF Streak",
    value: "14",
    icon: ShieldCheck,
    accent: "blue",
  },
  {
    label: "Hackathon Streak",
    value: "7",
    icon: Trophy,
    accent: "purple",
  },
  {
    label: "Datathon Streak",
    value: "9",
    icon: BarChart3,
    accent: "orange",
  },
];
