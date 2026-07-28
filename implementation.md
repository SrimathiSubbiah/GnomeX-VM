# GenomeX VM — Implementation Roadmap

---

## Project Vision

Create a reverse engineering CTF where DNA is not biological data.
Instead, DNA represents the instruction set of a fictional virtual CPU.

Players must reverse engineer the GenomeX Virtual Machine by understanding its architecture
and executing a DNA program to recover the encryption key.

---

## Technical Requirements

| Requirement | Value |
|---|---|
| Language | Python 3.8+ |
| External Dependencies | None (stdlib only) |
| Data Structures | dict (registers), list (memory), list (program) |
| Encoding | UTF-8 for `.dna` files, raw bytes for `.bin` files |

---

## Overall Architecture

```
program.dna
        │
        ▼
 GenomeX Emulator
        │
        ▼
 Decode DNA Codons → Binary
        │
        ▼
 Execute Instructions
        │
        ▼
 Modify Registers / Memory
        │
        ▼
 Read memory.bin
        │
        ▼
 Recover Encryption Key
        │
        ▼
 Decrypt vault.zip
        │
        ▼
 Flag: expX{...}
```

---

## Phase 1 — CPU Design

### Registers

| Register | Size | Purpose |
|---|---|---|
| R0 | 8-bit | General purpose / accumulator |
| R1 | 8-bit | General purpose |
| R2 | 8-bit | General purpose |
| R3 | 8-bit | General purpose / stack pointer (optional) |

All registers are 8-bit unsigned (0x00–0xFF).

### Flags

| Flag | Purpose |
|---|---|
| Zero (Z) | Set when ALU result is 0x00 |
| Carry (C) | Set when ALU result exceeds 0xFF |

### Program Counter

| Register | Size | Behavior |
|---|---|---|
| PC | 16-bit | Points to current instruction index. Increments by 1 after each fetch. Jump instructions modify PC directly. |

### Stack Pointer (Optional)

Only required if PUSH/POP instructions are implemented.
If implemented, SP starts at 0xFF and decrements on PUSH, increments on POP.

### Memory

| Region | Address Range | Size | Purpose |
|---|---|---|---|
| Program | 0x00–0x3F | 64 bytes | DNA program (read-only at runtime) |
| Constants | 0x40–0x7F | 64 bytes | Lookup tables, constants |
| Encrypted Key | 0x80–0xBF | 64 bytes | Encrypted key bytes |
| Scratch | 0xC0–0xFF | 64 bytes | Runtime scratch memory |

Total: 256 bytes. Represented by `memory.bin`.

**Done when:**
- [x] Register count and width defined
- [x] Flag behavior specified
- [x] Memory layout documented with address ranges
- [x] PC behavior documented

---

## Phase 2 — Instruction Set Architecture

### DNA Codon Encoding

Each DNA base maps to 2 bits:

| Base | Binary |
|---|---|
| A | 00 |
| C | 01 |
| G | 10 |
| T | 11 |

Each instruction is **3 codons** (9 bases = 18 bits).
Only 16 bits are used; the remaining 2 bits are padding (set to 0).

### Bit Layout

```
Codon 1    Codon 2    Codon 3
┌─────────┬─────────┬─────────┐
│ opcode  │dst src  │ immediate │
│ 4 bits  │2 bits   │ 8 bits    │
│         │2 bits   │           │
│         │pad 2bits│           │
└─────────┴─────────┴─────────┘
 6 bits    6 bits    6 bits
```

| Field | Bits | Description |
|---|---|---|
| Opcode | 4 | Instruction identifier (0x0–0xF) |
| Dst | 2 | Destination register index (0–3) |
| Src | 2 | Source register index (0–3) |
| Immediate | 8 | Literal value or address |
| Padding | 2 | Reserved, set to 0 |

### Opcode Table

