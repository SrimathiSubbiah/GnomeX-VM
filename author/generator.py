#!/usr/bin/env python3
"""GenomeX VM Challenge Generator

Creates all challenge artifacts:
- program.dna: The DNA-encoded VM program
- memory.bin: Initial memory state with encrypted flag
- vault.zip: Encrypted archive (bonus, same flag)
"""

import os
import sys
import zipfile
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assembler import encode_instruction

FLAG = b"expX{d3n4_pr0gr4mm1ng_1s_c00l}"
XOR_KEY_BYTE = 0x37
CONSTANTS_ADDR = 0x40
ENCRYPTED_ADDR = 0x50
DECRYPTED_ADDR = 0x50


def encrypt_data(data, key_byte):
    return bytes([b ^ key_byte for b in data])


def create_challenge():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    challenge_dir = os.path.join(base_dir, 'challenge')
    os.makedirs(challenge_dir, exist_ok=True)

    print("=== GenomeX Challenge Generator ===\n")

    print(f"Flag: {FLAG.decode()}")
    print(f"XOR key byte: 0x{XOR_KEY_BYTE:02x}")

    encrypted = encrypt_data(FLAG, XOR_KEY_BYTE)
    print(f"Encrypted flag ({len(encrypted)} bytes): {encrypted.hex()}")

    print("\n[1/3] Building DNA program...")
    dna = build_and_save_program(challenge_dir)

    print("\n[2/3] Creating memory.bin...")
    memory = create_memory(encrypted)
    mem_path = os.path.join(challenge_dir, 'memory.bin')
    with open(mem_path, 'wb') as f:
        f.write(bytes(memory))
    print(f"  0x40: XOR key = 0x{XOR_KEY_BYTE:02x}")
    print(f"  0x50-0x{0x50 + len(encrypted) - 1:02X}: Encrypted flag ({len(encrypted)} bytes)")

    print("\n[3/3] Creating vault.zip...")
    vault_path = os.path.join(challenge_dir, 'vault.zip')
    create_vault(vault_path, FLAG, XOR_KEY_BYTE)
    print(f"  Vault: {vault_path}")

    print("\n=== Done ===")
    print(f"Challenge dir: {challenge_dir}")

    return dna, memory


def build_and_save_program(challenge_dir):
    dna_path = os.path.join(challenge_dir, 'program.dna')

    instructions = []

    instructions.append(encode_instruction(0x1, dst=2, imm=CONSTANTS_ADDR))
    instructions.append(encode_instruction(0xE, dst=2))

    num_bytes = len(FLAG)
    for i in range(num_bytes):
        src_addr = ENCRYPTED_ADDR + i
        dst_addr = DECRYPTED_ADDR + i
        instructions.append(encode_instruction(0x1, dst=0, imm=src_addr))
        instructions.append(encode_instruction(0x6, dst=0, src=2))
        instructions.append(encode_instruction(0x2, src=0, imm=dst_addr))

    instructions.append(encode_instruction(0xF))

    dna_str = ''.join(instructions)
    with open(dna_path, 'w') as f:
        f.write(dna_str)

    print(f"  {len(instructions)} instructions -> {dna_path}")
    print(f"  DNA length: {len(dna_str)} bases ({len(dna_str) // 9} codons)")
    return dna_str


def create_memory(encrypted_flag):
    memory = [0] * 256

    memory[CONSTANTS_ADDR] = XOR_KEY_BYTE

    for i, byte in enumerate(encrypted_flag):
        addr = ENCRYPTED_ADDR + i
        if addr < 0x80:
            memory[addr] = byte

    return memory


def create_vault(vault_path, flag, key_byte):
    encrypted = encrypt_data(flag, key_byte)
    with zipfile.ZipFile(vault_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('flag.bin', encrypted)
        zf.writestr('hint.txt', 'The flag is XOR-encrypted. Same key as memory.')
        md5 = hashlib.md5(flag).hexdigest()
        zf.writestr('checksum.md5', md5)


if __name__ == '__main__':
    create_challenge()
