# Changelog

All notable changes to the Audio-SpectraCLI VS Code extension are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Live in-editor visualization**: `Audio-SpectraCLI: Start Live Visualization` / `Stop Live Visualization` commands spawn a headless Python process (`python -m Audio_SpectraCLI.headless`) and stream its output into a real webview panel — previously the extension only inserted a code snippet and showed a static status message.
- Settings: `audioSpectraCli.pythonPath`, `audioSpectraCli.sampleRate`, `audioSpectraCli.blockSize`, `audioSpectraCli.bars`.
- `lineParser.ts`: pure line-buffering/JSON-parsing logic extracted for unit testing without a `vscode` import, with a plain Node (`node:test`) unit test suite (`npm run test:unit`).

### Fixed

- The `eslint` toolchain was broken — `eslint.config.mjs` referenced `@typescript-eslint/eslint-plugin` and `@typescript-eslint/parser`, neither of which were installed. Installed both plus `eslint` itself; fixed the one warning (`curly`) it then surfaced.
- Removed a dependency duplication: both `vsce` and `@vscode/vsce` were listed under `dependencies` (packaging tools belong in `devDependencies`, and only one is needed).

### Known limitations

- The full Electron-based integration test suite (`npm test`, driven by `.vscode-test.mjs`) needs `@vscode/test-cli`, which isn't installed, and requires downloading/running real VS Code — not exercised by CI or this repo's own tooling yet. `npm run test:unit` covers the pure logic (line parsing) without that dependency.
