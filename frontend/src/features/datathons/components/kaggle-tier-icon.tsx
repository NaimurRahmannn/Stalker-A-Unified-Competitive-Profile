import type { SVGProps } from "react";

export const KAGGLE_TIERS = ["Novice", "Contributor", "Expert", "Master", "Grandmaster"] as const;
type KaggleTier = (typeof KAGGLE_TIERS)[number];

const tierColors: Record<KaggleTier, string> = {
  Novice: "#48c98f",
  Contributor: "#00b3ec",
  Expert: "#954c91",
  Master: "#ff642c",
  Grandmaster: "#e5b600",
};

const tierNodes: Record<KaggleTier, [number, number][]> = {
  Novice: [[24, 6], [7, 39], [41, 39]],
  Contributor: [[24, 5], [5, 24], [24, 43], [43, 24]],
  Expert: [[24, 5], [43, 19], [36, 42], [12, 42], [5, 19]],
  Master: [[24, 4], [41, 14], [41, 34], [24, 44], [7, 34], [7, 14]],
  Grandmaster: [[24, 4], [40, 12], [44, 28], [34, 43], [15, 43], [4, 28], [8, 12]],
};

export function KaggleTierIcon({ tier, ...props }: { tier: string | null } & SVGProps<SVGSVGElement>) {
  const name = KAGGLE_TIERS.find((candidate) => candidate.toLowerCase() === tier?.toLowerCase());
  if (!name) return null;

  const nodes = tierNodes[name];
  const center = name === "Master" || name === "Grandmaster";
  return <svg viewBox="0 0 48 48" fill="none" color={tierColors[name]} aria-hidden="true" {...props}>
    <polygon points={nodes.map(([x, y]) => `${x},${y}`).join(" ")} stroke="currentColor" strokeWidth="3.2" strokeLinejoin="round" />
    {name === "Grandmaster" && nodes.map(([x, y], index) => <line key={index} x1="24" y1="25" x2={x} y2={y} stroke="currentColor" strokeWidth="2.5" />)}
    {nodes.map(([x, y], index) => <circle key={index} cx={x} cy={y} r="4.4" fill="white" stroke="currentColor" strokeWidth="3.2" />)}
    {center && <circle cx="24" cy={name === "Master" ? "24" : "25"} r="4.4" fill="white" stroke="currentColor" strokeWidth="3.2" />}
  </svg>;
}
