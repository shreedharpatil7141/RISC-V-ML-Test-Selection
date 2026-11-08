#!/usr/bin/env python3
"""Minimal RV32I assembler (Stage 1). Output: one 32-bit hex word per line ($readmemh).
Supports: RV32I + RV32M mnemonics, labels, .org, .word, pseudos (nop li la mv j jal jr jalr ret beqz bnez fence).
Numeric branch/jump operands are raw byte offsets; label operands are PC-relative."""
import re, sys

ABI = {'zero':0,'ra':1,'sp':2,'gp':3,'tp':4,'t0':5,'t1':6,'t2':7,'s0':8,'fp':8,'s1':9,
       'a0':10,'a1':11,'a2':12,'a3':13,'a4':14,'a5':15,'a6':16,'a7':17,
       's2':18,'s3':19,'s4':20,'s5':21,'s6':22,'s7':23,'s8':24,'s9':25,'s10':26,'s11':27,
       't3':28,'t4':29,'t5':30,'t6':31}
def reg(s):
    s = s.strip()
    if s in ABI: return ABI[s]
    m = re.fullmatch(r'x(\d+)', s)
    if m and int(m.group(1)) < 32: return int(m.group(1))
    raise ValueError(f"bad register '{s}'")

R_OPS = {'add':(0,0),'sub':(0x20,0),'sll':(0,1),'slt':(0,2),'sltu':(0,3),'xor':(0,4),
         'srl':(0,5),'sra':(0x20,5),'or':(0,6),'and':(0,7),
         # RV32M (funct7=0000001): MUL MULH MULHSU MULHU DIV DIVU REM REMU = funct3 0..7
         'mul':(1,0),'mulh':(1,1),'mulhsu':(1,2),'mulhu':(1,3),'div':(1,4),'divu':(1,5),'rem':(1,6),'remu':(1,7)}
I_OPS = {'addi':0,'slti':2,'sltiu':3,'xori':4,'ori':6,'andi':7}
SH_OPS = {'slli':(0,1),'srli':(0,5),'srai':(0x20,5)}
LD_OPS = {'lb':0,'lh':1,'lw':2,'lbu':4,'lhu':5}
ST_OPS = {'sb':0,'sh':1,'sw':2}
BR_OPS = {'beq':0,'bne':1,'blt':4,'bge':5,'bltu':6,'bgeu':7}

