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
exports.lintFiles = lintFiles;
exports.lintText = lintText;
exports.getRuleNameFromRuleId = getRuleNameFromRuleId;
exports.prettyPrintLintResult = prettyPrintLintResult;
const os = __importStar(require("os"));
const path = __importStar(require("path"));
const util_1 = require("util");
const url_1 = require("url");
const util_2 = require("./util");
const secretsScanningRules = [
    {
        id: "@secretlint/secretlint-rule-preset-recommend",
        rules: [
            {
                id: "@secretlint/secretlint-rule-basicauth",
                allowMessageIds: ["BasicAuth"]
            },
            {
                id: "@secretlint/secretlint-rule-privatekey",
                options: {
                    allows: [
                        // Allow all keys which do not start and end with the BEGIN/END PRIVATE KEY and has at least 50 characters in between
                        // https://github.com/microsoft/vscode-vsce/issues/1147
                        "/^(?![\\s\\S]*-----BEGIN .*PRIVATE KEY-----[A-Za-z0-9+/=\\r\\n]{50,}-----END .*PRIVATE KEY-----)[\\s\\S]*$/"
                    ]
                }
            }, {
                id: "@secretlint/secretlint-rule-npm",
                options: {
                    allows: [
                        // An npm token has the prefix npm_ followed by 36 Base62 characters (30 random + 6-character checksum), totaling 40 characters.
                        // https://github.com/microsoft/vscode-vsce/issues/1153
                        "/^(?!(?:npm_[0-9A-Za-z]{36})$).+$/"
                    ]
                }
            }
        ]
    }
];
const dotEnvRules = [
    {
        id: "@secretlint/secretlint-rule-no-dotenv"
    }
];
async function getConfig(scanSecrets, scanDotEnv) {
    const [{ creator: recommend }, { creator: noDotenv }] = await Promise.all([
        importSecretLintRule("@secretlint/secretlint-rule-preset-recommend"),
        importSecretLintRule("@secretlint/secretlint-rule-no-dotenv")
    ]);
    const rules = [];
    if (scanSecrets) {
        rules.push({
            ...secretsScanningRules[0],
            rule: recommend
        });
    }
    if (scanDotEnv) {
        rules.push({
            ...dotEnvRules[0],
            rule: noDotenv
        });
    }
    return { rules };
}
function importSecretLintRule(packageName) {
    return import(packageName);
}
async function mapConcurrently(values, mapper) {
    const results = new Array(values.length);
    let nextIndex = 0;
    async function worker() {
        while (nextIndex < values.length) {
            const index = nextIndex++;
            results[index] = await mapper(values[index]);
        }
    }
    const workerCount = Math.min(os.availableParallelism(), values.length);
    await Promise.all(Array.from({ length: workerCount }, worker));
    return results;
}
async function lintFiles(filePaths, scanSecrets, scanDotEnv) {
    let results;
    try {
        const [{ lintSource }, { createRawSource }, config] = await Promise.all([
            import("@secretlint/core"),
            import("@secretlint/source-creator"),
            getConfig(scanSecrets, scanDotEnv)
        ]);
        results = await mapConcurrently(filePaths, async (filePath) => lintSource({
            source: await createRawSource(filePath),
            options: {
                config,
                maskSecrets: false
            }
        }));
    }
    catch (error) {
        util_2.log.error('Error occurred while scanning secrets (files):', error);
        process.exit(1);
    }
    return parseResult(results);
}
async function lintText(content, fileName, scanSecrets, scanDotEnv) {
    let result;
    try {
        const [{ lintSource }, config] = await Promise.all([
            import("@secretlint/core"),
            getConfig(scanSecrets, scanDotEnv)
        ]);
        result = await lintSource({
            source: {
                content,
                filePath: fileName,
                ext: path.extname(fileName),
                contentType: "text"
            },
            options: {
                config,
                maskSecrets: false
            }
        });
    }
    catch (error) {
        util_2.log.error('Error occurred while scanning secrets (content):', error);
        process.exit(1);
    }
    return parseResult([result]);
}
function parseResult(fileResults) {
    const results = fileResults.flatMap(fileResult => fileResult.messages.map((message) => ({
        message: message.message,
        ruleId: message.ruleParentId ? `${message.ruleParentId} > ${message.ruleId}` : message.ruleId,
        level: message.severity === "info" ? "note" : message.severity,
        filePath: process.env.SARIF_URI_ABSOLUTE
            ? (0, url_1.pathToFileURL)(fileResult.filePath).toString()
            : path.relative(process.cwd(), fileResult.filePath),
        startLine: fixLine(message.loc.start.line),
        startColumn: fixColumn(message.loc.start.column),
        endLine: fixLine(message.loc.end.line),
        endColumn: fixColumn(message.loc.end.column)
    })));
    return {
        ok: !fileResults.some(fileResult => fileResult.messages.some(message => message.severity === "error")),
        results
    };
}
function fixLine(value) {
    return value === null ? undefined : value === 0 ? 1 : value;
}
function fixColumn(value) {
    return value === null ? undefined : value === 0 ? 1 : value + 1;
}
function getRuleNameFromRuleId(ruleId) {
    const parts = ruleId.split('-rule-');
    return parts[parts.length - 1];
}
function prettyPrintLintResult(result) {
    const text = result.message;
    const title = text.length > 54 ? text.slice(0, 50) + '...' : text;
    const ruleName = getRuleNameFromRuleId(result.ruleId);
    let output = `\t${(0, util_1.styleText)(['bold', result.level === "error" ? 'red' : 'yellow'], title)} [${ruleName}]\n`;
    output += `\t${prettyPrintLocation(result)}\n`;
    return output;
}
function prettyPrintLocation(result) {
    let output = result.filePath;
    const regionStringified = prettyPrintRegion(result);
    if (regionStringified) {
        output += `#${regionStringified}`;
    }
    return output;
}
function prettyPrintRegion(result) {
    const startPosition = prettyPrintPosition(result.startLine, result.startColumn);
    const endPosition = prettyPrintPosition(result.endLine, result.endColumn);
    if (!startPosition) {
        return undefined;
    }
    let output = startPosition;
    if (endPosition && startPosition !== endPosition) {
        output += `-${endPosition}`;
    }
    return output;
}
function prettyPrintPosition(line, column) {
    if (line === undefined) {
        return undefined;
    }
    let output = line.toString();
    if (column !== undefined) {
        output += `:${column}`;
    }
    return output;
}
//# sourceMappingURL=secretLint.js.map