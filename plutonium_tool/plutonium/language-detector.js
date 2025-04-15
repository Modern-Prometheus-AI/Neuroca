/**
 * Language Detector Module for Plutonium
 * 
 * This module detects programming languages, frameworks, and package managers
 * used in a project to enable language-agnostic analysis.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Language detection signatures
const LANGUAGE_SIGNATURES = {
  javascript: {
    extensions: ['.js', '.jsx', '.mjs', '.cjs'],
    filePatterns: ['package.json', '.eslintrc', 'webpack.config.js', 'rollup.config.js'],
    packageManagers: ['npm', 'yarn', 'pnpm']
  },
  typescript: {
    extensions: ['.ts', '.tsx', '.d.ts'],
    filePatterns: ['tsconfig.json', 'tslint.json'],
    packageManagers: ['npm', 'yarn', 'pnpm']
  },
  python: {
    extensions: ['.py', '.pyw', '.pyx', '.pyi'],
    filePatterns: ['setup.py', 'requirements.txt', 'pyproject.toml', 'Pipfile'],
    packageManagers: ['pip', 'poetry', 'conda', 'pipenv']
  },
  java: {
    extensions: ['.java', '.class', '.jar', '.war'],
    filePatterns: ['pom.xml', 'build.gradle', 'settings.gradle', '.classpath'],
    packageManagers: ['maven', 'gradle']
  },
  csharp: {
    extensions: ['.cs', '.csproj', '.sln'],
    filePatterns: ['App.config', 'Web.config', 'packages.config', '.csproj', '.sln'],
    packageManagers: ['nuget']
  },
  ruby: {
    extensions: ['.rb', '.erb', '.gemspec'],
    filePatterns: ['Gemfile', 'Rakefile', '.ruby-version'],
    packageManagers: ['gem', 'bundler']
  },
  php: {
    extensions: ['.php', '.phtml', '.php5', '.php7'],
    filePatterns: ['composer.json', '.htaccess', 'artisan'],
    packageManagers: ['composer']
  },
  go: {
    extensions: ['.go'],
    filePatterns: ['go.mod', 'go.sum', 'Gopkg.toml', 'Gopkg.lock'],
    packageManagers: ['go modules']
  },
  rust: {
    extensions: ['.rs'],
    filePatterns: ['Cargo.toml', 'Cargo.lock', 'rustfmt.toml'],
    packageManagers: ['cargo']
  },
  kotlin: {
    extensions: ['.kt', '.kts', '.ktm'],
    filePatterns: ['settings.gradle.kts', 'build.gradle.kts'],
    packageManagers: ['gradle', 'maven']
  },
  swift: {
    extensions: ['.swift'],
    filePatterns: ['Package.swift', '.xcodeproj', '.xcworkspace'],
    packageManagers: ['swift package manager', 'cocoapods', 'carthage']
  },
  cpp: {
    extensions: ['.cpp', '.cc', '.cxx', '.hpp', '.hh', '.h', '.c'],
    filePatterns: ['CMakeLists.txt', '.vcxproj', 'Makefile', 'conanfile.txt'],
    packageManagers: ['conan', 'vcpkg', 'cmake']
  }
};

// Framework detection signatures
const FRAMEWORK_SIGNATURES = {
  react: {
    filePatterns: ['react', 'jsx', 'react-dom'],
    fileContent: {
      'package.json': ['react', 'react-dom'],
      'any_js': ['import React', 'from \'react\'', 'React.Component']
    }
  },
  angular: {
    filePatterns: ['angular.json', '.angular-cli.json'],
    fileContent: {
      'package.json': ['@angular/core'],
      'any_ts': ['@Component', '@NgModule', 'import { Component }']
    }
  },
  vue: {
    filePatterns: ['vue.config.js'],
    fileContent: {
      'package.json': ['vue'],
      'any_js': ['import Vue', 'from \'vue\'', 'new Vue']
    }
  },
  django: {
    filePatterns: ['manage.py', 'wsgi.py'],
    fileContent: {
      'manage.py': ['django', 'DJANGO_SETTINGS_MODULE'],
      'any_py': ['from django', 'django.db', '@admin.register']
    }
  },
  flask: {
    fileContent: {
      'requirements.txt': ['flask'],
      'any_py': ['from flask import', 'Flask(', 'flask.']
    }
  },
  fastapi: {
    fileContent: {
      'requirements.txt': ['fastapi'],
      'any_py': ['from fastapi import', 'FastAPI(']
    }
  },
  spring: {
    filePatterns: ['application.properties', 'application.yml', 'spring.factories'],
    fileContent: {
      'pom.xml': ['<artifactId>spring-boot', '<artifactId>spring-core'],
      'any_java': ['@SpringBootApplication', '@Autowired', '@RestController']
    }
  },
  rails: {
    filePatterns: ['Gemfile', 'config/routes.rb', 'app/controllers', 'app/models'],
    fileContent: {
      'Gemfile': ['rails'],
      'any_rb': ['Rails.application', 'ActiveRecord::Base']
    }
  },
  laravel: {
    filePatterns: ['artisan', 'composer.json'],
    fileContent: {
      'composer.json': ['laravel/framework'],
      'any_php': ['Illuminate\\', 'namespace App;']
    }
  },
  express: {
    fileContent: {
      'package.json': ['express'],
      'any_js': ['require(\'express\')', 'import express from']
    }
  },
  nextjs: {
    filePatterns: ['next.config.js'],
    fileContent: {
      'package.json': ['next'],
      'any_js': ['import { NextPage }', 'from \'next\'']
    }
  }
};

/**
 * Detect language by analyzing files in a directory
 * 
 * @param {string} projectPath - Path to the project directory
 * @returns {Object} - Detected project information
 */
