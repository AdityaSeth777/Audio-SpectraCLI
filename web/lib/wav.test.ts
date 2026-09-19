import { describe, expect, it } from "vitest";
import { parseWav, UnsupportedWavError } from "./wav";

/** Builds a minimal 16-bit PCM mono WAV buffer from the given sample values (each in [-1, 1]). */
function buildWav16(sampleRate: number, samples: number[], numChannels = 1): Buffer {
  const bitsPerSample = 16;
  const bytesPerSample = bitsPerSample / 8;
  const dataSize = samples.length * bytesPerSample * numChannels;
  const buffer = Buffer.alloc(44 + dataSize);

  buffer.write("RIFF", 0, "ascii");
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write("WAVE", 8, "ascii");

  buffer.write("fmt ", 12, "ascii");
  buffer.writeUInt32LE(16, 16); // fmt chunk size
  buffer.writeUInt16LE(1, 20); // audio format: PCM
  buffer.writeUInt16LE(numChannels, 22);
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * numChannels * bytesPerSample, 28); // byte rate
  buffer.writeUInt16LE(numChannels * bytesPerSample, 32); // block align
  buffer.writeUInt16LE(bitsPerSample, 34);

  buffer.write("data", 36, "ascii");
  buffer.writeUInt32LE(dataSize, 40);

  let offset = 44;
  for (const sample of samples) {
    for (let channel = 0; channel < numChannels; channel++) {
      buffer.writeInt16LE(Math.round(sample * 32767), offset);
      offset += 2;
    }
  }

  return buffer;
}

describe("parseWav", () => {
  it("extracts sample rate and normalized samples from a mono 16-bit WAV", () => {
    const wav = buildWav16(22050, [0, 0.5, -0.5, 1, -1]);
    const decoded = parseWav(wav);
    expect(decoded.sampleRate).toBe(22050);
    expect(decoded.samples.length).toBe(5);
    expect(decoded.samples[0]).toBeCloseTo(0, 3);
    expect(decoded.samples[1]).toBeCloseTo(0.5, 3);
    expect(decoded.samples[3]).toBeCloseTo(1, 3);
  });

  it("averages channels down to mono for a stereo WAV", () => {
    // Left channel all 1.0, right channel all -1.0 -> average should be ~0.
    const bitsPerSample = 16;
    const numChannels = 2;
    const frames = 4;
    const buffer = Buffer.alloc(44 + frames * numChannels * (bitsPerSample / 8));
    buffer.write("RIFF", 0, "ascii");
    buffer.writeUInt32LE(buffer.length - 8, 4);
    buffer.write("WAVE", 8, "ascii");
    buffer.write("fmt ", 12, "ascii");
    buffer.writeUInt32LE(16, 16);
    buffer.writeUInt16LE(1, 20);
    buffer.writeUInt16LE(numChannels, 22);
    buffer.writeUInt32LE(44100, 24);
    buffer.writeUInt32LE(44100 * numChannels * 2, 28);
    buffer.writeUInt16LE(numChannels * 2, 32);
    buffer.writeUInt16LE(bitsPerSample, 34);
    buffer.write("data", 36, "ascii");
    buffer.writeUInt32LE(frames * numChannels * 2, 40);

    let offset = 44;
    for (let i = 0; i < frames; i++) {
      buffer.writeInt16LE(32767, offset);
      buffer.writeInt16LE(-32767, offset + 2);
      offset += 4;
    }

    const decoded = parseWav(buffer);
    expect(decoded.samples.length).toBe(frames);
    for (const sample of decoded.samples) {
      expect(sample).toBeCloseTo(0, 2);
    }
  });

  it("rejects a non-WAV buffer", () => {
    const notWav = Buffer.from("this is not a wav file, just some plain text padding to be long enough");
    expect(() => parseWav(notWav)).toThrow(UnsupportedWavError);
  });
});
