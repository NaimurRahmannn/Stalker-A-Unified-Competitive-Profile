import Image from "next/image";
import Link from "next/link";

export function PublicProfileFooter() {
  return (
    <footer className="border-t border-slate-200 bg-[#f5f8fb]">
      <div className="mx-auto flex max-w-310 flex-col gap-5 px-5 py-8 sm:flex-row sm:items-end sm:justify-between sm:px-8">
        <div>
          <Link href="/" aria-label="STALKER home"><Image src="/images/stalker_main_logo_lockup_transparent_generated.png" alt="STALKER" width={130} height={49} className="h-9 w-auto object-contain" /></Link>
          <p className="mt-2 max-w-sm text-xs leading-5 text-slate-500">A place to share the work behind your progress.</p>
        </div>
        <p className="text-xs text-slate-500">© {new Date().getFullYear()} STALKER</p>
      </div>
    </footer>
  );
}
