/**
 * Local (browser-only) CRUD for visualizer settings presets, stored in
 * localStorage under a single key. Unlike the DB-backed presets in
 * PresetsManager.tsx/app/api/presets, this needs no sign-in, no network
 * call, and no paid plan - it works for anonymous visitors on /visualize.
 *
 * Every read/write is wrapped in try/catch: localStorage can throw (private
 * browsing, disabled storage, quota) or simply not exist, and none of that
 * should crash the page - callers just get an empty list / a no-op.
 */
import type { VisualizerSettings } from "@/components/Visualizer";

export type LocalPreset = {
  id: string;
  name: string;
  settings: VisualizerSettings;
  createdAt: string;
};

const STORAGE_KEY = "audiospectra:local-presets";

function isLocalPreset(value: unknown): value is LocalPreset {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.name === "string" &&
    typeof v.createdAt === "string" &&
    !!v.settings &&
    typeof v.settings === "object"
  );
}

function readAll(): LocalPreset[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isLocalPreset);
  } catch {
    return [];
  }
}

function writeAll(presets: LocalPreset[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(presets));
  } catch {
    // Storage unavailable or full - the in-memory list the caller already
    // has is still valid for the current page session, so this is a no-op.
  }
}

function makeId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Lists all locally-saved presets, newest last. Never throws. */
export function listLocalPresets(): LocalPreset[] {
  return readAll();
}

/** Saves the given settings under `name` and returns the updated list. */
export function createLocalPreset(name: string, settings: VisualizerSettings): LocalPreset[] {
  const trimmed = name.trim();
  const presets = readAll();
  const next = [...presets, { id: makeId(), name: trimmed || "Untitled preset", settings, createdAt: new Date().toISOString() }];
  writeAll(next);
  return next;
}

/** Renames a preset in place and returns the updated list. */
export function renameLocalPreset(id: string, newName: string): LocalPreset[] {
  const trimmed = newName.trim();
  const presets = readAll();
  const next = presets.map((p) => (p.id === id && trimmed ? { ...p, name: trimmed } : p));
  writeAll(next);
  return next;
}

/** Deletes a preset and returns the updated list. */
export function deleteLocalPreset(id: string): LocalPreset[] {
  const presets = readAll();
  const next = presets.filter((p) => p.id !== id);
  writeAll(next);
  return next;
}
