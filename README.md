# Framework de Análise e Geração de Testes RISC-V

Um framework completo para analisar conjuntos de instruções RISC-V e gerar casos de teste randomizados com parâmetros válidos.

# Ferramentas Principais

As principais ferramentas estão na pasta `tools/`.

```bash
# Pra gerar código assembly RISC-V com parâmetros aleatórios válidos
python tools/generate_riscv_code.py add sub sll --count 5

# Pra checar se o código assembly RISC-V está correto
python tools/validate_riscv_code.py arquivo_assembly.s

# Pra demonstrar o workflow inteiro
python tools/demo.py
```

### Exemplo de Geração de Código

```bash
# Pra gerar 3 testes pra add sub e addi
python tools/generate_riscv_code.py add sub addi --count 3

# Pra gerar 10 testes com todas as instruções do tipo R
python tools/generate_riscv_code.py --format R --count 10

# Pra salvar na pasta output, use --save-to-output
python tools/generate_riscv_code.py add sub --count 5 --save-to-output

# Pode especificar o nome do arquivo onde quer salvar com --output
python tools/generate_riscv_code.py add --output teste_tipo_i.s
```

### Exemplo de Validação de Código

```bash
# Validação básica
python tools/validate_riscv_code.py codigo_gerado.s

# Validação linha por linha
python tools/validate_riscv_code.py codigo_gerado.s --verbose
```

### Geração de Código (`generate_riscv_code.py`)
-  Gera números de registradores válidos (x0-x31) e valores imediatos corretos
-  Funciona com todos os formatos de instrução RISC-V (R, I, S, B, U, J)
-  Ranges de valores imediatos e requisitos de alinhamento específicos por formato
-  Lista instruções disponíveis para cada formato

### Validação de Código (`validate_riscv_code.py`)
- Análisa ranges de registradores, ranges de valores imediatos, numero de parâmetros
- Validação de restrições específicas do formato da instrução
- Instruções desconhecidas, valores fora do range, tipos incorretos são consideradas error

### Formatos de Instrução Válidos

Aqui estão os tipos de instrução que o framework tem support:

| Formato | Descrição | Parâmetros | Exemplo |
|---------|-----------|------------|---------|
| R-Type | Operações registro-registro | rd, rs1, rs2 | `add x1, x2, x3` |
| I-Type | Operações com imediato | rd, rs1, imm | `addi x1, x2, 100` |
| S-Type | Operações de store | rs1, rs2, imm | `sw x1, 4(x2)` |
| B-Type | Operações de branch | rs1, rs2, imm | `beq x1, x2, 8` |
| U-Type | Imediato superior | rd, imm | `lui x1, 0x10000` |
| J-Type | Operações de jump | rd, imm | `jal x1, 0x1000` |

## Para Instalar

1. **Clone o repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd risc-v-rework
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Inicialize os dados de opcode e profiles**:
   ```bash
   python src/riscv_tools/fetch_opcodes.py
   python src/fetch_riscv_profiles.py
   ```

### Pra gerar testes
```bash
# Gerar casos de teste abrangentes para diferentes formatos
python tools/generate_riscv_code.py --format R --count 50 --save-to-output
python tools/generate_riscv_code.py --format I --count 50 --save-to-output
python tools/generate_riscv_code.py --format B --count 25 --save-to-output
```

### Pra validar código gerado
```bash
# Validar todos os arquivos gerados
for file in output/*.s; do
    echo "Validando $file..."
    python tools/validate_riscv_code.py "$file"
done
```

### Fluxo geral de criação de testes
```bash
# Gerar casos de teste
python tools/generate_riscv_code.py add sub mul div --count 10 --output teste_aritmetica.s

# Validar o código gerado
python tools/validate_riscv_code.py teste_aritmetica.s --verbose

# Usar no seu pipeline de testes
if python tools/validate_riscv_code.py teste_aritmetica.s --quiet; then
    echo "Casos de teste válidos gerados"
    # Continuar com os testes...
else
    echo "Código inválido gerado"
    exit 1
fi
```

## Demo

Para ver tudo funcionando, rode:
```bash
python tools/demo.py
```

Para executar testes específicos:
```bash
python tests/debug_validator.py
python tests/test_validate.py
```
