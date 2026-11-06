#!/usr/bin/env python3
"""Stage-2 fault injection (Verilator only): apply ONE pipeline RTL bug at a time and require the Stage-2
regression to FAIL. Stage 1 golden results are reused from a baseline run (Stage 1 RTL is not mutated).
Usage: python mutation_check_stage2.py <baseline_sim_dir> [mutant indices...]   (baseline = output of run_stage2.py)"""
import csv, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
BASE = sys.argv[1]; WORK = os.environ.get('MUT_DIR', '/tmp/mut_s2')
F = 'rtl/pipeline/'
MUT = [
 ("no EX/MEM forwarding (rs1)", F+"rv_forward_unit.sv", "assign fwd_a = a_exmem_match ? FWD_EXMEM : (a_memwb_match ? FWD_MEMWB : FWD_NONE);", "assign fwd_a = a_memwb_match ? FWD_MEMWB : FWD_NONE;"),
 ("no MEM/WB forwarding (rs2)", F+"rv_forward_unit.sv", "assign fwd_b = b_exmem_match ? FWD_EXMEM : (b_memwb_match ? FWD_MEMWB : FWD_NONE);", "assign fwd_b = b_exmem_match ? FWD_EXMEM : FWD_NONE;"),
 ("forward priority swapped (rs1)", F+"rv_forward_unit.sv", "assign fwd_a = a_exmem_match ? FWD_EXMEM : (a_memwb_match ? FWD_MEMWB : FWD_NONE);", "assign fwd_a = a_memwb_match ? FWD_MEMWB : (a_exmem_match ? FWD_EXMEM : FWD_NONE);"),
 ("load-use stall disabled", F+"rv_hazard_unit.sv", "assign stall = id_valid && ex_valid", "assign stall = 1'b0 && id_valid && ex_valid"),
 ("stall ignores rs2", F+"rv_hazard_unit.sv", "(id_uses_rs2 && (id_rs2 == ex_rd))", "1'b0"),
 ("no WB->ID bypass (rs1)", F+"rv_id_stage.sv", "assign bypass_rs1 = wb_we && (wb_rd != 5'd0) && (wb_rd == rs1);", "assign bypass_rs1 = 1'b0;"),
 ("redirect does not flush ID/EX", F+"rv_pipe_regs.sv", "if (kill || redirect || stall) id_ex <= '0;", "if (kill || stall) id_ex <= '0;"),
 ("redirect does not flush IF/ID", F+"rv_pipe_regs.sv", "if (kill || redirect) if_id <= '0;", "if (kill) if_id <= '0;"),
 ("x0 can be forwarded from EX/MEM", F+"rv_forward_unit.sv", "(exmem_rd != 5'd0) && !exmem_is_load;", "!exmem_is_load;"),
 ("store data not forwarded", F+"rv_ex_stage.sv", "ex_mem_next.store_data = rs2_f;", "ex_mem_next.store_data = id_ex.rs2_data;"),
 ("fault does not squash younger", "rtl/core/rv_core_pipe.sv", "assign kill = halted || fault;", "assign kill = halted;"),
 ("faulting store still writes memory", F+"rv_mem_stage.sv", "assign dmem_we    = (commit && ex_mem.mem_we) ? lsu_be : 4'b0000;", "assign dmem_we    = (ex_mem.valid && ex_mem.mem_we) ? lsu_be : 4'b0000;"),
 ("load forwarded from EX/MEM (data not ready)", F+"rv_forward_unit.sv", "(exmem_rd != 5'd0) && !exmem_is_load;", "(exmem_rd != 5'd0);"),
 ("stall does not hold PC", F+"rv_if_stage.sv", "else if (!stall)   pc <= pc + 32'd4;", "else pc <= pc + 32'd4;"),
 ("branch compare uses unforwarded operands", F+"rv_ex_stage.sv", ".a(rs1_f), .b(rs2_f), .funct3(id_ex.funct3)", ".a(id_ex.rs1_data), .b(id_ex.rs2_data), .funct3(id_ex.funct3)"),
 ("JAL/JALR link = pc+8", F+"rv_ex_stage.sv", "(id_ex.pc + 32'd4) : alu_y;", "(id_ex.pc + 32'd8) : alu_y;"),
 ("stall inserts no bubble (duplicate execution)", F+"rv_pipe_regs.sv", "if (kill || redirect || stall) id_ex <= '0;", "if (kill || redirect) id_ex <= '0;"),
 ("JALR keeps target bit0", F+"rv_ex_stage.sv", "{alu_y[31:1], 1'b0}", "alu_y"),
 ("MEM/WB forward uses address not data", "rtl/core/rv_core_pipe.sv", ".memwb_data(mem_wb.wb_data)", ".memwb_data(mem_wb.mem_addr)"),
 ("misaligned load not detected in MEM", F+"rv_mem_stage.sv", "if (ex_mem.mem_re && lsu_misaligned)      cause = HALT_LOAD_MISALIGN;", "if (1'b0)      cause = HALT_LOAD_MISALIGN;"),
]
def sh(cmd, **kw): return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)
sel = [int(a) for a in sys.argv[2:]] or range(len(MUT)); res = []
for i in sel:
    name, f, old, new = MUT[i]; p = os.path.join(ROOT, f); src = open(p).read()
    assert old in src, f"mutant {i}: pattern not found"
    if os.path.exists(WORK): shutil.rmtree(WORK)
    shutil.copytree(BASE, WORK, ignore=shutil.ignore_patterns('*.pipe.*', 'units_pipe.log', 'obj_*'))
    open(p, 'w').write(src.replace(old, new, 1))
    try:
        ok = True
        for tb, top, exe in (('tb_rv_pipe_units', 'tb_rv_pipe_units', 'Vunitsp'), ('tb_rv_pipe', 'tb_rv_pipe', 'Vpipe')):
            r = sh(['verilator', '-sv', '--binary', '--timing', '-Wno-fatal', '-Wno-lint', '-Wno-style', '-f', os.path.join(HERE, 'stage2_rtl.f'),
                    f'verification/environment/{tb}.sv', '--top-module', top, '-Mdir', f'{WORK}/obj_{exe}', '-o', exe])
            if r.returncode: ok = False; print("   build failed", r.stderr[-200:])
        if ok:
            open(f'{WORK}/units_pipe.log', 'w').write(sh([f'{WORK}/obj_Vunitsp/Vunitsp']).stdout)
            for row in csv.DictReader(open(f'{WORK}/manifest_all.csv')):
                n = row['name']
                a = [f'{WORK}/obj_Vpipe/Vpipe', f"+HEX={row['hexpath']}", f"+TRACE={WORK}/{n}.pipe.trace", f"+EXPECT_CAUSE={row['expect_cause']}", f"+CHECK_GP={row['check_gp']}", "+TIMEOUT=20000"]
                open(f'{WORK}/{n}.pipe.log', 'w').write(sh(a).stdout)
        c = sh([sys.executable, os.path.join(HERE, 'check_stage2_results.py'), WORK, 'verilator'])
        failing = [l.split()[0] for l in c.stdout.splitlines() if ('FAIL' in l or 'DIFF' in l) and not l.startswith(('STAGE2', 'SUITE', 'TOTAL', 'Stage', 'test'))]
        caught = c.returncode != 0
        tot = [l for l in c.stdout.splitlines() if l.startswith('TOTAL')]
        layer = ('unit-TB ' if 'Stage 2 pipe unit TB: PASS' not in c.stdout else '') + ('system ' if tot and not tot[0].startswith('TOTAL: 164 passed, 0 failed') or (tot and ' 0 failed' not in tot[0]) else '')
        if caught and not layer.strip(): layer = 'coverage/other'
    finally:
        open(p, 'w').write(src)
    res.append(caught)
    print(f"mutant {i:2d} {'CAUGHT ' if caught else 'MISSED!'} {name:46s} by[{layer.strip()}] {tot[0] if tot else ''}  first={failing[:2]}", flush=True)
print(f"MUTATION_STAGE2: {sum(res)}/{len(res)} caught")
sys.exit(0 if all(res) else 1)
