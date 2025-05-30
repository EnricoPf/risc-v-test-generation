import argparse
import json
import sys
import os
from pathlib import Path

from classifier.profile_classifier import ProfileClassifier

def print_instruction_details(instruction, verbose=False):
    """Pretty print instruction details"""
    print(f"Instruction: {instruction.get('instruction', 'Unknown')}")
    print(f"Type: {instruction.get('type', 'Unknown')}")
    print(f"Hex: {instruction.get('hex', 'Unknown')}")
    print(f"Binary: {instruction.get('binary', 'Unknown')}")
    print(f"Extension: {instruction.get('extension', 'Unknown')}")
    
    if verbose:
        print(f"Opcode: 0x{instruction.get('opcode', 0):02x}")
        print(f"funct3: 0x{instruction.get('funct3', 0):01x}")
        print(f"funct7: 0x{instruction.get('funct7', 0):02x}")
        print(f"rd: x{instruction.get('rd', 0)}")
        print(f"rs1: x{instruction.get('rs1', 0)}")
        print(f"rs2: x{instruction.get('rs2', 0)}")
        
        if "immediate" in instruction:
            print(f"immediate: 0x{instruction['immediate'] & 0xFFFFFFFF:08x}")
    
    if "compatible_profiles" in instruction:
        print("Compatible Profiles:")
        for profile in instruction["compatible_profiles"]:
            print(f"  - {profile}")
    
    print()

def print_summary(result):
    """Print summary of results"""
    print("\n--- Summary ---")
    print("Extensions Used:")
    for ext in result["extensions_used"]:
        print(f"  - {ext}")
    
    print("\nCompatible Profiles:")
    for profile in result["compatible_profiles"]:
        print(f"  - {profile}")

def main():
    parser = argparse.ArgumentParser(description="RISC-V Profile Classifier")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Classify instruction
    instr_parser = subparsers.add_parser("instruction", help="Classify a single instruction")
    instr_parser.add_argument("instruction", help="Hexadecimal instruction value")
    instr_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed information")
    
    # Classify binary file
    bin_parser = subparsers.add_parser("binary", help="Classify a binary file")
    bin_parser.add_argument("file", help="Path to binary file")
    bin_parser.add_argument("-o", "--offset", type=int, default=0, help="Starting offset in the file")
    bin_parser.add_argument("-l", "--limit", type=int, help="Maximum number of instructions to process")
    bin_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed information")
    bin_parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    
    # Classify hex file
    hex_parser = subparsers.add_parser("hexfile", help="Classify a file containing hexadecimal instructions")
    hex_parser.add_argument("file", help="Path to file containing hex instructions")
    hex_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed information")
    hex_parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    
    # List profiles
    profile_parser = subparsers.add_parser("profiles", help="List available profiles")
    profile_parser.add_argument("profile", nargs="?", help="Get details for a specific profile")
    profile_parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize classifier
    classifier = ProfileClassifier()
    
    if args.command == "instruction":
        # Classify a single instruction
        result = classifier.classify_instruction(args.instruction)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return 1
        
        print_instruction_details(result, args.verbose)
    
    elif args.command == "binary":
        # Read binary file
        try:
            with open(args.file, "rb") as f:
                binary_data = f.read()
        except Exception as e:
            print(f"Error: Failed to read file '{args.file}': {str(e)}")
            return 1
        
        # Classify binary data
        result = classifier.classify_binary(binary_data, args.offset)
        
        if args.json:
            # Output as JSON
            print(json.dumps(result, indent=2))
        else:
            # Print each instruction
            for i, instruction in enumerate(result["instructions"]):
                if args.limit and i >= args.limit:
                    break
                
                if "error" in instruction:
                    print(f"Error at offset {instruction.get('offset', 'unknown')}: {instruction['error']}")
                else:
                    print(f"Offset {instruction['offset']}:")
                    print_instruction_details(instruction, args.verbose)
            
            # Print summary
            print_summary(result)
    
    elif args.command == "hexfile":
        # Read hex file
        try:
            with open(args.file, "r") as f:
                hex_content = f.read()
        except Exception as e:
            print(f"Error: Failed to read file '{args.file}': {str(e)}")
            return 1
        
        # Classify hex content
        result = classifier.classify_hex_file(hex_content)
        
        if args.json:
            # Output as JSON
            print(json.dumps(result, indent=2))
        else:
            # Print each instruction
            for instruction in result["instructions"]:
                if "error" in instruction:
                    print(f"Error at line {instruction.get('line', 'unknown')}: {instruction['error']}")
                else:
                    print(f"Line {instruction['line']}:")
                    print_instruction_details(instruction, args.verbose)
            
            # Print summary
            print_summary(result)
    
    elif args.command == "profiles":
        # Get profile database
        profiles_db = classifier.profiles_db
        
        if args.profile:
            # Get details for a specific profile
            profile_details = classifier.get_profile_requirements(args.profile)
            
            if "error" in profile_details:
                print(f"Error: {profile_details['error']}")
                return 1
            
            if args.json:
                # Output as JSON
                print(json.dumps(profile_details, indent=2))
            else:
                # Print profile details
                print(f"Profile: {profile_details['profile']} - {profile_details['name']}")
                print(f"Description: {profile_details['description']}")
                print(f"Base ISA: {profile_details['base']['name']} - {profile_details['base']['description']}")
                
                print("\nMandatory Extensions:")
                for ext in profile_details["mandatory_extensions"]:
                    print(f"  - {ext['name']}: {ext['description']}")
                
                print("\nOptional Extensions:")
                for ext in profile_details["optional_extensions"]:
                    print(f"  - {ext['name']}: {ext['description']}")
        else:
            # List all available profiles
            profiles = profiles_db.get_profiles()
            
            if args.json:
                # Output as JSON
                print(json.dumps(profiles, indent=2))
            else:
                # Print profiles
                print("Available RISC-V Profiles:")
                for profile_name, profile in profiles.items():
                    print(f"  - {profile_name}: {profile['name']}")
                    print(f"    {profile['description']}")
    
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 