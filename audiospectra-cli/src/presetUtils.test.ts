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
    const dir = resolvePresetsDir({ AUDIOSPECTRA_CLI_HOME: "/custom/home" } as NodeJS.ProcessEnv, "/home/user");
    assert.equal(dir, path.join("/custom/home", "presets"));
});
