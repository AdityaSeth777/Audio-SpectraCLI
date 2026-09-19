/**
 * A minimal iterative radix-2 Cooley-Tukey FFT, written from scratch because
 * the analysis API runs server-side (Node), where there's no AnalyserNode
 * (browser-only) and no numpy (Python-only) to lean on. Real-valued input
 * only, power-of-two length required by the caller.
 */

export function isPowerOfTwo(n: number): boolean {
  return n > 0 && (n & (n - 1)) === 0;
}

export function nextPowerOfTwo(n: number): number {
  let p = 1;
  while (p < n) p *= 2;
  return p;
}

/** Hann window - reduces spectral leakage from analyzing a finite-length block. */
export function applyHannWindow(samples: Float32Array): Float32Array {
  const n = samples.length;
  const windowed = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const w = 0.5 * (1 - Math.cos((2 * Math.PI * i) / (n - 1)));
    windowed[i] = samples[i] * w;
  }
  return windowed;
}

/** In-place iterative radix-2 FFT over parallel real/imaginary arrays. Length must be a power of two. */
function fftInPlace(real: Float64Array, imag: Float64Array): void {
  const n = real.length;
  if (!isPowerOfTwo(n)) {
    throw new Error(`fftInPlace requires a power-of-two length, got ${n}`);
  }

  // Bit-reversal permutation.
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) {
      j ^= bit;
    }
    j ^= bit;
    if (i < j) {
      [real[i], real[j]] = [real[j], real[i]];
      [imag[i], imag[j]] = [imag[j], imag[i]];
    }
  }

  // Iterative butterfly.
  for (let len = 2; len <= n; len <<= 1) {
    const angleStep = (-2 * Math.PI) / len;
    const wReal = Math.cos(angleStep);
    const wImag = Math.sin(angleStep);
    for (let start = 0; start < n; start += len) {
      let curReal = 1;
      let curImag = 0;
      for (let k = 0; k < len / 2; k++) {
        const evenIndex = start + k;
        const oddIndex = start + k + len / 2;

        const oddReal = real[oddIndex] * curReal - imag[oddIndex] * curImag;
        const oddImag = real[oddIndex] * curImag + imag[oddIndex] * curReal;

        real[oddIndex] = real[evenIndex] - oddReal;
        imag[oddIndex] = imag[evenIndex] - oddImag;
        real[evenIndex] += oddReal;
        imag[evenIndex] += oddImag;

        const nextReal = curReal * wReal - curImag * wImag;
        const nextImag = curReal * wImag + curImag * wReal;
        curReal = nextReal;
        curImag = nextImag;
      }
    }
  }
}

/**
 * Computes the magnitude spectrum of real-valued `samples` (like numpy's
 * `np.abs(np.fft.rfft(...))`). `samples.length` must be a power of two -
 * pad or truncate before calling. Returns `samples.length / 2 + 1` bins.
 */
export function rfftMagnitude(samples: Float32Array): Float64Array {
  const n = samples.length;
  const real = Float64Array.from(samples);
  const imag = new Float64Array(n);
  fftInPlace(real, imag);

  const numBins = n / 2 + 1;
  const magnitudes = new Float64Array(numBins);
  for (let i = 0; i < numBins; i++) {
    magnitudes[i] = Math.hypot(real[i], imag[i]);
  }
  return magnitudes;
}
