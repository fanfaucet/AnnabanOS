/**
 * Curiosity Telemetry Relay
 *
 * Simulation-safe telemetry sideload/relay module for MarsSim.
 *
 * IP / provenance:
 *   Conceptual architecture and implementation authored by
 *   Jacob Wayne Kinnaird for ANNABAN / AnnabanOS.
 *
 * STATUS:
 *   Simulation/design artifact only.
 *
 * SAFETY BOUNDARY:
 *   - No connection to NASA/JPL systems.
 *   - No modification of Curiosity flight software.
 *   - No transmission of real mission telemetry.
 *   - Requires a simulation-only sink capability.
 */

export type TelemetrySource =
  | "CURIOSITY_SIMULATOR"
  | "GROUND_SIMULATOR"
  | "MISSION_REPLAY";

export type TelemetryPriority = "LOW" | "NORMAL" | "HIGH" | "CRITICAL";

export type RelayStatus =
  | "QUEUED"
  | "VALIDATED"
  | "REJECTED"
  | "RELAYED_SIMULATION"
  | "FAILED";

export interface CuriosityTelemetry {
  missionId: string;
  rover: "CURIOSITY";
  sol: number;
  timestamp: string;
  source: TelemetrySource;
  sequence: number;
  priority: TelemetryPriority;
  payload: Record<string, unknown>;
}

export interface TelemetryProvenance {
  simulationId: string;
  generatedBy: string;
  modelVersion?: string;
  sourceClassification: "SIMULATED";
  generatedAt: string;
  assumptions: string[];
  evidenceRefs: string[];
}

export interface TelemetryEnvelope {
  id: string;
  createdAt: string;
  telemetry: CuriosityTelemetry;
  checksum: string;
  simulationOnly: true;
  externalEffect: false;
  provenance: TelemetryProvenance;
}

/**
 * Capability boundary: the relay can only receive a simulation-scoped sink.
 * A production transport must not satisfy this interface merely by exposing
 * an accept() method.
 */
export interface SimulationTelemetrySink {
  readonly capability: "SIMULATION_TELEMETRY_ONLY";
  accept(envelope: TelemetryEnvelope): Promise<void>;
}

export interface RelayResult {
  envelopeId: string;
  status: RelayStatus;
  validated: boolean;
  deliveredTo: "SIMULATED_NASA_GATEWAY" | "NONE";
  error?: string;
}

export class SimulatedNASADataGateway implements SimulationTelemetrySink {
  readonly capability = "SIMULATION_TELEMETRY_ONLY" as const;

  private readonly received: TelemetryEnvelope[] = [];

  async accept(envelope: TelemetryEnvelope): Promise<void> {
    if (
      envelope.simulationOnly !== true ||
      envelope.externalEffect !== false ||
      envelope.provenance.sourceClassification !== "SIMULATED"
    ) {
      throw new Error(
        "Telemetry gateway rejected envelope: simulation boundary violated.",
      );
    }

    this.received.push(envelope);
  }

  getReceived(): readonly TelemetryEnvelope[] {
    return this.received;
  }
}

export class CuriosityTelemetryRelay {
  constructor(
    private readonly sink: SimulationTelemetrySink,
    private readonly missionId: string,
    private readonly simulationId = "MarsSim",
  ) {}

  async relay(telemetry: CuriosityTelemetry): Promise<RelayResult> {
    const validationError = this.validate(telemetry);

    if (validationError) {
      return {
        envelopeId: "",
        status: "REJECTED",
        validated: false,
        deliveredTo: "NONE",
        error: validationError,
      };
    }

    const envelope = await this.createEnvelope(telemetry);

    try {
      await this.sink.accept(envelope);

      return {
        envelopeId: envelope.id,
        status: "RELAYED_SIMULATION",
        validated: true,
        deliveredTo: "SIMULATED_NASA_GATEWAY",
      };
    } catch (error) {
      return {
        envelopeId: envelope.id,
        status: "FAILED",
        validated: true,
        deliveredTo: "NONE",
        error:
          error instanceof Error
            ? error.message
            : "Unknown telemetry relay failure",
      };
    }
  }

  private validate(
    telemetry: CuriosityTelemetry,
  ): string | undefined {
    if (telemetry.rover !== "CURIOSITY") {
      return "Invalid rover identifier.";
    }

    if (telemetry.missionId !== this.missionId) {
      return "Mission identifier mismatch.";
    }

    if (!Number.isInteger(telemetry.sol) || telemetry.sol < 0) {
      return "Invalid Martian sol.";
    }

    if (!Number.isInteger(telemetry.sequence) || telemetry.sequence < 0) {
      return "Invalid telemetry sequence.";
    }

    if (!telemetry.timestamp) {
      return "Telemetry timestamp is required.";
    }

    if (!telemetry.source) {
      return "Telemetry source is required.";
    }

    return undefined;
  }

  private async createEnvelope(
    telemetry: CuriosityTelemetry,
  ): Promise<TelemetryEnvelope> {
    const canonical = JSON.stringify(telemetry);

    return {
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      telemetry,
      checksum: await sha256(canonical),
      simulationOnly: true,
      externalEffect: false,
      provenance: {
        simulationId: this.simulationId,
        generatedBy: "MarsSim.CuriosityTelemetryRelay",
        sourceClassification: "SIMULATED",
        generatedAt: new Date().toISOString(),
        assumptions: [
          "Telemetry originates from a simulation or mission replay.",
          "No NASA/JPL system is connected.",
          "No flight-software command is generated.",
        ],
        evidenceRefs: [],
      },
    };
  }
}

async function sha256(value: string): Promise<string> {
  const data = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", data);

  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}