function detectProjectType(projectPath) {
  // Normalize path
  const basePath = path.resolve(projectPath);
  
  // Ensure path exists
  if (!fs.existsSync(basePath)) {
    throw new Error(`Path does not exist: ${basePath}`);
  }
  
  // Get all files from the project (limit depth for performance)
  const files = getFiles(basePath, 3);
  
  // Count file extensions
  const extensionCount = {};
  const fileNameCount = {};
  
  // Track language scores
  const languageScores = {};
  const frameworkScores = {};
  
  // Initialize language scores
  Object.keys(LANGUAGE_SIGNATURES).forEach(lang => {
    languageScores[lang] = 0;
  });
  
  // Initialize framework scores
  Object.keys(FRAMEWORK_SIGNATURES).forEach(framework => {
    frameworkScores[framework] = 0;
  });
  
  // Count file extensions and special files
  files.forEach(file => {
    const ext = path.extname(file).toLowerCase();
    const fileName = path.basename(file).toLowerCase();
    
    // Count extension
    extensionCount[ext] = (extensionCount[ext] || 0) + 1;
    
    // Count filename
    fileNameCount[fileName] = (fileNameCount[fileName] || 0) + 1;
    
    // Check language signatures
    Object.keys(LANGUAGE_SIGNATURES).forEach(lang => {
      const signature = LANGUAGE_SIGNATURES[lang];
      
      // Check extensions
      if (signature.extensions.includes(ext)) {
        languageScores[lang] += 10;
      }
      
      // Check file patterns
      if (signature.filePatterns.some(pattern => 
          fileName === pattern || file.toLowerCase().includes(pattern.toLowerCase()))) {
        languageScores[lang] += 50;
      }
    });
    
    // Check framework signatures
    Object.keys(FRAMEWORK_SIGNATURES).forEach(framework => {
      const signature = FRAMEWORK_SIGNATURES[framework];
      
      // Check file patterns
      if (signature.filePatterns && signature.filePatterns.some(pattern => 
          fileName === pattern || file.toLowerCase().includes(pattern.toLowerCase()))) {
        frameworkScores[framework] += 30;
      }
      
      // Check file content
      if (signature.fileContent) {
        Object.keys(signature.fileContent).forEach(contentFile => {
          if (contentFile === 'any_js' && ['.js', '.jsx', '.mjs'].includes(ext) ||
              contentFile === 'any_py' && ext === '.py' || 
              contentFile === 'any_java' && ext === '.java' ||
              contentFile === 'any_rb' && ext === '.rb' ||
              contentFile === 'any_php' && ext === '.php' ||
              contentFile === 'any_ts' && ['.ts', '.tsx'].includes(ext) ||
              path.basename(file).toLowerCase() === contentFile.toLowerCase()) {
            
            try {
              const content = fs.readFileSync(file, 'utf8');
              const patterns = signature.fileContent[contentFile];
              
              patterns.forEach(pattern => {
                if (content.includes(pattern)) {
                  frameworkScores[framework] += 20;
                }
              });
            } catch (err) {
              // Skip files that can't be read
            }
          }
        });
      }
    });
  });
  
  // Sort languages by score
  const detectedLanguages = Object.keys(languageScores)
    .filter(lang => languageScores[lang] > 0)
    .sort((a, b) => languageScores[b] - languageScores[a])
    .map(lang => ({
      name: lang,
      score: languageScores[lang],
      confidence: Math.min(100, Math.round(languageScores[lang] / 2))
    }));
  
  // Sort frameworks by score
  const detectedFrameworks = Object.keys(frameworkScores)
    .filter(framework => frameworkScores[framework] > 20) // Threshold for framework detection
    .sort((a, b) => frameworkScores[b] - frameworkScores[a])
    .map(framework => ({
      name: framework,
      score: frameworkScores[framework],
      confidence: Math.min(100, Math.round(frameworkScores[framework] / 1.5))
    }));
  
  // Determine project type
  let projectType = "unknown";
  let packageManagers = [];
  
  if (detectedLanguages.length > 0) {
    const primaryLanguage = detectedLanguages[0].name;
    
    // Try to detect package managers
    if (LANGUAGE_SIGNATURES[primaryLanguage].packageManagers) {
      packageManagers = detectPackageManagers(basePath, LANGUAGE_SIGNATURES[primaryLanguage].packageManagers);
    }
    
    // Set project type
    if (detectedFrameworks.length > 0) {
      projectType = `${detectedFrameworks[0].name} (${primaryLanguage})`;
    } else {
      projectType = primaryLanguage;
    }
  }
  
  // Special case for monorepos and hybrid projects
  if (detectedLanguages.length > 1 && detectedLanguages[1].confidence > 50) {
    projectType = "hybrid";
  }
  
  // Special case for monorepos
  if (fs.existsSync(path.join(basePath, 'lerna.json')) || 
      fs.existsSync(path.join(basePath, 'pnpm-workspace.yaml')) ||
      (fs.existsSync(path.join(basePath, 'package.json')) && 
       JSON.parse(fs.readFileSync(path.join(basePath, 'package.json'), 'utf8')).workspaces)) {
    projectType = "monorepo";
  }
  
  return {
    type: projectType,
    languages: detectedLanguages,
    frameworks: detectedFrameworks,
    packageManagers: packageManagers.map(pm => ({ name: pm })),
    files: {
      byExtension: extensionCount,
      byName: fileNameCount
    }
  };
}

