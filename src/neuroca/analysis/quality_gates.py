"""
Quality Gates and Validation Framework for Codebase Summarization

This module implements comprehensive quality gates and validation mechanisms
to ensure the integrity and accuracy of the summarization pipeline.
"""

import json
import hashlib
import logging
import re
import ast
import tokenize
import io
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for summarization"""
    missing_references: List[str]
    unresolved_imports: List[str]
    token_ratio_outliers: List[str]
    consistency_issues: List[str]
    completeness_score: float
    accuracy_score: float
    integrity_score: float
    overall_passed: bool
    details: Dict[str, Any]


@dataclass
class ValidationResult:
    """Result of a validation check"""
    name: str
    passed: bool
    score: float
    issues: List[str]
    recommendations: List[str]
    severity: str  # 'low', 'medium', 'high', 'critical'


class QualityGateEngine:
    """Engine for running quality gates and validation checks"""
    
    def __init__(self, workspace_path: str, file_metadata: Dict, component_metadata: Dict):
        self.workspace_path = Path(workspace_path)
        self.file_metadata = file_metadata
        self.component_metadata = component_metadata
        self.validation_results: List[ValidationResult] = []
        
    async def run_all_quality_gates(self) -> QualityMetrics:
        """Run comprehensive quality gate validation"""
        logger.info("Running comprehensive quality gate validation")
        
        # Reference and import validation
        missing_refs = await self.check_missing_references()
        unresolved_imports = await self.check_unresolved_imports()
        
        # Token and content validation
        token_outliers = await self.check_token_ratio_outliers()
        
        # Consistency validation
        consistency_issues = await self.check_consistency()
        
        # Completeness validation
        completeness_score = await self.calculate_completeness_score()
        
        # Accuracy validation
        accuracy_score = await self.calculate_accuracy_score()
        
        # Integrity validation
        integrity_score = await self.calculate_integrity_score()
        
        # Overall assessment
        overall_passed = self._assess_overall_quality(
            missing_refs, unresolved_imports, token_outliers, 
            consistency_issues, completeness_score, accuracy_score, integrity_score
        )
        
        metrics = QualityMetrics(
            missing_references=missing_refs,
            unresolved_imports=unresolved_imports,
            token_ratio_outliers=token_outliers,
            consistency_issues=consistency_issues,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            integrity_score=integrity_score,
            overall_passed=overall_passed,
            details=self._compile_detailed_results()
        )
        
        await self._generate_quality_report(metrics)
        return metrics
    
    async def check_missing_references(self) -> List[str]:
        """Check for missing file references and broken links"""
        logger.info("Checking for missing references")
        
        missing_refs = []
        
        # Check imports and includes
        for file_path, metadata in self.file_metadata.items():
            full_path = self.workspace_path / file_path
            if not full_path.exists():
                continue
                
            try:
                content = self._read_file_safely(full_path)
                if content is None:
                    continue
                    
                # Check Python imports
                if metadata.language == 'python':
                    missing_refs.extend(self._check_python_imports(content, file_path))
                    
                # Check JavaScript/TypeScript imports
                elif metadata.language in ['javascript', 'typescript']:
                    missing_refs.extend(self._check_js_imports(content, file_path))
                    
                # Check relative file references
                missing_refs.extend(self._check_relative_references(content, file_path))
                
            except Exception as e:
                logger.warning(f"Error checking references in {file_path}: {e}")
                
        return list(set(missing_refs))  # Remove duplicates
    
    def _check_python_imports(self, content: str, file_path: str) -> List[str]:
        """Check Python import statements for missing modules"""
        missing = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._is_import_resolvable(alias.name, file_path):
                            missing.append(f"{file_path}: import {alias.name}")
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module and not self._is_import_resolvable(node.module, file_path):
                        missing.append(f"{file_path}: from {node.module} import ...")
                        
        except SyntaxError:
            # File has syntax errors, skip import checking
            pass
        except Exception as e:
            logger.debug(f"Error parsing Python imports in {file_path}: {e}")
            
        return missing
    
    def _check_js_imports(self, content: str, file_path: str) -> List[str]:
        """Check JavaScript/TypeScript import statements"""
        missing = []
        
        # Simple regex-based checking for JS/TS imports
        import_patterns = [
            r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
            r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for module in matches:
                if module.startswith('./') or module.startswith('../'):
                    # Relative import - check if file exists
                    ref_path = self._resolve_relative_path(file_path, module)
                    if not ref_path or not (self.workspace_path / ref_path).exists():
                        missing.append(f"{file_path}: import '{module}'")
                        
        return missing
    
    def _check_relative_references(self, content: str, file_path: str) -> List[str]:
        """Check for relative file references in content"""
        missing = []
        
        # Common patterns for file references
        patterns = [
            r"['\"](\./[^'\"]+)['\"]",  # ./path/to/file
            r"['\"](\.\./[^'\"]+)['\"]",  # ../path/to/file
            r"['\"]([^'\"]*\.(?:py|js|ts|json|yaml|yml|md|txt))['\"]"  # file extensions
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for ref in matches:
                if ref.startswith('./') or ref.startswith('../'):
                    ref_path = self._resolve_relative_path(file_path, ref)
                    if ref_path and not (self.workspace_path / ref_path).exists():
                        missing.append(f"{file_path}: reference '{ref}'")
                        
        return missing
    
    def _is_import_resolvable(self, module_name: str, file_path: str) -> bool:
        """Check if a Python import can be resolved"""
        # Standard library modules (simplified check)
        stdlib_modules = {
            'os', 'sys', 'json', 'logging', 'datetime', 'pathlib', 'typing',
            'collections', 'itertools', 'functools', 'asyncio', 'threading',
            'multiprocessing', 're', 'hashlib', 'base64', 'urllib', 'http'
        }
        
        if module_name.split('.')[0] in stdlib_modules:
            return True
            
        # Check if it's a relative import within the project
        if module_name.startswith('.'):
            return True  # Assume relative imports are valid for now
            
        # Check if it's a known third-party package (would need dependency analysis)
        # For now, assume external packages are available
        if not module_name.startswith(('src.', 'neuroca.')):
            return True
            
        # Check if it's a project module
        potential_paths = [
            module_name.replace('.', '/') + '.py',
            module_name.replace('.', '/') + '/__init__.py'
        ]
        
        for path in potential_paths:
            if (self.workspace_path / path).exists():
                return True
                
        return False
    
    def _resolve_relative_path(self, current_file: str, relative_ref: str) -> Optional[str]:
        """Resolve relative path reference"""
        try:
            current_dir = Path(current_file).parent
            resolved = (current_dir / relative_ref).resolve()
            return str(resolved.relative_to(self.workspace_path.resolve()))
        except:
            return None
    
    async def check_unresolved_imports(self) -> List[str]:
        """Check for unresolved import statements using static analysis"""
        logger.info("Checking for unresolved imports")
        
        unresolved = []
        
        # Build project module map
        project_modules = self._build_project_module_map()
        
        for file_path, metadata in self.file_metadata.items():
            if metadata.language == 'python':
                full_path = self.workspace_path / file_path
                try:
                    content = self._read_file_safely(full_path)
                    if content:
                        unresolved.extend(
                            self._check_python_import_resolution(content, file_path, project_modules)
                        )
                except Exception as e:
                    logger.debug(f"Error checking imports in {file_path}: {e}")
                    
        return unresolved
    
    def _build_project_module_map(self) -> Dict[str, str]:
        """Build map of available project modules"""
        modules = {}
        
        for file_path, metadata in self.file_metadata.items():
            if metadata.language == 'python' and file_path.endswith('.py'):
                # Convert file path to module name
                module_path = file_path.replace('/', '.').replace('\\', '.')
                if module_path.startswith('src.'):
                    module_path = module_path[4:]  # Remove 'src.' prefix
                if module_path.endswith('.__init__.py'):
                    module_path = module_path[:-12]  # Remove '.__init__.py'
                elif module_path.endswith('.py'):
                    module_path = module_path[:-3]  # Remove '.py'
                    
                modules[module_path] = file_path
                
        return modules
    
    def _check_python_import_resolution(self, content: str, file_path: str, project_modules: Dict[str, str]) -> List[str]:
        """Check if Python imports can be resolved"""
        unresolved = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_parts = node.module.split('.')
                        if module_parts[0] in ['neuroca', 'src']:
                            # This is a project import
                            clean_module = '.'.join(module_parts[1:] if module_parts[0] == 'src' else module_parts)
                            if clean_module not in project_modules:
                                unresolved.append(f"{file_path}: from {node.module} import ...")
                                
        except SyntaxError:
            pass  # Skip files with syntax errors
        except Exception as e:
            logger.debug(f"Error resolving imports in {file_path}: {e}")
            
        return unresolved
    
    async def check_token_ratio_outliers(self) -> List[str]:
        """Check for unusual token count ratios and potential issues"""
        logger.info("Checking token ratio outliers")
        
        outliers = []
        
        # Calculate token statistics
        token_stats = []
        for file_path, metadata in self.file_metadata.items():
            if metadata.size_bytes > 0:
                # Estimate tokens (rough approximation)
                estimated_tokens = metadata.size_bytes // 4
                token_per_line = estimated_tokens / max(1, metadata.lines_of_code)
                chars_per_token = metadata.size_bytes / max(1, estimated_tokens)
                
                token_stats.append({
                    'file': file_path,
                    'tokens': estimated_tokens,
                    'token_per_line': token_per_line,
                    'chars_per_token': chars_per_token,
                    'size': metadata.size_bytes,
                    'loc': metadata.lines_of_code
                })
        
        if not token_stats:
            return outliers
            
        # Calculate statistics
        avg_token_per_line = sum(s['token_per_line'] for s in token_stats) / len(token_stats)
        avg_chars_per_token = sum(s['chars_per_token'] for s in token_stats) / len(token_stats)
        
        # Find outliers (more than 3 standard deviations from mean)
        for stats in token_stats:
            issues = []
            
            # Check token per line ratio
            if stats['token_per_line'] > avg_token_per_line * 3:
                issues.append("unusually high token density")
            elif stats['token_per_line'] < avg_token_per_line * 0.1:
                issues.append("unusually low token density")
                
            # Check characters per token ratio
            if stats['chars_per_token'] > avg_chars_per_token * 2:
                issues.append("unusually long tokens (possible minified/generated code)")
            elif stats['chars_per_token'] < avg_chars_per_token * 0.5:
                issues.append("unusually short tokens")
                
            # Check for very large files
            if stats['size'] > 1024 * 1024:  # 1MB
                issues.append("very large file size")
                
            if issues:
                outliers.append(f"{stats['file']}: {', '.join(issues)}")
                
        return outliers
    
    async def check_consistency(self) -> List[str]:
        """Check for consistency issues in metadata and summaries"""
        logger.info("Checking consistency issues")
        
        issues = []
        
        # Check for inconsistent file extensions vs detected language
        language_extensions = {
            'python': ['.py', '.pyw'],
            'javascript': ['.js', '.mjs'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cxx', '.cc'],
            'c': ['.c'],
            'json': ['.json'],
            'yaml': ['.yml', '.yaml'],
            'markdown': ['.md', '.markdown']
        }
        
        for file_path, metadata in self.file_metadata.items():
            file_ext = Path(file_path).suffix.lower()
            expected_exts = language_extensions.get(metadata.language, [])
            
            if expected_exts and file_ext not in expected_exts:
                issues.append(f"{file_path}: language '{metadata.language}' inconsistent with extension '{file_ext}'")
        
        # Check for files with zero LOC but non-zero size
        for file_path, metadata in self.file_metadata.items():
            if metadata.size_bytes > 100 and metadata.lines_of_code == 0:
                issues.append(f"{file_path}: non-zero size but zero lines of code")
        
        # Check for unrealistic complexity scores
        for file_path, metadata in self.file_metadata.items():
            if metadata.complexity_score > 20:
                issues.append(f"{file_path}: unrealistically high complexity score ({metadata.complexity_score})")
        
        return issues
    
    async def calculate_completeness_score(self) -> float:
        """Calculate completeness score based on metadata coverage"""
        logger.info("Calculating completeness score")
        
        if not self.file_metadata:
            return 0.0
            
        total_files = len(self.file_metadata)
        complete_files = 0
        
        for metadata in self.file_metadata.values():
            # Check if metadata is reasonably complete
            completeness_factors = [
                metadata.language != 'unknown',
                metadata.lines_of_code >= 0,
                metadata.size_bytes > 0,
                metadata.last_modified != '',
                metadata.author != 'unknown',
                metadata.encoding != 'unknown'
            ]
            
            if sum(completeness_factors) >= 4:  # At least 4 out of 6 factors
                complete_files += 1
                
        return complete_files / total_files
    
    async def calculate_accuracy_score(self) -> float:
        """Calculate accuracy score based on validation checks"""
        logger.info("Calculating accuracy score")
        
        # Simple accuracy calculation based on validation results
        accuracy_factors = []
        
        # File count accuracy
        expected_files = len(list(self.workspace_path.rglob("*")))
        actual_files = len(self.file_metadata)
        file_accuracy = min(actual_files / max(1, expected_files), 1.0)
        accuracy_factors.append(file_accuracy)
        
        # Language detection accuracy (spot check)
        correct_detections = 0
        total_checks = 0
        
        for file_path, metadata in list(self.file_metadata.items())[:10]:  # Sample 10 files
            expected_lang = self._detect_language_by_content(self.workspace_path / file_path)
            if expected_lang == metadata.language:
                correct_detections += 1
            total_checks += 1
            
        if total_checks > 0:
            lang_accuracy = correct_detections / total_checks
            accuracy_factors.append(lang_accuracy)
        
        return sum(accuracy_factors) / len(accuracy_factors) if accuracy_factors else 0.0
    
    async def calculate_integrity_score(self) -> float:
        """Calculate integrity score based on data consistency"""
        logger.info("Calculating integrity score")
        
        integrity_factors = []
        
        # Check for data integrity issues
        total_files = len(self.file_metadata)
        if total_files == 0:
            return 0.0
            
        # Factor 1: Files with consistent metadata
        consistent_files = 0
        for file_path, metadata in self.file_metadata.items():
            full_path = self.workspace_path / file_path
            if full_path.exists():
                actual_size = full_path.stat().st_size
                if abs(actual_size - metadata.size_bytes) < 100:  # Allow small variance
                    consistent_files += 1
                    
        integrity_factors.append(consistent_files / total_files)
        
        # Factor 2: No duplicate entries
        unique_paths = len(set(self.file_metadata.keys()))
        integrity_factors.append(unique_paths / total_files)
        
        # Factor 3: Valid file paths
        valid_paths = 0
        for file_path in self.file_metadata.keys():
            if (self.workspace_path / file_path).exists():
                valid_paths += 1
                
        integrity_factors.append(valid_paths / total_files)
        
        return sum(integrity_factors) / len(integrity_factors)
    
    def _assess_overall_quality(self, missing_refs: List[str], unresolved_imports: List[str], 
                               token_outliers: List[str], consistency_issues: List[str],
                               completeness: float, accuracy: float, integrity: float) -> bool:
        """Assess overall quality based on all metrics"""
        
        # Quality gate thresholds
        thresholds = {
            'max_missing_refs': 10,
            'max_unresolved_imports': 5,
            'max_token_outliers': 20,
            'max_consistency_issues': 15,
            'min_completeness': 0.8,
            'min_accuracy': 0.7,
            'min_integrity': 0.9
        }
        
        # Check each threshold
        checks = [
            len(missing_refs) <= thresholds['max_missing_refs'],
            len(unresolved_imports) <= thresholds['max_unresolved_imports'],
            len(token_outliers) <= thresholds['max_token_outliers'],
            len(consistency_issues) <= thresholds['max_consistency_issues'],
            completeness >= thresholds['min_completeness'],
            accuracy >= thresholds['min_accuracy'],
            integrity >= thresholds['min_integrity']
        ]
        
        # Require at least 5 out of 7 checks to pass
        return sum(checks) >= 5
    
    def _compile_detailed_results(self) -> Dict[str, Any]:
        """Compile detailed validation results"""
        return {
            'validation_results': [
                {
                    'name': result.name,
                    'passed': result.passed,
                    'score': result.score,
                    'issues_count': len(result.issues),
                    'severity': result.severity
                }
                for result in self.validation_results
            ],
            'file_count': len(self.file_metadata),
            'component_count': len(self.component_metadata),
            'timestamp': logger.handlers[0].format(logger.makeRecord(
                logger.name, logging.INFO, __file__, 0, "timestamp", (), None
            )) if logger.handlers else "unknown"
        }
    
    async def _generate_quality_report(self, metrics: QualityMetrics):
        """Generate comprehensive quality report"""
        report_path = self.workspace_path / "analysis_artifacts" / "summarization" / "quality_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        report_content = f"""# Quality Gate Report

