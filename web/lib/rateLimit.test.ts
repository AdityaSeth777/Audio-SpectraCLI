import { describe, expect, it } from "vitest";
import { checkRateLimit } from "./rateLimit";

describe("checkRateLimit", () => {
  it("allows requests up to the limit, then blocks", () => {
    const key = `test-key-${Math.random()}`;
    const opts = { limit: 3, windowMs: 60_000 };

    expect(checkRateLimit(key, opts).allowed).toBe(true);
    expect(checkRateLimit(key, opts).allowed).toBe(true);
    expect(checkRateLimit(key, opts).allowed).toBe(true);
    expect(checkRateLimit(key, opts).allowed).toBe(false);
  });

  it("tracks separate windows per key independently", () => {
    const opts = { limit: 1, windowMs: 60_000 };
    const keyA = `key-a-${Math.random()}`;
    const keyB = `key-b-${Math.random()}`;

    expect(checkRateLimit(keyA, opts).allowed).toBe(true);
    expect(checkRateLimit(keyB, opts).allowed).toBe(true);
    expect(checkRateLimit(keyA, opts).allowed).toBe(false);
  });

  it("resets after the window elapses", async () => {
    const key = `test-key-${Math.random()}`;
    const opts = { limit: 1, windowMs: 10 };

    expect(checkRateLimit(key, opts).allowed).toBe(true);
    expect(checkRateLimit(key, opts).allowed).toBe(false);

    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(checkRateLimit(key, opts).allowed).toBe(true);
  });
});
