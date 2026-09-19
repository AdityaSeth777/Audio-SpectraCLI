import { eq, isNull, and } from "drizzle-orm";
import { db } from "./db";
import { apiKeys, users } from "./db/schema";
import { extractBearerKey, hashApiKey } from "./apiKeys";
import { checkRateLimit } from "./rateLimit";

const RATE_LIMIT = { limit: 60, windowMs: 60_000 }; // 60 requests/minute per key

export type ApiAuthResult =
  | { ok: true; apiKeyId: string; ownerId: string }
  | { ok: false; status: number; error: string };

/**
 * Authenticates a Data/Analysis API request via `Authorization: Bearer <key>`,
 * checks the key owner's subscription is currently active (the Analysis API
 * is a paid-plan feature - enforced here, not just at key-creation time, so
 * a downgraded account's existing keys stop working without needing to be
 * explicitly revoked), then rate-limits it.
 */
export async function authenticateApiRequest(request: Request): Promise<ApiAuthResult> {
  const plaintextKey = extractBearerKey(request.headers.get("authorization"));
  if (!plaintextKey) {
    return { ok: false, status: 401, error: "Missing Authorization: Bearer <api key> header." };
  }

  const keyHash = hashApiKey(plaintextKey);
  const [row] = await db
    .select({ id: apiKeys.id, ownerId: apiKeys.ownerId, subscriptionStatus: users.subscriptionStatus })
    .from(apiKeys)
    .innerJoin(users, eq(apiKeys.ownerId, users.id))
    .where(and(eq(apiKeys.keyHash, keyHash), isNull(apiKeys.revokedAt)))
    .limit(1);

  if (!row) {
    return { ok: false, status: 401, error: "Invalid or revoked API key." };
  }

  if (row.subscriptionStatus !== "active") {
    return {
      ok: false,
      status: 402,
      error: "The Data/Analysis API requires an active paid plan. This key's account is not currently on the paid plan.",
    };
  }

  const { allowed } = await checkRateLimit(row.id, RATE_LIMIT);
  if (!allowed) {
    return { ok: false, status: 429, error: "Rate limit exceeded (60 requests/minute per key)." };
  }

  await db.update(apiKeys).set({ lastUsedAt: new Date() }).where(eq(apiKeys.id, row.id));

  return { ok: true, apiKeyId: row.id, ownerId: row.ownerId };
}
