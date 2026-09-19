import { spawn } from "child_process";
import ffmpegPath from "ffmpeg-static";
import type { DecodedAudio } from "./wav";

export class TranscodeError extends Error {}

const OUTPUT_SAMPLE_RATE = 44100;

/**
 * Decodes compressed audio (MP3, AAC, OGG, ...) to mono PCM via a bundled
 * static ffmpeg binary (ffmpeg-static) — there's no pure-JS/WASM MP3/AAC
 * decoder worth trusting for this, and ffmpeg is the standard tool for it.
 * Chosen over relying on a system `ffmpeg` install specifically so this
 * works out of the box on Vercel Node.js functions (adds ~80MB to the
 * function bundle in exchange for zero host setup).
 */
export function transcodeToMono16BitPcm(inputBytes: Buffer): Promise<DecodedAudio> {
  return new Promise((resolve, reject) => {
    if (!ffmpegPath) {
      reject(new TranscodeError("ffmpeg-static did not resolve a binary for this platform."));
      return;
    }

    const ffmpeg = spawn(ffmpegPath, [
      "-hide_banner",
      "-loglevel",
      "error",
      "-i",
      "pipe:0", // read the compressed input from stdin
      "-f",
      "s16le", // raw signed 16-bit little-endian PCM
      "-ac",
      "1", // downmix to mono
      "-ar",
      String(OUTPUT_SAMPLE_RATE),
      "pipe:1", // write raw PCM to stdout
    ]);

    const outputChunks: Buffer[] = [];
    const stderrChunks: Buffer[] = [];

    ffmpeg.stdout.on("data", (chunk: Buffer) => outputChunks.push(chunk));
    ffmpeg.stderr.on("data", (chunk: Buffer) => stderrChunks.push(chunk));

    ffmpeg.on("error", (err) => {
      reject(new TranscodeError(`Failed to start ffmpeg: ${err.message}`));
    });

    ffmpeg.on("close", (code) => {
      if (code !== 0) {
        reject(new TranscodeError(`ffmpeg exited with code ${code}: ${Buffer.concat(stderrChunks).toString()}`));
        return;
      }

      const pcmBuffer = Buffer.concat(outputChunks);
      const samples = new Float32Array(pcmBuffer.length / 2);
      for (let i = 0; i < samples.length; i++) {
        samples[i] = pcmBuffer.readInt16LE(i * 2) / 32768;
      }

      resolve({ sampleRate: OUTPUT_SAMPLE_RATE, samples });
    });

    ffmpeg.stdin.on("error", () => {
      // Writing to stdin after ffmpeg has exited (e.g. it rejected the input
      // as an unrecognized format) throws EPIPE — the 'close' handler above
      // still fires with a non-zero code and reports the real error.
    });
    ffmpeg.stdin.write(inputBytes);
    ffmpeg.stdin.end();
  });
}
