#!/usr/bin/env python3
"""Helix Exo — Reference Solution

Reconstructs the Exo-VM, executes the DNA program, and recovers the flag.

Usage:
    python solve.py
"""

import os
import sys


BASE_MAP = {'A': '00', 'C': '01', 'G': '10', 'T': '11'}
BASE_MAP_INV = {v: k for k, v in BASE_MAP.items()}


def dna_to_bits(dna_str):
    bits = ''
    for base in dna_str:
        bits += BASE_MAP[base]
    return bits


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

    def load_program(self, dna_file):
        with open(dna_file, 'r') as f:
            dna = f.read().strip().replace('\n', '').replace(' ', '')
        self.program = [dna[i:i+9] for i in range(0, len(dna), 9)]
        print(f"Loaded {len(self.program)} instructions")

    def load_memory(self, mem_file):
        with open(mem_file, 'rb') as f:
            data = f.read()
        for i, byte in enumerate(data[:256]):
            self.memory[i] = byte
        print(f"Loaded {len(data)} bytes of memory")

    def decode(self, instruction):
        bits = dna_to_bits(instruction)
        opcode = bits_to_int(bits[0:4])
        dst = bits_to_int(bits[4:6])
        src = bits_to_int(bits[6:8])
        imm = bits_to_int(bits[8:16])
        return opcode, dst, src, imm

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
                raise RuntimeError(f"Cycle limit exceeded ({self.max_cycles})")

            instr = self.program[self.pc]
            opcode, dst, src, imm = self.decode(instr)

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

            elif opcode == 0xE:
                pass

            elif opcode == 0xF:
                self.running = False
                return

            if not jumped:
                self.pc += 1


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    challenge_dir = os.path.join(base_dir, 'Challenge')

    print("=== Helix Exo Solver ===\n")

    print("[1/3] Loading challenge files...")
    vm = GenomeXVM()
    vm.load_program(os.path.join(challenge_dir, 'program.dna'))
    vm.load_memory(os.path.join(challenge_dir, 'memory.bin'))

    print("\n[2/3] Executing DNA program...")
    vm.run()
    print(f"  PC: {vm.pc}  |  R0: {vm.registers[0]:#04x}  R1: {vm.registers[1]:#04x}  "
          f"R2: {vm.registers[2]:#04x}  R3: {vm.registers[3]:#04x}")

    print("\n[3/3] Extracting flag from memory...")
    flag_bytes = bytes([vm.memory[i] for i in range(0x50, 0x6E)])
    flag = flag_bytes.decode('ascii', errors='replace')
    print(f"  Flag: {flag}")

    print(f"\n{'='*50}")
    print(f"FLAG: {flag}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
