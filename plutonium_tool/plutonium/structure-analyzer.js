/**
 * Structure Analyzer Module for Plutonium
 * 
 * This module analyzes project structure and provides insights and recommendations
 * for different types of codebases.
 */

const fs = require('fs');
const path = require('path');
const { getFiles } = require('./language-detector');

/**
 * Common project structures by type
 */
const PROJECT_STRUCTURES = {
  javascript: {
    dirs: ['src', 'test', 'dist', 'public', 'assets'],
    files: ['package.json', '.eslintrc', '.prettierrc', 'jest.config.js'],
    patterns: {
      'src/**/*.js': 'Source code files',
      'test/**/*.js': 'Test files',
      '**/*.test.js': 'Test files',
      '**/*.spec.js': 'Test files',
      'src/components/**/*.js': 'UI components'
    }
  },
  typescript: {
    dirs: ['src', 'test', 'dist', 'types'],
    files: ['tsconfig.json', 'package.json', '.eslintrc'],
    patterns: {
      'src/**/*.ts': 'Source code files',
      'src/**/*.tsx': 'React components',
      'test/**/*.ts': 'Test files',
      'types/**/*.d.ts': 'Type definition files'
    }
  },
  python: {
    dirs: ['src', 'tests', 'docs', 'scripts'],
    files: ['setup.py', 'requirements.txt', 'pyproject.toml', '.flake8', 'pytest.ini'],
    patterns: {
      'src/**/*.py': 'Source code files',
      'tests/**/*.py': 'Test files',
      '**/*_test.py': 'Test files',
      'test_*.py': 'Test files'
    }
  },
  java: {
    dirs: ['src/main/java', 'src/test/java', 'target', 'build'],
    files: ['pom.xml', 'build.gradle', '.classpath', '.project'],
    patterns: {
      'src/main/java/**/*.java': 'Source code files',
      'src/test/java/**/*.java': 'Test files',
      '**/impl/*.java': 'Implementation classes',
      '**/model/*.java': 'Model classes',
      '**/service/*.java': 'Service classes',
      '**/controller/*.java': 'Controller classes'
    }
  },
  csharp: {
    dirs: ['src', 'tests', 'Properties', 'obj', 'bin'],
    files: ['*.csproj', '*.sln', 'App.config', 'Web.config'],
    patterns: {
      'src/**/*.cs': 'Source code files',
      'tests/**/*.cs': 'Test files',
      '**/Models/*.cs': 'Model classes',
      '**/Controllers/*.cs': 'Controller classes',
      '**/Views/**/*.cshtml': 'View templates'
    }
  },
  ruby: {
    dirs: ['app', 'config', 'db', 'lib', 'test', 'spec'],
    files: ['Gemfile', 'Rakefile', 'config.ru'],
    patterns: {
      'app/**/*.rb': 'Application code',
      'app/models/*.rb': 'Model classes',
      'app/controllers/*.rb': 'Controller classes',
      'app/views/**/*.erb': 'View templates',
      'test/**/*.rb': 'Test files',
      'spec/**/*.rb': 'RSpec test files'
    }
  },
  go: {
    dirs: ['cmd', 'pkg', 'internal', 'api', 'web', 'docs'],
    files: ['go.mod', 'go.sum', 'main.go'],
    patterns: {
      '**/*.go': 'Go source files',
      '**/*_test.go': 'Test files',
      '**/cmd/**/*.go': 'Command line tools',
      '**/pkg/**/*.go': 'Public packages',
      '**/internal/**/*.go': 'Private packages'
    }
  },
  rust: {
    dirs: ['src', 'tests', 'examples', 'benches', 'target'],
    files: ['Cargo.toml', 'Cargo.lock', 'rustfmt.toml'],
    patterns: {
      'src/**/*.rs': 'Source code files',
      'tests/**/*.rs': 'Test files',
      'examples/**/*.rs': 'Example code',
      'benches/**/*.rs': 'Benchmarks'
    }
  },
  react: {
    dirs: ['src/components', 'src/pages', 'src/hooks', 'src/context', 'public'],
    files: ['package.json', 'tsconfig.json', '.eslintrc'],
    patterns: {
      'src/components/**/*.(js|jsx|ts|tsx)': 'React components',
      'src/pages/**/*.(js|jsx|ts|tsx)': 'Page components',
      'src/hooks/**/*.(js|jsx|ts|tsx)': 'Custom hooks',
      'src/context/**/*.(js|jsx|ts|tsx)': 'React context',
      '**/*.test.(js|jsx|ts|tsx)': 'Test files'
    }
  },
  angular: {
    dirs: ['src/app', 'src/assets', 'src/environments'],
    files: ['angular.json', 'tsconfig.json', 'package.json'],
    patterns: {
      'src/app/**/*.component.ts': 'Angular components',
      'src/app/**/*.service.ts': 'Angular services',
      'src/app/**/*.module.ts': 'Angular modules',
      'src/app/**/*.directive.ts': 'Angular directives',
      'src/app/**/*.pipe.ts': 'Angular pipes',
      'src/app/**/*.guard.ts': 'Route guards',
      'src/app/**/*.spec.ts': 'Test files'
    }
  },
  vue: {
    dirs: ['src/components', 'src/views', 'src/store', 'public'],
    files: ['package.json', 'vue.config.js'],
    patterns: {
      'src/components/**/*.vue': 'Vue components',
      'src/views/**/*.vue': 'Vue views/pages',
      'src/store/**/*.js': 'Vuex store modules',
      'src/router/**/*.js': 'Vue router configuration',
      '**/*.spec.js': 'Test files'
    }
  },
  django: {
    dirs: ['app_name', 'templates', 'static', 'media', 'migrations'],
    files: ['manage.py', 'requirements.txt', 'settings.py', 'urls.py', 'wsgi.py', 'asgi.py'],
    patterns: {
      '**/models.py': 'Django models',
      '**/views.py': 'Django views',
      '**/admin.py': 'Django admin configuration',
      '**/forms.py': 'Django forms',
      '**/urls.py': 'URL configuration',
      '**/tests.py': 'Test files',
      '**/migrations/*.py': 'Database migrations'
    }
  },
  flask: {
    dirs: ['app', 'static', 'templates', 'migrations', 'tests'],
    files: ['requirements.txt', 'config.py', '__init__.py', 'run.py'],
    patterns: {
      '**/models.py': 'Database models',
      '**/views.py': 'View functions',
      '**/forms.py': 'WTForms definitions',
      '**/routes.py': 'Route definitions',
      'tests/**/*.py': 'Test files'
    }
  },
  fastapi: {
    dirs: ['app', 'routers', 'models', 'schemas', 'tests'],
    files: ['main.py', 'requirements.txt'],
    patterns: {
      'app/main.py': 'Main FastAPI application',
      'app/dependencies.py': 'Dependencies and middleware',
      '**/models.py': 'Database models',
      '**/schemas.py': 'Pydantic schemas',
      '**/routers/*.py': 'API route definitions',
      'tests/**/*.py': 'Test files'
    }
  },
  spring: {
    dirs: ['src/main/java', 'src/main/resources', 'src/test/java'],
    files: ['pom.xml', 'build.gradle', 'application.properties', 'application.yml'],
    patterns: {
      '**/controller/**/*.java': 'REST controllers',
      '**/service/**/*.java': 'Service classes',
      '**/repository/**/*.java': 'Repository classes',
      '**/model/**/*.java': 'Model/Entity classes',
      '**/config/**/*.java': 'Configuration classes',
      'src/test/**/*.java': 'Test files'
    }
  },
  rails: {
    dirs: ['app', 'config', 'db', 'lib', 'test', 'spec'],
    files: ['Gemfile', 'Rakefile', 'config.ru', 'config/routes.rb'],
    patterns: {
      'app/models/**/*.rb': 'Model classes',
      'app/controllers/**/*.rb': 'Controller classes',
      'app/views/**/*.erb': 'View templates',
      'db/migrate/**/*.rb': 'Database migrations',
      'config/routes.rb': 'Route definitions',
      'test/**/*.rb': 'Test::Unit tests',
      'spec/**/*.rb': 'RSpec tests'
    }
  },
  laravel: {
    dirs: ['app', 'config', 'database', 'resources', 'routes', 'tests'],
    files: ['composer.json', '.env.example', 'artisan', 'phpunit.xml'],
    patterns: {
      'app/Http/Controllers/**/*.php': 'Controllers',
      'app/Models/**/*.php': 'Eloquent models',
      'database/migrations/**/*.php': 'Database migrations',
      'routes/**/*.php': 'Route definitions',
      'resources/views/**/*.blade.php': 'Blade templates',
      'tests/**/*.php': 'Test files'
    }
  }
};

