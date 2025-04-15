#!/usr/bin/env node
/**
 * Plutonium - A comprehensive development toolkit for any codebase
 *
 * This unified CLI tool provides multiple operations to enhance development workflow:
 *  - Dependency analysis and harmonization
 *  - Multi-language dependency checking
 *  - Performance profiling and optimization
 *  - Project structure analysis
 *  - Cross-language compatibility checks
 *
 * Usage: node plutonium.js [command] [options]
 *
 * Commands:
 *   deps:check     - Analyze dependencies across multiple languages
 *   deps:harmonize - Synchronize versions of shared dependencies
 *   deps:update    - Intelligently update dependencies with compatibility checks
 *   perf:analyze   - Analyze application performance metrics
 *   struct:analyze - Analyze project structure and suggest optimizations
 *   lang:detect    - Detect languages and frameworks in the project
 *
 * Global Options:
 *   --verbose      - Show detailed output
 *   --json         - Output results as JSON
 *   --help         - Show help information for a command
 */

// Load utility modules
const utils = require("./plutonium/utils")
const { checkDependencies } = require("./plutonium/dependency-checker")
const { harmonizeDependencies } = require("./plutonium/dependency-harmonizer")
const { detectProjectType } = require("./plutonium/language-detector")

// Parse command line arguments
const args = process.argv.slice(2)
const command = args[0] || "help"
const options = {
	verbose: args.includes("--verbose"),
	json: args.includes("--json"),
	fix: args.includes("--fix"),
	help: args.includes("--help"),
	force: args.includes("--force"),
	language: args.find(arg => arg.startsWith("--language="))?.split("=")[1] || "auto",
	path: args.find(arg => arg.startsWith("--path="))?.split("=")[1] || ".",
}

/**
 * Analyze project structure and generate reports
 */
function analyzeStructure() {
	utils.heading("Project Structure Analysis")
	utils.log("Analyzing project structure and organization...")

	// Get project type first
	const projectType = detectProjectType(options.path)
	utils.log(`Detected project type: ${projectType.type}`)
	utils.log(`Primary languages: ${projectType.languages.join(", ")}`)
	
	// Implement recursive directory analysis
	const structureAnalyzer = require("./plutonium/structure-analyzer")
	const result = structureAnalyzer.analyze(options.path, projectType)
	
	if (result.status === "success") {
		utils.log("Project structure analysis completed", "success")
		return result
	} else {
		utils.log("Project structure analysis failed", "error")
		return { status: "failed", error: result.error }
	}
}

/**
 * Analyze performance metrics
 */
function analyzePerformance() {
	utils.heading("Performance Analysis")
	utils.log("Analyzing performance metrics...")

	// Get project type first to determine correct performance analyzer
	const projectType = detectProjectType(options.path)
	utils.log(`Detected project type: ${projectType.type}`)
	
	// Select appropriate performance analyzer based on project type
	const performanceAnalyzer = require("./plutonium/performance-analyzer")
	const result = performanceAnalyzer.analyze(options.path, projectType)

	if (result.status === "success") {
		utils.log("Performance analysis completed", "success")
		return result
	} else {
		utils.log("Performance analysis not implemented for this project type", "warning")
		return { status: "not implemented for " + projectType.type }
	}
}

/**
 * Detect languages and frameworks in the project
 */
function detectLanguages() {
	utils.heading("Language Detection")
	utils.log("Detecting languages and frameworks in the project...")

	// Run the language detector
	const projectType = detectProjectType(options.path)
	
	utils.log(`\nProject Type: ${projectType.type}`, "info")
	utils.log(`Primary Languages:`, "info")
	projectType.languages.forEach(lang => {
		utils.log(`  - ${lang.name}: ${lang.confidence}% confidence`, "info")
	})
	
	if (projectType.frameworks && projectType.frameworks.length > 0) {
		utils.log(`\nFrameworks:`, "info")
		projectType.frameworks.forEach(framework => {
			utils.log(`  - ${framework.name}: ${framework.confidence}% confidence`, "info")
		})
	}
	
	if (projectType.packageManagers && projectType.packageManagers.length > 0) {
		utils.log(`\nPackage Managers:`, "info")
		projectType.packageManagers.forEach(pm => {
			utils.log(`  - ${pm.name}`, "info")
		})
	}
	
	return projectType
}

/**
 * Show help information
 */
