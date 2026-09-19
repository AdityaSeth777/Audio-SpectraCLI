"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { dbToUnitRange, findDominantBin, movingAverage } from "@/lib/dsp";

type ViewMode = "bars" | "waterfall" | "tuner";

export type VisualizerSettings = {
  sampleRate: number; // Hz, mirrors the CLI's `fs`
  fftSize: number; // power of 2, mirrors the CLI's `block_size`
  frequencyRange: [number, number];
  color: string;
  viewMode: ViewMode;
};

export const DEFAULT_SETTINGS: VisualizerSettings = {
  sampleRate: 44100,
  fftSize: 2048,
  frequencyRange: [20, 20000],
  color: "#3b82f6",
  viewMode: "bars",
};

const WATERFALL_HISTORY_ROWS = 120;

export function Visualizer({ isPaid }: { isPaid: boolean }) {
  const [settings, setSettings] = useState<VisualizerSettings>(DEFAULT_SETTINGS);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dominantFrequency, setDominantFrequency] = useState<number | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const waterfallHistoryRef = useRef<Float32Array[]>([]);
  const drawRef = useRef<() => void>(() => {});
  const tickRef = useRef<() => void>(() => {});

  const effectiveViewMode: ViewMode = isPaid ? settings.viewMode : "bars";

  const stop = useCallback(() => {
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    audioContextRef.current?.close();
    audioContextRef.current = null;
    analyserRef.current = null;
    waterfallHistoryRef.current = [];
    setRunning(false);
  }, []);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !analyser || !ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const rawDb = new Float32Array(bufferLength);
    analyser.getFloatFrequencyData(rawDb);
    const smoothed = movingAverage(rawDb, 3);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (effectiveViewMode === "bars") {
      const barWidth = canvas.width / bufferLength;
      for (let i = 0; i < bufferLength; i++) {
        const unit = dbToUnitRange(smoothed[i]);
        const barHeight = unit * canvas.height;
        ctx.fillStyle = settings.color;
        ctx.fillRect(i * barWidth, canvas.height - barHeight, barWidth, barHeight);
      }
    } else if (effectiveViewMode === "waterfall") {
      waterfallHistoryRef.current.push(smoothed);
      if (waterfallHistoryRef.current.length > WATERFALL_HISTORY_ROWS) {
        waterfallHistoryRef.current.shift();
      }
      const rows = waterfallHistoryRef.current;
      const rowHeight = canvas.height / WATERFALL_HISTORY_ROWS;
      const colWidth = canvas.width / bufferLength;
      rows.forEach((row, rowIndex) => {
        for (let i = 0; i < row.length; i++) {
          const unit = dbToUnitRange(row[i]);
          ctx.fillStyle = `rgba(59, 130, 246, ${unit})`;
          ctx.fillRect(i * colWidth, canvas.height - (rowIndex + 1) * rowHeight, colWidth, rowHeight);
        }
      });
    } else if (effectiveViewMode === "tuner") {
      const dominant = findDominantBin(
        smoothed,
        settings.sampleRate,
        settings.fftSize,
        settings.frequencyRange[0],
        settings.frequencyRange[1],
      );
      setDominantFrequency(dominant.frequencyHz);
      ctx.font = "48px sans-serif";
      ctx.fillStyle = settings.color;
      ctx.textAlign = "center";
      ctx.fillText(`${dominant.frequencyHz.toFixed(1)} Hz`, canvas.width / 2, canvas.height / 2);
    }

  }, [effectiveViewMode, settings.color, settings.sampleRate, settings.fftSize, settings.frequencyRange]);

  useEffect(() => {
    drawRef.current = draw;
  }, [draw]);

  useEffect(() => {
    tickRef.current = () => {
      drawRef.current();
      animationFrameRef.current = requestAnimationFrame(() => tickRef.current());
    };
  }, []);

  const start = useCallback(async () => {
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Microphone access isn't supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const audioContext = new AudioContext({ sampleRate: settings.sampleRate });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = settings.fftSize;
      analyser.smoothingTimeConstant = 0.6;
      source.connect(analyser);
      analyserRef.current = analyser;

      setRunning(true);
      animationFrameRef.current = requestAnimationFrame(() => tickRef.current());
    } catch {
      setError("Microphone permission was denied. Allow access and try again.");
    }
  }, [settings.sampleRate, settings.fftSize]);

  const exportPng = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement("a");
    link.download = "spectrum.png";
    link.href = canvas.toDataURL("image/png");
    link.click();
  }, []);

  useEffect(() => stop, [stop]);

  return (
    <div className="flex flex-col gap-4">
      <canvas ref={canvasRef} width={800} height={400} className="w-full rounded border border-white/10 bg-black" />

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={running ? stop : start}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          {running ? "Stop" : "Start Visualization"}
        </button>

        {isPaid && (
          <>
            <select
              value={settings.viewMode}
              onChange={(e) => setSettings((s) => ({ ...s, viewMode: e.target.value as ViewMode }))}
              className="rounded border border-white/20 bg-transparent px-2 py-2"
            >
              <option value="bars">Bars</option>
              <option value="waterfall">Waterfall</option>
              <option value="tuner">Tuner</option>
            </select>
            <button onClick={exportPng} className="rounded border border-white/20 px-4 py-2 hover:bg-white/10">
              Export PNG
            </button>
          </>
        )}

        {!isPaid && (
          <span className="text-sm text-white/60">
            Waterfall, tuner mode, and export are available on the paid plan.
          </span>
        )}
      </div>

      {effectiveViewMode === "tuner" && dominantFrequency !== null && (
        <p className="text-sm text-white/60">Dominant frequency: {dominantFrequency.toFixed(1)} Hz</p>
      )}
    </div>
  );
}
