"use client";

import { useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { ExternalLink, Link2, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import type { PlatformAccount } from "@/features/platforms/types";
import { connectPlatformSchema, type ConnectPlatformFormValues } from "@/features/platforms/schemas";
import { formatTimestamp } from "../formatters";

export function KaggleAccountPanel({ account, lastSuccessfulAt, busy, onConnect, onChange, onDisconnect }: {
  account: PlatformAccount | null;
  lastSuccessfulAt: string | null;
  busy: boolean;
  onConnect: (handle: string) => Promise<void>;
  onChange: (handle: string) => Promise<void>;
  onDisconnect: () => Promise<void>;
}) {
  const form = useForm<ConnectPlatformFormValues>({ resolver: zodResolver(connectPlatformSchema), defaultValues: { platform: "kaggle", handle: "" } });
  const { reset } = form;
  useEffect(() => { reset({ platform: "kaggle", handle: "" }); }, [account?.id, account?.handle, reset]);
  const submit = form.handleSubmit(async ({ handle }) => {
    if (busy) return;
    try {
      if (account) await onChange(handle);
      else await onConnect(handle);
      reset({ platform: "kaggle", handle: "" });
    } catch { /* Parent presents the API error and keeps the input. */ }
  });
  return <section className="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="kaggle-account-heading">
    <div className="flex items-center gap-3"><span className="grid size-11 shrink-0 place-items-center rounded-xl border border-slate-100 bg-white"><Image src="/images/kaggle_logo.png" alt="" width={30} height={30} /></span><div><h2 id="kaggle-account-heading" className="text-lg font-semibold text-slate-950">Kaggle account</h2><p className="text-sm text-slate-500">Your linked public profile</p></div></div>
    {account ? <div className="mt-5 space-y-2 text-sm"><p className="break-all font-semibold text-slate-950">@{account.handle}</p><a className="inline-flex max-w-full items-center gap-1 break-all text-orange-700 underline-offset-2 hover:underline focus-visible:rounded focus-visible:outline-2 focus-visible:outline-orange-500" href={account.profile_url} target="_blank" rel="noopener noreferrer" aria-label={`Open Kaggle profile for ${account.handle}`}><span className="min-w-0 break-all">{account.profile_url}</span><ExternalLink className="size-4 shrink-0" /></a><p className="text-slate-600">Status: Linked public username · Ownership not verified</p><p className="text-slate-600">Last successful collection: {formatTimestamp(lastSuccessfulAt)}</p></div> : <div className="mt-5"><p className="text-sm text-slate-600">Connect your Kaggle username to organize your data science profile in STALKER.</p><p className="mt-2 text-xs text-slate-500">Linking a username does not verify account ownership or automatically retrieve rankings.</p></div>}
    <form className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-start" onSubmit={(event) => void submit(event)} noValidate><input type="hidden" {...form.register("platform")} value="kaggle" /><div className="min-w-0 flex-1"><label htmlFor="kaggle-handle" className="mb-1 block text-xs font-medium text-slate-600">{account ? "New Kaggle username or profile URL" : "Kaggle username or profile URL"}</label><input id="kaggle-handle" autoComplete="off" aria-invalid={!!form.formState.errors.handle} aria-describedby={form.formState.errors.handle ? "kaggle-handle-error" : undefined} placeholder="example_user" className="h-10 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none focus-visible:border-orange-500 focus-visible:ring-2 focus-visible:ring-orange-200" {...form.register("handle")} />{form.formState.errors.handle && <p id="kaggle-handle-error" role="alert" className="mt-1 text-xs text-red-700">{form.formState.errors.handle.message}</p>}</div><button type="submit" disabled={busy || form.formState.isSubmitting} className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-xl bg-orange-600 px-4 text-sm font-semibold text-white hover:bg-orange-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-600 disabled:cursor-not-allowed disabled:opacity-50 sm:mt-5">{busy || form.formState.isSubmitting ? <Loader2 className="size-4 animate-spin" /> : <Link2 className="size-4" />}{account ? "Change account" : "Connect Kaggle"}</button></form>
    {account ? <button type="button" onClick={() => void onDisconnect().catch(() => {})} disabled={busy} className="mt-4 text-xs font-semibold text-red-700 underline-offset-2 hover:underline focus-visible:rounded focus-visible:outline-2 focus-visible:outline-red-600 disabled:opacity-50">Disconnect Kaggle account</button> : <p className="mt-4 text-xs text-slate-500">You can also manage this link on the <Link href="/platforms" className="font-semibold text-orange-700 underline-offset-2 hover:underline">Platforms page</Link>.</p>}
  </section>;
}
