"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Loader2, Plus } from "lucide-react";
import {
  connectPlatformSchema,
  type ConnectPlatformFormValues,
} from "@/features/platforms/schemas";

type ConnectPlatformFormProps = {
  /** Returns true when the account was connected, so the form can reset. */
  onConnect: (values: ConnectPlatformFormValues) => Promise<boolean>;
};

export function ConnectPlatformForm({ onConnect }: ConnectPlatformFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ConnectPlatformFormValues>({
    resolver: zodResolver(connectPlatformSchema),
    defaultValues: { handle: "" },
  });

  const submit = handleSubmit(async (values) => {
    const connected = await onConnect(values);

    if (connected) {
      reset();
    }
  });

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <h2 className="text-sm font-semibold text-slate-950">
        Connect a platform
      </h2>
      <p className="mt-1 text-xs font-medium text-slate-500">
        Add a Codeforces handle, then sync to pull in real stats.
      </p>

      <form
        onSubmit={submit}
        className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-start"
        noValidate
      >
        <div className="w-full sm:w-44">
          <label
            htmlFor="platform"
            className="mb-1 block text-xs font-semibold text-slate-600"
          >
            Platform
          </label>
          <select
            id="platform"
            disabled
            defaultValue="codeforces"
            aria-label="Platform"
            className="h-11 w-full cursor-not-allowed rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm font-medium text-slate-700 outline-none"
          >
            <option value="codeforces">Codeforces</option>
          </select>
        </div>

        <div className="min-w-0 flex-1">
          <label
            htmlFor="handle"
            className="mb-1 block text-xs font-semibold text-slate-600"
          >
            Handle
          </label>
          <input
            id="handle"
            type="text"
            autoComplete="off"
            spellCheck={false}
            placeholder="e.g. tourist"
            aria-invalid={errors.handle ? "true" : "false"}
            className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-800 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-blue-300 focus:ring-4 focus:ring-blue-100"
            {...register("handle")}
          />
          {errors.handle ? (
            <p className="mt-1 text-xs font-medium text-red-600">
              {errors.handle.message}
            </p>
          ) : null}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60 sm:mt-6"
        >
          {isSubmitting ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Plus className="size-4" />
          )}
          {isSubmitting ? "Connecting..." : "Connect"}
        </button>
      </form>
    </section>
  );
}
