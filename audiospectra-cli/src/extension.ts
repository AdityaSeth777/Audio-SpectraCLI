import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { LiveVisualizerPanel } from './visualizerPanel';
import { computeDominantFrequency } from './lineParser';
import { resolvePresetsDir, sanitizePresetName } from './presetUtils';

// Command to insert Audio-SpectraCLI code into the active editor
function addSpectraCode() {
    const editor = vscode.window.activeTextEditor;
    if (editor) {
        const position = editor.selection.active;

        // Code to insert when the command is called
        const spectraCode = `# Audio-SpectraCLI sample code\nfrom Audio_SpectraCLI import AudioSpectrumVisualizer\nfrom PyQt5.QtWidgets import QApplication\n\napp = QApplication([])\naudio_visualizer = AudioSpectrumVisualizer(duration=5, fs=22050, block_size=1024, frequency_range=(1000, 5000), color='red')\naudio_visualizer.show()\napp.exec_()`;

        editor.edit(editBuilder => {
            editBuilder.insert(position, spectraCode);
        }).then(success => {
            if (success) {
                vscode.window.showInformationMessage('Audio-SpectraCLI code added!');
            } else {
                vscode.window.showErrorMessage('Failed to add Audio-SpectraCLI code.');
            }
        });
    } else {
        vscode.window.showErrorMessage('No active editor found!');
    }
}

// Command to show the Audio-SpectraCLI status
function viewSpectraCLIStatus() {
    vscode.window.showInformationMessage('Audio-SpectraCLI is ready to use!');
}

// Status bar item showing the dominant frequency/peak magnitude of the most
// recently parsed frame while a live visualization is running. Created when
// a panel starts streaming frames and torn down when it stops.
let statusBarItem: vscode.StatusBarItem | undefined;
let statusBarFrameSubscription: vscode.Disposable | undefined;
let statusBarDisposeSubscription: vscode.Disposable | undefined;

function attachStatusBarItem(panel: LiveVisualizerPanel) {
    if (statusBarItem) {
        // Already attached to a running panel.
        return;
    }

    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.text = 'Audio-SpectraCLI: waiting for frames...';
    statusBarItem.show();

    statusBarFrameSubscription = panel.onFrame((frame) => {
        const dominant = computeDominantFrequency(frame);
        if (statusBarItem && dominant) {
            statusBarItem.text = `$(pulse) Audio-SpectraCLI: ${dominant.frequency.toFixed(0)} Hz (peak ${dominant.magnitude.toFixed(2)})`;
        }
    });

    statusBarDisposeSubscription = panel.onDispose(() => disposeStatusBarItem());
}

function disposeStatusBarItem() {
    statusBarFrameSubscription?.dispose();
    statusBarFrameSubscription = undefined;
    statusBarDisposeSubscription?.dispose();
    statusBarDisposeSubscription = undefined;
    statusBarItem?.dispose();
    statusBarItem = undefined;
}

// Command to open the live, in-editor spectrum visualizer webview, backed by
// a spawned `python -m Audio_SpectraCLI.headless` process.
function startLiveVisualization(context: vscode.ExtensionContext) {
    const panel = LiveVisualizerPanel.createOrShow(context.extensionUri);
    attachStatusBarItem(panel);
}

// Command to stop and dispose the live visualizer, if one is running.
function stopLiveVisualization() {
    if (LiveVisualizerPanel.current) {
        LiveVisualizerPanel.current.dispose();
    } else {
        vscode.window.showInformationMessage('Audio-SpectraCLI: no live visualization is running.');
    }
    disposeStatusBarItem();
}

// Command to write the extension's current visualizer settings out as a
// named preset JSON file, in the same `~/.audiospectra_cli/presets/<name>.json`
// format (and `AUDIOSPECTRA_CLI_HOME` override) that the Python-side
// `Audio_SpectraCLI.presets` module reads and writes, so presets are
// interchangeable between the GUI and this extension.
async function saveCurrentFrameAsPreset() {
    const rawName = await vscode.window.showInputBox({
        prompt: 'Name for the new Audio-SpectraCLI preset',
        placeHolder: 'e.g. my-favorite-settings',
    });
    if (rawName === undefined) {
        return; // Cancelled.
    }

    const sanitized = sanitizePresetName(rawName);
    if (!sanitized) {
        vscode.window.showErrorMessage('Audio-SpectraCLI: preset name must contain at least one valid character.');
        return;
    }

    const config = vscode.workspace.getConfiguration('audioSpectraCli');
    const settings = {
        fs: config.get<number>('sampleRate', 44100),
        block_size: config.get<number>('blockSize', 4096),
    };

    const presetsDir = resolvePresetsDir();
    const presetPath = path.join(presetsDir, `${sanitized}.json`);

    try {
        fs.mkdirSync(presetsDir, { recursive: true });
        fs.writeFileSync(presetPath, JSON.stringify(settings, null, 2));
        vscode.window.showInformationMessage(`Audio-SpectraCLI: saved preset "${sanitized}" to ${presetPath}.`);
    } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`Audio-SpectraCLI: failed to save preset "${sanitized}": ${message}`);
    }
}

// Activation function
export function activate(context: vscode.ExtensionContext) {
    console.log('Audio-SpectraCLI extension is now active.');

    let addCodeCommand = vscode.commands.registerCommand('extension.addSpectraCode', addSpectraCode);
    let viewStatusCommand = vscode.commands.registerCommand('extension.viewSpectraCLIStatus', viewSpectraCLIStatus);
    let startLiveCommand = vscode.commands.registerCommand('extension.startLiveVisualization', () =>
        startLiveVisualization(context),
    );
    let stopLiveCommand = vscode.commands.registerCommand('extension.stopLiveVisualization', stopLiveVisualization);
    let savePresetCommand = vscode.commands.registerCommand(
        'extension.saveCurrentFrameAsPreset',
        saveCurrentFrameAsPreset,
    );

    context.subscriptions.push(
        addCodeCommand,
        viewStatusCommand,
        startLiveCommand,
        stopLiveCommand,
        savePresetCommand,
    );
}

// Deactivation function
export function deactivate() {
    LiveVisualizerPanel.current?.dispose();
    disposeStatusBarItem();
    console.log('Audio-SpectraCLI extension deactivated.');
}
