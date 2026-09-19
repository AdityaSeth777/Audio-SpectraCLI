import { describe, expect, it } from "vitest";
import { applyHannWindow, isPowerOfTwo, nextPowerOfTwo, rfftMagnitude } from "./fft";

describe("isPowerOfTwo / nextPowerOfTwo", () => {
  it("identifies powers of two", () => {
    expect(isPowerOfTwo(1)).toBe(true);
    expect(isPowerOfTwo(2)).toBe(true);
    expect(isPowerOfTwo(1024)).toBe(true);
    expect(isPowerOfTwo(0)).toBe(false);
    expect(isPowerOfTwo(3)).toBe(false);
  });

  it("rounds up to the next power of two", () => {
    expect(nextPowerOfTwo(1)).toBe(1);
    expect(nextPowerOfTwo(5)).toBe(8);
    expect(nextPowerOfTwo(1024)).toBe(1024);
    expect(nextPowerOfTwo(1025)).toBe(2048);
  });
});

describe("applyHannWindow", () => {
  it("tapers the first and last samples toward zero", () => {
    const flat = new Float32Array(8).fill(1);
    const windowed = applyHannWindow(flat);
    expect(windowed[0]).toBeCloseTo(0, 5);
    expect(windowed[windowed.length - 1]).toBeCloseTo(0, 5);
    expect(windowed[Math.floor(windowed.length / 2)]).toBeGreaterThan(0.9);
  });
});

describe("rfftMagnitude", () => {
  it("puts the peak at the bin matching a pure sine tone's frequency", () => {
    const sampleRate = 8192;
    const fftSize = 1024;
    const toneHz = 1000; // falls near bin (toneHz / sampleRate) * fftSize = 125
    const samples = new Float32Array(fftSize);
    for (let i = 0; i < fftSize; i++) {
      samples[i] = Math.sin((2 * Math.PI * toneHz * i) / sampleRate);
    }

    const magnitudes = rfftMagnitude(samples);
    expect(magnitudes.length).toBe(fftSize / 2 + 1);

    let peakBin = 0;
    for (let i = 1; i < magnitudes.length; i++) {
      if (magnitudes[i] > magnitudes[peakBin]) peakBin = i;
    }
    const expectedBin = Math.round((toneHz * fftSize) / sampleRate);
    expect(peakBin).toBe(expectedBin);
  });

  it("returns near-zero magnitude for silence", () => {
    const silence = new Float32Array(64);
    const magnitudes = rfftMagnitude(silence);
    for (const m of magnitudes) {
      expect(m).toBeCloseTo(0, 5);
    }
  });

  it("throws for a non-power-of-two length", () => {
    expect(() => rfftMagnitude(new Float32Array(100))).toThrow();
  });
});
