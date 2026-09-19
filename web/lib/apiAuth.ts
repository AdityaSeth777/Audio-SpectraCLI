import { eq, isNull, and } from "drizzle-orm";
import { db } from "./db";
import { apiKeys } from "./db/schema";
import { extractBearerKey, hashApiKey } from "./apiKeys";
import { checkRateLimit } from "./rateLimit";

const RATE_LIMIT = { limit: 60, windowMs: 60_000 }; // 60 requests/minute per key

export type ApiAuthResult =
  | { ok: true; apiKeyId: string; ownerId: string }
  | { ok: false; status: number; error: string };

/** Authenticates a Data/Analysis API request via `Authorization: Bearer <key>`, then rate-limits it. */
export async function authenticateApiRequest(request: Request): Promise<ApiAuthResult> {
  const plaintextKey = extractBearerKey(request.headers.get("authorization"));
  if (!plaintextKey) {
    return { ok: false, status: 401, error: "Missing Authorization: Bearer <api key> header." };
  }

  const keyHash = hashApiKey(plaintextKey);
  const [row] = await db
    .select()
    .from(apiKeys)
    .where(and(eq(apiKeys.keyHash, keyHash), isNull(apiKeys.revokedAt)))
    .limit(1);

  if (!row) {
    return { ok: false, status: 401, error: "Invalid or revoked API key." };
  }

  const { allowed } = checkRateLimit(row.id, RATE_LIMIT);
  if (!allowed) {
    return { ok: false, status: 429, error: "Rate limit exceeded (60 requests/minute per key)." };
  }

  await db.update(apiKeys).set({ lastUsedAt: new Date() }).where(eq(apiKeys.id, row.id));

  return { ok: true, apiKeyId: row.id, ownerId: row.ownerId };
}
