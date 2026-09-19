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
exports.LegacyCredentialMigration = void 0;
const crypto_1 = require("crypto");
const fs = __importStar(require("fs"));
const os_1 = require("os");
const path = __importStar(require("path"));
const proper_lockfile_1 = require("proper-lockfile");
const legacyCredentials_1 = require("./legacyCredentials");
const util_1 = require("./util");
const validation_1 = require("./validation");
// Decorate the native store so migration policy and write synchronization stay
// separate from its ordinary credential operations.
class LegacyCredentialMigration {
    store;
    openStore;
    static wrap(store, openStore, options = {}) {
        const platform = options.platform ?? process.platform;
        return platform === 'win32' || platform === 'linux'
            ? new LegacyCredentialMigration(store, openStore, options)
            : store;
    }
    serviceName;
    platform;
    lockPath;
    interactive;
    prompt;
    readCredential;
    constructor(store, openStore, options = {}) {
        this.store = store;
        this.openStore = openStore;
        this.serviceName = options.serviceName ?? 'vscode-vsce';
        this.platform = options.platform ?? process.platform;
        this.lockPath = options.lockPath ?? path.join((0, os_1.homedir)(), '.vsce-keytar-migration', (0, crypto_1.createHash)('sha256').update(`${this.platform}:${this.serviceName}`).digest('hex'));
        // read() otherwise answers "y" in tests and non-interactive processes.
        this.interactive = options.interactive ?? Boolean(process.stdin.isTTY && process.stdout.isTTY && !process.env.VSCE_TESTS);
        this.prompt = options.prompt ?? util_1.read;
        this.readCredential = options.readCredential
            ?? ((service, name) => (0, legacyCredentials_1.readLegacyCredential)(service, name, { platform: this.platform }));
    }
    get size() {
        return this.store.size;
    }
    get(name) {
        return this.findPublisher(this.store, name);
    }
    async add(publisher) {
        await this.withLock(() => this.store.add({
            name: this.get(publisher.name)?.name ?? publisher.name,
            pat: publisher.pat,
        }));
    }
    async delete(name) {
        await this.withLock(() => this.store.delete(this.get(name)?.name ?? name));
    }
    [Symbol.iterator]() {
        return this.store[Symbol.iterator]();
    }
    async tryMigratePublisher(name) {
        (0, validation_1.validatePublisher)(name);
        const existing = this.get(name);
        if (existing || !this.interactive || (this.platform !== 'win32' && this.platform !== 'linux')) {
            return existing;
        }
        try {
            const legacy = await this.readCredential(this.serviceName, name);
            if (!legacy) {
                return undefined;
            }
            if (!this.sameAccount(legacy.name, name) || !legacy.pat) {
                throw new legacyCredentials_1.LegacyMigrationError('The legacy credential reader returned an invalid credential.');
            }
            const answer = await this.prompt(`A saved PAT for publisher '${name}' was found in the previous credential store. Copy it to the new store? [y/N] `);
            if (!/^y$/i.test(answer.trim())) {
                return undefined;
            }
            // Do not hold a cross-process lock while waiting for the user's answer.
            return await this.withLock(() => this.copyAndVerify({ name, pat: legacy.pat }));
        }
        catch (error) {
            if (!(error instanceof legacyCredentials_1.LegacyMigrationError)) {
                throw error;
            }
            util_1.log.warn(`${error.message} The previous credential was not changed. `
                + (this.platform === 'linux' ? 'Legacy lookup requires secret-tool (libsecret-tools on Debian/Ubuntu) and an accessible desktop keyring. ' : '')
                + 'Enter a PAT to continue, or retry after resolving the credential-store problem.');
            return undefined;
        }
    }
    async copyAndVerify(publisher) {
        let verified;
        try {
            const destination = await this.openStore();
            const current = this.findPublisher(destination, publisher.name);
            if (current) {
                this.store = destination;
                return current;
            }
            await destination.add(publisher);
            verified = await this.openStore();
            const saved = this.findPublisher(verified, publisher.name);
            if (saved?.pat !== publisher.pat) {
                throw new legacyCredentials_1.LegacyMigrationError('The copied PAT could not be verified.');
            }
        }
        catch (error) {
            if (!(error instanceof Error)) {
                throw error;
            }
            // Native failures must not include secret values in CLI diagnostics.
            throw new legacyCredentials_1.LegacyMigrationError(`Could not copy and verify the previous PAT for publisher '${publisher.name}'.`);
        }
        this.store = verified;
        util_1.log.info(`Copied the saved PAT for publisher '${publisher.name}'. The previous credential was not changed.`);
        return publisher;
    }
    sameAccount(a, b) {
        return this.platform === 'win32' ? a.toLowerCase() === b.toLowerCase() : a === b;
    }
    findPublisher(store, name) {
        return [...store].find(publisher => this.sameAccount(publisher.name, name));
    }
    async withLock(operation) {
        let release;
        try {
            await fs.promises.mkdir(this.lockPath, { recursive: true, mode: 0o700 });
            release = await (0, proper_lockfile_1.lock)(this.lockPath, {
                stale: 120_000,
                update: 5_000,
                retries: { retries: 120, factor: 1, minTimeout: 250, maxTimeout: 250 },
            });
        }
        catch (error) {
            if (error instanceof Error && 'code' in error) {
                throw new legacyCredentials_1.LegacyMigrationError('Could not lock the credential store. Another vsce command may still be using it.');
            }
            throw error;
        }
        try {
            return await operation();
        }
        finally {
            await release();
        }
    }
}
exports.LegacyCredentialMigration = LegacyCredentialMigration;
//# sourceMappingURL=keytarMigration.js.map