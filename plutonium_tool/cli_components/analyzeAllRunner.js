/**
 * Component handling the logic for the 'analyze-all' command.
 * Orchestrates various analysis steps like dependency checks, structure analysis,
 * testing, coverage reporting, and unified report generation.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { generateUnifiedHtmlReport, aggregateReportData } = require('./reportGenerator');

// Read the Plutonium icon as base64 for embedding in the report
const plutoniumIconBase64 = fs.existsSync(path.join(__dirname, '../reports/plutonium-icon.png')) ? 
    `data:image/png;base64,${fs.readFileSync(path.join(__dirname, '../reports/plutonium-icon.png')).toString('base64')}` : '';

/**
 * Helper function to determine if a command is available
 * @param {string} command - Command to check
 * @returns {boolean} True if command exists
 */
function commandExists(command) {
    try {
        const isWin = process.platform === 'win32';
        if (isWin) {
            execSync(`where ${command}`);
        } else {
            execSync(`which ${command}`);
        }
        return true;
    } catch (e) {
        return false;
    }
}

/**
 * Run a command synchronously and return the result
 * @param {string} command - Main command
 * @param {Array} args - Command arguments
 * @param {Object} options - Execution options
 * @returns {Object} Result object with status, stdout, stderr
 */
function runSyncCommand(command, args, options = {}) {
    try {
        const stdout = execSync(`${command} ${args.join(' ')}`, options);
        return {
            status: 0,
            stdout: stdout ? stdout.toString() : '',
            stderr: ''
        };
    } catch (e) {
        return {
            status: e.status || 1,
            stdout: e.stdout ? e.stdout.toString() : '',
            stderr: e.stderr ? e.stderr.toString() : e.message
        };
    }
}

/**
 * Runs the comprehensive project analysis and generates a unified HTML report
 * @param {string} projectRoot - Path to the project root
 * @param {string} toolDirName - The name of the tool directory (e.g., 'Neuroca')
 * @param {string} toolSubdirName - The name of the tool subdirectory (e.g., 'plutonium_tool')
 * @param {string} plutoniumToolPath - Path to plutonium.js
 * @returns {number} Exit code (0 for success, non-zero for errors)
 */
