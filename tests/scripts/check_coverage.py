#!/usr/bin/env python3
"""
Test Coverage Verification Script

This script runs the test suite with coverage tracking and verifies that coverage meets 
specified targets for different parts of the codebase.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple


# Coverage targets (percentage)
TARGETS = {
    "overall": 90.0,
    "modules": {
        "neuroca/memory/backends": 95.0,
        "neuroca/memory/tiers": 90.0,
        "neuroca/memory/manager": 95.0,
        "neuroca/memory/annealing": 85.0,
        "neuroca/memory/models": 98.0,
        "neuroca/memory/interfaces": 100.0,
        "neuroca/memory/config": 95.0
    }
}


def run_coverage() -> bool:
    """
    Run the test suite with coverage and generate reports.
    
    Returns:
        True if coverage run successful, False otherwise
    """
    print("Running tests with coverage tracking...")
    
    # Ensure coverage reports directory exists
    os.makedirs("reports/coverage", exist_ok=True)
    
    # Run pytest with coverage
    cmd = [
        "pytest",
        "tests/unit/memory",
        "tests/integration/memory",
        "--cov=src/neuroca/memory",
        "--cov-report=term",
        "--cov-report=html:reports/coverage/html",
        "--cov-report=json:reports/coverage/coverage.json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error running tests with coverage:")
        print(result.stderr)
        return False
    
    print(result.stdout)
    return True


def load_coverage_data() -> Dict[str, Any]:
    """
    Load coverage data from the JSON report.
    
    Returns:
        Dictionary with coverage data
    
    Raises:
        FileNotFoundError: If the coverage report doesn't exist
    """
    report_path = Path("reports/coverage/coverage.json")
    
    if not report_path.exists():
        raise FileNotFoundError(f"Coverage report not found at {report_path}")
    
    with open(report_path, 'r') as f:
        return json.load(f)


def calculate_module_coverage(coverage_data: Dict[str, Any], module_path: str) -> Tuple[float, List[str]]:
    """
    Calculate coverage percentage for a specific module.
    
    Args:
        coverage_data: Coverage data dictionary
        module_path: Module path to filter for
        
    Returns:
        Tuple of (coverage_percentage, uncovered_files)
    """
    files = []
    total_statements = 0
    total_missing = 0
    uncovered_files = []
    
    for file_path, data in coverage_data['files'].items():
        if module_path in file_path:
            files.append(file_path)
            statements = len(data.get('executed_lines', []))
            missing = len(data.get('missing_lines', []))
            
            total_statements += statements + missing
            total_missing += missing
            
            # Track files with <80% coverage
            if statements > 0:
                file_coverage = 100 * statements / (statements + missing)
                if file_coverage < 80:
                    uncovered_files.append((file_path, file_coverage))
    
    if total_statements == 0:
        return 0.0, []
    
    coverage_pct = 100 * (total_statements - total_missing) / total_statements
    
    # Sort uncovered files by coverage, lowest first
    uncovered_files.sort(key=lambda x: x[1])
    
    return coverage_pct, [f"{file} ({cov:.1f}%)" for file, cov in uncovered_files]


def verify_coverage(coverage_data: Dict[str, Any]) -> bool:
    """
    Verify coverage meets targets and print report.
    
    Args:
        coverage_data: Coverage data dictionary
        
    Returns:
        True if all targets met, False otherwise
    """
    print("\n=== Coverage Report ===\n")
    
    total_statements = sum(len(data.get('executed_lines', [])) + len(data.get('missing_lines', []))
                           for data in coverage_data['files'].values())
    total_missing = sum(len(data.get('missing_lines', []))
                       for data in coverage_data['files'].values())
    
    overall_coverage = 100 * (total_statements - total_missing) / total_statements if total_statements > 0 else 0
    
    # Check overall coverage
    overall_target_met = overall_coverage >= TARGETS['overall']
    print(f"Overall Coverage: {overall_coverage:.2f}% (Target: {TARGETS['overall']}%)")
    print(f"{'✅' if overall_target_met else '❌'} Target {'met' if overall_target_met else 'not met'}")
    print()
    
    # Check module coverage
    all_targets_met = overall_target_met
    
    print("Module Coverage:")
    
    for module, target in TARGETS['modules'].items():
        coverage_pct, uncovered_files = calculate_module_coverage(coverage_data, module)
        target_met = coverage_pct >= target
        
        if not target_met:
            all_targets_met = False
        
        status = '✅' if target_met else '❌'
        print(f"{status} {module}: {coverage_pct:.2f}% (Target: {target}%)")
        
        if uncovered_files:
            print("   Files with <80% coverage:")
            for file in uncovered_files[:5]:  # Show only top 5 worst
                print(f"   - {file}")
            
            if len(uncovered_files) > 5:
                print(f"   - ... and {len(uncovered_files) - 5} more")
    
    return all_targets_met


def main() -> int:
    """
    Main function to run coverage check.
    
    Returns:
        Exit code (0 if successful and all targets met, 1 otherwise)
    """
    if not run_coverage():
        print("Failed to run tests with coverage")
        return 1
    
    try:
        coverage_data = load_coverage_data()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    
    all_targets_met = verify_coverage(coverage_data)
    
    if all_targets_met:
        print("\nAll coverage targets met! 🎉")
        return 0
    else:
        print("\nSome coverage targets not met. Please add more tests. ⚠️")
        return 1


if __name__ == "__main__":
    sys.exit(main())
