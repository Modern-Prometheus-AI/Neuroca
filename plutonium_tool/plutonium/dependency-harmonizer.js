/**
 * Plutonium Dependency Harmonizer Module
 *
 * Synchronizes dependency versions between main and webview packages
 * to ensure consistency across the project.
 */

const fs = require("fs")
const path = require("path")
const { parseVersion, getHigherVersion } = require("./dependency-checker")

// Configuration paths are relative to repo root
const ROOT_DIR = path.resolve(__dirname, "../..")
const MAIN_PACKAGE_JSON = path.join(ROOT_DIR, "package.json")
const WEBVIEW_PACKAGE_JSON = path.join(ROOT_DIR, "webview-ui", "package.json")

/**
 * Harmonize dependency versions between main and webview packages
 */
function harmonizeDependencies(options, utils) {
	const { log, heading, colors } = utils

	heading("Harmonizing Dependencies")
	log("Synchronizing versions between main and webview-ui packages...")

	try {
		// Read package.json files
		const mainPkg = JSON.parse(fs.readFileSync(MAIN_PACKAGE_JSON, "utf8"))
		const webviewPkg = JSON.parse(fs.readFileSync(WEBVIEW_PACKAGE_JSON, "utf8"))

		// Track changes
		const changes = {
			main: [],
			webview: [],
		}

		// Combine all dependency types
		const dependencyTypes = ["dependencies", "devDependencies"]

		// Process each dependency type
		dependencyTypes.forEach((depType) => {
			const mainDeps = mainPkg[depType] || {}
			const webviewDeps = webviewPkg[depType] || {}

			// Find shared dependencies
			const sharedDeps = Object.keys(mainDeps).filter((dep) => webviewDeps[dep])

			heading(`Checking ${sharedDeps.length} shared ${depType}...`)

			// Compare versions for each shared dependency
			sharedDeps.forEach((dep) => {
				const mainVersion = mainDeps[dep]
				const webviewVersion = webviewDeps[dep]

				if (mainVersion !== webviewVersion) {
					const higherVersion = getHigherVersion(mainVersion, webviewVersion)

					// Update versions
					if (higherVersion !== mainVersion) {
						mainDeps[dep] = higherVersion
						changes.main.push({
							name: dep,
							from: mainVersion,
							to: higherVersion,
						})
					}

					if (higherVersion !== webviewVersion) {
						webviewDeps[dep] = higherVersion
						changes.webview.push({
							name: dep,
							from: webviewVersion,
							to: higherVersion,
						})
					}

					log(
						`  ${colors.yellow}${dep}${colors.reset}: main(${mainVersion}) vs webview(${webviewVersion}) → ${colors.green}${higherVersion}${colors.reset}`,
					)
				}
			})
		})

		// Write updated package.json files if --fix flag is used
		if (options.fix) {
			fs.writeFileSync(MAIN_PACKAGE_JSON, JSON.stringify(mainPkg, null, 2) + "\n")
			fs.writeFileSync(WEBVIEW_PACKAGE_JSON, JSON.stringify(webviewPkg, null, 2) + "\n")

			log("\nUpdated package.json files with harmonized dependencies", "success")
			log(`  - Updated ${changes.main.length} dependencies in main package.json`)
			log(`  - Updated ${changes.webview.length} dependencies in webview-ui/package.json`)

			// Next steps
			log("\nTo update the lock files, run:")
			log(`  ${colors.yellow}npm install && cd webview-ui && npm install${colors.reset}`)
		} else {
			log(`\n${colors.yellow}Run with --fix flag to apply these changes${colors.reset}`)
		}

		return {
			changes,
			totalChanges: changes.main.length + changes.webview.length,
		}
	} catch (error) {
		log(`Error: ${error.message}`, "error")
		process.exit(1)
	}
}

// Export module functions
module.exports = {
	harmonizeDependencies,
}
