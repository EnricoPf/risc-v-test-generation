import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.instruction_parser import RiscVInstructionParser
from database.risc_v_profiles import RiscVProfiles

class ProfileClassifier:
    def __init__(self):
        self.parser = RiscVInstructionParser()
        self.profiles_db = RiscVProfiles()
    
    def classify_instruction(self, instruction_hex):
        """
        Classify a single instruction and determine which profiles can run it
        
        Args:
            instruction_hex: Hexadecimal instruction string
            
        Returns:
            Dictionary with instruction details and compatible profiles
        """
        # Parse the instruction
        instruction = self.parser.parse_hex(instruction_hex)
        
        if "error" in instruction:
            return {"error": instruction["error"]}
        
        # Get the extension for this instruction
        extension = self.parser.get_instruction_extension(instruction["instruction"])
        instruction["extension"] = extension
        
        # Find compatible profiles
        compatible_profiles = self.profiles_db.get_compatible_profiles([extension])
        instruction["compatible_profiles"] = compatible_profiles
        
        return instruction
    
    def classify_binary(self, binary_data, offset=0):
        """
        Classify a binary file and determine which profiles can run it
        
        Args:
            binary_data: Bytes object containing the binary data
            offset: Starting offset in the binary data
            
        Returns:
            Dictionary with all instructions, extensions used, and compatible profiles
        """
        instructions = []
        extensions_used = set()
        
        # Process 4 bytes at a time (32-bit instructions)
        for i in range(offset, len(binary_data), 4):
            if i + 4 <= len(binary_data):
                # Extract 4 bytes and convert to int
                instr_bytes = binary_data[i:i+4]
                instr_int = int.from_bytes(instr_bytes, byteorder='little')
                
                # Parse the instruction
                instruction = self.parser.parse_binary(instr_int)
                
                if "error" in instruction:
                    instruction["offset"] = i
                    instructions.append(instruction)
                    continue
                
                # Get the extension
                extension = self.parser.get_instruction_extension(instruction["instruction"])
                instruction["extension"] = extension
                
                # Store instruction info
                instruction["offset"] = i
                instructions.append(instruction)
                
                # Track used extensions
                if extension != "Unknown Extension":
                    extensions_used.add(extension)
        
        # Find compatible profiles for all instructions
        compatible_profiles = self.profiles_db.get_compatible_profiles(list(extensions_used))
        
        return {
            "instructions": instructions,
            "extensions_used": list(extensions_used),
            "compatible_profiles": compatible_profiles
        }
    
    def classify_hex_file(self, hex_content):
        """
        Classify a file containing hexadecimal instructions
        
        Args:
            hex_content: String containing hexadecimal instructions
            
        Returns:
            Dictionary with all instructions, extensions used, and compatible profiles
        """
        instructions = []
        extensions_used = set()
        
        # Split content into lines and process each line
        lines = hex_content.strip().split('\n')
        for line_num, line in enumerate(lines):
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Remove any comments and whitespace
            if '#' in line:
                line = line.split('#')[0].strip()
            
            # Process the line as hexadecimal
            try:
                # Parse the instruction
                instruction = self.parser.parse_hex(line)
                
                if "error" in instruction:
                    instruction["line"] = line_num + 1
                    instructions.append(instruction)
                    continue
                
                # Get the extension
                extension = self.parser.get_instruction_extension(instruction["instruction"])
                instruction["extension"] = extension
                
                # Store instruction info
                instruction["line"] = line_num + 1
                instructions.append(instruction)
                
                # Track used extensions
                if extension != "Unknown Extension":
                    extensions_used.add(extension)
            except Exception as e:
                instructions.append({
                    "error": f"Failed to parse line {line_num + 1}: {str(e)}",
                    "line": line_num + 1
                })
        
        # Find compatible profiles for all instructions
        compatible_profiles = self.profiles_db.get_compatible_profiles(list(extensions_used))
        
        return {
            "instructions": instructions,
            "extensions_used": list(extensions_used),
            "compatible_profiles": compatible_profiles
        }
    
    def get_profile_requirements(self, profile_name):
        """
        Get the requirements for a specific profile
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Dictionary with profile details and extension information
        """
        profile = self.profiles_db.get_profile_details(profile_name)
        if not profile:
            return {"error": f"Profile {profile_name} not found"}
        
        # Get details for each extension
        base_details = self.profiles_db.get_extension_details(profile["base"])
        
        mandatory_extensions = []
        for ext in profile["mandatory"]:
            ext_details = self.profiles_db.get_extension_details(ext)
            mandatory_extensions.append({
                "name": ext,
                "description": ext_details if ext_details else "Unknown extension"
            })
        
        optional_extensions = []
        for ext in profile["optional"]:
            ext_details = self.profiles_db.get_extension_details(ext)
            optional_extensions.append({
                "name": ext,
                "description": ext_details if ext_details else "Unknown extension"
            })
        
        return {
            "profile": profile_name,
            "name": profile["name"],
            "description": profile["description"],
            "base": {
                "name": profile["base"],
                "description": base_details if base_details else "Unknown base ISA"
            },
            "mandatory_extensions": mandatory_extensions,
            "optional_extensions": optional_extensions
        } 