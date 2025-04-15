/**
 * Plutonium Dependency Checker Module
 *
 * Analyzes dependencies across JavaScript and Python components,
 * finding inconsistencies and generating reports.
 */

const fs = require("fs")
const path = require("path")
const semver = require("semver")

// Configuration paths are relative to repo root
const ROOT_DIR = path.resolve(__dirname, "../..")
const MAIN_PACKAGE_JSON = path.join(ROOT_DIR, "package.json")
const WEBVIEW_PACKAGE_JSON = path.join(ROOT_DIR, "webview-ui", "package.json")
// Corrected path to point to the root requirements.txt
const PYTHON_REQUIREMENTS = path.join(ROOT_DIR, "requirements.txt")
const PYPROJECT_TOML = path.join(ROOT_DIR, "pyproject.toml")
const REPORTS_DIR = path.join(ROOT_DIR, "reports")
const PLUTONIUM_ICON = path.join(__dirname, "assets", "plutonium-icon.png")

// Ensure reports directory exists
if (!fs.existsSync(REPORTS_DIR)) {
	fs.mkdirSync(REPORTS_DIR, { recursive: true })
}

/**
 * 
 * Parse version string to ensure valid semver format
 * Returns a normalized version string or null if invalid
 */
function parseVersion(version) {
	if (!version) {
		return null
	}

	// Remove any leading ^ or ~ characters
	let cleanVersion = version.replace(/^[\^~]/, "")

	// Handle "x" versions like "20.x"
	if (cleanVersion.includes("x")) {
		cleanVersion = cleanVersion.replace(/\.x$/, ".0")
	}

	// Try to coerce to a valid semver
	return semver.valid(semver.coerce(cleanVersion))
}

/**
 * Get the higher version between two version strings
 */
function getHigherVersion(v1, v2) {
	const parsedV1 = parseVersion(v1)
	const parsedV2 = parseVersion(v2)

	if (!parsedV1) {
		return v2
	}
	if (!parsedV2) {
		return v1
	}

	// Compare and return the higher version with the original prefix (^ or ~)
	const prefix1 = v1.startsWith("^") ? "^" : v1.startsWith("~") ? "~" : ""
	const prefix2 = v2.startsWith("^") ? "^" : v2.startsWith("~") ? "~" : ""

	// Choose the prefix from the higher version, or default to ^ for compatibility
	const prefix = semver.gt(parsedV1, parsedV2) ? prefix1 : prefix2 || "^"

	return prefix + (semver.gt(parsedV1, parsedV2) ? parsedV1 : parsedV2)
}

/**
 * Find Python requirements files in a directory
 * 
 * @param {string} dir Directory to search
 * @param {number} depth Maximum depth to search
 * @returns {string[]} Array of requirements files paths
 */
function findRequirementsFiles(dir, depth = 3) {
	if (depth === 0) return [];
	
	let results = [];
	
	try {
		const entries = fs.readdirSync(dir, { withFileTypes: true });
		
		// Check for requirements files in this directory
		const reqFiles = entries
			.filter(entry => !entry.isDirectory() && 
				(entry.name === 'requirements.txt' || 
				 entry.name === 'pyproject.toml' ||
				 entry.name === 'Pipfile' ||
				 entry.name === 'setup.py'))
			.map(entry => path.join(dir, entry.name));
		
		results = results.concat(reqFiles);
		
		// Recursively search subdirectories (but skip common large directories)
		const subDirs = entries
			.filter(entry => entry.isDirectory() && 
				entry.name !== 'node_modules' && 
				entry.name !== '.git' &&
				entry.name !== 'venv' &&
				entry.name !== 'env' &&
				entry.name !== '__pycache__' &&
				!entry.name.startsWith('.'))
			.map(entry => path.join(dir, entry.name));
		
		for (const subDir of subDirs) {
			results = results.concat(findRequirementsFiles(subDir, depth - 1));
		}
	} catch (err) {
		// Skip directories we can't read
	}
	
	return results;
}

/**
 * Read and parse Python requirements from a file
 * 
 * @param {string} filePath Path to requirements file
 * @returns {Object} Parsed requirements
 */
