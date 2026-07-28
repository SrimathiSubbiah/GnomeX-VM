# GenomeX VM — Architecture Reference

## Block Diagram

```
┌─────────────────────────────────────────────────────┐
│                  GenomeX VM                         │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  Program  │───▶│ Decoder  │───▶│ Executor │      │
│  │  Memory   │    │          │    │          │      │
│  └──────────┘    └──────────┘    └─────┬────┘      │
│                                        │            │
│  ┌──────────────────────────────────────┤            │
│  │                                      ▼            │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │  │  R0  │  │  R1  │  │  R2  │  │  R3  │        │
│  │  │ 8bit │  │ 8bit │  │ 8bit │  │ 8bit │        │
│  │  └──────┘  └──────┘  └──────┘  └──────┘        │
│  │         Register File                           │
│  │                                                  │
│  │  ┌──────┐  ┌──────┐                             │
│  │  │  Z   │  │  C   │                             │
│  │  │ flag │  │ flag │                             │
│  │  └──────┘  └──────┘                             │
│  │         Status Flags                             │
│  │                                                  │
│  │  ┌─────────────────────────────────────────┐    │
│  │  │              Data Memory                 │    │
│  │  │  0x00-0x3F  │  Program (64B)            │    │
│  │  │  0x40-0x7F  │  Constants (64B)          │    │
│  │  │  0x80-0xBF  │  Encrypted Key (64B)      │    │
│  │  │  0xC0-0xFF  │  Scratch (64B)            │    │
│  │  └─────────────────────────────────────────┘    │
│  └──────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────┘
```

## Data Flow

```
program.dna
    │
    ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Fetch   │────▶│  Decode  │────▶│ Execute  │
│ (read 9  │     │ (DNA →   │     │ (update  │
│  bases)  │     │  binary) │     │  state)  │
└─────────┘     └─────────┘     └─────────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │ Update PC   │
                              │ Update Flags│
                              │ Update Regs │
                              └─────────────┘
                                     │
                                     ▼
                              (loop until HALT)
```

## DNA Encoding

Each instruction maps to 9 DNA bases:

```
Base:    A    C    G    T
Bits:   00   01   10   11
```

Three consecutive bases form one codon = 6 bits.

Three codons = 18 bits total (16 used, 2 padding).
