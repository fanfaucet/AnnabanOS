import test from "node:test";
import assert from "node:assert/strict";

import {
  CodexExecutorNode,
  IATransferBus,
  MemoryArtifactStore,
  encodeTransferPacket,
} from "../src/core/iaftp.ts";
import { GitLedger } from "../src/core/gitLedger.ts";

test("IAFTP packet transfer writes artifact and records verifiable ledger entry", async () => {
  const packet = encodeTransferPacket({
    packetId: "TX-88421",
    source: "chatgpt-planner",
    destination: "codex-executor",
    artifactType: "typescript_module",
    path: "/src/core/gitLedger.ts",
    payload: { code: "export class GitLedger {}" },
    flags: { immutable: true, requiresReview: true },
  });

  const bus = new IATransferBus();
  const executor = new CodexExecutorNode(new MemoryArtifactStore(), new GitLedger());
  const events = bus.route(packet);
  const receipt = await executor.receive(packet, events);

  assert.equal(receipt.status, "success");
  assert.equal(receipt.verification, "integrity_passed");
  assert.equal(receipt.artifact, "gitLedger.ts");
  assert.equal(await executor.readArtifact("/src/core/gitLedger.ts"), "export class GitLedger {}");
  assert.equal(executor.verifyLedger(), true);
  assert.equal(executor.ledgerEntries().length, 1);
  assert.equal(events.length, 3);
});

test("IAFTP rejects payloads whose integrity hash no longer matches", async () => {
  const packet = encodeTransferPacket({
    packetId: "TX-88421",
    source: "chatgpt-planner",
    destination: "codex-executor",
    artifactType: "typescript_module",
    path: "/src/core/gitLedger.ts",
    payload: { code: "export class GitLedger {}" },
    flags: { immutable: true, requiresReview: true },
  });

  const tamperedPacket = {
    ...packet,
    payload: { code: "export class GitLedger { tampered = true }" },
  };

  const executor = new CodexExecutorNode();
  await assert.rejects(
    () => executor.receive(tamperedPacket),
    /Integrity check failed for packet TX-88421/,
  );
});
