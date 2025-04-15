#!/usr/bin/env node
/**
 * Plutonium CLI Wrapper (Neuroca subdirectory)
 * 
 * This is a convenience wrapper that forwards commands to the actual
 * Plutonium implementation in the plutonium_tool directory.
 */

const path = require('path');
const { spawnSync } = require('child_process');

// The actual path to the Plutonium implementation
const PLUTONIUM_PATH = path.join(__dirname, 'plutonium_tool', 'plutonium.js');

// Forward all arguments
const args = process.argv.slice(2);

// Run the actual Plutonium script with all arguments
const result = spawnSync('node', [PLUTONIUM_PATH, ...args], {
  stdio: 'inherit',
  cwd: process.cwd()
});

// Forward the exit code
process.exit(result.status || 0);