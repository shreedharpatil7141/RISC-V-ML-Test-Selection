`timescale 1ns/1ps
// rv_ex_stage.sv - Execute: operand forwarding, ALU, branch/jump resolution.
// Branches/jumps resolve here; a taken transfer redirects PC and squashes IF/ID + ID/EX (2 bubbles).
// A transfer with a misaligned (bit1) target raises HALT_FETCH_MISALIGN instead of redirecting.
module rv_ex_stage
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
#(
  parameter bit USE_ITERATIVE_M = 1'b1,
  parameter bit ENABLE_C = 1'b0
)
(
  input  id_ex_t   id_ex,
  input  fwd_sel_e fwd_a,
  input  fwd_sel_e fwd_b,
  input  logic     clk,
  input  logic     rst_n,
  input  logic     kill,
  input  word_t    exmem_alu_y,   // forward source: EX/MEM result
  input  word_t    memwb_data,    // forward source: MEM/WB write-back data
  output ex_mem_t  ex_mem_next,
  output logic     redirect,
  output word_t    redirect_target,
  output logic     md_hold,
  output logic     md_start,
  output logic     md_busy,
  output logic     md_done,
  output logic     md_abort_started,
  output logic     dbg_m_issue,
  output logic     dbg_m_complete,
  output logic     dbg_md_ready,
  output word_t    dbg_m_pc,
  output word_t    dbg_m_insn,
  output word_t    dbg_m_operand_a,
  output word_t    dbg_m_operand_b,
  output logic [1:0] dbg_m_fwd_a,
  output logic [1:0] dbg_m_fwd_b
);
  word_t rs1_f, rs2_f, alu_a, alu_b, alu_y, md_y, md_comb_y, md_result, result, target;
  logic  cmp_taken, redirect_raw, md_ready, md_accepted, md_done_raw, md_abort_raw;
  logic  is_div, md_start_req;

  always_comb begin
    case (fwd_a)
      FWD_EXMEM: rs1_f = exmem_alu_y;
      FWD_MEMWB: rs1_f = memwb_data;
      default:   rs1_f = id_ex.rs1_data;
    endcase
    case (fwd_b)
      FWD_EXMEM: rs2_f = exmem_alu_y;
      FWD_MEMWB: rs2_f = memwb_data;
      default:   rs2_f = id_ex.rs2_data;
    endcase
    case (id_ex.a_sel)
      A_PC:    alu_a = id_ex.pc;
      A_ZERO:  alu_a = 32'h0;
      default: alu_a = rs1_f;
    endcase
    alu_b = id_ex.b_imm ? id_ex.imm : rs2_f;
  end

  rv_alu        u_alu  (.a(alu_a), .b(alu_b), .op(id_ex.alu_op), .y(alu_y));
  rv_md_comb u_md_comb (.funct3(id_ex.funct3), .a(rs1_f), .b(rs2_f), .y(md_comb_y));
  rv_md_exec u_md_exec (
    .clk(clk), .rst_n(rst_n), .start(md_start_req), .abort(kill),
    .funct3(id_ex.funct3), .a(rs1_f), .b(rs2_f), .ready(md_ready),
    .accepted(md_accepted), .busy(md_busy), .done(md_done_raw),
    .aborted(md_abort_raw), .y(md_y)
  );
  rv_branch_cmp u_bcmp (.a(rs1_f), .b(rs2_f), .funct3(id_ex.funct3), .taken(cmp_taken));

  assign is_div = id_ex.funct3[2];
  assign md_start_req = USE_ITERATIVE_M && id_ex.valid && id_ex.is_m && is_div && md_ready && !kill;
  assign md_start = USE_ITERATIVE_M && md_accepted;
  assign md_hold = USE_ITERATIVE_M && id_ex.valid && id_ex.is_m && is_div &&
                   !md_done_raw && !kill;
  assign md_done = USE_ITERATIVE_M && md_done_raw && !kill;
  assign md_abort_started = USE_ITERATIVE_M && md_abort_raw;
  assign dbg_md_ready = md_ready;

  // Coverage/debug view of the actual forwarded EX operands. Divide issue is
  // the one accepted start; multiply issue/completion is its single EX transfer.
  assign dbg_m_issue = id_ex.valid && id_ex.is_m && !kill &&
                       (is_div ? (USE_ITERATIVE_M ? md_accepted : 1'b1) : 1'b1);
  assign dbg_m_complete = id_ex.valid && id_ex.is_m && !kill &&
                          (is_div ? (USE_ITERATIVE_M ? md_done_raw : 1'b1) : 1'b1);
  assign dbg_m_pc = id_ex.pc;
  assign dbg_m_insn = id_ex.insn;
  assign dbg_m_operand_a = rs1_f;
  assign dbg_m_operand_b = rs2_f;
  assign dbg_m_fwd_a = fwd_a;
  assign dbg_m_fwd_b = fwd_b;

  assign redirect_raw = (id_ex.is_branch && cmp_taken) || id_ex.is_jal || id_ex.is_jalr;
  assign target       = id_ex.is_jalr ? {alu_y[31:1], 1'b0} : (id_ex.pc + id_ex.imm);
  assign md_result    = USE_ITERATIVE_M ? md_y : md_comb_y;
  // Preserve the Stage 2 link-value mutation target; M result selection is applied at EX/MEM below.
  assign result       = (id_ex.wb_sel == WB_PC4) ?
                        (id_ex.pc + (ENABLE_C ? id_ex.ilen_bytes : 5'd4)) : alu_y;

  halt_cause_e cause;
  always_comb begin
    cause = id_ex.cause;
    if (cause == HALT_NONE && redirect_raw && (ENABLE_C ? target[0] : target[1]))
      cause = HALT_FETCH_MISALIGN;
  end

  assign redirect        = id_ex.valid && (cause == HALT_NONE) && redirect_raw;
  assign redirect_target = target;

  always_comb begin
    ex_mem_next.valid      = id_ex.valid;
    ex_mem_next.pc         = id_ex.pc;
    ex_mem_next.raw_insn   = id_ex.raw_insn;
    ex_mem_next.insn       = id_ex.insn;
    ex_mem_next.ilen_bytes = id_ex.ilen_bytes;
    ex_mem_next.rd         = id_ex.rd;
    ex_mem_next.rs2        = id_ex.rs2;
    ex_mem_next.reg_we     = id_ex.reg_we;
    ex_mem_next.funct3     = id_ex.funct3;
    ex_mem_next.mem_re     = id_ex.mem_re;
    ex_mem_next.mem_we     = id_ex.mem_we;
    ex_mem_next.is_a       = id_ex.is_a;
    ex_mem_next.alu_y      = id_ex.is_a ? rs1_f : (id_ex.is_m ? md_result : result);
    ex_mem_next.store_data = rs2_f;
    ex_mem_next.cause      = cause;
  end
endmodule
