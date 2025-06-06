#!/usr/bin/env python3
"""Debug script to test the validator."""

import sys
from validate_riscv_code import RiscVValidator

def test_validator():
    validator = RiscVValidator()
    
    # Test cases
    test_lines = [
        "add x1, x2, x3",
        "add x50, x1, x2", 
        "addi x1, x2, 5000",
        "invalid_instr x1"
    ]
    
    print("Testing individual lines:")
    for i, line in enumerate(test_lines, 1):
        print(f"\nLine {i}: '{line}'")
        result = validator.validate_assembly_line(line, i)
        print(f"  Type: {result['type']}")
        print(f"  Valid: {result['valid']}")
        print(f"  Instruction: {result.get('instruction')}")
        print(f"  Parameters: {result.get('parameters')}")
        if result.get('errors'):
            print(f"  Errors: {result['errors']}")
        if result.get('warnings'):
            print(f"  Warnings: {result['warnings']}")

if __name__ == "__main__":
    test_validator() 