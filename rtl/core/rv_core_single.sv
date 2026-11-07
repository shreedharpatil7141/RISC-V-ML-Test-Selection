`timescale 1ns/1ps
// rv_core_single.sv - Non-pipelined (single-cycle) RV32I core. Stage 1 golden baseline.
// Dependencies: rv32_pkg, rv_decoder, rv_imm_gen, rv_regfile, rv_alu, rv_branch_cmp,
//               rv_control, rv_lsu
//
// Memory interface: combinational read, synchronous write (byte enables).
// No trap CSRs yet: ECALL/EBREAK/illegal/misaligned stop the core (halted=1) with
// halt_cause set; the faulting instruction does NOT retire or change state.
// Retirement port is flat (RVVI-inspired); an interface wrapper comes in Stage 2.
module rv_core_single
  import rv32_pkg::*;
#(
  parameter word_t RESET_PC = 32'h0000_0000
) (
  input  logic        clk,
  input  logic        rst_n,
  // instruction port
  output word_t       imem_addr,
  input  word_t       imem_rdata,
  // data port
  output word_t       dmem_addr,
  output logic        dmem_re,
  output logic [3:0]  dmem_we,
  output word_t       dmem_wdata,
  input  word_t       dmem_rdata,
  // status
  output logic        halted,
  output halt_cause_e halt_cause,
  output word_t       halt_pc,
  // retirement
  output logic        ret_valid,
  output word_t       ret_pc,
  output word_t       ret_insn,
  output word_t       ret_pc_next,
  output logic        ret_rd_we,     // register write with rd != x0
  output reg_t        ret_rd,
  output word_t       ret_rd_wdata,
  output logic        ret_mem_re,
  output logic        ret_mem_we,
  output word_t       ret_mem_addr,
  output logic [3:0]  ret_mem_be,
  output word_t       ret_mem_wdata, // lane-aligned
  output word_t       ret_mem_rdata  // raw word read
);
  // ---------------- Fetch ----------------
  word_t pc, pc_plus4, pc_next, insn;
  assign imem_addr = pc;
  assign insn      = imem_rdata;
  assign pc_plus4  = pc + 32'd4;

  // ---------------- Decode ----------------
  logic [6:0] opcode;
  reg_t       rd, rs1, rs2;
  logic [2:0] funct3;
  logic [6:0] funct7;
  logic       dec_illegal, is_ecall, is_ebreak, is_fence, is_m;

  rv_decoder u_dec (
    .insn(insn), .opcode(opcode), .rd(rd), .rs1(rs1), .rs2(rs2),
    .funct3(funct3), .funct7(funct7), .illegal(dec_illegal),
    .is_ecall(is_ecall), .is_ebreak(is_ebreak), .is_fence(is_fence), .is_m(is_m)
  );

  word_t imm;
  rv_imm_gen u_imm (.insn(insn), .imm(imm));

  logic       reg_we, b_imm, mem_re, mem_we, is_branch, is_jal, is_jalr;
  alu_a_sel_e a_sel;
  alu_op_e    alu_op;
  wb_sel_e    wb_sel;

  rv_control u_ctl (
    .opcode(opcode), .funct3(funct3), .funct7(funct7), .illegal(dec_illegal),
    .reg_we(reg_we), .a_sel(a_sel), .b_imm(b_imm), .alu_op(alu_op),
    .mem_re(mem_re), .mem_we(mem_we), .wb_sel(wb_sel),
    .is_branch(is_branch), .is_jal(is_jal), .is_jalr(is_jalr), .is_m(is_m)
  );

  // ---------------- Register file / ALU ----------------
  word_t rs1_data, rs2_data, wb_data, alu_a, alu_b, alu_y;
  logic  rf_we;

  rv_regfile u_rf (
    .clk(clk), .we(rf_we), .waddr(rd), .wdata(wb_data),
    .rs1_addr(rs1), .rs2_addr(rs2), .rs1_data(rs1_data), .rs2_data(rs2_data)
  );

  always_comb begin
    case (a_sel)
      A_PC:    alu_a = pc;
      A_ZERO:  alu_a = 32'h0;
      default: alu_a = rs1_data;
    endcase
    alu_b = b_imm ? imm : rs2_data;
  end

  rv_alu u_alu (.a(alu_a), .b(alu_b), .op(alu_op), .y(alu_y));
  word_t md_y;
  rv_md_comb u_md (.a(rs1_data), .b(rs2_data), .funct3(funct3), .y(md_y));

  // ---------------- Branch / jump ----------------
  logic  cmp_taken, redirect;
  word_t target;
  rv_branch_cmp u_bcmp (.a(rs1_data), .b(rs2_data), .funct3(funct3), .taken(cmp_taken));

  assign redirect = (is_branch && cmp_taken) || is_jal || is_jalr;
  assign target   = is_jalr ? {alu_y[31:1], 1'b0} : (pc + imm);
  assign pc_next  = redirect ? target : pc_plus4;

  // ---------------- Load/store ----------------
  logic [3:0] lsu_be;
  word_t      lsu_wdata, lsu_load_data;
  logic       lsu_misaligned;

  rv_lsu u_lsu (
    .funct3(funct3), .is_load(mem_re), .is_store(mem_we), .addr(alu_y),
    .store_data(rs2_data), .mem_rdata(dmem_rdata),
    .be(lsu_be), .mem_wdata(lsu_wdata), .load_data(lsu_load_data),
    .misaligned(lsu_misaligned)
  );

  // ---------------- Halt / fault detection (priority order) ----------------
  halt_cause_e cause;
  always_comb begin
    cause = HALT_NONE;
    if (dec_illegal)                      cause = HALT_ILLEGAL;
    else if (is_ecall)                    cause = HALT_ECALL;
    else if (is_ebreak)                   cause = HALT_EBREAK;
    else if (redirect && target[1])       cause = HALT_FETCH_MISALIGN; // no C ext: 4-byte aligned only
    else if (mem_re && lsu_misaligned)    cause = HALT_LOAD_MISALIGN;
    else if (mem_we && lsu_misaligned)    cause = HALT_STORE_MISALIGN;
  end

  logic commit;
  assign commit = !halted && (cause == HALT_NONE);

  always_comb begin
    case (wb_sel)
      WB_MEM:  wb_data = lsu_load_data;
      WB_PC4:  wb_data = pc_plus4;
      default: wb_data = is_m ? md_y : alu_y;
    endcase
  end

  assign rf_we      = commit && reg_we;
  assign dmem_addr  = alu_y;
  assign dmem_re    = !halted && mem_re;
  assign dmem_we    = (commit && mem_we) ? lsu_be : 4'b0000;
  assign dmem_wdata = lsu_wdata;

  // ---------------- State ----------------
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pc         <= RESET_PC;
      halted     <= 1'b0;
      halt_cause <= HALT_NONE;
      halt_pc    <= 32'h0;
    end else if (!halted) begin
      if (cause != HALT_NONE) begin
        halted     <= 1'b1;
        halt_cause <= cause;
        halt_pc    <= pc;
      end else begin
        pc <= pc_next;
      end
    end
  end

  // ---------------- Retirement port ----------------
  assign ret_valid     = commit;
  assign ret_pc        = pc;
  assign ret_insn      = insn;
  assign ret_pc_next   = pc_next;
  assign ret_rd_we     = commit && reg_we && (rd != 5'd0);
  assign ret_rd        = rd;
  assign ret_rd_wdata  = wb_data;
  assign ret_mem_re    = commit && mem_re;
  assign ret_mem_we    = commit && mem_we;
  assign ret_mem_addr  = alu_y;
  assign ret_mem_be    = lsu_be;
  assign ret_mem_wdata = lsu_wdata;
  assign ret_mem_rdata = dmem_rdata;
endmodule
