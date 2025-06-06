import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RiscVTestGenerator:
    """Generates random test cases for RISC-V instructions using opcode metadata."""
    
    def __init__(self, opcodes_dir: Optional[str] = None):
        """
        Initialize the test generator.
        
        Args:
            opcodes_dir: Directory containing opcode JSON files.
                        If None, uses src/database/data/opcodes/
        """
        if opcodes_dir is None:
            # Navigate to project root and then to data directory
            project_root = Path(__file__).parent.parent.parent
            self.opcodes_dir = project_root / "data" / "opcodes"
        else:
            self.opcodes_dir = Path(opcodes_dir)
            
        self.opcodes_db = {}
        self._load_opcodes()
    
    def _load_opcodes(self):
        """Load all opcode definitions from the opcodes directory."""
        try:
            with open(self.opcodes_dir / "all_opcodes.json", 'r') as f:
                self.opcodes_db = json.load(f)
            logger.info(f"Loaded opcodes for {len(self.opcodes_db)} extensions")
        except Exception as e:
            logger.error(f"Failed to load opcodes: {e}")
            self.opcodes_db = {}
    
    def get_available_instructions(self) -> List[str]:
        """Get a list of all available instruction names."""
        instructions = []
        for ext_name, ext_data in self.opcodes_db.items():
            for instr_name in ext_data.keys():
                if not instr_name.startswith('$'):  # Skip pseudo-ops
                    instructions.append(instr_name)
        return sorted(set(instructions))
    
    def get_instruction_info(self, instruction_name: str) -> Optional[Dict]:
        """Get detailed information about a specific instruction."""
        for ext_name, ext_data in self.opcodes_db.items():
            if instruction_name in ext_data:
                info = ext_data[instruction_name].copy()
                info['extension'] = ext_name
                return info
        return None
    
    def _generate_random_register(self, constraints: Dict) -> int:
        """Generate a random register number within constraints."""
        min_val = constraints.get('min', 0)
        max_val = constraints.get('max', 31)
        exclude = constraints.get('exclude', [])
        
        available = [r for r in range(min_val, max_val + 1) if r not in exclude]
        return random.choice(available) if available else 0
    
    def _generate_random_immediate(self, constraints: Dict) -> int:
        """Generate a random immediate value within constraints."""
        min_val = constraints.get('min', -2048)
        max_val = constraints.get('max', 2047)
        return random.randint(min_val, max_val)
    
    def _adjust_immediate_for_format(self, value: int, inst_format: str) -> int:
        """Adjust immediate value based on instruction format constraints."""
        if inst_format == 'U':
            # U-Type uses 20-bit immediate in upper 20 bits
            return value & 0xFFFFF  # 20-bit mask
        elif inst_format == 'J':
            # J-Type uses 20-bit immediate with specific encoding
            # Ensure it's even (LSB is always 0 for jumps)
            return (value & 0xFFFFE)  # Clear LSB
        elif inst_format == 'B':
            # B-Type uses 12-bit immediate with specific encoding
            # Ensure it's even (LSB is always 0 for branches)
            return (value & 0xFFE)  # Clear LSB, 12-bit range
        else:
            # I-Type and S-Type use 12-bit signed immediate
            return value & 0xFFF if value >= 0 else (value | 0xFFFFF000)
    
    def generate_random_test_case(self, instruction_name: str, count: int = 1) -> List[Dict]:
        """
        Generate random test cases for a specific instruction.
        
        Args:
            instruction_name: Name of the instruction to generate tests for
            count: Number of test cases to generate
            
        Returns:
            List of test case dictionaries containing instruction and parameters
        """
        instr_info = self.get_instruction_info(instruction_name)
        if not instr_info:
            logger.error(f"Instruction '{instruction_name}' not found")
            return []
        
        test_cases = []
        for _ in range(count):
            test_case = {
                'instruction': instruction_name,
                'format': instr_info.get('format', 'Unknown'),
                'parameters': {},
                'assembly': '',
                'description': f"Random test case for {instruction_name}"
            }
            
            # Generate random values for each parameter
            parameters = instr_info.get('parameters', [])
            for param in parameters:
                param_name = param['name']
                constraints = param['constraints']
                
                if constraints['type'] == 'register':
                    value = self._generate_random_register(constraints)
                    test_case['parameters'][param_name] = value
                elif constraints['type'] == 'immediate':
                    value = self._generate_random_immediate(constraints)
                    # Adjust immediate based on instruction format
                    value = self._adjust_immediate_for_format(value, test_case['format'])
                    test_case['parameters'][param_name] = value
                else:
                    test_case['parameters'][param_name] = 0
            
            # Generate assembly string using template
            template = instr_info.get('assembly_template', instruction_name)
            try:
                assembly = template.format(**test_case['parameters'])
                test_case['assembly'] = assembly
            except KeyError as e:
                logger.warning(f"Template parameter missing: {e}")
                test_case['assembly'] = instruction_name
            
            test_cases.append(test_case)
        
        return test_cases
    
    def generate_test_suite(self, instructions: List[str], cases_per_instruction: int = 10) -> Dict:
        """
        Generate a comprehensive test suite for multiple instructions.
        
        Args:
            instructions: List of instruction names to generate tests for
            cases_per_instruction: Number of test cases per instruction
            
        Returns:
            Dictionary containing organized test suite
        """
        test_suite = {
            'metadata': {
                'total_instructions': len(instructions),
                'cases_per_instruction': cases_per_instruction,
                'total_test_cases': len(instructions) * cases_per_instruction
            },
            'test_cases': {}
        }
        
        for instruction in instructions:
            test_cases = self.generate_random_test_case(instruction, cases_per_instruction)
            if test_cases:
                test_suite['test_cases'][instruction] = test_cases
            else:
                logger.warning(f"No test cases generated for {instruction}")
        
        return test_suite
    
    def generate_format_specific_tests(self, format_type: str, count: int = 50) -> List[Dict]:
        """
        Generate random test cases for all instructions of a specific format.
        
        Args:
            format_type: Instruction format ('R', 'I', 'S', 'B', 'U', 'J')
            count: Total number of test cases to generate
            
        Returns:
            List of test cases for the specified format
        """
        format_instructions = []
        
        # Find all instructions of the specified format
        for ext_name, ext_data in self.opcodes_db.items():
            for instr_name, instr_info in ext_data.items():
                if (not instr_name.startswith('$') and 
                    instr_info.get('format') == format_type):
                    format_instructions.append(instr_name)
        
        if not format_instructions:
            logger.warning(f"No instructions found for format {format_type}")
            return []
        
        # Generate test cases
        test_cases = []
        cases_per_instruction = max(1, count // len(format_instructions))
        remaining_cases = count % len(format_instructions)
        
        for i, instruction in enumerate(format_instructions):
            case_count = cases_per_instruction
            if i < remaining_cases:
                case_count += 1
            
            cases = self.generate_random_test_case(instruction, case_count)
            test_cases.extend(cases)
        
        return test_cases
    
    def export_test_suite(self, test_suite: Dict, output_file: str):
        """Export test suite to a JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(test_suite, f, indent=2)
        
        logger.info(f"Test suite exported to {output_path}")
    
    def export_assembly_file(self, test_cases: List[Dict], output_file: str):
        """Export test cases as a RISC-V assembly file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write("# Generated RISC-V Test Cases\n")
            f.write("# This file contains randomly generated instruction test cases\n\n")
            f.write(".section .text\n")
            f.write(".global _start\n\n")
            f.write("_start:\n")
            
            for i, test_case in enumerate(test_cases):
                f.write(f"    # Test case {i+1}: {test_case['description']}\n")
                f.write(f"    {test_case['assembly']}\n")
            
            f.write("\n    # Program termination\n")
            f.write("    li a7, 93     # sys_exit\n")
            f.write("    li a0, 0      # exit status\n")
            f.write("    ecall\n")
        
        logger.info(f"Assembly file exported to {output_path}")

def main():
    """Demo function showing test generation capabilities."""
    generator = RiscVTestGenerator()
    
    # Get available instructions
    instructions = generator.get_available_instructions()
    print(f"Available instructions: {len(instructions)}")
    
    # Generate test cases for a specific instruction
    if 'add' in instructions:
        test_cases = generator.generate_random_test_case('add', 5)
        print(f"\nGenerated test cases for 'add':")
        for case in test_cases:
            print(f"  {case['assembly']}")
    
    # Generate test cases for all R-Type instructions
    r_type_tests = generator.generate_format_specific_tests('R', 20)
    print(f"\nGenerated {len(r_type_tests)} R-Type test cases")
    
    # Generate a comprehensive test suite
    sample_instructions = instructions[:10] if len(instructions) >= 10 else instructions
    test_suite = generator.generate_test_suite(sample_instructions, 3)
    print(f"\nGenerated test suite with {test_suite['metadata']['total_test_cases']} total cases")

if __name__ == "__main__":
    main() 