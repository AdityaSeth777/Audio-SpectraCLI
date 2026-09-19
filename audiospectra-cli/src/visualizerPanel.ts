import * as vscode from "vscode";
import { ChildProcessWithoutNullStreams, spawn } from "child_process";
import { SpectrumFrame, parseFrameLines } from "./lineParser";

/**
 * Owns the live-visualization webview panel and the headless Python process
 * (`python -m Audio_SpectraCLI.headless`) that streams FFT frames to it as
 * newline-delimited JSON on stdout. This is what makes the extension
 * actually "live" - earlier versions only inserted a code snippet.
 */
export class LiveVisualizerPanel {
  public static current: LiveVisualizerPanel | undefined;

  private readonly panel: vscode.WebviewPanel;
  private process: ChildProcessWithoutNullStreams | undefined;
  private stdoutBuffer = "";
  private frameListeners: Array<(frame: SpectrumFrame) => void> = [];
  private disposeListeners: Array<() => void> = [];

  public static createOrShow(extensionUri: vscode.Uri): LiveVisualizerPanel {
    if (LiveVisualizerPanel.current) {
      LiveVisualizerPanel.current.panel.reveal();
      return LiveVisualizerPanel.current;
    }

    const panel = vscode.window.createWebviewPanel(
      "audioSpectraCliLiveVisualizer",
      "Audio-SpectraCLI: Live Visualizer",
      vscode.ViewColumn.Beside,
      { enableScripts: true, retainContextWhenHidden: true },
    );

    LiveVisualizerPanel.current = new LiveVisualizerPanel(panel, extensionUri);
    return LiveVisualizerPanel.current;
  }

  private constructor(panel: vscode.WebviewPanel, _extensionUri: vscode.Uri) {
    this.panel = panel;
    const config = vscode.workspace.getConfiguration("audioSpectraCli");
    const barColor = config.get<string>("visualizerColor", "#3b82f6");
    this.panel.webview.html = this.getHtml(barColor);
    this.panel.onDidDispose(() => this.dispose());
    this.startProcess();
  }

  /**
   * Subscribes to every parsed frame as it arrives, in addition to the
   * frame being posted into the webview. Used to drive UI that lives
   * outside the webview, e.g. a status bar item. Returns a disposable to
   * unsubscribe.
   */
  public onFrame(listener: (frame: SpectrumFrame) => void): vscode.Disposable {
    this.frameListeners.push(listener);
    return new vscode.Disposable(() => {
      this.frameListeners = this.frameListeners.filter((l) => l !== listener);
    });
  }

  /** Subscribes to this panel being disposed (stopped or closed). Returns a disposable to unsubscribe. */
  public onDispose(listener: () => void): vscode.Disposable {
    this.disposeListeners.push(listener);
    return new vscode.Disposable(() => {
      this.disposeListeners = this.disposeListeners.filter((l) => l !== listener);
    });
  }

  private startProcess() {
    const config = vscode.workspace.getConfiguration("audioSpectraCli");
    const pythonPath = config.get<string>("pythonPath", "python3");
    const fs = config.get<number>("sampleRate", 44100);
    const blockSize = config.get<number>("blockSize", 4096);
    const bars = config.get<number>("bars", 64);

    this.process = spawn(pythonPath, [
      "-m",
      "Audio_SpectraCLI.headless",
      "--fs",
      String(fs),
      "--block-size",
      String(blockSize),
      "--bars",
      String(bars),
    ]);

    this.process.stdout.on("data", (chunk: Buffer) => this.handleStdout(chunk));

    this.process.stderr.on("data", (chunk: Buffer) => {
      this.panel.webview.postMessage({ type: "error", message: chunk.toString() });
    });

    this.process.on("error", (err) => {
      this.panel.webview.postMessage({
        type: "error",
        message: `Failed to start "${pythonPath}": ${err.message}. Set "audioSpectraCli.pythonPath" if Python isn't on your PATH.`,
      });
    });

    this.process.on("exit", (code) => {
      this.panel.webview.postMessage({ type: "stopped", code });
    });
  }

  private handleStdout(chunk: Buffer) {
    const { frames, remainder } = parseFrameLines(this.stdoutBuffer, chunk.toString());
    this.stdoutBuffer = remainder;
    for (const frame of frames) {
      this.panel.webview.postMessage({ type: "frame", frame });
      for (const listener of this.frameListeners) {
        listener(frame);
      }
    }
  }

  public dispose() {
    this.process?.kill();
    this.process = undefined;
    LiveVisualizerPanel.current = undefined;
    this.panel.dispose();
    for (const listener of this.disposeListeners) {
      listener();
    }
    this.frameListeners = [];
    this.disposeListeners = [];
  }

  private getHtml(barColor: string): string {
    return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<style>
  body { margin: 0; background: #000; color: #ddd; font-family: sans-serif; }
  #status { padding: 4px 8px; font-size: 12px; color: #999; }
  #error { padding: 4px 8px; font-size: 12px; color: #f66; white-space: pre-wrap; }
  canvas { display: block; width: 100%; height: 400px; }
</style>
</head>
<body>
  <div id="status">Starting...</div>
  <div id="error"></div>
  <canvas id="canvas"></canvas>
  <script>
    const BAR_COLOR = ${JSON.stringify(barColor)};
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const statusEl = document.getElementById('status');
    const errorEl = document.getElementById('error');

    function resize() {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    window.addEventListener('message', (event) => {
      const message = event.data;
      if (message.type === 'frame') {
        statusEl.textContent = 'Live';
        drawFrame(message.frame);
      } else if (message.type === 'error') {
        errorEl.textContent = message.message;
      } else if (message.type === 'stopped') {
        statusEl.textContent = 'Stopped (exit code ' + message.code + ')';
      }
    });

    function drawFrame(frame) {
      const { spectrum } = frame;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = canvas.width / spectrum.length;
      const maxVal = Math.max(1e-6, ...spectrum);
      for (let i = 0; i < spectrum.length; i++) {
        const barHeight = (spectrum[i] / maxVal) * canvas.height;
        ctx.fillStyle = BAR_COLOR;
        ctx.fillRect(i * barWidth, canvas.height - barHeight, barWidth - 1, barHeight);
      }
    }
  </script>
</body>
</html>`;
  }
}
