# RISC-V Profile Analyzer

This project analyzes RISC-V binary or hexadecimal code to:
1. Interpret opcodes and determine which instructions are being used
2. Identify which RISC-V extensions the instructions belong to
3. Classify which RISC-V profiles could run the analyzed code

## Project Structure

```
.
├── src/
│   ├── parser/              # RISC-V instruction parsing
│   ├── database/            # RISC-V profiles and extensions data
│   │   ├── data/            # JSON files with extension and profile data
│   │   │   ├── extensions.json  # RISC-V extensions database
│   │   │   └── profiles.json    # RISC-V profiles database
│   ├── classifier/          # Profile compatibility classifier
│   └── main.py              # CLI interface
├── examples/                # Example RISC-V code
└── tests/                   # Test cases
```

## Features

- Parse RISC-V binary and hexadecimal instructions
- Identify instruction types, operands, and immediates
- Map instructions to their respective RISC-V extensions
- Determine which RISC-V profiles are compatible with the analyzed code
- Complete database of RISC-V extensions and profiles stored in JSON files
- Support for adding custom extensions and profiles

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/risc-v-profile-analyzer.git
cd risc-v-profile-analyzer

# Install dependencies (if any)
pip install -r requirements.txt
```

## Usage

### Analyzing a Single Instruction

```bash
python src/main.py instruction 0x00500513
```

### Analyzing a Binary File

```bash
python src/main.py binary path/to/binary/file -v
```

### Analyzing a File with Hexadecimal Instructions

```bash
python src/main.py hexfile path/to/hexfile -v
```

### Listing All Available Profiles

```bash
python src/main.py profiles
```

### Getting Details for a Specific Profile

```bash
python src/main.py profiles RVA20
```

### JSON Output

Add `-j` or `--json` flag to get output in JSON format:

```bash
python src/main.py instruction 0x00500513 --json
```

## RISC-V Profiles

The project includes comprehensive information about RISC-V profiles, categorized as:

- **Application Profiles**: RVA20, RVA22
- **General Purpose Profiles**: RVG20, RVG22
- **Integer-only Profiles**: RVI20, RVI22
- **Embedded Profiles**: RVE20, RVE22, RV64E20, RV32IM, RV32EM, RV64IM
- **Specialized Profiles**: RVB23, RVZ23, RVP23, RVV23
- **Classic Profiles**: RV32G, RV64G, RV32IMAC, RV64IMAC, RV32IMAFC, RV64IMAFC

## RISC-V Extensions

The analyzer supports all RISC-V extensions:

- **Base ISA**: RV32I, RV64I, RV128I, RV32E, RV64E
- **Standard Extensions**: M, A, F, D, G, Q, L, C, B, J, T, P, V, N, H, S, U
- **Specialized "Z" Extensions**: Zifencei, Zicsr, and many more
- **Supervisor Extensions**: Svpbmt, Svnapot, Svinval
- **Hypervisor Extensions**: Sstc, Smstateen, Smepmp

## Customizing Extensions and Profiles

All extensions and profiles are stored in JSON files for easy modification:

- **Extensions**: `src/database/data/extensions.json`
- **Profiles**: `src/database/data/profiles.json`

You can add, modify, or remove extensions and profiles by editing these files or by using the API methods:

```python
from src.database.risc_v_profiles import RiscVProfiles

# Create database instance
db = RiscVProfiles()

# Add a new extension
db.add_extension("Znew", "New custom extension")

# Add a new profile
db.add_profile("CUSTOM1", {
    "name": "Custom Profile",
    "description": "My custom RISC-V profile",
    "base": "RV64I",
    "mandatory": ["M", "C"],
    "optional": ["A", "F"]
})

# Save changes to files
db.save_extensions()
db.save_profiles()
```

## Example

Here's an example output for analyzing the instruction `0x00500513`:

```
Instruction: ADDI
Type: I-Type
Hex: 0x00500513
Binary: 00000000010100000101000100010011
Extension: RV32I

Compatible Profiles:
  - RVA20
  - RVA22
  - RVG20
  - RVG22
  - RVI20
  - RVI22
  - RV32IM
  - RV64IM
  - RVB23
  - RVZ23
  - RVP23
  - RVV23
  - RV32G
  - RV64G
  - RV32IMAC
  - RV64IMAC
  - RV32IMAFC
  - RV64IMAFC
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- Your Name <your.email@example.com>

## Acknowledgments

- RISC-V Foundation for the ISA specification
- RISC-V International for the profile specifications 