#!/usr/bin/env python3
"""
RISC-V Code Validator Script

This script validates generated RISC-V assembly code for correctness including:
- Instruction syntax validation
- Parameter constraint checking
- Register range validation
- Immediate value range validation
- Instruction format compliance

Usage:
    python validate_riscv_code.py <assembly_file>
    python validate_riscv_code.py --stdin
    python validate_riscv_code.py <assembly_file> --verbose
"""

import argparse
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import logging

# Add the src directory to the path to import riscv_tools
sys.path.append(str(Path(__file__).parent.parent / "src"))
from riscv_tools import RiscVTestGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class RiscVValidator:
    """Validates RISC-V assembly code for correctness."""
    
    def __init__(self):
        self.test_generator = RiscVTestGenerator()
        self.validation_errors = []
        self.validation_warnings = []
        
        # Compile regex patterns for parsing
        self.register_pattern = re.compile(r'^x(\d+)$')  # Any x followed by digits
        self.immediate_pattern = re.compile(r'^-?\d+$')
        self.instruction_pattern = re.compile(r'^([a-zA-Z][a-zA-Z0-9_.]*)\s*(.*)$')
        
    def validate_assembly_file(self, file_path: str) -> Dict:
        """
        Validate an entire assembly file.
        
        Args:
            file_path: Path to assembly file
            
        Returns:
            Dictionary with validation results
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            return {
                'valid': False,
                'error': f"Failed to read file: {e}",
                'line_results': []
            }
        
        return self.validate_assembly_lines(lines, file_path)
    
    def validate_assembly_lines(self, lines: List[str], source: str = "input") -> Dict:
        """
        Validate a list of assembly lines.
        
        Args:
            lines: List of assembly code lines
            source: Source identifier for error reporting
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'source': source,
            'total_lines': len(lines),
            'instruction_lines': 0,
            'valid_instructions': 0,
            'errors': [],
            'warnings': [],
            'line_results': []
        }
        
        for line_num, line in enumerate(lines, 1):
            line_result = self.validate_assembly_line(line.strip(), line_num)
            results['line_results'].append(line_result)
            
            if line_result['type'] == 'instruction':
                results['instruction_lines'] += 1
                if line_result['valid']:
                    results['valid_instructions'] += 1
                else:
                    results['valid'] = False
                    
            # Collect errors and warnings
            results['errors'].extend(line_result.get('errors', []))
            results['warnings'].extend(line_result.get('warnings', []))
        
        return results
    
    def validate_assembly_line(self, line: str, line_num: int = 1) -> Dict:
        """
        Validate a single assembly line.
        
        Args:
            line: Assembly code line
            line_num: Line number for error reporting
            
        Returns:
            Dictionary with line validation results
        """
        result = {
            'line_number': line_num,
            'line': line,
            'type': 'unknown',
            'valid': True,
            'errors': [],
            'warnings': [],
            'instruction': None,
            'parameters': {}
        }
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            result['type'] = 'comment'
            return result
        
        # Parse instruction
        match = self.instruction_pattern.match(line)
        if not match:
            result['type'] = 'invalid'
            result['valid'] = False
            result['errors'].append(f"Line {line_num}: Invalid instruction format")
            return result
        
        instruction_name = match.group(1).lower()
        params_str = match.group(2).strip()
        
        # Remove inline comments
        if '#' in params_str:
            params_str = params_str.split('#')[0].strip()
        
        result['type'] = 'instruction'
        result['instruction'] = instruction_name
        
        # Get instruction information
        instr_info = self.test_generator.get_instruction_info(instruction_name)
        if not instr_info:
            result['valid'] = False
            result['errors'].append(f"Line {line_num}: Unknown instruction '{instruction_name}'")
            return result
        
        # Parse parameters
        parsed_params = self._parse_parameters(params_str, line_num)
        if parsed_params is None:
            result['valid'] = False
            result['errors'].append(f"Line {line_num}: Failed to parse parameters")
            return result
        
        result['parameters'] = parsed_params
        
        # Validate parameters against instruction definition
        validation_result = self._validate_instruction_parameters(
            instruction_name, instr_info, parsed_params, line_num
        )
        
        result['valid'] = validation_result['valid']
        result['errors'].extend(validation_result['errors'])
        result['warnings'].extend(validation_result['warnings'])
        
        return result
    
    def _parse_parameters(self, params_str: str, line_num: int) -> Optional[Dict]:
        """Parse parameter string into components."""
        if not params_str.strip():
            return {}
        
        try:
            # Split by comma and clean up
            param_parts = [p.strip() for p in params_str.split(',')]
            parsed = {}
            
            for i, part in enumerate(param_parts):
                # Determine parameter type
                reg_match = self.register_pattern.match(part)
                if reg_match:
                    # Register parameter (validate range later)
                    reg_num = int(reg_match.group(1))
                    parsed[f'param_{i}'] = {
                        'type': 'register',
                        'value': part,
                        'numeric_value': reg_num
                    }
                elif self.immediate_pattern.match(part):
                    # Immediate parameter
                    imm_val = int(part)
                    parsed[f'param_{i}'] = {
                        'type': 'immediate',
                        'value': part,
                        'numeric_value': imm_val
                    }
                else:
                    # Unknown parameter type
                    parsed[f'param_{i}'] = {
                        'type': 'unknown',
                        'value': part,
                        'numeric_value': None
                    }
            
            return parsed
            
        except Exception as e:
            logger.debug(f"Parameter parsing error on line {line_num}: {e}")
            return None
    
    def _validate_instruction_parameters(self, instruction_name: str, instr_info: Dict, 
                                       parsed_params: Dict, line_num: int) -> Dict:
        """Validate parsed parameters against instruction definition."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        expected_params = instr_info.get('parameters', [])
        
        # Check parameter count
        if len(parsed_params) != len(expected_params):
            result['valid'] = False
            result['errors'].append(
                f"Line {line_num}: {instruction_name} expects {len(expected_params)} "
                f"parameters, got {len(parsed_params)}"
            )
            return result
        
        # Validate each parameter
        for i, expected_param in enumerate(expected_params):
            param_key = f'param_{i}'
            if param_key not in parsed_params:
                continue
                
            parsed_param = parsed_params[param_key]
            param_name = expected_param['name']
            constraints = expected_param['constraints']
            
            # Validate parameter type
            expected_type = constraints['type']
            actual_type = parsed_param['type']
            
            if expected_type != actual_type:
                result['valid'] = False
                result['errors'].append(
                    f"Line {line_num}: Parameter {i+1} ({param_name}) should be "
                    f"{expected_type}, got {actual_type}"
                )
                continue
            
            # Validate parameter constraints
            if expected_type == 'register':
                reg_result = self._validate_register_constraints(
                    parsed_param['numeric_value'], constraints, param_name, line_num
                )
                if not reg_result['valid']:
                    result['valid'] = False
                result['errors'].extend(reg_result['errors'])
                result['warnings'].extend(reg_result['warnings'])
                
            elif expected_type == 'immediate':
                imm_result = self._validate_immediate_constraints(
                    parsed_param['numeric_value'], constraints, param_name, 
                    instr_info.get('format', 'Unknown'), line_num
                )
                if not imm_result['valid']:
                    result['valid'] = False
                result['errors'].extend(imm_result['errors'])
                result['warnings'].extend(imm_result['warnings'])
        
        return result
    
    def _validate_register_constraints(self, reg_value: int, constraints: Dict, 
                                     param_name: str, line_num: int) -> Dict:
        """Validate register parameter constraints."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        min_val = constraints.get('min', 0)
        max_val = constraints.get('max', 31)
        exclude = constraints.get('exclude', [])
        
        # Check range
        if reg_value < min_val or reg_value > max_val:
            result['valid'] = False
            result['errors'].append(
                f"Line {line_num}: Register {param_name} (x{reg_value}) out of range "
                f"[{min_val}-{max_val}]"
            )
        
        # Check exclusions
        if reg_value in exclude:
            result['valid'] = False
            result['errors'].append(
                f"Line {line_num}: Register {param_name} (x{reg_value}) is excluded "
                f"for this instruction"
            )
        
        # Warning for x0 usage in destination
        if reg_value == 0 and param_name == 'rd':
            result['warnings'].append(
                f"Line {line_num}: Writing to x0 (zero register) has no effect"
            )
        
        return result
    
    def _validate_immediate_constraints(self, imm_value: int, constraints: Dict, 
                                      param_name: str, inst_format: str, line_num: int) -> Dict:
        """Validate immediate parameter constraints."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        min_val = constraints.get('min', -2048)
        max_val = constraints.get('max', 2047)
        
        # Format-specific constraints
        if inst_format == 'I':
            # I-Type: 12-bit signed immediate
            if imm_value < -2048 or imm_value > 2047:
                result['valid'] = False
                result['errors'].append(
                    f"Line {line_num}: I-Type immediate {param_name} ({imm_value}) "
                    f"out of range [-2048, 2047]"
                )
        elif inst_format == 'S':
            # S-Type: 12-bit signed immediate
            if imm_value < -2048 or imm_value > 2047:
                result['valid'] = False
                result['errors'].append(
                    f"Line {line_num}: S-Type immediate {param_name} ({imm_value}) "
                    f"out of range [-2048, 2047]"
                )
        elif inst_format == 'B':
            # B-Type: 12-bit signed immediate, must be even
            if imm_value < -2048 or imm_value > 2047:
                result['valid'] = False
                result['errors'].append(
                    f"Line {line_num}: B-Type immediate {param_name} ({imm_value}) "
                    f"out of range [-2048, 2047]"
                )
            if imm_value % 2 != 0:
                result['valid'] = False
                result['errors'].append(
                    f"Line {line_num}: B-Type immediate {param_name} ({imm_value}) "
                    f"must be even (aligned to 2 bytes)"
                )
        elif inst_format == 'U':
            # U-Type: 20-bit immediate in upper bits
            if imm_value < 0 or imm_value > 0xFFFFF:
                result['valid'] = False
                result['errors'].append(
                    f"Line {line_num}: U-Type immediate {param_name} ({imm_value}) "
                    f"out of range [0, {0xFFFFF}]"
                )
        elif inst_format == 'J':
            # J-Type: 20-bit signed immediate, must be even
            if imm_value < -524288 or imm_value > 524287:
                result['valid'] = False
                result['errors'].append(
                    f"Line {line_num}: J-Type immediate {param_name} ({imm_value}) "
                    f"out of range [-524288, 524287]"
                )
            if imm_value % 2 != 0:
                result['valid'] = False
                result['errors'].append(
                    f"Line {line_num}: J-Type immediate {param_name} ({imm_value}) "
                    f"must be even (aligned to 2 bytes)"
                )
        
        # Check general constraints only for non-format-specific cases
        # Skip this check for types that have format-specific validation
        if inst_format not in ['U', 'J', 'I', 'S', 'B'] and (imm_value < min_val or imm_value > max_val):
            result['warnings'].append(
                f"Line {line_num}: Immediate {param_name} ({imm_value}) outside "
                f"typical range [{min_val}, {max_val}]"
            )
        
        return result
    
    def print_validation_report(self, results: Dict, verbose: bool = False):
        """Print a formatted validation report."""
        print(f"\n=== RISC-V Code Validation Report ===")
        print(f"Source: {results['source']}")
        print(f"Total lines: {results['total_lines']}")
        print(f"Instruction lines: {results['instruction_lines']}")
        print(f"Valid instructions: {results['valid_instructions']}")
        print(f"Overall result: {'✓ VALID' if results['valid'] else '✗ INVALID'}")
        
        # Print errors
        if results['errors']:
            print(f"\n🔴 Errors ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  {error}")
        
        # Print warnings
        if results['warnings']:
            print(f"\n🟡 Warnings ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"  {warning}")
        
        # Print line-by-line results if verbose
        if verbose and results['line_results']:
            print(f"\n📋 Line-by-line Results:")
            for line_result in results['line_results']:
                line_num = line_result['line_number']
                line_type = line_result['type']
                valid = line_result['valid']
                
                if line_type == 'instruction':
                    status = "✓" if valid else "✗"
                    instruction = line_result.get('instruction', 'unknown')
                    print(f"  {line_num:3d}: {status} {instruction}")
                    
                    if line_result['errors']:
                        for error in line_result['errors']:
                            print(f"       🔴 {error}")
                    
                    if line_result['warnings']:
                        for warning in line_result['warnings']:
                            print(f"       🟡 {warning}")
        
        print()

def main():
    parser = argparse.ArgumentParser(
        description="Validate RISC-V assembly code for correctness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generated_code.s
  %(prog)s --stdin < assembly_code.txt
  %(prog)s generated_code.s --verbose
  %(prog)s multiple_files.s --json-output validation_results.json
        """
    )
    
    # Input options
    parser.add_argument(
        'file',
        nargs='?',
        help='Assembly file to validate'
    )
    
    parser.add_argument(
        '--stdin',
        action='store_true',
        help='Read assembly code from stdin'
    )
    
    # Output options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output with line-by-line results'
    )
    
    parser.add_argument(
        '--json-output',
        help='Output validation results to JSON file'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only output final result (valid/invalid)'
    )
    
    args = parser.parse_args()
    
    # Validate input arguments
    if not args.file and not args.stdin:
        parser.print_help()
        print("\nError: Must specify either a file or --stdin")
        sys.exit(1)
    
    if args.file and args.stdin:
        print("Error: Cannot specify both file and --stdin")
        sys.exit(1)
    
    # Initialize validator
    try:
        validator = RiscVValidator()
    except Exception as e:
        print(f"Error: Failed to initialize validator: {e}")
        sys.exit(1)
    
    # Validate assembly code
    try:
        if args.stdin:
            lines = sys.stdin.readlines()
            results = validator.validate_assembly_lines(lines, "stdin")
        else:
            results = validator.validate_assembly_file(args.file)
    except Exception as e:
        print(f"Error: Validation failed: {e}")
        sys.exit(1)
    
    # Output results
    if args.json_output:
        try:
            with open(args.json_output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Validation results written to {args.json_output}")
        except Exception as e:
            print(f"Error: Failed to write JSON output: {e}")
            sys.exit(1)
    
    if args.quiet:
        print("VALID" if results['valid'] else "INVALID")
    else:
        validator.print_validation_report(results, args.verbose)
    
    # Exit with appropriate code
    sys.exit(0 if results['valid'] else 1)

if __name__ == "__main__":
    main() 