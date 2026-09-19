import { randomBytes, createHash } from "crypto";

const KEY_PREFIX = "sk_spectra_";

/** Generates a new plaintext API key. Shown to the user exactly once. */
export function generateApiKey(): string {
  return KEY_PREFIX + randomBytes(24).toString("hex");
}

/** Hashes a plaintext key for storage/lookup — we never store the plaintext. */
export function hashApiKey(plaintextKey: string): string {
  return createHash("sha256").update(plaintextKey).digest("hex");
}

/** Extracts the bearer key from an `Authorization: Bearer <key>` header, if present. */
export function extractBearerKey(authorizationHeader: string | null): string | null {
  if (!authorizationHeader) return null;
  const match = /^Bearer\s+(.+)$/i.exec(authorizationHeader.trim());
  return match ? match[1] : null;
}
