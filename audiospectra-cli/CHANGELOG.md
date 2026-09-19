# Changelog

All notable changes to the Audio-SpectraCLI VS Code extension are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.0]

### Added

- **Live in-editor visualization**: `Audio-SpectraCLI: Start Live Visualization` / `Stop Live Visualization` commands spawn a headless Python process (`python -m Audio_SpectraCLI.headless`) and stream its output into a real webview panel - previously the extension only inserted a code snippet and showed a static status message.
- **Live status bar item**: shows the dominant frequency/peak magnitude of the most recently parsed frame while a live visualization is running, torn down on stop/dispose.
- **New command**: `Audio-SpectraCLI: Save Current Frame as Preset` - writes the extension's current `fs`/`blockSize` settings to `~/.audiospectra_cli/presets/<name>.json` (respecting `AUDIOSPECTRA_CLI_HOME`), the same location/format the Python-side `Audio_SpectraCLI.presets` module reads and writes, so presets are interchangeable between the GUI and this extension - verified end to end (write from the extension, read from Python) after fixing a directory-resolution bug (see Fixed).
- Settings: `audioSpectraCli.pythonPath`, `audioSpectraCli.sampleRate`, `audioSpectraCli.blockSize`, `audioSpectraCli.bars`, `audioSpectraCli.visualizerColor`.
- `lineParser.ts`: pure line-buffering/JSON-parsing logic extracted for unit testing without a `vscode` import, with a plain Node (`node:test`) unit test suite (`npm run test:unit`). Also exports `computeDominantFrequency`, used by the new status bar item.
- `presetUtils.ts`: pure `sanitizePresetName`/`resolvePresetsDir` helpers backing the new save-preset command, unit tested the same way.

### Fixed

- The `eslint` toolchain was broken - `eslint.config.mjs` referenced `@typescript-eslint/eslint-plugin` and `@typescript-eslint/parser`, neither of which were installed. Installed both plus `eslint` itself; fixed the one warning (`curly`) it then surfaced.
- Removed a dependency duplication: both `vsce` and `@vscode/vsce` were listed under `dependencies` (packaging tools belong in `devDependencies`, and only one is needed).
- `@vscode/vsce` bumped 3.2.1 → 4.0.0, resolving every then-open Dependabot alert reachable through this package's dependency tree (`npm audit`: 0 vulnerabilities).
- `resolvePresetsDir()` resolved to a *different* directory than the Python side whenever `AUDIOSPECTRA_CLI_HOME` was set (it skipped appending `.audiospectra_cli` in that branch) - found by an actual write-from-extension, read-from-Python round trip, which silently returned nothing until this was fixed.

### Known limitations

- The full Electron-based integration test suite (`npm test`, driven by `.vscode-test.mjs`) needs `@vscode/test-cli`, which isn't installed, and requires downloading/running real VS Code - not exercised by CI or this repo's own tooling yet. `npm run test:unit` covers the pure logic (line parsing, dominant-frequency computation, preset-name sanitization/directory resolution) without that dependency.
- `visualizerColor` is only picked up the next time "Start Live Visualization" runs, not hot-reloaded into an already-open panel.
