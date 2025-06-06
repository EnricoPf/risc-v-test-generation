import requests
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging
import re

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RiscVOpcodesFetcher:
    """Fetches RISC-V opcode definitions from the GitHub repository."""
    
    BASE_URL = "https://api.github.com/repos/riscv/riscv-opcodes/contents"
    RAW_BASE_URL = "https://raw.githubusercontent.com/riscv/riscv-opcodes/master"
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the fetcher.
        
        Args:
            output_dir: Directory to save the fetched opcode definitions.
                       If None, saves to src/database/data/opcodes/
        """
        if output_dir is None:
            # Navigate to project root and then to data directory
            project_root = Path(__file__).parent.parent.parent
            self.output_dir = project_root / "data" / "opcodes"
        else:
            self.output_dir = Path(output_dir)
            
        logger.debug(f"Output directory: {self.output_dir}")
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define instruction parameter patterns based on RISC-V formats
        self.instruction_formats = {
            # R-Type: rd = rs1 op rs2
            'R': ['rd', 'rs1', 'rs2'],
            # I-Type: rd = rs1 op imm OR rd = mem[rs1 + imm]
            'I': ['rd', 'rs1', 'imm'],
            # S-Type: mem[rs1 + imm] = rs2
            'S': ['rs1', 'rs2', 'imm'],
            # B-Type: if (rs1 op rs2) pc += imm
            'B': ['rs1', 'rs2', 'imm'],
            # U-Type: rd = imm
            'U': ['rd', 'imm'],
            # J-Type: rd = pc+4; pc += imm
            'J': ['rd', 'imm']
        }
        
    def _get_extension_files(self) -> List[Dict]:
        """Get list of extension files from the extensions directory."""
        url = f"{self.BASE_URL}/extensions"
        logger.debug(f"Fetching extension files from: {url}")
        try:
            response = requests.get(url)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            
            if response.status_code == 403:
                logger.error("GitHub API rate limit exceeded. Try again later or use a GitHub token.")
                return []
                
            response.raise_for_status()
            files = response.json()
            logger.debug(f"Found {len(files)} files in extensions directory")
            for file in files:
                logger.debug(f"File: {file.get('name', 'unknown')}")
            return files
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch extension files: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response text: {e.response.text}")
            return []
            
    def _fetch_file_content(self, file_path: str) -> Optional[str]:
        """Fetch raw content of a file from the repository."""
        url = f"{self.RAW_BASE_URL}/{file_path}"
        logger.debug(f"Fetching file content from: {url}")
        try:
            response = requests.get(url)
            logger.debug(f"Response status code: {response.status_code}")
            
            if response.status_code == 403:
                logger.error("GitHub API rate limit exceeded. Try again later or use a GitHub token.")
                return None
                
            response.raise_for_status()
            content = response.text
            logger.debug(f"Fetched {len(content)} bytes of content")
            return content
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch file {file_path}: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response text: {e.response.text}")
            return None
    
    def _determine_instruction_format(self, instruction_name: str, encoding: Dict) -> str:
        """
        Determine the instruction format based on the instruction name and encoding.
        """
        # Known instruction format mappings
        format_mappings = {
            # R-Type instructions
            'add': 'R', 'sub': 'R', 'sll': 'R', 'slt': 'R', 'sltu': 'R', 'xor': 'R',
            'srl': 'R', 'sra': 'R', 'or': 'R', 'and': 'R', 'mul': 'R', 'mulh': 'R',
            'mulhsu': 'R', 'mulhu': 'R', 'div': 'R', 'divu': 'R', 'rem': 'R', 'remu': 'R',
            
            # I-Type instructions
            'addi': 'I', 'slti': 'I', 'sltiu': 'I', 'xori': 'I', 'ori': 'I', 'andi': 'I',
            'slli': 'I', 'srli': 'I', 'srai': 'I', 'lb': 'I', 'lh': 'I', 'lw': 'I',
            'lbu': 'I', 'lhu': 'I', 'jalr': 'I', 'ecall': 'I', 'ebreak': 'I',
            
            # S-Type instructions
            'sb': 'S', 'sh': 'S', 'sw': 'S',
            
            # B-Type instructions
            'beq': 'B', 'bne': 'B', 'blt': 'B', 'bge': 'B', 'bltu': 'B', 'bgeu': 'B',
            
            # U-Type instructions
            'lui': 'U', 'auipc': 'U',
            
            # J-Type instructions
            'jal': 'J'
        }
        
        # Check direct mapping first
        if instruction_name in format_mappings:
            return format_mappings[instruction_name]
        
        # Determine based on encoding fields
        fields = encoding.get('fields', {})
        has_funct7 = 'funct7' in encoding
        has_funct3 = 'funct3' in encoding
        has_opcode = 'opcode' in encoding
        
        # R-Type: has funct7, funct3, opcode (register-to-register operations)
        if has_funct7 and has_funct3 and has_opcode:
            return 'R'
        
        # Check for instruction patterns
        if instruction_name.endswith('i') and instruction_name not in ['lui']:
            return 'I'  # Most immediate instructions
        
        if instruction_name.startswith('l') and len(instruction_name) <= 4:
            return 'I'  # Load instructions
        
        if instruction_name.startswith('s') and len(instruction_name) <= 4:
            return 'S'  # Store instructions
        
        if instruction_name.startswith('b') and instruction_name not in ['beqz', 'bnez']:
            return 'B'  # Branch instructions
        
        # Default fallback
        return 'Unknown'
    
    def _get_parameter_constraints(self, param: str) -> Dict:
        """
        Get parameter constraints for random generation.
        """
        constraints = {
            'rd': {
                'type': 'register',
                'min': 0,
                'max': 31,
                'description': 'Destination register (x0-x31)',
                'exclude': []  # Could exclude x0 for some instructions
            },
            'rs1': {
                'type': 'register', 
                'min': 0,
                'max': 31,
                'description': 'Source register 1 (x0-x31)',
                'exclude': []
            },
            'rs2': {
                'type': 'register',
                'min': 0,
                'max': 31, 
                'description': 'Source register 2 (x0-x31)',
                'exclude': []
            },
            'imm': {
                'type': 'immediate',
                'min': -2048,  # 12-bit signed immediate default
                'max': 2047,
                'description': 'Immediate value',
                'bits': 12
            }
        }
        
        return constraints.get(param, {'type': 'unknown'})

    def _parse_opcode_file(self, content: str) -> Dict:
        """
        Parse an opcode definition file.
        
        The file format is typically:
        inst rd,rs1,rs2 31..25=0x00 14..12=0x0 6..0=0x13
        
        Returns a dictionary with instruction encoding information.
        """
        instructions = {}
        logger.debug(f"Parsing opcode file with {len(content.splitlines())} lines")
        
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            try:
                # Split into instruction and encoding parts
                parts = line.split()
                if not parts:
                    continue
                    
                inst_part = parts[0]
                encoding_parts = parts[1:]
                
                # Parse instruction name and parameters from first part
                # Format could be: "inst" or "inst rd,rs1,rs2" etc.
                inst_name = inst_part
                inst_params = []
                
                # Check if there are parameter specifications in the line
                # Look for patterns like "rd,rs1,rs2" in the instruction part
                if ',' in inst_part or any(param in inst_part for param in ['rd', 'rs1', 'rs2', 'imm']):
                    # Extract parameters from the instruction specification
                    param_match = re.search(r'\s+(.*)', ' '.join(parts))
                    if param_match:
                        param_str = param_match.group(1)
                        # Extract parameter names (rd, rs1, rs2, etc.)
                        param_pattern = r'\b(rd|rs1|rs2|rs3|imm|shamt|csr)\b'
                        inst_params = re.findall(param_pattern, param_str)
                
                logger.debug(f"Parsing instruction: {inst_name} with params: {inst_params} and {len(encoding_parts)} encoding parts")
                
                # Parse the encoding
                encoding = {
                    'fields': {},
                }
                for part in encoding_parts:
                    if '=' in part:
                        bits, value = part.split('=')
                        value_int = int(value, 16)
                        if '..' in bits:
                            msb, lsb = map(int, bits.split('..'))
                            encoding['fields'][f"{msb}..{lsb}"] = value_int
                        else:
                            bit = int(bits)
                            encoding['fields'][str(bit)] = value_int
                
                # Combine fields for opcode, funct3, funct7 if present
                fields = encoding['fields']
                # Opcode: bits 6..0
                if '6..2' in fields and '1..0' in fields:
                    encoding['opcode'] = (fields['6..2'] << 2) | fields['1..0']
                    del fields['6..2']
                    del fields['1..0']
                elif '6..0' in fields:
                    encoding['opcode'] = fields['6..0']
                    del fields['6..0']
                # funct3: bits 14..12
                if '14..12' in fields:
                    encoding['funct3'] = fields['14..12']
                    del fields['14..12']
                # funct7: bits 31..25
                if '31..25' in fields:
                    encoding['funct7'] = fields['31..25']
                    del fields['31..25']
                
                # Determine instruction format
                inst_format = self._determine_instruction_format(inst_name, encoding)
                
                # If no parameters were found in the instruction line, use format defaults
                if not inst_params and inst_format in self.instruction_formats:
                    inst_params = self.instruction_formats[inst_format].copy()
                
                # Add parameter information
                encoding['format'] = inst_format
                encoding['parameters'] = []
                
                for param in inst_params:
                    param_info = {
                        'name': param,
                        'constraints': self._get_parameter_constraints(param)
                    }
                    encoding['parameters'].append(param_info)
                
                # Add assembly template for test generation
                if inst_params:
                    template_params = []
                    for param in inst_params:
                        if param in ['rd', 'rs1', 'rs2', 'rs3']:
                            template_params.append(f"x{{{param}}}")
                        elif param in ['imm', 'shamt']:
                            template_params.append(f"{{{param}}}")
                        else:
                            template_params.append(f"{{{param}}}")
                    
                    encoding['assembly_template'] = f"{inst_name} {', '.join(template_params)}"
                else:
                    encoding['assembly_template'] = inst_name
                
                instructions[inst_name] = encoding
                logger.debug(f"Successfully parsed instruction: {inst_name} with format: {inst_format} and parameters: {[p['name'] for p in encoding['parameters']]}")
                
            except Exception as e:
                logger.warning(f"Failed to parse line {line_num}: {line} - {e}")
                continue
                
        logger.debug(f"Parsed {len(instructions)} instructions")
        return instructions
        
    def fetch_all_opcodes(self) -> Dict[str, Dict]:
        """
        Fetch and parse all opcode definitions.
        
        Returns a dictionary mapping extension names to their instruction encodings.
        """
        all_opcodes = {}
        extension_files = self._get_extension_files()
        
        if not extension_files:
            logger.error("No extension files found!")
            return all_opcodes
            
        for file_info in extension_files:
            # Remove the .txt extension check since files don't have extensions
            extension_name = file_info['name']
            logger.info(f"Fetching opcodes for extension: {extension_name}")
            
            content = self._fetch_file_content(f"extensions/{file_info['name']}")
            if content:
                opcodes = self._parse_opcode_file(content)
                if opcodes:
                    all_opcodes[extension_name] = opcodes
                    
                    # Save individual extension file
                    output_file = self.output_dir / f"{extension_name}.json"
                    with open(output_file, 'w') as f:
                        json.dump(opcodes, f, indent=2)
                    logger.info(f"Saved opcodes for {extension_name} to {output_file}")
                else:
                    logger.warning(f"No opcodes parsed for {extension_name}")
            else:
                logger.warning(f"No content fetched for {extension_name}")
        
        # Save combined opcodes file
        combined_file = self.output_dir / "all_opcodes.json"
        with open(combined_file, 'w') as f:
            json.dump(all_opcodes, f, indent=2)
        logger.info(f"Saved all opcodes to {combined_file}")
        
        return all_opcodes

def main():
    """Main function to fetch and save opcode definitions."""
    logger.info("Starting opcode fetch process")
    fetcher = RiscVOpcodesFetcher()
    opcodes = fetcher.fetch_all_opcodes()
    logger.info(f"Fetch process completed. Found {len(opcodes)} extensions")

if __name__ == "__main__":
    main() 