| Opcode | Binary | DNA Codon | Instruction | Operand Type |
|---|---|---|---|---|
| 0x0 | 0000 | AAA | NOP | None |
| 0x1 | 0001 | AAC | LOAD | Dst, Immediate |
| 0x2 | 0010 | AAG | STORE | Src, Immediate |
| 0x3 | 0011 | AAT | MOV | Dst, Src |
| 0x4 | 0100 | ACA | ADD | Dst, Src |
| 0x5 | 0101 | ACC | SUB | Dst, Src |
| 0x6 | 0110 | ACG | XOR | Dst, Src |
| 0x7 | 0111 | ACT | AND | Dst, Src |
| 0x8 | 1000 | AGA | OR | Dst, Src |
| 0x9 | 1001 | AGC | CMP | Dst, Src |
| 0xA | 1010 | AGG | JMP | Immediate (address) |
| 0xB | 1011 | AGT | JZ | Immediate (address) |
| 0xC | 1100 | ATA | PUSH | Src |
| 0xD | 1101 | ATC | POP | Dst |
| 0xE | 1110 | ATG | PRINT | Dst |
| 0xF | 1111 | ATT | HALT | None |

### Instruction Encoding Examples

**LOAD R1, [0xFF] (load from memory address)**

```
Opcode:  0001 (LOAD)
Dst:     01   (R1)
Src:     00   (unused)
Imm:     11111111 (0xFF)
Pad:     00

Binary:  0001 01 00 11111111 00
Split:   000101 | 001111 | 111100
Bases:   ACC     ATT      TGA

DNA:     ACC ATT TGA
```

**ADD R0, R1 (register to register)**

```
Opcode:  0100 (ADD)
Dst:     00   (R0)
Src:     01   (R1)
Imm:     00000000 (unused)
Pad:     00

Binary:  0100 00 01 00000000 00
Split:   010000 | 010000 | 000000
Bases:   ACA     ACA      AAA

DNA:     ACA ACA AAA
```

**JMP 0x10 (jump to address)**

```
Opcode:  1010 (JMP)
Dst:     00   (unused)
Src:     00   (unused)
Imm:     00010000 (0x10)
Pad:     00

Binary:  1010 00 00 00010000 00
Split:   101000 | 000001 | 000000
Bases:   GAA     AAA      AAA

DNA:     GAA AAA AAA
```

**HALT**

```
Opcode:  1111 (HALT)
Dst:     00
Src:     00
Imm:     00000000
Pad:     00

Binary:  1111 00 00 00000000 00
Split:   111100 | 000000 | 000000
Bases:   TGA      AAA      AAA

DNA:     TGA AAA AAA
```

### Instruction Semantics

| Instruction | Operation | Flags Affected |
|---|---|---|
| NOP | No operation | None |
| LOAD Rd, addr | Rd ← mem[addr] | None |
| STORE Rs, addr | mem[addr] ← Rs | None |
| MOV Rd, Rs | Rd ← Rs | None |
| ADD Rd, Rs | Rd ← Rd + Rs | Z, C |
| SUB Rd, Rs | Rd ← Rd - Rs | Z, C |
| XOR Rd, Rs | Rd ← Rd ^ Rs | Z |
| AND Rd, Rs | Rd ← Rd & Rs | Z |
| OR Rd, Rs | Rd ← Rd \| Rs | Z |
| CMP Rd, Rs | Set flags on Rd - Rs (discard result) | Z, C |
| JMP addr | PC ← addr | None |
| JZ addr | If Z=1 then PC ← addr | None |
| PUSH Rs | mem[SP] ← Rs; SP-- | None |
| POP Rd | SP++; Rd ← mem[SP] | None |
| PRINT Rd | Output Rd value (stdout or memory) | None |
| HALT | Stop execution | None |

**Done when:**
- [x] All 16 opcodes defined with binary values
- [x] DNA codon mapping documented
- [x] Bit layout specified with field widths
- [x] Encoding examples provided for each instruction type
- [x] Instruction semantics and flag behavior defined

