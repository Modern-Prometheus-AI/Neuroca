/**
 * Component for aggregating analysis data and generating the unified HTML report.
 */
const fs = require('fs');
const path = require('path');

/**
 * Checks if a version string indicates a pinned version (basic check).
 * @param {string} version - The version string.
 * @returns {boolean} True if likely pinned, false otherwise.
 */
function isPinned(version) {
    // A version is considered pinned if it's not empty and doesn't contain
    // common range specifiers or wildcards. This is a basic check.
    // Real pinning often involves '=='. This checks for common non-pinned indicators.
    return !!version && !/[*<>=^~]/.test(version);
}

/**
 * Checks if a Python package exists in the installed list (case-insensitive).
 * @param {object} packages - Object mapping package names to versions.
 * @param {string} name - The package name to check.
 * @returns {boolean} True if the package exists.
 */
function hasPythonPackage(packages, name) {
    // Ensure packages is a valid object
    if (!packages || typeof packages !== 'object') {
        return false;
    }
    const lowerCaseName = name.toLowerCase();
    // Check if any key matches case-insensitively
    return Object.keys(packages).some(key => key.toLowerCase() === lowerCaseName);
}

/**
 * Evaluates the status of a package version and returns appropriate status indicators.
 * @param {string} name - Package name
 * @param {string} version - Package version
 * @param {Array} conflicts - List of conflicts
 * @returns {object} Status object with type, icon, and message
 */
function getPackageStatus(name, version, conflicts) {
    // Check if this package is involved in any conflicts
    const hasConflict = conflicts.some(conflict => 
        conflict.toLowerCase().includes(name.toLowerCase())
    );
    
    if (hasConflict) {
        return {
            type: 'error',
            icon: '🛑', // Red stop sign
            cssClass: 'conflict',
            message: 'Conflict detected'
        };
    }
    
    if (!isPinned(version)) {
        return {
            type: 'warning',
            icon: '⚠️', // Yellow warning
            cssClass: 'unpinned',
            message: 'Not pinned'
        };
    }

    // Default - everything looks good
    return {
        type: 'success',
        icon: '✅', // Green checkmark
        cssClass: 'ok',
        message: 'Pinned'
    };
}

/**
 * Recursively collects test file paths from a directory, ignoring common cache/config dirs.
 * @param {string} dir - The directory to scan.
 * @param {string} baseDir - The base directory for calculating relative paths.
 * @returns {string[]} An array of relative test file paths using forward slashes.
 */
function collectTestFiles(dir, baseDir) {
    const results = [];
    try {
        // Ensure directory exists before reading
        if (!fs.existsSync(dir)) {
            console.warn(`Test directory to scan does not exist: ${dir}`);
            return results;
        }
        const entries = fs.readdirSync(dir, { withFileTypes: true });

        for (const entry of entries) {
            const fullPath = path.join(dir, entry.name);
            // Use path.relative for consistent relative paths
            const relativePath = path.relative(baseDir, fullPath);

            // Skip common cache/config/node directories and hidden files/dirs
            const ignoredNames = ['__pycache__', '.pytest_cache', 'node_modules'];
            if (ignoredNames.includes(entry.name) || entry.name.startsWith('.')) {
                continue;
            }

            if (entry.isDirectory()) {
                // Recurse into subdirectories
                results.push(...collectTestFiles(fullPath, baseDir));
            } else if (entry.isFile() &&
                       (entry.name.startsWith('test_') || entry.name.endsWith('_test.py'))) {
                // Add test file path, ensuring forward slashes for consistency
                results.push(relativePath.replace(/\\/g, '/'));
            }
        }
    } catch (e) {
         // Log errors during file collection
         console.error(`Error scanning test directory ${dir}: ${e.message}`);
    }
    return results;
}

/**
 * Aggregates data from various analysis steps into a structured object for reporting.
 * @param {string} projectRoot - Absolute path to the project root.
 * @param {string} toolDirName - Name of the main tool directory (e.g., 'Neuroca').
 * @param {string} reportsDir - Absolute path to the reports directory.
 * @param {object} results - Object containing results from commandRunner steps (e.g., results.pkgCheck, results.conflictCheck).
 * @returns {object} Structured data object containing aggregated analysis results.
 */
