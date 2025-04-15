/**
 * Performance Analyzer Module for Plutonium
 * 
 * This module analyzes performance metrics for various types of projects
 * and provides insights and recommendations for optimization.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { getFiles } = require('./language-detector');

// Performance analysis configurations for different project types
const PERFORMANCE_CONFIGS = {
  javascript: {
    metrics: ['bundleSize', 'startupTime', 'memoryUsage'],
    tools: ['webpack-bundle-analyzer', 'lighthouse', 'source-map-explorer'],
    commands: {
      bundleSize: 'npm run build && du -sh ./dist',
      dependencies: 'npx madge --circular ./src'
    }
  },
  typescript: {
    metrics: ['bundleSize', 'startupTime', 'typeCheckTime', 'memoryUsage'],
    tools: ['webpack-bundle-analyzer', 'ts-metrics', 'source-map-explorer'],
    commands: {
      bundleSize: 'npm run build && du -sh ./dist',
      typeCheckTime: 'time npx tsc --noEmit',
      dependencies: 'npx madge --circular --ts ./src'
    }
  },
  react: {
    metrics: ['bundleSize', 'renderTime', 'memoryUsage'],
    tools: ['webpack-bundle-analyzer', 'react-profiler', 'why-did-you-render'],
    commands: {
      bundleSize: 'npm run build && du -sh ./build',
      dependencies: 'npx madge --circular ./src'
    }
  },
  angular: {
    metrics: ['bundleSize', 'startupTime', 'changeDetection'],
    tools: ['webpack-bundle-analyzer', 'angular-performance', 'source-map-explorer'],
    commands: {
      bundleSize: 'ng build --prod && du -sh ./dist',
      dependencies: 'npx madge --circular ./src'
    }
  },
  vue: {
    metrics: ['bundleSize', 'startupTime', 'renderTime'],
    tools: ['webpack-bundle-analyzer', 'vue-perf-devtool', 'source-map-explorer'],
    commands: {
      bundleSize: 'npm run build && du -sh ./dist',
      dependencies: 'npx madge --circular ./src'
    }
  },
  python: {
    metrics: ['startupTime', 'memoryUsage', 'importTime'],
    tools: ['py-spy', 'memory_profiler', 'pytest-profiling', 'scalene'],
    commands: {
      importTime: 'python -X importtime -c "import main"',
      startupTime: 'time python -c "import main"',
      dependencies: 'pipdeptree'
    }
  },
  django: {
    metrics: ['queryCount', 'renderTime', 'memoryUsage'],
    tools: ['django-debug-toolbar', 'django-silk', 'py-spy', 'django-perf-rec'],
    commands: {
      startupTime: 'time python manage.py runserver --noreload',
      migrations: 'python manage.py showmigrations',
      dependencies: 'pipdeptree'
    }
  },
  flask: {
    metrics: ['requestTime', 'memoryUsage', 'startupTime'],
    tools: ['flask-profiler', 'py-spy', 'memory_profiler'],
    commands: {
      startupTime: 'time python -m flask run --no-debugger --no-reload',
      dependencies: 'pipdeptree'
    }
  },
  java: {
    metrics: ['startupTime', 'memoryUsage', 'garbageCollection'],
    tools: ['jvisualvm', 'jmh', 'async-profiler'],
    commands: {
      dependencies: 'mvn dependency:tree',
      compileTime: 'time mvn compile'
    }
  },
  spring: {
    metrics: ['startupTime', 'requestTime', 'memoryUsage', 'beanInitialization'],
    tools: ['spring-boot-devtools', 'spring-boot-actuator', 'jvisualvm'],
    commands: {
      startupTime: 'time mvn spring-boot:run',
      dependencies: 'mvn dependency:tree'
    }
  },
  go: {
    metrics: ['buildTime', 'binarySize', 'memoryUsage', 'goroutines'],
    tools: ['pprof', 'trace', 'benchstat'],
    commands: {
      buildTime: 'time go build -o app .',
      binarySize: 'go build -o app . && du -sh ./app',
      dependencies: 'go mod graph'
    }
  },
  rust: {
    metrics: ['buildTime', 'binarySize', 'memoryUsage'],
    tools: ['cargo-flamegraph', 'dhat', 'criterion'],
    commands: {
      buildTime: 'time cargo build --release',
      binarySize: 'cargo build --release && du -sh ./target/release',
      dependencies: 'cargo tree'
    }
  },
  cpp: {
    metrics: ['buildTime', 'binarySize', 'memoryUsage'],
    tools: ['gprof', 'valgrind', 'perf'],
    commands: {
      buildTime: 'time make',
      binarySize: 'make && du -sh ./build'
    }
  }
};

/**
 * Execute shell command and capture output
 * 
 * @param {string} command - Command to execute
 * @param {string} cwd - Working directory
 * @returns {Object} - Result with stdout, stderr, and status
 */
