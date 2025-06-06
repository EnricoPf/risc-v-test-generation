# Framework de Análise e Geração de Testes RISC-V

Um framework completo para analisar conjuntos de instruções RISC-V e gerar casos de teste randomizados com parâmetros válidos.

## 🚀 Começando Rapidamente

### Ferramentas Principais

As principais ferramentas estão na pasta `tools/`. É bem simples de usar:

```bash
# Gerar código assembly RISC-V com parâmetros aleatórios válidos
python tools/generate_riscv_code.py add sub sll --count 5

# Validar a correção do código assembly RISC-V
python tools/validate_riscv_code.py arquivo_assembly.s

# Ver demonstração completa do workflow
python tools/demo.py
```

### Exemplos de Geração de Código

```bash
# Gerar instruções específicas
python tools/generate_riscv_code.py add sub addi --count 3

# Gerar todas as instruções do tipo R
python tools/generate_riscv_code.py --format R --count 10

# Salvar na pasta output com nome de arquivo gerado automaticamente
python tools/generate_riscv_code.py add sub --count 5 --save-to-output

# Gerar e salvar em arquivo específico
python tools/generate_riscv_code.py --format I --count 20 --output teste_tipo_i.s
```

### Exemplos de Validação de Código

```bash
# Validação básica
python tools/validate_riscv_code.py codigo_gerado.s

# Validação detalhada com análise linha por linha
python tools/validate_riscv_code.py codigo_gerado.s --verbose

# Validar a partir da entrada padrão
cat codigo_assembly.s | python tools/validate_riscv_code.py --stdin
```

## 📁 Estrutura do Projeto

Organizamos tudo de forma bem clara para você não se perder:

```
risc-v-rework/
├── README.md                    # Este arquivo - visão geral do projeto
├── requirements.txt             # Dependências do Python
│
├── tools/                       # 🔧 Scripts principais que você vai usar
│   ├── generate_riscv_code.py   # Gera assembly RISC-V com parâmetros aleatórios
│   ├── validate_riscv_code.py   # Valida se o código assembly está correto
│   └── demo.py                  # Demonstração completa do workflow
│
├── src/                         # 📚 Módulos de biblioteca principal
│   ├── riscv_tools/            # Biblioteca de ferramentas RISC-V
│   │   ├── __init__.py
│   │   ├── test_generator.py    # Geração de casos de teste aleatórios
│   │   ├── fetch_opcodes.py     # Busca e processamento de opcodes
│   │   └── profiles.py          # Perfis de instruções RISC-V
│   ├── parser/                  # Análise de instruções (já existia)
│   ├── classifier/              # Classificação de instruções (já existia)
│   └── main.py                  # Aplicação principal (já existia)
│
├── data/                        # 📊 Arquivos de dados
│   └── opcodes/                 # Definições de opcodes RISC-V (JSON)
│
├── tests/                       # 🧪 Arquivos de teste e ferramentas de debug
│   ├── debug_validator.py       # Script de debug do validador
│   ├── test_validate.py         # Testes de validação
│   └── *.s                      # Arquivos de teste assembly
│
├── output/                      # 📁 Arquivos gerados automaticamente
│   └── (criado automaticamente quando usar --save-to-output)
│
├── docs/                        # 📖 Documentação
│   └── tools_README.md          # Documentação detalhada das ferramentas
│
└── examples/                    # 📝 Exemplos de uso e arquivos de amostra
```

## 🛠️ O Que Este Framework Faz

### Geração de Código (`generate_riscv_code.py`)
- ✅ **Parâmetros Aleatórios Inteligentes**: Gera números de registradores válidos (x0-x31) e valores imediatos corretos
- ✅ **Suporte a Todos os Formatos**: Funciona com todos os formatos de instrução RISC-V (R, I, S, B, U, J)
- ✅ **Respeitando Restrições**: Ranges de valores imediatos e requisitos de alinhamento específicos por formato
- ✅ **Saída Flexível**: Console, arquivo, ou pasta organizada automaticamente
- ✅ **Descoberta de Instruções**: Lista instruções disponíveis por formato

