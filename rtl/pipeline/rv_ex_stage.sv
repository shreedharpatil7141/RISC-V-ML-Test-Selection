`timescale 1ns/1ps
// rv_ex_stage.sv - Execute: operand forwarding, ALU, branch/jump resolution.
// Branches/jumps resolve here; a taken transfer redirects PC and squashes IF/ID + ID/EX (2 bubbles).
// A transfer with a misaligned (bit1) target raises HALT_FETCH_MISALIGN instead of redirecting.
module rv_ex_stage
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
(
  input  id_ex_t   id_ex,
  input  fwd_sel_e fwd_a,
  input  fwd_sel_e fwd_b,
  input  word_t    exmem_alu_y,   // forward source: EX/MEM result
  input  word_t    memwb_data,    // forward source: MEM/WB write-back data
  output ex_mem_t  ex_mem_next,
  output logic     redirect,
  output word_t    redirect_target
);
  word_t rs1_f, rs2_f, alu_a, alu_b, alu_y, result, target;
  logic  cmp_taken, redirect_raw;

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
  rv_branch_cmp u_bcmp (.a(rs1_f), .b(rs2_f), .funct3(id_ex.funct3), .taken(cmp_taken));

  assign redirect_raw = (id_ex.is_branch && cmp_taken) || id_ex.is_jal || id_ex.is_jalr;
  assign target       = id_ex.is_jalr ? {alu_y[31:1], 1'b0} : (id_ex.pc + id_ex.imm);
  assign result       = (id_ex.wb_sel == WB_PC4) ? (id_ex.pc + 32'd4) : alu_y;

  halt_cause_e cause;
  always_comb begin
    cause = id_ex.cause;
    if (cause == HALT_NONE && redirect_raw && target[1]) cause = HALT_FETCH_MISALIGN;
  end

  assign redirect        = id_ex.valid && (cause == HALT_NONE) && redirect_raw;
  assign redirect_target = target;

  always_comb begin
    ex_mem_next.valid      = id_ex.valid;
    ex_mem_next.pc         = id_ex.pc;
    ex_mem_next.insn       = id_ex.insn;
    ex_mem_next.rd         = id_ex.rd;
    ex_mem_next.rs2        = id_ex.rs2;
    ex_mem_next.reg_we     = id_ex.reg_we;
    ex_mem_next.funct3     = id_ex.funct3;
    ex_mem_next.mem_re     = id_ex.mem_re;
    ex_mem_next.mem_we     = id_ex.mem_we;
    ex_mem_next.alu_y      = result;
    ex_mem_next.store_data = rs2_f;
    ex_mem_next.cause      = cause;
  end
endmodule
