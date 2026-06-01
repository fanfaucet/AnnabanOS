import { encodeTransferPacket, simulateIaftpTransfer } from "./iaftp.ts";

const packet = encodeTransferPacket({
  packetId: "TX-88421",
  source: "chatgpt-planner",
  destination: "codex-executor",
  artifactType: "typescript_module",
  path: "/src/core/gitLedger.ts",
  payload: {
    code: "export class GitLedger { /* planner-provided artifact */ }",
  },
  flags: {
    immutable: true,
    requiresReview: true,
  },
});

const receipt = await simulateIaftpTransfer(packet);
console.log(JSON.stringify(receipt, null, 2));
