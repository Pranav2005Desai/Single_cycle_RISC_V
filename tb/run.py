#!/usr/bin/env python3
"""Random RV32I program generator + golden ISS, compared against the RTL in Icarus."""
import random, subprocess, sys, os

M = 0xFFFFFFFF
BASE = 0x8000_0000
def sx(v, b): v &= (1 << b) - 1; return v - (1 << b) if v >> (b - 1) else v

# ---------- encoders ----------
def R(f7, rs2, rs1, f3, rd, op=0x33): return (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op
def I(imm, rs1, f3, rd, op): return ((imm & 0xFFF) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op
def S(imm, rs2, rs1, f3): imm &= 0xFFF; return ((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((imm & 31) << 7) | 0x23
def B(imm, rs2, rs1, f3):
    imm &= 0x1FFF
    return (((imm >> 12) & 1) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (((imm >> 1) & 0xF) << 8) | (((imm >> 11) & 1) << 7) | 0x63
def U(imm20, rd, op): return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | op
def J(imm, rd):
    imm &= 0x1FFFFF
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20) | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F

# ---------- golden ISS ----------
class ISS:
    def __init__(s, prog): s.prog = prog; s.mem = {}; s.reset()
    def reset(s): s.pc = BASE; s.x = [0] * 32
    def rb(s, a): return s.mem.get(a & 0xFFFF, 0)
    def wb(s, a, v): s.mem[a & 0xFFFF] = v & 0xFF
    def step(s):
        idx = (s.pc - BASE) >> 2
        ins = s.prog[idx] if 0 <= idx < len(s.prog) else 0x13
        op = ins & 0x7F; rd = (ins >> 7) & 31; f3 = (ins >> 12) & 7
        rs1 = (ins >> 15) & 31; rs2 = (ins >> 20) & 31; f7 = ins >> 25
        a, b = s.x[rs1], s.x[rs2]
        iimm = sx(ins >> 20, 12)
        npc = (s.pc + 4) & M; w = None
        if op == 0x33:
            w = alu(f3, a, b, f7 == 0x20, True)
        elif op == 0x13:
            w = alu(f3, a, iimm & M, f7 == 0x20, False)
        elif op == 0x03:
            ad = (a + iimm) & M
            if f3 == 0: w = sx(s.rb(ad), 8) & M
            elif f3 == 1: w = sx(s.rb(ad) | s.rb(ad + 1) << 8, 16) & M
            elif f3 == 4: w = s.rb(ad)
            elif f3 == 5: w = s.rb(ad) | s.rb(ad + 1) << 8
            else: w = s.rb(ad) | s.rb(ad + 1) << 8 | s.rb(ad + 2) << 16 | s.rb(ad + 3) << 24
        elif op == 0x23:
            simm = sx(((ins >> 25) << 5) | ((ins >> 7) & 31), 12)
            ad = (a + simm) & M
            for k in range({0: 1, 1: 2}.get(f3 & 3, 4)): s.wb(ad + k, b >> (8 * k))
        elif op == 0x63:
            bimm = sx((((ins >> 31) & 1) << 12) | (((ins >> 7) & 1) << 11) | (((ins >> 25) & 0x3F) << 5) | (((ins >> 8) & 0xF) << 1), 13)
            sa, sb = sx(a, 32), sx(b, 32)
            t = {0: a == b, 1: a != b, 4: sa < sb, 5: sa >= sb, 6: a < b, 7: a >= b}.get(f3, False)
            if t: npc = (s.pc + bimm) & M
        elif op == 0x6F:
            jimm = sx((((ins >> 31) & 1) << 20) | (((ins >> 12) & 0xFF) << 12) | (((ins >> 20) & 1) << 11) | (((ins >> 21) & 0x3FF) << 1), 21)
            w = npc; npc = (s.pc + jimm) & M
        elif op == 0x67:
            w = npc; npc = (a + iimm) & M & ~1
        elif op == 0x37: w = ins & 0xFFFFF000
        elif op == 0x17: w = (s.pc + (ins & 0xFFFFF000)) & M
        if w is not None and rd: s.x[rd] = w & M
        s.pc = npc

def alu(f3, a, b, alt, rtype):
    sh = b & 31
    if f3 == 0: return (a - b if (alt and rtype) else a + b) & M
    if f3 == 1: return (a << sh) & M
    if f3 == 2: return int(sx(a, 32) < sx(b, 32))
    if f3 == 3: return int(a < b)
    if f3 == 4: return a ^ b
    if f3 == 5: return (sx(a, 32) >> sh) & M if alt else a >> sh
    if f3 == 6: return a | b
    return a & b

# ---------- random program ----------
def gen(rng, n):
    p = []
    # x31 = data base (0x8001_0000), kept fixed
    p.append(U(0x80010, 31, 0x37))
    for r in range(1, 31):
        p.append(U(rng.getrandbits(20), r, 0x37) if rng.random() < .5 else I(rng.randint(-2048, 2047), 0, 0, r, 0x13))
    while len(p) < n:
        rd = rng.randint(0, 30); r1 = rng.randint(0, 31); r2 = rng.randint(0, 31)
        k = rng.random()
        if k < .22:
            f3 = rng.randint(0, 7); alt = f3 in (0, 5) and rng.random() < .5
            p.append(R(0x20 if alt else 0, r2, r1, f3, rd))
        elif k < .42:
            f3 = rng.randint(0, 7)
            if f3 in (1, 5):
                p.append(I((0x400 if f3 == 5 and rng.random() < .5 else 0) | rng.randint(0, 31), r1, f3, rd, 0x13))
            else:
                p.append(I(rng.randint(-2048, 2047), r1, f3, rd, 0x13))
        elif k < .54:   # store relative to x31
            f3 = rng.choice([0, 1, 2]); al = {0: 1, 1: 2, 2: 4}[f3]
            p.append(S(rng.randrange(0, 2040, al), r2, 31, f3))
        elif k < .66:   # load relative to x31
            f3 = rng.choice([0, 1, 2, 4, 5]); al = {0: 1, 1: 2, 2: 4, 4: 1, 5: 2}[f3]
            p.append(I(rng.randrange(0, 2040, al), 31, f3, rd, 0x03))
        elif k < .80:   # forward branch
            p.append(B(4 * rng.randint(1, 4), r2, r1, rng.choice([0, 1, 4, 5, 6, 7])))
        elif k < .86:
            p.append(J(4 * rng.randint(1, 4), rd))
        elif k < .91:   # JALR: auipc rd, 0 ; jalr rd2, rd, small
            t = rng.randint(1, 30)
            p.append(U(0, t, 0x17)); p.append(I(4 * rng.randint(2, 5) + rng.randint(0, 1), t, 0, rd, 0x67))
        elif k < .95: p.append(U(rng.getrandbits(20), rd, 0x37))
        else: p.append(U(rng.getrandbits(20), rd, 0x17))
    # backward loop occasionally (bounded via cycle count anyway)
    p.append(J(-4 * rng.randint(1, len(p) - 1), 0))
    return p

def directed():
    p = [U(0x80010, 31, 0x37),
         I(-5, 0, 0, 1, 0x13), I(7, 0, 0, 2, 0x13),
         R(0, 2, 1, 0, 3), R(0x20, 2, 1, 0, 4), R(0, 2, 1, 2, 5), R(0, 2, 1, 3, 6),
         I(0x400 | 1, 1, 5, 7, 0x13), I(1, 1, 5, 8, 0x13), I(3, 2, 1, 9, 0x13),
         S(0, 1, 31, 2), S(4, 2, 31, 1), S(6, 1, 31, 0),
         I(0, 31, 2, 10, 0x03), I(4, 31, 1, 11, 0x03), I(6, 31, 0, 12, 0x03), I(6, 31, 4, 13, 0x03), I(0, 31, 5, 14, 0x03),
         B(8, 2, 1, 0), I(1, 0, 0, 15, 0x13),          # beq not taken
         B(8, 1, 1, 0), I(99, 0, 0, 15, 0x13),         # beq taken (skip)
         B(8, 2, 1, 4), I(99, 0, 0, 16, 0x13),         # blt taken
         B(8, 2, 1, 6), I(1, 0, 0, 16, 0x13),          # bltu not taken (0xfffffffb > 7)
         J(8, 17), I(99, 0, 0, 18, 0x13),
         U(0, 19, 0x17), I(13, 19, 0, 20, 0x67), I(99, 0, 0, 21, 0x13), I(1, 0, 0, 22, 0x13),
         U(0xABCDE, 23, 0x37), U(0x12345, 24, 0x17),
         R(0, 0, 0, 0, 0) | 0, I(5, 0, 0, 0, 0x13),    # writes to x0 ignored
         J(0, 0)]
    return p

def run(name, prog, ctl, n, d):
    with open(f"{d}/prog.hex", "w") as f: f.write("\n".join(f"{w:08x}" for w in prog) + "\n")
    with open(f"{d}/ctl.hex", "w") as f: f.write("\n".join(f"{c:x}" for c in ctl) + "\n")
    r = subprocess.run([f"{d}/obj/Vtb", f"+N={n}"], cwd=d, capture_output=True, text=True)
    rtl = open(f"{d}/rtl_trace.txt").read().split("\n")
    iss = ISS(prog); exp = []
    for i in range(n):
        rs, st = ctl[i] >> 1, ctl[i] & 1
        if rs: iss.reset(); continue
        exp.append(f"{i} {iss.pc:08x}")
        if not st: iss.step()
    exp += [f"x{i} {iss.x[i]:08x}" for i in range(1, 32)]
    words = {}
    for a, v in iss.mem.items(): words[a & ~3] = words.get(a & ~3, 0) | v << (8 * (a & 3))
    exp += [f"m{a:04x} {v:08x}" for a, v in sorted(words.items()) if v]
    rtl = [l for l in rtl if l]
    ok = rtl == exp
    if not ok:
        for j, (x, y) in enumerate(zip(exp, rtl)):
            if x != y: print(f"  first mismatch @line {j}: exp '{x}' rtl '{y}'"); break
        else: print(f"  length mismatch exp {len(exp)} rtl {len(rtl)}")
    print(f"{name}: {'PASS' if ok else 'FAIL'}  ({n} cycles, {len(prog)} instrs)")
    return ok

if __name__ == "__main__":
    d = os.path.dirname(os.path.abspath(__file__))
    rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    allok = run("directed", directed(), [0] * 60, 60, d)
    for t in range(int(sys.argv[2]) if len(sys.argv) > 2 else 20):
        p = gen(rng, 300); n = 1500
        allok &= run(f"random{t}", p, [0] * n, n, d)
        allok &= run(f"stall{t}", p, [int(rng.random() < .25) for _ in range(n)], n, d)
        ctl = [int(rng.random() < .2) for _ in range(n)]
        r0 = rng.randint(200, 1000)
        for k in range(r0, r0 + rng.randint(1, 3)): ctl[k] = 2
        allok &= run(f"reset{t}", p, ctl, n, d)
    print("ALL PASS" if allok else "SOME FAILED")