---

## Phase 3 — Instruction Format (Detailed)

Every instruction is exactly 3 codons (9 DNA bases).

```
[opcode_3bases] [dst_src_2bases+pad_1base] [imm_4bases+pad_2bases]
```

### Encoding Rules

1. Every instruction is exactly 9 bases long (3 codons)
2. First 3 bases encode the opcode
3. Next 2 bases encode destination register (2 bits)
4. Next 1 base encodes source register high bit + padding
5. Last 3 bases encode immediate low bits + padding
6. Unused fields are zero-filled

### Register Encoding

| Register | Binary |
|---|---|
| R0 | 00 |
| R1 | 01 |
| R2 | 10 |
| R3 | 11 |

### Validation

The assembler and emulator must validate:
- DNA string length is a multiple of 9
- All characters are A, C, G, or T
- Register indices are 0–3
- Immediate values fit in 8 bits (0x00–0xFF)
- Jump targets are within program bounds

**Done when:**
- [x] Encoding rules documented
- [x] Register encoding table complete
- [x] Validation rules specified

---

## Phase 4 — Emulator

Create `emulator.py`.

### Responsibilities

1. Read `program.dna`
2. Split into 9-base chunks (instructions)
3. Decode each instruction from DNA to binary
4. Execute instruction
5. Update registers
6. Update flags
7. Increment Program Counter (or jump)
8. Repeat until HALT

### Data Structures

```python
registers = {"R0": 0, "R1": 0, "R2": 0, "R3": 0}
flags = {"Z": False, "C": False}
memory = [0] * 256
program = []          # list of DNA instruction strings
pc = 0                # program counter
running = True        # False after HALT
```

### Pseudocode

```python
def fetch():
    return program[pc]

def decode(codon_str):
    opcode = dna_to_bits(codon_str[0:3])
    dst    = dna_to_bits(codon_str[3:5])
    src    = dna_to_bits(codon_str[5:7])
    imm    = dna_to_bits(codon_str[7:9])
    return opcode, dst, src, imm

def execute(opcode, dst, src, imm):
    global pc, running

    if opcode == 0x0:  # NOP
        pass
    elif opcode == 0x1:  # LOAD
        addr = imm & 0xFF
        registers[f"R{dst}"] = memory[addr]
    elif opcode == 0x2:  # STORE
        memory[imm] = registers[f"R{src}"]
    elif opcode == 0x3:  # MOV
        registers[f"R{dst}"] = registers[f"R{src}"]
    elif opcode == 0x4:  # ADD
        result = registers[f"R{dst}"] + registers[f"R{src}"]
        flags["C"] = result > 0xFF
        registers[f"R{dst}"] = result & 0xFF
        flags["Z"] = registers[f"R{dst}"] == 0
    elif opcode == 0x5:  # SUB
        result = registers[f"R{dst}"] - registers[f"R{src}"]
        flags["C"] = result < 0
        registers[f"R{dst}"] = result & 0xFF
        flags["Z"] = registers[f"R{dst}"] == 0
    elif opcode == 0x6:  # XOR
        registers[f"R{dst}"] ^= registers[f"R{src}"]
        flags["Z"] = registers[f"R{dst}"] == 0
    elif opcode == 0x7:  # AND
        registers[f"R{dst}"] &= registers[f"R{src}"]
        flags["Z"] = registers[f"R{dst}"] == 0
    elif opcode == 0x8:  # OR
        registers[f"R{dst}"] |= registers[f"R{src}"]
        flags["Z"] = registers[f"R{dst}"] == 0
    elif opcode == 0x9:  # CMP
        result = registers[f"R{dst}"] - registers[f"R{src}"]
        flags["C"] = result < 0
        flags["Z"] = (result & 0xFF) == 0
    elif opcode == 0xA:  # JMP
        pc = imm
        return  # skip pc += 1
    elif opcode == 0xB:  # JZ
        if flags["Z"]:
            pc = imm
            return  # skip pc += 1
    elif opcode == 0xC:  # PUSH
        memory[0xC0 + registers["R3"]] = registers[f"R{src}"]
        registers["R3"] = (registers["R3"] - 1) & 0xFF
    elif opcode == 0xD:  # POP
        registers["R3"] = (registers["R3"] + 1) & 0xFF
        registers[f"R{dst}"] = memory[0xC0 + registers["R3"]]
    elif opcode == 0xE:  # PRINT
        print(registers[f"R{dst}"])
    elif opcode == 0xF:  # HALT
        running = False
        return

    pc += 1

def run():
    load_memory("memory.bin")
    while running:
        instruction = fetch()
        opcode, dst, src, imm = decode(instruction)
        execute(opcode, dst, src, imm)
```

