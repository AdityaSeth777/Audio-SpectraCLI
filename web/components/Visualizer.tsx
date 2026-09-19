"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { dbToUnitRange, findDominantBin, movingAverage } from "@/lib/dsp";
import {
  createLocalPreset,
  deleteLocalPreset,
  listLocalPresets,
  renameLocalPreset,
  type LocalPreset,
} from "@/lib/localPresets";
import {
  computeRms,
  DEFAULT_SUSTAINED_SILENCE_FRAMES,
  isClipping,
  nextSilenceStreak,
} from "@/lib/sessionStats";
import { decodeSettingsFromParams, encodeSettingsToParams } from "@/lib/urlConfig";

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
const FREQUENCY_HISTORY_LENGTH = 150; // ~2.5s of sparkline at 60fps
const STATS_UI_UPDATE_EVERY_N_FRAMES = 6; // throttle React re-renders for the readouts
const URL_SYNC_DEBOUNCE_MS = 400;

type SavedPreset = { id: string; name: string; settings: VisualizerSettings };

type SessionStats = {
  rms: number;
  clipping: boolean;
  sustainedSilence: boolean;
};

/**
 * Draws the dominant-frequency history as a small sparkline directly onto
 * its own canvas, imperatively - like the main visualizer canvas, this is
 * updated every animation frame without going through React state, since
 * that would mean a re-render at up to 60fps.
 */
