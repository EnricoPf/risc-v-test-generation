# RISC-V Code Generation and Validation Tools

This directory contains tools for generating and validating RISC-V assembly code with randomized parameters.

## Scripts

### 1. `generate_riscv_code.py` - Code Generator

Generates valid RISC-V assembly code with randomized valid parameter values.

#### Usage Examples:

```bash
# Generate code for specific instructions
python3 generate_riscv_code.py add sub sll

# Generate multiple instances per instruction
python3 generate_riscv_code.py add sub --count 5

# Generate code for all R-type instructions
python3 generate_riscv_code.py --format R --count 10

# Save to file
python3 generate_riscv_code.py add sub sll --output test_code.s

# List available instructions
python3 generate_riscv_code.py --list-instructions

# List instructions by format
python3 generate_riscv_code.py --list-by-format
```

#### Features:
- Random but valid parameter generation
- Support for all RISC-V instruction formats (R, I, S, B, U, J)
- Format-specific constraints (register ranges, immediate ranges)
- Assembly template formatting
- Instruction format classification

### 2. `validate_riscv_code.py` - Code Validator

Validates RISC-V assembly code for syntax and constraint compliance.

#### Usage Examples:

```bash
# Validate assembly file
python3 validate_riscv_code.py test_code.s

# Validate with verbose output
python3 validate_riscv_code.py test_code.s --verbose

# Validate from stdin
cat assembly_code.s | python3 validate_riscv_code.py --stdin

# Output validation results to JSON
python3 validate_riscv_code.py test_code.s --json-output results.json

# Quiet mode (only show valid/invalid)
python3 validate_riscv_code.py test_code.s --quiet
```

#### Validation Features:
- Instruction name validation
- Parameter count verification
- Register range validation (x0-x31)
- Immediate value range checking per format
- Format-specific constraint validation
- Detailed error and warning reporting

### 3. `demo.py` - Demonstration Script

Shows complete workflow of generation and validation.

```bash
python3 demo.py
```

## Instruction Format Support

The tools support all standard RISC-V instruction formats:

- **R-Type**: Three register operands (rd, rs1, rs2)
- **I-Type**: Two registers + immediate (rd, rs1, imm)
- **S-Type**: Two registers + immediate for stores (rs1, rs2, imm)
- **B-Type**: Two registers + immediate for branches (rs1, rs2, imm)
- **U-Type**: One register + 20-bit immediate (rd, imm)
- **J-Type**: One register + 20-bit immediate for jumps (rd, imm)

## Parameter Constraints

### Registers
- Valid range: x0-x31
- Special handling for x0 (zero register) warnings

### Immediates
- **I-Type/S-Type**: 12-bit signed (-2048 to 2047)
- **B-Type**: 12-bit signed, must be even (branch alignment)
- **U-Type**: 20-bit unsigned (0 to 1048575)
- **J-Type**: 20-bit signed, must be even (jump alignment)

## Integration Examples

### Generate Test Suite
```bash
# Generate comprehensive test cases
python3 generate_riscv_code.py --format R --count 50 --output r_type_tests.s
python3 generate_riscv_code.py --format I --count 50 --output i_type_tests.s
```

### Validate Generated Code
```bash
# Validate and get detailed report
python3 validate_riscv_code.py r_type_tests.s --verbose
python3 validate_riscv_code.py i_type_tests.s --json-output validation_results.json
```

### Pipeline Integration
```bash
#!/bin/bash
# Generate and validate in one pipeline
python3 generate_riscv_code.py add sub sll addi lui --count 10 --output test.s
if python3 validate_riscv_code.py test.s --quiet; then
    echo "✅ Generated valid test cases"
    # Run additional tests...
else
    echo "❌ Generated invalid code"
    exit 1
fi
```

## Output Examples

### Generated Code
```assembly
# Generated RISC-V Assembly Code
# Instructions: add, sub, sll

# add instructions
add x23, x11, x11
    # Parameters: rd=23, rs1=11, rs2=11
add x23, x3, x2
    # Parameters: rd=23, rs1=3, rs2=2

# sub instructions
sub x13, x21, x31
    # Parameters: rd=13, rs1=21, rs2=31
```

### Validation Report
```
=== RISC-V Code Validation Report ===
Source: test_code.s
Total lines: 15
Instruction lines: 6
Valid instructions: 6
Overall result: ✓ VALID
```

## Error Detection

The validator detects:
- Unknown instruction names
- Invalid register numbers (> x31)
- Out-of-range immediate values
- Wrong parameter types (register vs immediate)
- Format-specific constraint violations

## Dependencies

- Python 3.6+
- `test_generator.py` (opcode database interface)
- RISC-V opcode data in `data/opcodes/all_opcodes.json`

## Notes

- The tools use the enhanced opcode database created by `fetch_opcodes.py`
- All generated parameters are guaranteed to be within valid ranges
- Validation is based on standard RISC-V specification constraints
- Both tools support extensive logging and debugging options 