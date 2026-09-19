/**
 * Encodes/decodes VisualizerSettings to and from URL query params, for the
 * "Copy Share Link" feature on /visualize. Pure functions only - the
 * component owns debouncing (`history.replaceState`) and reading
 * `window.location`.
 */
import type { VisualizerSettings } from "@/components/Visualizer";

const VIEW_MODES = ["bars", "waterfall", "tuner"] as const;

function isViewMode(value: string | null): value is VisualizerSettings["viewMode"] {
  return VIEW_MODES.includes(value as VisualizerSettings["viewMode"]);
}

function isHexColor(value: string): boolean {
  return /^#[0-9a-fA-F]{3,8}$/.test(value);
}

/** Serializes settings into a URLSearchParams instance. */
export function encodeSettingsToParams(settings: VisualizerSettings): URLSearchParams {
  const params = new URLSearchParams();
  params.set("sampleRate", String(settings.sampleRate));
  params.set("fftSize", String(settings.fftSize));
  params.set("minHz", String(settings.frequencyRange[0]));
  params.set("maxHz", String(settings.frequencyRange[1]));
  params.set("color", settings.color);
  params.set("viewMode", settings.viewMode);
  return params;
}

/**
 * Parses settings out of URLSearchParams, falling back to `fallback` field
 * by field for anything missing or invalid - a malformed/partial/hand-edited
 * URL should never crash or produce nonsensical settings.
 */
export function decodeSettingsFromParams(
  params: URLSearchParams,
  fallback: VisualizerSettings,
): VisualizerSettings {
  const sampleRate = Number(params.get("sampleRate"));
  const fftSize = Number(params.get("fftSize"));
  const minHz = Number(params.get("minHz"));
  const maxHz = Number(params.get("maxHz"));
  const color = params.get("color");
  const viewMode = params.get("viewMode");

  return {
    sampleRate: Number.isFinite(sampleRate) && sampleRate > 0 ? sampleRate : fallback.sampleRate,
    fftSize: Number.isFinite(fftSize) && fftSize > 0 ? fftSize : fallback.fftSize,
    frequencyRange:
      Number.isFinite(minHz) && Number.isFinite(maxHz) && minHz >= 0 && maxHz > minHz
        ? [minHz, maxHz]
        : fallback.frequencyRange,
    color: color && isHexColor(color) ? color : fallback.color,
    viewMode: isViewMode(viewMode) ? viewMode : fallback.viewMode,
  };
}
