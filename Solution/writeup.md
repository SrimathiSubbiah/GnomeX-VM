# Helix Exo — Solution Writeup

## 1. Challenge Overview

We're given:
- `Helix.7z` — Contains `program.dna` (837 bases) and `memory.bin` (256 bytes)

No documentation is provided. Players must reverse the DNA encoding and ISA from scratch.

**Goal:** Build an emulator, run the DNA program, and extract the flag from memory.

---

## 2. Understanding DNA Encoding

DNA bases encode 2-bit values:

| Base | Binary |
|------|--------|
| A    | 00     |
| C    | 01     |
| G    | 10     |
| T    | 11     |

Each instruction is exactly **9 bases** (3 codons):
- 3 bases × 2 bits = 6 bits per codon
- 3 codons = 18 bits total
- Only 16 bits are used, 2 are padding

Field layout (16 bits):
```
[opcode:4][dst:2][src:2][imm:8]
```

Example: `ACGACAAAA`
```
A=00  C=01  G=10  → opcode = 0001 = 0x1 (LOAD)
A=00  C=01        → dst = 01 = 1 (R1)
A=00  A=00        → src = 00 = 0 (R0)
A=00  A=00  A=00  → imm = 00000000 = 0x00
```

---

## 3. Reversing the ISA

The ISA encoding table:

| Opcode | Binary | Mnemonic | Description |
|--------|--------|----------|-------------|
| 0x0    | 0000   | NOP      | No operation |
| 0x1    | 0001   | LOAD     | Load byte from memory into register |
| 0x2    | 0010   | STORE    | Store register byte to memory |
| 0x3    | 0011   | MOV      | Copy register to register |
| 0x4    | 0100   | ADD      | Add source to destination |
| 0x5    | 0101   | SUB      | Subtract source from destination |
| 0x6    | 0110   | XOR      | Bitwise XOR |
| 0x7    | 0111   | AND      | Bitwise AND |
| 0x8    | 1000   | OR       | Bitwise OR |
| 0x9    | 1001   | CMP      | Compare (sets flags only) |
| 0xA    | 1010   | JMP      | Unconditional jump |
| 0xB    | 1011   | JZ       | Jump if zero flag set |
| 0xC    | 1100   | ???      | [REDACTED] |
| 0xD    | 1101   | ???      | [REDACTED] |
| 0xE    | 1110   | PRINT    | Output register value |
| 0xF    | 1111   | HALT     | Stop execution |

Opcodes 0xC and 0xD are redacted but not used in this program.

---

## 4. Understanding the Program

Disassembling the 93 instructions reveals a simple pattern:

```python
# Instruction 0: Load XOR key from memory
LOAD R2, 0x40        # R2 = memory[0x40] = 0x37

# Instructions 1: Print key (debug)
PRINT R2

# Instructions 2-91: XOR loop (30 iterations)
# For each address 0x50 through 0x6D:
LOAD R0, 0x50        # R0 = memory[addr]
XOR R0, R2           # R0 = R0 ^ R2
STORE R0, 0x50       # memory[addr] = R0

LOAD R0, 0x51
XOR R0, R2
STORE R0, 0x51
# ... repeat for all 30 bytes ...

# Instruction 92: Halt
HALT
```

**The algorithm:** XOR each byte at addresses 0x50–0x6D with the key at 0x40.

---

## 5. Building the Emulator

### 5.1 DNA to Binary Conversion

```python
BASE_MAP = {'A': '00', 'C': '01', 'G': '10', 'T': '11'}

def dna_to_bits(dna_str):
    bits = ''
    for base in dna_str:
        bits += BASE_MAP[base]
    return bits

def bits_to_int(bits):
    return int(bits, 2)
```

### 5.2 Instruction Decoder

```python
def decode(self, instruction):
    bits = dna_to_bits(instruction)
    opcode = bits_to_int(bits[0:4])    # bits 0-3
    dst    = bits_to_int(bits[4:6])    # bits 4-5
    src    = bits_to_int(bits[6:8])    # bits 6-7
    imm    = bits_to_int(bits[8:16])   # bits 8-15
    return opcode, dst, src, imm
```

### 5.3 Execution Loop

