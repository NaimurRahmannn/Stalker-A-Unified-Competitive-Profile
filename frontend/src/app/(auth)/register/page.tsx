"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { TextField } from "@/components/forms/text-field";
import {
  registerSchema,
  type RegisterFormValues,
} from "@/features/auth/schemas";
import { useAuth } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/utils";

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser } = useAuth();
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

  const onSubmit = handleSubmit(async (values) => {
    try {
      await registerUser(values);
      toast.success("Account created. Welcome to STALKER!");
      router.push("/dashboard");
    } catch (error) {
      toast.error(
        getApiErrorMessage(
          error,
          "Could not create your account. Please try again.",
        ),
      );
    }
  });

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_14px_34px_rgba(15,23,42,0.04)]">
      <h1 className="text-xl font-semibold text-slate-950">
        Create your account
      </h1>
      <p className="mt-1 text-sm text-slate-500">
        Connect your platforms and track your growth in one place.
      </p>

      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-4" noValidate>
        <TextField
          id="full_name"
          label="Full name"
          placeholder="Ada Lovelace"
          autoComplete="name"
          registration={register("full_name")}
          error={errors.full_name?.message}
        />
        <TextField
          id="username"
          label="Username"
          placeholder="your-handle"
          autoComplete="username"
          registration={register("username")}
          error={errors.username?.message}
        />
        <TextField
          id="email"
          label="Email"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          registration={register("email")}
          error={errors.email?.message}
        />
        <TextField
          id="password"
          label="Password"
          type="password"
          placeholder="At least 8 characters"
          autoComplete="new-password"
          registration={register("password")}
          error={errors.password?.message}
        />
        <TextField
          id="password_confirm"
          label="Confirm password"
          type="password"
          placeholder="Re-enter your password"
          autoComplete="new-password"
          registration={register("password_confirm")}
          error={errors.password_confirm?.message}
        />

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-1 inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-semibold text-blue-700 transition hover:text-blue-800"
        >
          Sign in
        </Link>
      </p>
    </section>
  );
}
