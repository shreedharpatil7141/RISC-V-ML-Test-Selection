#!/usr/bin/env python3
"""Stage 4.1 software validation; RTL/simulator behavior is not exercised."""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import rv32_asm
import rv32i_iss
import rv32c_asm
import rv32c_model
import rv32imc_iss


def oracle_length(h):
    """Independent table decode; None means the reserved >=192-bit prefix."""
    if h & 3 != 3:
        return 16
    if h & 0x1C != 0x1C:
        return 32
    if h & 0x3F == 0x1F:
        return 48
    if h & 0x7F == 0x3F:
        return 64
    if h & 0x7F == 0x7F:
        nnn = (h >> 12) & 7
        return None if nnn == 7 else 80 + 16 * nnn
    return None


def oi(imm, rs1, f3, rd, op=0x13):
    return ((imm & 4095) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op


def orr(a, b, f3, d, f7=0):
    return (f7 << 25) | (b << 20) | (a << 15) | (f3 << 12) | (d << 7) | 0x33


def ose(imm, b, a):
    return (((imm >> 5) & 127) << 25) | (b << 20) | (a << 15) | (2 << 12) | ((imm & 31) << 7) | 0x23


def ob(imm, b, a, f3):
    i = imm & 8191
    return (((i >> 12) & 1) << 31) | (((i >> 5) & 63) << 25) | (b << 20) | (a << 15) | (f3 << 12) | (((i >> 1) & 15) << 8) | (((i >> 11) & 1) << 7) | 0x63


def oj(imm, d):
    i = imm & 0x1FFFFF
    return (((i >> 20) & 1) << 31) | (((i >> 1) & 1023) << 21) | (((i >> 11) & 1) << 20) | (((i >> 12) & 255) << 12) | (d << 7) | 0x6F


def oracle_decode(h):
    """Table-oriented expected decoder, intentionally separate from ISS code."""
    h &= 65535
    if oracle_length(h) != 16:
        return "long", 0
    q, f = h & 3, h >> 13
    rd, r2 = (h >> 7) & 31, (h >> 2) & 31
    rp, ap, bp = 8 + ((h >> 2) & 7), 8 + ((h >> 7) & 7), 8 + ((h >> 2) & 7)
    imm6 = ((h >> 2) & 31) | (((h >> 12) & 1) << 5)
    si6 = imm6 - 64 if imm6 & 32 else imm6

    def legal(insn): return "legal", insn & 0xFFFFFFFF
    def hint(): return "hint", 0x00000013
    def bad(): return "illegal", 0

    if q == 0:
        if f == 0:
            n = (((h >> 11) & 3) << 4) | (((h >> 7) & 15) << 6) | (((h >> 6) & 1) << 2) | (((h >> 5) & 1) << 3)
            return bad() if not n else legal(oi(n, 2, 0, rp))
        if f in (2, 6):
            n = (((h >> 10) & 7) << 3) | (((h >> 6) & 1) << 2) | (((h >> 5) & 1) << 6)
            return legal(oi(n, ap, 2, rp, 0x03)) if f == 2 else legal(ose(n, bp, ap))
        return bad()

    if q == 1:
        if f == 0:
            if rd == 0:
                return legal(0x13) if si6 == 0 else hint()
            return hint() if si6 == 0 else legal(oi(si6, rd, 0, rd))
        if f == 1 or f == 5:
            j = (((h >> 12) & 1) << 11) | (((h >> 11) & 1) << 4) | (((h >> 9) & 3) << 8) | (((h >> 8) & 1) << 10) | (((h >> 7) & 1) << 6) | (((h >> 6) & 1) << 7) | (((h >> 3) & 7) << 1) | (((h >> 2) & 1) << 5)
            j = j - 4096 if j & 2048 else j
            return legal(oj(j, 1 if f == 1 else 0))
        if f == 2:
            return hint() if rd == 0 else legal(oi(si6, 0, 0, rd))
        if f == 3:
            if rd == 2:
                n = (((h >> 12) & 1) << 9) | (((h >> 6) & 1) << 4) | (((h >> 5) & 1) << 6) | (((h >> 3) & 3) << 7) | (((h >> 2) & 1) << 5)
                n = n - 1024 if n & 512 else n
                return bad() if n == 0 else legal(oi(n, 2, 0, 2))
            if si6 == 0:
                return bad()
            if rd == 0:
                return hint()
            return legal(((si6 & 0xFFFFF) << 12) | (rd << 7) | 0x37)
        if f == 4:
            band = (h >> 10) & 3
            if band < 2:
                sh = ((h >> 2) & 31) | (((h >> 12) & 1) << 5)
                if sh & 32: return bad()
                if sh == 0: return hint()
                return legal(oi(sh | (0x400 if band else 0), ap, 5, ap))
            if band == 2:
                return legal(oi(si6, ap, 7, ap))
            if h & 0x1000:
                return bad()
            code = (h >> 5) & 3
            return legal(orr(ap, bp, (0, 4, 6, 7)[code], ap, 0x20 if code == 0 else 0))
        if f in (6, 7):
            b = (((h >> 12) & 1) << 8) | (((h >> 10) & 3) << 3) | (((h >> 5) & 3) << 6) | (((h >> 3) & 3) << 1) | (((h >> 2) & 1) << 5)
            b = b - 512 if b & 256 else b
            return legal(ob(b, 0, ap, 0 if f == 6 else 1))
        return bad()

    if q == 2:
        if f == 0:
            sh = ((h >> 2) & 31) | (((h >> 12) & 1) << 5)
            if sh & 32: return bad()
            if rd == 0 or sh == 0: return hint()
            return legal(oi(sh, rd, 1, rd))
        if f == 2:
            n = (((h >> 12) & 1) << 5) | (((h >> 4) & 7) << 2) | (((h >> 2) & 3) << 6)
            return bad() if rd == 0 else legal(oi(n, 2, 2, rd, 0x03))
        if f == 4:
            hi = (h >> 12) & 1
            if hi == 0 and r2 == 0:
                return bad() if rd == 0 else legal(oi(0, rd, 0, 0, 0x67))
            if hi == 0:
                return hint() if rd == 0 else legal(orr(0, r2, 0, rd))
            if r2 == 0:
                if rd == 0: return legal(0x00100073)
                return legal(oi(0, rd, 0, 1, 0x67))
            return hint() if rd == 0 else legal(orr(rd, r2, 0, rd))
        if f == 6:
            n = (((h >> 9) & 15) << 2) | (((h >> 7) & 3) << 6)
            return legal(ose(n, r2, 2))
        return bad()
    return bad()


def check_encoding_and_length():
    from collections import Counter
    classes, lengths = Counter(), Counter()
    failures = 0
    for h in range(65536):
        expected_len = oracle_length(h)
        lengths[expected_len] += 1
        try:
            got_len = rv32c_model.instruction_length(h)
        except Exception as exc:
            failures += 1
            if failures < 12:
                print(f"LENGTH_ERROR raw={h:04x} {type(exc).__name__}: {exc}")
            continue
        if expected_len != got_len:
            failures += 1
            if failures < 12:
                print(f"LENGTH_DIFF raw={h:04x} expected={expected_len} got={got_len}")
            continue
        try:
            expected_status, expected_word = oracle_decode(h)
            got = rv32c_model.decode16(h)
        except Exception as exc:
            failures += 1
            if failures < 12:
                print(f"DECODE_ERROR raw={h:04x} {type(exc).__name__}: {exc}")
            continue
        classes[expected_status] += 1
        if (got.status, got.expanded) != (expected_status, expected_word):
            failures += 1
            if failures < 12:
                print(f"DECODE_DIFF raw={h:04x} expected={expected_status}/{expected_word:08x} got={got.status}/{got.expanded:08x} reason={got.reason}")
    expected_lengths = {16: 49152, 32: 14336, 48: 1024, 64: 512,
                        80: 64, 96: 64, 112: 64, 128: 64, 144: 64,
                        160: 64, 176: 64, None: 64}
    expected_classes = {"legal": 28461, "hint": 362, "illegal": 20329, "long": 16384}
    length_ok = lengths == expected_lengths
    class_ok = classes == expected_classes
    length_counts = dict(sorted(lengths.items(), key=lambda pair: -1 if pair[0] is None else pair[0]))
    unsupported = sum(count for length, count in lengths.items() if length is None or length > 32)
    print("RV32C_LENGTH_SWEEP", "PASS" if length_ok else "FAIL", f"prefix_counts={length_counts} project_unsupported={unsupported} frozen_lengths=16,32")
    print("RV32C_ENCODING_SWEEP", "PASS" if failures == 0 and class_ok else "FAIL", f"halfwords=65536 mismatches={failures} classes={dict(sorted(classes.items()))}")
    return failures == 0 and length_ok and class_ok, classes


def check_anchors():
    anchors = [
        ("c.nop", "", 0x0001), ("c.addi", "x1, 1", 0x0085),
        ("c.li", "x10, -1", 0x557d), ("c.j", "0", 0xa001),
        ("c.jal", "2", 0x2009), ("c.ebreak", "", 0x9002),
        ("c.lwsp", "x1, 0", 0x4082), ("c.swsp", "x1, 0", 0xc006),
        ("c.addi4spn", "x8, 4", 0x0040), ("c.addi4spn", "x8, 1020", 0x1fe0),
        ("c.lw", "x8, 0(x8)", 0x4000),
        ("c.sw", "x8, 0(x8)", 0xc000), ("c.jalr", "x5", 0x9282),
        ("c.beqz", "x8, 2", 0xc009), ("c.beqz", "x8, -256", 0xd001),
        ("c.addi16sp", "-512", 0x7101), ("c.addi16sp", "496", 0x617d),
        ("c.addi16sp", "-16", 0x717d), ("c.lui", "x8, 1", 0x6405),
        ("c.lui", "x0, 1", 0x6005), ("c.addi", "x1, -32", 0x1081),
        ("c.addi", "x1, 31", 0x00fd), ("c.li", "x1, -32", 0x5081),
        ("c.lw", "x15, 124(x15)", 0x5ffc), ("c.lwsp", "x31, 252", 0x5ffe),
        ("c.swsp", "x31, 252", 0xdffe), ("c.slli", "x31, 31", 0x0ffe),
        ("c.slli", "x1, 1", 0x0086), ("c.srli", "x8, 0", 0x8001),
        ("c.srli", "x8, 1", 0x8005), ("c.srai", "x8, 1", 0x8405),
        ("c.andi", "x8, -1", 0x987d), ("c.sub", "x8, x9", 0x8c05),
        ("c.mv", "x1, x2", 0x808a), ("c.add", "x1, x2", 0x908a),
    ]
    bad = 0
    for mn, args, expected in anchors:
        try:
            image = rv32c_asm.assemble_bytes(mn + (" " + args if args else ""), c_enabled=True)
            got = image.get(0, 0) | (image.get(1, 0) << 8)
            packed = rv32c_asm.to_words(image)[0] & 0xFFFF
        except Exception as exc:
            bad += 1
            print(f"ASM_ANCHOR_ERROR {mn} {args}: {type(exc).__name__}: {exc}")
            continue
        if got != expected:
            bad += 1
            print(f"ASM_ANCHOR_DIFF {mn} {args} expected={expected:04x} got={got:04x}")
        if packed != expected:
            bad += 1
            print(f"ASM_PACKING_DIFF {mn} {args} expected_le_halfword={expected:04x} got={packed:04x}")
        try:
            dec = rv32c_model.decode16(expected)
            status, exp_word = oracle_decode(expected)
        except Exception as exc:
            bad += 1
            print(f"ANCHOR_DECODE_ERROR raw={expected:04x}: {type(exc).__name__}: {exc}")
            continue
        if (dec.status, dec.expanded) != (status, exp_word):
            bad += 1
            print(f"ANCHOR_DECODE_DIFF {expected:04x} expected={status}/{exp_word:08x} got={dec.status}/{dec.expanded:08x}")

    rejected = [
        "c.addi4spn x8, 0", "c.lw x7, 0(x8)", "c.srli x8, 32",
        "c.addi16sp 0", "c.lui x2, 1", "c.jr x0", "c.mul x8, x9",
        "c.andi x8, 32",
    ]
    reject_errors = 0
    for src in rejected:
        try:
            rv32c_asm.assemble_bytes(src, c_enabled=True)
            reject_errors += 1
            print(f"ASM_ACCEPTED_INVALID {src}")
        except (ValueError, AssertionError):
            pass
        except Exception as exc:
            reject_errors += 1
            print(f"ASM_REJECT_ERROR {src}: {type(exc).__name__}: {exc}")
    bad += reject_errors
    print(f"RV32C_HAND_ANCHORS {'PASS' if bad == 0 else 'FAIL'} checked={len(anchors)} rejected_encodings={len(rejected)} errors={bad}")
    return bad == 0


def check_pseudos_and_labels():
    """Check fixed-size li/la expansion, aliases, and mixed-width label values."""
    cases = [
        ("la_forward_alias", "la t0, target\nc.nop\ntarget: c.ebreak\n", 10, 0x00A28293),
        ("la_backward", "target: c.nop\nc.nop\nla x5, target\nc.ebreak\n", 0, 0x00028293),
        ("la_mixed_address", ".org 2\nc.nop\n.org 6\nla fp, target\ntarget: c.ebreak\n", 14, 0x00E40413),
    ]
    bad = 0
    for name, source, address, expected_addi in cases:
        try:
            image = rv32c_asm.assemble_bytes(source, c_enabled=True)
            # `la` remains a fixed 8-byte LUI+ADDI expansion at address 0 or
            # 6; independently check its second word and resolved label value.
            pc = 0 if name == "la_forward_alias" else 4 if name == "la_backward" else 6
            # The final case starts at PC=6, so this ordinary instruction
            # crosses a word boundary; recover all four bytes by address.
            addi = sum(image[pc + 4 + i] << (8 * i) for i in range(4))
            if len([a for a in image if pc <= a < pc + 8]) != 8 or addi != expected_addi:
                bad += 1
                print(f"ASM_LABEL_DIFF {name} expected_addi={expected_addi:08x} got={addi:08x} la_bytes={sum(pc <= a < pc + 8 for a in image)}")
        except Exception as exc:
            bad += 1
            print(f"ASM_LABEL_ERROR {name}: {type(exc).__name__}: {exc}")

    # li remains fixed by its existing size rule and numeric operands are not
    # mistaken for symbols. Include both one-word and two-word aliases.
    li_cases = [("li_alias_small", "li fp, -1\n", [0xFFF00413]),
                ("li_alias_large", "li t0, 0x12345678\n", [0x123452B7, 0x67828293])]
    for name, source, expected in li_cases:
        try:
            image = rv32c_asm.assemble_bytes(source, c_enabled=False)
            got = rv32c_asm.to_words(image)
            if got != expected:
                bad += 1
                print(f"ASM_LI_DIFF {name} expected={expected} got={[f'{w:08x}' for w in got]}")
        except Exception as exc:
            bad += 1
            print(f"ASM_LI_ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"RV32C_PSEUDO_LABELS {'PASS' if bad == 0 else 'FAIL'} cases={len(cases) + len(li_cases)} failures={bad}")
    return bad == 0


def _words(byte_mem):
    return rv32c_asm.to_words(byte_mem)


def check_c_disabled_baseline():
    dirs = ("rv32i", "pipeline", "pipeline_m", "m_extension", "pipeline_div", "pipeline_div_coverage")
    tests = traces = image_matches = errors = 0
    for folder in dirs:
        test_dir = os.path.join(ROOT, "tests", "directed", folder)
        with open(os.path.join(test_dir, "manifest.csv"), newline="", encoding="utf-8") as mf:
            rows = list(csv.DictReader(mf))
        for row in rows:
            name = row["name"]
            tests += 1
            try:
                with open(os.path.join(test_dir, name + ".s"), encoding="utf-8") as src:
                    text = src.read()
                old_mem = rv32_asm.assemble(text)
                new_mem = rv32c_asm.assemble_bytes(text, c_enabled=False)
                new_words = _words(new_mem)
                old_words = [old_mem.get(4 * i, 0) for i in range(max(old_mem) // 4 + 1)]
                images_same = new_words == old_words
                image_matches += images_same
                old_result = rv32i_iss.run(old_words)
                new_result = rv32imc_iss.run(new_words, c_enabled=False)
                same = old_result == new_result
                traces += same
            except Exception as exc:
                images_same = same = False
                print(f"C_DISABLED_CASE_ERROR {folder}/{name}: {type(exc).__name__}: {exc}")
            if not images_same or not same:
                errors += 1
                print(f"C_DISABLED_DIFF {folder}/{name} image={images_same} trace_state={same}")
    print(f"C_DISABLED_STAGE3_COMPAT {'PASS' if errors == 0 else 'FAIL'} tests={tests} identical_images={image_matches}/{tests} identical_iss_results_and_traces={traces}/{tests}")
    return tests == 209 and errors == 0


def check_software_directed():
    test_dir = os.path.join(ROOT, "tests", "directed", "rv32imc_software")
    expected_regs = {
        "mixed_cross": {8: 18}, "jump_link": {1: 2}, "jalr_link": {1: 10},
        "branches": {8: 0, 9: 2}, "loads_stores": {8: 17, 9: 17, 10: 17, 11: 0x4000},
        "hints_overlap": {8: 14}, "reserved": {}, "floating_illegal": {},
        "custom_shift_illegal": {}, "load_boundary": {8: 0x10000},
        "last_halfword": {}, "missing_second_parcel": {},
    }
    records = list(csv.DictReader(open(os.path.join(test_dir, "manifest.csv"), newline="", encoding="utf-8")))
    bad = 0
    for row in records:
        name = row["name"]
        try:
            with open(os.path.join(test_dir, name + ".s"), encoding="utf-8") as source:
                image = rv32c_asm.assemble_bytes(source.read(), c_enabled=True)
            cause, regs, trace, footer, oob, instret = rv32imc_iss.run(_words(image), c_enabled=True, start_pc=int(row["start_pc"]))
        except Exception as exc:
            bad += 1
            print(f"RV32IMC_CASE_ERROR {name}: {type(exc).__name__}: {exc}")
            continue
        passed = cause == int(row["cause"]) and instret == int(row["instret"]) and oob == 0
        passed = passed and all(regs[r] == value for r, value in expected_regs[name].items())
        if name == "mixed_cross":
            passed = passed and [int(line.split()[3]) for line in trace] == [2, 4, 2]
            passed = passed and int(trace[1].split()[2], 16) == 0x01100413
        if name == "loads_stores":
            passed = passed and "MEM 00004000 00000011" in footer and "MEM 00004004 00000011" in footer
        if name == "jump_link":
            passed = passed and trace[0].startswith("I 00000000 ") and int(trace[0].split()[3]) == 2
        if name == "jalr_link":
            passed = passed and int(trace[2].split()[3]) == 2
        stop = next((line for line in footer if line.startswith("STOP ")), "")
        if name == "reserved":
            passed = passed and stop == "STOP 00000000 00008000 02 3"
        if name == "floating_illegal":
            passed = passed and stop == "STOP 00000000 00002000 02 3"
        if name == "custom_shift_illegal":
            passed = passed and stop == "STOP 00000000 00001402 02 3"
        if name == "missing_second_parcel":
            passed = passed and stop == "STOP 0000fffe 00000093 04 9"
        if name == "last_halfword":
            passed = passed and stop == "STOP 00010000 00000000 00 9"
        if not passed:
            bad += 1
            print(f"RV32IMC_CASE_FAIL {name} cause={cause} instret={instret} oob={oob} trace={trace}")
        else:
            print(f"RV32IMC_CASE_PASS {name} cause={cause} instret={instret} trace_rows={len(trace)}")
    print(f"RV32IMC_DIRECTED {'PASS' if bad == 0 else 'FAIL'} tests={len(records)} failures={bad}")
    return bad == 0 and len(records) == 12


def check_m_metadata():
    src = "addi x5, x0, 7\naddi x6, x0, 2\nmul x7, x5, x6\nc.li x8, 1\ndiv x9, x7, x6\nc.ebreak\n"
    image = rv32c_asm.assemble_bytes(src, c_enabled=True)
    events, costs = [], []
    cause, regs, trace, footer, oob, n = rv32imc_iss.run(_words(image), c_enabled=True, m_events=events, divider_cost_events=costs)
    expected_m_events = [
        (8, 0x026283B3, 0, 7, 5, 6, 7, 2, 14),
        (14, 0x0263C4B3, 4, 9, 7, 6, 14, 2, 7),
    ]
    expected_costs = [(14, 0x0263C4B3, 4, 33)]
    fields_ok = (cause == 2 and regs[7] == 14 and regs[9] == 7 and events == expected_m_events
                 and costs == expected_costs and oob == 0)
    print(f"RV32IMC_M_METADATA {'PASS' if fields_ok else 'FAIL'} expected_m_events={expected_m_events} actual_m_events={events}")
    print(f"RV32IMC_M_COST_FIELDS expected={expected_costs} actual={costs} decoded_div=pc=0x0000000e raw=0x{0x0263C4B3:08x} opcode=0x33 funct7=1 funct3=4 rd=x9 rs1=x7 rs2=x6 length_bytes=4 extra_cycles=33 instret={n}")
    return fields_ok


def check_assembler_group():
    anchors_ok = pseudos_ok = False
    try:
        anchors_ok = check_anchors()
    except Exception as exc:
        print(f"RV32C_HAND_ANCHORS ERROR {type(exc).__name__}: {exc}")
    try:
        pseudos_ok = check_pseudos_and_labels()
    except Exception as exc:
        print(f"RV32C_PSEUDO_LABELS ERROR {type(exc).__name__}: {exc}")
    return anchors_ok and pseudos_ok


def main():
    groups = [
        ("encoding_and_length", lambda: check_encoding_and_length()[0]),
        ("assembler_anchors_and_labels", check_assembler_group),
        ("c_disabled_stage3_compat", check_c_disabled_baseline),
        ("rv32imc_directed_iss", check_software_directed),
        ("rv32m_metadata", check_m_metadata),
    ]
    failed = 0
    completed = 0
    for name, check in groups:
        completed += 1
        try:
            if not check():
                failed += 1
                print(f"STAGE4_1_GROUP_FAIL {name}")
        except Exception as exc:
            failed += 1
            print(f"STAGE4_1_GROUP_ERROR {name}: {type(exc).__name__}: {exc}")
    ok = failed == 0 and completed == 5
    print(f"STAGE4_1_SOFTWARE_VALIDATION {'PASS' if ok else 'FAIL'} checks={completed} failures={failed}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
