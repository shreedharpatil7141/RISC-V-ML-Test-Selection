`timescale 1ns/1ps
// rv_core_pipe.sv - 5-stage in-order pipeline with Stage 3.4 fixed-latency M execution.
// Same memory ports, halt semantics and retirement port names as rv_core_single (Stage 1,
// the golden reference), so traces are directly comparable. Differences:
//   * no ret_pc_next port
//   * USE_ITERATIVE_M=0 reproduces the Stage 3.3 combinational M pipeline milestone.
//   * debug outputs include divider protocol counters (simulation aids)
// Hazards: forwarding EX/MEM->EX and MEM/WB->EX, WB->ID bypass, 1-cycle load-use stall,
//          taken branch/jump resolved in EX (2 bubbles, predict-not-taken).
// Faults (illegal/ECALL/EBREAK/misaligned) travel down the pipe and halt at MEM: older
// instructions retire, the faulting one does not, younger ones are squashed.
// Dependencies: rv32_pkg, rv_pipe_pkg, rv_decoder, rv_imm_gen, rv_control, rv_regfile,
//               rv_alu, rv_md_comb, rv_mul, rv_div_iter, rv_md_exec, rv_branch_cmp, rv_lsu,
//               rv_hazard_unit, rv_forward_unit, pipeline stages and rv_pipe_regs
module rv_core_pipe
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
#(
  parameter word_t RESET_PC = 32'h0000_0000,
  parameter bit USE_ITERATIVE_M = 1'b1,
  parameter bit ENABLE_C = 1'b0,
  parameter bit ENABLE_A = 1'b0,
  parameter bit ENABLE_Z = 1'b0,
  parameter bit ENABLE_M = 1'b0
) (
  input  logic        clk,
  input  logic        rst_n,
  output word_t       imem_addr,
  output word_t       imem_addr_next,
  input  word_t       imem_rdata,
  input  logic        imem_valid,
  input  word_t       imem_rdata_next,
  input  logic        imem_next_valid,
  output word_t       dmem_addr,
  output logic        dmem_re,
  output logic [3:0]  dmem_we,
  output word_t       dmem_wdata,
  output logic        dmem_atomic_commit,
  input  word_t       dmem_rdata,
  input  logic        dmem_valid,
  input  logic        irq_msip,
  input  logic        irq_mtip,
  input  logic        irq_meip,
  output logic        halted,
  output halt_cause_e halt_cause,
  output word_t       halt_pc,
  output word_t       halt_raw_insn,
  output logic [4:0]  halt_ilen_bytes,
  // retirement (from WB)
  output logic        ret_valid,
  output word_t       ret_pc,
  output word_t       ret_insn,
  output word_t       ret_expanded_insn,
  output logic [4:0]  ret_ilen_bytes,
  output logic        ret_rd_we,
  output reg_t        ret_rd,
  output word_t       ret_rd_wdata,
  output logic        ret_mem_re,
  output logic        ret_mem_we,
  output word_t       ret_mem_addr,
  output logic [3:0]  ret_mem_be,
  output word_t       ret_mem_wdata,
  output word_t       ret_mem_rdata,
  // debug / coverage (simulation only)
  output logic        dbg_stall,
  output logic        dbg_redirect,
  output logic [15:0] dbg_events,
  output logic        dbg_assert_fail,
  output logic        dbg_md_start,
  output logic        dbg_md_busy,
  output logic        dbg_md_done,
  output logic        dbg_md_abort_started,
  output logic        dbg_m_issue,
  output logic        dbg_m_complete,
  output word_t       dbg_m_pc,
  output word_t       dbg_m_insn,
  output word_t       dbg_m_operand_a,
  output word_t       dbg_m_operand_b,
  output logic [1:0]  dbg_m_fwd_a,
  output logic [1:0]  dbg_m_fwd_b,
  output logic        dbg_m_squash_redirect,
  output logic [1:0]  dbg_m_squash_fault,
  output logic        dbg_m_fault_start_suppressed,
  output logic [1:0]  dbg_m_loaduse
);
  // pipeline registers and their next-state values
  if_id_t  if_id,  if_id_next;
  id_ex_t  id_ex,  id_ex_next;
  ex_mem_t ex_mem, ex_mem_next;
  mem_wb_t mem_wb, mem_wb_next;

  logic        stall, load_stall, csr_serialize, md_hold, front_stall, redirect, ex_redirect, kill, fault;
  logic machine_trap, irq_take, irq_pending, mstatus_mie;
  logic csr_inflight;
  logic [2:0] irq_levels;
  logic [4:0] irq_cause, architectural_cause, entry_cause;
  word_t csr_data, mepc_value, trap_target, mret_target, trap_value, entry_pc;
  word_t csr0, csr1;
  word_t       redirect_target, ex_redirect_target;
  halt_cause_e fault_cause;
  assign kill = halted || fault || irq_take;
  assign csr_inflight = (id_ex.valid && id_ex.is_csr) ||
                        (id_ex.valid && id_ex.is_mret) ||
                        (ex_mem.valid && ex_mem.insn[6:0] == OPC_SYSTEM &&
                         (ex_mem.insn[14:12] inside {3'b001,3'b010,3'b011,3'b101,3'b110,3'b111})) ||
                        (ex_mem.valid && ex_mem.is_mret) ||
                        (mem_wb.valid && mem_wb.insn[6:0] == OPC_SYSTEM &&
                         (mem_wb.insn[14:12] inside {3'b001,3'b010,3'b011,3'b101,3'b110,3'b111})) ||
                        (mem_wb.valid && mem_wb.is_mret);

  // ---------------- IF ----------------
  rv_if_stage #(.RESET_PC(RESET_PC), .ENABLE_C(ENABLE_C)) u_if (
    .clk(clk), .rst_n(rst_n), .stall(front_stall), .redirect(redirect),
    .redirect_target(redirect_target), .halted(halted),
    .imem_addr(imem_addr), .imem_addr_next(imem_addr_next),
    .imem_rdata(imem_rdata), .imem_valid(imem_valid),
    .imem_rdata_next(imem_rdata_next), .imem_next_valid(imem_next_valid),
    .if_id_next(if_id_next)
  );

  // ---------------- ID ----------------
  reg_t  rs1_addr, rs2_addr;
  word_t rf_rs1_data, rf_rs2_data;
  logic  id_uses_rs1, id_uses_rs2, bypass_rs1, bypass_rs2;
  logic  wb_rf_we;
  reg_t  wb_rf_rd;
  word_t wb_rf_wdata;

  rv_regfile u_rf (
    .clk(clk), .we(wb_rf_we), .waddr(wb_rf_rd), .wdata(wb_rf_wdata),
    .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .rs1_data(rf_rs1_data), .rs2_data(rf_rs2_data)
  );

  rv_id_stage #(.ENABLE_A(ENABLE_A), .ENABLE_Z(ENABLE_Z), .ENABLE_M(ENABLE_M)) u_id (
    .if_id(if_id), .rf_rs1_data(rf_rs1_data), .rf_rs2_data(rf_rs2_data),
    .wb_we(wb_rf_we), .wb_rd(wb_rf_rd), .wb_data(wb_rf_wdata),
    .csr_data(csr_data),
    .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .uses_rs1(id_uses_rs1), .uses_rs2(id_uses_rs2),
    .bypass_rs1(bypass_rs1), .bypass_rs2(bypass_rs2), .id_ex_next(id_ex_next)
  );

  rv_hazard_unit u_haz (
    .id_valid(if_id.valid), .id_rs1(rs1_addr), .id_rs2(rs2_addr),
    .id_uses_rs1(id_uses_rs1), .id_uses_rs2(id_uses_rs2),
    .ex_valid(id_ex.valid), .ex_mem_re(id_ex.mem_re), .ex_rd(id_ex.rd), .stall(load_stall)
  );
  assign csr_serialize =
      (ENABLE_Z && ((id_ex.valid && id_ex.is_csr) ||
                    (ex_mem.valid && ex_mem.insn[6:0] == OPC_SYSTEM &&
                     (ex_mem.insn[14:12] inside {3'b001,3'b010,3'b011,3'b101,3'b110,3'b111})) ||
                    (mem_wb.valid && mem_wb.insn[6:0] == OPC_SYSTEM &&
                     (mem_wb.insn[14:12] inside {3'b001,3'b010,3'b011,3'b101,3'b110,3'b111})) ||
                    (if_id.valid && if_id.insn[6:0] == OPC_SYSTEM &&
                     (if_id.insn[14:12] inside {3'b001,3'b010,3'b011,3'b101,3'b110,3'b111}) &&
                     (id_ex.valid || ex_mem.valid || mem_wb.valid)))) ||
      (ENABLE_M && ((id_ex.valid && id_ex.is_mret) || (ex_mem.valid && ex_mem.is_mret) ||
                    (mem_wb.valid && mem_wb.is_mret) ||
                    (if_id.valid && if_id.insn == INSN_MRET &&
                     (id_ex.valid || ex_mem.valid || mem_wb.valid))));
  assign stall = load_stall || csr_serialize;

  // ---------------- EX ----------------
  fwd_sel_e fwd_a, fwd_b;
  logic a_exmem_m, a_memwb_m, b_exmem_m, b_memwb_m;
  logic dbg_md_ready;

  rv_forward_unit u_fwd (
    .ex_rs1(id_ex.rs1), .ex_rs2(id_ex.rs2),
    .exmem_valid(ex_mem.valid), .exmem_reg_we(ex_mem.reg_we),
    .exmem_is_load(ex_mem.mem_re), .exmem_rd(ex_mem.rd),
    .memwb_valid(mem_wb.valid), .memwb_reg_we(mem_wb.reg_we), .memwb_rd(mem_wb.rd),
    .fwd_a(fwd_a), .fwd_b(fwd_b),
    .a_exmem_match(a_exmem_m), .a_memwb_match(a_memwb_m),
    .b_exmem_match(b_exmem_m), .b_memwb_match(b_memwb_m)
  );

  rv_ex_stage #(.USE_ITERATIVE_M(USE_ITERATIVE_M), .ENABLE_C(ENABLE_C), .ENABLE_M(ENABLE_M)) u_ex (
    .id_ex(id_ex), .fwd_a(fwd_a), .fwd_b(fwd_b),
    .exmem_alu_y(mem_wb_next.wb_data), .memwb_data(mem_wb.wb_data),
    .clk(clk), .rst_n(rst_n), .kill(kill), .mret_target(mret_target),
    .ex_mem_next(ex_mem_next), .redirect(ex_redirect), .redirect_target(ex_redirect_target),
    .md_hold(md_hold), .md_start(dbg_md_start), .md_busy(dbg_md_busy),
    .md_done(dbg_md_done), .md_abort_started(dbg_md_abort_started),
    .dbg_m_issue(dbg_m_issue), .dbg_m_complete(dbg_m_complete), .dbg_md_ready(dbg_md_ready),
    .dbg_m_pc(dbg_m_pc), .dbg_m_insn(dbg_m_insn),
    .dbg_m_operand_a(dbg_m_operand_a), .dbg_m_operand_b(dbg_m_operand_b),
    .dbg_m_fwd_a(dbg_m_fwd_a), .dbg_m_fwd_b(dbg_m_fwd_b)
  );

  // ---------------- MEM ----------------
  rv_mem_stage #(.ENABLE_C(ENABLE_C), .ENABLE_A(ENABLE_A)) u_mem (
    .clk(clk), .rst_n(rst_n), .ex_mem(ex_mem), .dmem_rdata(dmem_rdata), .dmem_valid(dmem_valid),
    .dmem_addr(dmem_addr), .dmem_re(dmem_re), .dmem_we(dmem_we), .dmem_wdata(dmem_wdata),
    .dmem_atomic_commit(dmem_atomic_commit), .reservation_invalidate(machine_trap || irq_take),
    .mem_wb_next(mem_wb_next), .fault(fault), .fault_cause(fault_cause)
  );

  assign irq_levels = {irq_meip, irq_mtip, irq_msip};
  assign machine_trap = ENABLE_M && fault;
  assign irq_take = ENABLE_M && !fault && irq_pending && !csr_inflight &&
                    !(id_ex.valid && ex_mem_next.cause != HALT_NONE) &&
                    !(if_id.valid && id_ex_next.cause != HALT_NONE) &&
                    !(if_id.valid && if_id.cause != HALT_NONE) && (id_ex.valid || if_id.valid);
  assign entry_pc = fault ? ex_mem.pc : (id_ex.valid ? id_ex.pc : if_id.pc);
  always_comb begin
    architectural_cause = 0;
    trap_value = 0;
    case (fault_cause)
      HALT_FETCH_MISALIGN: begin architectural_cause = 0; trap_value = ex_mem.alu_y; end
      HALT_FETCH_ACCESS: begin architectural_cause = 1; trap_value = ex_mem.pc; end
      HALT_ILLEGAL: begin architectural_cause = 2; trap_value = ex_mem.raw_insn; end
      HALT_EBREAK: architectural_cause = 3;
      HALT_LOAD_MISALIGN: begin architectural_cause = 4; trap_value = ex_mem.alu_y; end
      HALT_LOAD_ACCESS: begin architectural_cause = 5; trap_value = ex_mem.alu_y; end
      HALT_STORE_MISALIGN: begin architectural_cause = 6; trap_value = ex_mem.alu_y; end
      HALT_STORE_ACCESS: begin architectural_cause = 7; trap_value = ex_mem.alu_y; end
      HALT_ECALL: architectural_cause = 11;
      default: architectural_cause = 2;
    endcase
  end
  assign entry_cause = irq_take ? irq_cause : architectural_cause;
  rv_machine_state #(.ENABLE_A(ENABLE_A), .ENABLE_C(ENABLE_C)) u_machine (
    .clk(clk), .rst_n(rst_n), .raddr(if_id.insn[31:20]), .irq_levels(irq_levels),
    .rdata(csr_data), .irq_pending(irq_pending), .irq_cause(irq_cause),
    .csr_we(mem_wb.valid && mem_wb.csr_write), .csr_waddr(mem_wb.csr_addr),
    .csr_wdata(mem_wb.csr_new), .retired(ret_valid),
    .trap_enter(machine_trap || irq_take), .trap_interrupt(irq_take),
    .trap_pc(entry_pc), .trap_cause(entry_cause), .trap_value(trap_value),
    .mret(mem_wb.valid && mem_wb.is_mret), .mepc_value(mepc_value),
    .trap_target(trap_target), .mret_target(mret_target), .mstatus_mie(mstatus_mie)
  );
  assign csr0 = u_machine.scratch0;
  assign csr1 = u_machine.scratch1;
  assign redirect = machine_trap || irq_take || (ex_redirect && !fault && !irq_take);
  assign redirect_target = (machine_trap || irq_take) ? trap_target : ex_redirect_target;

  // ---------------- WB ----------------
  rv_wb_stage u_wb (
    .mem_wb(mem_wb), .rf_we(wb_rf_we), .rf_rd(wb_rf_rd), .rf_wdata(wb_rf_wdata),
    .ret_valid(ret_valid), .ret_pc(ret_pc), .ret_insn(ret_insn),
    .ret_expanded_insn(ret_expanded_insn), .ret_ilen_bytes(ret_ilen_bytes),
    .ret_rd_we(ret_rd_we), .ret_rd(ret_rd), .ret_rd_wdata(ret_rd_wdata),
    .ret_mem_re(ret_mem_re), .ret_mem_we(ret_mem_we), .ret_mem_addr(ret_mem_addr),
    .ret_mem_be(ret_mem_be), .ret_mem_wdata(ret_mem_wdata), .ret_mem_rdata(ret_mem_rdata)
  );

  // ---------------- Pipeline registers ----------------
  rv_pipe_regs u_regs (
    .clk(clk), .rst_n(rst_n), .stall(stall), .md_hold(md_hold), .redirect(redirect), .kill(kill),
    .if_id_next(if_id_next), .id_ex_next(id_ex_next),
    .ex_mem_next(ex_mem_next), .mem_wb_next(mem_wb_next),
    .if_id(if_id), .id_ex(id_ex), .ex_mem(ex_mem), .mem_wb(mem_wb)
  );

  // ---------------- Halt state ----------------
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      halted     <= 1'b0;
      halt_cause <= HALT_NONE;
      halt_pc    <= 32'h0;
      halt_raw_insn <= 32'h0;
      halt_ilen_bytes <= 5'd0;
    end else if (!ENABLE_M && !halted && fault) begin
      halted     <= 1'b1;
      halt_cause <= fault_cause;
      halt_pc    <= ex_mem.pc;
      halt_raw_insn <= ex_mem.raw_insn;
      halt_ilen_bytes <= ex_mem.ilen_bytes;
    end
  end

  // ---------------- Debug / coverage events (gated by !kill) ----------------
  logic run;
  assign run          = !kill;
  assign front_stall  = stall || md_hold;
  // Keep generic load-use stalls separate from the 33-cycle md_busy accounting.
  assign dbg_stall    = run && stall;
  assign dbg_redirect = run && redirect;

  // M-specific coverage signals. Squashed instructions are counted before
  // their pipeline register is cleared; these are distinct from issued work.
  assign dbg_m_squash_redirect = redirect && !kill && if_id.valid && id_ex_next.is_m;
  assign dbg_m_squash_fault[0] = fault && id_ex.valid && id_ex.is_m;
  assign dbg_m_squash_fault[1] = fault && if_id.valid && id_ex_next.is_m;
  assign dbg_m_fault_start_suppressed = fault && id_ex.valid && id_ex.is_m &&
                                        id_ex.funct3[2] && dbg_md_ready;
  assign dbg_m_loaduse[0] = run && stall && if_id.valid && id_ex_next.is_m &&
                            id_uses_rs1 && (rs1_addr == id_ex.rd);
  assign dbg_m_loaduse[1] = run && stall && if_id.valid && id_ex_next.is_m &&
                            id_uses_rs2 && (rs2_addr == id_ex.rd);

  logic exmem_x0_w, memwb_x0_w;
  assign exmem_x0_w = ex_mem.valid && ex_mem.reg_we && (ex_mem.rd == 5'd0);
  assign memwb_x0_w = mem_wb.valid && mem_wb.reg_we && (mem_wb.rd == 5'd0);

  always_comb begin
    dbg_events    = 16'h0;
    // 0/1: load-use stall caused by rs1 / rs2
    dbg_events[0]  = run && stall && id_uses_rs1 && (rs1_addr == id_ex.rd);
    dbg_events[1]  = run && stall && id_uses_rs2 && (rs2_addr == id_ex.rd);
    // 2..5: forwarding actually used by an instruction in EX
    dbg_events[2]  = run && id_ex.valid && id_ex.uses_rs1 && (fwd_a == FWD_EXMEM);
    dbg_events[3]  = run && id_ex.valid && id_ex.uses_rs1 && (fwd_a == FWD_MEMWB);
    dbg_events[4]  = run && id_ex.valid && id_ex.uses_rs2 && (fwd_b == FWD_EXMEM);
    dbg_events[5]  = run && id_ex.valid && id_ex.uses_rs2 && (fwd_b == FWD_MEMWB);
    // 6/7: WB->ID bypass used
    dbg_events[6]  = run && if_id.valid && id_uses_rs1 && bypass_rs1;
    dbg_events[7]  = run && if_id.valid && id_uses_rs2 && bypass_rs2;
    // 8/9: both producers match, EX/MEM wins
    dbg_events[8]  = run && id_ex.valid && id_ex.uses_rs1 && a_exmem_m && a_memwb_m;
    dbg_events[9]  = run && id_ex.valid && id_ex.uses_rs2 && b_exmem_m && b_memwb_m;
    // 10..12: redirect source
    dbg_events[10] = run && redirect && id_ex.is_branch;
    dbg_events[11] = run && redirect && id_ex.is_jal;
    dbg_events[12] = run && redirect && id_ex.is_jalr;
    // 13: store data forwarded; 14: branch operand forwarded
    dbg_events[13] = run && id_ex.valid && id_ex.mem_we && id_ex.uses_rs2 && (fwd_b != FWD_NONE);
    dbg_events[14] = run && id_ex.valid && id_ex.is_branch && ((fwd_a != FWD_NONE) || (fwd_b != FWD_NONE));
    // 15: in-flight write to x0 while a consumer reads x0 (must NOT be forwarded)
    dbg_events[15] = run && id_ex.valid &&
                     ((id_ex.uses_rs1 && (id_ex.rs1 == 5'd0)) || (id_ex.uses_rs2 && (id_ex.rs2 == 5'd0))) &&
                     (exmem_x0_w || memwb_x0_w);
  end

  // ---------------- Self-checks (sticky) ----------------
  logic viol_loaduse, viol_x0fwd;
  assign viol_loaduse = run && id_ex.valid && ex_mem.valid && ex_mem.mem_re && (ex_mem.rd != 5'd0) &&
                        ((id_ex.uses_rs1 && (id_ex.rs1 == ex_mem.rd)) ||
                         (id_ex.uses_rs2 && (id_ex.rs2 == ex_mem.rd)));      // load-use escaped the stall
  assign viol_x0fwd   = run && id_ex.valid &&
                        (((id_ex.rs1 == 5'd0) && (fwd_a != FWD_NONE)) ||
                         ((id_ex.rs2 == 5'd0) && (fwd_b != FWD_NONE)));       // x0 must never be forwarded

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)                          dbg_assert_fail <= 1'b0;
    else if (viol_loaduse || viol_x0fwd) dbg_assert_fail <= 1'b1;
  end
endmodule
