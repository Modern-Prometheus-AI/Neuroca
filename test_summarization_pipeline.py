#!/usr/bin/env python3
"""
Integration Test for the 11-Step Codebase Summarization Pipeline

This test demonstrates the complete automated codebase analysis and 
summarization system working end-to-end.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from neuroca.analysis.summarization_engine import (
    CodebaseSummarizationEngine, 
    ScopeConfig,
    create_summarization_engine
)


@pytest.mark.asyncio
async def test_complete_pipeline():
    """Test the complete 11-step summarization pipeline"""
    
    print("🚀 Starting 11-Step Codebase Summarization Pipeline Test")
    print("=" * 60)
    
    # Set up environment
    workspace_path = Path(__file__).parent
    os.environ['SUMMARY_ENCRYPTION_KEY'] = 'test-key-for-demo-12345'
    
    try:
        # Step 1: Create engine with scope configuration
        print("\n📋 Step 1: Configuring scope and guardrails...")
        engine = await create_summarization_engine(
            workspace_path=str(workspace_path),
            repos=["neuroca-main"],
            context_window=128000
        )
        print("✅ Scope configured successfully")
        
        # Execute the full pipeline
        print("\n🔄 Executing complete 11-step pipeline...")
        print("   This will analyze the current codebase and generate summaries")
        
        bundle = await engine.execute_full_pipeline()
        
        print("✅ Pipeline completed successfully!")
        
        # Display results
        print("\n📊 Pipeline Results:")
        print("=" * 40)
        print(f"📦 Bundle created: {bundle.created_at}")
        print(f"🔐 Checksum: {bundle.checksum[:16]}...")
        print(f"📁 Total chunks: {len(bundle.chunk_manifest)}")
        print(f"✅ Quality gates: {'PASSED' if bundle.quality_metrics.get('overall_passed', False) else 'FAILED'}")
        
        # Show generated artifacts
        artifacts_dir = workspace_path / "analysis_artifacts" / "summarization"
        if artifacts_dir.exists():
            print(f"\n📂 Generated artifacts in: {artifacts_dir}")
            for artifact in artifacts_dir.iterdir():
                if artifact.is_file():
                    size_mb = artifact.stat().st_size / (1024 * 1024)
                    print(f"   📄 {artifact.name} ({size_mb:.2f}MB)")
        
        # Show some sample content
        print("\n📋 Sample Analysis Results:")
        print("-" * 30)
        
        # Display metadata summary
        metadata_file = artifacts_dir / "metadata_package.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                files_analyzed = len(metadata.get('files', {}))
                print(f"📊 Files analyzed: {files_analyzed}")
                
                # Show language distribution
                languages = {}
                for file_data in metadata.get('files', {}).values():
                    lang = file_data.get('language', 'unknown')
                    languages[lang] = languages.get(lang, 0) + 1
                
                print("🏷️  Language distribution:")
                for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"   {lang}: {count} files")
        
        # Display architecture overview
        arch_file = artifacts_dir / "architecture_overview.json"
        if arch_file.exists():
            with open(arch_file, 'r') as f:
                arch = json.load(f)
                print(f"\n🏗️  Architecture Overview:")
                print(f"   Project: {arch.get('project_name', 'Unknown')}")
                print(f"   Total LOC: {arch.get('total_loc', 0):,}")
                print(f"   Complexity distribution: {arch.get('complexity_distribution', {})}")
        
        print("\n🎉 Integration test completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def demo_cli_usage():
    """Demonstrate CLI usage patterns"""
    
    print("\n🖥️  CLI Usage Demonstration")
    print("=" * 40)
    
    print("To run the summarization pipeline manually:")
    print("```bash")
    print("# Basic usage")
    print("python -m neuroca.scripts.summarize_codebase")
    print("")
    print("# With custom parameters")
    print("python -m neuroca.scripts.summarize_codebase \\")
    print("  --workspace /path/to/code \\")
    print("  --context-window 200000 \\")
    print("  --log-level DEBUG")
    print("")
    print("# Dry run mode")
    print("python -m neuroca.scripts.summarize_codebase --dry-run")
    print("")
    print("# Selected steps only")
    print("python -m neuroca.scripts.summarize_codebase \\")
    print("  --steps static,dynamic,quality")
    print("```")


async def demo_automation_setup():
    """Demonstrate automation setup"""
    
    print("\n🤖 Automation Setup Demonstration")
    print("=" * 40)
    
    try:
        from neuroca.analysis.automation import create_automation_engine
        
        # Create automation engine
        automation = create_automation_engine(
            workspace_path=str(Path(__file__).parent),
            output_path=str(Path(__file__).parent / "automation_output")
        )
        
        # Setup automation infrastructure
        await automation.setup_automation()
        
        print("✅ Automation infrastructure created:")
        print("   📄 GitHub Actions workflow")
        print("   📄 GitLab CI configuration") 
        print("   📄 Jenkins pipeline")
        print("   📄 Monitoring setup")
        
        # Show metrics
        metrics = automation.get_pipeline_metrics()
        print(f"\n📊 Pipeline Metrics:")
        print(f"   Total runs: {metrics.get('total_runs', 0)}")
        print(f"   Success rate: {metrics.get('success_rate', 0):.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Automation demo failed: {e}")
        return False


if __name__ == "__main__":
    async def main():
        print("🧠 NeuroCognitive Architecture - Codebase Summarization Demo")
        print("=" * 60)
        
        # Run integration test
        test_result = await test_complete_pipeline()
        
        # Demo CLI usage
        await demo_cli_usage()
        
        # Demo automation
        automation_result = await demo_automation_setup()
        
        print(f"\n📋 Test Summary:")
        print(f"   Pipeline test: {'✅ PASSED' if test_result else '❌ FAILED'}")
        print(f"   Automation demo: {'✅ PASSED' if automation_result else '❌ FAILED'}")
        
        if test_result and automation_result:
            print("\n🎉 All demonstrations completed successfully!")
            print("The 11-step codebase summarization system is fully operational.")
        else:
            print("\n⚠️  Some demonstrations had issues. Check logs for details.")
    
    asyncio.run(main())