function aggregateReportData(projectRoot, toolDirName, reportsDir, results) {
    const timestamp = new Date().toISOString().replace(/T/, ' ').replace(/\..+/, ''); // Format timestamp
    const coverageDir = path.join(reportsDir, 'coverage'); // Path to coverage reports

    // --- Dependency Data Aggregation ---
    let installedPackages = {};
    let unpinnedCount = 0;
    // Check if package check command ran successfully and produced output
    if (results.pkgCheck?.status === 0 && results.pkgCheck.stdout) {
        try {
            // Attempt to parse the JSON output from the package check command
            installedPackages = JSON.parse(results.pkgCheck.stdout);
            // Save the raw installed packages list to a file for reference
            fs.writeFileSync(
                path.join(reportsDir, 'installed_packages.json'),
                JSON.stringify(installedPackages, null, 2) // Pretty-print JSON
            );
             console.log(`✅ Parsed ${Object.keys(installedPackages).length} installed Python packages`);
             // Count how many packages are likely not pinned
             unpinnedCount = Object.values(installedPackages).reduce((count, version) => {
                 return count + (isPinned(version) ? 0 : 1);
             }, 0);
        } catch (e) {
            // Log errors if JSON parsing fails
            console.error('❌ Error parsing installed packages JSON:', e.message);
            console.error('Raw output:', results.pkgCheck.stdout); // Show raw output for debugging
        }
    } else {
        console.error('❌ Failed to retrieve installed packages or command failed.');
        if (results.pkgCheck?.stderr) console.error("Stderr:", results.pkgCheck.stderr);
    }

    // --- Conflict Data Aggregation ---
    let dependencyConflicts = [];
    // Check if conflict check command produced any output (stdout or stderr)
    if (results.conflictCheck && (results.conflictCheck.stdout || results.conflictCheck.stderr)) {
        // Combine stdout and stderr for parsing
        const output = (results.conflictCheck.stdout || '') + '\n' + (results.conflictCheck.stderr || '');
        const lines = output.split('\n');
        // Filter lines that indicate conflicts according to 'pip check' format
        dependencyConflicts = lines.filter(line =>
            line.includes('requires') && (line.includes('which is not installed') || line.includes('has requirement'))
        ).map(line => line.trim()); // Store trimmed lines

         if (dependencyConflicts.length > 0) {
             console.log(`⚠️ Found ${dependencyConflicts.length} dependency conflicts or missing dependencies.`);
             // Save conflicts to a file
             try {
                 fs.writeFileSync(
                     path.join(reportsDir, 'dependency_conflicts.json'),
                     JSON.stringify(dependencyConflicts, null, 2) // Pretty-print JSON
                 );
             } catch(e) {
                  console.error(`❌ Failed to write dependency conflicts file: ${e.message}`);
             }
         } else if (results.conflictCheck.status === 0) {
             // Only log success if pip check exited cleanly
             console.log('✅ No dependency conflicts found via pip check.');
         } else {
              console.warn('⚠️ Pip check exited with non-zero status but no conflict lines detected in output.');
         }
    } else {
        console.error('❌ Failed to run or get output from pip check for conflicts.');
    }

    // --- Coverage Data Aggregation ---
    let coverageData = { covered: 0, total: 0, coverage_percent: 0 };
    try {
        const coveragePath = path.join(coverageDir, 'coverage.json'); // Path to JSON coverage report
        // Check if the coverage JSON file exists
        if (fs.existsSync(coveragePath)) {
            // Read and parse the coverage JSON data
            const rawCoverageData = JSON.parse(fs.readFileSync(coveragePath, 'utf8'));
            // Extract totals if they exist
            if (rawCoverageData.totals) {
                coverageData.covered = rawCoverageData.totals.covered_lines ?? 0;
                coverageData.total = rawCoverageData.totals.num_statements ?? 0;
                // Safely get percentage, default to 0 if missing or not a number
                coverageData.coverage_percent = typeof rawCoverageData.totals.percent_covered === 'number'
                    ? rawCoverageData.totals.percent_covered
                    : 0;
                console.log(`✅ Parsed coverage data: ${coverageData.coverage_percent.toFixed(2)}%`);
            } else {
                 console.warn(`⚠️ Coverage JSON found at ${coveragePath} but missing "totals" key.`);
            }
        } else {
             // Warn if the coverage report wasn't generated or found
             console.warn(`⚠️ Coverage JSON report not found at: ${coveragePath}. Test run might have failed.`);
        }
    } catch (e) {
        // Log errors during coverage data processing
        console.error(`❌ Error reading or parsing coverage data: ${e.message}`);
    }

     // --- Test Files Aggregation ---
     let testFiles = [];
     try {
         // Define the base directory for tests relative to project root
         const testDir = path.join(projectRoot, toolDirName, 'tests');
         testFiles = collectTestFiles(testDir, projectRoot); // Collect recursively
         console.log(`✅ Found ${testFiles.length} potential test files.`);
     } catch (e) {
         console.error(`❌ Error collecting test files: ${e.message}`);
     }

    // --- Assemble Final Report Data Structure ---
    const reportData = {
        timestamp,
        dependency_analysis: {
            total_packages: Object.keys(installedPackages).length,
            unpinned_packages: unpinnedCount,
            conflicts: dependencyConflicts,
            installed_packages: installedPackages // Include the full list
        },
        testing_analysis: {
            coverage: coverageData,
            test_files: testFiles
        },
        recommendations: [] // Populated below
    };

    // --- Generate Recommendations Based on Aggregated Data ---
    if (reportData.dependency_analysis.unpinned_packages > 0) {
        reportData.recommendations.push({
            type: 'warning', // Severity type
            area: 'dependencies', // Area of concern
            message: `Pin the ${reportData.dependency_analysis.unpinned_packages} unpinned package(s) to specific versions in your requirements file(s) (e.g., requirements.txt, pyproject.toml) for reproducible builds.`,
            priority: 'high' // Priority level
        });
    }

    if (reportData.dependency_analysis.conflicts.length > 0) {
        reportData.recommendations.push({
            type: 'critical',
            area: 'dependencies',
            message: `Resolve ${reportData.dependency_analysis.conflicts.length} dependency conflict(s) identified by 'pip check'. See the 'Conflicts' tab for details. Mismatched versions can cause runtime errors.`,
            priority: 'high'
        });
    }

    // Add recommendation for low coverage only if lines were actually executed
    if (coverageData.total > 0 && coverageData.coverage_percent < 80) {
        reportData.recommendations.push({
            type: 'warning',
            area: 'testing',
            message: `Improve test coverage (currently ${coverageData.coverage_percent.toFixed(2)}%). Aim for 80% or higher to ensure code reliability.`,
            // Adjust priority based on how low the coverage is
            priority: coverageData.coverage_percent < 50 ? 'high' : 'medium'
        });
    } else if (coverageData.total === 0 && testFiles.length > 0) {
         // Warn if tests exist but no lines were covered
         reportData.recommendations.push({
            type: 'warning',
            area: 'testing',
            message: `No executable lines found during coverage analysis, although ${testFiles.length} test files were detected. Ensure tests are running correctly and covering the intended code in 'src/${toolDirName}'.`,
            priority: 'medium'
        });
    }

     // Save the aggregated data to a JSON file for potential other uses
     try {
         fs.writeFileSync(
             path.join(reportsDir, 'unified_analysis.json'),
             JSON.stringify(reportData, null, 2) // Pretty-print
         );
     } catch (e) {
          console.error(`❌ Failed to write unified JSON data: ${e.message}`);
     }

    // Return the structured data
    return reportData;
}


