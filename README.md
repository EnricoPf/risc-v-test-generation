# RISC-V Analysis and Test Generation Framework

A comprehensive framework for analyzing RISC-V instruction sets and generating randomized test cases with valid parameters.

## 🚀 Quick Start

### Main Tools

The primary tools are located in the `tools/` directory:

```bash
# Generate RISC-V assembly code with random valid parameters
python tools/generate_riscv_code.py add sub sll --count 5

# Validate RISC-V assembly code for correctness
python tools/validate_riscv_code.py assembly_file.s

# See complete workflow demonstration
python tools/demo.py
```

### Generate Code Examples

```bash
# Generate specific instructions
python tools/generate_riscv_code.py add sub addi --count 3

# Generate all R-type instructions
python tools/generate_riscv_code.py --format R --count 10

# Save to output folder with auto-generated filename
python tools/generate_riscv_code.py add sub --count 5 --save-to-output

# Generate and save to specific file
python tools/generate_riscv_code.py --format I --count 20 --output test_i_type.s
```

### Validate Code Examples

```bash
# Basic validation
python tools/validate_riscv_code.py generated_code.s

# Detailed validation with line-by-line analysis
python tools/validate_riscv_code.py generated_code.s --verbose

# Validate from stdin
cat assembly_code.s | python tools/validate_riscv_code.py --stdin
```

## 📁 Project Structure

```
risc-v-rework/
├── README.md                    # This file - main project overview
├── requirements.txt             # Python dependencies
│
├── tools/                       # 🔧 Main executable scripts
│   ├── generate_riscv_code.py   # Generate RISC-V assembly with random parameters
│   ├── validate_riscv_code.py   # Validate RISC-V assembly for correctness
│   └── demo.py                  # Complete workflow demonstration
│
├── src/                         # 📚 Core library modules
│   ├── riscv_tools/            # RISC-V tools library
│   │   ├── __init__.py
│   │   ├── test_generator.py    # Random test case generation
│   │   ├── fetch_opcodes.py     # Opcode fetching and processing
│   │   └── profiles.py          # RISC-V instruction profiles
│   ├── parser/                  # Instruction parsing (existing)
│   ├── classifier/              # Instruction classification (existing)
│   └── main.py                  # Main application (existing)
│
├── data/                        # 📊 Data files
│   └── opcodes/                 # RISC-V opcode definitions (JSON)
│
├── tests/                       # 🧪 Test files and debugging tools
│   ├── debug_validator.py       # Validator debugging script
│   ├── test_validate.py         # Validation testing
│   └── *.s                      # Test assembly files
│
├── output/                      # 📁 Generated output files
│   └── (auto-created when using --save-to-output)
│
├── docs/                        # 📖 Documentation
│   └── tools_README.md          # Detailed tools documentation
│
└── examples/                    # 📝 Example files and usage samples
```

## 🛠️ Features

### Code Generation (`generate_riscv_code.py`)
- ✅ **Random Parameter Generation**: Generates valid register numbers (x0-x31) and immediate values
- ✅ **Format-Specific Support**: All RISC-V instruction formats (R, I, S, B, U, J)
- ✅ **Constraint Compliance**: Format-specific immediate ranges and alignment requirements
- ✅ **Flexible Output**: Console output, file output, or auto-organized output folder
- ✅ **Instruction Discovery**: List available instructions by format

### Code Validation (`validate_riscv_code.py`)
- ✅ **Syntax Validation**: Proper instruction format parsing
- ✅ **Parameter Checking**: Register ranges, immediate ranges, parameter counts
- ✅ **Format Compliance**: Instruction format-specific constraint validation
- ✅ **Error Detection**: Unknown instructions, out-of-range values, type mismatches
- ✅ **Detailed Reporting**: Line-by-line analysis with verbose output

### Supported Instruction Formats

| Format | Description | Parameters | Example |
|--------|-------------|------------|---------|
| R-Type | Register-register operations | rd, rs1, rs2 | `add x1, x2, x3` |
| I-Type | Immediate operations | rd, rs1, imm | `addi x1, x2, 100` |
| S-Type | Store operations | rs1, rs2, imm | `sw x1, 4(x2)` |
| B-Type | Branch operations | rs1, rs2, imm | `beq x1, x2, 8` |
| U-Type | Upper immediate | rd, imm | `lui x1, 0x10000` |
| J-Type | Jump operations | rd, imm | `jal x1, 0x1000` |

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd risc-v-rework
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize opcode data** (if needed):
   ```bash
   python src/riscv_tools/fetch_opcodes.py
   ```

## 📊 Usage Workflows

### 1. Generate Test Suite
```bash
# Generate comprehensive test cases for different formats
python tools/generate_riscv_code.py --format R --count 50 --save-to-output
python tools/generate_riscv_code.py --format I --count 50 --save-to-output
python tools/generate_riscv_code.py --format B --count 25 --save-to-output
```

### 2. Validate Generated Code
```bash
# Validate all generated files
for file in output/*.s; do
    echo "Validating $file..."
    python tools/validate_riscv_code.py "$file"
done
```

### 3. Development Pipeline
```bash
# Generate test cases
python tools/generate_riscv_code.py add sub mul div --count 10 --output test_arithmetic.s

# Validate the generated code
python tools/validate_riscv_code.py test_arithmetic.s --verbose

# Use in your testing pipeline
if python tools/validate_riscv_code.py test_arithmetic.s --quiet; then
    echo "✅ Generated valid test cases"
    # Proceed with testing...
else
    echo "❌ Generated invalid code"
    exit 1
fi
```

## 🧪 Testing

Run the demo to see all functionality:
```bash
python tools/demo.py
```

Run specific tests:
```bash
python tests/debug_validator.py
python tests/test_validate.py
```

## 📚 Documentation

- **[Tools Documentation](docs/tools_README.md)**: Detailed documentation for code generation and validation tools
- **[Examples](examples/)**: Usage examples and sample files
- **[API Reference](src/riscv_tools/)**: Core library documentation

## 🤝 Contributing

1. Add new features to the appropriate directory (`tools/` for scripts, `src/riscv_tools/` for libraries)
2. Add tests to the `tests/` directory
3. Update documentation in the `docs/` directory
4. Follow the organized structure for maintainability

## 📈 Roadmap

- [ ] Support for RISC-V vector extensions
- [ ] Integration with RISC-V simulators
- [ ] Performance benchmarking tools
- [ ] Web interface for code generation
- [ ] Custom instruction set support

---

**Previous Structure**: All files were in `src/database/` making it hard to find main tools  
**New Structure**: Clear separation of tools, libraries, data, tests, and documentation 