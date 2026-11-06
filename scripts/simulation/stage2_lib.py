#!/usr/bin/env python3
"""Shared Stage-2 helpers: dynamic stall/redirect model (from the ISS trace), result parsing, comparison.

Performance model (independent of the RTL, derived from the architectural trace only):
  stall    : retired (or finally-faulting) instruction directly after a LOAD (rd!=x0) that reads that rd
             through a source field the instruction really uses  -> 1 bubble each
  redirect : every retired JAL/JALR, and every retired BRANCH whose next PC != pc+4 -> 2 bubbles each
  cycles   : instret + CYCLE_CONST + stalls + 2*redirects
             CYCLE_CONST = 5 = 4 (IF->MEM latency of the halting instruction) + 1 (testbench samples
             'halted' one edge late: cycles++ executes before the NBA that sets halted).
"""
import os, re
CYCLE_CONST = 5
EVENTS = ["stall_rs1", "stall_rs2", "fwd_a_exmem", "fwd_a_memwb", "fwd_b_exmem", "fwd_b_memwb",
          "wb_bypass_rs1", "wb_bypass_rs2", "fwd_a_priority", "fwd_b_priority",
          "redirect_branch", "redirect_jal", "redirect_jalr", "store_data_fwd", "branch_operand_fwd", "x0_not_forwarded"]
USES1 = {0x67, 0x63, 0x03, 0x23, 0x13, 0x33}
USES2 = {0x63, 0x23, 0x33}

def parse_trace(text):
    recs, halt = [], None
    for ln in text.splitlines():
        p = ln.split()
        if not p: continue
        if p[0] == 'HALT': halt = (int(p[1]), int(p[2], 16))
        elif p[0] in ('REG', 'MEM'): continue
        else: recs.append((int(p[0], 16), int(p[1], 16)))
    return recs, halt

def uses(insn):
    if insn & 3 != 3: return False, False
    op = insn & 0x7F
    return op in USES1, op in USES2

def perf_model(trace_text, words):
    recs, halt = parse_trace(trace_text)
    seq = list(recs)
    cause, hpc = halt
    if cause in (4, 5, 6) and (hpc >> 2) < len(words):       # legal instruction that faults in EX/MEM still stalls on load-use
        seq.append((hpc, words[hpc >> 2]))
    stalls = redirects = 0
    for i, (pc, insn) in enumerate(seq):
        if i > 0:
            ppc, pin = seq[i - 1]
            if pin & 0x7F == 0x03 and (pin & 3) == 3:
                rd = (pin >> 7) & 31; u1, u2 = uses(insn)
                if rd != 0 and ((u1 and ((insn >> 15) & 31) == rd) or (u2 and ((insn >> 20) & 31) == rd)): stalls += 1
        if i < len(recs):                                     # retired instructions only
            op = insn & 0x7F
            if op in (0x6F, 0x67): redirects += 1
            elif op == 0x63:
                nxt = seq[i + 1][0] if i + 1 < len(seq) else hpc
                if nxt != pc + 4: redirects += 1
    return len(recs), stalls, redirects

RE_RES = re.compile(r"TEST_RESULT: (PASS|FAIL) hex=(\S+) cause=(\d+) expect=(\d+) gp=0x(\w+) instret=(\d+) cycles=(\d+) oob=(\d+)")
RE_STATS = re.compile(r"STATS stalls=(\d+) redirects=(\d+) cycles=(\d+) instret=(\d+) assert_fail=(\d+)")
RE_COV = re.compile(r"COV ((?:\d+ ?)+)")

def read(path):
    try: return open(path, errors='replace').read()
    except OSError: return None

def parse_log(text):
    r = {'pass': False}
    if not text: return r
    m = RE_RES.search(text)
    if m: r.update(pass_=m.group(1) == 'PASS', cause=int(m.group(3)), instret=int(m.group(6)), cycles=int(m.group(7)))
    r['pass'] = bool(m and m.group(1) == 'PASS')
    m = RE_STATS.search(text)
    if m: r.update(stalls=int(m.group(1)), redirects=int(m.group(2)), assert_fail=int(m.group(5)))
    m = RE_COV.search(text)
    if m: r['cov'] = [int(x) for x in m.group(1).split()]
    return r

