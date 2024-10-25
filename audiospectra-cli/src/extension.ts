import * as vscode from 'vscode';

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

// Activation function
export function activate(context: vscode.ExtensionContext) {
    console.log('Audio-SpectraCLI extension is now active.');

    let addCodeCommand = vscode.commands.registerCommand('extension.addSpectraCode', addSpectraCode);
    let viewStatusCommand = vscode.commands.registerCommand('extension.viewSpectraCLIStatus', viewSpectraCLIStatus);

    context.subscriptions.push(addCodeCommand);
    context.subscriptions.push(viewStatusCommand);
}

// Deactivation function
export function deactivate() {
    console.log('Audio-SpectraCLI extension deactivated.');
}
