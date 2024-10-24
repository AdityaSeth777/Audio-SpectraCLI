const esbuild = require("esbuild");

const production = process.argv.includes('--production');
const watch = process.argv.includes('--watch');

/**
 * @type {import('esbuild').Plugin}
 */
const esbuildProblemMatcherPlugin = {
	name: 'esbuild-problem-matcher',

	setup(build) {
		build.onStart(() => {
			console.log('[watch] build started');
		});
		build.onEnd((result) => {
			result.errors.forEach(({ text, location }) => {
				console.error(`✘ [ERROR] ${text}`);
				console.error(`    ${location.file}:${location.line}:${location.column}:`);
			});
			if (result.errors.length === 0) {
				console.log('[watch] build finished successfully');
			}
		});
	},
};

async function main() {
	const ctx = await esbuild.context({
		entryPoints: [
			'src/extension.ts'  // Points to your extension's main TypeScript file
		],
		bundle: true,
		format: 'cjs',        // CommonJS format, necessary for Node.js
		minify: production,   // Minifies if in production mode
		sourcemap: !production, // Include sourcemap in non-production builds
		sourcesContent: false, 
		platform: 'node',     // Target Node.js environment
		outfile: 'dist/extension.js',  // Output location
		external: ['vscode'], // Keep 'vscode' as an external module
		logLevel: 'silent',
		plugins: [
			/* add to the end of plugins array */
			esbuildProblemMatcherPlugin,
		],
	});
	if (watch) {
		await ctx.watch();  // Watch mode for development
	} else {
		await ctx.rebuild(); // One-time build
		await ctx.dispose(); // Clean up resources
	}
}

main().catch(e => {
	console.error(e);
	process.exit(1);
});
