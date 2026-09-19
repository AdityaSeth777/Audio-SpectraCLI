/**
 * Minimal parser for uncompressed PCM WAV files (16-bit int or 32-bit float).
 * Deliberately scoped to WAV only for the API's v1 - decoding MP3/AAC/etc.
 * server-side needs a real codec (ffmpeg or similar), which is a bigger,
 * separate piece of work than this API's first release covers.
 */

export class UnsupportedWavError extends Error { }

export type DecodedAudio = {
  sampleRate: number;
  samples: Float32Array; // mono, channels averaged down if the file is multi-channel
};

function findChunk(buffer: Buffer, chunkId: string, searchFrom: number): { offset: number; size: number } | null {
  let offset = searchFrom;
  while (offset + 8 <= buffer.length) {
    const id = buffer.toString("ascii", offset, offset + 4);
    const size = buffer.readUInt32LE(offset + 4);
    if (id === chunkId) {
      return { offset: offset + 8, size };
    }
    offset += 8 + size + (size % 2); // chunks are word-aligned
  }
  return null;
}

export function parseWav(buffer: Buffer): DecodedAudio {
  if (buffer.length < 44 || buffer.toString("ascii", 0, 4) !== "RIFF" || buffer.toString("ascii", 8, 12) !== "WAVE") {
    throw new UnsupportedWavError("Not a valid WAV file (missing RIFF/WAVE header).");
  }

  const fmtChunk = findChunk(buffer, "fmt ", 12);
  if (!fmtChunk) throw new UnsupportedWavError("WAV file has no fmt chunk.");

  const audioFormat = buffer.readUInt16LE(fmtChunk.offset);
  const numChannels = buffer.readUInt16LE(fmtChunk.offset + 2);
  const sampleRate = buffer.readUInt32LE(fmtChunk.offset + 4);
  const bitsPerSample = buffer.readUInt16LE(fmtChunk.offset + 14);

  if (audioFormat !== 1 && audioFormat !== 3) {
    throw new UnsupportedWavError(`Unsupported WAV audio format code ${audioFormat} (only PCM/IEEE float supported).`);
  }
  if (bitsPerSample !== 16 && bitsPerSample !== 32) {
    throw new UnsupportedWavError(`Unsupported bit depth ${bitsPerSample} (only 16-bit PCM or 32-bit float supported).`);
  }

  const dataChunk = findChunk(buffer, "data", 12);
  if (!dataChunk) throw new UnsupportedWavError("WAV file has no data chunk.");

  const bytesPerSample = bitsPerSample / 8;
  const frameCount = Math.floor(dataChunk.size / (bytesPerSample * numChannels));
  const mono = new Float32Array(frameCount);

  for (let frame = 0; frame < frameCount; frame++) {
    let sum = 0;
    for (let channel = 0; channel < numChannels; channel++) {
      const sampleOffset = dataChunk.offset + (frame * numChannels + channel) * bytesPerSample;
      if (bitsPerSample === 16) {
        sum += buffer.readInt16LE(sampleOffset) / 32768;
      } else {
        sum += buffer.readFloatLE(sampleOffset);
      }
    }
    mono[frame] = sum / numChannels;
  }

  return { sampleRate, samples: mono };
}
