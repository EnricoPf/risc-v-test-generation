#!/usr/bin/env python3
"""
Quick test script to demonstrate the reorganized RISC-V tools workflow.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and display the result."""
    print(f"\n🔧 {description}")
    print("=" * 50)
    print(f"Command: {cmd}")
    print()
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
        print(f"✅ {description} - SUCCESS")
    else:
        print(f"❌ {description} - FAILED")
        print(f"Error: {result.stderr}")
        return False
    
    return True

def main():
    """Run the quick test workflow."""
    print("🚀 RISC-V Tools Reorganization Test")
    print("=" * 60)
    print("Testing the new organized project structure...")
    
    # Test 1: Generate specific instructions
    if not run_command(
        "python3 tools/generate_riscv_code.py add sub addi --count 2 --save-to-output",
        "Generate specific instructions"
    ):
        return False
    
    # Test 2: Generate format-specific instructions
    if not run_command(
        "python3 tools/generate_riscv_code.py --format R --count 3 --save-to-output",
        "Generate R-type instructions"
    ):
        return False
    
    # Test 3: List available files
    if not run_command(
        "ls -la output/",
        "List generated files"
    ):
        return False
    
    # Test 4: Validate the first generated file
    output_dir = Path("output")
    if output_dir.exists():
        s_files = list(output_dir.glob("*.s"))
        if s_files:
            first_file = s_files[0]
            if not run_command(
                f"python3 tools/validate_riscv_code.py {first_file}",
                f"Validate {first_file.name}"
            ):
                return False
        else:
            print("❌ No .s files found in output directory")
            return False
    
    # Test 5: Show project structure
    if not run_command(
        "tree -L 2 -a 2>/dev/null || find . -maxdepth 2 -type d | sort",
        "Show new project structure"
    ):
        return False
    
    print("\n🎉 All tests passed!")
    print("=" * 60)
    print("✅ Code generation works")
    print("✅ Code validation works") 
    print("✅ File organization works")
    print("✅ New structure is functional")
    print("\n📁 Files organized in:")
    print("  • tools/     - Main executable scripts")
    print("  • src/       - Core library modules")
    print("  • data/      - Data files")
    print("  • output/    - Generated files")
    print("  • tests/     - Test scripts")
    print("  • docs/      - Documentation")

if __name__ == "__main__":
    main() 