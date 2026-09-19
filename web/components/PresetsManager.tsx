"use client";

import { useEffect, useState } from "react";
import type { VisualizerSettings } from "./Visualizer";

type SavedPreset = {
  id: string;
  name: string;
  settings: VisualizerSettings;
  createdAt: string;
};

export function PresetsManager({ isPaid }: { isPaid: boolean }) {
  const [presets, setPresets] = useState<SavedPreset[]>([]);
  // Starts already-not-loading when the viewer isn't paid, since no fetch
  // will ever run for them - avoids a synchronous setState(false) in the
  // effect body below, which react-hooks/set-state-in-effect flags (see
  // ApiKeysManager.tsx for the same "loading starts true, only ever set to
  // false" convention this follows).
  const [loading, setLoading] = useState(isPaid);
  const [error, setError] = useState<string | null>(null);

  const loadPresets = async () => {
    try {
      const res = await fetch("/api/presets");
      if (!res.ok) throw new Error((await res.json()).error ?? "Failed to load presets");
      const data = await res.json();
      setPresets(data.presets);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load presets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isPaid) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard fetch-on-mount, see ApiKeysManager.tsx for the same pattern
    loadPresets();
  }, [isPaid]);

  const deletePreset = async (id: string) => {
    await fetch(`/api/presets?id=${id}`, { method: "DELETE" });
    loadPresets();
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">Saved Visualizer Presets</h2>

      {!isPaid && <p className="text-sm text-white/60">Presets require the paid plan.</p>}

      {error && <p className="text-sm text-red-500">{error}</p>}

      {isPaid && (loading ? (
        <p className="text-sm text-white/60">Loading...</p>
      ) : presets.length === 0 ? (
        <p className="text-sm text-white/60">
          No presets saved yet - save one from the{" "}
          <a href="/visualize" className="underline">
            visualizer
          </a>
          .
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {presets.map((preset) => (
            <li
              key={preset.id}
              className="flex items-center justify-between rounded border border-white/10 px-3 py-2 text-sm"
            >
              <div>
                <p className="font-medium">{preset.name}</p>
                <p className="text-white/50">
                  {preset.settings.viewMode} view · {preset.settings.sampleRate}Hz ·{" "}
                  {new Date(preset.createdAt).toLocaleDateString()}
                </p>
              </div>
              <button onClick={() => deletePreset(preset.id)} className="text-red-400 hover:underline">
                Delete
              </button>
            </li>
          ))}
        </ul>
      ))}
    </div>
  );
}
