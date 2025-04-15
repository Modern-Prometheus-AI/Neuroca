/**
 * Component handling the logic for the 'analyze-all' command.
 * Orchestrates various analysis steps like dependency checks, structure analysis,
 * testing, coverage reporting, and unified report generation.
 */
const path = require('path');
const fs = require('fs');
const { runSyncCommand } = require('./commandRunner');
const { generateUnifiedHtmlReport, aggregateReportData } = require('./reportGenerator');

/**
 * Determines the correct python command ('python' or 'python3').
 * Exits if neither is found.
 * @returns {string} The python command to use.
 */
function getPythonCommand() {
    const commandsToTry = ['python', 'python3'];
    for (const cmd of commandsToTry) {
        // Use spawnSync to check if the command exists and runs
        const result = runSyncCommand(cmd, ['--version'], { stdio: 'ignore', encoding: 'utf8' });
        if (result.status === 0 || (result.stdout && result.stdout.includes('Python'))) {
             console.log(`✅ Using Python command: ${cmd}`);
            return cmd;
        }
    }

    // If loop completes without returning, neither command worked
    console.error("❌ Error: Could not find 'python' or 'python3' command.");
    console.error("Please ensure Python is installed and accessible in your system's PATH.");
    process.exit(1); // Exit if Python command cannot be determined
}

/**
 * Loads the Plutonium icon as base64 data URL for embedding in HTML.
 * @param {string} projectRoot - Absolute path to the project root.
 * @param {string} toolDirName - Name of the main tool directory (e.g., 'Neuroca').
 * @param {string} toolSubdirName - Name of the tool subdirectory (e.g., 'plutonium_tool').
 * @returns {string} Base64 encoded icon data URL, or empty string if not found/error.
 */
function loadIconBase64(projectRoot, toolDirName, toolSubdirName) {
    // Construct the expected path to the icon
    const iconPath = path.join(projectRoot, toolDirName, toolSubdirName, 'plutonium', 'assets', 'plutonium-icon.png');
    if (fs.existsSync(iconPath)) {
        try {
            const iconData = fs.readFileSync(iconPath);
            console.log('✅ Plutonium icon loaded for embedding');
            // Format as a data URL
            return `data:image/png;base64,${iconData.toString('base64')}`;
        } catch (err) {
            console.error('❌ Error reading Plutonium icon:', err.message);
        }
    } else {
        // Warn if the icon isn't found at the expected path
        console.warn(`⚠️ Plutonium icon not found at: ${iconPath}`);
    }
    return ''; // Return empty string if icon cannot be loaded
}

/**
 * Runs the full analysis suite ('analyze-all' command logic).
 * @param {string} projectRoot - Absolute path to the project root.
 * @param {string} toolDirName - Name of the main tool directory (e.g., 'Neuroca').
 * @param {string} toolSubdirName - Name of the tool subdirectory (e.g., 'plutonium_tool').
 * @param {string} plutoniumToolPath - Absolute path to the core plutonium.js script.
 */