function parsePythonRequirements(filePath) {
	const results = {
		packages: [],
		unpinned: []
	};
	
	try {
		if (path.basename(filePath) === 'requirements.txt') {
			const content = fs.readFileSync(filePath, 'utf8');
			const lines = content.split('\n');
			
			for (const line of lines) {
				const trimmedLine = line.trim();
				// Skip comments and empty lines
				if (!trimmedLine || trimmedLine.startsWith("#")) {
					continue;
				}
				
				// Extract package name and version
				let packageName = trimmedLine.split("#")[0].trim();
				let packageVersion = null;
				
				if (packageName.includes("==")) {
					[packageName, packageVersion] = packageName.split("==");
					packageVersion = '==' + packageVersion;
				} else if (packageName.includes(">=")) {
					[packageName, packageVersion] = packageName.split(">=");
					packageVersion = ">=" + packageVersion;
				} else if (packageName.includes("<=")) {
					[packageName, packageVersion] = packageName.split("<=");
					packageVersion = "<=" + packageVersion;
				} else if (packageName.includes(">")) {
					[packageName, packageVersion] = packageName.split(">");
					packageVersion = ">" + packageVersion;
				} else if (packageName.includes("<")) {
					[packageName, packageVersion] = packageName.split("<");
					packageVersion = "<" + packageVersion;
				} else if (packageName.includes("~=")) {
					[packageName, packageVersion] = packageName.split("~=");
					packageVersion = "~=" + packageVersion;
				} else {
					results.unpinned.push(packageName);
				}
				
				packageName = packageName.trim();
				
				results.packages.push({
					name: packageName,
					version: packageVersion ? packageVersion.trim() : null,
					file: path.basename(filePath)
				});
			}
		}
		// TODO: Add support for pyproject.toml, Pipfile, and setup.py parsing
	} catch (err) {
		console.error(`Error parsing ${filePath}: ${err.message}`);
	}
	
	return results;
}

/**
 * Generate HTML report for dependencies
 */
function generateHtmlReport(data) {
	const timestamp = new Date().toISOString().replace(/T/, " ").replace(/\..+/, "")

	// Create HTML content with styling - using dark theme by default
	const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Plutonium Dependency Analysis</title>
  <style>
    :root {
      color-scheme: dark;
      
      --primary-color: #bb86fc;
      --secondary-color: #03dac6;
      --warning-color: #ffb74d;
      --error-color: #cf6679;
      --success-color: #81c784;
      --background-color: #121212;
      --card-bg: #1e1e1e;
      --text-color: #e0e0e0;
      --border-color: #333333;
    }
    
    @media (prefers-color-scheme: light) {
      :root {
        color-scheme: light;
        
        --primary-color: #6200ee;
        --secondary-color: #03dac6;
        --warning-color: #ff9800;
        --error-color: #b00020;
        --success-color: #4caf50;
        --background-color: #f5f5f5;
        --card-bg: #ffffff;
        --text-color: #333333;
        --border-color: #dddddd;
      }
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.6;
      color: var(--text-color);
      background-color: var(--background-color);
      margin: 0;
      padding: 0;
    }
    
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 20px;
    }
    
    header {
      background-color: rgba(0, 0, 0, 0.2);
      padding: 30px 0;
      text-align: center;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 40px;
    }
    
    .header-content {
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
    }
    
    .header-icon {
      max-width: 188px; /* Adjusted size +25% */
      height: auto;
      margin: 20px 0;
      filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3)); /* Optional shadow */
    }
    
    .timestamp {
      font-size: 16px;
      color: var(--text-color);
      opacity: 0.7;
    }
    
    h1, h2, h3 {
      color: var(--primary-color);
      font-weight: 600;
    }
    
    .card {
      background-color: var(--card-bg);
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      padding: 25px;
      margin-bottom: 30px;
      border: 1px solid var(--border-color);
    }
    
    .info {
      color: var(--primary-color);
    }
    
    .warning {
      color: var(--warning-color);
    }
    
    .error {
      color: var(--error-color);
    }
    
    .success {
      color: var(--success-color);
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 0 0 1px var(--border-color);
    }
    
    th, td {
      padding: 12px 15px;
      text-align: left;
      border-bottom: 1px solid var(--border-color);
    }
    
    th {
      background-color: rgba(187, 134, 252, 0.1);
      font-weight: 600;
      color: var(--primary-color);
      position: sticky;
      top: 0;
    }
    
    tr:hover {
      background-color: rgba(255, 255, 255, 0.03);
    }
    
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    .badge-warning {
      background-color: rgba(255, 183, 77, 0.2);
      color: var(--warning-color);
      border: 1px solid var(--warning-color);
    }
    
    .badge-error {
      background-color: rgba(207, 102, 121, 0.2);
      color: var(--error-color);
      border: 1px solid var(--error-color);
    }
    
    .badge-success {
      background-color: rgba(129, 199, 132, 0.2);
      color: var(--success-color);
      border: 1px solid var(--success-color);
    }
    
    .summary-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }
    
    .stat-card {
      background: linear-gradient(135deg, rgba(187, 134, 252, 0.05), rgba(3, 218, 198, 0.05));
      border-radius: 8px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      border: 1px solid var(--border-color);
    }
    
    .stat-value {
      font-size: 36px;
      font-weight: 700;
      margin: 10px 0;
    }
    
    .stat-label {
      font-size: 16px;
      color: var(--text-color);
      opacity: 0.8;
    }
    
    .status-indicator {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 8px;
    }
    
    .status-warning {
      background-color: var(--warning-color);
    }
    
    .status-error {
      background-color: var(--error-color);
    }
    
    .status-success {
      background-color: var(--success-color);
    }
    
    footer {
      margin-top: 60px;
      padding: 20px 0;
      text-align: center;
      font-size: 14px;
      color: var(--text-color);
      opacity: 0.7;
      border-top: 1px solid var(--border-color);
    }
  </style>
