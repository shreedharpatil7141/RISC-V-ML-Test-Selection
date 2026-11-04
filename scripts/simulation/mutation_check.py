#!/usr/bin/env python3
"""Fault-injection sanity check: apply one deliberate RTL bug at a time, run the Stage-1 regression,
require it to FAIL (bug detected), then restore the original file."""
import os, subprocess, sys, shutil
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
MUT = [
 ("SRA acts as SRL",            "rtl/alu/rv_alu.sv",            "word_t'($signed(a) >>> b[4:0])", "a >> b[4:0]"),
 ("BLTU uses signed compare",   "rtl/alu/rv_branch_cmp.sv",     "3'b110:  taken = (a <  b);", "3'b110:  taken = ($signed(a) < $signed(b));"),
 ("B-imm bit 11/7 swapped",     "rtl/decoder/rv_imm_gen.sv",    "insn[31], insn[7], insn[30:25]", "insn[31], insn[30], insn[29:25], insn[7]"),
 ("LB zero-extends",            "rtl/memory/rv_lsu.sv",         "{{24{shifted[7]}},  shifted[7:0]}", "{24'b0, shifted[7:0]}"),
 ("JALR keeps bit0",            "rtl/core/rv_core_single.sv",   "{alu_y[31:1], 1'b0}", "alu_y"),
 ("x0 writable (write+read guards removed)", "rtl/register_file/rv_regfile.sv", (("if (we && (waddr != 5'd0))", "if (we)"), ("assign rs1_data = (rs1_addr == 5'd0) ? 32'h0 : regs[rs1_addr];", "assign rs1_data = regs[rs1_addr];")), None),
 ("faulting store still writes","rtl/core/rv_core_single.sv",   "(commit && mem_we) ? lsu_be", "(!halted && mem_we) ? lsu_be"),
 ("SLLI funct7 not checked",    "rtl/decoder/rv_decoder.sv",    "illegal = (funct7 != 7'b0000000);                       // SLLI", "illegal = 1'b0;"),
 ("SLTU decoded as SLT",        "rtl/control_unit/rv_control.sv","3'b011:  return ALU_SLTU;", "3'b011:  return ALU_SLT;"),
 ("SH byte enable wrong",       "rtl/memory/rv_lsu.sv",         "be        = addr[1] ? 4'b1100 : 4'b0011;", "be        = 4'b0011;"),
 ("AUIPC uses rs1 not PC",      "rtl/control_unit/rv_control.sv","OPC_AUIPC: begin reg_we = 1'b1; a_sel = A_PC;", "OPC_AUIPC: begin reg_we = 1'b1; a_sel = A_RS1;"),
 ("BGE treated as BGEU",        "rtl/alu/rv_branch_cmp.sv",     "3'b101:  taken = ($signed(a) >= $signed(b));", "3'b101:  taken = (a >= b);"),
 ("JAL link = pc+8",            "rtl/core/rv_core_single.sv",   "WB_PC4:  wb_data = pc_plus4;", "WB_PC4:  wb_data = pc_plus4 + 32'd4;"),
 ("misaligned load not caught", "rtl/core/rv_core_single.sv",   "else if (mem_re && lsu_misaligned)", "else if (1'b0)"),
]
sel = [int(a) for a in sys.argv[1:]] or range(len(MUT))
res = []
for i in sel:
    name, f, old, new = MUT[i]; p = os.path.join(ROOT, f)
    src = open(p).read()
    pairs = old if new is None else [(old, new)]      # (old, None) form = list of (old,new) pairs
    mut = src
    for o, n in pairs:
        assert o in mut, f"mutant {i}: pattern not found"
        mut = mut.replace(o, n, 1)
    open(p, 'w').write(mut)
    try:
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts/simulation/run_stage1.py')], capture_output=True, text=True, cwd=ROOT,
                           env=dict(os.environ, SIM_DIR='/home/claude/sim_mut', NO_REPORT='1'))
        caught = r.returncode != 0
        why = [l for l in r.stdout.splitlines() if l.startswith(('UNIT TESTS', 'SYSTEM TESTS'))]
        failing = [l.split()[0] for l in r.stdout.splitlines() if (' FAIL ' in l or ' DIFF ' in l)]
    finally:
        open(p, 'w').write(src)
    res.append(caught)
    print(f"mutant {i:2d} {'CAUGHT ' if caught else 'MISSED!'} {name:30s} {' | '.join(why)}  first_fail={failing[:3]}", flush=True)
print(f"MUTATION: {sum(res)}/{len(res)} caught")
sys.exit(0 if all(res) else 1)
