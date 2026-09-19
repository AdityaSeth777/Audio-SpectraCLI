export type SpectrumFrame = {
    freqBins: number[];
    spectrum: number[];
    maxMagnitude: number;
};

export type DominantFrequency = {
    frequency: number;
    magnitude: number;
};

/**
 * Returns the frequency bin with the largest magnitude in a frame's
 * spectrum (i.e. argmax(spectrum) mapped through freqBins), or undefined
 * for an empty/mismatched frame. Used to drive the live status bar item
 * without needing the vscode module.
 */
export function computeDominantFrequency(frame: SpectrumFrame): DominantFrequency | undefined {
    const { freqBins, spectrum } = frame;
    if (spectrum.length === 0 || freqBins.length === 0) {
        return undefined;
    }

    let maxIndex = 0;
    for (let i = 1; i < spectrum.length; i++) {
        if (spectrum[i] > spectrum[maxIndex]) {
            maxIndex = i;
        }
    }

    if (maxIndex >= freqBins.length) {
        return undefined;
    }

    return { frequency: freqBins[maxIndex], magnitude: spectrum[maxIndex] };
}

/**
 * Splits a newline-delimited JSON stream chunk into complete parsed frames
 * plus whatever partial line remains buffered for the next chunk. Pulled out
 * of visualizerPanel.ts so it's testable without importing `vscode`.
 */
export function parseFrameLines(
    previousRemainder: string,
    chunk: string,
): { frames: SpectrumFrame[]; remainder: string } {
    const combined = previousRemainder + chunk;
    const lines = combined.split("\n");
    const remainder = lines.pop() ?? "";

    const frames: SpectrumFrame[] = [];
    for (const line of lines) {
        if (!line.trim()) {
            continue;
        }
        try {
            frames.push(JSON.parse(line));
        } catch {
            // Malformed/interleaved line (e.g. stray stderr text) - skip it.
        }
    }

    return { frames, remainder };
}
