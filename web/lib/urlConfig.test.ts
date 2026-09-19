import { describe, expect, it } from "vitest";
import { decodeSettingsFromParams, encodeSettingsToParams } from "./urlConfig";
import { DEFAULT_SETTINGS } from "@/components/Visualizer";

describe("encodeSettingsToParams / decodeSettingsFromParams", () => {
  it("round-trips the default settings", () => {
    const params = encodeSettingsToParams(DEFAULT_SETTINGS);
    const decoded = decodeSettingsFromParams(params, DEFAULT_SETTINGS);
    expect(decoded).toEqual(DEFAULT_SETTINGS);
  });

  it("round-trips a non-default configuration", () => {
    const settings = {
      sampleRate: 48000,
      fftSize: 4096,
      frequencyRange: [50, 8000] as [number, number],
      color: "#ff00aa",
      viewMode: "waterfall" as const,
    };
    const decoded = decodeSettingsFromParams(encodeSettingsToParams(settings), DEFAULT_SETTINGS);
    expect(decoded).toEqual(settings);
  });

  it("falls back field-by-field for missing params", () => {
    const params = new URLSearchParams("viewMode=tuner");
    const decoded = decodeSettingsFromParams(params, DEFAULT_SETTINGS);
    expect(decoded.viewMode).toBe("tuner");
    expect(decoded.sampleRate).toBe(DEFAULT_SETTINGS.sampleRate);
    expect(decoded.color).toBe(DEFAULT_SETTINGS.color);
  });

  it("ignores an invalid viewMode and falls back", () => {
    const params = new URLSearchParams("viewMode=not-a-real-mode");
    const decoded = decodeSettingsFromParams(params, DEFAULT_SETTINGS);
    expect(decoded.viewMode).toBe(DEFAULT_SETTINGS.viewMode);
  });

  it("ignores a malformed color and falls back", () => {
    const params = new URLSearchParams("color=javascript:alert(1)");
    const decoded = decodeSettingsFromParams(params, DEFAULT_SETTINGS);
    expect(decoded.color).toBe(DEFAULT_SETTINGS.color);
  });

  it("ignores a nonsensical frequency range (min >= max) and falls back", () => {
    const params = new URLSearchParams("minHz=5000&maxHz=100");
    const decoded = decodeSettingsFromParams(params, DEFAULT_SETTINGS);
    expect(decoded.frequencyRange).toEqual(DEFAULT_SETTINGS.frequencyRange);
  });

  it("ignores non-numeric sampleRate/fftSize and falls back", () => {
    const params = new URLSearchParams("sampleRate=abc&fftSize=");
    const decoded = decodeSettingsFromParams(params, DEFAULT_SETTINGS);
    expect(decoded.sampleRate).toBe(DEFAULT_SETTINGS.sampleRate);
    expect(decoded.fftSize).toBe(DEFAULT_SETTINGS.fftSize);
  });

  it("handles a completely empty query string", () => {
    const decoded = decodeSettingsFromParams(new URLSearchParams(""), DEFAULT_SETTINGS);
    expect(decoded).toEqual(DEFAULT_SETTINGS);
  });
});
