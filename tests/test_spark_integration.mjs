import test from "node:test";
import assert from "node:assert/strict";

import {
  AnnabanPolicyGate,
  HapticControllerBridge,
  runFictionalRtxSparkSession,
} from "../src/core/sparkIntegration.ts";

test("fictional RTX Spark session approves low-risk haptics and blocks high-risk output", () => {
  const result = runFictionalRtxSparkSession();

  assert.equal(result.summary.approvedActions, 1);
  assert.equal(result.summary.blockedActions, 1);
  assert.equal(result.summary.safetyViolations, 0);
  assert.equal(result.hapticOutputs[0].actuatorState, "ACTIVE");
  assert.equal(result.hapticOutputs[0].frequencyHz, 212);
  assert.equal(result.hapticOutputs[0].intensity, 0.81);
  assert.equal(result.hapticOutputs[1].actuatorState, "SAFE");
  assert.equal(result.hapticOutputs[1].frequencyHz, 0);
  assert.equal(result.ledgerEntries.length, 2);
});

test("policy gate blocks excessive risk before haptic output", () => {
  const policyGate = new AnnabanPolicyGate();
  const haptics = new HapticControllerBridge();
  const decision = policyGate.evaluate("RoutingAssist", {
    confidence: 0.54,
    risk: 0.88,
    ethicalScore: 0.91,
  });
  const output = haptics.output(decision, {
    confidence: 0.54,
    risk: 0.88,
    ethicalScore: 0.91,
  });

  assert.equal(decision.status, "blocked");
  assert.equal(decision.reason, "risk threshold exceeded");
  assert.equal(output.actuatorState, "SAFE");
  assert.equal(output.intensity, 0);
});
