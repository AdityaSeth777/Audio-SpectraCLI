import { describe, expect, it } from "vitest";
import {
  computeRms,
  DEFAULT_SUSTAINED_SILENCE_FRAMES,
  isClipping,
  isSilentFrame,
  nextSilenceStreak,
} from "./sessionStats";

describe("computeRms", () => {
  it("is zero for silence", () => {
    expect(computeRms(new Float32Array([0, 0, 0, 0]))).toBe(0);
  });

  it("is zero for an empty buffer", () => {
    expect(computeRms(new Float32Array([]))).toBe(0);
  });

  it("is 1 for a full-scale constant signal", () => {
    expect(computeRms(new Float32Array([1, -1, 1, -1]))).toBeCloseTo(1);
  });

  it("matches the closed-form RMS of a known signal", () => {
    const buf = new Float32Array([0.5, -0.5, 0.5, -0.5]);
    expect(computeRms(buf)).toBeCloseTo(0.5);
  });
});

describe("isClipping", () => {
  it("is false for a signal well under full scale", () => {
    expect(isClipping(new Float32Array([0.1, -0.2, 0.3]))).toBe(false);
  });

  it("is true when a sample reaches the clip threshold", () => {
    expect(isClipping(new Float32Array([0.1, 0.99, 0.2]))).toBe(true);
  });

  it("is true for a negative sample past the threshold", () => {
    expect(isClipping(new Float32Array([0.1, -0.995, 0.2]))).toBe(true);
  });

  it("respects a custom threshold", () => {
    expect(isClipping(new Float32Array([0.5]), 0.4)).toBe(true);
    expect(isClipping(new Float32Array([0.3]), 0.4)).toBe(false);
  });
});

describe("isSilentFrame", () => {
  it("flags near-zero RMS as silent", () => {
    expect(isSilentFrame(0.001)).toBe(true);
  });

  it("does not flag audible RMS as silent", () => {
    expect(isSilentFrame(0.2)).toBe(false);
  });
});

describe("nextSilenceStreak", () => {
  it("increments on consecutive silent frames", () => {
    let streak = 0;
    streak = nextSilenceStreak(streak, 0.0001);
    streak = nextSilenceStreak(streak, 0.0001);
    streak = nextSilenceStreak(streak, 0.0001);
    expect(streak).toBe(3);
  });

  it("resets as soon as a loud frame arrives", () => {
    let streak = 5;
    streak = nextSilenceStreak(streak, 0.5);
    expect(streak).toBe(0);
  });

  it("can cross the sustained-silence threshold used by the UI", () => {
    let streak = 0;
    for (let i = 0; i < DEFAULT_SUSTAINED_SILENCE_FRAMES; i++) {
      streak = nextSilenceStreak(streak, 0);
    }
    expect(streak).toBeGreaterThanOrEqual(DEFAULT_SUSTAINED_SILENCE_FRAMES);
  });
});
