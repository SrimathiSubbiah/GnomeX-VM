#!/usr/bin/env python3
"""GenomeX VM Assembler

Converts assembly language to DNA-encoded programs.
Each instruction produces exactly 9 DNA bases (3 codons).

Usage:
    python assembler.py input.asm output.dna
"""

import sys
import re

BASE_MAP_INV = {'00': 'A', '01': 'C', '10': 'G', '11': 'T'}

OPCODE_TABLE = {
    'NOP':   0x0, 'LOAD':  0x1, 'STORE': 0x2, 'MOV':   0x3,
    'ADD':   0x4, 'SUB':   0x5, 'XOR':   0x6, 'AND':   0x7,
    'OR':    0x8, 'CMP':   0x9, 'JMP':   0xA, 'JZ':    0xB,
    'PUSH':  0xC, 'POP':   0xD, 'PRINT': 0xE, 'HALT':  0xF,
}

REGISTER_TABLE = {'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3}


def bits_to_dna(bits):
    dna = ''
    for i in range(0, len(bits), 2):
        pair = bits[i:i+2]
        dna += BASE_MAP_INV[pair]
    return dna


def int_to_bits(value, width):
    return format(value & ((1 << width) - 1), f'0{width}b')


def encode_instruction(opcode, dst=0, src=0, imm=0):
    opcode_bits = int_to_bits(opcode, 4)
    dst_bits = int_to_bits(dst, 2)
    src_bits = int_to_bits(src, 2)
    imm_bits = int_to_bits(imm, 8)
    pad_bits = '00'
    all_bits = opcode_bits + dst_bits + src_bits + imm_bits + pad_bits
    return bits_to_dna(all_bits)


def parse_register(s):
    s = s.strip().upper()
    if s not in REGISTER_TABLE:
        raise ValueError(f"Invalid register: '{s}' (expected R0-R3)")
    return REGISTER_TABLE[s]


def parse_immediate(s):
    s = s.strip()
    if s.startswith('0x') or s.startswith('0X'):
        return int(s, 16)
    return int(s)


def parse_line(line):
    line = line.strip()
    if not line or line.startswith('#') or line.startswith(';'):
        return None
    line = re.sub(r'#.*$', '', line)
    line = re.sub(r';.*$', '', line)
    line = line.strip()
    if not line:
        return None
    parts = line.split(None, 1)
    mnemonic = parts[0].upper()
    operands_str = parts[1].strip() if len(parts) > 1 else ''
    if not operands_str:
        return mnemonic, []
    operands = [op.strip() for op in operands_str.split(',')]
    return mnemonic, operands


def assemble_instruction(mnemonic, operands):
    if mnemonic not in OPCODE_TABLE:
        raise ValueError(f"Unknown mnemonic: '{mnemonic}'")

    opcode = OPCODE_TABLE[mnemonic]

    if mnemonic in ('NOP', 'HALT'):
        return encode_instruction(opcode)

    elif mnemonic == 'LOAD':
        dst = parse_register(operands[0])
        imm = parse_immediate(operands[1])
        return encode_instruction(opcode, dst=dst, imm=imm)

    elif mnemonic == 'STORE':
        src = parse_register(operands[0])
        imm = parse_immediate(operands[1])
        return encode_instruction(opcode, src=src, imm=imm)

    elif mnemonic in ('MOV', 'ADD', 'SUB', 'XOR', 'AND', 'OR', 'CMP'):
        dst = parse_register(operands[0])
        src = parse_register(operands[1])
        return encode_instruction(opcode, dst=dst, src=src)

    elif mnemonic in ('JMP', 'JZ'):
        imm = parse_immediate(operands[0])
        return encode_instruction(opcode, imm=imm)

    elif mnemonic == 'PUSH':
        src = parse_register(operands[0])
        return encode_instruction(opcode, src=src)

    elif mnemonic == 'POP':
        dst = parse_register(operands[0])
        return encode_instruction(opcode, dst=dst)

    elif mnemonic == 'PRINT':
        dst = parse_register(operands[0])
        return encode_instruction(opcode, dst=dst)

    else:
        raise ValueError(f"Unhandled mnemonic: '{mnemonic}'")


def assemble(input_file, output_file):
    instructions = []
    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            result = parse_line(line)
            if result is None:
                continue
            mnemonic, operands = result
            try:
                dna = assemble_instruction(mnemonic, operands)
                instructions.append(dna)
            except Exception as e:
                raise ValueError(f"Line {line_num}: {e}") from e

    output = ''.join(instructions)
    with open(output_file, 'w') as f:
        f.write(output)

    print(f"Assembled {len(instructions)} instructions -> {output_file}")
    print(f"Output: {len(output)} DNA bases ({len(output) // 9} codons)")
    return output


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input.asm output.dna")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    assemble(input_file, output_file)


if __name__ == '__main__':
    main()