```python
def run(self):
    self.running = True
    self.pc = 0
    cycles = 0

    while self.running:
        if self.pc >= len(self.program):
            self.running = False
            break

        cycles += 1
        if cycles > self.max_cycles:
            raise RuntimeError("Cycle limit exceeded")

        instr = self.program[self.pc]
        opcode, dst, src, imm = self.decode(instr)

        jumped = False

        if opcode == 0x0:   # NOP
            pass
        elif opcode == 0x1: # LOAD
            addr = imm & 0xFF
            self.registers[dst] = self.memory[addr] & 0xFF
        elif opcode == 0x2: # STORE
            addr = imm & 0xFF
            self.memory[addr] = self.registers[src] & 0xFF
        elif opcode == 0x3: # MOV
            self.registers[dst] = self.registers[src] & 0xFF
        elif opcode == 0x4: # ADD
            result = self.registers[dst] + self.registers[src]
            self.flags['C'] = result > 0xFF
            self.registers[dst] = result & 0xFF
            self.flags['Z'] = self.registers[dst] == 0
        elif opcode == 0x5: # SUB
            result = self.registers[dst] - self.registers[src]
            self.flags['C'] = result < 0
            self.registers[dst] = result & 0xFF
            self.flags['Z'] = self.registers[dst] == 0
        elif opcode == 0x6: # XOR
            self.registers[dst] ^= self.registers[src]
            self.registers[dst] &= 0xFF
            self.flags['Z'] = self.registers[dst] == 0
        elif opcode == 0x7: # AND
            self.registers[dst] &= self.registers[src]
            self.registers[dst] &= 0xFF
            self.flags['Z'] = self.registers[dst] == 0
        elif opcode == 0x8: # OR
            self.registers[dst] |= self.registers[src]
            self.registers[dst] &= 0xFF
            self.flags['Z'] = self.registers[dst] == 0
        elif opcode == 0x9: # CMP
            result = self.registers[dst] - self.registers[src]
            self.flags['C'] = result < 0
            self.flags['Z'] = (result & 0xFF) == 0
        elif opcode == 0xA: # JMP
            self.pc = imm
            jumped = True
        elif opcode == 0xB: # JZ
            if self.flags['Z']:
                self.pc = imm
                jumped = True
        elif opcode == 0xE: # PRINT
            pass  # Debug only
        elif opcode == 0xF: # HALT
            self.running = False
            return

        if not jumped:
            self.pc += 1
```

---

## 6. Extracting the Flag

### 6.1 Memory Layout

```
0x40: XOR key (0x37)
0x50-0x6D: Encrypted flag data (30 bytes)
```

### 6.2 Run the Emulator

```bash
python solve.py
```

Output:
```
[1/4] Loading challenge files...
Loaded 93 instructions
Loaded 256 bytes of memory

[2/4] Executing DNA program...
  PC: 92  |  R0: 0x7d  R1: 0x00  R2: 0x37  R3: 0x00

[3/4] Extracting flag from memory...
  Flag: expX{d3n4_pr0gr4mm1ng_1s_c00l}

[4/4] Decrypting vault.zip...
  Vault flag: expX{d3n4_pr0gr4mm1ng_1s_c00l}
```

### 6.3 Read Flag from Memory

```python
flag_bytes = bytes([vm.memory[i] for i in range(0x50, 0x6E)])
flag = flag_bytes.decode('ascii')
# Result: expX{d3n4_pr0gr4mm1ng_1s_c00l}
```

---

## 7. Decrypting the Vault (Author Only)

> **Note:** `vault.zip` is not distributed to players. It exists in the Solution directory for verification purposes only.

The vault contains:
- `flag.bin` — 30 bytes of XOR-encrypted data
- `hint.txt` — "The flag is XOR-encrypted. Same key as memory."
- `checksum.md5` — Integrity verification

```python
import zipfile

xor_key = vm.memory[0x40]  # 0x37

with zipfile.ZipFile('vault.zip', 'r') as zf:
    with zf.open('flag.bin') as f:
        encrypted = f.read()

decrypted = bytes([b ^ xor_key for b in encrypted])
# Result: expX{d3n4_pr0gr4mm1ng_1s_c00l}
```

---

## 8. Alternative Approaches

### Manual Decoding

Possible but tedious. You'd need to:
1. Map each 9-base instruction to binary
2. Extract opcode/dst/src/imm fields
3. Manually execute 93 instructions
4. Track register and memory state

### Static Analysis Without Emulator

Since the program is just an XOR loop, you can skip the emulator entirely:
1. Analyze `program.dna` to understand the XOR loop pattern
2. Look at `memory.bin` at address 0x40 → key = 0x37
3. XOR bytes at 0x50–0x6D with 0x37
4. Decode ASCII → flag

```python
data = open('memory.bin', 'rb').read()
key = data[0x40]
flag = bytes([b ^ key for b in data[0x50:0x6E]])
print(flag.decode('ascii'))
```

### CyberChef

1. Load `memory.bin` as hex
2. Extract bytes 0x50–0x6D
3. XOR with key 0x37
4. Output as ASCII

---

## 9. Key Insights

1. **DNA = Binary**: The core trick is realizing DNA bases encode 2-bit values. A=00, C=01, G=10, T=11.

2. **Fixed-width instructions**: Every instruction is exactly 9 bases (3 codons = 18 bits, 16 used).

3. **LOAD reads from memory**: The LOAD instruction uses the immediate value as a memory address, not as a literal.

4. **XOR is symmetric**: XORing the encrypted data with the same key twice returns the original plaintext.

5. **The key is in memory**: Address 0x40 contains the single-byte XOR key needed to decrypt the flag.

6. **The program is simple**: Despite being 93 instructions, it's just 30 copies of `LOAD → XOR → STORE` plus a HALT. No loops, no conditionals.

---

## Flag

```
expX{d3n4_pr0gr4mm1ng_1s_c00l}
```