function drawStatsSparkline(canvas: HTMLCanvasElement | null, history: number[], color: string): void {
  const ctx = canvas?.getContext("2d");
  if (!canvas || !ctx || history.length === 0) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  let max = -Infinity;
  let min = Infinity;
  for (const value of history) {
    if (value > max) max = value;
    if (value < min) min = value;
  }
  const range = max - min || 1;

  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  const stepX = canvas.width / Math.max(1, FREQUENCY_HISTORY_LENGTH - 1);
  history.forEach((value, i) => {
    const x = i * stepX;
    const unit = (value - min) / range;
    const y = canvas.height - unit * canvas.height;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

export function Visualizer({ isPaid }: { isPaid: boolean }) {
  const [settings, setSettings] = useState<VisualizerSettings>(DEFAULT_SETTINGS);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dominantFrequency, setDominantFrequency] = useState<number | null>(null);
  const [presets, setPresets] = useState<SavedPreset[]>([]);
  const [newPresetName, setNewPresetName] = useState("");

  // Local (localStorage-backed) presets - available to everyone, no sign-in
  // or paid plan required. Kept entirely separate from the DB-backed
  // `presets`/`newPresetName` state above.
  const [localPresets, setLocalPresets] = useState<LocalPreset[]>([]);
  const [newLocalPresetName, setNewLocalPresetName] = useState("");
  const [editingLocalPresetId, setEditingLocalPresetId] = useState<string | null>(null);
  const [editingLocalPresetName, setEditingLocalPresetName] = useState("");

  // Client-side session stats (RMS/clip/silence), computed from data the
  // draw loop already reads off the AnalyserNode each frame.
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [shareMessage, setShareMessage] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const statsCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const waterfallHistoryRef = useRef<Float32Array[]>([]);
  const timeDomainRef = useRef<Float32Array<ArrayBuffer> | null>(null);
  const frequencyHistoryRef = useRef<number[]>([]);
  const silenceStreakRef = useRef(0);
  const statsFrameCounterRef = useRef(0);
  const hydratedFromUrlRef = useRef(false);
  const drawRef = useRef<() => void>(() => { });
  const tickRef = useRef<() => void>(() => { });

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
    timeDomainRef.current = null;
    frequencyHistoryRef.current = [];
    silenceStreakRef.current = 0;
    statsFrameCounterRef.current = 0;
    setStats(null);
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

    // Session stats reuse this same per-frame data: the dominant bin comes
    // from the magnitude array already computed above (`smoothed`), and the
    // one new read below (time-domain, for RMS/clipping) is the only extra
    // AnalyserNode call this feature needs - no second analysis path.
    const dominant = findDominantBin(
      smoothed,
      settings.sampleRate,
      settings.fftSize,
      settings.frequencyRange[0],
      settings.frequencyRange[1],
    );
    const history = frequencyHistoryRef.current;
    history.push(dominant.frequencyHz);
    if (history.length > FREQUENCY_HISTORY_LENGTH) history.shift();

    if (!timeDomainRef.current || timeDomainRef.current.length !== analyser.fftSize) {
      timeDomainRef.current = new Float32Array(analyser.fftSize);
    }
    const timeDomain = timeDomainRef.current;
    analyser.getFloatTimeDomainData(timeDomain);
    const rms = computeRms(timeDomain);
    const clipping = isClipping(timeDomain);
    silenceStreakRef.current = nextSilenceStreak(silenceStreakRef.current, rms);
    const sustainedSilence = silenceStreakRef.current >= DEFAULT_SUSTAINED_SILENCE_FRAMES;

    statsFrameCounterRef.current += 1;
    if (statsFrameCounterRef.current >= STATS_UI_UPDATE_EVERY_N_FRAMES) {
      statsFrameCounterRef.current = 0;
      setStats({ rms, clipping, sustainedSilence });
    }

    drawStatsSparkline(statsCanvasRef.current, history, settings.color);

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

  const loadPresets = async () => {
    const res = await fetch("/api/presets");
    if (!res.ok) return; // not paid, or not signed in - presets UI is hidden entirely in that case anyway
    const data = await res.json();
    setPresets(data.presets);
  };

  useEffect(() => {
    if (!isPaid) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard fetch-on-mount, see ApiKeysManager.tsx for the same pattern
    loadPresets();
  }, [isPaid]);

  const savePreset = async () => {
    if (!newPresetName.trim()) return;
    const res = await fetch("/api/presets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newPresetName.trim(), settings }),
    });
    if (res.ok) {
      setNewPresetName("");
      loadPresets();
    }
  };

  const deletePreset = async (id: string) => {
    await fetch(`/api/presets?id=${id}`, { method: "DELETE" });
    loadPresets();
  };

  // Local presets load once on mount - no sign-in/paid gate, works for
  // anonymous visitors too.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reading localStorage synchronously on mount, same fetch-on-mount shape as loadPresets() above
    setLocalPresets(listLocalPresets());
  }, []);

  const saveLocalPreset = () => {
    if (!newLocalPresetName.trim()) return;
    setLocalPresets(createLocalPreset(newLocalPresetName, settings));
    setNewLocalPresetName("");
  };

  const startRenamingLocalPreset = (preset: LocalPreset) => {
    setEditingLocalPresetId(preset.id);
    setEditingLocalPresetName(preset.name);
  };

  const confirmRenameLocalPreset = () => {
    if (!editingLocalPresetId) return;
    setLocalPresets(renameLocalPreset(editingLocalPresetId, editingLocalPresetName));
    setEditingLocalPresetId(null);
    setEditingLocalPresetName("");
  };

  const removeLocalPreset = (id: string) => {
    setLocalPresets(deleteLocalPreset(id));
  };

  // Shareable URL config: hydrate settings from the query string once on
  // mount (client-only - the server-rendered page has no `window`), then
  // keep the query string in sync with `settings` afterwards, debounced so
  // dragging a slider doesn't spam history.replaceState.
  useEffect(() => {
    try {
      const decoded = decodeSettingsFromParams(new URLSearchParams(window.location.search), DEFAULT_SETTINGS);
      // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time hydration from the URL on mount, mirrors the localStorage read above
      setSettings(decoded);
    } catch {
      // Malformed/unavailable URL state - keep the defaults already in state.
    } finally {
      hydratedFromUrlRef.current = true;
    }
  }, []);

  useEffect(() => {
    if (!hydratedFromUrlRef.current) return;
    const handle = setTimeout(() => {
      try {
        const params = encodeSettingsToParams(settings);
        window.history.replaceState(null, "", `${window.location.pathname}?${params.toString()}`);
      } catch {
        // History API unavailable (e.g. some embedded/private contexts) - the
        // in-app settings still work, sharing the link just won't.
      }
    }, URL_SYNC_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [settings]);

  const copyShareLink = async () => {
    try {
      if (!navigator.clipboard) throw new Error("Clipboard API unavailable");
      await navigator.clipboard.writeText(window.location.href);
      setShareMessage("Link copied to clipboard.");
    } catch {
      setShareMessage("Couldn't copy automatically - copy the URL from your address bar.");
    } finally {
      setTimeout(() => setShareMessage(null), 4000);
    }
  };

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

        <button onClick={copyShareLink} className="rounded border border-white/20 px-4 py-2 text-sm hover:bg-white/10">
          Copy Share Link
        </button>
        {shareMessage && <span className="text-sm text-white/60">{shareMessage}</span>}
      </div>

      {effectiveViewMode === "tuner" && dominantFrequency !== null && (
        <p className="text-sm text-white/60">Dominant frequency: {dominantFrequency.toFixed(1)} Hz</p>
      )}

      <div className="flex flex-col gap-2 border-t border-white/10 pt-4">
        <h3 className="text-sm font-medium">Session Stats</h3>
        <canvas
          ref={statsCanvasRef}
          width={800}
          height={60}
          className="w-full rounded border border-white/10 bg-black"
        />
        <div className="flex flex-wrap items-center gap-3 text-sm text-white/60">
          <span>RMS: {stats ? stats.rms.toFixed(3) : "-"}</span>
          {stats?.clipping && <span className="font-medium text-red-400">Clipping</span>}
          {stats?.sustainedSilence && <span className="font-medium text-yellow-400">Silence</span>}
          {!running && <span>Start the visualizer to see live stats.</span>}
        </div>
      </div>

      <div className="flex flex-col gap-2 border-t border-white/10 pt-4">
        <h3 className="text-sm font-medium">Local Presets</h3>
        <p className="text-xs text-white/40">
          Saved in this browser only - no sign-in required, and separate from the account-wide presets on the
          dashboard.
        </p>

        <div className="flex gap-2">
          <input
            value={newLocalPresetName}
            onChange={(e) => setNewLocalPresetName(e.target.value)}
            placeholder="Preset name"
            className="flex-1 rounded border border-white/20 bg-transparent px-3 py-2 text-sm"
          />
          <button onClick={saveLocalPreset} className="rounded border border-white/20 px-4 py-2 text-sm hover:bg-white/10">
            Save As
          </button>
        </div>

        {localPresets.length > 0 && (
          <ul className="flex flex-col gap-1">
            {localPresets.map((preset) => (
              <li key={preset.id} className="flex items-center gap-2 rounded border border-white/10 px-2 py-1 text-sm">
                {editingLocalPresetId === preset.id ? (
                  <>
                    <input
                      value={editingLocalPresetName}
                      onChange={(e) => setEditingLocalPresetName(e.target.value)}
                      className="flex-1 rounded border border-white/20 bg-transparent px-2 py-1 text-sm"
                    />
                    <button onClick={confirmRenameLocalPreset} className="hover:underline">
                      Save
                    </button>
                    <button onClick={() => setEditingLocalPresetId(null)} className="text-white/50 hover:underline">
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button onClick={() => setSettings(preset.settings)} className="flex-1 text-left hover:underline">
                      {preset.name}
                    </button>
                    <button onClick={() => startRenamingLocalPreset(preset)} className="text-white/50 hover:underline">
                      Rename
                    </button>
                    <button onClick={() => removeLocalPreset(preset.id)} className="text-red-400 hover:underline">
                      Delete
                    </button>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {isPaid && (
        <div className="flex flex-col gap-2 border-t border-white/10 pt-4">
          <h3 className="text-sm font-medium">Presets</h3>

          <div className="flex gap-2">
            <input
              value={newPresetName}
              onChange={(e) => setNewPresetName(e.target.value)}
              placeholder="Preset name"
              className="flex-1 rounded border border-white/20 bg-transparent px-3 py-2 text-sm"
            />
            <button onClick={savePreset} className="rounded border border-white/20 px-4 py-2 text-sm hover:bg-white/10">
              Save current settings
            </button>
          </div>

          {presets.length > 0 && (
            <ul className="flex flex-wrap gap-2">
              {presets.map((preset) => (
                <li key={preset.id} className="flex items-center gap-1 rounded border border-white/10 px-2 py-1 text-sm">
                  <button onClick={() => setSettings(preset.settings)} className="hover:underline">
                    {preset.name}
                  </button>
                  <button onClick={() => deletePreset(preset.id)} className="text-red-400 hover:underline">
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
