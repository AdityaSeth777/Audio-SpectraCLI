import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  createLocalPreset,
  deleteLocalPreset,
  listLocalPresets,
  renameLocalPreset,
} from "./localPresets";
import { DEFAULT_SETTINGS } from "@/components/Visualizer";

/**
 * Node's test environment has no `localStorage` global by default. We
 * install a minimal in-memory mock that mirrors the real Storage API so
 * these tests exercise the same code paths the browser would run.
 */
function installLocalStorageMock() {
  const store = new Map<string, string>();
  const mock: Storage = {
    getItem: (key: string) => (store.has(key) ? store.get(key)! : null),
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => store.clear(),
    key: (index: number) => Array.from(store.keys())[index] ?? null,
    get length() {
      return store.size;
    },
  };
  Object.defineProperty(globalThis, "localStorage", { value: mock, configurable: true, writable: true });
}

function uninstallLocalStorage() {
  Object.defineProperty(globalThis, "localStorage", { value: undefined, configurable: true, writable: true });
}

describe("localPresets (localStorage unavailable)", () => {
  beforeEach(() => uninstallLocalStorage());

  it("listLocalPresets returns [] instead of throwing", () => {
    expect(listLocalPresets()).toEqual([]);
  });

  it("createLocalPreset does not throw and returns the in-memory addition", () => {
    const result = createLocalPreset("My preset", DEFAULT_SETTINGS);
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("My preset");
  });

  it("deleteLocalPreset on an empty/unavailable store does not throw", () => {
    expect(deleteLocalPreset("nonexistent")).toEqual([]);
  });
});

describe("localPresets (localStorage available)", () => {
  beforeEach(() => installLocalStorageMock());
  afterEach(() => uninstallLocalStorage());

  it("starts empty", () => {
    expect(listLocalPresets()).toEqual([]);
  });

  it("creates and lists a preset", () => {
    createLocalPreset("Loud room", DEFAULT_SETTINGS);
    const presets = listLocalPresets();
    expect(presets).toHaveLength(1);
    expect(presets[0].name).toBe("Loud room");
    expect(presets[0].settings).toEqual(DEFAULT_SETTINGS);
    expect(presets[0].id).toBeTruthy();
    expect(presets[0].createdAt).toBeTruthy();
  });

  it("persists across separate calls (i.e. actually writes to storage)", () => {
    createLocalPreset("A", DEFAULT_SETTINGS);
    createLocalPreset("B", DEFAULT_SETTINGS);
    expect(listLocalPresets().map((p) => p.name)).toEqual(["A", "B"]);
  });

  it("trims whitespace and falls back to a default name when blank", () => {
    createLocalPreset("   ", DEFAULT_SETTINGS);
    expect(listLocalPresets()[0].name).toBe("Untitled preset");
  });

  it("renames a preset by id", () => {
    createLocalPreset("Original", DEFAULT_SETTINGS);
    const [preset] = listLocalPresets();
    renameLocalPreset(preset.id, "Renamed");
    expect(listLocalPresets()[0].name).toBe("Renamed");
  });

  it("ignores a blank rename", () => {
    createLocalPreset("Original", DEFAULT_SETTINGS);
    const [preset] = listLocalPresets();
    renameLocalPreset(preset.id, "   ");
    expect(listLocalPresets()[0].name).toBe("Original");
  });

  it("deletes a preset by id", () => {
    createLocalPreset("Keep", DEFAULT_SETTINGS);
    createLocalPreset("Remove", DEFAULT_SETTINGS);
    const toRemove = listLocalPresets().find((p) => p.name === "Remove")!;
    deleteLocalPreset(toRemove.id);
    const remaining = listLocalPresets();
    expect(remaining).toHaveLength(1);
    expect(remaining[0].name).toBe("Keep");
  });

  it("ignores corrupted JSON in storage instead of throwing", () => {
    localStorage.setItem("audiospectra:local-presets", "{not valid json");
    expect(listLocalPresets()).toEqual([]);
  });

  it("ignores a non-array value in storage", () => {
    localStorage.setItem("audiospectra:local-presets", JSON.stringify({ not: "an array" }));
    expect(listLocalPresets()).toEqual([]);
  });

  it("filters out malformed entries within an otherwise valid array", () => {
    localStorage.setItem(
      "audiospectra:local-presets",
      JSON.stringify([{ id: "1", name: "ok", createdAt: "now", settings: {} }, { garbage: true }]),
    );
    const presets = listLocalPresets();
    expect(presets).toHaveLength(1);
    expect(presets[0].id).toBe("1");
  });
});
