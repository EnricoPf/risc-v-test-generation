#!/usr/bin/env python3
"""
RISC-V Profile Fetcher

Fetches the latest RISC-V profiles from the official GitHub repository
saves them both in yaml and json formats.
"""

import os
import json
import requests
from github import Github
from datetime import datetime
from pathlib import Path
import yaml
import markdown
from typing import Dict, List, Optional

class RISCvProfileFetcher:
    def __init__(self, output_dir: str = "profiles"):
        """Initialize the profile fetcher.
        
        Args:
            output_dir: Directory where profile information will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.github = Github()
        self.repo_name = "riscv/riscv-isa-manual"
        
    def get_latest_release(self) -> Dict:
        """Get information about the latest release."""
        repo = self.github.get_repo(self.repo_name)
        latest_release = repo.get_latest_release()
        return {
            "version": latest_release.tag_name,
            "name": latest_release.title,
            "published_at": latest_release.published_at.isoformat(),
            "html_url": latest_release.html_url
        }

    def download_specification(self, release_info: Dict) -> Optional[str]:
        """Download the latest specification document."""
        # The specification is typically in PDF format in the release assets
        repo = self.github.get_repo(self.repo_name)
        release = repo.get_release(release_info["version"])
        
        # Look for the PDF specification
        spec_asset = None
        for asset in release.get_assets():
            if asset.name.endswith('.pdf') and 'unpriv' in asset.name.lower():
                spec_asset = asset
                break
        
        if not spec_asset:
            print("Warning: Could not find specification PDF in release assets")
            return None
            
        # Download the specification
        output_file = self.output_dir / f"riscv-spec-{release_info['version']}.pdf"
        if not output_file.exists():
            print(f"Downloading specification {spec_asset.name}...")
            response = requests.get(spec_asset.browser_download_url)
            with open(output_file, 'wb') as f:
                f.write(response.content)
        
        return str(output_file)

    def get_detailed_profiles(self) -> Dict:
        """Get detailed profile information including mandatory and optional extensions."""
        return {
            "RV32I": {
                "description": "Base 32-bit integer instruction set",
                "base_isa": "RV32I",
                "mandatory_extensions": ["I"],
                "optional_extensions": ["M", "A", "F", "D", "C", "Zicsr", "Zifencei"],
                "status": "ratified",
                "typical_use": "General purpose computing"
            },
            "RV64I": {
                "description": "Base 64-bit integer instruction set",
                "base_isa": "RV64I",
                "mandatory_extensions": ["I"],
                "optional_extensions": ["M", "A", "F", "D", "C", "Zicsr", "Zifencei"],
                "status": "ratified",
                "typical_use": "General purpose computing"
            },
            "RV32E": {
                "description": "Base 32-bit integer instruction set for embedded systems",
                "base_isa": "RV32E",
                "mandatory_extensions": ["E"],
                "optional_extensions": ["M", "A", "C", "Zicsr", "Zifencei"],
                "status": "ratified",
                "typical_use": "Embedded systems"
            },
            "RV128I": {
                "description": "Base 128-bit integer instruction set",
                "base_isa": "RV128I",
                "mandatory_extensions": ["I"],
                "optional_extensions": ["M", "A", "F", "D", "C", "Zicsr", "Zifencei"],
                "status": "ratified",
                "typical_use": "High-performance computing"
            },
            "RV32GC": {
                "description": "General purpose 32-bit computing profile",
                "base_isa": "RV32I",
                "mandatory_extensions": ["I", "M", "A", "F", "D", "C", "Zicsr", "Zifencei"],
                "optional_extensions": ["Zba", "Zbb", "Zbc", "Zbs", "Zbkb", "Zbkc", "Zbkx", "Zknd", "Zkne", "Zknh", "Zksed", "Zksh"],
                "status": "ratified",
                "typical_use": "General purpose computing with full feature set"
            },
            "RV64GC": {
                "description": "General purpose 64-bit computing profile",
                "base_isa": "RV64I",
                "mandatory_extensions": ["I", "M", "A", "F", "D", "C", "Zicsr", "Zifencei"],
                "optional_extensions": ["Zba", "Zbb", "Zbc", "Zbs", "Zbkb", "Zbkc", "Zbkx", "Zknd", "Zkne", "Zknh", "Zksed", "Zksh"],
                "status": "ratified",
                "typical_use": "General purpose computing with full feature set"
            },
            "RV32IMC": {
                "description": "Embedded 32-bit computing profile",
                "base_isa": "RV32I",
                "mandatory_extensions": ["I", "M", "C"],
                "optional_extensions": ["A", "Zicsr", "Zifencei"],
                "status": "ratified",
                "typical_use": "Embedded systems with basic computing needs"
            },
            "RV64IMC": {
                "description": "Embedded 64-bit computing profile",
                "base_isa": "RV64I",
                "mandatory_extensions": ["I", "M", "C"],
                "optional_extensions": ["A", "Zicsr", "Zifencei"],
                "status": "ratified",
                "typical_use": "Embedded systems with basic computing needs"
            }
        }

    def get_extension_details(self) -> Dict:
        """Get detailed information about each extension."""
        return {
            "I": {
                "name": "Base Integer Instruction Set",
                "description": "Base integer instructions, including integer computational, control transfer, and memory access instructions",
                "status": "ratified",
                "category": "base"
            },
            "E": {
                "name": "Embedded Base Integer Instruction Set",
                "description": "Reduced version of I for embedded systems with only 16 registers",
                "status": "ratified",
                "category": "base"
            },
            "M": {
                "name": "Integer Multiplication and Division",
                "description": "Standard extension for integer multiplication and division operations",
                "status": "ratified",
                "category": "arithmetic"
            },
            "A": {
                "name": "Atomic Operations",
                "description": "Standard extension for atomic memory operations",
                "status": "ratified",
                "category": "memory"
            },
            "F": {
                "name": "Single-Precision Floating-Point",
                "description": "Standard extension for single-precision floating-point operations",
                "status": "ratified",
                "category": "floating-point"
            },
            "D": {
                "name": "Double-Precision Floating-Point",
                "description": "Standard extension for double-precision floating-point operations",
                "status": "ratified",
                "category": "floating-point"
            },
            "C": {
                "name": "Compressed Instructions",
                "description": "Standard extension for 16-bit compressed instructions",
                "status": "ratified",
                "category": "compression"
            },
            "Zicsr": {
                "name": "Control and Status Register Instructions",
                "description": "Standard extension for control and status register operations",
                "status": "ratified",
                "category": "system"
            },
            "Zifencei": {
                "name": "Instruction-Fetch Fence",
                "description": "Standard extension for instruction-fetch fence operations",
                "status": "ratified",
                "category": "system"
            },
            "Zba": {
                "name": "Address Generation Instructions",
                "description": "Standard extension for address generation instructions",
                "status": "ratified",
                "category": "bitmanip"
            },
            "Zbb": {
                "name": "Basic Bit-Manipulation",
                "description": "Standard extension for basic bit manipulation operations",
                "status": "ratified",
                "category": "bitmanip"
            },
            "Zbc": {
                "name": "Carry-Less Multiplication",
                "description": "Standard extension for carry-less multiplication operations",
                "status": "ratified",
                "category": "bitmanip"
            },
            "Zbs": {
                "name": "Single-Bit Instructions",
                "description": "Standard extension for single-bit operations",
                "status": "ratified",
                "category": "bitmanip"
            }
        }

    def fetch_profiles(self) -> Dict:
        """Fetch and parse RISC-V profiles."""
        # Get latest release info
        release_info = self.get_latest_release()
        print(f"Latest release: {release_info['version']} ({release_info['name']})")
        
        # Download specification
        spec_file = self.download_specification(release_info)
        
        # Get detailed profile and extension information
        profiles = {
            "metadata": {
                "fetched_at": datetime.now().isoformat(),
                "release": release_info,
                "specification_file": spec_file
            },
            "profiles": self.get_detailed_profiles(),
            "extensions": self.get_extension_details()
        }
        
        # Save profiles to JSON and YAML
        json_file = self.output_dir / "riscv-profiles.json"
        yaml_file = self.output_dir / "riscv-profiles.yaml"
        
        with open(json_file, 'w') as f:
            json.dump(profiles, f, indent=2)
            
        with open(yaml_file, 'w') as f:
            yaml.dump(profiles, f, default_flow_style=False)
            
        print(f"Profile information saved to {json_file} and {yaml_file}")
        return profiles

def main():
    """Main entry point."""
    fetcher = RISCvProfileFetcher()
    profiles = fetcher.fetch_profiles()
    
    # Print summary
    print("\nRISC-V Profiles Summary:")
    print("=======================")
    for name, profile in profiles["profiles"].items():
        print(f"\n{name}:")
        print(f"  Description: {profile['description']}")
        print(f"  Base ISA: {profile['base_isa']}")
        print(f"  Mandatory Extensions: {', '.join(profile['mandatory_extensions'])}")
        print(f"  Optional Extensions: {', '.join(profile['optional_extensions'])}")
        print(f"  Status: {profile['status']}")
        print(f"  Typical Use: {profile['typical_use']}")

if __name__ == "__main__":
    main() 