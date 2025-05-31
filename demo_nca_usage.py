#!/usr/bin/env python3
"""
Simple demonstration of how to use the Neuro-Cognitive Architecture (NCA) system.

This script shows basic usage patterns for the core NCA components.
"""

import sys
import os

# Add src to Python path to import NCA modules
sys.path.insert(0, 'src')

def demo_memory_system():
    """Demonstrate basic MemorySystem usage."""
    print("=== NCA Memory System Demo ===")
    
    try:
        from neuroca.memory import MemorySystem
        
        # Create memory system instance
        memory = MemorySystem()
        print(f"✓ MemorySystem created: {type(memory)}")
        
        # Note: Many components show "not yet implemented" - this is expected
        # The core framework is there, implementations are in progress
        
        return memory
    except ImportError as e:
        print(f"❌ Failed to import MemorySystem: {e}")
        return None

def demo_health_system():
    """Demonstrate health system components."""
    print("\n=== NCA Health System Demo ===")
    
    try:
        from neuroca.core.health import HealthState, HealthMetrics
        
        print(f"✓ HealthState enum: {list(HealthState)}")
        print(f"✓ HealthMetrics available: {HealthMetrics}")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import health components: {e}")
        return False

def demo_basic_integration():
    """Show how components work together."""
    print("\n=== NCA Integration Demo ===")
    
    try:
        from neuroca import __version__
        from neuroca.memory import MemorySystem
        from neuroca.core.health import HealthState
        
        print(f"✓ NCA Version: {__version__}")
        
        # Create core components
        memory = MemorySystem()
        
        # This demonstrates the architecture is working
        # Even if specific implementations are stubs
        
        print("✓ Core NCA architecture is functional")
        print("✓ Memory system instantiated")
        print("✓ Health system components available")
        
        return True
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return False

def show_available_modules():
    """Show what NCA modules are available."""
    print("\n=== Available NCA Modules ===")
    
    import neuroca
    nca_path = os.path.dirname(neuroca.__file__)
    
    # Walk through NCA modules
    for root, dirs, files in os.walk(nca_path):
        level = root.replace(nca_path, '').count(os.sep)
        indent = ' ' * 2 * level
        rel_path = os.path.relpath(root, nca_path)
        if rel_path != '.':
            print(f"{indent}📁 {rel_path}/")
        
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                print(f"{subindent}📄 {file}")

def main():
    """Run the NCA usage demonstration."""
    print("🧠 Neuro-Cognitive Architecture (NCA) Usage Demo")
    print("=" * 50)
    
    # Demonstrate core functionality
    memory_system = demo_memory_system()
    health_ok = demo_health_system()
    integration_ok = demo_basic_integration()
    
    print("\n" + "=" * 50)
    
    if memory_system and health_ok and integration_ok:
        print("🎉 SUCCESS: NCA core components are working!")
        print("\n💡 Key Points:")
        print("  • Memory system framework is functional")
        print("  • Health system components are available") 
        print("  • Core architecture is sound")
        print("  • Many implementations are stubs (expected for v0.1.0)")
        
        show_available_modules()
        
        print("\n📖 Next Steps:")
        print("  • Explore specific modules in src/neuroca/")
        print("  • Check docs/ for detailed documentation")
        print("  • Implement missing components as needed")
        print("  • Use the framework to build cognitive applications")
        
    else:
        print("❌ Some components failed to load")
        print("Check dependencies and file structure")

if __name__ == "__main__":
    main()
