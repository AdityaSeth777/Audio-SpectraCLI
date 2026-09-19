import { spawn } from "child_process";
import ffmpegPath from "ffmpeg-static";
import { describe, expect, it } from "vitest";
import { transcodeToMono16BitPcm } from "./transcode";
import { applyHannWindow, nextPowerOfTwo, rfftMagnitude } from "./fft";
import { findDominantBin } from "./dsp";

/** Builds a real MP3 fixture (a pure tone) using the same bundled ffmpeg binary under test. */
function buildToneMp3(frequencyHz: number, durationSeconds = 1): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    if (!ffmpegPath) return reject(new Error("ffmpeg-static did not resolve a binary."));

    const ffmpeg = spawn(ffmpegPath, [
      "-hide_banner",
      "-loglevel",
      "error",
      "-f",
      "lavfi",
      "-i",
      `sine=frequency=${frequencyHz}:duration=${durationSeconds}`,
      "-ar",
      "44100",
      "-f",
      "mp3",
      "pipe:1",
    ]);

    const chunks: Buffer[] = [];
    ffmpeg.stdout.on("data", (chunk: Buffer) => chunks.push(chunk));
    ffmpeg.on("error", reject);
    ffmpeg.on("close", (code) => {
      if (code !== 0) reject(new Error(`ffmpeg exited with code ${code}`));
      else resolve(Buffer.concat(chunks));
    });
  });
}

describe("transcodeToMono16BitPcm", () => {
  it("decodes a real MP3 tone to PCM whose FFT peak matches the injected frequency", async () => {
    const mp3Bytes = await buildToneMp3(440);
    const decoded = await transcodeToMono16BitPcm(mp3Bytes);

    expect(decoded.sampleRate).toBe(44100);
    expect(decoded.samples.length).toBeGreaterThan(1000);

    const analysisSlice = decoded.samples.subarray(0, 8192);
    const windowed = applyHannWindow(analysisSlice);
    const fftSize = nextPowerOfTwo(windowed.length);
    const padded = new Float32Array(fftSize);
    padded.set(windowed);

    const magnitudes = rfftMagnitude(padded);
    const dominant = findDominantBin(Float32Array.from(magnitudes), decoded.sampleRate, fftSize);

    const binResolution = decoded.sampleRate / fftSize;
    expect(Math.abs(dominant.frequencyHz - 440)).toBeLessThanOrEqual(binResolution);
  }, 15_000);

  it("rejects garbage input instead of hanging", async () => {
    await expect(transcodeToMono16BitPcm(Buffer.from("not audio data"))).rejects.toThrow();
  }, 15_000);
});