### CLI Interface

```
python emulator.py program.dna memory.bin
```

**Done when:**
- [x] All 16 instructions execute correctly
- [x] Flags update after arithmetic operations
- [x] Jumps modify PC correctly
- [x] Memory read/write works within bounds
- [x] HALT stops execution
- [x] CLI accepts program.dna and memory.bin arguments

---

## Phase 5 — Assembler

Create `assembler.py`.

### Input

Assembly text file (one instruction per line):

```
LOAD R0, 0x41
LOAD R1, 0x42
ADD R0, R1
STORE R0, 0x80
HALT
```

### Output

DNA text file:

```
ACCAAAAAAAACCAAAAAAAACACAAAAAAAAACCTGAAAAAAAAA
```

(9 bases per instruction, no spaces in output)

### Assembly Syntax

| Instruction | Syntax | Example |
|---|---|---|
| NOP | `NOP` | `NOP` |
| LOAD | `LOAD Rd, imm` | `LOAD R0, 0x41` |
| STORE | `STORE Rs, addr` | `STORE R0, 0x80` |
| MOV | `MOV Rd, Rs` | `MOV R0, R1` |
| ADD | `ADD Rd, Rs` | `ADD R0, R1` |
| SUB | `SUB Rd, Rs` | `SUB R0, R1` |
| XOR | `XOR Rd, Rs` | `XOR R0, R1` |
| AND | `AND Rd, Rs` | `AND R0, R1` |
| OR | `OR Rd, Rs` | `OR R0, R1` |
| CMP | `CMP Rd, Rs` | `CMP R0, R1` |
| JMP | `JMP addr` | `JMP 0x05` |
| JZ | `JZ addr` | `JZ 0x05` |
| PUSH | `PUSH Rs` | `PUSH R0` |
| POP | `POP Rd` | `POP R0` |
| PRINT | `PRINT Rd` | `PRINT R0` |
| HALT | `HALT` | `HALT` |

### Encoding Process

```
Assembly → Tokenize → Resolve Labels → Encode Binary → Convert to DNA → Output
```

### CLI Interface

```
python assembler.py input.asm output.dna
```

### Round-Trip Test

Assembling the same program and then disassembling it must produce the original assembly (ignoring comments and whitespace).

**Done when:**
- [x] All 16 instructions assemble correctly
- [x] Register parsing works (R0–R3)
- [x] Immediate parsing works (decimal, 0x hex)
- [x] Output is valid DNA (only A, C, G, T)
- [x] Output length is multiple of 9
- [x] Round-trip test passes

---

## Phase 6 — Compiler (Optional)

Create `compiler.py`.

### Purpose

Convert high-level constructs to assembly. Not required for the challenge.
Useful for generating complex test programs.

### Pipeline

```
High-level language → Assembly → DNA
```

### Notes

- Can be a simple macro expander
- No need for full parser or type system
- Focus on loops, conditionals, and arithmetic

---

## Phase 7 — Challenge Files

### File List

