import Image from "next/image";
import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-10 text-slate-900">
      <div className="w-full max-w-md">
        <div className="mb-6 flex justify-center">
          <Image
            src="/images/stalker_main_logo_lockup_transparent_generated.png"
            alt="STALKER - Tech Progress. Tracked."
            width={224}
            height={85}
            priority
            className="h-auto w-48 max-w-full object-contain"
          />
        </div>
        {children}
      </div>
    </main>
  );
}
