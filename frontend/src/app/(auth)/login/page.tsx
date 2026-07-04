"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { TextField } from "@/components/forms/text-field";
import { loginSchema, type LoginFormValues } from "@/features/auth/schemas";
import { useAuth } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/utils";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await login(values);
      toast.success("Welcome back!");
      router.push("/dashboard");
    } catch (error) {
      toast.error(
        getApiErrorMessage(
          error,
          "Could not sign you in. Check your credentials and try again.",
        ),
      );
    }
  });

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <h1 className="text-xl font-semibold text-slate-950">Welcome back</h1>
      <p className="mt-1 text-sm text-slate-500">
        Sign in to continue tracking your technical journey.
      </p>

      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-4" noValidate>
        <TextField
          id="username"
          label="Username"
          placeholder="your-handle"
          autoComplete="username"
          registration={register("username")}
          error={errors.username?.message}
        />
        <TextField
          id="password"
          label="Password"
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
          registration={register("password")}
          error={errors.password?.message}
        />

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-1 inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="font-semibold text-blue-700 transition hover:text-blue-800"
        >
          Create one
        </Link>
      </p>
    </section>
  );
}