| File | Purpose |
|---|---|
| `README.md` | Challenge description and rules |
| `architecture.pdf` | GenomeX CPU architecture reference (deliberately incomplete) |
| `genome_manual.txt` | Partial ISA documentation (has gaps players must deduce) |
| `program.dna` | The DNA program to execute |
| `memory.bin` | Initial memory state (contains encrypted key) |
| `vault.zip` | Encrypted archive containing the flag |

### Documentation Design

The `genome_manual.txt` should describe:
- Register model (complete)
- Memory layout (complete)
- Instruction format (partially — some fields redacted or ambiguous)
- Opcode table (incomplete — missing 2–3 entries)
- Example programs (1–2 working examples)

Players must deduce missing opcodes by:
1. Analyzing the provided example programs
2. Understanding the encoding pattern
3. Filling in the gaps through logical inference

**Done when:**
- [x] All challenge files created
- [x] Manual has deliberate gaps (not too many, not too few)
- [x] Example programs are correct and solvable
- [x] Vault.zip encryption/decryption works

---

## Phase 8 — Story

### Narrative

GenomeX Laboratories developed the world's first DNA-based secure computation engine.
Instead of storing software in binary, programs are encoded using synthetic DNA.

During a cyber attack, one GenomeX program became corrupted.
The only remaining artifact is the encoded DNA program.

Your objective is to reconstruct the GenomeX Virtual Machine and execute the recovered DNA program.

### Player Briefing

```
CLASSIFIED — GenomeX Incident Report

During the breach on [DATE], threat actors compromised the GenomeX
secure computation engine. All traditional software artifacts were
destroyed or encrypted.

A single DNA-encoded program was recovered from volatile memory.
The program contains the encryption key needed to decrypt the
vault.

You have been provided with:
- A partial architecture manual
- The DNA program
- The initial memory state
- An encrypted vault

Recover the key. Decrypt the vault. Find the flag.
```

---

## Phase 9 — Player Workflow

```
Read Documentation
        │
        ▼
Understand VM Architecture
        │
        ▼
Reverse the Instruction Encoding
        │
        ▼
Fill in Missing Opcode Entries
        │
        ▼
Write or Reconstruct Emulator
        │
        ▼
Assemble / Decode DNA Program
        │
        ▼
Execute Against memory.bin
        │
        ▼
Recover Encryption Key (64 bytes from 0x80–0xBF)
        │
        ▼
Decrypt vault.zip Using Key
        │
        ▼
Obtain Flag: expX{...}
```

---

## Phase 10 — Testing

### Unit Tests

| Test | Description |
|---|---|
| `test_dna_decode` | Verify DNA→binary conversion for all 64 codons |
| `test_dna_encode` | Verify binary→DNA conversion round-trip |
| `test_instruction_decode` | Verify opcode, register, immediate extraction |
| `test_alu_add` | ADD with no carry, with carry, result zero |
| `test_alu_sub` | SUB with no borrow, with borrow, result zero |
| `test_alu_xor` | XOR producing zero and non-zero |
| `test_alu_and` | AND producing zero and non-zero |
| `test_alu_or` | OR producing zero and non-zero |
| `test_cmp` | CMP setting Z and C flags correctly |
| `test_mov` | MOV copies register value |
| `test_load` | LOAD immediate into register |
| `test_store` | STORE register to memory |
| `test_jmp` | JMP sets PC to target |
| `test_jz_taken` | JZ jumps when Z=1 |
| `test_jz_not_taken` | JZ does not jump when Z=0 |
| `test_push_pop` | PUSH/POP stack operations |
| `test_halt` | HALT stops execution |
| `test_memory_bounds` | Accessing 0x00–0xFF works, 0x100 faults |

### Integration Tests

| Test | Description |
|---|---|
| `test_assemble_disassemble` | asm → dna → asm round-trip |
| `test_full_program` | Run known program, verify final register state |
| `test_challenge_program` | Run program.dna, verify recovered key matches expected |

### Test Commands