## Overall Assessment
**Status**: {'✅ PASSED' if metrics.overall_passed else '❌ FAILED'}

## Quality Scores
- **Completeness**: {metrics.completeness_score:.2%}
- **Accuracy**: {metrics.accuracy_score:.2%}
- **Integrity**: {metrics.integrity_score:.2%}

## Issues Found

### Missing References ({len(metrics.missing_references)})
{self._format_issue_list(metrics.missing_references)}

### Unresolved Imports ({len(metrics.unresolved_imports)})
{self._format_issue_list(metrics.unresolved_imports)}

### Token Ratio Outliers ({len(metrics.token_ratio_outliers)})
{self._format_issue_list(metrics.token_ratio_outliers)}

### Consistency Issues ({len(metrics.consistency_issues)})
{self._format_issue_list(metrics.consistency_issues)}

## Recommendations
{self._generate_recommendations(metrics)}

## Detailed Metrics
```json
{json.dumps(metrics.details, indent=2)}
```
"""
        
        with open(report_path, 'w') as f:
            f.write(report_content)
            
        logger.info(f"Quality report generated: {report_path}")
    
    def _format_issue_list(self, issues: List[str], max_items: int = 20) -> str:
        """Format list of issues for report"""
        if not issues:
            return "None found."
            
        formatted = []
        for i, issue in enumerate(issues[:max_items], 1):
            formatted.append(f"{i}. {issue}")
            
        if len(issues) > max_items:
            formatted.append(f"... and {len(issues) - max_items} more")
            
        return '\n'.join(formatted)
    
    def _generate_recommendations(self, metrics: QualityMetrics) -> str:
        """Generate recommendations based on quality metrics"""
        recommendations = []
        
        if len(metrics.missing_references) > 5:
            recommendations.append("- Review and fix missing file references")
            
        if len(metrics.unresolved_imports) > 3:
            recommendations.append("- Resolve import issues or update dependency configuration")
            
        if metrics.completeness_score < 0.8:
            recommendations.append("- Improve metadata collection for better coverage")
            
        if metrics.accuracy_score < 0.7:
            recommendations.append("- Review language detection and file analysis accuracy")
            
        if metrics.integrity_score < 0.9:
            recommendations.append("- Check for data consistency issues in metadata")
            
        if not recommendations:
            recommendations.append("- All quality metrics are within acceptable ranges")
            
        return '\n'.join(recommendations)
    
    def _read_file_safely(self, file_path: Path) -> Optional[str]:
        """Safely read file content with encoding detection"""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try latin-1 as fallback
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except:
                # Binary file or unreadable
                return None
        except Exception:
            return None
    
    def _detect_language_by_content(self, file_path: Path) -> str:
        """Detect language by examining file content"""
        if not file_path.exists():
            return 'unknown'
            
        # First try by extension
        ext_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c'
        }
        
        ext_lang = ext_map.get(file_path.suffix.lower())
        if ext_lang:
            return ext_lang
            
        # Try content-based detection
        content = self._read_file_safely(file_path)
        if not content:
            return 'unknown'
            
        # Simple heuristics
        if 'def ' in content and 'import ' in content:
            return 'python'
        elif 'function ' in content and ('var ' in content or 'let ' in content):
            return 'javascript'
        elif 'public class ' in content:
            return 'java'
            
        return 'unknown'
