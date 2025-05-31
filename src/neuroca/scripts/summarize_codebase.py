"""
Command Line Interface for Automated Codebase Summarization Engine

This script provides a user-friendly CLI for executing the 11-step
codebase analysis and summarization pipeline.
"""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from ..analysis.summarization_engine import (
    CodebaseSummarizationEngine, 
    ScopeConfig,
    create_summarization_engine
)
from ..utils.logging import setup_logging


def setup_cli_logging(level: str = "INFO"):
    """Setup logging for CLI operations"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('summarization.log')
        ]
    )


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Automated Codebase Summarization Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic summarization of current directory
  python -m neuroca.scripts.summarize_codebase

  # Summarize specific workspace with custom config
  python -m neuroca.scripts.summarize_codebase --workspace /path/to/code --config config.json

  # Quick analysis with higher context window
  python -m neuroca.scripts.summarize_codebase --context-window 200000 --quick

  # Full pipeline with custom repositories
  python -m neuroca.scripts.summarize_codebase --repos main dev feature/new --branches main dev
        """
    )
    
    # Basic options
    parser.add_argument(
        '--workspace', '-w',
        type=str,
        default='.',
        help='Path to the workspace/repository to analyze (default: current directory)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to JSON configuration file with ScopeConfig parameters'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory for analysis artifacts (default: workspace/analysis_artifacts)'
    )
    
    # Scope configuration
    parser.add_argument(
        '--repos',
        nargs='*',
        default=['main'],
        help='List of repositories to analyze (default: main)'
    )
    
    parser.add_argument(
        '--branches',
        nargs='*',
        default=['main'],
        help='List of branches to analyze (default: main)'
    )
    
    parser.add_argument(
        '--exclude-patterns',
        nargs='*',
        help='Additional file patterns to exclude'
    )
    
    # LLM target configuration
    parser.add_argument(
        '--context-window',
        type=int,
        default=128000,
        help='Target LLM context window size (default: 128000)'
    )
    
    parser.add_argument(
        '--input-limit',
        type=int,
        help='Input limit for target LLM (default: 80% of context window)'
    )
    
    # Pipeline options
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Skip dynamic analysis for faster execution'
    )
    
    parser.add_argument(
        '--no-encryption',
        action='store_true',
        help='Skip encryption of transfer bundle (for testing only)'
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip test execution during dynamic analysis'
    )
    
    parser.add_argument(
        '--steps',
        nargs='*',
        choices=[
            'scope', 'environment', 'static', 'dynamic', 'metadata',
            'chunking', 'quality', 'transfer', 'validation', 'automation', 'docs'
        ],
        help='Run only specific pipeline steps (default: all steps)'
    )
    
    # Logging and debugging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
    
    # Quality gates
    parser.add_argument(
        '--quality-threshold',
        type=float,
        default=0.8,
        help='Quality gate threshold (0.0-1.0, default: 0.8)'
    )
    
    parser.add_argument(
        '--force-quality',
        action='store_true',
        help='Proceed even if quality gates fail'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else args.log_level
    setup_cli_logging(log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate workspace
        workspace_path = Path(args.workspace).resolve()
        if not workspace_path.exists():
            logger.error(f"Workspace path does not exist: {workspace_path}")
            sys.exit(1)
            
        logger.info(f"Starting codebase summarization for: {workspace_path}")
        
        # Load or create configuration
        if args.config:
            config = load_config_file(args.config)
        else:
            config = create_config_from_args(args)
            
        if args.dry_run:
            print_dry_run_info(workspace_path, config, args)
            return
            
        # Create summarization engine
        engine = CodebaseSummarizationEngine(config, str(workspace_path))
        
        # Execute pipeline
        if args.steps:
            bundle = await execute_selected_steps(engine, args.steps, args)
        else:
            bundle = await engine.execute_full_pipeline()
            
        # Validate quality gates
        if not bundle.quality_metrics.get('overall_passed', False) and not args.force_quality:
            logger.error("Quality gates failed. Use --force-quality to proceed anyway.")
            sys.exit(1)
            
        # Generate summary report
        generate_summary_report(engine, bundle, args)
        
        logger.info("Codebase summarization completed successfully!")
        logger.info(f"Results available in: {engine.output_dir}")
        
    except Exception as e:
        logger.error(f"Summarization failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def load_config_file(config_path: str) -> ScopeConfig:
    """Load configuration from JSON file"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_file, 'r') as f:
        config_data = json.load(f)
        
    return ScopeConfig(**config_data)


def create_config_from_args(args) -> ScopeConfig:
    """Create ScopeConfig from command line arguments"""
    
    exclude_patterns = None
    if args.exclude_patterns:
        exclude_patterns = args.exclude_patterns
        
    input_limit = args.input_limit
    if input_limit is None:
        input_limit = int(args.context_window * 0.8)
        
    return ScopeConfig(
        repos=args.repos,
        branches=args.branches,
        exclude_patterns=exclude_patterns,
        target_llm_profile={
            "context_window": args.context_window,
            "input_limits": input_limit,
            "accepted_formats": ["json", "markdown", "yaml"],
            "rate_limits": {"requests_per_minute": 60}
        }
    )


def print_dry_run_info(workspace_path: Path, config: ScopeConfig, args):
    """Print what would be executed in dry run mode"""
    print("=== DRY RUN MODE ===")
    print(f"Workspace: {workspace_path}")
    print(f"Repositories: {config.repos}")
    print(f"Branches: {config.branches}")
    print(f"Context Window: {config.target_llm_profile['context_window']}")
    print(f"Exclude Patterns: {config.exclude_patterns}")
    print(f"Skip Tests: {args.skip_tests}")
    print(f"Quick Mode: {args.quick}")
    print(f"Quality Threshold: {args.quality_threshold}")
    
    if args.steps:
        print(f"Selected Steps: {args.steps}")
    else:
        print("Pipeline: Full 11-step process")
        
    print("\nSteps that would be executed:")
    steps = [
        "1. Scoping & Guardrails",
        "2. Environment Prep", 
        "3. Static Harvest",
        "4. Dynamic Insights" if not args.quick else "4. Dynamic Insights (SKIPPED)",
        "5. Metadata & Context Packaging",
        "6. Chunking & Summarization", 
        "7. Quality Gates",
        "8. Secure Transfer Prep" if not args.no_encryption else "8. Transfer Prep (NO ENCRYPTION)",
        "9. Post-Transfer Validation",
        "10. Automation Integration",
        "11. Documentation & Handoff"
    ]
    
    for step in steps:
        if args.steps:
            step_name = step.split('.')[1].strip().lower().replace(' ', '').replace('&', '')
            if any(s in step_name for s in args.steps):
                print(f"  ✓ {step}")
            else:
                print(f"  ✗ {step} (SKIPPED)")
        else:
            print(f"  ✓ {step}")


async def execute_selected_steps(engine, selected_steps: List[str], args) -> dict:
    """Execute only selected pipeline steps"""
    logger = logging.getLogger(__name__)
    
    step_map = {
        'scope': lambda: logger.info("Scoping already configured"),
        'environment': engine._prepare_environment,
        'static': engine._static_analysis,
        'dynamic': engine._dynamic_analysis,
        'metadata': engine._package_metadata,
        'chunking': engine._chunk_and_summarize,
        'quality': engine._quality_validation,
        'transfer': lambda: engine._prepare_secure_bundle([]),
        'validation': engine._prepare_validation_suite,
        'automation': engine._setup_automation,
        'docs': engine._generate_documentation
    }
    
    logger.info(f"Executing selected steps: {selected_steps}")
    
    results = {}
    for step in selected_steps:
        if step in step_map:
            logger.info(f"Executing step: {step}")
            if step == 'chunking':
                results[step] = await step_map[step]()
            elif step == 'transfer':
                chunks = results.get('chunking', [])
                results[step] = await engine._prepare_secure_bundle(chunks)
            else:
                await step_map[step]()
                results[step] = "completed"
        else:
            logger.warning(f"Unknown step: {step}")
            
    # Return a mock bundle for selected steps
    from ..analysis.summarization_engine import SummaryBundle
    from datetime import datetime, timezone
    
    return SummaryBundle(
        metadata={"selected_steps": selected_steps},
        global_overview="Partial analysis completed",
        hierarchical_summaries={},
        chunk_manifest=results.get('chunking', []),
        quality_metrics={"overall_passed": True},
        checksum="partial",
        created_at=datetime.now(timezone.utc).isoformat(),
        version="1.0.0"
    )


def generate_summary_report(engine, bundle, args):
    """Generate a human-readable summary report"""
    report_path = engine.output_dir / "summary_report.md"
    
    # Calculate statistics
    total_files = len(engine.file_metadata)
    total_loc = sum(m.lines_of_code for m in engine.file_metadata.values())
    languages = set(m.language for m in engine.file_metadata.values())
    
    report_content = f"""# Codebase Summarization Report

## Analysis Summary
- **Workspace**: {args.workspace}
- **Total Files Analyzed**: {total_files:,}
- **Total Lines of Code**: {total_loc:,}
- **Programming Languages**: {', '.join(sorted(languages))}
- **Analysis Completed**: {bundle.created_at}

## Quality Metrics
- **Quality Gates Passed**: {bundle.quality_metrics.get('overall_passed', False)}
- **Test Coverage**: {engine._calculate_coverage_summary().get('overall', 0):.1f}%
- **Complexity Distribution**: {engine._calculate_complexity_distribution()}

## Output Artifacts
- **Metadata Package**: `metadata_package.json`
- **Architecture Overview**: `architecture_overview.json` 
- **Hierarchical Summaries**: `hierarchical_summaries.json`
- **Chunk Manifest**: `chunk_manifest.json`
- **Quality Metrics**: `quality_metrics.json`
- **Encrypted Bundle**: `summary_bundle_encrypted.enc`
- **Transfer Manifest**: `transfer_manifest.json`

## Key Components
{_format_key_components(engine._identify_key_components())}

## Next Steps
1. Review quality metrics in `quality_metrics.json`
2. Validate chunk sizes in `chunk_manifest.json`
3. Test transfer bundle with target LLM system
4. Set up automation pipeline if needed
5. Review documentation for maintenance procedures

## Usage with Target LLM
```bash
# Decrypt and extract bundle
openssl enc -aes-256-cbc -d -in summary_bundle_encrypted.enc -out summary_bundle.zip

# Load into your LLM system
# Context Window: {bundle.metadata.get('context_window', 'unknown')}
# Total Chunks: {len(bundle.chunk_manifest)}
```

Generated by NeuroCognitive Architecture Summarization Engine v{bundle.version}
"""
    
    with open(report_path, 'w') as f:
        f.write(report_content)
        
    print(f"\n📊 Summary report generated: {report_path}")


def _format_key_components(components: List[dict]) -> str:
    """Format key components for report"""
    if not components:
        return "No key components identified."
        
    lines = []
    for i, comp in enumerate(components[:10], 1):  # Top 10
        lines.append(f"{i}. **{comp['path']}** ({comp['language']}) - {comp['loc']} LOC, Complexity: {comp['complexity']:.1f}")
        
    return '\n'.join(lines)


def create_sample_config():
    """Create a sample configuration file"""
    sample_config = {
        "repos": ["main", "develop"],
        "branches": ["main", "develop", "feature/*"],
        "submodules": True,
        "include_generated": False,
        "include_data_files": True,
        "exclude_patterns": [
            "*.log", "*.tmp", "node_modules/", "__pycache__/", 
            ".git/", "*.pyc", "*.pyo", ".DS_Store", "dist/", "build/"
        ],
        "redflags": [
            "password", "secret", "api_key", "token", "private_key",
            "ssn", "credit_card", "license", "proprietary", "confidential"
        ],
        "target_llm_profile": {
            "context_window": 128000,
            "input_limits": 100000,
            "accepted_formats": ["json", "markdown", "yaml"],
            "rate_limits": {"requests_per_minute": 60}
        }
    }
    
    with open("summarization_config.json", 'w') as f:
        json.dump(sample_config, f, indent=2)
        
    print("Sample configuration created: summarization_config.json")


if __name__ == "__main__":
    # Handle special commands
    if len(sys.argv) > 1 and sys.argv[1] == "create-config":
        create_sample_config()
        sys.exit(0)
        
    asyncio.run(main())
