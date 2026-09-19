import { describe, expect, it } from "vitest";
import {
  binToFrequency,
  dbToUnitRange,
  findDominantBin,
  frequencyToBin,
  movingAverage,
} from "./dsp";

describe("movingAverage", () => {
  it("returns the input unchanged for a window smaller than 2", () => {
    const input = new Float32Array([1, 2, 3]);
    expect(Array.from(movingAverage(input, 1))).toEqual([1, 2, 3]);
  });

  it("smooths a spike toward its neighbors", () => {
    const input = new Float32Array([0, 0, 10, 0, 0]);
    const result = movingAverage(input, 3);
    expect(result[2]).toBeLessThan(10);
    expect(result[2]).toBeGreaterThan(0);
  });
});

describe("dbToUnitRange", () => {
  it("clamps and normalizes to 0..1", () => {
    expect(dbToUnitRange(-100)).toBeCloseTo(0);
    expect(dbToUnitRange(-30)).toBeCloseTo(1);
    expect(dbToUnitRange(-200)).toBeCloseTo(0);
    expect(dbToUnitRange(0)).toBeCloseTo(1);
  });
});

describe("bin <-> frequency mapping", () => {
  it("round-trips for a standard 44.1kHz/2048 setup", () => {
    const sampleRate = 44100;
    const fftSize = 2048;
    const freq = 440; // A4
    const bin = frequencyToBin(freq, sampleRate, fftSize);
    const backToFreq = binToFrequency(bin, sampleRate, fftSize);
    // Bin resolution here is ~21.5Hz (sampleRate / fftSize), so allow one bin's worth of error.
    const binResolution = sampleRate / fftSize;
    expect(Math.abs(backToFreq - freq)).toBeLessThanOrEqual(binResolution);
  });
});

describe("findDominantBin", () => {
  it("finds the loudest bin within the given frequency range", () => {
    const sampleRate = 44100;
    const fftSize = 2048;
    const magnitudes = new Float32Array(fftSize / 2 + 1).fill(-100);
    const targetBin = frequencyToBin(1000, sampleRate, fftSize);
    magnitudes[targetBin] = -10;

    const result = findDominantBin(magnitudes, sampleRate, fftSize, 20, 20000);
    expect(result.binIndex).toBe(targetBin);
    expect(result.magnitude).toBe(-10);
  });
});
