import struct
import json
import os
from pathlib import Path

class RiscVInstructionParser:
    def __init__(self):
        self.opcodes_db = {}
        self._load_opcodes()
        # Debug: print all loaded extension names
        print(f"[DEBUG] Loaded extension names: {list(self.opcodes_db.keys())}")
    
    def _load_opcodes(self):
        """Load all opcode files from the opcodes directory"""
        opcodes_dir = Path(__file__).parent.parent / "database" / "data" / "opcodes"
        
        # Load all_opcodes.json
        try:
            with open(opcodes_dir / "all_opcodes.json", 'r') as f:
                data = json.load(f)
                
                # Process each extension
                for ext_name, ext_data in data.items():
                    # Extract base extension name (e.g., rv32_i -> I)
                    base_ext = ext_name.split('_')[-1].upper()
                    
                    # Process each instruction in the extension
                    for instr_name, instr_data in ext_data.items():
                        # Skip pseudo-ops and imports
                        if instr_name.startswith('$'):
                            continue
                            
                        # Create instruction entry
                        instr_entry = {
                            'instruction': instr_name,
                            'extension': base_ext,
                            'opcode': instr_data.get('opcode'),
                            'funct3': instr_data.get('funct3'),
                            'funct7': instr_data.get('funct7'),
                            'type': self._determine_instruction_type(instr_data)
                        }
                        
                        # Add to database
                        if base_ext not in self.opcodes_db:
                            self.opcodes_db[base_ext] = []
                        self.opcodes_db[base_ext].append(instr_entry)
                        
        except Exception as e:
            print(f"Warning: Failed to load all_opcodes.json: {e}")
            self.opcodes_db = {}
    
    def _determine_instruction_type(self, instr_data):
        """Determine instruction type based on fields or fallback mapping"""
        fields = instr_data.get('fields', {})
        name = instr_data.get('instruction', '').lower()
        # Fallback mapping for common instructions
        fallback_types = {
            'addi': 'I-Type', 'slti': 'I-Type', 'sltiu': 'I-Type', 'xori': 'I-Type', 'ori': 'I-Type', 'andi': 'I-Type',
            'jalr': 'I-Type', 'lb': 'I-Type', 'lh': 'I-Type', 'lw': 'I-Type', 'lbu': 'I-Type', 'lhu': 'I-Type',
            'slli': 'I-Type', 'srli': 'I-Type', 'srai': 'I-Type',
            'add': 'R-Type', 'sub': 'R-Type', 'sll': 'R-Type', 'slt': 'R-Type', 'sltu': 'R-Type', 'xor': 'R-Type',
            'srl': 'R-Type', 'sra': 'R-Type', 'or': 'R-Type', 'and': 'R-Type',
            'sw': 'S-Type', 'sh': 'S-Type', 'sb': 'S-Type',
            'beq': 'B-Type', 'bne': 'B-Type', 'blt': 'B-Type', 'bge': 'B-Type', 'bltu': 'B-Type', 'bgeu': 'B-Type',
            'lui': 'U-Type', 'auipc': 'U-Type', 'jal': 'J-Type',
        }
        if not fields and name in fallback_types:
            return fallback_types[name]
        # Original logic
        if '31..25' in fields and '14..12' in fields:
            return 'R-Type'
        elif '31..20' in fields and '14..12' in fields:
            return 'I-Type'
        elif '31..25' in fields and '11..7' in fields and '4..0' in fields:
            return 'S-Type'
        elif '31..25' in fields and '11..8' in fields and '4..1' in fields:
            return 'B-Type'
        elif '31..12' in fields:
            return 'U-Type'
        elif '31..21' in fields and '20' in fields and '10..1' in fields:
            return 'J-Type'
        elif '15..13' in fields and '1..0' in fields:
            return 'C-Type'
        else:
            return 'Unknown'
    
    def parse_hex(self, instruction_hex):
        """Parse a hexadecimal instruction string"""
        try:
            # Convert hex string to integer
            instr_int = int(instruction_hex, 16)
            return self.parse_binary(instr_int)
        except ValueError as e:
            return {"error": f"Invalid hexadecimal instruction: {e}"}
    
    def parse_binary(self, instruction_int):
        """Parse a binary instruction (as integer)"""
        # Extract opcode (bits 0-6)
        opcode = instruction_int & 0x7F
        
        # Always extract funct3 and funct7 as integers
        funct3 = (instruction_int >> 12) & 0x7
        funct7 = (instruction_int >> 25) & 0x7F
        
        # Debug print: show extracted fields
        print(f"[DEBUG] Parsed instruction: 0x{instruction_int:08x} opcode={opcode} funct3={funct3} funct7={funct7}")
        
        # Debug print: show loaded opcodes for each extension
        for ext in self.opcodes_db:
            print(f"[DEBUG] Searching extension: {ext}")
            for instr in self.opcodes_db[ext]:
                print(f"  {instr['instruction']}: opcode={instr.get('opcode')} funct3={instr.get('funct3')} funct7={instr.get('funct7')}")
        
        # Extract register fields
        rd = (instruction_int >> 7) & 0x1F
        rs1 = (instruction_int >> 15) & 0x1F
        rs2 = (instruction_int >> 20) & 0x1F
        
        # Try to find matching instruction in opcodes database
        instruction_info = None
        extension = None
        
        # Search through all extensions
        for ext, opcodes in self.opcodes_db.items():
            for instr in opcodes:
                if (instr.get('opcode') == opcode and 
                    (instr.get('funct3') is None or instr.get('funct3') == funct3) and
                    (instr.get('funct7') is None or instr.get('funct7') == funct7)):
                    instruction_info = instr
                    extension = ext
                    break
            if instruction_info:
                break
        
        if not instruction_info:
            return {
                "error": "Unknown instruction",
                "opcode": opcode,
                "funct3": funct3,
                "funct7": funct7,
                "rd": rd,
                "rs1": rs1,
                "rs2": rs2,
                "hex": f"{instruction_int:08x}",
                "binary": f"{instruction_int:032b}",
                "extension": "Unknown"
            }
        
        # Set the type field using the improved _determine_instruction_type method
        instr_type = instruction_info.get('type')
        if not instr_type or instr_type == 'Unknown':
            instr_type = self._determine_instruction_type(instruction_info)
        
        # Build instruction details
        result = {
            "instruction": instruction_info.get('instruction', 'Unknown'),
            "type": instr_type,
            "opcode": opcode,
            "funct3": funct3,
            "funct7": funct7,
            "rd": rd,
            "rs1": rs1,
            "rs2": rs2,
            "hex": f"{instruction_int:08x}",
            "binary": f"{instruction_int:032b}",
            "extension": extension
        }
        
        return result

    def get_instruction_extension(self, instruction_name):
        """Get the extension for a given instruction name"""
        # Search through all extensions
        for ext, opcodes in self.opcodes_db.items():
            for instr in opcodes:
                if instr.get('instruction') == instruction_name:
                    return ext
        
            return "Unknown Extension" 