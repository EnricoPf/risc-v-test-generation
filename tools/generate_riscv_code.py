#!/usr/bin/env python3
"""
RISC-V Code Generator Script

This script takes instruction names as command-line parameters and generates
valid RISC-V assembly code with randomized valid parameter values.

Usage:
    python generate_riscv_code.py <instruction1> <instruction2> ... [options]

Examples:
    python generate_riscv_code.py add sub sll
    python generate_riscv_code.py addi lui --count 5
    python generate_riscv_code.py --all-r-type --count 10
    python generate_riscv_code.py add sub --output generated_code.s
"""

import argparse
import sys
import random
from pathlib import Path
from typing import List, Dict, Optional
import logging
import datetime

# Add the src directory to the path to import riscv_tools
sys.path.append(str(Path(__file__).parent.parent / "src"))
from riscv_tools import RiscVTestGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class RiscVCodeGenerator:
    """Generates valid RISC-V assembly code from instruction names."""
    
    def __init__(self):
        self.test_generator = RiscVTestGenerator()
        
    def generate_code_for_instructions(self, instructions: List[str], count_per_instruction: int = 1) -> List[str]:
        """
        Generate RISC-V assembly code for specified instructions.
        
        Args:
            instructions: List of instruction names
            count_per_instruction: Number of instances to generate per instruction
            
        Returns:
            List of assembly code lines
        """
        assembly_lines = []
        
        # Add header comment
        assembly_lines.append("# Generated RISC-V Assembly Code")
        assembly_lines.append("# Instructions: " + ", ".join(instructions))
        assembly_lines.append("")
        
        for instruction in instructions:
            # Check if instruction exists
            instr_info = self.test_generator.get_instruction_info(instruction)
            if not instr_info:
                logger.warning(f"Instruction '{instruction}' not found, skipping...")
                assembly_lines.append(f"# WARNING: Instruction '{instruction}' not found")
                continue
                
            # Generate test cases for this instruction
            test_cases = self.test_generator.generate_random_test_case(instruction, count_per_instruction)
            
            if test_cases:
                assembly_lines.append(f"# {instruction} instructions")
                for i, test_case in enumerate(test_cases, 1):
                    assembly_line = test_case.get('assembly', instruction)
                    assembly_lines.append(f"{assembly_line}")
                    
                    # Add a comment with parameter details
                    params = test_case.get('parameters', {})
                    if params:
                        param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                        assembly_lines.append(f"    # Parameters: {param_str}")
                assembly_lines.append("")
            else:
                logger.warning(f"No test cases generated for {instruction}")
                
        return assembly_lines
    
    def generate_format_code(self, format_type: str, count: int = 10) -> List[str]:
        """
        Generate code for all instructions of a specific format.
        
        Args:
            format_type: Instruction format ('R', 'I', 'S', 'B', 'U', 'J')
            count: Total number of instructions to generate
            
        Returns:
            List of assembly code lines
        """
        assembly_lines = []
        
        # Get all instructions of the specified format
        format_instructions = []
        for ext_name, ext_data in self.test_generator.opcodes_db.items():
            for instr_name, instr_info in ext_data.items():
                if (not instr_name.startswith('$') and 
                    instr_info.get('format') == format_type):
                    format_instructions.append(instr_name)
        
        if not format_instructions:
            logger.error(f"No instructions found for format {format_type}")
            return ["# No instructions found for format " + format_type]
        
        # Randomly select instructions to generate
        selected_instructions = random.sample(
            format_instructions, 
            min(count, len(format_instructions))
        )
        
        logger.info(f"Generating code for {len(selected_instructions)} {format_type}-type instructions")
        
        # Add header
        assembly_lines.append(f"# Generated {format_type}-Type RISC-V Instructions")
        assembly_lines.append(f"# Selected instructions: {', '.join(selected_instructions)}")
        assembly_lines.append("")
        
        # Generate code for each selected instruction
        for instruction in selected_instructions:
            test_cases = self.test_generator.generate_random_test_case(instruction, 1)
            if test_cases:
                test_case = test_cases[0]
                assembly_line = test_case.get('assembly', instruction)
                assembly_lines.append(f"{assembly_line}")
                
                # Add comment with details
                params = test_case.get('parameters', {})
                if params:
                    param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                    assembly_lines.append(f"    # {instruction} - {param_str}")
        
        return assembly_lines
    
    def list_available_instructions(self) -> List[str]:
        """Get list of all available instructions."""
        return self.test_generator.get_available_instructions()
    
    def list_instructions_by_format(self) -> Dict[str, List[str]]:
        """Get instructions organized by format."""
        by_format = {}
        
        for ext_name, ext_data in self.test_generator.opcodes_db.items():
            for instr_name, instr_info in ext_data.items():
                if not instr_name.startswith('$'):  # Skip pseudo-ops
                    format_type = instr_info.get('format', 'Unknown')
                    if format_type not in by_format:
                        by_format[format_type] = []
                    by_format[format_type].append(instr_name)
        
        # Sort lists
        for format_type in by_format:
            by_format[format_type] = sorted(set(by_format[format_type]))
            
        return by_format
    
    def generate_output_filename(self, instructions: List[str] = None, format_type: str = None, count: int = 1) -> str:
        """
        Generate an appropriate filename for the output.
        
        Args:
            instructions: List of instruction names (if specific instructions)
            format_type: Format type (if format-specific generation)
            count: Number of instances generated
            
        Returns:
            Generated filename with timestamp
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type:
            # Format-specific generation
            filename = f"riscv_{format_type.lower()}_type_{count}instr_{timestamp}.s"
        elif instructions:
            # Specific instructions
            if len(instructions) <= 3:
                instr_str = "_".join(instructions[:3])
            else:
                instr_str = f"{len(instructions)}instructions"
            filename = f"riscv_{instr_str}_{count}each_{timestamp}.s"
        else:
            # General case
            filename = f"riscv_generated_{timestamp}.s"
        
        return filename

def main():
    parser = argparse.ArgumentParser(
        description="Generate valid RISC-V assembly code with randomized parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add sub sll
  %(prog)s addi lui --count 5
  %(prog)s --all-r-type --count 10
  %(prog)s add sub --output generated_code.s
  %(prog)s add sub sll --save-to-output
  %(prog)s --format I --count 20 --save-to-output
  %(prog)s --list-instructions
  %(prog)s --list-by-format
        """
    )
    
    # Instruction arguments
    parser.add_argument(
        'instructions', 
        nargs='*', 
        help='Instruction names to generate code for'
    )
    
    # Generation options
    parser.add_argument(
        '--count', 
        type=int, 
        default=1,
        help='Number of instances per instruction (default: 1)'
    )
    
    # Format-specific generation
    parser.add_argument(
        '--all-r-type',
        action='store_true',
        help='Generate code for all R-type instructions'
    )
    
    parser.add_argument(
        '--all-i-type',
        action='store_true',
        help='Generate code for all I-type instructions'
    )
    
    parser.add_argument(
        '--format',
        choices=['R', 'I', 'S', 'B', 'U', 'J'],
        help='Generate code for all instructions of specified format'
    )
    
    # Output options
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: print to stdout)'
    )
    
    parser.add_argument(
        '--save-to-output',
        action='store_true',
        help='Save generated code to output/ folder with auto-generated filename'
    )
    
    # Information options
    parser.add_argument(
        '--list-instructions',
        action='store_true',
        help='List all available instructions and exit'
    )
    
    parser.add_argument(
        '--list-by-format',
        action='store_true',
        help='List instructions organized by format and exit'
    )
    
    # Verbose output
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize code generator
    try:
        generator = RiscVCodeGenerator()
    except Exception as e:
        logger.error(f"Failed to initialize code generator: {e}")
        sys.exit(1)
    
    # Handle information requests
    if args.list_instructions:
        instructions = generator.list_available_instructions()
        print(f"Available instructions ({len(instructions)}):")
        for i, instr in enumerate(instructions, 1):
            print(f"  {i:3d}. {instr}")
        sys.exit(0)
    
    if args.list_by_format:
        by_format = generator.list_instructions_by_format()
        print("Instructions by format:")
        for format_type, instrs in sorted(by_format.items()):
            print(f"\n{format_type}-Type ({len(instrs)} instructions):")
            for instr in instrs[:10]:  # Show first 10
                print(f"  {instr}")
            if len(instrs) > 10:
                print(f"  ... and {len(instrs) - 10} more")
        sys.exit(0)
    
    # Generate assembly code
    assembly_lines = []
    
    if args.all_r_type or args.format == 'R':
        assembly_lines = generator.generate_format_code('R', args.count)
    elif args.all_i_type or args.format == 'I':
        assembly_lines = generator.generate_format_code('I', args.count)
    elif args.format:
        assembly_lines = generator.generate_format_code(args.format, args.count)
    elif args.instructions:
        assembly_lines = generator.generate_code_for_instructions(args.instructions, args.count)
    else:
        parser.print_help()
        print("\nError: No instructions or format specified")
        sys.exit(1)
    
    # Output results
    output_text = '\n'.join(assembly_lines)
    
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(output_text)
            logger.info(f"Assembly code written to {args.output}")
        except Exception as e:
            logger.error(f"Failed to write to {args.output}: {e}")
            sys.exit(1)
    elif args.save_to_output:
        try:
            # Create output directory if it doesn't exist
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Generate appropriate filename
            if args.format or args.all_r_type or args.all_i_type:
                format_type = args.format or ('R' if args.all_r_type else 'I')
                filename = generator.generate_output_filename(format_type=format_type, count=args.count)
            else:
                filename = generator.generate_output_filename(instructions=args.instructions, count=args.count)
            
            output_path = output_dir / filename
            
            with open(output_path, 'w') as f:
                f.write(output_text)
            logger.info(f"Assembly code written to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write to output folder: {e}")
            sys.exit(1)
    else:
        print(output_text)

if __name__ == "__main__":
    main() 