def enc_r(f7,rs2,rs1,f3,rd,op): return (f7<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|op
def enc_i(imm,rs1,f3,rd,op):
    assert -2048 <= imm <= 2047, f"I-imm out of range: {imm}"
    return ((imm & 0xFFF)<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|op
def enc_s(imm,rs2,rs1,f3,op):
    assert -2048 <= imm <= 2047, f"S-imm out of range: {imm}"
    imm &= 0xFFF
    return ((imm>>5)<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|((imm&0x1F)<<7)|op
def enc_b(imm,rs2,rs1,f3,op):
    assert -4096 <= imm <= 4094 and imm % 2 == 0, f"B-imm bad: {imm}"
    i = imm & 0x1FFF
    return (((i>>12)&1)<<31)|(((i>>5)&0x3F)<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|(((i>>1)&0xF)<<8)|(((i>>11)&1)<<7)|op
def enc_u(imm20,rd,op): return ((imm20 & 0xFFFFF)<<12)|(rd<<7)|op
def enc_j(imm,rd,op):
    assert -(1<<20) <= imm < (1<<20) and imm % 2 == 0, f"J-imm bad: {imm}"
    i = imm & 0x1FFFFF
    return (((i>>20)&1)<<31)|(((i>>1)&0x3FF)<<21)|(((i>>11)&1)<<20)|(((i>>12)&0xFF)<<12)|(rd<<7)|op

def is_num(s):
    try: int(s, 0); return True
    except ValueError: return False

def split_li(v):
    v &= 0xFFFFFFFF
    sv = v - (1<<32) if v >> 31 else v
    if -2048 <= sv <= 2047: return None, sv          # single addi
    lo = ((v & 0xFFF) ^ 0x800) - 0x800
    hi = ((v - lo) >> 12) & 0xFFFFF
    return hi, lo

def li_size(v):
    hi, lo = split_li(int(v, 0))
    return 1 if hi is None else (1 if lo == 0 else 2)

def parse(src):
    items = []   # (kind, mnemonic, operands, lineno)
    for ln, raw in enumerate(src.splitlines(), 1):
        line = raw.split('#')[0].strip()
        while True:
            m = re.match(r'^([A-Za-z_.][\w.]*):\s*(.*)$', line)
            if not m: break
            items.append(('label', m.group(1), None, ln)); line = m.group(2)
        if not line: continue
        parts = line.split(None, 1)
        mn = parts[0].lower()
        ops = [o.strip() for o in parts[1].split(',')] if len(parts) > 1 else []
        items.append(('insn', mn, ops, ln))
    return items

def size_of(mn, ops):
    if mn == 'li': return 4 * li_size(ops[1])
    if mn == 'la': return 8
    return 4

def assemble(src):
    items = parse(src)
    labels, addr = {}, 0
    for kind, mn, ops, ln in items:            # pass 1
        if kind == 'label':
            if mn in labels: raise ValueError(f"line {ln}: duplicate label {mn}")
            labels[mn] = addr
        elif mn == '.org': addr = int(ops[0], 0)
        elif mn == '.word': addr += 4 * len(ops)
        else: addr += size_of(mn, ops)
    mem, addr = {}, 0
    def emit(w): 
        nonlocal addr
        mem[addr] = w & 0xFFFFFFFF; addr += 4
    def target(tok, pc):
        return int(tok, 0) if is_num(tok) else labels[tok] - pc
    for kind, mn, ops, ln in items:            # pass 2
        if kind == 'label': continue
        try:
            pc = addr
            if mn == '.org': addr = int(ops[0], 0)
            elif mn == '.word':
                for o in ops: emit(int(o, 0))
            elif mn in R_OPS:
                f7, f3 = R_OPS[mn]; emit(enc_r(f7, reg(ops[2]), reg(ops[1]), f3, reg(ops[0]), 0x33))
            elif mn in I_OPS:
                emit(enc_i(int(ops[2], 0), reg(ops[1]), I_OPS[mn], reg(ops[0]), 0x13))
            elif mn in SH_OPS:
                f7, f3 = SH_OPS[mn]; sh = int(ops[2], 0); assert 0 <= sh < 32
                emit(enc_i((f7 << 5) | sh, reg(ops[1]), f3, reg(ops[0]), 0x13))
            elif mn in LD_OPS:
                m = re.fullmatch(r'(-?\w+)\((\w+)\)', ops[1].replace(' ', ''))
                emit(enc_i(int(m.group(1), 0), reg(m.group(2)), LD_OPS[mn], reg(ops[0]), 0x03))
            elif mn in ST_OPS:
                m = re.fullmatch(r'(-?\w+)\((\w+)\)', ops[1].replace(' ', ''))
                emit(enc_s(int(m.group(1), 0), reg(ops[0]), reg(m.group(2)), ST_OPS[mn], 0x23))
            elif mn in BR_OPS:
                emit(enc_b(target(ops[2], pc), reg(ops[1]), reg(ops[0]), BR_OPS[mn], 0x63))
            elif mn == 'lui':   emit(enc_u(int(ops[1], 0), reg(ops[0]), 0x37))
            elif mn == 'auipc': emit(enc_u(int(ops[1], 0), reg(ops[0]), 0x17))
            elif mn == 'jal':
                if len(ops) == 1: emit(enc_j(target(ops[0], pc), 1, 0x6F))
                else:             emit(enc_j(target(ops[1], pc), reg(ops[0]), 0x6F))
            elif mn == 'jalr':
                if len(ops) == 1: emit(enc_i(0, reg(ops[0]), 0, 1, 0x67))
                else:
                    m = re.fullmatch(r'(-?\w+)\((\w+)\)', ops[1].replace(' ', ''))
                    emit(enc_i(int(m.group(1), 0), reg(m.group(2)), 0, reg(ops[0]), 0x67))
            elif mn == 'j':    emit(enc_j(target(ops[0], pc), 0, 0x6F))
            elif mn == 'jr':   emit(enc_i(0, reg(ops[0]), 0, 0, 0x67))
            elif mn == 'ret':  emit(enc_i(0, 1, 0, 0, 0x67))
            elif mn == 'nop':  emit(enc_i(0, 0, 0, 0, 0x13))
            elif mn == 'mv':   emit(enc_i(0, reg(ops[1]), 0, reg(ops[0]), 0x13))
            elif mn == 'beqz': emit(enc_b(target(ops[1], pc), 0, reg(ops[0]), 0, 0x63))
            elif mn == 'bnez': emit(enc_b(target(ops[1], pc), 0, reg(ops[0]), 1, 0x63))
            elif mn == 'li':
                rd = reg(ops[0]); hi, lo = split_li(int(ops[1], 0))
                if hi is None: emit(enc_i(lo, 0, 0, rd, 0x13))
                else:
                    emit(enc_u(hi, rd, 0x37))
                    if lo != 0: emit(enc_i(lo, rd, 0, rd, 0x13))
            elif mn == 'la':
                rd = reg(ops[0]); hi, lo = split_li(labels[ops[1]] + 0x100000000 * 0)
                if hi is None: hi, lo = 0, lo
                emit(enc_u(hi, rd, 0x37)); emit(enc_i(lo, rd, 0, rd, 0x13))
            elif mn == 'fence': emit(0x0FF0000F)
            elif mn == 'ecall': emit(0x00000073)
            elif mn == 'ebreak': emit(0x00100073)
            else: raise ValueError(f"unknown mnemonic '{mn}'")
        except Exception as e:
            raise ValueError(f"line {ln}: {mn} {ops}: {e}") from e
    return mem

def to_hex(mem):
    top = max(mem) // 4 + 1 if mem else 0
    return "\n".join(f"{mem.get(4*i, 0):08x}" for i in range(top)) + "\n"

if __name__ == '__main__':
    out = to_hex(assemble(open(sys.argv[1]).read()))
    open(sys.argv[2], 'w').write(out)
