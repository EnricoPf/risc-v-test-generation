#!/usr/bin/env python3
"""Minimal test to debug validator."""

from validate_riscv_code import RiscVValidator

def main():
    validator = RiscVValidator()
    
    print("Testing simple validation...")
    
    # Test with a simple file
    try:
        results = validator.validate_assembly_file('simple_test.s')
        print("Results:")
        print(f"  Valid: {results['valid']}")
        print(f"  Total lines: {results['total_lines']}")
        print(f"  Instruction lines: {results['instruction_lines']}")
        print(f"  Valid instructions: {results['valid_instructions']}")
        print(f"  Errors: {results['errors']}")
        print(f"  Warnings: {results['warnings']}")
        
        validator.print_validation_report(results, True)
        
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 