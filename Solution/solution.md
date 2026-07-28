# GenomeX VM — Solution Walkthrough

## Step 1: Study the Documentation

Read `genome_manual.txt` and `architecture.md`. Key observations:

- 4 registers (R0-R3), 8-bit each
- 256 bytes of memory
- Instructions are 9 DNA bases (3 codons)
- DNA encoding: A=00, C=01, G=10, T=11
- 14 of 16 opcodes documented (2 redacted)

## Step 2: Reverse the Encoding

From the manual:
- First 3 bases → opcode (4 bits used)
- Next 3 bases → destination + source registers
- Last 3 bases → immediate/address value

The encoding table shows:
```
AAA = 0x0 = NOP
AAC = 0x1 = LOAD
AAG = 0x2 = STORE
...
```

This matches the pattern: convert each base to 2 bits, read the
first 4 bits as the opcode number.

## Step 3: Deduce Missing Opcodes

The manual redacts opcodes 0xC and 0xD. From the pattern:
- 0xC = ATA → Likely PUSH (stack operation)
- 0xD = ATC → Likely POP (stack operation)

These are not needed for the challenge program but complete the ISA.

## Step 4: Build an Emulator

Write a Python script that:
1. Reads `program.dna` and splits into 9-base chunks
2. Decodes each chunk into opcode, dst, src, imm
3. Executes the instruction, updating registers/memory/flags
4. Repeats until HALT

See `solve.py` for the reference implementation.

## Step 5: Execute the Program

Run the emulator against `program.dna` + `memory.bin`:

```bash
python solve.py
```

The program:
1. Loads the XOR key from address 0x40 (value: 0x37)
2. XORs each byte at 0x50-0x6D with the key
3. Stores decrypted bytes back to the same addresses
4. Halts

## Step 6: Read the Flag

After execution, memory addresses 0x50-0x6D contain:

```
expX{d3n4_pr0gr4mm1ng_1s_c00l}
```

## Step 7: Decrypt the Vault (Bonus)

The vault.zip contains the same flag encrypted with XOR.
Using the key from memory (0x37), decrypt the vault contents
to verify the flag.

## Key Insights

1. **DNA = Binary**: The core trick is realizing DNA bases encode
   2-bit values. A=00, C=01, G=10, T=11.

2. **Fixed-width instructions**: Every instruction is exactly 9
   bases (3 codons = 18 bits, 16 used).

3. **LOAD reads from memory**: The LOAD instruction uses the
   immediate value as a memory address, not as a literal.

4. **XOR is symmetric**: XORing the encrypted data with the same
   key twice returns the original plaintext.

5. **The key is in memory**: Address 0x40 contains the single-byte
   XOR key needed to decrypt the flag.
