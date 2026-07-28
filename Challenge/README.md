# GenomeX VM — CTF Challenge

## Category
Reverse Engineering

## Difficulty
Medium-Hard

## Points
500

## Estimated Solve Time
90–120 minutes

---

## Description

GenomeX Laboratories developed the world's first DNA-based secure
computation engine. Instead of storing software in binary, programs
are encoded using synthetic DNA sequences.

During a cyber attack, one GenomeX program became corrupted. The only
remaining artifact is the encoded DNA program and a memory dump.

You have been provided with:
- The DNA-encoded program (`program.dna`)
- A memory dump (`memory.bin`)
- An encrypted vault (`vault.zip`)
- Partial documentation (`genome_manual.txt`, `architecture.md`)

Your objective: Reconstruct the GenomeX Virtual Machine, execute the
DNA program, and recover the encryption key to decrypt the vault.

## Files

| File | Description |
|------|-------------|
| `program.dna` | The DNA-encoded VM program (837 bases) |
| `memory.bin` | Initial memory state (256 bytes) |
| `vault.zip` | Encrypted archive containing the flag |
| `genome_manual.txt` | Partial ISA documentation |
| `architecture.md` | Architecture block diagram |

## Hints

1. The documentation is deliberately incomplete. Some opcodes are
   missing from the manual. You'll need to deduce them from the
   encoding pattern.

2. Each instruction is exactly 9 DNA bases (3 codons).

3. The memory dump at address 0x40 contains the XOR key.

4. The flag format is `expX{...}`

## Solution Summary

1. Study the documentation to understand the VM architecture
2. Reverse the DNA→binary encoding scheme
3. Deduce any missing opcode entries
4. Build or write an emulator
5. Execute the DNA program against the memory dump
6. Read the decrypted flag from memory addresses 0x50-0x6D
7. Use the XOR key to decrypt vault.zip (bonus)

## Flag

```
expX{d3n4_pr0gr4mm1ng_1s_c00l}
```
