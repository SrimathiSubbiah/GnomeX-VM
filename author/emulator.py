#!/usr/bin/env python3
"""GenomeX VM Reference Emulator

Execution engine for DNA-encoded programs.
Decodes DNA codons into binary instructions and executes them
on a simulated 8-bit CPU with 256 bytes of memory.

Usage:
    python emulator.py program.dna memory.bin
"""

import sys
import os

BASE_MAP = {'A': '00', 'C': '01', 'G': '10', 'T': '11'}
BASE_MAP_INV = {v: k for k, v in BASE_MAP.items()}

OPCODES = {
    0x0: 'NOP', 0x1: 'LOAD', 0x2: 'STORE', 0x3: 'MOV',
    0x4: 'ADD', 0x5: 'SUB', 0x6: 'XOR', 0x7: 'AND',
    0x8: 'OR', 0x9: 'CMP', 0xA: 'JMP', 0xB: 'JZ',
    0xC: 'PUSH', 0xD: 'POP', 0xE: 'PRINT', 0xF: 'HALT',
}


def dna_to_bits(dna_str):
    bits = ''
    for base in dna_str:
        if base not in BASE_MAP:
            raise ValueError(f"Invalid DNA base: '{base}'")
        bits += BASE_MAP[base]
    return bits


def bits_to_dna(bits):
    dna = ''
    for i in range(0, len(bits), 2):
        pair = bits[i:i+2]
        dna += BASE_MAP_INV[pair]
    return dna


def bits_to_int(bits):
    return int(bits, 2)


def int_to_bits(value, width):
    return format(value & ((1 << width) - 1), f'0{width}b')


class GenomeXVM:
    def __init__(self):
        self.registers = [0, 0, 0, 0]
        self.flags = {'Z': False, 'C': False}
        self.memory = [0] * 256
        self.program = []
        self.pc = 0
        self.running = False
        self.max_cycles = 100000
        self.cycle_count = 0
        self.output = []

    def load_program(self, dna_file):
        with open(dna_file, 'r') as f:
            dna = f.read().strip().replace('\n', '').replace(' ', '')
        valid_bases = set('ACGT')
        if not all(b in valid_bases for b in dna):
            bad = [b for b in dna if b not in valid_bases]
            raise ValueError(f"Invalid DNA bases found: {bad}")
        if len(dna) % 9 != 0:
            raise ValueError(f"DNA length {len(dna)} is not a multiple of 9")
        self.program = [dna[i:i+9] for i in range(0, len(dna), 9)]

    def load_memory(self, mem_file):
        if os.path.exists(mem_file):
            with open(mem_file, 'rb') as f:
                data = f.read()
            for i, byte in enumerate(data[:256]):
                self.memory[i] = byte

    def save_memory(self, mem_file):
        with open(mem_file, 'wb') as f:
            f.write(bytes(self.memory))

    def fetch(self):
        if self.pc >= len(self.program):
            self.running = False
            return None
        return self.program[self.pc]

    def decode(self, instruction):
        bits = dna_to_bits(instruction)
        opcode = bits_to_int(bits[0:4])
        dst = bits_to_int(bits[4:6])
        src = bits_to_int(bits[6:8])
        imm = bits_to_int(bits[8:16])
        return opcode, dst, src, imm

    def execute(self, opcode, dst, src, imm):
        self.cycle_count += 1
        if self.cycle_count > self.max_cycles:
            raise RuntimeError(f"Execution exceeded {self.max_cycles} cycles")

        jumped = False

        if opcode == 0x0:
            pass

        elif opcode == 0x1:
            addr = imm & 0xFF
            self.registers[dst] = self.memory[addr] & 0xFF

        elif opcode == 0x2:
            addr = imm & 0xFF
            self.memory[addr] = self.registers[src] & 0xFF

        elif opcode == 0x3:
            self.registers[dst] = self.registers[src] & 0xFF

        elif opcode == 0x4:
            result = self.registers[dst] + self.registers[src]
            self.flags['C'] = result > 0xFF
            self.registers[dst] = result & 0xFF
            self.flags['Z'] = self.registers[dst] == 0

        elif opcode == 0x5:
            result = self.registers[dst] - self.registers[src]
            self.flags['C'] = result < 0
            self.registers[dst] = result & 0xFF
            self.flags['Z'] = self.registers[dst] == 0

        elif opcode == 0x6:
            self.registers[dst] ^= self.registers[src]
            self.registers[dst] &= 0xFF
            self.flags['Z'] = self.registers[dst] == 0

        elif opcode == 0x7:
            self.registers[dst] &= self.registers[src]
            self.registers[dst] &= 0xFF
            self.flags['Z'] = self.registers[dst] == 0

        elif opcode == 0x8:
            self.registers[dst] |= self.registers[src]
            self.registers[dst] &= 0xFF
            self.flags['Z'] = self.registers[dst] == 0

        elif opcode == 0x9:
            result = self.registers[dst] - self.registers[src]
            self.flags['C'] = result < 0
            self.flags['Z'] = (result & 0xFF) == 0

        elif opcode == 0xA:
            self.pc = imm
            jumped = True

        elif opcode == 0xB:
            if self.flags['Z']:
                self.pc = imm
                jumped = True

        elif opcode == 0xC:
            sp = self.registers[3]
            self.memory[0xC0 + (sp & 0x3F)] = self.registers[src] & 0xFF
            self.registers[3] = (self.registers[3] - 1) & 0xFF

        elif opcode == 0xD:
            self.registers[3] = (self.registers[3] + 1) & 0xFF
            sp = self.registers[3]
            self.registers[dst] = self.memory[0xC0 + (sp & 0x3F)] & 0xFF

        elif opcode == 0xE:
            val = self.registers[dst] & 0xFF
            self.output.append(val)

        elif opcode == 0xF:
            self.running = False
            return

        else:
            raise ValueError(f"Unknown opcode: {opcode:#x}")

        if not jumped:
            self.pc += 1

    def run(self):
        self.running = True
        self.pc = 0
        self.cycle_count = 0
        while self.running:
            instr = self.fetch()
            if instr is None:
                break
            opcode, dst, src, imm = self.decode(instr)
            self.execute(opcode, dst, src, imm)
        return self.registers, self.flags, self.memory

    def dump_state(self):
        lines = []
        lines.append("=== GenomeX VM State ===")
        lines.append(f"PC: {self.pc}  Cycles: {self.cycle_count}")
        lines.append(f"Registers: R0={self.registers[0]:#04x} R1={self.registers[1]:#04x} "
                      f"R2={self.registers[2]:#04x} R3={self.registers[3]:#04x}")
        lines.append(f"Flags: Z={self.flags['Z']} C={self.flags['C']}")
        lines.append(f"Program: {len(self.program)} instructions")
        lines.append(f"Output: {self.output}")
        return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} program.dna [memory.bin]")
        sys.exit(1)

    dna_file = sys.argv[1]
    mem_file = sys.argv[2] if len(sys.argv) > 2 else None

    vm = GenomeXVM()
    vm.load_program(dna_file)

    if mem_file:
        vm.load_memory(mem_file)

    print(f"Loaded {len(vm.program)} instructions from {dna_file}")
    vm.run()
    print(vm.dump_state())

    if mem_file:
        vm.save_memory(mem_file)
        print(f"Memory saved to {mem_file}")

    if vm.output:
        print(f"Program output: {[hex(b) for b in vm.output]}")


if __name__ == '__main__':
    main()