</head>
<body>
  <header>
    <div class="container header-content">
      <img src="../scripts/plutonium/assets/plutonium-icon.png" alt="Plutonium Icon" class="header-icon">
      <p class="timestamp">Dependency Analysis Report • Generated on ${timestamp}</p>
    </div>
  </header>
  
  <div class="container">
    <div class="card">
      <h2>Summary</h2>
      <div class="summary-stats">
        <div class="stat-card">
          <div class="stat-label">Python Packages</div>
          <div class="stat-value">${data.pythonPackages.length}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Main npm Packages</div>
          <div class="stat-value">${data.mainPackages.length}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Webview npm Packages</div>
          <div class="stat-value">${data.webviewPackages.length}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Shared Packages</div>
          <div class="stat-value">${data.sharedPackages.length}</div>
        </div>
      </div>
      
      <h3>Status</h3>
      <ul>
        <li>
          <span class="status-indicator ${data.npmInconsistencies.length > 0 ? "status-warning" : "status-success"}"></span>
          <strong>npm Version Inconsistencies:</strong>
          <span class="${data.npmInconsistencies.length > 0 ? "warning" : "success"}">
            ${data.npmInconsistencies.length}
          </span>
        </li>
        <li>
          <span class="status-indicator ${data.crossLanguageIssues.length > 0 ? "status-warning" : "status-success"}"></span>
          <strong>Cross-language Conflicts:</strong>
          <span class="${data.crossLanguageIssues.length > 0 ? "warning" : "success"}">
            ${data.crossLanguageIssues.length}
          </span>
        </li>
        <li>
          <span class="status-indicator ${data.unpinnedPythonDeps.length > 0 ? "status-warning" : "status-success"}"></span>
          <strong>Unpinned Python Dependencies:</strong>
          <span class="${data.unpinnedPythonDeps.length > 0 ? "warning" : "success"}">
            ${data.unpinnedPythonDeps.length}
          </span>
        </li>
      </ul>
    </div>
    
    ${
		data.npmInconsistencies.length > 0
			? `
    <div class="card">
      <h2>npm Version Inconsistencies</h2>
      <p>The following packages have different versions between main and webview environments:</p>
      <table>
        <thead>
          <tr>
            <th>Package</th>
            <th>Main Version</th>
            <th>Webview Version</th>
            <th>Recommended</th>
          </tr>
        </thead>
        <tbody>
          ${data.npmInconsistencies
				.map(
					(item) => `
            <tr>
              <td>${item.name}</td>
              <td>${item.mainVersion}</td>
              <td>${item.webviewVersion}</td>
              <td><span class="success">${item.recommended}</span></td>
            </tr>
          `,
				)
				.join("")}
        </tbody>
      </table>
    </div>
    `
			: ""
	}
    
    ${
		data.crossLanguageIssues.length > 0
			? `
    <div class="card">
      <h2>Cross-language Dependency Conflicts</h2>
      <p>Potential version conflicts between Python and JavaScript packages:</p>
      <table>
        <thead>
          <tr>
            <th>Package</th>
            <th>Python Version</th>
            <th>JavaScript Version</th>
          </tr>
        </thead>
        <tbody>
          ${data.crossLanguageIssues
				.map(
					(item) => `
            <tr>
              <td>${item.name}</td>
              <td>${item.pythonVersion}</td>
              <td>${item.jsVersion}</td>
            </tr>
          `,
				)
				.join("")}
        </tbody>
      </table>
      <p class="info"><i>Note: Review these packages to ensure version compatibility between languages</i></p>
    </div>
    `
			: ""
	}
    
    ${
		data.unpinnedPythonDeps.length > 0
			? `
    <div class="card">
      <h2>Unpinned Python Dependencies</h2>
      <p>The following Python dependencies are not pinned to specific versions:</p>
      <ul>
        ${data.unpinnedPythonDeps
			.map(
				(dep) => `
          <li>${dep}</li>
        `,
			)
			.join("")}
      </ul>
      <p class="warning">Unpinned dependencies can lead to inconsistent builds and security issues. Consider pinning these dependencies to specific versions.</p>
    </div>
    `
			: ""
	}
    
    <div class="card">
      <h2>All Dependencies</h2>
      
      <h3>Main npm Dependencies (${data.mainPackages.length})</h3>
      <table>
        <thead>
          <tr>
            <th>Package</th>
            <th>Version</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody>
          ${data.mainPackages
				.slice(0, 20)
				.map(
					(pkg) => `
            <tr>
              <td>${pkg.name}</td>
              <td>${pkg.version}</td>
              <td>${pkg.type}</td>
            </tr>
          `,
				)
				.join("")}
          ${
				data.mainPackages.length > 20
					? `
            <tr>
              <td colspan="3"><i>...and ${data.mainPackages.length - 20} more</i></td>
            </tr>
          `
					: ""
			}
        </tbody>
      </table>
      
      <h3>Python Dependencies (${data.pythonPackages.length})</h3>
      <table>
        <thead>
          <tr>
            <th>Package</th>
            <th>Version</th>
          </tr>
        </thead>
        <tbody>
          ${data.pythonPackages
				.map(
					(pkg) => `
            <tr>
              <td>${pkg.name}</td>
              <td>${pkg.version || "<i>not pinned</i>"}</td>
            </tr>
          `,
				)
				.join("")}
        </tbody>
      </table>
    </div>
    
    <footer>
      Generated by Plutonium - Apex CodeGenesis Development Toolkit
    </footer>
  </div>