function runAnalyzeAll(projectRoot, toolDirName, toolSubdirName, plutoniumToolPath) {
    console.log(`\n🔍 Running comprehensive project analysis...`);
    
    // Initialize result container
    const results = {};
    let stepFailed = false; // Track if any critical step fails
    
    // Define paths
    const reportsDir = path.join(projectRoot, toolDirName, 'reports');
    
    // Ensure reports directory exists
    try {
        if (!fs.existsSync(reportsDir)) {
            fs.mkdirSync(reportsDir, { recursive: true });
            console.log(`Created reports directory: ${reportsDir}`);
        }
    } catch (e) {
        console.error(`❌ Failed to create reports directory: ${e.message}`);
        return 1;
    }
    
    // Detect Python command (python or python3)
    let pythonCmd = 'python';
    if (!commandExists('python')) {
        if (commandExists('python3')) {
            pythonCmd = 'python3';
            console.log('Using python3 command');
        } else {
            console.warn('⚠️ Python not found in PATH. Some tests may be skipped.');
        }
    }

    // Detect Node.js
    const hasNode = commandExists('node');
    if (!hasNode) {
        console.warn('⚠️ Node.js not found in PATH. JavaScript dependency analysis will be limited.');
    }

    // Detect pip
    const hasPip = commandExists(`${pythonCmd} -m pip`);
    if (!hasPip) {
        console.warn('⚠️ pip not found. Python dependency analysis will be limited.');
    }
    
    // Step 1: Analyze project structure
    console.log('\n📁 Step 1: Analyzing project structure...');
    // Simple file count by extension
    try {
        const fileStats = {};
        function countFiles(dir, stats = {}) {
            try {
                if (!fs.existsSync(dir)) return stats;
                
                const entries = fs.readdirSync(dir, { withFileTypes: true });
                for (const entry of entries) {
                    if (entry.name === 'node_modules' || entry.name === '__pycache__' || 
                        entry.name === 'venv' || entry.name === '.git' || 
                        entry.name === '.pytest_cache') continue;
                    
                    const fullPath = path.join(dir, entry.name);
                    if (entry.isDirectory()) {
                        countFiles(fullPath, stats);
                    } else if (entry.isFile()) {
                        const ext = path.extname(entry.name).toLowerCase();
                        if (!stats[ext]) stats[ext] = 0;
                        stats[ext]++;
                    }
                }
                return stats;
            } catch (e) {
                console.error(`Error reading directory ${dir}: ${e.message}`);
                return stats;
            }
        }
        
        results.fileStats = countFiles(projectRoot, {});
        console.log(`Found file types: ${Object.keys(results.fileStats).join(', ')}`);
    } catch (e) {
        console.error(`❌ Error analyzing project structure: ${e.message}`);
        results.fileStats = {};
    }

    // Step 2: Find JavaScript/Node.js Dependencies
    console.log('\n📦 Step 2: Checking JavaScript dependencies...');
    results.nodeDependencies = { packages: {}, devPackages: {} };
    try {
        // Check for package.json files
        const packageJsonFiles = findFilesRecursive(projectRoot, 'package.json', ['node_modules', '.git']);
        console.log(`Found ${packageJsonFiles.length} package.json files`);
        
        if (packageJsonFiles.length > 0) {
            // Parse package.json files to extract dependencies
            for (const pkgFile of packageJsonFiles) {
                try {
                    const pkgJson = JSON.parse(fs.readFileSync(pkgFile, 'utf8'));
                    const pkgDir = path.dirname(pkgFile);
                    const relativePath = path.relative(projectRoot, pkgDir);
                    
                    // Add to dependencies
                    if (pkgJson.dependencies) {
                        results.nodeDependencies.packages[relativePath] = pkgJson.dependencies;
                    }
                    
                    // Add to devDependencies
                    if (pkgJson.devDependencies) {
                        results.nodeDependencies.devPackages[relativePath] = pkgJson.devDependencies;
                    }
                    
                    console.log(`✓ Processed ${relativePath}/package.json`);
                } catch (e) {
                    console.error(`❌ Error processing ${pkgFile}: ${e.message}`);
                }
            }
        } else {
            console.log('No package.json files found. Skipping JavaScript dependency analysis.');
        }
    } catch (e) {
        console.error(`❌ Error analyzing Node.js dependencies: ${e.message}`);
    }
    
    // Step 3: Run pytest (auto-install pytest-cov if missing)
    console.log('\n🧪 Step 3: Running unit tests with coverage...');
    const coverageDir = path.join(reportsDir, 'coverage');
    try {
        if (!fs.existsSync(coverageDir)) {
            fs.mkdirSync(coverageDir, { recursive: true });
        }
    } catch (e) {
        console.error(`❌ Failed to create coverage directory: ${e.message}`);
    }
    
    // Try to import pytest-cov to see if it's installed
    const checkCovResult = runSyncCommand(pythonCmd, [
        '-c', 'try: import pytest_cov; print("installed"); except ImportError: print("missing")'
    ], {
        cwd: projectRoot,
        stdio: 'pipe'
    });
    
    // If pytest-cov is missing, try to install it
    if (checkCovResult.stdout.trim() === 'missing') {
        console.log('pytest-cov not found. Attempting to install...');
        const installResult = runSyncCommand(pythonCmd, ['-m', 'pip', 'install', 'pytest-cov', '--user'], {
            cwd: projectRoot,
            stdio: 'pipe'
        });
        
        if (installResult.status !== 0) {
            console.warn(`⚠️ Failed to install pytest-cov: ${installResult.stderr}`);
            console.warn('Will run tests without coverage reporting.');
            
            // Run tests without coverage
            results.pytestResult = runSyncCommand(pythonCmd, ['-m', 'pytest'], {
                cwd: projectRoot,
                stdio: 'pipe'
            });
        } else {
            console.log('Successfully installed pytest-cov.');
        }
    }
    
    // Run tests with coverage
    const testdataDir = path.join(projectRoot, toolDirName); // Directory containing tests to run
    const sourceDir = path.join(projectRoot, toolDirName, 'src'); // Source directory to measure coverage for
    
    // Check if source directory exists; if not, try to find a suitable one
    let effectiveSourceDir = sourceDir;
    if (!fs.existsSync(sourceDir)) {
        // Look for 'src' directory or fallback to main project directory
        const possibleSrcDirs = [
            path.join(projectRoot, 'src'),
            path.join(projectRoot, toolDirName, 'neuroca'),
            path.join(projectRoot, 'neuroca')
        ];
        
        for (const dir of possibleSrcDirs) {
            if (fs.existsSync(dir)) {
                effectiveSourceDir = dir;
                console.log(`Using ${effectiveSourceDir} as the source directory for coverage`);
                break;
            }
        }
    }
    
    // Check if tests directory exists
    const testsDir = path.join(projectRoot, toolDirName, 'tests');
    const hasTests = fs.existsSync(testsDir);
    
    if (hasTests) {
        if (checkCovResult.stdout.trim() === 'installed' || checkCovResult.status === 0) {
            // Run pytest with coverage if we have it
            results.pytestResult = runSyncCommand(pythonCmd, [
                '-m', 'pytest',
                testsDir,
                '--cov=' + effectiveSourceDir,
                '--cov-report=term',
                '--cov-report=json:' + path.join(coverageDir, 'coverage.json'),
                '--cov-report=html:' + path.join(coverageDir, 'html')
            ], {
                cwd: projectRoot,
                stdio: 'pipe'
            });
            
            if (results.pytestResult.status === 0) {
                console.log('✅ Tests completed successfully with coverage report generated.');
            } else {
                console.warn(`⚠️ Tests had failures or errors: ${results.pytestResult.stderr}`);
                stepFailed = true;
            }
        } else {
            // Run tests without coverage as fallback
            results.pytestResult = runSyncCommand(pythonCmd, ['-m', 'pytest', testsDir], {
                cwd: projectRoot,
                stdio: 'pipe'
            });
            
            if (results.pytestResult.status === 0) {
                console.log('✅ Tests completed successfully (without coverage).');
            } else {
                console.warn(`⚠️ Tests had failures or errors: ${results.pytestResult.stderr}`);
                stepFailed = true;
            }
        }
    } else {
        console.warn(`⚠️ No tests directory found at ${testsDir}. Skipping test run.`);
    }

    // Step 4: Python Package Check
    console.log('\n📋 Step 4: Checking installed Python package versions...');
    results.pythonPkgCheck = runSyncCommand(pythonCmd, [
        '-c', 
        'import sys, json\ntry:\n    from importlib import metadata\n    print(json.dumps({dist.metadata["Name"]: dist.version for dist in metadata.distributions()}))\nexcept ImportError:\n    try:\n        import pkg_resources\n        print(json.dumps({d.key: d.version for d in pkg_resources.working_set}))\n    except ImportError:\n        print(json.dumps({}))'
    ], {
        cwd: projectRoot,
        stdio: 'pipe'
    });

    // Step 5: Check Python requirements files
    console.log('\n📄 Step 5: Analyzing Python requirements files...');
    results.pythonRequirements = { files: [] };
    try {
        // Find all requirements files
        const requirementFiles = findFilesRecursive(
            projectRoot, 
            file => file === 'requirements.txt' || file.endsWith('-requirements.txt'),
            ['node_modules', '.git', 'venv']
        );
        
        console.log(`Found ${requirementFiles.length} requirements files`);
        
        // Parse each requirements file
        for (const reqFile of requirementFiles) {
            try {
                const content = fs.readFileSync(reqFile, 'utf8');
                const lines = content.split('\n')
                    .map(line => line.trim())
                    .filter(line => line && !line.startsWith('#'));
                
                const requirements = [];
                for (const line of lines) {
                    // Basic parsing of requirements line
                    let name = line;
                    let version = null;
                    
                    // Extract version constraints if present
                    if (line.includes('==')) {
                        [name, version] = line.split('==');
                    } else if (line.includes('>=')) {
                        [name, version] = line.split('>=');
                        version = '>=' + version;
                    } else if (line.includes('<=')) {
                        [name, version] = line.split('<=');
                        version = '<=' + version;
                    } else if (line.includes('>')) {
                        [name, version] = line.split('>');
                        version = '>' + version;
                    } else if (line.includes('<')) {
                        [name, version] = line.split('<');
                        version = '<' + version;
                    } else if (line.includes('~=')) {
                        [name, version] = line.split('~=');
                        version = '~=' + version;
                    }
                    
                    name = name.trim();
                    if (version) version = version.trim();
                    
                    requirements.push({ name, version });
                }
                
                results.pythonRequirements.files.push({
                    path: path.relative(projectRoot, reqFile),
                    requirements
                });
            } catch (e) {
                console.error(`❌ Error parsing ${reqFile}: ${e.message}`);
            }
        }
    } catch (e) {
        console.error(`❌ Error analyzing requirements files: ${e.message}`);
    }

    // Step 6: Check for pyproject.toml and poetry.lock
    console.log('\n📄 Step 6: Checking for Poetry/pyproject.toml configuration...');
    results.poetryConfig = null;
    try {
        const pyprojectPath = path.join(projectRoot, toolDirName, 'pyproject.toml');
        const poetryLockPath = path.join(projectRoot, toolDirName, 'poetry.lock');
        
        if (fs.existsSync(pyprojectPath)) {
            console.log(`Found pyproject.toml at ${path.relative(projectRoot, pyprojectPath)}`);
            results.poetryConfig = {
                path: path.relative(projectRoot, pyprojectPath),
                content: fs.readFileSync(pyprojectPath, 'utf8')
            };
        } else {
            console.log('No pyproject.toml found. Skipping Poetry dependency analysis.');
        }
        
        if (fs.existsSync(poetryLockPath)) {
            console.log(`Found poetry.lock at ${path.relative(projectRoot, poetryLockPath)}`);
            results.poetryLock = {
                path: path.relative(projectRoot, poetryLockPath),
                content: fs.readFileSync(poetryLockPath, 'utf8')
            };
        }
    } catch (e) {
        console.error(`❌ Error reading Poetry configuration: ${e.message}`);
    }

    // Step 7: Dependency Conflict Check (using pip)
    console.log('\n🔍 Step 7: Checking for Python dependency conflicts...');
    if (hasPip) {
        results.conflictCheck = runSyncCommand(pythonCmd, ['-m', 'pip', 'check'], {
            cwd: projectRoot,
            stdio: 'pipe'
        });
    } else {
        console.log('pip not found, skipping conflict check');
        results.conflictCheck = { status: -1, stdout: '', stderr: 'pip not available' };
    }

    // Step 8: Check for cross-language dependencies
    console.log('\n🧩 Step 8: Analyzing potential cross-language dependencies...');
    results.crossLanguage = { packages: [] };
    try {
        // Define common Python packages that have JS/Node.js equivalents
        const commonCrossDeps = [
            { py: 'requests', js: 'axios' },
            { py: 'numpy', js: 'numjs' },
            { py: 'pandas', js: 'danfojs' },
            { py: 'matplotlib', js: 'chart.js' },
            { py: 'flask', js: 'express' },
            { py: 'pytest', js: 'jest' },
            { py: 'scikit-learn', js: 'ml.js' },
            { py: 'tensorflow', js: 'tensorflow.js' },
            { py: 'torch', js: 'onnx.js' },
            { py: 'django', js: 'react' }, // Not direct equivalents but common pairings
            { py: 'celery', js: 'bull' },
            { py: 'redis', js: 'redis' },
            { py: 'sqlalchemy', js: 'sequelize' },
        ];
        
        // Check Python packages against Node packages to find potential cross-language equivalents
        const pythonPackages = [];
        if (results.pythonPkgCheck.status === 0 && results.pythonPkgCheck.stdout) {
            try {
                const packages = JSON.parse(results.pythonPkgCheck.stdout);
                for (const [name, version] of Object.entries(packages)) {
                    pythonPackages.push(name.toLowerCase());
                }
            } catch (e) {
                console.error(`Error parsing Python packages: ${e.message}`);
            }
        }
        
        // Extract all Node.js dependencies from various package.json files
        const nodePackages = [];
        if (results.nodeDependencies) {
            const allPkgs = { ...results.nodeDependencies.packages, ...results.nodeDependencies.devPackages };
            for (const [dirPath, deps] of Object.entries(allPkgs)) {
                for (const [name, version] of Object.entries(deps)) {
                    nodePackages.push(name.toLowerCase());
                }
            }
        }
        
        // Find potential cross-language dependencies
        for (const crossDep of commonCrossDeps) {
            const pythonHas = pythonPackages.includes(crossDep.py.toLowerCase());
            const nodeHas = nodePackages.includes(crossDep.js.toLowerCase());
            
            if (pythonHas || nodeHas) {
                results.crossLanguage.packages.push({
                    python: { name: crossDep.py, installed: pythonHas },
                    javascript: { name: crossDep.js, installed: nodeHas },
                    crossCompatibilityRisk: pythonHas !== nodeHas // Flag as risk if only one language has it
                });
            }
        }
        
        console.log(`Found ${results.crossLanguage.packages.length} potential cross-language dependencies`);
    } catch (e) {
        console.error(`❌ Error analyzing cross-language dependencies: ${e.message}`);
    }

    // Helper function to find files recursively
    function findFilesRecursive(dir, matcher, ignoreDirs = []) {
        const results = [];
        try {
            if (!fs.existsSync(dir)) return results;
            
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            for (const entry of entries) {
                // Skip ignored directories
                if (entry.isDirectory() && ignoreDirs.includes(entry.name)) continue;
                
                const fullPath = path.join(dir, entry.name);
                
                if (entry.isDirectory()) {
                    // Recursively search subdirectories
                    results.push(...findFilesRecursive(fullPath, matcher, ignoreDirs));
                } else if (entry.isFile()) {
                    // Check if file matches the criteria
                    const isMatch = typeof matcher === 'function' 
                        ? matcher(entry.name) 
                        : entry.name === matcher;
                        
                    if (isMatch) {
                        results.push(fullPath);
                    }
                }
            }
        } catch (e) {
            console.error(`Error searching in directory ${dir}: ${e.message}`);
        }
        return results;
    }

    // Step 9: Aggregate Data and Generate Unified Report
    console.log('\n📊 Step 9: Generating unified analysis report...');
    const analysisData = aggregateReportData(projectRoot, toolDirName, reportsDir, results);
    const htmlReport = generateUnifiedHtmlReport(analysisData, plutoniumIconBase64);
    const htmlReportPath = path.join(reportsDir, 'unified_analysis.html');

    try {
        fs.writeFileSync(htmlReportPath, htmlReport);
        const relativeReportPath = path.relative(process.cwd(), htmlReportPath);
        console.log(`\n✅ Analysis complete! Unified report generated at: ${relativeReportPath}`);

        // Log key findings summary from aggregated data
        console.log('\n--- Analysis Summary ---');
        console.log(`- Python Packages Found: ${analysisData.dependency_analysis.python.total_packages}`);
        console.log(`- Node.js Packages Found: ${analysisData.dependency_analysis.javascript.total_packages || 0}`);
        console.log(`- Unpinned Python Packages: ${analysisData.dependency_analysis.python.unpinned_packages}`);
        console.log(`- Dependency Conflicts: ${analysisData.dependency_analysis.conflicts.length}`);
        console.log(`- Cross-Language Dependencies: ${analysisData.dependency_analysis.cross_language.length}`);
        console.log(`- Test Coverage: ${analysisData.testing_analysis.coverage.coverage_percent.toFixed(2)}% (${analysisData.testing_analysis.coverage.covered}/${analysisData.testing_analysis.coverage.total} lines)`);
        console.log(`- Test Files Found: ${analysisData.testing_analysis.test_files.length}`);
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
