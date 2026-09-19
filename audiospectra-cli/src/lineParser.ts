export type SpectrumFrame = {
    freqBins: number[];
    spectrum: number[];
    maxMagnitude: number;
};

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
        if (!line.trim()) continue;
        try {
            frames.push(JSON.parse(line));
        } catch {
            // Malformed/interleaved line (e.g. stray stderr text) - skip it.
        }
    }

    return { frames, remainder };
}
