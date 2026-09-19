import * as os from "os";
import * as path from "path";

/**
 * Characters invalid in filenames across common filesystems, plus control
 * characters. Mirrors the sanitization the Python-side `Audio_SpectraCLI.presets`
 * module applies so preset files stay interchangeable between the GUI and
 * this extension.
 */
const INVALID_FILENAME_CHARS = /[/\\:*?"<>|\x00-\x1f]/g;

/**
 * Strips characters that are invalid in filenames, returning a name safe to
 * use as `<name>.json`. Pulled out so it's testable without importing `vscode`.
 */
export function sanitizePresetName(name: string): string {
    return name.replace(INVALID_FILENAME_CHARS, "").trim();
}

/**
 * Resolves the directory named presets are stored in, honoring the
 * `AUDIOSPECTRA_CLI_HOME` env var override (same behavior as the Python
 * `Audio_SpectraCLI.presets` module) so preset files are interchangeable
 * between the GUI and this extension. `env`/`homedir` are injectable for
 * testing without touching the real environment.
 */
export function resolvePresetsDir(
    env: NodeJS.ProcessEnv = process.env,
    homedir: string = os.homedir(),
): string {
    // AUDIOSPECTRA_CLI_HOME substitutes for the user's *home* directory
    // (that's how the Python side's tests use it to isolate from a real
    // $HOME), not for `.audiospectra_cli` itself - `.audiospectra_cli/presets`
    // is appended in both cases. Appending it only in the no-override branch
    // (an earlier version of this function did that) pointed the two
    // implementations at different directories whenever the override was
    // set, silently breaking the "presets are interchangeable" guarantee
    // this module exists for - caught by an actual cross-language E2E run.
    const home = env.AUDIOSPECTRA_CLI_HOME || homedir;
    return path.join(home, ".audiospectra_cli", "presets");
}
