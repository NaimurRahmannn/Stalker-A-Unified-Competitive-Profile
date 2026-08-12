import Image from "next/image";
import { CodeXml, MessageCircle, Send } from "lucide-react";

const columns = [
  { title: "Product", links: ["Features", "Leaderboards", "Compare", "Blog"] },
  { title: "Platform", links: ["Supported Platforms", "API", "Status", "Roadmap"] },
  { title: "Legal", links: ["Privacy Policy", "Terms of Service", "Contact"] },
];

export function PublicProfileFooter() {
  return <footer className="mt-4 border-t border-slate-200 bg-white"><div className="mx-auto grid max-w-310 gap-10 px-5 py-8 sm:px-8 md:grid-cols-[1.3fr_2fr] lg:grid-cols-[1.2fr_2fr_auto]">
    <div><Image src="/images/stalker_main_logo_lockup_transparent_generated.png" alt="STALKER" width={130} height={49} className="h-9 w-auto object-contain" /><p className="mt-3 max-w-54 text-[10px] leading-5 text-slate-500">A unified platform for developers and problem solvers to track progress and grow together.</p><div className="mt-3 flex gap-3 text-slate-500"><CodeXml className="size-4" /><MessageCircle className="size-4" /><Send className="size-4" /></div></div>
    <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">{columns.map((column) => <div key={column.title}><h2 className="text-[10px] font-semibold text-slate-900">{column.title}</h2><ul className="mt-3 space-y-2">{column.links.map((link) => <li key={link} className="text-[9px] text-slate-500">{link}</li>)}</ul></div>)}</div>
    <p className="self-end whitespace-nowrap text-[9px] text-slate-500">© {new Date().getFullYear()} Stalker. All rights reserved.</p>
  </div></footer>;
}
