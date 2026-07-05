import type { PlatformMark } from "./types";

const platformMarks: PlatformMark[] = [
  "atcoder",
  "codechef",
  "codeforces",
  "github",
  "kaggle",
  "leetcode",
];

const platformDisplayNames: Record<PlatformMark, string> = {
  atcoder: "AtCoder",
  codechef: "CodeChef",
  codeforces: "Codeforces",
  github: "GitHub",
  kaggle: "Kaggle",
  leetcode: "LeetCode",
};

export const platformLogoSrc: Record<PlatformMark, string> = {
  atcoder: "/images/atcoder_logo.png",
  codechef: "/images/codechef_logo.png",
  codeforces: "/images/codeforces_logo.png",
  github: "/images/github_logo.png",
  kaggle: "/images/kaggle_logo.png",
  leetcode: "/images/leetcode_logo.png",
};

export function getPlatformMark(platform: string): PlatformMark | null {
  const normalized = platform.toLowerCase();

  if (platformMarks.includes(normalized as PlatformMark)) {
    return normalized as PlatformMark;
  }

  return null;
}

export function formatDashboardPlatformName(platform: string): string {
  const mark = getPlatformMark(platform);

  if (mark) {
    return platformDisplayNames[mark];
  }

  return platform
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
