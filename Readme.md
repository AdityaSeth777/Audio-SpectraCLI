```
    _             _ _            ____                  _              ____ _     ___
   / \  _   _  __| (_) ___      / ___| _ __   ___  ___| |_ _ __ __ _ / ___| |   |_ _|
  / _ \| | | |/ _` | |/ _ \ ____\___ \| '_ \ / _ \/ __| __| '__/ _` | |   | |    | |
 / ___ \ |_| | (_| | | (_) |_____|__) | |_) |  __/ (__| |_| | | (_| | |___| |___ | |
/_/   \_\__,_|\__,_|_|\___/     |____/| .__/ \___|\___|\__|_|  \__,_|\____|_____|___|
                                      |_|
```

<div align=center>

[![cover.png](https://i.postimg.cc/1t7F1J9j/cover.png)](https://postimg.cc/bDbrQ0Sx)

</div>

## Audio Spectrum Visualization is a Python project that visualizes real-time audio input as a spectrum using Fast Fourier Transform (FFT). It provides an interactive and dynamic interface for users to start the visualization and exit the program.

 <p>

![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat)
[![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FAdityaSeth777%2FAudio-SpectraCLI&label=Visitors&countColor=%23263759&style=plastic)](https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2FAdityaSeth777%2FAudio-SpectraCLI)
![GitHub forks](https://img.shields.io/github/forks/AdityaSeth777/Audio-SpectraCLI)
![GitHub Repo stars](https://img.shields.io/github/stars/AdityaSeth777/Audio-SpectraCLI)
![GitHub last commit](https://img.shields.io/github/last-commit/AdityaSeth777/Audio-SpectraCLI)
![GitHub repo size](https://img.shields.io/github/repo-size/AdityaSeth777/Audio-SpectraCLI)
![GitHub issues](https://img.shields.io/github/issues/AdityaSeth777/Audio-SpectraCLI)
![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/AdityaSeth777/Audio-SpectraCLI)
![GitHub pull requests](https://img.shields.io/github/issues-pr/AdityaSeth777/Audio-SpectraCLI)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed/AdityaSeth777/Audio-SpectraCLI)

 </p>

<a href="https://www.producthunt.com/posts/audio-spectracli?utm_source=badge-featured&utm_medium=badge&utm_souce=badge-audio&#0045;spectracli" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=458166&theme=light" alt="Audio&#0045;SpectraCLI - Visualizing&#0032;real&#0045;time&#0032;audio&#0032;input&#0032;as&#0032;a&#0032;spectrum&#0032;using&#0032;FFT | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

### Notable point : From v4.0, I have implemented a whole new code using PyQt5, which you will find evident here in the new main default code - [&#39;main.py&#39;](./Audio_SpectraCLI/main.py) and the [&#39;test.py&#39;](./tests/test.py) case supporting that.

### The [&#39;main-old.py&#39;](./Audio_SpectraCLI/main-old.py), which is the code for the main file for v3.2, and the [&#39;test-old.py&#39;](./tests/test-old.py) case supporting that, is DEPRECATED.

## Current Features (with respect to 4.1.0)

- Real-time visualization of Fast Fourier Transform (FFT) spectrum of audio input.
- Live VS Code Extension support - the extension now spawns a real headless
  audio process and streams the spectrum into a live webview canvas (see
  [Web & Extension Additions](#web--extension-additions) below).
- Support for adjusting parameters such as duration, sampling rate, and block size.
- Seamless integration with SoundDevice for audio input capture.
- Customizable Frequency Range: Allow users to specify the frequency range to display in the spectrum.
- Color Customization: Provide options for users to customize the colors used in the spectrum visualization.
- Added PyQt5 modules and a Gaussian filter that enables user input for Duration (in seconds), Sampling Rate (in Hz), Block Size, and also smoothens the output.
- Might need to keep in mind that the Gaussian filter is too strong and it won't recognise any noise and display it's spectra. Only actual input through mic such as conversations and music are displayed which can be categorised as real inputs or audio, and of course in real time.
- Much more dynamic and user-controlled interface.
- A headless, GUI-free streaming mode (`python -m Audio_SpectraCLI.headless`)
  that emits spectrum frames as JSON lines - the same audio/FFT engine that
  powers the GUI, usable from scripts or other tools without PyQt5 installed.
- The GUI redraws at a fixed ~30fps from the latest audio frame rather than
  redrawing on every single incoming audio block. Real microphone input can
  deliver far more blocks per second than a matplotlib redraw can keep up
  with, which previously could back up the GUI's event queue and, on some
  PyQt5/sip builds, crash the whole app outright after sustained use. Any
  error during a redraw is now also caught and logged instead of being
  allowed to propagate and abort the process.
- The GUI's canvas now resizes properly on window maximize (no clipped axis
  labels), and every slider (Duration/Sampling Rate/Block Size/Noise
  Threshold) has a paired numeric spinbox next to it — the exact value is
  always visible and directly typeable, not just draggable.
- Five view modes: **Line** (the original), **Bars** (equalizer-style),
  **Waterfall** (scrolling history spectrogram), **Circular** (radial
  display), and **Tuner** (big musical-note readout for the dominant
  frequency, e.g. "A4 · 441.4 Hz · +6 cents").
- **dB (logarithmic) scale** toggle, **windowing function** choice
  (None/Hann/Hamming/Blackman) to reduce spectral leakage, an adjustable
  **noise threshold** and **Gaussian smoothing strength** (previously
  hardcoded), and **stereo channel selection** (Mono mix/Left/Right —
  previously always forced mono).
- **Peak-hold markers** (Line/Bars views) — a line that holds at the recent
  peak and decays, like a hardware audio meter.
- **Live BPM estimation** and a **dominant-note readout**, always shown
  above the canvas regardless of view mode. The BPM estimate is a simple
  onset/energy heuristic, not lab-grade beat tracking — expect it to be
  unstable on non-rhythmic input, that's inherent to how simple it is.
- **Export** the current view as PNG (also bound to Ctrl+S) or the current
  frame's data as CSV, and **record microphone input to a WAV file**.
- **Save/load setting presets** to a local JSON file.
- **In-GUI microphone selection** (previously only choosable via the
  `launch.py` interactive launcher at startup) — swap devices from a
  dropdown before clicking Start; changing it while running is disabled,
  the same way sampling rate/block size are, since a live stream can't be
  reconfigured without reopening it.
- **MIDI-out**: converts the dominant frequency to a MIDI note and sends it
  to a virtual MIDI port, turning the visualizer into a simple audio-to-MIDI
  tool. `mido`/`python-rtmidi` are core dependencies (installed
  automatically by `requirements.txt`/`pip install Audio-SpectraCLI`/the
  interactive launcher's `.venv` setup) — but the checkbox still degrades
  gracefully with a clear explanation instead of crashing if they're somehow
  missing or fail to build in a given environment. Windows has no native
  virtual MIDI port support without a third-party loopback driver like
  loopMIDI; the same message covers that case too. A stuck note is released
  automatically both when input goes quiet for 0.5s and when you click Stop.

## Packaging

```
Audio-SpectraCLI/

├── .gitignore
├── CODE_OF_CONDUCT.md
├── Contributing.md
├── Dockerfile
├── LICENSE
├── Readme.md
├── requirements.txt
├── setup.cfg
├── setup.py
├── launch.py           # interactive cross-platform launcher (see Instant Launch)
├── run.sh              # canonical launcher entry point for macOS/Linux terminals: ./run.sh
├── run.command         # thin double-click wrapper around run.sh, for macOS/Linux Finder
├── run.bat             # double-click/terminal entry point for Windows
├── .github/
│   └── workflows/
│       ├── docker-publish.yml
│       ├── label.yml
│       └── python-publish.yml
├── Audio_SpectraCLI/
│   ├── main-old.py
│   ├── main.py           # PyQt5 GUI, now built on engine.py
│   ├── engine.py         # Qt-independent capture/FFT/smoothing core, shared by main.py and headless.py
│   ├── analysis.py       # pure DSP helpers: windowing, dB conversion, note naming, BPM estimation
│   ├── midi_out.py       # optional MIDI-out (gracefully degrades if python-rtmidi isn't installed)
│   ├── headless.py       # `python -m Audio_SpectraCLI.headless` JSON-streaming CLI mode
│   └── __init__.py
├── tests/
│   ├── test-old.py
│   ├── test.py
│   ├── test_engine.py
│   ├── test_headless.py
│   ├── test_analysis.py
│   ├── test_midi_out.py
│   ├── test_gui_smoke.py
│   ├── test_gui_stress.py
│   ├── test_gui_controls.py
│   └── test_gui_features.py
├── audiospectra-cli/         # VS Code extension (now with a real live webview)
│   ├── assets
│   ├── dist
│   ├── src/
│   │   ├── test
│   │   ├── extension.test.ts
│   │   ├── extension.ts
│   │   ├── visualizerPanel.ts
│   │   ├── lineParser.ts
│   │   └── lineParser.test.ts
│   ├── audio-spectracli-extension-v.vsix
│   ├── CHANGELOG.md
│   ├── esbuild.js
│   ├── eslint.config.mjs
│   ├── package.json
│   ├── package-lock.json
│   ├── README.md
│   ├── sample.py
│   └── tsconfig.json
└── web/                       # Next.js SaaS app: hosted visualizer, accounts/billing, analysis API
    ├── app/
    ├── components/
    ├── lib/
    └── README.md
```

## Installation Methods : (Now Extension available)

<details open>

<summary> Instant Launch (interactive script — double-click and go)</summary>

If you already have the repo (`git clone` or downloaded), the fastest way to
run the native GUI is the interactive launcher — it sits alongside every
other installation method below, it doesn't replace them.

- **macOS/Linux, from a terminal**: `./run.sh` — this is the canonical
  entry point; read it if you want to know exactly what runs.
- **macOS/Linux, by double-clicking in Finder**: double-click
  **`run.command`** — Finder normally opens a plain `.sh` file in a text
  editor instead of running it, so `run.command` exists purely as a thin
  wrapper that calls `run.sh` for that double-click case. It contains no
  logic of its own.
- **Windows**: double-click **`run.bat`** (or run it from a terminal).
- **Any OS directly**: `python3 launch.py` (or `python launch.py`).

It detects your OS and Python version, checks whether `numpy`/`scipy`/
`sounddevice`/`matplotlib`/`PyQt5` are installed. If any are missing, it
offers to set up a local `.venv` next to the script and install them there
— it deliberately never tries to `pip install` straight into your system
Python, since modern Homebrew/python.org Python (and recent Linux distros)
refuse that with an "externally-managed-environment" error. After that
one-time setup, it lists your real audio input devices (via
`sounddevice.query_devices()`) so you can pick one (or just hit Enter for
the system default) — this is the only thing it asks, since it's the one
setting the GUI itself has no way to know. It then opens the GUI and starts
visualizing immediately, no extra click. Duration, sampling rate, and block
size are **not** asked in the terminal, since the GUI already has sliders
for all three once it's open — asking twice for the same thing would just
be redundant. Once `.venv` exists, later runs skip the setup check entirely
and go straight to the device prompt.

#### First time on macOS, step by step

1. **Get Python 3**, if you don't already have it: open Terminal and run
   `python3 --version`. If that fails, install Python from
   [python.org](https://python.org) (or `brew install python3` if you use
   Homebrew), then try again.
2. **Get the repo**: `git clone https://github.com/AdityaSeth777/Audio-SpectraCLI.git`
   (or download and unzip it from GitHub).
3. **Run it**: either open Terminal, `cd` into the repo folder, and run
   `./run.sh` — or double-click `run.command` in Finder.
   - Double-click, first time only: macOS may refuse to run it with an
     "unidentified developer" warning, since it isn't code-signed.
     Right-click (or Control-click) `run.command` → **Open** → confirm in
     the dialog. You only need to do this once.
4. **The launcher runs.** If packages are missing, it asks: `Set them up
   now in a local .venv (won't touch your system Python)? [Y/n]` — press
   Enter or `y`. This downloads and installs `numpy`/`scipy`/`sounddevice`/
   `matplotlib`/`PyQt5` into a `.venv` folder it creates next to the script
   (takes a minute or two; only happens once).
5. **Grant microphone access** when macOS prompts for it (a system dialog
   asking to let Terminal/Python use the microphone) — click **Allow**. If
   you miss it or previously denied it, go to **System Settings → Privacy
   & Security → Microphone** and enable it for Terminal yourself.
6. **Pick an audio input device** from the list it prints (or just press
   Enter for the default) — that's the only prompt.
7. The **GUI window opens and starts visualizing immediately** — speak or
   play audio near the selected microphone and you should see the spectrum
   move. Adjust duration/sampling rate/block size using the sliders inside
   the GUI itself.

---

</details>

----

<details>

<summary> Installation & Usage (Using VSCode Extensions - Marketplace)</summary>

# How to Use the Audio-SpectraCLI Extension

Follow these steps to use the Audio-SpectraCLI extension in Visual Studio Code:

1. **Open Visual Studio Code**
   - Launch VS Code on your computer (macOS, Windows, or Linux).

2. **Install the Audio-SpectraCLI Extension**
   - Go to the Extensions sidebar by clicking on the Extensions icon in the Activity Bar (or press `Ctrl+Shift+X` on Windows/Linux or `Cmd+Shift+X` on macOS).
   - Search for "Audio-SpectraCLI" in the Extensions Marketplace.
   - Click **Install** next to the Audio-SpectraCLI extension.

3. **Activate the Extension**
   - After installation, open the Command Palette by pressing `F1` or `Ctrl+Shift+P` on Windows/Linux or `Cmd+Shift+P` on macOS.
   - Type `>Audio-SpectraCLI: Add Sample Code` or `>Audio-SpectraCLI: View Status`.
   - Select either command to activate and use the extension.

4. **Using the Commands**
   - **Add Sample Code**: Inserts sample code for Audio-SpectraCLI into the current editor window.
     - Open any Python file or create a new one.
     - Run the command `Audio-SpectraCLI: Add Sample Code` from the Command Palette.
     - The sample code should appear in the editor.
   - **View Extension Status**: Displays the current status of Audio-SpectraCLI.
     - Run the command `Audio-SpectraCLI: View Status` from the Command Palette.
     - You’ll see a notification indicating that Audio-SpectraCLI is ready to use.

5. **Verify the Extension**
   - Ensure that the Audio-SpectraCLI commands work as expected by following the steps above.
   - You should see notifications for the status and sample code added in the editor.

6. **Customize as Needed**
   - You can modify the inserted code or use the extension as a reference for developing your own custom scripts with Audio-SpectraCLI.

> **Note**: If you encounter issues, check the extension's [README](./README.md) or reach out to contact@adityaseth.in support for troubleshooting.

Enjoy using Audio-SpectraCLI in VS Code!

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code. Also, the user can modify (wrt [v4.1.0](https://github.com/AdityaSeth777/Audio-SpectraCLI/tree/4.1.0)) the Duration (in seconds), Sampling Rate (in Hz), and Block Size.

---

</details>

----

<details>

<summary> Installation & Usage (Using PIP on Windows)</summary>

1. Install using pip (Use pip3 instead, if pip doesn't work.)

```
pip install Audio-SpectraCLI
```

2. Import and use modules

- Create a Python file.
- You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/test.py) as a reference or use the following code :

```python
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, fs=22050, block_size=1024, frequency_range=(1000, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.show()
app.exec_()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code. Also, the user can modify (wrt [v4.1.0](https://github.com/AdityaSeth777/Audio-SpectraCLI/tree/4.1.0)) the Duration (in seconds), Sampling Rate (in Hz), and Block Size.

---

</details>

---

<details>

<summary> Installation & Usage (Using Homebrew and pip on MacOS)</summary>

1. Install using pip (Use pip3 instead, if pip doesn't work.)

```
brew install pyaudio
pip install Audio-SpectraCLI
```

2. Import and use modules

- Create a Python file.
- You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/test.py) as a reference or use the following code :

```python
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, fs=22050, block_size=1024, frequency_range=(1000, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.show()
app.exec_()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code. Also, the user can modify (wrt [v4.1.0](https://github.com/AdityaSeth777/Audio-SpectraCLI/tree/4.1.0)) the Duration (in seconds), Sampling Rate (in Hz), and Block Size.

---

</details>


---

<details>

<summary> Examining & Usage (Using Docker) </summary>

1. Prerequisites
   You should have docker installed on your machine. You can download and install Docker from [here](https://www.docker.com/products/docker-desktop).
2. Pulling the Docker Image

You can pull the pre-built Docker image from Docker Hub using the following command:

```sh
docker pull adityaseth777/audio-spectracli
```

3. Viewing Files Inside the Docker Container
   For seeing the files inside the Docker container for debugging purposes, you can run an interactive shell session:

```sh
docker run --rm -it --entrypoint /bin/bash audio-spectracli
```

4. Use the 'ls' command to view the files and get a proper understanding of the file structure :

```sh
ls
```

5. You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/test.py) as a reference or use the following code :

```python
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, fs=22050, block_size=1024, frequency_range=(1000, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.show()
app.exec_()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code. Also, the user can modify (wrt [v4.1.0](https://github.com/AdityaSeth777/Audio-SpectraCLI/tree/4.1.0)) the Duration (in seconds), Sampling Rate (in Hz), and Block Size.

---

</details>

---

<details>

<summary> Building the Docker Image Locally </summary>

If you prefer to build the Docker image locally, follow these steps:

1. Clone the repository :

```sh
git clone https://github.com/AdityaSeth777/Audio-SpectraCLI.git
cd Audio-SpectraCLI
```

2. Build the Docker image:

```sh
docker build -t audio-spectracli .
```

3. Viewing Files Inside the Docker Container
   For seeing the files inside the Docker container for debugging purposes, you can run an interactive shell session:

```sh
docker run --rm -it --entrypoint /bin/bash audio-spectracli
```

4. Use the 'ls' command to view the files and get a proper understanding of the file structure :

```sh
ls
```

5. You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/test.py) as a reference or use the following code :

```python
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, fs=22050, block_size=1024, frequency_range=(1000, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.show()
app.exec_()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code. Also, the user can modify (wrt [v4.1.0](https://github.com/AdityaSeth777/Audio-SpectraCLI/tree/4.1.0)) the Duration (in seconds), Sampling Rate (in Hz), and Block Size.

</details>

---

## Web & Extension Additions

Audio-SpectraCLI is expanding beyond the native Python CLI into a small
family of products that all sit on top of the same FFT/DSP approach:

- **Hosted web visualizer** (`web/`) - a Next.js app with a client-side
  (browser-only, mic audio never leaves the device) visualizer, free vs.
  paid tiers (waterfall/tuner/export/presets are paid), Clerk accounts, and
  Stripe subscription billing. See [web/README.md](./web/README.md) for
  setup - it needs your own Clerk, Stripe, and Postgres (Neon) credentials
  to run.
- **Live VS Code extension** (`audiospectra-cli/`) - the extension now
  spawns `python -m Audio_SpectraCLI.headless` and streams the live
  spectrum into a real webview panel inside VS Code (`Audio-SpectraCLI:
  Start/Stop Live Visualization`), instead of only inserting a code
  snippet. Requires Python + this package installed and on your `PATH`
  (configurable via the `audioSpectraCli.pythonPath` setting). See
  [audiospectra-cli/README.md](./audiospectra-cli/README.md).
- **Data/Analysis API** (`web/app/api/v1/analyze`) - a server-side HTTP API
  for third parties: send WAV audio or raw PCM samples, get back spectrum
  and dominant-frequency JSON. Authenticated with per-account API keys,
  rate-limited, and billed on a usage basis. See
  [web/README.md](./web/README.md) for the request/response shape.

The native Python CLI (`main.py`/`AudioSpectrumVisualizer`) is unaffected -
it now runs on the same shared `engine.py` internally, but its behavior and
public API are unchanged.

## Upcoming Features

- CLI endpoints. ✅ Done - see `python -m Audio_SpectraCLI.headless` above.
- Save and Export: ✅ Done in the web visualizer (PNG export, paid tier).
  Native GUI export is still open.
- Option to choose between CLI/GUI. ✅ Done - `main.py` (GUI) vs.
  `headless.py` (CLI/JSON streaming) both run on the same engine.
- Server-side decoding of compressed audio formats (MP3/AAC) for the
  Analysis API - currently WAV-only.
- A shared, multi-instance-safe rate limiter (e.g. Redis/Upstash) for the
  Analysis API - the current one is in-memory, single-instance only.

---

## For contributing

Check the [Contributing page.](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/Contributing.md)

## License

[MIT © Aditya Seth](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/LICENSE)

## What next?

I will be improving this project.

## Where to contact ?

Contact: [contact@adityaseth.in](mailto:contact@adityaseth.in?subject=Email%20owing%20to%20adityaseth.in&body=Greetings%2C%0AI%20am%20%5Bname%5D.%20I%20just%20came%20across%20your%20website%20and%20was%20hoping%20to%20talk%20to%20you%20about%20something.)

## 🙋‍♂️ Support

💙 If you like this project, give it a ⭐ and share it with friends! <br><br>

[<img width="200" height="70" src="https://i.postimg.cc/R0cqPmDf/bmc-button.png" alt="buymeacoffee">](https://www.buymeacoffee.com/adityaseth)

---

# Made with <img width="40" height="40" src="https://img.icons8.com/clouds/100/love-circled.png" alt="love-circled"/> and <img width="40" height="40" src="https://img.icons8.com/clouds/100/python.png" alt="python"/>