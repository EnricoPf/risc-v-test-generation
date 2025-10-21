import os
import re
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RiscVValidator:
    """
    Validates RISC-V assembly at line and file level with:
      - Syntactic checks (mnemonic and operands)
      - Semantic checks (register ranges, immediate ranges/alignments)
      - Optional compilation using riscv32-unknown-elf-as
    """

    def __init__(self, enable_compile: bool = False, march: str = "rv32gc"):
        self.enable_compile = enable_compile
        self.march = march
        self.available_instructions = set()
        self.instr_format_map: Dict[str, str] = {}
        self._load_instruction_db()

    # ----------------------------- Public API ----------------------------- #
    def validate_assembly_line(self, line: str, line_number: int = 0) -> Dict:
        original_line = line
        line = self._strip_comments(line).strip()

        if not line:
            return {
                "type": "Empty",
                "valid": True,
                "instruction": None,
                "parameters": None,
                "errors": [],
                "warnings": []
            }

        mnemonic, operands = self._parse_line(line)
        errors: List[str] = []
        warnings: List[str] = []

        if mnemonic is None:
            return {
                "type": "Unknown",
                "valid": False,
                "instruction": None,
                "parameters": None,
                "errors": [f"Linha {line_number}: sintaxe inválida"],
                "warnings": []
            }

        # Check mnemonic existence (allow labels like "_start:")
        if mnemonic.endswith(":"):
            return {
                "type": "Label",
                "valid": True,
                "instruction": mnemonic[:-1],
                "parameters": [],
                "errors": [],
                "warnings": []
            }

        if mnemonic not in self.available_instructions:
            # Allow pseudo like "li", "mv" as warning (assembler will check)
            if mnemonic in {"li", "mv", "nop", "la"}:
                warnings.append("Instrução pseudônima; validação parcial")
            else:
                errors.append(f"Instrução desconhecida: {mnemonic}")

        inst_type = self._determine_format(mnemonic)
        param_errors, param_warnings = self._validate_operands(mnemonic, operands, inst_type)
        errors.extend(param_errors)
        warnings.extend(param_warnings)

        return {
            "type": inst_type if inst_type else "Unknown",
            "valid": len(errors) == 0,
            "instruction": mnemonic,
            "parameters": operands,
            "errors": errors,
            "warnings": warnings
        }

    def validate_assembly_file(self, file_path: str) -> Dict:
        resolved_path = self._resolve_assembly_path(file_path)
        if not resolved_path.exists():
            raise FileNotFoundError(f"Assembly file not found: {file_path}")

        errors: List[Tuple[int, str]] = []
        warnings: List[Tuple[int, str]] = []
        instruction_lines = 0
        valid_instructions = 0

        with open(resolved_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for idx, line in enumerate(lines, start=1):
            result = self.validate_assembly_line(line, idx)
            if result["type"] not in ("Empty", "Label"):
                instruction_lines += 1
            if result["valid"] and result["type"] not in ("Empty", "Label"):
                valid_instructions += 1
            for e in result["errors"]:
                errors.append((idx, e))
            for w in result["warnings"]:
                warnings.append((idx, w))

        compiled_ok = None
        compile_output = None
        if self.enable_compile and errors == []:
            compiled_ok, compile_output = self._compile_with_gas(resolved_path, lines)

        return {
            "valid": len(errors) == 0 and (compiled_ok is not False),
            "total_lines": len(lines),
            "instruction_lines": instruction_lines,
            "valid_instructions": valid_instructions,
            "errors": [f"L{ln}: {msg}" for ln, msg in errors],
            "warnings": [f"L{ln}: {msg}" for ln, msg in warnings],
            "compiled": compiled_ok,
            "compile_output": compile_output,
            "file": str(resolved_path)
        }

    def print_validation_report(self, results: Dict, verbose: bool = False) -> None:
        print("Validation Report")
        print("=================")
        print(f"File: {results.get('file', '')}")
        print(f"Valid: {results['valid']}")
        print(f"Lines (total/instructions/valid): {results['total_lines']}/{results['instruction_lines']}/{results['valid_instructions']}")
        if results.get("compiled") is not None:
            print(f"Compiled: {results['compiled']}")
        if verbose:
            if results["errors"]:
                print("\nErrors:")
                for e in results["errors"]:
                    print(f"  - {e}")
            if results["warnings"]:
                print("\nWarnings:")
                for w in results["warnings"]:
                    print(f"  - {w}")
            if results.get("compile_output"):
                print("\nAssembler output:")
                print(results["compile_output"])

    # ---------------------------- Internal logic -------------------------- #
    def _load_instruction_db(self) -> None:
        """
        Populate available_instructions from opcode JSONs. Prefer the checked-in
        path under src/database/data/opcodes/all_opcodes.json, fallback to src/data/opcodes.
        Also set heuristic format map for common instructions.
        """
        project_dir = Path(__file__).parent
        candidates = [
            project_dir / "database" / "data" / "opcodes" / "all_opcodes.json",
            project_dir / "data" / "opcodes" / "all_opcodes.json",
        ]

        for path in candidates:
            try:
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Collect instruction names across all extensions
                    for _ext, instrs in data.items():
                        for name in instrs.keys():
                            if not name.startswith("$"):
                                self.available_instructions.add(name)
                    break
            except Exception:
                continue

        # Heuristic format map similar to fetcher logic
        r_type = {
            'add','sub','sll','slt','sltu','xor','srl','sra','or','and',
            'mul','mulh','mulhsu','mulhu','div','divu','rem','remu'
        }
        i_type = {
            'addi','slti','sltiu','xori','ori','andi','slli','srli','srai',
            'lb','lh','lw','lbu','lhu','jalr','ecall','ebreak'
        }
        s_type = {'sb','sh','sw'}
        b_type = {'beq','bne','blt','bge','bltu','bgeu'}
        u_type = {'lui','auipc'}
        j_type = {'jal'}

        for n in self.available_instructions:
            base = n.split('.')[0]  # strip compressed qualifiers if any
            if base in r_type:
                self.instr_format_map[n] = 'R-Type'
            elif base in i_type:
                self.instr_format_map[n] = 'I-Type'
            elif base in s_type:
                self.instr_format_map[n] = 'S-Type'
            elif base in b_type:
                self.instr_format_map[n] = 'B-Type'
            elif base in u_type:
                self.instr_format_map[n] = 'U-Type'
            elif base in j_type:
                self.instr_format_map[n] = 'J-Type'

    def _strip_comments(self, line: str) -> str:
        # Support '#' style comments
        if '#' in line:
            return line.split('#', 1)[0]
        return line

    def _parse_line(self, line: str) -> Tuple[Optional[str], List[str]]:
        # Remove leading/trailing spaces
        line = line.strip()
        if not line:
            return None, []
        # Labels
        if line.endswith(":") and re.match(r"^[A-Za-z_$.][\w$.]*:$", line):
            return line, []
        # Directives like .text, .globl
        if line.startswith('.'):
            return "Directive", [line]
        # Parse mnemonic and operands
        parts = re.split(r"\s+", line, maxsplit=1)
        mnemonic = parts[0]
        operands_str = parts[1] if len(parts) > 1 else ""
        # split by commas respecting simple immediates
        operands = [op.strip() for op in operands_str.split(',') if op.strip()]
        return mnemonic, operands

    def _determine_format(self, mnemonic: str) -> str:
        if mnemonic in ("Directive",):
            return "Directive"
        if mnemonic in self.instr_format_map:
            return self.instr_format_map[mnemonic]
        base = mnemonic.split('.')[0]
        # Heuristics consistent with fetcher
        if base.endswith('i') and base not in {'lui'}:
            return 'I-Type'
        if base.startswith('l') and len(base) <= 4:
            return 'I-Type'
        if base.startswith('s') and len(base) <= 4:
            return 'S-Type'
        if base.startswith('b') and base not in {'beqz','bnez'}:
            return 'B-Type'
        return 'Unknown'

    def _validate_operands(self, mnemonic: str, operands: List[str], inst_type: str) -> Tuple[List[str], List[str]]:
        errors: List[str] = []
        warnings: List[str] = []

        # Expected operand counts by type (simplified)
        expected = {
            'R-Type': 3,   # rd, rs1, rs2
            'I-Type': 3,   # rd, rs1, imm  (or rd, imm for some pseudo)
            'S-Type': 3,   # rs2, rs1, imm  (store syntax varies by assembler; we accept 3)
            'B-Type': 3,   # rs1, rs2, imm
            'U-Type': 2,   # rd, imm
            'J-Type': 2,   # rd, imm
        }

        if inst_type in expected:
            if len(operands) != expected[inst_type]:
                # Some assemblers allow whitespace-only lines or directives; already filtered
                warnings.append(f"Número de operandos esperado para {inst_type}: {expected[inst_type]}")

        # Validate register and immediate constraints
        def is_reg(token: str) -> bool:
            return re.fullmatch(r"x([0-9]|[12][0-9]|3[01])", token) is not None

        def parse_imm(token: str) -> Optional[int]:
            try:
                if token.startswith('0x') or token.startswith('0X'):
                    return int(token, 16)
                return int(token, 0)
            except ValueError:
                return None

        # Helper to check ranges
        def check_reg(tok: str, role: str) -> None:
            if not is_reg(tok):
                errors.append(f"Operando {role} inválido: '{tok}' (esperado x0..x31)")
            else:
                if role == 'rd' and tok == 'x0':
                    warnings.append("rd = x0 (resultado será descartado)")

        # Attempt role assignment by type
        if inst_type == 'R-Type' and len(operands) >= 3:
            check_reg(operands[0], 'rd')
            check_reg(operands[1], 'rs1')
            check_reg(operands[2], 'rs2')

        elif inst_type == 'I-Type' and len(operands) >= 3:
            check_reg(operands[0], 'rd')
            check_reg(operands[1], 'rs1')
            imm = parse_imm(operands[2])
            if imm is None:
                errors.append(f"Imediato inválido: '{operands[2]}'")
            else:
                if imm < -2048 or imm > 2047:
                    warnings.append("Imediato fora do intervalo típico de 12 bits (-2048..2047)")

        elif inst_type == 'S-Type' and len(operands) >= 3:
            # Store syntax can be 'sw rs2, imm(rs1)' or 'sw rs2, rs1, imm'. Try both.
            if re.match(r"^-?\d+\(x\d+\)$", operands[1]):
                # rs2, imm(rs1)
                check_reg(operands[0], 'rs2')
                m = re.match(r"^(?P<imm>-?\d+)\((?P<rs1>x\d+)\)$", operands[1])
                if m:
                    check_reg(m.group('rs1'), 'rs1')
                    imm_val = parse_imm(m.group('imm'))
                    if imm_val is None:
                        errors.append(f"Imediato inválido: '{operands[1]}'")
                # third operand ignored in this form if present
            else:
                check_reg(operands[0], 'rs2')
                check_reg(operands[1], 'rs1')
                imm = parse_imm(operands[2])
                if imm is None:
                    errors.append(f"Imediato inválido: '{operands[2]}'")

        elif inst_type == 'B-Type' and len(operands) >= 3:
            check_reg(operands[0], 'rs1')
            check_reg(operands[1], 'rs2')
            imm = parse_imm(operands[2])
            if imm is None:
                errors.append(f"Imediato inválido: '{operands[2]}'")
            else:
                if imm % 2 != 0:
                    warnings.append("Imediato de branch idealmente par (múltiplo de 2)")

        elif inst_type == 'U-Type' and len(operands) >= 2:
            check_reg(operands[0], 'rd')
            imm = parse_imm(operands[1])
            if imm is None:
                errors.append(f"Imediato inválido: '{operands[1]}'")

        elif inst_type == 'J-Type' and len(operands) >= 2:
            check_reg(operands[0], 'rd')
            imm = parse_imm(operands[1])
            if imm is None:
                errors.append(f"Imediato inválido: '{operands[1]}'")
            else:
                if imm % 2 != 0:
                    warnings.append("Imediato de jump idealmente par (múltiplo de 2)")

        return errors, warnings

    def _resolve_assembly_path(self, file_path: str) -> Path:
        p = Path(file_path)
        if p.exists():
            return p
        # Try relative to src/assembly when running from src/
        base = Path(__file__).parent
        candidate = base / "assembly" / file_path
        if candidate.exists():
            return candidate
        return p

    def _compile_with_gas(self, asm_path: Path, lines: List[str]) -> Tuple[Optional[bool], Optional[str]]:
        # Check if assembler is available
        assembler = shutil.which("riscv32-unknown-elf-as")
        if assembler is None:
            return None, "Assembler 'riscv32-unknown-elf-as' não encontrado no PATH"

        temp_dir = Path(tempfile.mkdtemp(prefix="riscv_validate_"))
        try:
            temp_asm = temp_dir / "temp.s"
            content = "".join(lines)
            # If file lacks a section directive, wrap minimally
            needs_wrap = not any(l.strip().startswith('.') for l in lines)
            if needs_wrap:
                wrapped = [
                    ".section .text\n",
                    ".globl _start\n",
                    "_start:\n",
                ]
                wrapped.append(content)
                content = "".join(wrapped)
            with open(temp_asm, "w", encoding="utf-8") as f:
                f.write(content)

            temp_obj = temp_dir / "temp.o"
            cmd = [assembler, f"-march={self.march}", "-o", str(temp_obj), str(temp_asm)]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ok = proc.returncode == 0
            output = (proc.stdout or "") + (proc.stderr or "")
            return ok, output
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


__all__ = ["RiscVValidator"]


