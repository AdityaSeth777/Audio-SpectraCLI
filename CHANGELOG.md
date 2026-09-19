# Changelog 📝

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* Hosted web SaaS app (`web/`): browser-only visualizer with free/paid tiers, Clerk auth, Stripe billing, a Data/Analysis API (`/api/v1/analyze` — WAV/MP3/AAC input, API-key auth, usage-metered billing), distributed rate limiting (Upstash Redis with in-memory fallback), and a dashboard for managing API keys and saved presets.
* Live VS Code extension: spawns a new headless streaming mode (`python -m Audio_SpectraCLI.headless`) and renders it in a real webview panel instead of only inserting a code snippet.
* Interactive cross-platform launcher (`launch.py` / `run.sh` / `run.command` / `run.bat`) that auto-sets up a local `.venv` and gets a user running with one double-click, sidestepping `externally-managed-environment` pip failures.
* Native GUI: 5 view modes (Line/Bars/Waterfall/Circular/Tuner), dB scale toggle, windowing function choice (Hann/Hamming/Blackman), adjustable noise threshold and Gaussian smoothing strength, stereo channel selection (Mono mix/Left/Right), peak-hold markers, live BPM estimation, dominant-note readout, PNG/CSV export, WAV recording, save/load JSON presets, in-GUI device switching, and MIDI-out (converts the dominant frequency to a MIDI note over a virtual port).
* Qt-independent `engine.py`, shared by the GUI and the new headless mode, plus a pure `analysis.py` module (windowing, dB conversion, note naming, BPM heuristic) and `midi_out.py`.

### Fixed

* A production crash from redrawing on every audio callback instead of a throttled ~30fps timer, which backed up Qt's event queue under sustained real mic input and could abort the process on some PyQt5/sip builds; also fixed a `blocksize` mismatch that made this worse than intended.
* `gaussian_filter1d(sigma=0)` (unchecking "Smooth spectrum") crashed the background audio thread with `ZeroDivisionError`, silently killing all further updates with no visible error — found via a full end-to-end run against real hardware.
* Bars view was downsampled from the full spectrum while sized for the (narrower) selected frequency range, producing sparse, thin bars instead of a proper equalizer.
* dB-scale y-axis headroom was computed via multiplication, which is wrong for negative dB values and clipped the actual peak off the top of the plot.
* Toggling dB scale mid-session while in Waterfall view mixed linear and dB values in the same history, corrupting the color scale; changing the frequency range live while in Waterfall view could also produce rows of inconsistent width, crashing `imshow`.
* Loading a preset whose frequency range didn't overlap the currently-set range could silently apply the wrong range, due to an ordering dependency in how min/max were validated.
* Stopping visualization (or closing the window) while a WAV recording was in progress silently discarded the recording instead of prompting to save it, and could leave the Record button in an inconsistent state.
* `engine.start()` failures (device unplugged, unsupported sample rate/channels) and file I/O errors in Save/Load/Export buttons ran unguarded inside Qt click slots, risking a process crash on the same PyQt5/sip builds mentioned above.
* MIDI notes could get stuck on indefinitely — both when stopping visualization while a note was sounding, and when input went quiet (the engine simply stops calling back, so there was no "silence → note-off" path at all).
* "Mono (mix)" channel mode never actually mixed anything — the app always opened a 1-channel stream for it, so the averaging code path was unreachable; channel count is now resolved from the actual device's capability.
* The VS Code extension's own `eslint` toolchain was broken (missing `@typescript-eslint` dependencies) — installed and fixed the one warning it then surfaced.
* `Dockerfile`'s `CMD` (`python -m Audio_SpectraCLI.main`) silently did nothing — `main.py` had no `__main__` entry point.

### Known limitations (by design, not defects)

* BPM detection is a simple onset/energy heuristic, not lab-grade beat tracking — expect it to be unstable on non-rhythmic input.
* The Analysis API only accepts WAV, MP3, and AAC input, not every audio codec.
* Windows has no native virtual MIDI port support without a third-party loopback driver (e.g. loopMIDI) — inherent OS limitation.
* Presets can be saved/loaded/deleted from the web dashboard and inline in the visualizer; there's no cross-device sync beyond that.

## [version] - 2024-11-07

### Added

* 

### Changed

* 

### Fixed

* 

### Deprecated

* 

### Removed

* 

### Security

* 