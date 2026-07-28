# Helix Exo — CTF Challenge

## Category
Reverse Engineering

## Difficulty
Medium-Hard

## Points
500

## Estimated Solve Time
90–120 minutes

---

## Story

**Year: 2087**

Helix Labs pioneered biological computing — programs stored as synthetic
DNA instead of binary. Their flagship product, the **Exo-VM**, executed
code encoded in nucleotide sequences. It was unhackable. Untraceable.
Unkillable.

On March 15th, Helix Labs was raided. Most of their research was
destroyed. Servers were wiped. Engineers vanished.

But a single Exo-VM program survived — encoded in a corrupted DNA
sequence, dumped alongside a fragment of memory. Hidden inside is the
encryption key to a vault containing their final secret.

**Your mission:** Reconstruct the Exo-VM from scratch, execute the DNA
program, and recover the key before it's lost forever.

---

## You have been provided with

- `Helix.7z` — Contains the DNA-encoded program and a memory dump

**Your objective:** Extract the files, build an emulator, run the DNA program, and recover the flag.

## Files

| File | Description |
|------|-------------|
| `Helix.7z` | Archive containing `program.dna` and `memory.bin` |

**Inside the archive:**

| File | Description |
|------|-------------|
| `program.dna` | The DNA-encoded Exo-VM program (837 bases) |
| `memory.bin` | Initial memory state (256 bytes) |

## Hints

1. Each instruction is exactly 9 DNA bases (3 codons).

2. The memory dump at address 0x40 contains the XOR key.

3. The flag format is `expX{...}`

## Solution Summary

1. Reverse the DNA→binary encoding scheme
2. Deduce the instruction format and opcodes
3. Build or write an emulator
4. Execute the DNA program against the memory dump
5. Read the decrypted flag from memory addresses 0x50–0x6D

## Flag

```
expX{d3n4_pr0gr4mm1ng_1s_c00l}
```

## Writeup

See [Solution/writeup.md](Solution/writeup.md) for a full solution walkthrough.