/**
 * Generates a unified HTML report from aggregated analysis data.
 * @param {object} data - The aggregated analysis data from aggregateReportData.
 * @param {string} [plutoniumIconBase64=''] - Base64 encoded icon data URL (optional).
 * @returns {string} HTML report content as a string.
 */
function generateUnifiedHtmlReport(data, plutoniumIconBase64 = '') {
    // Destructure data for easier access
    const { timestamp, dependency_analysis: depData, testing_analysis: testData, recommendations } = data;

    // Helper function to determine CSS class based on coverage percentage
    const getCoverageClass = (percent) => {
        if (percent >= 80) return 'high-coverage';
        if (percent >= 60) return 'medium-coverage';
        if (percent >= 40) return 'low-coverage';
        return 'critical-coverage'; // Use for < 40%
    };
    const coverageClass = getCoverageClass(testData.coverage.coverage_percent);

    // Helper function for coverage status text
    const getCoverageStatusText = (percent, totalLines) => {
        if (totalLines === 0) return 'ℹ No lines found to cover.';
        if (percent >= 80) return '✓ Good coverage';
        if (percent >= 60) return 'ℹ Moderate coverage';
        if (percent >= 40) return '⚠️ Low coverage';
        return '❌ Critical: Very low coverage';
    };
    const coverageStatusText = getCoverageStatusText(testData.coverage.coverage_percent, testData.coverage.total);

    // Generate HTML using template literals for readability
    // Includes CSS for styling and basic JS for tabs and search functionality
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unified Project Analysis Report</title>
    <style>
        /* Embedded CSS for styling the report */
        :root { /* Dark theme defaults */
            color-scheme: dark;
            --primary-color: #bb86fc; --secondary-color: #03dac6;
            --warning-color: #ffb74d; --error-color: #cf6679; --success-color: #81c784;
            --background-color: #121212; --card-bg: #1e1e1e; --text-color: #e0e0e0;
            --border-color: #333333; --link-color: #8ab4f8;
        }
        @media (prefers-color-scheme: light) { /* Light theme overrides */
            :root {
                color-scheme: light;
                --primary-color: #6200ee; --secondary-color: #018786;
                --warning-color: #ffa000; --error-color: #b00020; --success-color: #388e3c;
                --background-color: #f5f5f5; --card-bg: #ffffff; --text-color: #212121;
                --border-color: #e0e0e0; --link-color: #1a73e8;
            }
        }
        /* General body styling */
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: var(--text-color); background-color: var(--background-color); margin: 0; padding: 0; font-size: 16px; }
        /* Container for centering content */
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        /* Header styling */
        header { background-color: rgba(0, 0, 0, 0.2); padding: 30px 0; text-align: center; border-bottom: 1px solid var(--border-color); margin-bottom: 40px; }
        .header-content { display: flex; align-items: center; justify-content: center; flex-direction: column; }
        .header-content img { max-width: 80px; margin-bottom: 15px; border-radius: 50%; background-color: var(--card-bg); padding: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        /* Headings */
        h1, h2, h3 { color: var(--primary-color); font-weight: 600; margin-top: 0; }
        h1 { font-size: 2.2em; margin-bottom: 10px; }
        h2 { font-size: 1.8em; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-top: 40px; margin-bottom: 25px; }
        h3 { font-size: 1.3em; color: var(--secondary-color); margin-bottom: 15px; }
        /* Card styling for sections */
        .card { background-color: var(--card-bg); border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15); padding: 25px; margin-bottom: 30px; border: 1px solid var(--border-color); }
        /* Status colors */
        .warning { color: var(--warning-color); } .error { color: var(--error-color); } .success { color: var(--success-color); } .info { color: var(--secondary-color); }
        /* Table styling */
        table { width: 100%; border-collapse: collapse; margin: 25px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 0 0 1px var(--border-color); }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid var(--border-color); vertical-align: top; }
        th { background-color: rgba(187, 134, 252, 0.1); font-weight: 600; color: var(--primary-color); position: sticky; top: 0; z-index: 1; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background-color: rgba(255, 255, 255, 0.03); }
        /* Summary statistics cards */
        .summary-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }
        .stat-card { background: linear-gradient(135deg, rgba(187, 134, 252, 0.05), rgba(3, 218, 198, 0.05)); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border: 1px solid var(--border-color); transition: transform 0.2s ease; }
        .stat-card:hover { transform: translateY(-3px); }
        .stat-value { font-size: 2.5em; font-weight: 700; margin: 8px 0; }
        .stat-label { font-size: 1em; color: var(--text-color); opacity: 0.8; }
        /* Footer */
        footer { margin-top: 60px; padding: 20px 0; text-align: center; font-size: 0.9em; color: var(--text-color); opacity: 0.7; border-top: 1px solid var(--border-color); }
        /* Progress bar for coverage */
        .progress-bar-container { width: 100%; background-color: rgba(255, 255, 255, 0.1); border-radius: 4px; margin: 10px 0; overflow: hidden; height: 12px; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, var(--primary-color), var(--secondary-color)); border-radius: 4px; transition: width 0.5s ease-in-out; }
        /* Recommendation styling */
        .recommendation { border-left: 5px solid var(--primary-color); padding: 10px 15px; margin-bottom: 20px; background-color: rgba(187, 134, 252, 0.03); border-radius: 0 4px 4px 0; }
        .recommendation h3 { margin-top: 0; margin-bottom: 8px; display: flex; align-items: center; font-size: 1.1em;}
        .recommendation p { margin-bottom: 0; }
        .recommendation.warning { border-left-color: var(--warning-color); background-color: rgba(255, 183, 77, 0.03); }
        .recommendation.critical { border-left-color: var(--error-color); background-color: rgba(207, 102, 121, 0.03); }
        .recommendation.info { border-left-color: var(--secondary-color); background-color: rgba(3, 218, 198, 0.03); }
        /* Priority badges */
        .badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 600; margin-right: 10px; border: 1px solid; line-height: 1; }
        .badge.high { background-color: rgba(207, 102, 121, 0.2); color: var(--error-color); border-color: var(--error-color); }
        .badge.medium { background-color: rgba(255, 183, 77, 0.2); color: var(--warning-color); border-color: var(--warning-color); }
        /* Coverage classes */
        .high-coverage { color: var(--success-color); }
        .medium-coverage { color: var(--secondary-color); }
        .low-coverage { color: var(--warning-color); }
        .critical-coverage { color: var(--error-color); }
        /* Tab styles */
        .tabs { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
        .tab { cursor: pointer; padding: 12px 20px; border-radius: 6px; background-color: rgba(255, 255, 255, 0.05); border: 1px solid var(--border-color); transition: all 0.2s ease; }
        .tab:hover { background-color: rgba(187, 134, 252, 0.1); }
        .tab.active { background-color: rgba(187, 134, 252, 0.2); border-color: var(--primary-color); color: var(--primary-color); font-weight: 600; }
        .tab-content { display: none; animation: fadeIn 0.3s; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        /* Coverage iframe */
        .coverage-iframe-container { width: 100%; height: 600px; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; margin-top: 20px; }
        .coverage-iframe { width: 100%; height: 100%; border: none; }
        /* Search */
        .search-container { margin-bottom: 15px; }
        .search-box { width: 100%; padding: 10px 15px; font-size: 16px; border-radius: 6px; border: 1px solid var(--border-color); background-color: rgba(255, 255, 255, 0.05); color: var(--text-color); transition: all 0.2s ease; }
        .search-box:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 2px rgba(187, 134, 252, 0.3); }
        /* Status tags for dependencies */
        .status-tag { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: 600; }
        .status-tag.ok { background-color: rgba(129, 199, 132, 0.2); color: var(--success-color); border: 1px solid var(--success-color); }
        .status-tag.unpinned { background-color: rgba(255, 183, 77, 0.2); color: var(--warning-color); border: 1px solid var(--warning-color); }
        .status-tag.conflict { background-color: rgba(207, 102, 121, 0.2); color: var(--error-color); border: 1px solid var(--error-color); }
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .container { padding: 0 15px; }
            .summary-stats { grid-template-columns: 1fr; }
            .tab { padding: 10px; width: calc(50% - 10px); text-align: center; }
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            ${plutoniumIconBase64 ? `<img src="${plutoniumIconBase64}" alt="Plutonium Logo">` : ''}
            <h1>Project Analysis Report</h1>
            <p class="generated-time">Generated: ${timestamp}</p>
        </div>
    </header>
    <div class="container">
        <div class="card">
            <h2>Executive Summary</h2>
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-label">Code Coverage</div>
                    <div class="stat-value ${coverageClass}">${testData.coverage.coverage_percent.toFixed(1)}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Packages</div>
                    <div class="stat-value">${depData.total_packages}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Unpinned Packages</div>
                    <div class="stat-value ${depData.unpinned_packages > 0 ? 'warning' : 'success'}">${depData.unpinned_packages}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Dependency Conflicts</div>
                    <div class="stat-value ${depData.conflicts.length > 0 ? 'error' : 'success'}">${depData.conflicts.length}</div>
                </div>
            </div>
        </div>

        ${recommendations.length > 0 ? `
        <div class="card">
            <h2>Recommendations</h2>
            ${recommendations.map(rec => `
                <div class="recommendation ${rec.type}">
                    <h3><span class="badge ${rec.priority}">${rec.priority.toUpperCase()}</span> ${rec.area.charAt(0).toUpperCase() + rec.area.slice(1)}</h3>
                    <p>${rec.message}</p>
                </div>
            `).join('')}
        </div>
        ` : ''}

        <div class="tabs">
            <div class="tab active" data-tab="coverage">Test Coverage (${testData.test_files.length})</div>
            <div class="tab" data-tab="dependencies">Dependencies (${depData.total_packages})</div>
            <div class="tab" data-tab="conflicts">Conflicts (${depData.conflicts.length})</div>
            <div class="tab" data-tab="detailed-coverage">Detailed Coverage</div>
        </div>

        <div class="tab-content active" id="tab-coverage">
            <div class="card">
                <h2>Test Coverage Analysis</h2>
                <div class="coverage-summary">
                    <div class="coverage-percent ${coverageClass}">${testData.coverage.coverage_percent.toFixed(1)}%</div>
                    <div class="coverage-details">
                        <p>Lines covered: <strong>${testData.coverage.covered}</strong> out of <strong>${testData.coverage.total}</strong></p>
                        <div class="progress-bar-container">
                            <div class="progress-bar" style="width: ${testData.coverage.coverage_percent}%;"></div>
                        </div>
                        <p class="${coverageClass}">${coverageStatusText}</p>
                    </div>
                </div>
                <h3>Test Files (${testData.test_files.length})</h3>
                 <div class="search-container">
                     <input type="text" class="search-box" id="test-file-search" placeholder="Search test files (e.g., test_memory.py)...">
                 </div>
                ${testData.test_files.length > 0 ? `
                <table>
                    <thead><tr><th>Test File Path</th></tr></thead>
                    <tbody class="searchable-content">
                        ${testData.test_files.map(file => `<tr><td>${file}</td></tr>`).join('')}
                    </tbody>
                </table>
                ` : '<p>No test files found or collected.</p>'}
            </div>
        </div>

        <div class="tab-content" id="tab-dependencies">
            <div class="card">
                <h2>Dependency Analysis</h2>
                <h3>Python Packages (${depData.total_packages})</h3>
                ${depData.unpinned_packages > 0 ? `
                <p class="warning">⚠️ ${depData.unpinned_packages} package(s) are not pinned to specific versions.</p>
                ` : '<p class="success">✓ All detected packages appear to be pinned.</p>'}
                 <div class="search-container">
                     <input type="text" class="search-box" id="package-search" placeholder="Search packages (e.g., requests)...">
                 </div>
                <table>
                    <thead><tr><th>Package</th><th>Installed Version</th><th>Status</th></tr></thead>
                    <tbody class="searchable-content">
                        ${Object.entries(depData.installed_packages).sort((a,b) => a[0].localeCompare(b[0])).map(([name, version]) => {
                            const status = getPackageStatus(name, version, depData.conflicts);
                            return `
                            <tr>
                                <td>${name}</td>
                                <td>${version}</td>
                                <td>
                                    <span class="status-tag ${status.cssClass}">${status.icon} ${status.message}</span>
                                </td>
                            </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="tab-content" id="tab-conflicts">
            <div class="card">
                <h2>Dependency Conflicts</h2>
                ${depData.conflicts.length > 0 ? `
                <p class="error">❌ Found ${depData.conflicts.length} dependency conflict(s) or missing dependencies via 'pip check'.</p>
                <table>
                    <thead><tr><th>Issue Description</th></tr></thead>
                    <tbody>
                        ${depData.conflicts.map(conflict => `<tr><td class="error">${conflict}</td></tr>`).join('')}
                    </tbody>
                </table>
                ` : '<p class="success">✓ No dependency conflicts found via \'pip check\'.</p>'}
            </div>
        </div>

        <div class="tab-content" id="tab-detailed-coverage">
             <div class="card">
                 <h2>Detailed Coverage Report</h2>
                 <div class="coverage-guide-card">
                    <h3>📊 How to Read Coverage Reports</h3>
                    <p>Coverage reports show which parts of your code are executed during tests:</p>
                    <ul>
                        <li><strong style="color: var(--success-color);">Green lines</strong>: Code that was executed by tests</li>
                        <li><strong style="color: var(--error-color);">Red lines</strong>: Code that was never executed during tests</li>
                        <li><strong style="color: var(--warning-color);">Yellow lines</strong> (if any): Branch coverage - a conditional that was only partially tested</li>
                    </ul>
                    <p>Higher percentages mean more code is being tested. When viewing the detailed report:</p>
                    <ol>
                        <li>Click on module/file names to drill down into specific code files</li>
                        <li>Look for red sections to identify untested code</li>
                        <li>Focus on testing critical functions with low coverage</li>
                    </ol>
                 </div>
                 <p>The full HTML coverage report provides line-by-line details. It may take a moment to load below.</p>
                 <p><a href="coverage/html/index.html" target="_blank">Open full HTML coverage report in new tab</a></p>
                 <div class="coverage-iframe-container">
                     <iframe class="coverage-iframe" src="coverage/html/index.html" title="Detailed Coverage Report" sandbox="allow-scripts allow-same-origin"></iframe>
                 </div>
             </div>
         </div>

        <footer>
            Generated by Plutonium - Universal Development Toolkit
        </footer>
    </div>

    <script>
        // Simple inline script for tabs and search - Consider moving to a separate file
        document.addEventListener('DOMContentLoaded', function() {
            // Tab switching logic
            const tabs = document.querySelectorAll('.tab');
            const tabContents = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    tabs.forEach(t => t.classList.remove('active'));
                    tabContents.forEach(c => c.classList.remove('active'));
                    tab.classList.add('active');
                    const targetId = 'tab-' + tab.getAttribute('data-tab');
                    const targetContent = document.getElementById(targetId);
                    if(targetContent) targetContent.classList.add('active');
                });
            });

            // Generic search filter function
            const addSearchFilter = (inputId, tableBodySelector) => {
                const searchInput = document.getElementById(inputId);
                if (!searchInput) return; // Exit if input not found
                const tableBody = document.querySelector(tableBodySelector);
                if (!tableBody) return; // Exit if table body not found
                const tableRows = tableBody.querySelectorAll('tr');
                if (tableRows.length === 0) return; // Exit if no rows

                searchInput.addEventListener('input', function() {
                    const searchTerm = this.value.toLowerCase().trim();
                    tableRows.forEach(row => {
                        const textContent = row.textContent.toLowerCase();
                        // Show row if search term is empty or text includes term
                        row.style.display = (searchTerm === '' || textContent.includes(searchTerm)) ? '' : 'none';
                    });
                });
            };

            // Apply search filters to relevant tables
            addSearchFilter('test-file-search', '#tab-coverage .searchable-content');
            addSearchFilter('package-search', '#tab-dependencies .searchable-content');
        });
    </script>
</body>
</html>`;
}


// Export the necessary functions
module.exports = {
    generateUnifiedHtmlReport,
    aggregateReportData // Exporting aggregation might be useful separately
};