</body>
</html>`

	// Write HTML report to file
	const reportPath = path.join(REPORTS_DIR, "dependency-report.html")
	fs.writeFileSync(reportPath, htmlContent)

	return reportPath
}

/**
 * Analyze dependencies across JavaScript and Python
 */
function checkDependencies(options, utils) {
	const { log, heading, colors } = utils

	heading("Analyzing dependencies")
	log("🔍 Dependency Analyzer (Plutonium Development Preview)")
	log(`Running on Node.js ${process.version} | ${process.platform}-${process.arch} | ${new Date().toISOString()}`)

	// Variables to hold dependency data
	let mainPkg = {};
	let webviewPkg = {};
	let mainPackages = [];
	let webviewPackages = [];
	let mainDeps = {};
	let webviewDeps = {};
	let sharedPackages = [];
	let npmInconsistencies = [];
	let pythonPackages = [];
	let unpinnedPythonDeps = [];
	let crossLanguageIssues = [];
	let analysisMode = "full";
	
	if (options.language === "python") {
		// Python-only mode
		analysisMode = "python-only";
		log("Running in Python-only mode - focusing on Python dependencies", "info");
	} else {
		// Check for JS dependencies
		if (fs.existsSync(MAIN_PACKAGE_JSON)) {
			// Read package.json files
			mainPkg = JSON.parse(fs.readFileSync(MAIN_PACKAGE_JSON, "utf8"))
			
			if (fs.existsSync(WEBVIEW_PACKAGE_JSON)) {
				webviewPkg = JSON.parse(fs.readFileSync(WEBVIEW_PACKAGE_JSON, "utf8"))
			} else {
				log("Webview package.json not found, skipping webview dependency analysis.", "warning")
			}
			
			// Extract npm dependencies
			mainDeps = {
				...(mainPkg.dependencies || {}),
				...(mainPkg.devDependencies || {}),
			}
			
			mainPackages = Object.entries(mainDeps).map(([name, version]) => ({
				name,
				version,
				type: mainPkg.dependencies && name in mainPkg.dependencies ? "dependency" : "devDependency",
			}))
			
			// Process webview dependencies only if webviewPkg was loaded
			webviewDeps = webviewPkg.dependencies || webviewPkg.devDependencies ? {
				...(webviewPkg.dependencies || {}),
				...(webviewPkg.devDependencies || {}),
			} : {}
			
			if (Object.keys(webviewDeps).length > 0) {
				webviewPackages = Object.entries(webviewDeps).map(([name, version]) => ({
					name,
					version,
					type: webviewPkg.dependencies && name in webviewPkg.dependencies ? "dependency" : "devDependency",
				}))
			}
			
			// Find shared dependencies
			sharedPackages = Object.keys(mainDeps).filter((dep) => dep in webviewDeps)
			
			// Check for version inconsistencies
			sharedPackages.forEach((pkg) => {
				const mainVersion = mainDeps[pkg]
				const webviewVersion = webviewDeps[pkg]
				
				if (mainVersion !== webviewVersion) {
					const recommended = getHigherVersion(mainVersion, webviewVersion)
					npmInconsistencies.push({
						name: pkg,
						mainVersion,
						webviewVersion,
						recommended,
					})
				}
			})
		} else if (options.language !== "python") {
			log("No package.json found in the project root.", "warning")
			analysisMode = "python-only";
		}
	}

	log("\nAnalyzing dependencies...")

	// Get Python dependencies - look for requirements files
	let requirementsFiles = [PYTHON_REQUIREMENTS]; // Default
	if (fs.existsSync(PYTHON_REQUIREMENTS)) {
		log(`Found root requirements.txt`, "info");
	} else {
		// Search for requirements files throughout the project
		requirementsFiles = findRequirementsFiles(ROOT_DIR);
		if (requirementsFiles.length > 0) {
			log(`Found ${requirementsFiles.length} Python requirements files in the project:`, "info");
			requirementsFiles.forEach(file => {
				log(`  - ${path.relative(ROOT_DIR, file)}`, "info");
			});
		} else {
			log("No Python requirements files found.", "warning");
		}
	}
	
	// Process all requirements files
	let totalPythonPackages = 0;
	let totalUnpinnedDeps = 0;
	
	requirementsFiles.forEach(reqFile => {
		if (fs.existsSync(reqFile)) {
			const reqData = parsePythonRequirements(reqFile);
			pythonPackages = pythonPackages.concat(reqData.packages);
			unpinnedPythonDeps = unpinnedPythonDeps.concat(reqData.unpinned);
			
			if (reqData.packages.length > 0) {
				log(`Parsed ${reqData.packages.length} packages from ${path.relative(ROOT_DIR, reqFile)}`, "info");
				totalPythonPackages += reqData.packages.length;
				totalUnpinnedDeps += reqData.unpinned.length;
			}
		}
	});

	// Check for cross-language conflicts
	if (analysisMode === "full" && pythonPackages.length > 0 && Object.keys(mainDeps).length > 0) {
		// Common packages that exist in both ecosystems
		const crossLanguageMapping = {
			openai: "openai",
			anthropic: "@anthropic-ai/sdk",
			"google-genai": "@google/generative-ai",
			"azure-openai": "@azure/openai",
			tiktoken: "tiktoken",
		}
		
		pythonPackages.forEach(pkg => {
			if (crossLanguageMapping[pkg.name] && mainDeps[crossLanguageMapping[pkg.name]]) {
				crossLanguageIssues.push({
					name: pkg.name,
					pythonVersion: `${pkg.name}@${pkg.version || "unpinned"}`,
					jsVersion: `${crossLanguageMapping[pkg.name]}@${mainDeps[crossLanguageMapping[pkg.name]]}`,
				})
			}
		});
	}

	// Print summary
	log(`Found ${pythonPackages.length} Python packages`, "info")
	
	if (analysisMode === "full") {
		log(`Found ${mainPackages.length} main npm packages`, "info")
		log(`Found ${webviewPackages.length} webview npm packages`, "info")
		
		heading("Checking npm dependency consistency")
		log(`Found ${sharedPackages.length} shared npm packages between main and webview`)
		
		if (npmInconsistencies.length > 0) {
			log("\n⚠️ Version inconsistencies found between npm environments:", "warning")
			npmInconsistencies.forEach((item) => {
				log(`  - ${item.name}: main(${item.mainVersion}) vs webview(${item.webviewVersion})`, "warning")
			})
		} else if (sharedPackages.length > 0) {
			log("✅ All shared npm packages have consistent versions", "success")
		}
		
		heading("Checking cross-language dependencies")
		
		if (crossLanguageIssues.length > 0) {
			log("\n⚠️ Potential cross-language dependency conflicts:", "warning")
			crossLanguageIssues.forEach((item) => {
				log(`  - Python: ${item.pythonVersion} / npm(main): ${item.jsVersion}`, "warning")
			})
			log("\n   ⓘ Review these packages to ensure version compatibility between languages")
		} else {
			log("✅ No cross-language dependency conflicts found", "success")
		}
	}

	heading("Checking for unpinned Python dependencies")

	if (unpinnedPythonDeps.length > 0) {
		log("\n⚠️ Found unpinned Python dependencies:", "warning")
		unpinnedPythonDeps.forEach((dep) => log(`  - ${dep}`, "warning"))
	} else if (pythonPackages.length > 0) {
		log("✅ All Python dependencies are properly pinned!", "success")
	}
	
	// Find testing-related dependencies
	const testDeps = pythonPackages.filter(pkg => 
		pkg.name.includes('test') || 
		pkg.name.includes('pytest') || 
		pkg.name === 'coverage' ||
		pkg.name === 'nose' ||
		pkg.name === 'mock' ||
		pkg.name === 'hypothesis' ||
		pkg.name === 'tox' ||
		pkg.name === 'unittest2'
	);
	
	if (testDeps.length > 0) {
		heading("Testing-related dependencies");
		log(`Found ${testDeps.length} testing-related Python packages:`, "info");
		testDeps.forEach(pkg => {
			log(`  - ${pkg.name}${pkg.version ? ' (' + pkg.version + ')' : ''}`, "info");
		});
	} else if (pythonPackages.length > 0) {
		heading("Testing-related dependencies");
		log("⚠️ No testing-related Python packages found. Consider adding pytest or similar testing libraries.", "warning");
	}

	// Build report data
	const reportData = {
		pythonPackages,
		mainPackages,
		webviewPackages,
		sharedPackages: sharedPackages.map((name) => ({ name })),
		npmInconsistencies,
		crossLanguageIssues,
		unpinnedPythonDeps,
		testingDependencies: testDeps
	}

	// Generate HTML report
	const reportPath = generateHtmlReport(reportData)
	log(`\nReport generated: ${reportPath}`)

	// Print analysis summary
	heading("Analysis Summary")
	
	if (analysisMode === "full") {
		log(`${npmInconsistencies.length} npm version inconsistencies`)
		log(`${crossLanguageIssues.length} potential cross-language issues`)
	}
	
	log(`${unpinnedPythonDeps.length} unpinned Python dependencies`)
	log(`${testDeps.length} testing-related dependencies`)
	
	log(`\nTo view the full report: xdg-open ${reportPath}`)

	return {
		reportPath,
		summary: {
			npmInconsistencies: npmInconsistencies.length,
			crossLanguageIssues: crossLanguageIssues.length,
			unpinnedPythonDeps: unpinnedPythonDeps.length,
			testingDependencies: testDeps.length
		},
	}
}

// Export module functions
module.exports = {
	checkDependencies,
	parseVersion,
	getHigherVersion,
	findRequirementsFiles,
	parsePythonRequirements
}