/**
 * Common anti-patterns by language
 */
const ANTI_PATTERNS = {
  javascript: [
    { pattern: 'var ', description: 'Use of var instead of let/const' },
    { pattern: '== null', description: 'Use === null or !== null for null checks' },
    { pattern: 'import * as', description: 'Wildcard imports may increase bundle size' }
  ],
  typescript: [
    { pattern: 'any', description: 'Use of any type should be minimized' },
    { pattern: '!important', description: 'Use of !important in inline styles' },
    { pattern: 'as any', description: 'Type casting to any circumvents type safety' }
  ],
  python: [
    { pattern: 'except:', description: 'Bare except clause should be avoided' },
    { pattern: 'import *', description: 'Wildcard imports pollute namespace' },
    { pattern: 'print(', description: 'Consider using logging instead of print' }
  ],
  java: [
    { pattern: 'catch (Exception', description: 'Catching generic Exception' },
    { pattern: 'public static void main', description: 'Main method in a class that should not be executable' },
    { pattern: 'null instanceof', description: 'null instanceof always returns false' }
  ],
};

/**
 * Analyze project structure
 * 
 * @param {string} projectPath - Path to the project
 * @param {Object} projectType - Project type information from language-detector
 * @returns {Object} - Analysis results
 */
function analyze(projectPath, projectType) {
  try {
    // Normalize path
    const basePath = path.resolve(projectPath);
    
    // Get all files recursively (with deeper depth)
    const files = getFiles(basePath, 6);
    
    // Results object
    const results = {
      status: 'success',
      structure: {
        fileCount: files.length,
        directoryCount: 0,
        byExtension: {},
        topLevelDirectories: [],
        fileTypes: {
          source: 0,
          test: 0,
          config: 0,
          documentation: 0,
          resource: 0,
          other: 0
        }
      },
      patterns: {
        followed: [],
        missing: [],
        antiPatterns: []
      },
      suggestions: []
    };
    
    // Count files by extension
    files.forEach(file => {
      const ext = path.extname(file).toLowerCase();
      results.structure.byExtension[ext] = (results.structure.byExtension[ext] || 0) + 1;
      
      // Detect file types
      if (file.includes('/test/') || file.includes('/tests/') || 
          file.includes('_test.') || file.includes('.test.') || 
          file.includes('.spec.') || file.match(/test_.+\./)) {
        results.structure.fileTypes.test++;
      } else if (ext === '.md' || ext === '.txt' || ext === '.rst' || 
                file.toLowerCase().includes('/docs/') || file.toLowerCase().includes('/documentation/')) {
        results.structure.fileTypes.documentation++;
      } else if (file.includes('.config.') || file.includes('.rc') || file.endsWith('.json') || 
                file.endsWith('.yml') || file.endsWith('.yaml') || file.endsWith('.toml') || 
                file.endsWith('.ini') || file.endsWith('.conf')) {
        results.structure.fileTypes.config++;
      } else if (ext === '.png' || ext === '.jpg' || ext === '.svg' || ext === '.css' || 
                ext === '.scss' || ext === '.less' || ext === '.ttf' || ext === '.woff' || 
                file.includes('/assets/') || file.includes('/static/') || file.includes('/resources/')) {
        results.structure.fileTypes.resource++;
      } else if (ext === '.js' || ext === '.ts' || ext === '.jsx' || ext === '.tsx' ||
                ext === '.py' || ext === '.java' || ext === '.rb' || ext === '.go' || 
                ext === '.rs' || ext === '.php' || ext === '.cs' || ext === '.cpp' || ext === '.c') {
        results.structure.fileTypes.source++;
      } else {
        results.structure.fileTypes.other++;
      }
    });
    
    // Extract top-level directories
    try {
      const topLevelItems = fs.readdirSync(basePath);
      results.structure.topLevelDirectories = topLevelItems
        .filter(item => {
          try {
            return fs.statSync(path.join(basePath, item)).isDirectory() && 
                  !item.startsWith('.') && 
                  item !== 'node_modules' && 
                  item !== 'venv' &&
                  item !== '__pycache__' &&
                  item !== 'dist' &&
                  item !== 'build';
          } catch (err) {
            return false;
          }
        });
        
      // Count total number of directories
      let directoryCount = 0;
      const countDirectories = (dir) => {
        try {
          const items = fs.readdirSync(dir);
          for (const item of items) {
            const itemPath = path.join(dir, item);
            try {
              if (fs.statSync(itemPath).isDirectory()) {
                directoryCount++;
                // Don't recurse into node_modules, venv, etc.
                if (!item.startsWith('.') && 
                    item !== 'node_modules' && 
                    item !== 'venv' &&
                    item !== '__pycache__' &&
                    item !== 'dist' &&
                    item !== 'build') {
                  countDirectories(itemPath);
                }
              }
            } catch (err) {
              // Skip items we can't stat
            }
          }
        } catch (err) {
          // Skip directories we can't read
        }
      };
      
      countDirectories(basePath);
      results.structure.directoryCount = directoryCount;
      
    } catch (err) {
      results.structure.topLevelDirectories = [];
    }
    
    // Check if project follows standard structure for its type
    const languages = projectType.languages.map(lang => lang.name);
    const frameworks = projectType.frameworks ? projectType.frameworks.map(f => f.name) : [];
    
    // Include both language and framework patterns for checking
    const allPatterns = [...languages, ...frameworks]
      .filter(type => PROJECT_STRUCTURES[type])
      .map(type => PROJECT_STRUCTURES[type])
      .filter(Boolean);
      
    if (allPatterns.length === 0) {
      // If we don't have patterns for this exact project type, use generic ones
      if (languages[0]) {
        const genericPatterns = PROJECT_STRUCTURES[languages[0]];
        if (genericPatterns) {
          allPatterns.push(genericPatterns);
        }
      }
    }
    
    // Check for expected directories and files
    if (allPatterns.length > 0) {
      // Flatten expected directories and files from all applicable patterns
      const expectedDirs = new Set();
      const expectedFiles = new Set();
      
      allPatterns.forEach(pattern => {
        if (pattern.dirs) {
          pattern.dirs.forEach(dir => expectedDirs.add(dir));
        }
        if (pattern.files) {
          pattern.files.forEach(file => expectedFiles.add(file));
        }
      });
      
      // Check for expected directories
      Array.from(expectedDirs).forEach(dir => {
        const normalizedDir = dir.replace(/\\/g, '/');
        const segments = normalizedDir.split('/');
        const topLevelDir = segments[0];
        
        if (results.structure.topLevelDirectories.includes(topLevelDir) || 
            files.some(file => file.includes(`/${topLevelDir}/`))) {
          results.patterns.followed.push({
            type: 'directory',
            name: normalizedDir,
            description: `Standard ${normalizedDir} directory exists`
          });
        } else {
          results.patterns.missing.push({
            type: 'directory',
            name: normalizedDir, 
            description: `Standard ${normalizedDir} directory is missing`
          });
        }
      });
      
      // Check for expected files
      Array.from(expectedFiles).forEach(file => {
        if (files.some(f => path.basename(f) === file)) {
          results.patterns.followed.push({
            type: 'file',
            name: file,
            description: `Standard ${file} exists`
          });
        } else {
          results.patterns.missing.push({
            type: 'file',
            name: file,
            description: `Standard ${file} is missing`
          });
        }
      });
      
      // Check for anti-patterns
      for (const lang of languages) {
        const antiPatterns = ANTI_PATTERNS[lang];
        if (antiPatterns) {
          for (const antiPattern of antiPatterns) {
            // Check a subset of files for anti-patterns (for performance)
            const relevantFiles = files
              .filter(file => {
                const ext = path.extname(file).toLowerCase();
                if (lang === 'javascript' && ['.js', '.jsx', '.mjs'].includes(ext)) return true;
                if (lang === 'typescript' && ['.ts', '.tsx'].includes(ext)) return true;
                if (lang === 'python' && ext === '.py') return true;
                if (lang === 'java' && ext === '.java') return true;
                return false;
              })
              .slice(0, 50); // Limit to 50 files for performance
            
            let matchCount = 0;
            
            for (const file of relevantFiles) {
              try {
                const content = fs.readFileSync(file, 'utf8');
                if (content.includes(antiPattern.pattern)) {
                  matchCount++;
                }
              } catch (err) {
                // Skip files that can't be read
              }
            }
            
            if (matchCount > 0) {
              results.patterns.antiPatterns.push({
                pattern: antiPattern.pattern,
                description: antiPattern.description,
                occurrences: matchCount
              });
            }
          }
        }
      }
      
      // Generate suggestions
      if (results.structure.fileTypes.test === 0) {
        results.suggestions.push({
          type: 'critical',
          description: 'No test files detected. Consider adding tests to improve code quality.'
        });
      }
      
      if (results.structure.fileTypes.test < results.structure.fileTypes.source * 0.25) {
        results.suggestions.push({
          type: 'warning',
          description: 'Low test coverage. Consider adding more tests.'
        });
      }
      
      if (results.structure.fileTypes.documentation < 3) {
        results.suggestions.push({
          type: 'info',
          description: 'Limited documentation found. Consider adding README.md, CONTRIBUTING.md, etc.'
        });
      }
      
      if (results.patterns.antiPatterns.length > 0) {
        results.suggestions.push({
          type: 'warning',
          description: `${results.patterns.antiPatterns.length} types of anti-patterns found. Consider refactoring.`
        });
      }
      
      if (results.patterns.missing.length > results.patterns.followed.length) {
        results.suggestions.push({
          type: 'info',
          description: 'Project structure deviates significantly from standard patterns. Consider reorganizing.'
        });
      }
      
      // Get complexity metrics
      results.metrics = {
        fileToDirectoryRatio: results.structure.fileCount / (results.structure.directoryCount || 1),
        testToCodeRatio: results.structure.fileTypes.test / (results.structure.fileTypes.source || 1),
        averageFilesPerDirectory: results.structure.fileCount / (results.structure.directoryCount || 1),
        configurationRatio: results.structure.fileTypes.config / (results.structure.fileCount || 1),
      };
      
      // Add complexity-based suggestions
      if (results.metrics.fileToDirectoryRatio > 20) {
        results.suggestions.push({
          type: 'warning',
          description: 'High file-to-directory ratio. Consider breaking down directories into smaller units.'
        });
      }
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
  PROJECT_STRUCTURES,
  ANTI_PATTERNS
};