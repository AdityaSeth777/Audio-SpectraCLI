import { describe, expect, it } from "vitest";
import { checkRateLimit, isRateLimitDistributed } from "./rateLimit";

describe("checkRateLimit (in-memory fallback — no UPSTASH_* env vars set in tests)", () => {
  it("is not backed by distributed storage without Upstash env vars", () => {
    expect(isRateLimitDistributed()).toBe(false);
  });

  it("allows requests up to the limit, then blocks", async () => {
    const key = `test-key-${Math.random()}`;
    const opts = { limit: 3, windowMs: 60_000 };

    expect((await checkRateLimit(key, opts)).allowed).toBe(true);
    expect((await checkRateLimit(key, opts)).allowed).toBe(true);
    expect((await checkRateLimit(key, opts)).allowed).toBe(true);
    expect((await checkRateLimit(key, opts)).allowed).toBe(false);
  });

  it("tracks separate windows per key independently", async () => {
    const opts = { limit: 1, windowMs: 60_000 };
    const keyA = `key-a-${Math.random()}`;
    const keyB = `key-b-${Math.random()}`;

    expect((await checkRateLimit(keyA, opts)).allowed).toBe(true);
    expect((await checkRateLimit(keyB, opts)).allowed).toBe(true);
    expect((await checkRateLimit(keyA, opts)).allowed).toBe(false);
  });

  it("resets after the window elapses", async () => {
    const key = `test-key-${Math.random()}`;
    const opts = { limit: 1, windowMs: 10 };

    expect((await checkRateLimit(key, opts)).allowed).toBe(true);
    expect((await checkRateLimit(key, opts)).allowed).toBe(false);

    await new Promise((resolve) => setTimeout(resolve, 20));
    expect((await checkRateLimit(key, opts)).allowed).toBe(true);
  });
});
