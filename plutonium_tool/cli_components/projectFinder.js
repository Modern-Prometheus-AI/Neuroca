/**
 * Component for finding the project root directory.
 */
const path = require('path');
const fs = require('fs');

/**
 * Traverses up the directory tree to find the project root.
 * The project root is identified by the presence of the specified tool directory structure.
 * @param {string} startDir - The directory to start searching from.
 * @param {string} toolDirName - The name of the main tool directory (e.g., 'Neuroca').
 * @param {string} toolSubdirName - The name of the subdirectory containing the tool (e.g., 'plutonium_tool').
 * @param {number} maxDepth - Maximum number of parent directories to check.
 * @returns {string|null} The absolute path to the project root, or null if not found.
 */
function findProjectRoot(startDir, toolDirName, toolSubdirName, maxDepth = 10) {
    let currentDir = path.resolve(startDir); // Ensure absolute path

    for (let i = 0; i < maxDepth; i++) {
        // Check if the specific tool directory exists within the main tool directory
        const toolDirPath = path.join(currentDir, toolDirName, toolSubdirName);
        // Also check for a common marker file/dir like 'pyproject.toml' or '.git' for robustness
        const markerPath = path.join(currentDir, 'pyproject.toml'); // Example marker

        // Check if both the specific tool path and a root marker exist
        // Adapt the marker check ('pyproject.toml') if necessary for your project structure
        if (fs.existsSync(toolDirPath) && fs.existsSync(markerPath)) {
            return currentDir; // Found the root
        }

        // Go up one directory level
        const parentDir = path.dirname(currentDir);
        if (parentDir === currentDir) {
            // Reached the filesystem root
            break;
        }
        currentDir = parentDir;
    }

    return null; // Project root not found within maxDepth
}

// Export the function for use in other modules
module.exports = {
    findProjectRoot
};
