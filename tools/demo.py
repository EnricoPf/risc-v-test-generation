#!/usr/bin/env python3
"""
RISC-V Code Generation and Validation Demo

This script demonstrates the complete workflow of generating random RISC-V
assembly code and validating it for correctness.
"""

import subprocess
import tempfile
import os
from pathlib import Path

def run_command(cmd):
    """Run a command and return the result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def demo_basic_generation():
    """Demo basic code generation."""
    print("🔧 DEMO 1: Basic Code Generation")
    print("=" * 50)
    
    cmd = "python3 generate_riscv_code.py add sub sll addi lui --count 2"
    ret_code, stdout, stderr = run_command(cmd)
    
    print("Command:", cmd)
    print("Generated code:")
    print(stdout)
    
    return stdout

def demo_format_generation():
    """Demo format-specific generation."""
    print("\n🔧 DEMO 2: Format-Specific Generation")
    print("=" * 50)
    
    cmd = "python3 generate_riscv_code.py --format I --count 5"
    ret_code, stdout, stderr = run_command(cmd)
    
    print("Command:", cmd)
    print("Generated I-Type instructions:")
    print(stdout)
    
    return stdout

def demo_validation(assembly_code):
    """Demo validation of generated code."""
    print("\n🔧 DEMO 3: Code Validation")
    print("=" * 50)
    
    # Create temporary file with assembly code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
        f.write(assembly_code)
        temp_file = f.name
    
    try:
        # Validate the code
        cmd = f"python3 validate_riscv_code.py {temp_file} --verbose"
        ret_code, stdout, stderr = run_command(cmd)
        
        print("Command:", cmd)
        print("Validation result:")
        print(stdout)
        
        if ret_code == 0:
            print("✅ Code validation: PASSED")
        else:
            print("❌ Code validation: FAILED")
            
    finally:
        # Clean up temporary file
        os.unlink(temp_file)

def demo_invalid_code():
    """Demo validation with invalid code."""
    print("\n🔧 DEMO 4: Invalid Code Detection")
    print("=" * 50)
    
    invalid_code = """# Test invalid instructions
add x1, x2, x3      # Valid
add x50, x1, x2     # Invalid register (x50 > x31)
addi x1, x2, 5000   # Invalid immediate (out of range)
invalid_instr x1    # Invalid instruction name
"""
    
    # Create temporary file with invalid assembly code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
        f.write(invalid_code)
        temp_file = f.name
    
    try:
        cmd = f"python3 validate_riscv_code.py {temp_file} --verbose"
        ret_code, stdout, stderr = run_command(cmd)
        
        print("Invalid test code:")
        print(invalid_code)
        print("Validation result:")
        print(stdout)
        
        if ret_code != 0:
            print("✅ Error detection: WORKING (correctly detected invalid code)")
        else:
            print("❌ Error detection: NOT WORKING (should have failed)")
            
    finally:
        os.unlink(temp_file)

def demo_instruction_listing():
    """Demo instruction listing capabilities."""
    print("\n🔧 DEMO 5: Available Instructions")
    print("=" * 50)
    
    cmd = "python3 generate_riscv_code.py --list-by-format"
    ret_code, stdout, stderr = run_command(cmd)
    
    print("Command:", cmd)
    print("Available instruction formats:")
    # Show only first few lines to keep output manageable
    lines = stdout.split('\n')
    for line in lines[:20]:
        print(line)
    print("... (truncated for demo)")

def main():
    """Run all demonstrations."""
    print("🚀 RISC-V Code Generation and Validation Demo")
    print("=" * 60)
    print("This demo shows the complete workflow of:")
    print("  1. Generating random RISC-V assembly code")
    print("  2. Validating the generated code for correctness")
    print("  3. Detecting invalid instructions and parameters")
    print()
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run demonstrations
    assembly_code = demo_basic_generation()
    format_code = demo_format_generation()
    demo_validation(assembly_code)
    demo_invalid_code()
    demo_instruction_listing()
    
    print("\n🎉 Demo Complete!")
    print("=" * 60)
    print("Summary of capabilities demonstrated:")
    print("  ✅ Random instruction generation with valid parameters")
    print("  ✅ Format-specific instruction generation")
    print("  ✅ Assembly code validation")
    print("  ✅ Error detection for invalid code")
    print("  ✅ Instruction format classification")
    print()
    print("Next steps:")
    print("  • Use generate_riscv_code.py to create test cases")
    print("  • Use validate_riscv_code.py to verify correctness")
    print("  • Integrate into your testing pipeline")

if __name__ == "__main__":
    main() 