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
    let packageData = {
        python: { installed: {}, unpinned: 0 },
        node: { installed: {}, unpinned: 0 },
        missing: [],
        crossLanguageConflicts: []
    };
    
    // Process Python packages
    if (results.pkgCheck?.status === 0 && results.pkgCheck.stdout) {
        try {
            // Attempt to parse the JSON output from the package check command
            packageData.python.installed = JSON.parse(results.pkgCheck.stdout);
            // Save the raw installed packages list to a file for reference
            fs.writeFileSync(
                path.join(reportsDir, 'installed_packages.json'),
                JSON.stringify(packageData.python.installed, null, 2) // Pretty-print JSON
            );
            console.log(`✅ Parsed ${Object.keys(packageData.python.installed).length} installed Python packages`);
            // Count how many packages are likely not pinned
            packageData.python.unpinned = Object.values(packageData.python.installed).reduce((count, version) => {
                return count + (isPinned(version) ? 0 : 1);
            }, 0);
        } catch (e) {
            // Log errors if JSON parsing fails
            console.error('❌ Error parsing installed packages JSON:', e.message);
            console.error('Raw output:', results.pkgCheck.stdout); // Show raw output for debugging
        }
    } else {
        console.error('❌ Failed to retrieve installed Python packages or command failed.');
        if (results.pkgCheck?.stderr) console.error("Stderr:", results.pkgCheck.stderr);
    }

    // Process Node.js packages
    if (results.npmCheck?.status === 0 && results.npmCheck.stdout) {
        try {
            // Parse npm list --json output
            const npmData = JSON.parse(results.npmCheck.stdout);
            if (npmData.dependencies) {
                // Extract packages from dependencies object
                Object.entries(npmData.dependencies).forEach(([name, data]) => {
                    packageData.node.installed[name] = data.version || 'unknown';
                    // Check if npm package uses a specific version (not a range)
                    if (data.from && !isPinned(data.from)) {
                        packageData.node.unpinned++;
                    }
                });
            }
            console.log(`✅ Parsed ${Object.keys(packageData.node.installed).length} installed Node.js packages`);
        } catch (e) {
            console.error('❌ Error parsing npm packages JSON:', e.message);
        }
    } else {
        console.log('ℹ️ No Node.js packages found or npm command failed.');
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

        // Process missing packages
        const missingRegex = /(\w+) requires (\w+).*which is not installed/i;
        dependencyConflicts.forEach(conflict => {
            const match = conflict.match(missingRegex);
            if (match) {
                packageData.missing.push({
                    requiringPackage: match[1],
                    missingPackage: match[2],
                    message: conflict
                });
            }
        });

        // Check for potential cross-language conflicts
        // This is a simple check looking for Node.js packages that might conflict with Python packages
        const pythonPackages = Object.keys(packageData.python.installed).map(p => p.toLowerCase());
        const nodePackages = Object.keys(packageData.node.installed).map(n => n.toLowerCase());
        
        // Find packages with same name in both ecosystems (potential namespace conflicts)
        const sameNamePackages = pythonPackages.filter(p => nodePackages.includes(p));
        if (sameNamePackages.length > 0) {
            packageData.crossLanguageConflicts = sameNamePackages.map(name => ({
                packageName: name,
                pythonVersion: packageData.python.installed[Object.keys(packageData.python.installed).find(p => p.toLowerCase() === name)],
                nodeVersion: packageData.node.installed[Object.keys(packageData.node.installed).find(n => n.toLowerCase() === name)],
                message: `Package "${name}" exists in both Python and Node.js ecosystems - could cause namespace conflicts if imported incorrectly.`
            }));
        }

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
            python: packageData.python,
            node: packageData.node,
            total_packages: Object.keys(packageData.python.installed).length + Object.keys(packageData.node.installed).length,
            unpinned_packages: packageData.python.unpinned + packageData.node.unpinned,
            conflicts: dependencyConflicts,
            missing_packages: packageData.missing,
            cross_language_conflicts: packageData.crossLanguageConflicts
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

    if (reportData.dependency_analysis.missing_packages.length > 0) {
        reportData.recommendations.push({
            type: 'critical',
            area: 'dependencies',
            message: `Install ${reportData.dependency_analysis.missing_packages.length} missing package(s) required by your dependencies. See the 'Conflicts' tab for details.`,
            priority: 'high'
        });
    }

    if (reportData.dependency_analysis.cross_language_conflicts.length > 0) {
        reportData.recommendations.push({
            type: 'warning',
            area: 'dependencies',
            message: `Found ${reportData.dependency_analysis.cross_language_conflicts.length} potential cross-language conflicts between Python and Node.js packages. Review imports to ensure correct package usage.`,
            priority: 'medium'
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
 * Generates HTML for the report using aggregated data.
 * @param {object} reportData - Object containing aggregated analysis data.
 * @param {string} reportsDir - Path to the reports directory where assets may be stored.
 * @returns {string} HTML content for the report.
 */
function generateReportHTML(reportData, reportsDir) {
    const iconPath = path.join(reportsDir, 'plutonium-icon.png');
    // Use a relative path for the HTML file
    const iconRelativePath = path.basename(iconPath);

    // Format timestamp
    const timestamp = reportData.timestamp;

    // Calculate total packages
    const totalPythonPackages = Object.keys(reportData.dependency_analysis.python.installed).length;
    const totalNodePackages = Object.keys(reportData.dependency_analysis.node.installed).length;
    const totalPackages = totalPythonPackages + totalNodePackages;
    
    // Format coverage percentage
    const coveragePercent = reportData.testing_analysis.coverage.coverage_percent.toFixed(2);
    
    // Generate HTML for installed Python packages (sorted alphabetically)
    const pythonPackageRows = Object.entries(reportData.dependency_analysis.python.installed)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([name, version]) => {
            const isPinned = version && !version.includes('~') && !version.includes('>') && 
                            !version.includes('<') && !version.includes('*');
            const statusClass = isPinned ? 'bg-success-subtle text-success-emphasis' : 'bg-warning-subtle text-warning-emphasis';
            const statusText = isPinned ? 'Pinned' : 'Unpinned';
            
            return `
            <tr>
                <td>${name}</td>
                <td>${version}</td>
                <td class="${statusClass}">${statusText}</td>
            </tr>`;
        }).join('');

    // Generate HTML for installed Node packages (sorted alphabetically)
    const nodePackageRows = Object.entries(reportData.dependency_analysis.node.installed)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([name, version]) => {
            const isPinned = version && !version.includes('~') && !version.includes('>') && 
                            !version.includes('<') && !version.includes('^') && !version.includes('*');
            const statusClass = isPinned ? 'bg-success-subtle text-success-emphasis' : 'bg-warning-subtle text-warning-emphasis';
            const statusText = isPinned ? 'Pinned' : 'Unpinned';
            
            return `
            <tr>
                <td>${name}</td>
                <td>${version}</td>
                <td class="${statusClass}">${statusText}</td>
            </tr>`;
        }).join('');

    // Generate HTML for missing packages
    const missingPackageRows = reportData.dependency_analysis.missing_packages
        .map(pkg => `
            <tr>
                <td>${pkg.requiringPackage}</td>
                <td>${pkg.missingPackage}</td>
                <td class="bg-danger-subtle text-danger-emphasis">${pkg.message}</td>
            </tr>
        `).join('');

    // Generate HTML for cross-language conflicts
    const crossLangConflictRows = reportData.dependency_analysis.cross_language_conflicts
        .map(conflict => `
            <tr>
                <td>${conflict.packageName}</td>
                <td>Python: ${conflict.pythonVersion}<br>Node.js: ${conflict.nodeVersion}</td>
                <td class="bg-warning-subtle text-warning-emphasis">${conflict.message}</td>
            </tr>
        `).join('');

    // Generate HTML for dependency conflicts
    const conflictRows = reportData.dependency_analysis.conflicts
        .map(conflict => `
            <tr>
                <td colspan="3" class="bg-danger-subtle text-danger-emphasis">${conflict}</td>
            </tr>
        `).join('');

    // Generate HTML for test files (showing path relative to project root)
    const testFileRows = reportData.testing_analysis.test_files
        .map(file => `
            <tr>
                <td>${file.relativePath}</td>
                <td>${file.fileSize} bytes</td>
            </tr>
        `).join('');

    // Generate HTML for recommendations using badge styling
    const recommendationsHTML = reportData.recommendations
        .sort((a, b) => {
            // Sort by priority (high > medium > low)
            const priorityOrder = { high: 0, medium: 1, low: 2 };
            return priorityOrder[a.priority] - priorityOrder[b.priority];
        })
        .map(rec => {
            // Select badge color based on type
            const badgeClass = rec.type === 'critical' ? 'bg-danger' :
                              rec.type === 'warning' ? 'bg-warning' :
                              'bg-info';
            
            // Select icon based on area
            const iconClass = rec.area === 'dependencies' ? 'bi-box-seam' :
                             rec.area === 'testing' ? 'bi-clipboard-check' :
                             'bi-info-circle';
            
            return `
            <div class="col-12 mb-3">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <span class="me-2"><i class="bi ${iconClass} fs-4"></i></span>
                            <div>
                                <div class="d-flex align-items-center mb-1">
                                    <span class="badge ${badgeClass} me-2">${rec.type.toUpperCase()}</span>
                                    <span class="badge bg-secondary">${rec.area}</span>
                                    <span class="ms-2 badge ${rec.priority === 'high' ? 'bg-danger' : 
                                                            rec.priority === 'medium' ? 'bg-warning' : 
                                                            'bg-info'}">
                                        Priority: ${rec.priority.toUpperCase()}
                                    </span>
                                </div>
                                <p class="mb-0">${rec.message}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
        }).join('');

    // Assemble the full HTML report
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plutonium - Project Analysis Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        body { background-color: #f8f9fa; }
        .report-header { 
            background: linear-gradient(135deg, #6f42c1, #007bff);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .logo-img {
            height: 60px;
            margin-right: 15px;
        }
        .card {
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-radius: 8px;
            border: none;
            margin-bottom: 1.5rem;
        }
        .card-header {
            background-color: #f1f1f1;
            border-bottom: 1px solid #e3e3e3;
            font-weight: 600;
        }
        .nav-tabs .nav-link {
            color: #495057;
            border: none;
            border-bottom: 2px solid transparent;
        }
        .nav-tabs .nav-link.active {
            color: #007bff;
            background-color: transparent;
            border-bottom: 2px solid #007bff;
        }
        .tab-pane {
            padding: 1.5rem;
        }
        .badge {
            font-weight: 500;
        }
        .progress {
            height: 8px;
            margin-bottom: 0.5rem;
        }
        .progress-label {
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
        }
        table {
            font-size: 0.875rem;
        }
        .timestamp {
            font-size: 0.8rem;
            color: rgba(255,255,255,0.8);
        }
    </style>
</head>
<body>
    <!-- Report Header -->
    <div class="report-header">
        <div class="container">
            <div class="d-flex align-items-center">
                <img src="${iconRelativePath}" alt="Plutonium Logo" class="logo-img">
                <div>
                    <h1 class="mb-0">Plutonium Code Analysis Report</h1>
                    <p class="timestamp mb-0">Generated on ${timestamp}</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="container mb-5">
        <!-- Summary Cards -->
        <div class="row mb-4">
            <div class="col-md-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">Test Coverage</h5>
                        <div class="progress-label d-flex justify-content-between">
                            <span>Coverage</span>
                            <span>${coveragePercent}%</span>
                        </div>
                        <div class="progress mb-3">
                            <div class="progress-bar ${coveragePercent >= 80 ? 'bg-success' : 
                                                      coveragePercent >= 50 ? 'bg-warning' : 
                                                      'bg-danger'}" 
                                 role="progressbar" 
                                 style="width: ${coveragePercent}%" 
                                 aria-valuenow="${coveragePercent}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100"></div>
                        </div>
                        <p class="mb-0">
                            <i class="bi bi-file-earmark-code me-1"></i>
                            ${reportData.testing_analysis.coverage.covered} / ${reportData.testing_analysis.coverage.total} lines covered
                        </p>
                        <p class="mb-0">
                            <i class="bi bi-file-earmark-text me-1"></i>
                            ${reportData.testing_analysis.test_files.length} test files
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">Dependencies</h5>
                        <p class="mb-1">
                            <i class="bi bi-box-seam me-1"></i>
                            ${totalPackages} Total Packages
                        </p>
                        <p class="mb-1">
                            <i class="bi bi-file-earmark-fill me-1"></i>
                            ${totalPythonPackages} Python packages
                        </p>
                        <p class="mb-1">
                            <i class="bi bi-filetype-js me-1"></i>
                            ${totalNodePackages} Node.js packages
                        </p>
                        <p class="mb-1 ${reportData.dependency_analysis.unpinned_packages > 0 ? 'text-warning' : 'text-success'}">
                            <i class="bi ${reportData.dependency_analysis.unpinned_packages > 0 ? 'bi-exclamation-triangle' : 'bi-check-circle'} me-1"></i>
                            ${reportData.dependency_analysis.unpinned_packages} Unpinned packages
                        </p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">Conflicts</h5>
                        <p class="mb-1 ${reportData.dependency_analysis.conflicts.length > 0 ? 'text-danger' : 'text-success'}">
                            <i class="bi ${reportData.dependency_analysis.conflicts.length > 0 ? 'bi-x-circle' : 'bi-check-circle'} me-1"></i>
                            ${reportData.dependency_analysis.conflicts.length} Dependency conflicts
                        </p>
                        <p class="mb-1 ${reportData.dependency_analysis.missing_packages.length > 0 ? 'text-danger' : 'text-success'}">
                            <i class="bi ${reportData.dependency_analysis.missing_packages.length > 0 ? 'bi-x-circle' : 'bi-check-circle'} me-1"></i>
                            ${reportData.dependency_analysis.missing_packages.length} Missing packages
                        </p>
                        <p class="mb-1 ${reportData.dependency_analysis.cross_language_conflicts.length > 0 ? 'text-warning' : 'text-success'}">
                            <i class="bi ${reportData.dependency_analysis.cross_language_conflicts.length > 0 ? 'bi-exclamation-triangle' : 'bi-check-circle'} me-1"></i>
                            ${reportData.dependency_analysis.cross_language_conflicts.length} Cross-language conflicts
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recommendations -->
        <div class="card mb-4">
            <div class="card-header">
                <i class="bi bi-lightbulb me-2"></i> Recommendations
            </div>
            <div class="card-body">
                <div class="row">
                    ${recommendationsHTML || `<div class="col-12"><p class="text-success mb-0"><i class="bi bi-check-circle me-2"></i>No issues found! Your project looks good.</p></div>`}
                </div>
            </div>
        </div>

        <!-- Detailed Analysis Tabs -->
        <div class="card">
            <div class="card-header">
                <ul class="nav nav-tabs card-header-tabs">
                    <li class="nav-item">
                        <a class="nav-link active" id="test-coverage-tab" data-bs-toggle="tab" href="#test-coverage">
                            Test Coverage (${reportData.testing_analysis.test_files.length})
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" id="dependencies-tab" data-bs-toggle="tab" href="#dependencies">
                            Dependencies (${totalPackages})
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link ${reportData.dependency_analysis.conflicts.length > 0 ? 'text-danger' : ''}" 
                           id="conflicts-tab" data-bs-toggle="tab" href="#conflicts">
                            Conflicts (${reportData.dependency_analysis.conflicts.length})
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" id="detailed-coverage-tab" data-bs-toggle="tab" href="#detailed-coverage">
                            Detailed Coverage
                        </a>
                    </li>
                </ul>
            </div>
            <div class="card-body p-0">
                <div class="tab-content">
                    <!-- Test Coverage Tab -->
                    <div class="tab-pane fade show active" id="test-coverage">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr>
                                        <th>Test File</th>
                                        <th>Size</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${testFileRows || `<tr><td colspan="2" class="text-center text-muted">No test files found.</td></tr>`}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Dependencies Tab -->
                    <div class="tab-pane fade" id="dependencies">
                        <div class="accordion" id="dependenciesAccordion">
                            <!-- Python Packages -->
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button" type="button" data-bs-toggle="collapse" 
                                            data-bs-target="#pythonPackages" aria-expanded="true" aria-controls="pythonPackages">
                                        Python Packages (${totalPythonPackages})
                                    </button>
                                </h2>
                                <div id="pythonPackages" class="accordion-collapse collapse show" data-bs-parent="#dependenciesAccordion">
                                    <div class="accordion-body p-0">
                                        <div class="table-responsive">
                                            <table class="table table-hover mb-0">
                                                <thead>
                                                    <tr>
                                                        <th>Package</th>
                                                        <th>Installed Version</th>
                                                        <th>Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${pythonPackageRows || `<tr><td colspan="3" class="text-center text-muted">No Python packages found.</td></tr>`}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Node Packages -->
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                            data-bs-target="#nodePackages" aria-expanded="false" aria-controls="nodePackages">
                                        Node.js Packages (${totalNodePackages})
                                    </button>
                                </h2>
                                <div id="nodePackages" class="accordion-collapse collapse" data-bs-parent="#dependenciesAccordion">
                                    <div class="accordion-body p-0">
                                        <div class="table-responsive">
                                            <table class="table table-hover mb-0">
                                                <thead>
                                                    <tr>
                                                        <th>Package</th>
                                                        <th>Installed Version</th>
                                                        <th>Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${nodePackageRows || `<tr><td colspan="3" class="text-center text-muted">No Node.js packages found.</td></tr>`}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Conflicts Tab -->
                    <div class="tab-pane fade" id="conflicts">
                        <div class="accordion" id="conflictsAccordion">
                            <!-- Dependency Conflicts -->
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button" type="button" data-bs-toggle="collapse" 
                                            data-bs-target="#dependencyConflicts" aria-expanded="true" aria-controls="dependencyConflicts">
                                        Dependency Conflicts (${reportData.dependency_analysis.conflicts.length})
                                    </button>
                                </h2>
                                <div id="dependencyConflicts" class="accordion-collapse collapse show" data-bs-parent="#conflictsAccordion">
                                    <div class="accordion-body p-0">
                                        <div class="table-responsive">
                                            <table class="table table-hover mb-0">
                                                <thead>
                                                    <tr>
                                                        <th colspan="3">Conflict Details</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${conflictRows || `<tr><td colspan="3" class="text-center text-muted">No dependency conflicts found.</td></tr>`}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Missing Packages -->
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                            data-bs-target="#missingPackages" aria-expanded="false" aria-controls="missingPackages">
                                        Missing Packages (${reportData.dependency_analysis.missing_packages.length})
                                    </button>
                                </h2>
                                <div id="missingPackages" class="accordion-collapse collapse" data-bs-parent="#conflictsAccordion">
                                    <div class="accordion-body p-0">
                                        <div class="table-responsive">
                                            <table class="table table-hover mb-0">
                                                <thead>
                                                    <tr>
                                                        <th>Requiring Package</th>
                                                        <th>Missing Package</th>
                                                        <th>Message</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${missingPackageRows || `<tr><td colspan="3" class="text-center text-muted">No missing packages found.</td></tr>`}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Cross-Language Conflicts -->
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" 
                                            data-bs-target="#crossLangConflicts" aria-expanded="false" aria-controls="crossLangConflicts">
                                        Cross-Language Conflicts (${reportData.dependency_analysis.cross_language_conflicts.length})
                                    </button>
                                </h2>
                                <div id="crossLangConflicts" class="accordion-collapse collapse" data-bs-parent="#conflictsAccordion">
                                    <div class="accordion-body p-0">
                                        <div class="table-responsive">
                                            <table class="table table-hover mb-0">
                                                <thead>
                                                    <tr>
                                                        <th>Package Name</th>
                                                        <th>Versions</th>
                                                        <th>Issue</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${crossLangConflictRows || `<tr><td colspan="3" class="text-center text-muted">No cross-language conflicts found.</td></tr>`}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Detailed Coverage Tab -->
                    <div class="tab-pane fade" id="detailed-coverage">
                        <div class="p-3">
                            <p class="mb-3">For detailed coverage information, check the generated HTML coverage report in the <code>reports/coverage</code> directory.</p>
                            <p class="mb-0"><i class="bi bi-info-circle me-2"></i>The coverage report contains line-by-line analysis of which code is covered by tests.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="text-center mt-4">
            <p class="text-muted small mb-0">Generated by Plutonium - Universal Development Toolkit</p>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>`;
}

// Export the necessary functions
module.exports = {
    generateReportHTML,
    aggregateReportData // Exporting aggregation might be useful separately
};