function executeCommand(command, cwd) {
  try {
    const output = execSync(command, { 
      cwd: cwd,
      encoding: 'utf8',
      stdio: 'pipe',
      timeout: 30000 // 30 seconds timeout
    });
    
    return {
      success: true,
      output: output.toString()
    };
  } catch (err) {
    return {
      success: false,
      error: err.message,
      output: err.stdout ? err.stdout.toString() : '',
      stderr: err.stderr ? err.stderr.toString() : ''
    };
  }
}

/**
 * Analyze file sizes within a project
 * 
 * @param {string} projectPath - Path to project
 * @param {string[]} extensions - File extensions to analyze
 * @returns {Object} - Size analysis results
 */
function analyzeFileSizes(projectPath, extensions) {
  const files = getFiles(projectPath, 5);
  const results = {
    totalSize: 0,
    largestFiles: [],
    byExtension: {},
    byDirectory: {}
  };
  
  // Filter files by extension if specified
  const filteredFiles = extensions && extensions.length > 0
    ? files.filter(file => extensions.some(ext => file.endsWith(ext)))
    : files;
  
  // Analyze file sizes
  filteredFiles.forEach(file => {
    try {
      const stats = fs.statSync(file);
      const size = stats.size;
      const ext = path.extname(file).toLowerCase();
      const dir = path.dirname(file).replace(projectPath, '').replace(/^[\/\\]/, '').split(path.sep)[0] || '.';
      
      // Update total size
      results.totalSize += size;
      
      // Track size by extension
      if (!results.byExtension[ext]) {
        results.byExtension[ext] = { count: 0, size: 0 };
      }
      results.byExtension[ext].count++;
      results.byExtension[ext].size += size;
      
      // Track size by directory
      if (!results.byDirectory[dir]) {
        results.byDirectory[dir] = { count: 0, size: 0 };
      }
      results.byDirectory[dir].count++;
      results.byDirectory[dir].size += size;
      
      // Track largest files
      results.largestFiles.push({
        path: file.replace(projectPath, '').replace(/^[\/\\]/, ''),
        size
      });
    } catch (err) {
      // Skip files we can't access
    }
  });
  
  // Sort largest files
  results.largestFiles.sort((a, b) => b.size - a.size);
  results.largestFiles = results.largestFiles.slice(0, 20); // Keep only top 20
  
  return results;
}

/**
 * Find system commands for performance analysis
 * 
 * @param {string[]} commands - Commands to check
 * @returns {string[]} - Available commands
 */
function findAvailableCommands(commands) {
  return commands.filter(cmd => {
    const baseCmd = cmd.split(' ')[0];
    try {
      execSync(`${process.platform === 'win32' ? 'where' : 'which'} ${baseCmd}`, { stdio: 'ignore' });
      return true;
    } catch (err) {
      return false;
    }
  });
}

/**
 * Analyze import/dependency structure
 * 
 * @param {string} projectPath - Path to project
 * @param {string} projectType - Project type
 * @returns {Object} - Dependency analysis results
 */
function analyzeDependencyStructure(projectPath, projectType) {
  const result = {
    success: false,
    circularDependencies: [],
    dependencyCount: 0
  };
  
  const config = PERFORMANCE_CONFIGS[projectType];
  if (!config || !config.commands || !config.commands.dependencies) {
    return result;
  }
  
  try {
    const cmdResult = executeCommand(config.commands.dependencies, projectPath);
    if (cmdResult.success) {
      result.success = true;
      result.output = cmdResult.output;
      
      // Try to extract circular dependencies from output
      if (cmdResult.output.includes('Circular dependencies')) {
        const circularMatches = cmdResult.output.match(/Circular dependencies.+?(?:\r?\n){2}/gs);
        if (circularMatches) {
          result.circularDependencies = circularMatches[0].split('\n')
            .filter(line => line.trim().length > 0 && !line.includes('Circular dependencies'))
            .map(line => line.trim());
        }
      }
      
      // Try to count dependencies
      const dependenciesMatch = cmdResult.output.match(/Found (\d+) dependencies/i);
      if (dependenciesMatch) {
        result.dependencyCount = parseInt(dependenciesMatch[1], 10);
      }
    }
  } catch (err) {
    // Ignore errors
  }
  
  return result;
}

/**
 * Analyze performance of a project
 * 
 * @param {string} projectPath - Path to the project
 * @param {Object} projectType - Project type information from language-detector
 * @returns {Object} - Performance analysis results
 */
