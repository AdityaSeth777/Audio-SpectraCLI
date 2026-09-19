/**
 * In-memory fixed-window rate limiter, keyed by an arbitrary string (an API
 * key id here). Good enough for a single Node process; it is NOT correct
 * across multiple serverless instances (each gets its own memory), since
 * that needs a shared store like Upstash/Redis - flagged here rather than
 * silently pretending this is production-grade multi-instance rate limiting.
 */

const windows = new Map<string, { count: number; windowStartMs: number }>();

export function checkRateLimit(
  key: string,
  { limit, windowMs }: { limit: number; windowMs: number },
): { allowed: boolean; remaining: number } {
  const now = Date.now();
  const existing = windows.get(key);

  if (!existing || now - existing.windowStartMs >= windowMs) {
    windows.set(key, { count: 1, windowStartMs: now });
    return { allowed: true, remaining: limit - 1 };
  }

  if (existing.count >= limit) {
    return { allowed: false, remaining: 0 };
  }

  existing.count += 1;
  return { allowed: true, remaining: limit - existing.count };
}
