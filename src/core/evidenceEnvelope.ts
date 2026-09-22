import { createHash, randomUUID } from "node:crypto";

export type AuthorizationStatus = "NOT_AUTHORIZED" | "AUTHORIZED" | "DENIED";
export type HumanReviewStatus = "REQUIRED" | "NOT_REQUIRED" | "COMPLETED";

export type AnnabanEvidenceEnvelope = {
  evidenceId: string;
  source: string;
  sourceType: string;
  provenance: string;
  timestamp: string;
  payload: Record<string, unknown>;
  integrityHash: `sha256:${string}`;
  interpretationStatus: string;
  authorizationStatus: AuthorizationStatus;
  humanReviewStatus: HumanReviewStatus;
};

export function createEvidenceEnvelope({
  source,
  sourceType,
  provenance,
  payload,
  interpretationStatus,
  authorizationStatus = "NOT_AUTHORIZED",
  humanReviewStatus = "REQUIRED",
  evidenceId = `evidence-${randomUUID()}`,
  timestamp = new Date().toISOString(),
}: Omit<AnnabanEvidenceEnvelope, "integrityHash"> & { integrityHash?: never }): AnnabanEvidenceEnvelope {
  const material = {
    evidenceId,
    source,
    sourceType,
    provenance,
    timestamp,
    payload,
    interpretationStatus,
    authorizationStatus,
    humanReviewStatus,
  };
  const integrityHash = `sha256:${createHash("sha256").update(JSON.stringify(material)).digest("hex")}` as const;
  return { ...material, integrityHash };
}
