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
  parameter word_t RESET_PC = 32'h0000_0000,
  parameter logic ENABLE_C = 1'b0,
  parameter logic ENABLE_A = 1'b0,
  parameter logic ENABLE_Z = 1'b0
) (
  input  logic        clk,
  input  logic        rst_n,
  // Instruction port: combinational, aligned 32-bit parcels/words.
  output word_t       imem_addr,
  output word_t       imem_addr_next,
  input  word_t       imem_rdata,
  input  logic        imem_valid,
  input  word_t       imem_rdata_next,
  input  logic        imem_next_valid,
  // Data port; dmem_valid is checked only in explicit C mode.
  output word_t       dmem_addr,
  output logic        dmem_re,
  output logic [3:0]  dmem_we,
  output word_t       dmem_wdata,
  output logic        dmem_atomic_commit,
  input  word_t       dmem_rdata,
  input  logic        dmem_valid,
  // status
  output logic        halted,
  output halt_cause_e halt_cause,
  output word_t       halt_pc,
  // retirement
  output logic        ret_valid,
  output word_t       ret_pc,
  output word_t       ret_insn, // raw bits, zero-extended for compressed form
  output word_t       ret_raw_insn,
  output word_t       ret_expanded_insn,
  output logic [4:0]  ret_ilen_bytes,
  output word_t       ret_pc_next,
  output logic        ret_rd_we,     // register write with rd != x0
  output reg_t        ret_rd,
  output word_t       ret_rd_wdata,
  output logic        ret_mem_re,
  output logic        ret_mem_we,
  output word_t       ret_mem_addr,
  output logic [3:0]  ret_mem_be,
  output word_t       ret_mem_wdata, // lane-aligned
  output word_t       ret_mem_rdata, // raw word read
  output word_t       halt_raw_insn,
  output logic [4:0]  halt_ilen_bytes
);
  // ---------------- Fetch ----------------
  word_t pc, pc_after, pc_next, insn, raw_insn;
  logic [15:0] raw_parcel;
  logic [7:0] c_length_bits;
  logic c_is_compressed, c_is_32bit, c_unsupported_length;
  logic c_illegal, c_hint;
  word_t c_expanded;
  logic fetch_pc_misaligned, fetch_access_fault, fetch_unsupported;
  logic [4:0] ilen_bytes;

  assign imem_addr      = {pc[31:2], 2'b00};
  assign imem_addr_next = imem_addr + 32'd4;
  assign raw_parcel     = pc[1] ? imem_rdata[31:16] : imem_rdata[15:0];

  rv32c_decompressor u_c_decompress (
    .raw_halfword(raw_parcel), .expanded_insn(c_expanded),
    .length_bits(c_length_bits), .is_compressed(c_is_compressed),
    .is_32bit_prefix(c_is_32bit), .unsupported_length(c_unsupported_length),
    .illegal(c_illegal), .hint(c_hint)
  );

  always_comb begin
    insn = imem_rdata;
    raw_insn = imem_rdata;
    ilen_bytes = 5'd4;
    fetch_pc_misaligned = 1'b0;
    fetch_access_fault = 1'b0;
    fetch_unsupported = 1'b0;
    if (ENABLE_C) begin
      if (pc[0]) begin
        insn = 32'b0;
        raw_insn = 32'b0;
        ilen_bytes = 5'd0;
        fetch_pc_misaligned = 1'b1;
      end else if (!imem_valid) begin
        insn = 32'b0;
        raw_insn = 32'b0;
        ilen_bytes = 5'd0;
        fetch_access_fault = 1'b1;
      end else if (c_is_compressed) begin
        insn = c_expanded;
        raw_insn = {16'b0, raw_parcel};
        ilen_bytes = 5'd2;
      end else if (c_is_32bit) begin
        ilen_bytes = 5'd4;
        if (pc[1] && !imem_next_valid) begin
          insn = 32'b0;
          raw_insn = {16'b0, raw_parcel};
          fetch_access_fault = 1'b1;
        end else if (pc[1]) begin
          insn = {imem_rdata_next[15:0], imem_rdata[31:16]};
          raw_insn = insn;
        end else begin
          insn = imem_rdata;
          raw_insn = imem_rdata;
        end
      end else begin
        insn = 32'b0;
        raw_insn = {16'b0, raw_parcel};
        ilen_bytes = c_length_bits == 0 ? 5'd0 : (c_length_bits >> 3);
        fetch_unsupported = c_unsupported_length;
      end
    end
  end

  assign pc_after = pc + ilen_bytes;

  // ---------------- Decode ----------------
  logic [6:0] opcode;
  reg_t       rd, rs1, rs2;
  logic [2:0] funct3;
  logic [6:0] funct7;
  logic       dec_illegal, is_ecall, is_ebreak, is_fence, is_m, is_a;

  rv_decoder #(.ENABLE_A(ENABLE_A), .ENABLE_Z(ENABLE_Z)) u_dec (
    .insn(insn), .opcode(opcode), .rd(rd), .rs1(rs1), .rs2(rs2),
    .funct3(funct3), .funct7(funct7), .illegal(dec_illegal),
    .is_ecall(is_ecall), .is_ebreak(is_ebreak), .is_fence(is_fence), .is_m(is_m), .is_a(is_a)
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
    .is_branch(is_branch), .is_jal(is_jal), .is_jalr(is_jalr), .is_m(is_m), .is_a(is_a)
  );

  // ---------------- Register file / ALU ----------------
  word_t rs1_data, rs2_data, wb_data, alu_a, alu_b, alu_y;
  logic  rf_we;
  logic csr_inst, csr_write;
  logic [11:0] csr_addr;
  word_t csr0, csr1, csr_old, csr_source, csr_new;
  assign csr_inst = ENABLE_Z && opcode == OPC_SYSTEM && !is_ecall && !is_ebreak;
  assign csr_addr = insn[31:20];
  assign csr_old = csr_addr == 12'hCC0 ? CSR_STAGE6_ID :
                   (csr_addr == 12'h800 ? csr0 : csr1);
  assign csr_source = funct3[2] ? {27'b0,rs1} : rs1_data;
  always_comb begin
    csr_new = csr_old;
    csr_write = 1'b0;
    if (csr_inst) begin
      case (funct3[1:0])
        2'b01: begin csr_new = csr_source; csr_write = 1'b1; end
        2'b10: begin csr_new = csr_old | csr_source; csr_write = (rs1 != 0); end
        2'b11: begin csr_new = csr_old & ~csr_source; csr_write = (rs1 != 0); end
        default: ;
      endcase
    end
  end

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
  logic commit;
  logic reservation_valid, atomic_sc, atomic_lr, atomic_write;
  word_t reservation_addr, atomic_new_word, atomic_wb, atomic_addr;
  assign atomic_addr = is_a ? rs1_data : alu_y;
  assign atomic_sc = is_a && funct7[6:2] == 5'b00011;
  assign atomic_lr = is_a && funct7[6:2] == 5'b00010;
  assign atomic_write = is_a && !atomic_lr && (!atomic_sc || (reservation_valid && reservation_addr == atomic_addr));
  rv_a_unit u_a (.funct5(funct7[6:2]), .old_word(dmem_rdata), .source_word(rs2_data), .new_word(atomic_new_word));
  assign atomic_wb = atomic_lr || (is_a && !atomic_sc) ? dmem_rdata :
                     (reservation_valid && reservation_addr == atomic_addr ? 32'b0 : 32'd1);

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin reservation_valid <= 1'b0; reservation_addr <= 32'b0; end
    else if (commit) begin
      if (is_a && atomic_lr) begin reservation_valid <= 1'b1; reservation_addr <= atomic_addr; end
      else if (is_a && atomic_sc) reservation_valid <= 1'b0;
      else if ((mem_we || atomic_write) && reservation_valid &&
               (is_a ? atomic_addr[31:2] : alu_y[31:2]) == reservation_addr[31:2])
        reservation_valid <= 1'b0;
    end
  end

  // ---------------- Branch / jump ----------------
  logic  cmp_taken, redirect;
  word_t target;
  rv_branch_cmp u_bcmp (.a(rs1_data), .b(rs2_data), .funct3(funct3), .taken(cmp_taken));

  assign redirect = (is_branch && cmp_taken) || is_jal || is_jalr;
  assign target   = is_jalr ? {alu_y[31:1], 1'b0} : (pc + imm);
  assign pc_next  = redirect ? target : pc_after;

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
    if (ENABLE_C && fetch_pc_misaligned)  cause = HALT_FETCH_MISALIGN;
    else if (ENABLE_C && fetch_access_fault) cause = HALT_FETCH_ACCESS;
    else if (ENABLE_C && fetch_unsupported)  cause = HALT_ILLEGAL;
    else if (ENABLE_C && c_illegal)          cause = HALT_ILLEGAL;
    else if (dec_illegal)                    cause = HALT_ILLEGAL;
    else if (is_ecall)                    cause = HALT_ECALL;
    else if (is_ebreak)                   cause = HALT_EBREAK;
    else if (!ENABLE_C && redirect && target[1]) cause = HALT_FETCH_MISALIGN;
    else if (mem_re && lsu_misaligned)    cause = HALT_LOAD_MISALIGN;
    else if (mem_we && lsu_misaligned)    cause = HALT_STORE_MISALIGN;
    else if (ENABLE_A && is_a && atomic_addr[1:0] != 0) cause = atomic_lr ? HALT_LOAD_MISALIGN : HALT_STORE_MISALIGN;
    else if (ENABLE_C && mem_re && !dmem_valid) cause = HALT_LOAD_ACCESS;
    else if (ENABLE_C && mem_we && !dmem_valid) cause = HALT_STORE_ACCESS;
    else if (ENABLE_A && is_a && !dmem_valid) cause = atomic_lr ? HALT_LOAD_ACCESS : HALT_STORE_ACCESS;
  end

  assign commit = !halted && (cause == HALT_NONE);

  always_comb begin
    case (wb_sel)
      WB_MEM:  wb_data = lsu_load_data;
      WB_PC4:  wb_data = pc_after;
      default: wb_data = csr_inst ? csr_old : (is_a ? atomic_wb : (is_m ? md_y : alu_y));
    endcase
  end

  assign rf_we      = commit && (reg_we || csr_inst) && (rd != 0);
  assign dmem_addr  = is_a ? atomic_addr : alu_y;
  assign dmem_re    = !halted && (mem_re || is_a) &&
                      (!ENABLE_A || cause == HALT_NONE) &&
                      (!ENABLE_C && !ENABLE_A || dmem_valid);
  assign dmem_we    = commit && (mem_we || atomic_write) ? (is_a ? 4'b1111 : lsu_be) : 4'b0000;
  assign dmem_wdata = is_a ? (atomic_sc ? rs2_data : atomic_new_word) : lsu_wdata;
  assign dmem_atomic_commit = commit && ENABLE_A && is_a;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin csr0 <= 32'b0; csr1 <= 32'b0; end
    else if (commit && csr_write) begin
      if (csr_addr == 12'h800) csr0 <= csr_new;
      else if (csr_addr == 12'h801) csr1 <= csr_new;
    end
  end

  // ---------------- State ----------------
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pc         <= RESET_PC;
      halted     <= 1'b0;
      halt_cause <= HALT_NONE;
      halt_pc    <= 32'h0;
      halt_raw_insn <= 32'h0;
      halt_ilen_bytes <= 5'd0;
    end else if (!halted) begin
      if (cause != HALT_NONE) begin
        halted     <= 1'b1;
        halt_cause <= cause;
        halt_pc    <= pc;
        halt_raw_insn <= raw_insn;
        halt_ilen_bytes <= ilen_bytes;
      end else begin
        pc <= pc_next;
      end
    end
  end

  // ---------------- Retirement port ----------------
  assign ret_valid     = commit;
  assign ret_pc        = pc;
  assign ret_insn      = raw_insn;
  assign ret_raw_insn = raw_insn;
  assign ret_expanded_insn = insn;
  assign ret_ilen_bytes = ilen_bytes;
  assign ret_pc_next   = pc_next;
  assign ret_rd_we     = commit && (reg_we || csr_inst) && (rd != 5'd0);
  assign ret_rd        = rd;
  assign ret_rd_wdata  = wb_data;
  assign ret_mem_re    = commit && mem_re;
  assign ret_mem_we    = commit && (mem_we || atomic_write);
  assign ret_mem_addr  = is_a ? atomic_addr : alu_y;
  assign ret_mem_be    = is_a ? 4'b1111 : lsu_be;
  assign ret_mem_wdata = dmem_wdata;
  assign ret_mem_rdata = dmem_rdata;
endmodule
