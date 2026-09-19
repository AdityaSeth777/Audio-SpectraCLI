import * as vscode from 'vscode';
import { LiveVisualizerPanel } from './visualizerPanel';

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

// Command to open the live, in-editor spectrum visualizer webview, backed by
// a spawned `python -m Audio_SpectraCLI.headless` process.
function startLiveVisualization(context: vscode.ExtensionContext) {
    LiveVisualizerPanel.createOrShow(context.extensionUri);
}

// Command to stop and dispose the live visualizer, if one is running.
function stopLiveVisualization() {
    if (LiveVisualizerPanel.current) {
        LiveVisualizerPanel.current.dispose();
    } else {
        vscode.window.showInformationMessage('Audio-SpectraCLI: no live visualization is running.');
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

    context.subscriptions.push(addCodeCommand, viewStatusCommand, startLiveCommand, stopLiveCommand);
}

// Deactivation function
export function deactivate() {
    LiveVisualizerPanel.current?.dispose();
    console.log('Audio-SpectraCLI extension deactivated.');
}