def evaluate(sim_dir, manifest_rows, expected, simulator):
    """Returns (report_lines, ok). Expects <name>.s1.log/.s1.trace (Stage 1 golden) and <name>.pipe.log/.pipe.trace."""
    lines, bad = [], 0
    cov_tot = [0] * 16; cov_tests = [0] * 16
    suite_cnt = {}
    lines.append(f"{'test':40s} s1   pipe iss== gold== perf  stalls redir cycles")
    for row in manifest_rows:
        n = row['name']; e = expected[n]; suite = e['suite']
        iss = read(os.path.join(sim_dir, 'iss', n + '.iss.trace'))
        s1t = read(os.path.join(sim_dir, n + '.s1.trace')); pt = read(os.path.join(sim_dir, n + '.pipe.trace'))
        s1 = parse_log(read(os.path.join(sim_dir, n + '.s1.log'))); pl = parse_log(read(os.path.join(sim_dir, n + '.pipe.log')))
        s1_ok = s1['pass'] and s1t is not None
        pipe_ok = pl['pass'] and pt is not None and pl.get('assert_fail', 1) == 0
        iss_eq = pt is not None and iss is not None and pt == iss
        gold_eq = pt is not None and s1t is not None and pt == s1t
        mstall, mred = int(e['model_stalls']), int(e['model_redirects'])
        perf_ok = ('stalls' in pl and pl['stalls'] == mstall and pl['redirects'] == mred and
                   pl.get('instret') == int(e['instret']) and pl['cycles'] == int(e['instret']) + CYCLE_CONST + mstall + 2 * mred)
        cs, cr = int(e['exp_stalls']), int(e['exp_redirects'])        # constructed (by test design), -1 = not asserted
        if cs >= 0 and pl.get('stalls') != cs: perf_ok = False
        if cr >= 0 and pl.get('redirects') != cr: perf_ok = False
        ok = s1_ok and pipe_ok and iss_eq and gold_eq and perf_ok
        bad += not ok
        sc = suite_cnt.setdefault(suite, [0, 0]); sc[0 if ok else 1] += 1
        if 'cov' in pl:
            for i, v in enumerate(pl['cov']):
                cov_tot[i] += v; cov_tests[i] += v > 0
        lines.append(f"{n:40s} {'ok' if s1_ok else 'FAIL':4s} {'ok' if pipe_ok else 'FAIL':4s} {'ok' if iss_eq else 'DIFF':5s} {'ok' if gold_eq else 'DIFF':5s} {'ok' if perf_ok else 'FAIL':5s} "
                     f"{pl.get('stalls', -1):6d} {pl.get('redirects', -1):5d} {pl.get('cycles', -1):6d}" +
                     ("" if ok else f"   [model stalls={mstall} redir={mred} cons={cs}/{cr}]"))
    lines.append("")
    lines.append(f"Pipeline functional coverage (event counters, all tests, simulator={simulator}):")
    for i, nme in enumerate(EVENTS):
        lines.append(f"  {i:2d} {nme:20s} hits={cov_tot[i]:8d} tests={cov_tests[i]:3d} {'COVERED' if cov_tot[i] else 'NOT COVERED'}")
    ncov = sum(1 for v in cov_tot if v)
    lines.append(f"Coverage events hit: {ncov}/16")
    for suite, (p, f) in sorted(suite_cnt.items()):
        lines.append(f"SUITE {suite}: {p} passed, {f} failed, {p + f} total")
    lines.append(f"TOTAL: {len(manifest_rows) - bad} passed, {bad} failed, {len(manifest_rows)} total")
    return lines, (bad == 0 and ncov == 16), bad, ncov
