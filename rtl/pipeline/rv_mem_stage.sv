`timescale 1ns/1ps
// rv_mem_stage.sv - Memory access and precise fault resolution.
// The oldest instruction reaching MEM with a fault halts the core: it does not retire,
// does not write memory, and everything younger is squashed (done in rv_core_pipe).
module rv_mem_stage
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
#(
  parameter bit ENABLE_C = 1'b0
)
(
  input  ex_mem_t      ex_mem,
  input  word_t        dmem_rdata,
  input  logic         dmem_valid,
  output word_t        dmem_addr,
  output logic         dmem_re,
  output logic [3:0]   dmem_we,
  output word_t        dmem_wdata,
  output mem_wb_t      mem_wb_next,
  output logic         fault,
  output halt_cause_e  fault_cause
);
  logic [3:0] lsu_be;
  word_t      lsu_wdata, lsu_load_data;
  logic       lsu_misaligned;

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
    end
  end

  assign fault       = ex_mem.valid && (cause != HALT_NONE);
  assign fault_cause = cause;

  logic commit;
  assign commit = ex_mem.valid && (cause == HALT_NONE);

  assign dmem_addr  = ex_mem.alu_y;
  assign dmem_re    = ex_mem.valid && ex_mem.mem_re && (!ENABLE_C || dmem_valid);
  assign dmem_we    = (commit && ex_mem.mem_we) ? lsu_be : 4'b0000;
  assign dmem_wdata = lsu_wdata;

  always_comb begin
    mem_wb_next.valid    = commit;
    mem_wb_next.pc       = ex_mem.pc;
    mem_wb_next.raw_insn = ex_mem.raw_insn;
    mem_wb_next.insn     = ex_mem.insn;
    mem_wb_next.ilen_bytes = ex_mem.ilen_bytes;
    mem_wb_next.rd       = ex_mem.rd;
    mem_wb_next.reg_we   = ex_mem.reg_we;
    mem_wb_next.wb_data  = ex_mem.mem_re ? lsu_load_data : ex_mem.alu_y;
    mem_wb_next.ld_re    = ex_mem.mem_re;
    mem_wb_next.st_we    = ex_mem.mem_we;
    mem_wb_next.mem_addr = ex_mem.alu_y;
    mem_wb_next.st_be    = lsu_be;
    mem_wb_next.st_wdata = lsu_wdata;
    mem_wb_next.ld_rdata = dmem_rdata;
  end
endmodule