function analyze(projectPath, projectType) {
  try {
    // Normalize path
    const basePath = path.resolve(projectPath);
    
    // Determine which performance config to use
    const languages = projectType.languages.map(lang => lang.name);
    const frameworks = projectType.frameworks ? projectType.frameworks.map(f => f.name) : [];
    
    // Try to use framework config first, then language config
    let selectedConfig = null;
    for (const framework of frameworks) {
      if (PERFORMANCE_CONFIGS[framework]) {
        selectedConfig = PERFORMANCE_CONFIGS[framework];
        break;
      }
    }
    
    // If no framework config, use language config
    if (!selectedConfig && languages.length > 0) {
      for (const lang of languages) {
        if (PERFORMANCE_CONFIGS[lang]) {
          selectedConfig = PERFORMANCE_CONFIGS[lang];
          break;
        }
      }
    }
    
    // If no config found, return a basic analysis
    if (!selectedConfig) {
      return {
        status: 'limited',
        message: `No specific performance config for ${projectType.type}`,
        basicAnalysis: analyzeFileSizes(basePath, null)
      };
    }
    
    // Get file extension for the primary language
    let fileExtensions = [];
    if (languages[0] === 'javascript') fileExtensions = ['.js', '.jsx'];
    else if (languages[0] === 'typescript') fileExtensions = ['.ts', '.tsx'];
    else if (languages[0] === 'python') fileExtensions = ['.py'];
    else if (languages[0] === 'java') fileExtensions = ['.java'];
    else if (languages[0] === 'ruby') fileExtensions = ['.rb'];
    else if (languages[0] === 'go') fileExtensions = ['.go'];
    else if (languages[0] === 'rust') fileExtensions = ['.rs'];
    else if (languages[0] === 'cpp' || languages[0] === 'c') fileExtensions = ['.cpp', '.c', '.h', '.hpp'];
    
    // Build results object
    const results = {
      status: 'success',
      projectType: projectType.type,
      fileAnalysis: analyzeFileSizes(basePath, fileExtensions),
      recommendedTools: selectedConfig.tools || [],
      availableMetrics: selectedConfig.metrics || [],
      commandResults: {},
      systemSupport: {
        availableCommands: []
      },
      suggestions: []
    };
    
    // Check which performance-related commands are available
    const commonCommands = ['time', 'du', 'find', 'grep'];
    results.systemSupport.availableCommands = findAvailableCommands(commonCommands);
    
    // Run appropriate commands if possible
    if (selectedConfig.commands) {
      Object.entries(selectedConfig.commands).forEach(([key, command]) => {
        // Skip commands that would modify the project
        if (command.includes('build') && !command.includes('--dry-run')) {
          results.commandResults[key] = {
            skipped: true,
            reason: 'Build commands are skipped in analysis mode. Use --run-builds to enable.'
          };
          return;
        }
        
        // Execute command
        const cmdResult = executeCommand(command, basePath);
        results.commandResults[key] = cmdResult;
      });
    }
    
    // Analyze dependency structure
    results.dependencies = analyzeDependencyStructure(basePath, languages[0] || frameworks[0]);
    
    // Generate performance suggestions
    if (results.fileAnalysis.largestFiles.length > 0) {
      const largestFile = results.fileAnalysis.largestFiles[0];
      if (largestFile.size > 1000000) { // 1MB
        results.suggestions.push({
          type: 'warning',
          category: 'file-size',
          description: `Large file detected: ${largestFile.path} (${Math.round(largestFile.size / 1024)}KB)`,
          solution: 'Consider breaking down large files into smaller modules.'
        });
      }
    }
    
    // Extension-specific suggestions
    if (languages[0] === 'javascript' || languages[0] === 'typescript' || frameworks.includes('react') || frameworks.includes('vue') || frameworks.includes('angular')) {
      results.suggestions.push({
        type: 'info',
        category: 'bundling',
        description: 'Consider code splitting to reduce initial bundle size',
        solution: 'Use dynamic imports or React.lazy() to split code by route or component.'
      });
    }
    
    if (results.dependencies && results.dependencies.circularDependencies && results.dependencies.circularDependencies.length > 0) {
      results.suggestions.push({
        type: 'warning',
        category: 'architecture',
        description: `${results.dependencies.circularDependencies.length} circular dependencies detected`,
        solution: 'Refactor code to break circular dependencies, which can cause performance issues.'
      });
    }
    
    return results;
    
  } catch (err) {
    return {
      status: 'failed',
      error: err.message,
      stack: err.stack
    };
  }
}

module.exports = {
  analyze,
  PERFORMANCE_CONFIGS
};