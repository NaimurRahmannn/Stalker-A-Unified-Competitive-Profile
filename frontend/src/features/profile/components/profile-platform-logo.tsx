import Image from "next/image";
import { Braces, Shield } from "lucide-react";
import { platformLogoSrc } from "@/features/dashboard/data";
import type { PlatformMark } from "@/features/dashboard/types";

const fallbackLabels: Record<string, string> = { ctftime: "CTF", tryhackme: "THM", hackthebox: "HTB", devpost: "D", dorahacks: "DH" };

export function ProfilePlatformLogo({ mark, slug, name, size = "md" }: { mark: PlatformMark | null; slug?: string; name: string; size?: "sm" | "md" | "lg" }) {
  const dimensions = size === "lg" ? 36 : size === "sm" ? 24 : 30;
  const boxClass = size === "lg" ? "size-11" : size === "sm" ? "size-8" : "size-9";
  if (mark) {
    return <span className={`grid ${boxClass} shrink-0 place-items-center rounded-lg bg-white`}><Image src={platformLogoSrc[mark]} alt={`${name} logo`} width={dimensions} height={dimensions} className="max-h-full max-w-full object-contain" /></span>;
  }
  const label = slug ? fallbackLabels[slug] : null;
  return <span aria-hidden="true" className={`grid ${boxClass} shrink-0 place-items-center rounded-lg bg-slate-100 text-[9px] font-bold text-slate-600`}>{label ?? (slug?.includes("hack") ? <Shield className="size-4" /> : <Braces className="size-4" />)}</span>;
}
