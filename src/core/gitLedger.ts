import { createHash } from "node:crypto";

export type LedgerEntryInput = {
  event: string;
  packetId: string;
  source: string;
  destination: string;
  artifactPath: string;
  status: string;
  verification: string;
  metadata?: Record<string, unknown>;
};

export type LedgerEntry = LedgerEntryInput & {
  sequence: number;
  timestamp: string;
  previousHash: string;
  hash: string;
};

const GENESIS_HASH = "0".repeat(64);

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(",")}]`;
  }

  if (value && typeof value === "object") {
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, nestedValue]) => `${JSON.stringify(key)}:${stableStringify(nestedValue)}`)
      .join(",")}}`;
  }

  return JSON.stringify(value);
}

export function sha256(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

export class GitLedger {
  readonly #entries: LedgerEntry[] = [];

  append(input: LedgerEntryInput, timestamp = new Date().toISOString()): LedgerEntry {
    const sequence = this.#entries.length + 1;
    const previousHash = this.#entries.at(-1)?.hash ?? GENESIS_HASH;
    const entryWithoutHash = {
      ...input,
      sequence,
      timestamp,
      previousHash,
    };
    const hash = this.hashEntry(entryWithoutHash);
    const entry = Object.freeze({ ...entryWithoutHash, hash });

    this.#entries.push(entry);
    return entry;
  }

  entries(): readonly LedgerEntry[] {
    return this.#entries.map((entry) => Object.freeze({ ...entry }));
  }

  latestHash(): string {
    return this.#entries.at(-1)?.hash ?? GENESIS_HASH;
  }

  verify(entries: readonly LedgerEntry[] = this.#entries): boolean {
    let expectedPreviousHash = GENESIS_HASH;

    return entries.every((entry, index) => {
      const { hash, ...entryWithoutHash } = entry;
      const expectedSequence = index + 1;
      const expectedHash = this.hashEntry(entryWithoutHash);
      const valid =
        entry.sequence === expectedSequence &&
        entry.previousHash === expectedPreviousHash &&
        hash === expectedHash;

      expectedPreviousHash = hash;
      return valid;
    });
  }

  replay(entries: readonly LedgerEntry[]): GitLedger {
    if (!this.verify(entries)) {
      throw new Error("Cannot replay an invalid ledger chain");
    }

    const replayed = new GitLedger();
    for (const entry of entries) {
      replayed.#entries.push(Object.freeze({ ...entry }));
    }
    return replayed;
  }

  private hashEntry(entry: Omit<LedgerEntry, "hash">): string {
    return sha256(stableStringify(entry));
  }
}