function showHelp(command) {
	console.log(
		`${utils.colors.bright}${utils.colors.cyan}Plutonium - Universal Development Toolkit${utils.colors.reset}\n`,
	)

	if (command === "deps:check") {
		console.log("Usage: node plutonium.js deps:check [options]\n")
		console.log("Analyze dependencies across multiple languages\n")
		console.log("Options:")
		console.log("  --language=<lang>  Specify language to analyze (auto, js, python, java, rust, go, etc.)")
		console.log("  --path=<dir>       Path to project directory (default: current directory)")
		console.log("  --verbose          Show detailed analysis")
		console.log("  --json             Output results as JSON")
	} else if (command === "deps:harmonize") {
		console.log("Usage: node plutonium.js deps:harmonize [options]\n")
		console.log("Synchronize versions of shared dependencies\n")
		console.log("Options:")
		console.log("  --language=<lang>  Specify language to analyze (auto, js, python, java, rust, go, etc.)")
		console.log("  --path=<dir>       Path to project directory (default: current directory)")
		console.log("  --fix              Apply the recommended changes")
		console.log("  --verbose          Show detailed changes")
	} else if (command === "deps:update") {
		console.log("Usage: node plutonium.js deps:update [options]\n")
		console.log("Intelligently update dependencies with compatibility checks\n")
		console.log("Options:")
		console.log("  --language=<lang>  Specify language to analyze (auto, js, python, java, rust, go, etc.)")
		console.log("  --path=<dir>       Path to project directory (default: current directory)")
		console.log("  --fix              Apply the recommended updates")
	} else if (command === "perf:analyze") {
		console.log("Usage: node plutonium.js perf:analyze [options]\n")
		console.log("Analyze application performance metrics\n")
		console.log("Options:")
		console.log("  --path=<dir>       Path to project directory (default: current directory)")
		console.log("  --verbose          Show detailed metrics")
	} else if (command === "struct:analyze") {
		console.log("Usage: node plutonium.js struct:analyze [options]\n")
		console.log("Analyze project structure and suggest optimizations\n")
		console.log("Options:")
		console.log("  --path=<dir>       Path to project directory (default: current directory)")
		console.log("  --verbose          Show detailed analysis")
	} else if (command === "lang:detect") {
		console.log("Usage: node plutonium.js lang:detect [options]\n")
		console.log("Detect languages and frameworks in the project\n")
		console.log("Options:")
		console.log("  --path=<dir>       Path to project directory (default: current directory)")
		console.log("  --verbose          Show detailed detection information")
	} else {
		// General help
		console.log(`A comprehensive development toolkit that works with any codebase\n`)
		console.log("Usage: node plutonium.js <command> [options]\n")
		console.log("Commands:")
		console.log("  deps:check        Analyze dependencies across multiple languages")
		console.log("  deps:harmonize    Synchronize versions of shared dependencies")
		console.log("  deps:update       Intelligently update dependencies with compatibility checks")
		console.log("  perf:analyze      Analyze application performance metrics")
		console.log("  struct:analyze    Analyze project structure and suggest optimizations")
		console.log("  lang:detect       Detect languages and frameworks in the project")
		console.log("\nGlobal Options:")
		console.log("  --language=<lang>  Specify language to analyze (auto, js, python, java, rust, go, etc.)")
		console.log("  --path=<dir>       Path to project directory (default: current directory)")
		console.log("  --verbose          Show detailed output")
		console.log("  --json             Output results as JSON")
		console.log("  --fix              Apply recommended changes (for applicable commands)")
		console.log("  --help             Show help information for a command")
		console.log("\nExamples:")
		console.log("  node plutonium.js lang:detect")
		console.log("  node plutonium.js deps:check --language=rust")
		console.log("  node plutonium.js struct:analyze --path=/path/to/project")
	}
}

/**
 * Main function that runs the CLI
 */
function main() {
	console.log(
		`${utils.colors.bright}${utils.colors.magenta}🚀 Plutonium ${utils.colors.dim}v0.2.0 ${utils.colors.reset}${utils.colors.bright}${utils.colors.magenta}(Universal Development Toolkit)${utils.colors.reset}`,
	)

	// If help flag is used, show help and exit
	if (options.help) {
		showHelp(command)
		return
	}

	let result = null

	// Pass utils to each command for consistent logging and formatting
	const utilsWithHelpers = {
		...utils,
		colors: utils.colors,
		log: utils.log,
		heading: utils.heading,
		runCommand: utils.runCommand,
	}

	switch (command) {
		case "deps:check":
			result = checkDependencies(options, utilsWithHelpers)
			break
		case "deps:harmonize":
			result = harmonizeDependencies(options, utilsWithHelpers)
			break
		case "deps:update":
			utils.log("Dependency update feature not yet implemented", "warning")
			break
		case "perf:analyze":
			result = analyzePerformance()
			break
		case "struct:analyze":
			result = analyzeStructure()
			break
		case "lang:detect":
			result = detectLanguages()
			break
		case "help":
			showHelp(args[1])
			break
		default:
			utils.log(`Unknown command: ${command}`, "error")
			console.log("\nRun node plutonium.js help for available commands.")
			process.exit(1)
	}

	// Output JSON if requested
	if (options.json && result) {
		console.log(JSON.stringify(result, null, 2))
	}
}

// Run the CLI
main()
