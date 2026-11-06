`timescale 1ns/1ps
// rv_id_stage.sv - Decode, immediate, control, register-read with WB->ID bypass.
// Reuses the Stage 1 rv_decoder / rv_imm_gen / rv_control unchanged.
module rv_id_stage
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
(
  input  if_id_t  if_id,
  // register file read data (async) and WB-stage write for same-cycle bypass
  input  word_t   rf_rs1_data,
  input  word_t   rf_rs2_data,
  input  logic    wb_we,
  input  reg_t    wb_rd,
  input  word_t   wb_data,
  // register file read addresses
  output reg_t    rs1_addr,
  output reg_t    rs2_addr,
  output logic    uses_rs1,
  output logic    uses_rs2,
  output logic    bypass_rs1,
  output logic    bypass_rs2,
  output id_ex_t  id_ex_next
);
  logic [6:0] opcode;
  reg_t       rd, rs1, rs2;
  logic [2:0] funct3;
  logic [6:0] funct7;
  logic       dec_illegal, is_ecall, is_ebreak, is_fence;

  rv_decoder u_dec (
    .insn(if_id.insn), .opcode(opcode), .rd(rd), .rs1(rs1), .rs2(rs2),
    .funct3(funct3), .funct7(funct7), .illegal(dec_illegal),
    .is_ecall(is_ecall), .is_ebreak(is_ebreak), .is_fence(is_fence)
  );

  word_t imm;
  rv_imm_gen u_imm (.insn(if_id.insn), .imm(imm));

  logic       reg_we, b_imm, mem_re, mem_we, is_branch, is_jal, is_jalr;
  alu_a_sel_e a_sel;
  alu_op_e    alu_op;
  wb_sel_e    wb_sel;

  rv_control u_ctl (
    .opcode(opcode), .funct3(funct3), .funct7(funct7), .illegal(dec_illegal),
    .reg_we(reg_we), .a_sel(a_sel), .b_imm(b_imm), .alu_op(alu_op),
    .mem_re(mem_re), .mem_we(mem_we), .wb_sel(wb_sel),
    .is_branch(is_branch), .is_jal(is_jal), .is_jalr(is_jalr)
  );

  assign rs1_addr = rs1;
  assign rs2_addr = rs2;

  // Which source registers does this (legal) instruction actually read?
  assign uses_rs1 = !dec_illegal && ((opcode == OPC_JALR)   || (opcode == OPC_BRANCH) ||
                                     (opcode == OPC_LOAD)   || (opcode == OPC_STORE)  ||
                                     (opcode == OPC_OP_IMM) || (opcode == OPC_OP));
  assign uses_rs2 = !dec_illegal && ((opcode == OPC_BRANCH) || (opcode == OPC_STORE) ||
                                     (opcode == OPC_OP));

  // WB->ID bypass: instruction in WB writes the register this instruction reads this cycle.
  assign bypass_rs1 = wb_we && (wb_rd != 5'd0) && (wb_rd == rs1);
  assign bypass_rs2 = wb_we && (wb_rd != 5'd0) && (wb_rd == rs2);

  halt_cause_e id_cause;
  always_comb begin
    id_cause = HALT_NONE;
    if (dec_illegal)    id_cause = HALT_ILLEGAL;
    else if (is_ecall)  id_cause = HALT_ECALL;
    else if (is_ebreak) id_cause = HALT_EBREAK;
  end

  always_comb begin
    id_ex_next.valid     = if_id.valid;
    id_ex_next.pc        = if_id.pc;
    id_ex_next.insn      = if_id.insn;
    id_ex_next.rd        = rd;
    id_ex_next.rs1       = rs1;
    id_ex_next.rs2       = rs2;
    id_ex_next.uses_rs1  = uses_rs1;
    id_ex_next.uses_rs2  = uses_rs2;
    id_ex_next.rs1_data  = bypass_rs1 ? wb_data : rf_rs1_data;
    id_ex_next.rs2_data  = bypass_rs2 ? wb_data : rf_rs2_data;
    id_ex_next.imm       = imm;
    id_ex_next.funct3    = funct3;
    id_ex_next.alu_op    = alu_op;
    id_ex_next.a_sel     = a_sel;
    id_ex_next.b_imm     = b_imm;
    id_ex_next.reg_we    = reg_we;
    id_ex_next.mem_re    = mem_re;
    id_ex_next.mem_we    = mem_we;
    id_ex_next.wb_sel    = wb_sel;
    id_ex_next.is_branch = is_branch;
    id_ex_next.is_jal    = is_jal;
    id_ex_next.is_jalr   = is_jalr;
    id_ex_next.cause     = id_cause;
  end
endmodule
