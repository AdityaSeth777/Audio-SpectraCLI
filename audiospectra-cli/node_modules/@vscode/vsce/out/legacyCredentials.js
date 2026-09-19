"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.LegacyMigrationError = void 0;
exports.readLegacyCredential = readLegacyCredential;
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
const validation_1 = require("./validation");
const windowsKeytar_1 = require("./windowsKeytar");
class LegacyMigrationError extends Error {
}
exports.LegacyMigrationError = LegacyMigrationError;
const runCredentialCommand = (file, args, env) => new Promise((resolve, reject) => {
    (0, child_process_1.execFile)(file, args, {
        encoding: 'utf8',
        env,
        windowsHide: true,
        timeout: 30_000,
        maxBuffer: 1024 * 1024,
    }, (error, stdout, stderr) => {
        if (error && (typeof error.code !== 'number' || error.killed)) {
            // Child-process errors can contain stdout/stderr, including PATs.
            const reason = error.code === 'ENOENT' ? 'is not installed'
                : error.killed ? 'timed out or was terminated'
                    : 'failed to read the previous credential';
            reject(new LegacyMigrationError(`${path.basename(file)} ${reason}.`));
        }
        else {
            resolve({ stdout, stderr, exitCode: typeof error?.code === 'number' ? error.code : 0 });
        }
    });
});
function parseWindowsCredential(stdout, name) {
    let value;
    try {
        value = JSON.parse(stdout);
    }
    catch (error) {
        if (!(error instanceof SyntaxError)) {
            throw error;
        }
        throw new LegacyMigrationError('The Windows credential reader returned an invalid response.');
    }
    if (value === null) {
        return undefined;
    }
    if (!value || typeof value !== 'object'
        || !('name' in value) || typeof value.name !== 'string' || value.name.toLowerCase() !== name.toLowerCase()
        || !('pat' in value) || typeof value.pat !== 'string' || !value.pat) {
        throw new LegacyMigrationError('The Windows credential reader returned an invalid credential.');
    }
    return { name, pat: value.pat };
}
async function readLegacyCredential(serviceName, publisherName, { platform = process.platform, run = runCredentialCommand } = {}) {
    (0, validation_1.validatePublisher)(publisherName);
    if (platform === 'win32') {
        const powershell = path.win32.join(process.env.SystemRoot ?? 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
        const { stdout, exitCode } = await run(powershell, [
            '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', windowsKeytar_1.windowsKeytarReadScript,
        ], { ...process.env, VSCE_KEYTAR_SERVICE: serviceName, VSCE_KEYTAR_ACCOUNT: publisherName });
        if (exitCode !== 0) {
            throw new LegacyMigrationError('Windows PowerShell could not read the previous credential.');
        }
        return parseWindowsCredential(stdout, publisherName);
    }
    if (platform !== 'linux') {
        return undefined;
    }
    const { stdout, stderr, exitCode } = await run('secret-tool', [
        'lookup', 'service', serviceName, 'account', publisherName,
        'xdg:schema', 'org.freedesktop.Secret.Generic',
    ]);
    // secret-tool exits 1 without output when no item matches; other failures
    // must not masquerade as a missing credential or expose raw diagnostics.
    if (exitCode === 1 && !stdout && !stderr) {
        return undefined;
    }
    if (exitCode !== 0 || !stdout) {
        throw new LegacyMigrationError('secret-tool could not read the previous credential.');
    }
    return { name: publisherName, pat: stdout };
}
//# sourceMappingURL=legacyCredentials.js.map