`timescale 1ns/1ps
// rv_mem_stage.sv - Memory access and precise fault resolution.
// The oldest instruction reaching MEM with a fault halts the core: it does not retire,
// does not write memory, and everything younger is squashed (done in rv_core_pipe).
module rv_mem_stage
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
#(
  parameter bit ENABLE_C = 1'b0,
  parameter bit ENABLE_A = 1'b0
)
(
  input  logic         clk,
  input  logic         rst_n,
  input  ex_mem_t      ex_mem,
  input  word_t        dmem_rdata,
  input  logic         dmem_valid,
  output word_t        dmem_addr,
  output logic         dmem_re,
  output logic [3:0]   dmem_we,
  output word_t        dmem_wdata,
  output logic         dmem_atomic_commit,
  output mem_wb_t      mem_wb_next,
  output logic         fault,
  output halt_cause_e  fault_cause
);
  logic [3:0] lsu_be;
  word_t      lsu_wdata, lsu_load_data;
  logic       lsu_misaligned;
  logic reservation_valid, sc_success, atomic_write;
  word_t reservation_addr, atomic_new_word, atomic_wb;
  logic atomic_lr, atomic_sc;

  assign atomic_lr = ex_mem.is_a && ex_mem.insn[31:27] == 5'b00010;
  assign atomic_sc = ex_mem.is_a && ex_mem.insn[31:27] == 5'b00011;
  assign sc_success = reservation_valid && reservation_addr == ex_mem.alu_y;
  assign atomic_write = ex_mem.is_a && !atomic_lr && (!atomic_sc || sc_success);
  rv_a_unit u_a (.funct5(ex_mem.insn[31:27]), .old_word(dmem_rdata),
                 .source_word(ex_mem.store_data), .new_word(atomic_new_word));
  assign atomic_wb = atomic_lr || (!atomic_sc && ex_mem.is_a) ? dmem_rdata : (sc_success ? 32'b0 : 32'd1);

  rv_lsu u_lsu (
    .funct3(ex_mem.funct3), .is_load(ex_mem.mem_re), .is_store(ex_mem.mem_we),
    .addr(ex_mem.alu_y), .store_data(ex_mem.store_data), .mem_rdata(dmem_rdata),
    .be(lsu_be), .mem_wdata(lsu_wdata), .load_data(lsu_load_data),
    .misaligned(lsu_misaligned)
  );

  halt_cause_e cause;
  always_comb begin
    cause = ex_mem.cause;
    if (cause == HALT_NONE) begin
      if (ex_mem.mem_re && lsu_misaligned)      cause = HALT_LOAD_MISALIGN;
      else if (ex_mem.mem_we && lsu_misaligned) cause = HALT_STORE_MISALIGN;
      else if (ENABLE_C && ex_mem.mem_re && !dmem_valid) cause = HALT_LOAD_ACCESS;
      else if (ENABLE_C && ex_mem.mem_we && !dmem_valid) cause = HALT_STORE_ACCESS;
      else if (ENABLE_A && ex_mem.is_a && ex_mem.alu_y[1:0] != 0)
        cause = atomic_lr ? HALT_LOAD_MISALIGN : HALT_STORE_MISALIGN;
      else if (ENABLE_A && ex_mem.is_a && !dmem_valid)
        cause = atomic_lr ? HALT_LOAD_ACCESS : HALT_STORE_ACCESS;
    end
  end

  assign fault       = ex_mem.valid && (cause != HALT_NONE);
  assign fault_cause = cause;

  logic commit;
  assign commit = ex_mem.valid && (cause == HALT_NONE);

  assign dmem_addr  = ex_mem.alu_y;
  assign dmem_re    = ex_mem.valid && (ex_mem.mem_re || (ENABLE_A && ex_mem.is_a)) &&
                      (!ENABLE_A || cause == HALT_NONE) &&
                      (!ENABLE_C && !ENABLE_A || dmem_valid);
  assign dmem_we    = commit && (ex_mem.mem_we || atomic_write) ? (ex_mem.is_a ? 4'b1111 : lsu_be) : 4'b0000;
  assign dmem_wdata = ex_mem.is_a ? (atomic_sc ? ex_mem.store_data : atomic_new_word) : lsu_wdata;
  assign dmem_atomic_commit = commit && ENABLE_A && ex_mem.is_a;

  // Reservation belongs to this single-hart MEM/commit boundary. Faulting
  // operations cannot alter it; each completed SC consumes it.
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin reservation_valid <= 1'b0; reservation_addr <= 32'b0; end
    else if (commit) begin
      if (atomic_lr) begin reservation_valid <= 1'b1; reservation_addr <= ex_mem.alu_y; end
      else if (atomic_sc) reservation_valid <= 1'b0;
      else if ((ex_mem.mem_we || atomic_write) && reservation_valid &&
               ex_mem.alu_y[31:2] == reservation_addr[31:2])
        reservation_valid <= 1'b0;
    end
  end

  always_comb begin
    mem_wb_next.valid    = commit;
    mem_wb_next.pc       = ex_mem.pc;
    mem_wb_next.raw_insn = ex_mem.raw_insn;
    mem_wb_next.insn     = ex_mem.insn;
    mem_wb_next.ilen_bytes = ex_mem.ilen_bytes;
    mem_wb_next.rd       = ex_mem.rd;
    mem_wb_next.reg_we   = ex_mem.reg_we;
    mem_wb_next.wb_data  = ex_mem.is_a ? atomic_wb : (ex_mem.mem_re ? lsu_load_data : ex_mem.alu_y);
    mem_wb_next.ld_re    = ex_mem.mem_re;
    mem_wb_next.st_we    = ex_mem.mem_we || atomic_write;
    mem_wb_next.csr_write = ex_mem.csr_write;
    mem_wb_next.csr_addr  = ex_mem.csr_addr;
    mem_wb_next.csr_new   = ex_mem.csr_new;
    mem_wb_next.mem_addr = ex_mem.alu_y;
    mem_wb_next.st_be    = ex_mem.is_a ? 4'b1111 : lsu_be;
    mem_wb_next.st_wdata = dmem_wdata;
    mem_wb_next.ld_rdata = dmem_rdata;
  end
endmodule
