"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { loginUser } from "@/features/auth/api";
import { loginSchema, type LoginFormValues } from "@/features/auth/schemas";
import { getApiErrorMessage } from "@/lib/errors";

const inputClassName =
  "mt-2 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 outline-none transition focus:border-zinc-950 focus:ring-2 focus:ring-zinc-950/10";
const labelClassName = "block text-sm font-medium text-zinc-800";
const errorClassName = "mt-1 text-sm text-red-600";

export default function LoginPage() {
  const router = useRouter();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  async function onSubmit(values: LoginFormValues) {
    setSubmitError(null);

    try {
      await loginUser(values);
      router.push("/dashboard");
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 px-4 py-12 text-zinc-950">
      <section className="w-full max-w-md rounded-lg border border-zinc-200 bg-white p-8 shadow-sm">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-normal">
            Sign in to STALKER
          </h1>
          <p className="mt-2 text-sm leading-6 text-zinc-600">
            Continue tracking your progress across your connected platforms.
          </p>
        </div>

        {submitError ? (
          <div className="mb-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {submitError}
          </div>
        ) : null}

        <form className="space-y-5" noValidate onSubmit={handleSubmit(onSubmit)}>
          <div>
            <label className={labelClassName} htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              aria-invalid={Boolean(errors.username)}
              aria-describedby={errors.username ? "login-username-error" : undefined}
              className={inputClassName}
              {...register("username")}
            />
            {errors.username?.message ? (
              <p className={errorClassName} id="login-username-error">
                {errors.username.message}
              </p>
            ) : null}
          </div>

          <div>
            <label className={labelClassName} htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              aria-invalid={Boolean(errors.password)}
              aria-describedby={errors.password ? "login-password-error" : undefined}
              className={inputClassName}
              {...register("password")}
            />
            {errors.password?.message ? (
              <p className={errorClassName} id="login-password-error">
                {errors.password.message}
              </p>
            ) : null}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center rounded-md bg-zinc-950 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-zinc-600">
          Do not have an account?{" "}
          <Link
            className="font-medium text-zinc-950 hover:underline"
            href="/register"
          >
            Create one
          </Link>
        </p>
      </section>
    </main>
  );
}
