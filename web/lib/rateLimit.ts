import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

/**
 * Rate limiter, keyed by an arbitrary string (an API key id here).
 *
 * If UPSTASH_REDIS_REST_URL/UPSTASH_REDIS_REST_TOKEN are set, this uses a
 * real shared Redis-backed sliding window - correct across multiple
 * serverless instances. Without them, it falls back to the original
 * in-memory fixed-window limiter, which is only correct for a single Node
 * process; that fallback exists so the app still runs (e.g. `npm run dev`)
 * without requiring an Upstash account, not as a production substitute.
 */

const upstashConfigured = Boolean(process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN);

const inMemoryWindows = new Map<string, { count: number; windowStartMs: number }>();
const upstashLimiters = new Map<string, Ratelimit>();

function getUpstashLimiter(limit: number, windowMs: number): Ratelimit {
  const cacheKey = `${limit}:${windowMs}`;
  const existing = upstashLimiters.get(cacheKey);
  if (existing) return existing;

  const redis = new Redis({
    url: process.env.UPSTASH_REDIS_REST_URL!,
    token: process.env.UPSTASH_REDIS_REST_TOKEN!,
  });

  const limiter = new Ratelimit({
    redis,
    limiter: Ratelimit.slidingWindow(limit, `${windowMs} ms`),
    prefix: "audio-spectracli-ratelimit",
  });

  upstashLimiters.set(cacheKey, limiter);
  return limiter;
}

function checkInMemory(key: string, limit: number, windowMs: number): { allowed: boolean; remaining: number } {
  const now = Date.now();
  const existing = inMemoryWindows.get(key);

  if (!existing || now - existing.windowStartMs >= windowMs) {
    inMemoryWindows.set(key, { count: 1, windowStartMs: now });
    return { allowed: true, remaining: limit - 1 };
  }

  if (existing.count >= limit) {
    return { allowed: false, remaining: 0 };
  }

  existing.count += 1;
  return { allowed: true, remaining: limit - existing.count };
}

export async function checkRateLimit(
  key: string,
  { limit, windowMs }: { limit: number; windowMs: number },
): Promise<{ allowed: boolean; remaining: number }> {
  if (!upstashConfigured) {
    return checkInMemory(key, limit, windowMs);
  }

  const { success, remaining } = await getUpstashLimiter(limit, windowMs).limit(key);
  return { allowed: success, remaining };
}

/** Whether rate limiting is backed by shared, multi-instance-safe storage right now. */
export function isRateLimitDistributed(): boolean {
  return upstashConfigured;
}
