import requests
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

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
            self.output_dir = Path(__file__).parent / "data" / "opcodes"
        else:
            self.output_dir = Path(output_dir)
            
        logger.debug(f"Output directory: {self.output_dir}")
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
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
                    
                inst = parts[0]
                encoding_parts = parts[1:]
                logger.debug(f"Parsing instruction: {inst} with {len(encoding_parts)} encoding parts")
                
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
                instructions[inst] = encoding
                logger.debug(f"Successfully parsed instruction: {inst}")
                
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