function runAnalyzeAll(projectRoot, toolDirName, toolSubdirName, plutoniumToolPath) {
    console.log('🚀 Running comprehensive project analysis...');

    // --- Setup ---
    const reportsDir = path.join(projectRoot, toolDirName, 'reports');
    const coverageDir = path.join(reportsDir, 'coverage');
    const pythonCmd = getPythonCommand(); // Determine python command early

    // Create report/coverage directories if they don't exist
    try {
        fs.mkdirSync(coverageDir, { recursive: true }); // Ensures reportsDir is also created
        console.log(`✅ Ensured report directories exist: ${reportsDir}`);
    } catch (e) {
         console.error(`❌ Failed to create report directories: ${e.message}`);
         process.exit(1); // Cannot proceed without report directories
    }


    // Load icon for the report
    const plutoniumIconBase64 = loadIconBase64(projectRoot, toolDirName, toolSubdirName);

    // --- Analysis Steps ---
    let stepFailed = false; // Track if any step fails
    const results = {}; // Store results/status of each step

    // Step 1: Dependency Check (using the core plutonium tool)
    console.log('\n📦 Step 1: Analyzing dependencies...');
    results.deps = runSyncCommand('node', [plutoniumToolPath, 'deps:check', '--language=python'], { cwd: process.cwd() });
    if (results.deps.status !== 0) {
        console.error('❌ Dependency analysis step failed.');
        stepFailed = true;
        // Decide whether to exit early or continue
        // process.exit(results.deps.status || 1); // Option to exit early
    }

    // Step 2: Structure Analysis (using the core plutonium tool)
    console.log('\n🏗️ Step 2: Analyzing project structure...');
    results.struct = runSyncCommand('node', [plutoniumToolPath, 'struct:analyze'], { cwd: process.cwd() });
    if (results.struct.status !== 0) {
        console.error('❌ Structure analysis step failed (continuing analysis).');
        stepFailed = true; // Mark failure but continue
    }

    // Step 3: Tests & Coverage (using python pytest/coverage)
    console.log('\n🧪 Step 3: Running tests with coverage...');
    // Run pytest with coverage collection enabled. Run from project root.
    results.coverageRun = runSyncCommand(pythonCmd, ['-m', 'pytest', '--cov'], { cwd: projectRoot });

    // Only generate reports if the tests ran successfully (status 0)
    if (results.coverageRun.status === 0) {
        console.log('✅ Tests completed successfully. Generating coverage reports...');
        // Generate JSON report
        results.coverageJson = runSyncCommand(pythonCmd, ['-m', 'coverage', 'json', '-o', path.join(toolDirName, 'reports', 'coverage', 'coverage.json')], { cwd: projectRoot });
        if (results.coverageJson.status !== 0) {
             console.warn('⚠️ Failed to generate coverage JSON report.');
             stepFailed = true;
        }
        // Generate HTML report
        results.coverageHtml = runSyncCommand(pythonCmd, ['-m', 'coverage', 'html', '-d', path.join(toolDirName, 'reports', 'coverage', 'html')], { cwd: projectRoot });
         if (results.coverageHtml.status !== 0) {
             console.warn('⚠️ Failed to generate coverage HTML report.');
             stepFailed = true;
         }
    } else {
        console.error('❌ Test execution or coverage collection failed.');
        stepFailed = true;
        // Optional: Add a fallback simple test run here if needed
    }

    // Step 4: Installed Packages Check (using python)
    console.log('\n📋 Step 4: Checking installed package versions...');
    // Use importlib.metadata if available (Python 3.8+), fallback to pkg_resources
    const checkCmd = `
import sys, json
try:
    from importlib import metadata
    print(json.dumps({dist.metadata['Name']: dist.version for dist in metadata.distributions()}))
except ImportError:
    try:
        req = "pkg_resources"
        __import__(req)
        print(json.dumps({d.key: d.version for d in sys.modules[req].working_set}))
    except ImportError:
        print(json.dumps({})) # Return empty if neither works
`;
    results.pkgCheck = runSyncCommand(pythonCmd, ['-c', checkCmd], {
        cwd: projectRoot,
        stdio: 'pipe' // Capture stdout
    });
    // Note: aggregation logic will handle parsing this output

    // Step 5: Dependency Conflict Check (using pip)
    console.log('\n🔍 Step 5: Checking for dependency conflicts...');
    results.conflictCheck = runSyncCommand(pythonCmd, ['-m', 'pip', 'check'], {
        cwd: projectRoot,
        stdio: 'pipe' // Capture stdout/stderr
    });
     // Note: aggregation logic will handle parsing this output

    // Step 6: Aggregate Data and Generate Unified Report
    console.log('\n📊 Step 6: Generating unified analysis report...');
    const analysisData = aggregateReportData(projectRoot, toolDirName, reportsDir, results);
    const htmlReport = generateUnifiedHtmlReport(analysisData, plutoniumIconBase64);
    const htmlReportPath = path.join(reportsDir, 'unified_analysis.html');

    try {
        fs.writeFileSync(htmlReportPath, htmlReport);
        console.log(`\n✅ Analysis complete! Unified report generated at: ${path.relative(process.cwd(), htmlReportPath)}`);

        // Log key findings summary from aggregated data
        console.log('\n--- Analysis Summary ---');
        console.log(`- Python Packages Found: ${analysisData.dependency_analysis.total_packages}`);
        console.log(`- Unpinned Packages:     ${analysisData.dependency_analysis.unpinned_packages}`);
        console.log(`- Dependency Conflicts:  ${analysisData.dependency_analysis.conflicts.length}`);
        console.log(`- Test Coverage:         ${analysisData.testing_analysis.coverage.coverage_percent.toFixed(2)}% (${analysisData.testing_analysis.coverage.covered}/${analysisData.testing_analysis.coverage.total} lines)`);
        console.log(`- Test Files Found:      ${analysisData.testing_analysis.test_files.length}`);
        console.log('------------------------');

    } catch (e) {
        console.error(`❌ Failed to write unified HTML report: ${e.message}`);
        stepFailed = true;
    }

    // Exit with non-zero code if any critical step failed
    console.log(`\nAnalysis finished ${stepFailed ? 'with errors' : 'successfully'}.`);
    process.exit(stepFailed ? 1 : 0);
}

// Export the main function for this component
module.exports = {
    runAnalyzeAll
};
