"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { registerUser } from "@/features/auth/api";
import {
  registerSchema,
  type RegisterFormValues,
} from "@/features/auth/schemas";
import { getApiErrorMessage } from "@/lib/errors";

const inputClassName =
  "mt-2 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-950 outline-none transition focus:border-zinc-950 focus:ring-2 focus:ring-zinc-950/10";
const labelClassName = "block text-sm font-medium text-zinc-800";
const errorClassName = "mt-1 text-sm text-red-600";

export default function RegisterPage() {
  const router = useRouter();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: "",
      email: "",
      full_name: "",
      password: "",
      password_confirm: "",
    },
  });

  async function onSubmit(values: RegisterFormValues) {
    setSubmitError(null);

    try {
      await registerUser(values);
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
            Create your account
          </h1>
          <p className="mt-2 text-sm leading-6 text-zinc-600">
            Start tracking your competitive progress across platforms.
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
              aria-describedby={
                errors.username ? "register-username-error" : undefined
              }
              className={inputClassName}
              {...register("username")}
            />
            {errors.username?.message ? (
              <p className={errorClassName} id="register-username-error">
                {errors.username.message}
              </p>
            ) : null}
          </div>

          <div>
            <label className={labelClassName} htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              aria-invalid={Boolean(errors.email)}
              aria-describedby={
                errors.email ? "register-email-error" : undefined
              }
              className={inputClassName}
              {...register("email")}
            />
            {errors.email?.message ? (
              <p className={errorClassName} id="register-email-error">
                {errors.email.message}
              </p>
            ) : null}
          </div>

          <div>
            <label className={labelClassName} htmlFor="full_name">
              Full name
            </label>
            <input
              id="full_name"
              type="text"
              autoComplete="name"
              aria-invalid={Boolean(errors.full_name)}
              aria-describedby={
                errors.full_name ? "register-full-name-error" : undefined
              }
              className={inputClassName}
              {...register("full_name")}
            />
            {errors.full_name?.message ? (
              <p className={errorClassName} id="register-full-name-error">
                {errors.full_name.message}
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
              autoComplete="new-password"
              aria-invalid={Boolean(errors.password)}
              aria-describedby={
                errors.password ? "register-password-error" : undefined
              }
              className={inputClassName}
              {...register("password")}
            />
            {errors.password?.message ? (
              <p className={errorClassName} id="register-password-error">
                {errors.password.message}
              </p>
            ) : null}
          </div>

          <div>
            <label className={labelClassName} htmlFor="password_confirm">
              Confirm password
            </label>
            <input
              id="password_confirm"
              type="password"
              autoComplete="new-password"
              aria-invalid={Boolean(errors.password_confirm)}
              aria-describedby={
                errors.password_confirm
                  ? "register-password-confirm-error"
                  : undefined
              }
              className={inputClassName}
              {...register("password_confirm")}
            />
            {errors.password_confirm?.message ? (
              <p
                className={errorClassName}
                id="register-password-confirm-error"
              >
                {errors.password_confirm.message}
              </p>
            ) : null}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center rounded-md bg-zinc-950 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
          >
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-zinc-600">
          Already have an account?{" "}
          <Link className="font-medium text-zinc-950 hover:underline" href="/login">
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}
