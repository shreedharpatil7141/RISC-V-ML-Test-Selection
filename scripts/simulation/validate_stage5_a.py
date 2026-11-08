#!/usr/bin/env python3
"""Run Stage 5.1 RV32A software and Stage 4 compatibility validation groups.

Run from the repository root. The compatibility group compares all 230
Stage 4 source images, ISS architectural traces, and saved golden/pipeline
traces with the released Stage 4 artifact directory supplied by --stage4-dir.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import rv32_asm
import rv32a_model
import rv32c_asm
import rv32imc_iss

MASK32 = 0xFFFFFFFF
STAGE4_DEFAULT = ROOT / "sim_out_stage4_4_xsim_20261108T154108Z"
LEGACY_SUITES = ("rv32i", "pipeline", "pipeline_m", "m_extension", "pipeline_div", "pipeline_div_coverage")
C_SUITES = ("rv32imc", "rv32imc_pipeline")
ATOMIC_NAMES = ["lr.w", "sc.w", "amoswap.w", "amoadd.w", "amoxor.w", "amoand.w", "amoor.w",
                "amomin.w", "amomax.w", "amominu.w", "amomaxu.w"]


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def _words_from_bytes(memory):
    return rv32c_asm.to_words(memory)


def group_encoding():
    # Hand-derived anchors use rd=x1, rs1=x2, rs2=x3. The expected words are
    # literal encodings from the v20260120 RV32A format table, not generated
    # using the assembler or decoder under test.
    anchors = {
        "lr.w x1, (x2)": 0x100120AF,
        "sc.w x1, x3, (x2)": 0x183120AF,
        "amoswap.w x1, x3, (x2)": 0x083120AF,
        "amoadd.w x1, x3, (x2)": 0x003120AF,
        "amoxor.w x1, x3, (x2)": 0x203120AF,
        "amoand.w x1, x3, (x2)": 0x603120AF,
        "amoor.w x1, x3, (x2)": 0x403120AF,
        "amomin.w x1, x3, (x2)": 0x803120AF,
        "amomax.w x1, x3, (x2)": 0xA03120AF,
        "amominu.w x1, x3, (x2)": 0xC03120AF,
        "amomaxu.w x1, x3, (x2)": 0xE03120AF,
        "amoadd.w.aq x1, x3, (x2)": 0x043120AF,
        "amoadd.w.rl x1, x3, (x2)": 0x023120AF,
        "amoadd.w.aqrl x1, x3, (x2)": 0x063120AF,
    }
    for source, expected in anchors.items():
        image = rv32c_asm.assemble_bytes(source + "\necall\n", c_enabled=False, a_enabled=True)
        actual = rv32c_asm.to_words(image)[0]
        expect(actual == expected, f"anchor {source}: expected={expected:08x} actual={actual:08x}")
        decoded = rv32a_model.decode_atomic(actual)
        expect(decoded is not None, f"anchor did not decode: {source} {actual:08x}")
    for assemble_disabled in (
        lambda: rv32c_asm.assemble_bytes("amoadd.w x1, x3, (x2)\n", c_enabled=False, a_enabled=False),
        lambda: rv32_asm.assemble("amoadd.w x1, x3, (x2)\n"),
    ):
        try:
            assemble_disabled()
        except Exception:
            continue
        raise AssertionError("an A-disabled/legacy assembler accepted an A mnemonic")
    return len(anchors)


def group_legality():
    checked = legal = 0
    for funct5 in range(32):
        for funct3 in range(8):
            for rs2 in (0, 1):
                for order in range(4):
                    raw = (funct5 << 27) | ((order & 1) << 26) | (((order >> 1) & 1) << 25) | (rs2 << 20) | (2 << 15) | (funct3 << 12) | (1 << 7) | 0x2F
                    got = rv32a_model.decode_atomic(raw)
                    expected_name = rv32a_model.FUNCT5_TO_NAME.get(funct5)
                    expected_legal = funct3 == 2 and expected_name is not None and (expected_name != "lr.w" or rs2 == 0)
                    expect((got is not None) == expected_legal,
                           f"legality raw={raw:08x} expected={expected_legal} actual={got}")
                    if got is not None:
                        legal += 1
                        expect(got["aq"] == (order & 1) and got["rl"] == ((order >> 1) & 1),
                               f"aq/rl decode raw={raw:08x} fields={got}")
                    checked += 1
    expect(checked == 2048 and legal == 84, f"encoding matrix checked={checked} legal={legal}, expected 2048/84")
    for raw in (0x0000002F, 0x0000302F, 0x0000202B, 0x00002033):
        expect(rv32a_model.decode_atomic(raw) is None, f"reserved/non-A raw accepted: {raw:08x}")
    # RV64 .D and non-word/subword atomics are outside this RV32-only build.
    for source in ("lr.d x1, (x2)", "amoadd.d x1, x3, (x2)", "amoadd.b x1, x3, (x2)", "amoadd.h x1, x3, (x2)"):
        try:
            rv32_asm.assemble(source + "\n")
        except Exception:
            continue
        raise AssertionError(f"out-of-scope mnemonic was accepted: {source}")
    return checked


def group_amo_arithmetic():
    # Explicit expected results are independent of rv32a_model.amo_result.
    vectors = [
        (0x80000000, 0x7FFFFFFF, {"amoswap.w": 0x7FFFFFFF, "amoadd.w": 0xFFFFFFFF,
         "amoxor.w": 0xFFFFFFFF, "amoand.w": 0, "amoor.w": 0xFFFFFFFF, "amomin.w": 0x80000000,
         "amomax.w": 0x7FFFFFFF, "amominu.w": 0x7FFFFFFF, "amomaxu.w": 0x80000000}),
        (0x7FFFFFFF, 1, {"amoswap.w": 1, "amoadd.w": 0x80000000, "amoxor.w": 0x7FFFFFFE,
         "amoand.w": 1, "amoor.w": 0x7FFFFFFF, "amomin.w": 1, "amomax.w": 0x7FFFFFFF,
         "amominu.w": 1, "amomaxu.w": 0x7FFFFFFF}),
        (0xFFFFFFFF, 0, {"amoswap.w": 0, "amoadd.w": 0xFFFFFFFF, "amoxor.w": 0xFFFFFFFF,
         "amoand.w": 0, "amoor.w": 0xFFFFFFFF, "amomin.w": 0xFFFFFFFF, "amomax.w": 0,
         "amominu.w": 0, "amomaxu.w": 0xFFFFFFFF}),
        (0x80000000, 0xFFFFFFFF, {"amoswap.w": 0xFFFFFFFF, "amoadd.w": 0x7FFFFFFF,
         "amoxor.w": 0x7FFFFFFF, "amoand.w": 0x80000000, "amoor.w": 0xFFFFFFFF,
         "amomin.w": 0x80000000, "amomax.w": 0xFFFFFFFF, "amominu.w": 0x80000000,
         "amomaxu.w": 0xFFFFFFFF}),
    ]
    count = 0
    for old, source, expected in vectors:
        for op in ATOMIC_NAMES[2:]:
            actual = rv32a_model.amo_result(op, old, source)
            expect(actual == expected[op], f"{op} old={old:08x} source={source:08x} expected={expected[op]:08x} actual={actual:08x}")
            count += 1
    return count


def _prepare_source(source_path, c_enabled, a_enabled):
    source = source_path.read_text(encoding="utf-8")
    image = rv32c_asm.assemble_bytes(source, c_enabled=c_enabled, a_enabled=a_enabled)
    return source, image, _words_from_bytes(image)


def group_directed_iss():
    cases = list(csv.DictReader((ROOT / "tests/directed/rv32ima_software/manifest.csv").open(newline="")))
    expected = {
        "atomic_ops": {"cause": 1, "instret": 14, "regs": {4:0x80000000,5:0x7FFFFFFF,6:0xFFFFFFFE,7:0x7FFFFFFE,8:0x7FFFFFFE,9:0xFFFFFFFE,10:0xFFFFFFFE,11:0xFFFFFFFE,12:0x7FFFFFFF}, "mem": {0x5000:0x80000000}},
        "lrsc_sequences": {"cause": 1, "instret": 16, "regs": {3:0x11223344,5:0,6:1,7:0x55667788,9:1,10:0x55667788,11:1,12:1}, "mem": {0x5000:0x55667788}},
        "operand_overlap": {"cause": 1, "instret": 18, "regs": {1:0x89ABCDEF,3:0,5:0x89ABCDEF,7:0x13579BDF,8:0x76543210,9:0}, "mem": {0x5000:0x0F0F0F0F}},
        "atomic_orders": {"cause": 1, "instret": 13, "regs": {3:0,4:1,5:2,6:3,7:1,8:4,9:4}, "mem": {0x5000:2}},
        "reserved_encoding": {"cause": 3, "instret": 1, "regs": {}, "mem": {}},
        "lr_misaligned": {"cause": 4, "instret": 5, "regs": {}, "mem": {0x5000:0xA55AA55A}},
        "sc_misaligned": {"cause": 5, "instret": 6, "regs": {}, "mem": {0x5000:0xA55AA55A}},
        "amo_misaligned": {"cause": 5, "instret": 5, "regs": {}, "mem": {0x5000:0xA55AA55A}},
        "lr_access_fault": {"cause": 7, "instret": 5, "regs": {}, "mem": {0x5000:0xA55AA55A}},
        "sc_access_fault": {"cause": 8, "instret": 6, "regs": {}, "mem": {0x5000:0xA55AA55A}},
        "amo_access_fault": {"cause": 8, "instret": 6, "regs": {}, "mem": {0x5000:0xA55AA55A}},
        "amo_last_word": {"cause": 1, "instret": 7, "regs": {4:0x55,5:0x56}, "mem": {}},
    }
    seen = set()
    for row in cases:
        name = row["name"]
        src_path = ROOT / "tests/directed/rv32ima_software" / (name + ".s")
        _, _, words = _prepare_source(src_path, c_enabled=False, a_enabled=True)
        a_events = []
        cause, regs, trace, footer, oob, instret = rv32imc_iss.run(words, a_enabled=True, a_events=a_events)
        exp = expected[name]
        expect(cause == exp["cause"], f"{name}: expected cause={exp['cause']} actual={cause}")
        expect(instret == exp["instret"], f"{name}: expected retired={exp['instret']} actual={instret}")
        expect(oob == 0, f"{name}: image_oob={oob}")
        for reg, value in exp["regs"].items():
            expect(regs[reg] == value, f"{name}: x{reg} expected={value:08x} actual={regs[reg]:08x}")
        for addr, value in exp["mem"].items():
            actual = next((int(line.split()[2], 16) for line in footer if line.startswith(f"MEM {addr:08x} ")), 0)
            expect(actual == value, f"{name}: mem[{addr:08x}] expected={value:08x} actual={actual:08x}")
        if name in {"lr_misaligned", "sc_misaligned", "amo_misaligned", "lr_access_fault", "sc_access_fault", "amo_access_fault"}:
            bad_atomic_pc = int(footer[0].split()[1], 16)
            expect(all(not line.startswith(f"I {bad_atomic_pc:08x} ") for line in trace), f"{name}: faulting atomic retired")
            expect(not any(e[0] == bad_atomic_pc for e in a_events), f"{name}: faulting atomic entered retire sidecar")
        if name == "lrsc_sequences":
            statuses = [e[12] for e in a_events if e[2] == "sc.w"]
            # The source has five SC attempts: initial success, immediate
            # retry without a new LR, address mismatch, then two attempts
            # after an intervening store. Every completed attempt consumes
            # the reservation, so both final attempts fail.
            expect(statuses == [0, 1, 1, 1, 1], f"LR/SC success/retry/mismatch/store/retry statuses expected=[0,1,1,1,1] actual={statuses}")
            expect(all((e[11] is None) for e in a_events if e[2] == "sc.w" and e[12] != 0),
                   "failed SC sidecar must not describe a memory write")
        if name == "atomic_orders":
            orders = [(e[3], e[4]) for e in a_events]
            expected_orders = [(0,0),(1,0),(0,1),(1,1),(1,0),(0,1),(1,1),(0,0),(0,0),(0,0)]
            expect(orders == expected_orders, f"atomic aq/rl retirement sidecar expected={expected_orders} actual={orders}")
            statuses = [e[12] for e in a_events if e[2] == "sc.w"]
            expect(statuses == [1,0], f"SC failure/success including rd=x0 expected=[1,0] actual={statuses}")
        seen.add(name)
    expect(len(cases) == 12 and seen == set(expected), f"directed inventory expected=12 actual={len(cases)} names={sorted(seen)}")
    boundary_path = ROOT / "tests/directed/rv32ima_software/amo_last_word.s"
    _, _, boundary_words = _prepare_source(boundary_path, c_enabled=False, a_enabled=True)
    boundary_events = []
    _, boundary_regs, _, _, _, _ = rv32imc_iss.run(boundary_words, a_enabled=True, a_events=boundary_events)
    expect(len(boundary_events) == 1 and boundary_events[0][8:12] == (0xFFFC,0x55,1,0x56),
           f"last-word AMO sidecar expected address/old/source/new=(fffc,55,1,56), got={boundary_events}")
    expect(boundary_regs[4] == 0x55 and boundary_regs[5] == 0x56,
           f"last-word atomic readback expected rd4=55 rd5=56 actual={boundary_regs[4]:08x}/{boundary_regs[5]:08x}")

    c_source = ROOT / "tests/directed/rv32imac_software/amo_at_halfword_pc.s"
    _, c_image, c_words = _prepare_source(c_source, c_enabled=True, a_enabled=True)
    events = []
    cause, regs, trace, footer, oob, instret = rv32imc_iss.run(c_words, c_enabled=True, a_enabled=True, a_events=events)
    expect(cause == 1 and instret == 5 and oob == 0, f"amo_at_halfword_pc cause={cause} instret={instret} oob={oob}")
    expect(len(events) == 1 and events[0][0] == 14, f"AMO halfword-PC event expected pc=14 actual={events}")
    expect(regs[3] == 0x80000000, f"AMO halfword-PC rd expected=80000000 actual={regs[3]:08x}")
    expect(any(line == "MEM 00005000 80000000" for line in footer), "AMO halfword-PC final memory mismatch")
    expect(len(c_image) > 0, "mixed-width A test image is empty")

    # The same supported A word remains illegal in explicit A-disabled mode.
    raw = _words_from_bytes(rv32c_asm.assemble_bytes("amoadd.w x1, x3, (x2)\necall\n", a_enabled=True))[0]
    disabled_cause, _, disabled_trace, _, _, _ = rv32imc_iss.run([raw, 0x73], c_enabled=False, a_enabled=False)
    expect(disabled_cause == 3 and not disabled_trace, f"A-disabled mode accepted AMO: cause={disabled_cause} trace={disabled_trace}")
    return len(cases) + 1


def _source_sets():
    result = []
    for suite in LEGACY_SUITES:
        directory = ROOT / "tests/directed" / suite
        rows = list(csv.DictReader((directory / "manifest.csv").open(newline="")))
        for row in rows:
            result.append((row["name"], directory / (row["name"] + ".s"), False, False, row))
    for suite in C_SUITES:
        directory = ROOT / "tests/directed" / suite
        rows = list(csv.DictReader((directory / "manifest.csv").open(newline="")))
        for row in rows:
            result.append((row["name"], directory / (row["name"] + ".s"), True, False, row))
    return result


def group_stage4_compat(stage4_dir):
    errors = []
    sources = _source_sets()
    if len(sources) != 230:
        errors.append(f"source inventory expected=230 actual={len(sources)}")
    for index, (name, source_path, c_enabled, _, _row) in enumerate(sources, 1):
        try:
            if not source_path.is_file():
                raise FileNotFoundError(source_path)
            if c_enabled:
                _, byte_image, words = _prepare_source(source_path, True, False)
                expected_image = rv32c_asm.to_hex(byte_image)
                image_path = stage4_dir / "c_hex" / f"{name}.hex"
                iss_path = stage4_dir / "c_iss" / f"{name}.trace"
                current = rv32imc_iss.run(words, c_enabled=True, a_enabled=False)
                current_trace = "TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data\n" + "\n".join(current[2] + current[3]) + "\n"
            else:
                byte_words = rv32_asm.assemble(source_path.read_text(encoding="utf-8"))
                expected_image = rv32_asm.to_hex(byte_words)
                words = [byte_words.get(4*i, 0) for i in range(max(byte_words)//4 + 1)] if byte_words else []
                image_path = stage4_dir / "hex" / f"{name}.hex"
                iss_path = stage4_dir / "iss" / f"{name}.iss.trace"
                current = rv32imc_iss.run(words, c_enabled=False, a_enabled=False)
                current_trace = "\n".join(current[2] + current[3]) + "\n"
            saved_image = image_path.read_text(encoding="ascii")
            saved_iss = iss_path.read_text(encoding="ascii")
            if saved_image != expected_image:
                errors.append(f"{name}: image differs from released Stage 4 artifact {image_path}")
            if saved_iss != current_trace:
                errors.append(f"{name}: A-disabled ISS trace differs from saved Stage 4 reference {iss_path}")
            golden_path = stage4_dir / f"{name}.golden.trace"
            pipe_path = stage4_dir / f"{name}.pipe.trace"
            golden = golden_path.read_text(encoding="ascii")
            pipe = pipe_path.read_text(encoding="ascii")
            if golden != saved_iss:
                errors.append(f"{name}: saved golden trace differs from saved Stage 4 ISS reference")
            if pipe != saved_iss:
                errors.append(f"{name}: saved pipeline trace differs from saved Stage 4 ISS reference")
            if current[0] != int(_row["expect_cause"]) or current[4] != 0:
                errors.append(f"{name}: current ISS expected_cause={_row['expect_cause']} actual_cause={current[0]} oob={current[4]}")
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
        if index % 25 == 0 or index == len(sources):
            print(f"COMPAT_PROGRESS {index}/{len(sources)} errors={len(errors)}", flush=True)
    if errors:
        for error in errors[:30]:
            print("COMPAT_ERROR " + error, file=sys.stderr)
        raise AssertionError(f"230-case Stage 4 compatibility has {len(errors)} errors")
    return len(sources)


def run_group(name, fn):
    try:
        count = fn()
        print(f"STAGE5_A_{name} PASS checks={count}", flush=True)
        return True
    except Exception as exc:
        print(f"STAGE5_A_{name} FAIL: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage4-dir", type=Path, default=STAGE4_DEFAULT,
                        help="preserved Stage 4.4 XSim output directory containing all 230 images and traces")
    args = parser.parse_args()
    results = []
    # Groups are isolated so a defect in one does not suppress the other evidence.
    results.append(run_group("ENCODING", group_encoding))
    results.append(run_group("LEGALITY", group_legality))
    results.append(run_group("ARITHMETIC", group_amo_arithmetic))
    results.append(run_group("DIRECTED_ISS", group_directed_iss))
    results.append(run_group("STAGE4_COMPAT", lambda: group_stage4_compat(args.stage4_dir)))
    failures = sum(not value for value in results)
    print(f"STAGE5_A_SOFTWARE_VALIDATION {'PASS' if failures == 0 else 'FAIL'} groups={len(results)} failures={failures} stage4_cases=230", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