### Validação de Código (`validate_riscv_code.py`)
- ✅ **Validação de Sintaxe**: Análise adequada do formato das instruções
- ✅ **Verificação de Parâmetros**: Ranges de registradores, ranges de valores imediatos, contagem de parâmetros
- ✅ **Conformidade de Formato**: Validação de restrições específicas do formato da instrução
- ✅ **Detecção de Erros**: Instruções desconhecidas, valores fora do range, tipos incorretos
- ✅ **Relatórios Detalhados**: Análise linha por linha com saída verbosa

### Formatos de Instrução Suportados

Aqui estão os tipos de instrução que o framework entende:

| Formato | Descrição | Parâmetros | Exemplo |
|---------|-----------|------------|---------|
| R-Type | Operações registro-registro | rd, rs1, rs2 | `add x1, x2, x3` |
| I-Type | Operações com imediato | rd, rs1, imm | `addi x1, x2, 100` |
| S-Type | Operações de store | rs1, rs2, imm | `sw x1, 4(x2)` |
| B-Type | Operações de branch | rs1, rs2, imm | `beq x1, x2, 8` |
| U-Type | Imediato superior | rd, imm | `lui x1, 0x10000` |
| J-Type | Operações de jump | rd, imm | `jal x1, 0x1000` |

## 🔧 Como Instalar

É bem tranquilo de configurar:

1. **Clone o repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd risc-v-rework
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Inicialize os dados de opcode** (se necessário):
   ```bash
   python src/riscv_tools/fetch_opcodes.py
   ```

## 📊 Fluxos de Trabalho Úteis

### 1. Gerar Suíte de Testes Completa
```bash
# Gerar casos de teste abrangentes para diferentes formatos
python tools/generate_riscv_code.py --format R --count 50 --save-to-output
python tools/generate_riscv_code.py --format I --count 50 --save-to-output
python tools/generate_riscv_code.py --format B --count 25 --save-to-output
```

### 2. Validar Código Gerado
```bash
# Validar todos os arquivos gerados
for file in output/*.s; do
    echo "Validando $file..."
    python tools/validate_riscv_code.py "$file"
done
```

### 3. Pipeline de Desenvolvimento
```bash
# Gerar casos de teste
python tools/generate_riscv_code.py add sub mul div --count 10 --output teste_aritmetica.s

# Validar o código gerado
python tools/validate_riscv_code.py teste_aritmetica.s --verbose

# Usar no seu pipeline de testes
if python tools/validate_riscv_code.py teste_aritmetica.s --quiet; then
    echo "✅ Casos de teste válidos gerados"
    # Continuar com os testes...
else
    echo "❌ Código inválido gerado"
    exit 1
fi
```

## 🧪 Testando

Para ver tudo funcionando, rode a demonstração:
```bash
python tools/demo.py
```

Para executar testes específicos:
```bash
python tests/debug_validator.py
python tests/test_validate.py
```

## 📚 Documentação

- **[Documentação das Ferramentas](docs/tools_README.md)**: Documentação detalhada para ferramentas de geração e validação de código
- **[Exemplos](examples/)**: Exemplos de uso e arquivos de amostra
- **[Referência da API](src/riscv_tools/)**: Documentação da biblioteca principal

## 🤝 Como Contribuir

Se você quiser ajudar a melhorar o projeto:

1. Adicione novas funcionalidades no diretório apropriado (`tools/` para scripts, `src/riscv_tools/` para bibliotecas)
2. Adicione testes no diretório `tests/`
3. Atualize a documentação no diretório `docs/`
4. Siga a estrutura organizada para manter tudo arrumado

## 📈 Planos Futuros

Ideias para deixar o framework ainda melhor:

- [ ] Suporte para extensões vetoriais RISC-V
- [ ] Integração com simuladores RISC-V
- [ ] Ferramentas de benchmark de performance
- [ ] Interface web para geração de código
- [ ] Suporte a conjuntos de instruções customizados

---

**Como Era Antes**: Todos os arquivos estavam em `src/database/`, dificultando encontrar as ferramentas principais  
**Como Está Agora**: Separação clara de ferramentas, bibliotecas, dados, testes e documentação

**💡 Dica**: Comece testando com `python tools/demo.py` para ver tudo funcionando! 