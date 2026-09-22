export type BusinessContext = {
  owner: string;
  organization: string;
  orchestrationPlatform: string;
  operatingSystem: string;
  tagline: string;
  businessDomains: string[];
  modules: Record<string, string>;
};

export const JACOB_KINNAIRD_BUSINESS: BusinessContext = Object.freeze({
  owner: "Jacob Wayne Kinnaird",
  organization: "AnnabanAI",
  orchestrationPlatform: "SparkAI+",
  operatingSystem: "AnnabanOS",
  tagline: "Deterministic governance and simulation middleware for agentic AI systems.",
  businessDomains: Object.freeze([
    "AI governance middleware",
    "agent orchestration",
    "simulation systems",
    "logistics intelligence",
    "audit and safety tooling",
  ]),
  modules: Object.freeze({
    annabanBenchmark: "core governance, routing, constraints, signals, and audit ledger",
    annabanMaritime: "logistics demonstrator for ETA, route scoring, and alignment checks",
    iaftp: "local inter-agent artifact transfer emulation for planner/executor workflows",
    sparkIntegration: "fictional local SparkAI+ node safety simulation with haptic interlock",
  }),
});

export function businessTelemetryEnvelope(details: Record<string, unknown>): Record<string, unknown> {
  return {
    business: JACOB_KINNAIRD_BUSINESS,
    ...details,
  };
}
