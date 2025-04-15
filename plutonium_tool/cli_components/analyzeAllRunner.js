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
 * @param {string} reportsDir - Path to the reports directory
 * @returns {string} Base64 encoded icon data URL, or empty string if not found/error.
 */
function loadIconBase64(reportsDir) {
    // First try to find the icon in the reports directory
    const iconPath = path.join(reportsDir, 'plutonium-icon.png');
    
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
    // Use path.join for proper cross-platform path resolution
    const toolDir = path.join(projectRoot, toolDirName);
    const reportsDir = path.join(toolDir, 'reports');
    const coverageDir = path.join(reportsDir, 'coverage');
    const pythonCmd = getPythonCommand(); // Determine python command early

    // Create report/coverage directories if they don't exist
    try {
        fs.mkdirSync(coverageDir, { recursive: true }); // Ensures reportsDir is also created
        console.log(`✅ Created report directories at: ${reportsDir}`);
    } catch (e) {
        if (e.code !== 'EEXIST') {
            console.error(`❌ Failed to create report directories: ${e.message}`);
            process.exit(1); // Cannot proceed without report directories
        }
    }

    // Load icon for the report from the reports directory
    const plutoniumIconBase64 = loadIconBase64(reportsDir);

    // --- Analysis Steps ---
    let stepFailed = false; // Track if any step fails
    const results = {}; // Store results/status of each step

    // Step 1: Dependency Check (using the core plutonium tool)
    console.log('\n📦 Step 1: Analyzing dependencies...');
    results.deps = runSyncCommand('node', [plutoniumToolPath, 'deps:check', '--language=python'], { 
        cwd: projectRoot 
    });
    
    if (results.deps.status !== 0) {
        console.error('❌ Dependency analysis step failed.');
        stepFailed = true;
    }

    // Step 2: Structure Analysis (using the core plutonium tool)
    console.log('\n🏗️ Step 2: Analyzing project structure...');
    results.struct = runSyncCommand('node', [plutoniumToolPath, 'struct:analyze'], { 
        cwd: projectRoot 
    });
    
    if (results.struct.status !== 0) {
        console.error('❌ Structure analysis step failed (continuing analysis).');
        stepFailed = true; // Mark failure but continue
    }

    // Step 3: Tests & Coverage (using python pytest/coverage)
    console.log('\n🧪 Step 3: Running tests with coverage...');
    
    // Check if pytest-cov is installed
    console.log('Checking for required test packages...');
    const checkPytestCov = runSyncCommand(pythonCmd, [
        '-c', 
        'try:\n    import pytest_cov\n    print("INSTALLED")\nexcept ImportError:\n    print("NOT_INSTALLED")'
    ], {
        cwd: projectRoot,
        stdio: 'pipe'
    });
    
    // Install pytest-cov if not available
    if (!checkPytestCov.stdout || !checkPytestCov.stdout.includes("INSTALLED")) {
        console.log('📦 Installing pytest-cov package (required for coverage reporting)...');
        
        // First try with --user flag to avoid permission errors
        const installResult = runSyncCommand(pythonCmd, [
            '-m', 'pip', 'install', '--user', 'pytest-cov'
        ], {
            cwd: projectRoot,
            stdio: 'inherit' // Show output to user
        });
        
        if (installResult.status !== 0) {
            console.error('❌ Failed to install pytest-cov. Will try running tests without coverage.');
            results.testRun = runSyncCommand(pythonCmd, ['-m', 'pytest'], { 
                cwd: projectRoot,
                stdio: 'inherit'
            });
            stepFailed = true;
        } else {
            console.log('✅ Successfully installed pytest-cov.');
            // Verify the installation
            const verifyInstall = runSyncCommand(pythonCmd, [
                '-c', 'import pytest_cov; print("pytest-cov verified")'
            ], { 
                cwd: projectRoot,
                stdio: 'inherit'
            });
            
            if (verifyInstall.status !== 0) {
                console.error('❌ pytest-cov installed but still not working. Running tests without coverage.');
                results.testRun = runSyncCommand(pythonCmd, ['-m', 'pytest'], { 
                    cwd: projectRoot,
                    stdio: 'inherit'
                });
                stepFailed = true;
            }
        }
    } else {
        console.log('✅ pytest-cov is already installed.');
    }
    
    // Try to determine the correct module name for coverage by examining the project structure
    let moduleToTest = '';
    if (fs.existsSync(path.join(projectRoot, 'src', 'neuroca'))) {
        moduleToTest = 'src.neuroca';
    } else if (fs.existsSync(path.join(projectRoot, 'neuroca'))) {
        moduleToTest = 'neuroca';
    } else {
        // Just run coverage without module specifier - let pytest figure it out
        moduleToTest = '';
    }
    
    // Run pytest with coverage collection enabled
    console.log(`Running tests with coverage${moduleToTest ? ` for module: ${moduleToTest}` : ''}`);
    
    if (moduleToTest) {
        results.coverageRun = runSyncCommand(pythonCmd, ['-m', 'pytest', `--cov=${moduleToTest}`], { 
            cwd: projectRoot,
            stdio: 'inherit'
        });
    } else {
        // Try without module specifier first
        results.coverageRun = runSyncCommand(pythonCmd, ['-m', 'pytest', '--cov'], { 
            cwd: projectRoot,
            stdio: 'inherit'
        });
    }
    
    // If that fails, try other approaches
    if (results.coverageRun.status !== 0) {
        console.log('⚠️ Coverage test failed, trying with minimal options...');
        results.testRun = runSyncCommand(pythonCmd, ['-m', 'pytest'], {
            cwd: projectRoot,
            stdio: 'inherit'
        });
        if (results.testRun.status === 0) {
            console.log('✅ Tests passed without coverage enabled.');
        } else {
            console.error('❌ Tests failed to run.');
            stepFailed = true;
        }
    } else {
        // Tests ran successfully with coverage, generate reports
        console.log('✅ Tests completed successfully with coverage. Generating coverage reports...');
        
        try {
            // Ensure coverage directories exist
            fs.mkdirSync(path.join(coverageDir, 'html'), { recursive: true });
            
            // Generate JSON report
            results.coverageJson = runSyncCommand(pythonCmd, [
                '-m', 'coverage', 'json', 
                '-o', path.join(coverageDir, 'coverage.json')
            ], { cwd: projectRoot });
            
            if (results.coverageJson.status !== 0) {
                console.warn('⚠️ Failed to generate coverage JSON report.');
            } else {
                console.log(`✅ Generated coverage JSON report`);
            }
            
            // Generate HTML report
            results.coverageHtml = runSyncCommand(pythonCmd, [
                '-m', 'coverage', 'html', 
                '-d', path.join(coverageDir, 'html')
            ], { cwd: projectRoot });
            
            if (results.coverageHtml.status !== 0) {
                console.warn('⚠️ Failed to generate coverage HTML report.');
            } else {
                console.log(`✅ Generated coverage HTML report`);
            }
        } catch (e) {
            console.error(`❌ Error during coverage report generation: ${e.message}`);
            stepFailed = true;
        }
    }

    // Step 4: Installed Packages Check (multiple languages)
    console.log('\n📋 Step 4: Checking installed package versions...');
    
    // Python package detection - more robust approach
    console.log('Checking Python packages...');
    results.pythonPkgCheck = runSyncCommand(pythonCmd, [
        '-c', 
        'import sys, json, subprocess\ntry:\n    from importlib import metadata\n    pkgs = {dist.metadata["Name"].lower(): dist.version for dist in metadata.distributions()}\n    print(json.dumps(pkgs))\nexcept ImportError:\n    try:\n        import pkg_resources\n        pkgs = {d.key.lower(): d.version for d in pkg_resources.working_set}\n        print(json.dumps(pkgs))\n    except ImportError:\n        try:\n            pip_freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)\n            pkgs = {}\n            for line in pip_freeze.splitlines():\n                if "==" in line:\n                    name, version = line.split("==", 1)\n                    pkgs[name.lower()] = version\n            print(json.dumps(pkgs))\n        except:\n            print(json.dumps({}))'
    ], {
        cwd: projectRoot,
        stdio: 'pipe' // Capture stdout
    });

    // Node.js package detection
    console.log('Checking Node.js packages...');
    // First check if package.json exists in the project root or tool directories
    const possiblePackageJsonPaths = [
        path.join(projectRoot, 'package.json'),
        path.join(toolDir, 'package.json'),
        path.join(projectRoot, toolDirName, toolSubdirName, 'package.json')
    ];
    
    let jsPackages = {};
    for (const packageJsonPath of possiblePackageJsonPaths) {
        if (fs.existsSync(packageJsonPath)) {
            try {
                console.log(`Found package.json at ${packageJsonPath}`);
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                
                // Combine dependencies, devDependencies and peerDependencies
                const allDeps = {
                    ...(packageJson.dependencies || {}),
                    ...(packageJson.devDependencies || {}),
                    ...(packageJson.peerDependencies || {})
                };
                
                // Merge with any previously found packages
                jsPackages = { ...jsPackages, ...allDeps };
            } catch (e) {
                console.warn(`Failed to parse package.json at ${packageJsonPath}: ${e.message}`);
            }
        }
    }
    
    // Check installed npm packages if npm command available
    try {
        const npmListResult = runSyncCommand('npm', ['list', '--json', '--depth=0'], {
            cwd: projectRoot,
            stdio: 'pipe'
        });
        
        if (npmListResult.status === 0 && npmListResult.stdout) {
            try {
                const npmList = JSON.parse(npmListResult.stdout);
                if (npmList.dependencies) {
                    // Extract actual installed versions from npm list
                    const installedVersions = {};
                    Object.entries(npmList.dependencies).forEach(([name, info]) => {
                        installedVersions[name] = info.version || info;
                    });
                    
                    // Update existing dependencies with actual installed versions
                    jsPackages = { ...jsPackages, ...installedVersions };
                }
            } catch (e) {
                console.warn(`Failed to parse npm list output: ${e.message}`);
            }
        }
    } catch (e) {
        console.warn(`Failed to run npm list: ${e.message}`);
    }
    
    // Store JS packages result
    results.jsPackages = { stdout: JSON.stringify(jsPackages), status: 0 };

    // Step 5: Dependency Conflict Check (using pip)
    console.log('\n🔍 Step 5: Checking for dependency conflicts...');
    results.pythonConflictCheck = runSyncCommand(pythonCmd, ['-m', 'pip', 'check'], {
        cwd: projectRoot,
        stdio: 'pipe' // Capture stdout/stderr
    });
    
    // Check for npm dependency conflicts
    console.log('Checking for npm package conflicts...');
    let jsConflicts = [];
    try {
        const npmCheck = runSyncCommand('npm', ['audit'], {
            cwd: projectRoot,
            stdio: 'pipe'
        });
        
        if (npmCheck.status !== 0 || (npmCheck.stderr && npmCheck.stderr.includes('vulnerabilities'))) {
            // Parse npm audit output for conflicts and vulnerabilities
            const output = npmCheck.stdout || '';
            const lines = output.split('\n');
            
            // Extract vulnerability lines
            jsConflicts = lines.filter(line => 
                line.includes('vulnerability') || 
                line.includes('vulnerabilities') ||
                line.includes('require') && line.includes('not compatible')
            ).map(line => line.trim());
        }
        
        // Also check for peer dependency issues
        const npmLs = runSyncCommand('npm', ['ls'], {
            cwd: projectRoot,
            stdio: 'pipe'
        });
        
        if (npmLs.stderr) {
            // Extract peer dependency issues
            const peerIssues = npmLs.stderr.split('\n')
                .filter(line => line.includes('peer dep missing:') || line.includes('UNMET PEER DEPENDENCY'))
                .map(line => line.trim());
            
            jsConflicts = [...jsConflicts, ...peerIssues];
        }
    } catch (e) {
        console.warn(`Failed to check npm conflicts: ${e.message}`);
    }
    
    // Store JS conflicts result
    results.jsConflictCheck = { 
        stdout: jsConflicts.join('\n'),
        stderr: '',
        status: jsConflicts.length > 0 ? 1 : 0
    };

    // Step 6: Aggregate Data and Generate Unified Report
    console.log('\n📊 Step 6: Generating unified analysis report...');
    const analysisData = aggregateReportData(projectRoot, toolDirName, reportsDir, results);
    const htmlReport = generateUnifiedHtmlReport(analysisData, plutoniumIconBase64);
    const htmlReportPath = path.join(reportsDir, 'unified_analysis.html');

    try {
        fs.writeFileSync(htmlReportPath, htmlReport);
        const relativeReportPath = path.relative(process.cwd(), htmlReportPath);
        console.log(`\n✅ Analysis complete! Unified report generated at: ${relativeReportPath}`);

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
    return stepFailed ? 1 : 0;
}

// Export the main function for this component
module.exports = {
    runAnalyzeAll
};
