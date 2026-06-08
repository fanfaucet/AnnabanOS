import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, normalize, relative } from "node:path";

import { GitLedger, sha256, type LedgerEntry } from "./gitLedger.ts";

export type ArtifactPayload = {
  code: string;
};

export type TransferFlags = {
  immutable: boolean;
  requiresReview: boolean;
};

export type TransferPacket = {
  packetId: string;
  source: string;
  destination: string;
  artifactType: "typescript_module" | "json_document" | "text_artifact";
  path: string;
  compression: "none";
  integrityHash: `sha256:${string}`;
  payload: ArtifactPayload;
  flags: TransferFlags;
};

export type TransferEvent = {
  event: string;
  packetId: string;
  message: string;
  latencyMs?: number;
};

export type TransferReceipt = {
  packetId: string;
  artifact: string;
  status: "success";
  verification: "integrity_passed";
  readyForExecution: true;
  events: TransferEvent[];
  ledgerEntry: LedgerEntry;
};

export interface ArtifactStore {
  write(path: string, code: string): Promise<void>;
  read(path: string): Promise<string | undefined>;
}

export class MemoryArtifactStore implements ArtifactStore {
  readonly #files = new Map<string, string>();

  async write(path: string, code: string): Promise<void> {
    this.#files.set(path, code);
  }

  async read(path: string): Promise<string | undefined> {
    return this.#files.get(path);
  }
}

export class FileSystemArtifactStore implements ArtifactStore {
  private readonly rootDirectory: string;

  constructor(rootDirectory: string) {
    this.rootDirectory = rootDirectory;
  }

  async write(path: string, code: string): Promise<void> {
    const destination = this.resolveInsideRoot(path);
    await mkdir(dirname(destination), { recursive: true });
    await writeFile(destination, code, "utf8");
  }

  async read(path: string): Promise<string | undefined> {
    const destination = this.resolveInsideRoot(path);
    return readFile(destination, "utf8");
  }

  private resolveInsideRoot(path: string): string {
    const destination = normalize(join(this.rootDirectory, path.replace(/^\/+/, "")));
    const relativePath = relative(this.rootDirectory, destination);

    if (relativePath.startsWith("..") || relativePath === "") {
      throw new Error(`Refusing to write outside artifact root: ${path}`);
    }

    return destination;
  }
}

export function encodeTransferPacket(
  packet: Omit<TransferPacket, "integrityHash" | "compression">,
): TransferPacket {
  return {
    ...packet,
    compression: "none",
    integrityHash: `sha256:${sha256(packet.payload.code)}`,
  };
}

export class IATransferBus {
  readonly #events: TransferEvent[] = [];

  route(packet: TransferPacket, channel = "EXEC_PIPELINE_01", latencyMs = 12): TransferEvent[] {
    const events: TransferEvent[] = [
      {
        event: "EVENT_BUS_ROUTE",
        packetId: packet.packetId,
        message: `routing packet ${packet.packetId}`,
      },
      {
        event: "EVENT_BUS_RESOLVE_DESTINATION",
        packetId: packet.packetId,
        message: `resolving destination: ${packet.destination}`,
      },
      {
        event: "EVENT_BUS_CHANNEL_SELECTED",
        packetId: packet.packetId,
        message: `channel: ${channel}`,
        latencyMs,
      },
    ];

    this.#events.push(...events);
    return events;
  }

  events(): readonly TransferEvent[] {
    return this.#events.map((event) => Object.freeze({ ...event }));
  }
}

export class CodexExecutorNode {
  private readonly store: ArtifactStore;
  private readonly ledger: GitLedger;

  constructor(store: ArtifactStore = new MemoryArtifactStore(), ledger = new GitLedger()) {
    this.store = store;
    this.ledger = ledger;
  }

  async receive(packet: TransferPacket, events: readonly TransferEvent[] = []): Promise<TransferReceipt> {
    this.assertIntegrity(packet);
    await this.store.write(packet.path, packet.payload.code);

    const ledgerEntry = this.ledger.append({
      event: "FILE_TRANSFER_COMPLETE",
      packetId: packet.packetId,
      source: packet.source,
      destination: packet.destination,
      artifactPath: packet.path,
      status: "success",
      verification: "integrity_passed",
      metadata: {
        artifactType: packet.artifactType,
        immutable: packet.flags.immutable,
        requiresReview: packet.flags.requiresReview,
      },
    });

    return {
      packetId: packet.packetId,
      artifact: packet.path.split("/").at(-1) ?? packet.path,
      status: "success",
      verification: "integrity_passed",
      readyForExecution: true,
      events: [...events],
      ledgerEntry,
    };
  }

  async readArtifact(path: string): Promise<string | undefined> {
    return this.store.read(path);
  }

  ledgerEntries(): readonly LedgerEntry[] {
    return this.ledger.entries();
  }

  verifyLedger(): boolean {
    return this.ledger.verify();
  }

  private assertIntegrity(packet: TransferPacket): void {
    const expectedHash = `sha256:${sha256(packet.payload.code)}`;

    if (packet.integrityHash !== expectedHash) {
      throw new Error(`Integrity check failed for packet ${packet.packetId}`);
    }
  }
}

export async function simulateIaftpTransfer(packet: TransferPacket): Promise<TransferReceipt> {
  const bus = new IATransferBus();
  const executor = new CodexExecutorNode();
  const events = bus.route(packet);
  return executor.receive(packet, events);
}
