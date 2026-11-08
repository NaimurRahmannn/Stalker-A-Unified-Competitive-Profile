import { z } from "zod";

export const connectPlatformSchema = z.object({
  platform: z.enum(["codeforces", "atcoder", "leetcode", "ctftime", "kaggle"]),
  handle: z
    .string()
    .trim()
    .min(1, "Handle is required")
    .max(200, "Handle is too long"),
}).superRefine(({ platform, handle }, context) => {
  if (platform !== "kaggle" && handle.length > 64) {
    context.addIssue({ code: "custom", path: ["handle"], message: "Handle is too long" });
  }
  if (platform === "ctftime" && !/^[1-9][0-9]*$/.test(handle)) {
    context.addIssue({
      code: "custom",
      path: ["handle"],
      message: "Enter a numeric CTFtime team ID.",
    });
  }
});

export type ConnectPlatformFormValues = z.infer<typeof connectPlatformSchema>;
