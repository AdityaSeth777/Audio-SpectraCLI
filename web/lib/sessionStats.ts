/**
 * Pure math for the client-side session stats panel (RMS loudness, and
 * clip/silence detection) driven from the same per-frame time-domain buffer
 * the visualizer's AnalyserNode already produces - no second audio analysis
 * path is introduced.
 */

/** Root-mean-square loudness of a time-domain buffer (samples in -1..1). */
export function computeRms(timeDomain: Float32Array): number {
  if (timeDomain.length === 0) return 0;
  let sumSquares = 0;
  for (let i = 0; i < timeDomain.length; i++) {
    sumSquares += timeDomain[i] * timeDomain[i];
  }
  return Math.sqrt(sumSquares / timeDomain.length);
}

/** True if any sample in the buffer is at/near full scale (clipping). */
export function isClipping(timeDomain: Float32Array, threshold = 0.98): boolean {
  for (let i = 0; i < timeDomain.length; i++) {
    if (Math.abs(timeDomain[i]) >= threshold) return true;
  }
  return false;
}

/** True if the given RMS is at/near zero for a single frame. */
export function isSilentFrame(rms: number, threshold = 0.01): boolean {
  return rms <= threshold;
}

/**
 * Tracks consecutive silent frames and reports sustained silence once a
 * frame-count threshold is crossed. Kept as a small stateful helper (rather
 * than a class) so the caller can hold the counter in a ref across
 * animation frames without re-allocating anything.
 */
export function nextSilenceStreak(previousStreak: number, rms: number, silenceRmsThreshold = 0.01): number {
  return isSilentFrame(rms, silenceRmsThreshold) ? previousStreak + 1 : 0;
}

export const DEFAULT_SUSTAINED_SILENCE_FRAMES = 60; // ~1s at 60fps