/**
 * Get all files from a directory recursively
 * 
 * @param {string} dir - Directory to scan
 * @param {number} depth - Maximum depth to scan
 * @param {string[]} [results=[]] - Accumulated results
 * @returns {string[]} - List of file paths
 */
function getFiles(dir, depth, results = []) {
  if (depth <= 0) return results;
  
  try {
    // Skip certain directories to avoid performance issues
    if (path.basename(dir) === 'node_modules' || 
        path.basename(dir) === '.git' ||
        path.basename(dir) === 'venv' ||
        path.basename(dir) === '__pycache__' ||
        path.basename(dir) === '.idea' ||
        path.basename(dir) === 'dist' ||
        path.basename(dir) === 'build') {
      return results;
    }
    
    const files = fs.readdirSync(dir);
    
    files.forEach(file => {
      file = path.join(dir, file);
      const stat = fs.statSync(file);
      
      if (stat && stat.isDirectory()) {
        results = getFiles(file, depth - 1, results);
      } else {
        results.push(file);
      }
    });
    
    return results;
  } catch (err) {
    return results;
  }
}

/**
 * Detect package managers used in the project
 * 
 * @param {string} basePath - Project base path
 * @param {string[]} possiblePackageManagers - Possible package managers based on detected language
 * @returns {string[]} - Detected package managers
 */