```bash
python -m pytest testing/ -v
```

**Done when:**
- [x] All unit tests pass
- [x] All integration tests pass
- [x] Challenge program produces correct key

---

## Phase 11 — Error Handling

| Error | Behavior |
|---|---|
| Invalid DNA character | Raise `ValueError` with position |
| DNA length not multiple of 9 | Raise `ValueError` with length |
| Invalid opcode | Print error, halt execution |
| Invalid register index | Raise `ValueError` with index |
| Memory out of bounds (write) | Wrap address modulo 256 |
| Memory out of bounds (read) | Return 0x00 |
| Stack overflow (PUSH at SP=0x00) | Wrap to 0xFF |
| Stack underflow (POP at SP=0xFF) | Return 0x00 |
| Jump to invalid address | Raise `RuntimeError` |
| Division by zero (if DIV added) | Raise `ZeroDivisionError` |

---

## Development Order

| Step | Task | Phase |
|---|---|---|
| 1 | Design CPU and memory layout | Phase 1 |
| 2 | Define ISA and encoding | Phase 2 |
| 3 | Implement DNA↔binary conversion | Phase 3 |
| 4 | Build emulator | Phase 4 |
| 5 | Write unit tests for emulator | Phase 10 |
| 6 | Build assembler | Phase 5 |
| 7 | Write assembler tests | Phase 10 |
| 8 | Create test DNA programs | Phase 10 |
| 9 | Generate challenge DNA program | Phase 7 |
| 10 | Create memory.bin with encrypted key | Phase 7 |
| 11 | Create vault.zip and encrypt flag | Phase 7 |
| 12 | Write genome_manual.txt (with gaps) | Phase 7 |
| 13 | Write architecture.pdf | Phase 7 |
| 14 | Write README.md | Phase 7 |
| 15 | Write solution script | — |
| 16 | Test full solve path end-to-end | Phase 10 |
| 17 | Package challenge | — |

---

## Expected Repository

```
GenomeX-VM/
├── README.md                  # Challenge description
├── description.md             # Detailed challenge writeup
├── IMPLEMENT.md               # This file
├── GenomeX_VM.zip             # Packaged challenge
├── challenge/
│   ├── README.md
│   ├── architecture.pdf
│   ├── genome_manual.txt
│   ├── program.dna
│   ├── memory.bin
│   └── vault.zip
├── solution/
│   ├── solve.py               # Reference solution
│   └── solution.md            # Walkthrough
├── author/
│   ├── emulator.py            # Reference emulator
│   ├── assembler.py           # Reference assembler
│   └── generator.py           # Program generator
└── testing/
    ├── test_emulator.py
    ├── test_assembler.py
    └── test_encoding.py
```

---

## Target Difficulty

| Attribute | Value |
|---|---|
| Category | Reverse Engineering |
| Difficulty | Medium-Hard |
| Expected Solve Time | 90–120 Minutes |
| Prerequisites | Python knowledge, binary/encoding fundamentals |

---

## Success Criteria

A successful player should:

1. Understand the GenomeX architecture from partial documentation
2. Reverse the DNA→binary instruction encoding
3. Deduce missing opcode entries through pattern analysis
4. Build or reconstruct a working emulator
5. Execute the DNA program against the provided memory state
6. Recover the 64-byte encryption key from memory addresses 0x80–0xBF
7. Decrypt vault.zip using the recovered key
8. Obtain the flag: `expX{...}`

---

## Acceptance Criteria

The challenge is ready when:

- [ ] All 16 instructions work correctly in the emulator
- [ ] The assembler produces valid DNA output
- [ ] The reference solution recovers the correct flag
- [ ] The genome_manual.txt has exactly 2–3 missing opcode entries
- [ ] Example programs in the manual are solvable
- [ ] The challenge can be solved in 90–120 minutes by an experienced player
- [ ] No unintended solutions exist
- [ ] All files are included in GenomeX_VM.zip
