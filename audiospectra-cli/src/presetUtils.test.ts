import assert from "node:assert/strict";
import { test } from "node:test";
import * as path from "path";
import { resolvePresetsDir, sanitizePresetName } from "./presetUtils";

test("sanitizePresetName strips filesystem-invalid characters", () => {
    assert.equal(sanitizePresetName('my/preset\\name:*?"<>|'), "mypresetname");
});

test("sanitizePresetName strips control characters", () => {
    assert.equal(sanitizePresetName("bad\x00name\x1f"), "badname");
});

test("sanitizePresetName trims surrounding whitespace", () => {
    assert.equal(sanitizePresetName("  spaced out  "), "spaced out");
});

test("sanitizePresetName leaves an already-clean name untouched", () => {
    assert.equal(sanitizePresetName("hardware-tuned-preset"), "hardware-tuned-preset");
});

test("resolvePresetsDir defaults to ~/.audiospectra_cli/presets", () => {
    const dir = resolvePresetsDir({} as NodeJS.ProcessEnv, "/home/user");
    assert.equal(dir, path.join("/home/user", ".audiospectra_cli", "presets"));
});

test("resolvePresetsDir honors AUDIOSPECTRA_CLI_HOME override", () => {
    // AUDIOSPECTRA_CLI_HOME substitutes for $HOME, not for .audiospectra_cli
    // itself - matching Python's Audio_SpectraCLI.presets.get_presets_dir(),
    // which does os.path.join(home, ".audiospectra_cli", "presets") whether
    // `home` came from the env override or the real home directory.
    const dir = resolvePresetsDir({ AUDIOSPECTRA_CLI_HOME: "/custom/home" } as NodeJS.ProcessEnv, "/home/user");
    assert.equal(dir, path.join("/custom/home", ".audiospectra_cli", "presets"));
});
