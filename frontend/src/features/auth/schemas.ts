import { z } from "zod";

export const registerSchema = z
  .object({
    username: z.string().trim().min(3, "Username must be at least 3 characters"),
    email: z.string().trim().email("Enter a valid email address"),
    full_name: z.string().trim().min(2, "Full name must be at least 2 characters"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    password_confirm: z.string().min(1, "Please confirm your password"),
  })
  .refine((values) => values.password === values.password_confirm, {
    message: "Passwords do not match",
    path: ["password_confirm"],
  });

export const loginSchema = z.object({
  username: z.string().trim().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;
export type LoginFormValues = z.infer<typeof loginSchema>;