function detectPackageManagers(basePath, possiblePackageManagers) {
  const detected = [];
  
  possiblePackageManagers.forEach(pm => {
    switch (pm) {
      case 'npm':
        if (fs.existsSync(path.join(basePath, 'package-lock.json'))) {
          detected.push('npm');
        }
        break;
      case 'yarn':
        if (fs.existsSync(path.join(basePath, 'yarn.lock'))) {
          detected.push('yarn');
        }
        break;
      case 'pnpm':
        if (fs.existsSync(path.join(basePath, 'pnpm-lock.yaml'))) {
          detected.push('pnpm');
        }
        break;
      case 'pip':
        if (fs.existsSync(path.join(basePath, 'requirements.txt')) ||
            fs.existsSync(path.join(basePath, 'setup.py'))) {
          detected.push('pip');
        }
        break;
      case 'poetry':
        if (fs.existsSync(path.join(basePath, 'poetry.lock')) ||
            fs.existsSync(path.join(basePath, 'pyproject.toml'))) {
          detected.push('poetry');
        }
        break;
      case 'pipenv':
        if (fs.existsSync(path.join(basePath, 'Pipfile')) ||
            fs.existsSync(path.join(basePath, 'Pipfile.lock'))) {
          detected.push('pipenv');
        }
        break;
      case 'conda':
        if (fs.existsSync(path.join(basePath, 'environment.yml'))) {
          detected.push('conda');
        }
        break;
      case 'maven':
        if (fs.existsSync(path.join(basePath, 'pom.xml'))) {
          detected.push('maven');
        }
        break;
      case 'gradle':
        if (fs.existsSync(path.join(basePath, 'build.gradle')) ||
            fs.existsSync(path.join(basePath, 'build.gradle.kts'))) {
          detected.push('gradle');
        }
        break;
      case 'cargo':
        if (fs.existsSync(path.join(basePath, 'Cargo.toml'))) {
          detected.push('cargo');
        }
        break;
      case 'go modules':
        if (fs.existsSync(path.join(basePath, 'go.mod'))) {
          detected.push('go modules');
        }
        break;
      case 'composer':
        if (fs.existsSync(path.join(basePath, 'composer.json')) ||
            fs.existsSync(path.join(basePath, 'composer.lock'))) {
          detected.push('composer');
        }
        break;
      case 'nuget':
        if (fs.existsSync(path.join(basePath, 'packages.config')) ||
            fs.existsSync(path.join(basePath, '.nuget'))) {
          detected.push('nuget');
        }
        break;
      case 'bundler':
        if (fs.existsSync(path.join(basePath, 'Gemfile')) ||
            fs.existsSync(path.join(basePath, 'Gemfile.lock'))) {
          detected.push('bundler');
        }
        break;
    }
  });
  
  return detected;
}

module.exports = {
  detectProjectType,
  getFiles,
  detectPackageManagers,
  LANGUAGE_SIGNATURES,
  FRAMEWORK_SIGNATURES
};