import type { Achievement } from "./types";

export const verificationLabel: Record<Achievement["verification_status"], string> = {
  verified: "Verified",
  evidence_provided: "Evidence provided",
  self_reported: "Self-reported",
};
