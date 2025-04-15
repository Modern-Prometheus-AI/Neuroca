/**
 * Utility component for running synchronous external commands.
 */
const { spawnSync } = require('child_process');

/**
 * Runs a command synchronously and handles basic error reporting.
 * @param {string} command - The command to run (e.g., 'node', 'python').
 * @param {string[]} [args=[]] - An array of arguments for the command.
 * @param {object} [options={}] - Options for spawnSync (e.g., cwd, stdio, encoding).
 * @returns {object} The result object from spawnSync, including status, stdout, stderr, error.
 */
function runSyncCommand(command, args = [], options = {}) {
    // Log the command being executed
    console.log(`\n▶️ Running: ${command} ${args.join(' ')} ${options.cwd ? `(in ${options.cwd})` : ''}`);
    try {
        // Execute the command synchronously
        const result = spawnSync(command, args, {
            // Default options
            stdio: 'inherit', // Show output in real-time by default
            encoding: 'utf8',
            shell: process.platform === 'win32', // Use shell on Windows for better command compatibility
            ...options, // Allow overriding defaults
        });

        // Handle potential errors during spawn itself
        if (result.error) {
            console.error(`❌ Error executing command '${command}':`, result.error);
            // Ensure status is non-zero on error and add error object
            result.status = result.status ?? 1;
            result.error = result.error; // Ensure error object is attached
        }
        // Handle non-zero exit codes if stdio wasn't inherited (otherwise user saw it)
        else if (result.status !== 0 && options.stdio !== 'inherit') {
            console.error(`❌ Command '${command} ${args.join(' ')}' exited with status ${result.status}`);
            if (result.stderr) {
                console.error("Stderr:", result.stderr.trim());
            }
        }

        // Ensure stdout/stderr are strings, especially if stdio was 'pipe' or similar
        result.stdout = result.stdout || '';
        result.stderr = result.stderr || '';

        return result;
    } catch (err) {
        // Handle unexpected errors during the spawnSync call itself
        console.error(`❌ Unexpected error running command '${command}':`, err);
        // Return a consistent error structure
        return {
            status: 1,
            error: err,
            stdout: '',
            stderr: err.message || 'Unexpected error during command execution'
        };
    }
}

// Export the function
module.exports = {
    runSyncCommand
};
