import { z } from "zod";

export const connectPlatformSchema = z.object({
  handle: z
    .string()
    .trim()
    .min(1, "Handle is required")
    .max(64, "Handle is too long"),
});

export type ConnectPlatformFormValues = z.infer<typeof connectPlatformSchema>;
