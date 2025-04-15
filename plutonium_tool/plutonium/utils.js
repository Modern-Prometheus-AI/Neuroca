/**
 * Plutonium Utilities Module
 *
 * Provides common utility functions used across all Plutonium tools.
 */

const { execSync } = require("child_process")

// ANSI color codes for terminal output
const colors = {
	reset: "\x1b[0m",
	bright: "\x1b[1m",
	dim: "\x1b[2m",
	underscore: "\x1b[4m",
	blink: "\x1b[5m",
	reverse: "\x1b[7m",
	hidden: "\x1b[8m",

	black: "\x1b[30m",
	red: "\x1b[31m",
	green: "\x1b[32m",
	yellow: "\x1b[33m",
	blue: "\x1b[34m",
	magenta: "\x1b[35m",
	cyan: "\x1b[36m",
	white: "\x1b[37m",

	bgBlack: "\x1b[40m",
	bgRed: "\x1b[41m",
	bgGreen: "\x1b[42m",
	bgYellow: "\x1b[43m",
	bgBlue: "\x1b[44m",
	bgMagenta: "\x1b[45m",
	bgCyan: "\x1b[46m",
	bgWhite: "\x1b[47m",
}

/**
 * Log formatted message to console
 */
function log(message, level = "info") {
	const prefix = {
		info: `${colors.blue}ℹ${colors.reset}`,
		success: `${colors.green}✓${colors.reset}`,
		warning: `${colors.yellow}⚠️${colors.reset}`,
		error: `${colors.red}✖${colors.reset}`,
		heading: `${colors.magenta}${colors.bright}▶${colors.reset}`,
	}

	console.log(`${prefix[level] || ""} ${message}`)
}

/**
 * Display a heading
 */
function heading(title) {
	log(`\n${colors.bright}${colors.magenta}${title}${colors.reset}`, "heading")
}

/**
 * Run a command and return the output
 */
function runCommand(command, options = {}) {
	const { silent = false } = options

	try {
		const output = execSync(command, {
			encoding: "utf8",
			stdio: silent ? "pipe" : "inherit",
		})

		return { success: true, output }
	} catch (error) {
		if (silent) {
			return {
				success: false,
				error: error.message,
				stdout: error.stdout,
				stderr: error.stderr,
			}
		} else {
			console.error(`${colors.red}Command failed: ${command}${colors.reset}`)
			console.error(error.message)
			return { success: false }
		}
	}
}

module.exports = {
	colors,
	log,
	heading,
	runCommand,
}
