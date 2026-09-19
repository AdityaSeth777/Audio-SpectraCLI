/**
 * Pure, portable DSP helpers for the web visualizer.
 *
 * These mirror the approach in the Python CLI (Audio_SpectraCLI/main.py) as a
 * parallel spec, not shared code: a moving-average smoother stands in for the
 * CLI's Gaussian filter (simpler to run per-frame in a browser render loop),
 * and dB conversion follows the standard Web Audio convention.
 */

/** Smooths a magnitude/dB array with a simple centered moving average. */
export function movingAverage(values: Float32Array, windowSize: number): Float32Array {
  if (windowSize < 2) return values.slice();
  const half = Math.floor(windowSize / 2);
  const out = new Float32Array(values.length);
  for (let i = 0; i < values.length; i++) {
    let sum = 0;
    let count = 0;
    for (let j = Math.max(0, i - half); j <= Math.min(values.length - 1, i + half); j++) {
      sum += values[j];
      count++;
    }
    out[i] = sum / count;
  }
  return out;
}

/**
 * AnalyserNode.getFloatFrequencyData returns dB values already (typically
 * -100..0). This clamps and normalizes them to 0..1 for canvas rendering.
 */
export function dbToUnitRange(dbValue: number, minDb = -100, maxDb = -30): number {
  const clamped = Math.min(maxDb, Math.max(minDb, dbValue));
  return (clamped - minDb) / (maxDb - minDb);
}

/** Converts a linear FFT magnitude to dB (20*log10), matching the convention AnalyserNode uses. */
export function magnitudeToDb(magnitude: number, reference = 1): number {
  return 20 * Math.log10(Math.max(magnitude, 1e-12) / reference);
}

/** Reduces an array to `numBars` points by taking the max within each group - mirrors headless.py's downsampler. */
export function downsampleMaxPool(values: ArrayLike<number>, numBars: number): number[] {
  if (values.length <= numBars) return Array.from(values);
  const edges = Array.from({ length: numBars + 1 }, (_, i) => Math.floor((i * values.length) / numBars));
  const result: number[] = [];
  for (let i = 0; i < numBars; i++) {
    let max = -Infinity;
    for (let j = edges[i]; j < edges[i + 1]; j++) {
      if (values[j] > max) max = values[j];
    }
    result.push(max);
  }
  return result;
}

/** Maps an FFT bin index to its center frequency in Hz. */
export function binToFrequency(binIndex: number, sampleRate: number, fftSize: number): number {
  return (binIndex * sampleRate) / fftSize;
}

/** Maps a frequency in Hz to the nearest FFT bin index. */
export function frequencyToBin(frequencyHz: number, sampleRate: number, fftSize: number): number {
  return Math.round((frequencyHz * fftSize) / sampleRate);
}

/** Finds the bin with the highest magnitude within [minHz, maxHz] - used for tuner/pitch mode. */
export function findDominantBin(
  magnitudes: Float32Array,
  sampleRate: number,
  fftSize: number,
  minHz = 20,
  maxHz = 20000,
): { binIndex: number; frequencyHz: number; magnitude: number } {
  const startBin = Math.max(0, frequencyToBin(minHz, sampleRate, fftSize));
  const endBin = Math.min(magnitudes.length - 1, frequencyToBin(maxHz, sampleRate, fftSize));

  let bestBin = startBin;
  let bestMagnitude = -Infinity;
  for (let i = startBin; i <= endBin; i++) {
    if (magnitudes[i] > bestMagnitude) {
      bestMagnitude = magnitudes[i];
      bestBin = i;
    }
  }

  return {
    binIndex: bestBin,
    frequencyHz: binToFrequency(bestBin, sampleRate, fftSize),
    magnitude: bestMagnitude,
  };
}
