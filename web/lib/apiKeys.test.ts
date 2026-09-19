import { describe, expect, it } from "vitest";
import { extractBearerKey, generateApiKey, hashApiKey } from "./apiKeys";

describe("generateApiKey", () => {
  it("generates keys with the expected prefix and sufficient entropy", () => {
    const a = generateApiKey();
    const b = generateApiKey();
    expect(a).toMatch(/^sk_spectra_[0-9a-f]{48}$/);
    expect(a).not.toBe(b);
  });
});

describe("hashApiKey", () => {
  it("is deterministic and one-way-looking (hash != input)", () => {
    const key = generateApiKey();
    expect(hashApiKey(key)).toBe(hashApiKey(key));
    expect(hashApiKey(key)).not.toBe(key);
  });

  it("produces different hashes for different keys", () => {
    expect(hashApiKey(generateApiKey())).not.toBe(hashApiKey(generateApiKey()));
  });
});

describe("extractBearerKey", () => {
  it("extracts the key from a well-formed header", () => {
    expect(extractBearerKey("Bearer sk_spectra_abc123")).toBe("sk_spectra_abc123");
  });

  it("is case-insensitive on the Bearer scheme", () => {
    expect(extractBearerKey("bearer sk_spectra_abc123")).toBe("sk_spectra_abc123");
  });

  it("returns null for missing or malformed headers", () => {
    expect(extractBearerKey(null)).toBeNull();
    expect(extractBearerKey("")).toBeNull();
    expect(extractBearerKey("Basic sk_spectra_abc123")).toBeNull();
  });
});
