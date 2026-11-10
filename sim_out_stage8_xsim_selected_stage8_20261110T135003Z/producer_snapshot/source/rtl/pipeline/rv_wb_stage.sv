`timescale 1ns/1ps
// rv_wb_stage.sv - Write-back: register write request and retirement port.
// One retirement per instruction, in program order, from MEM/WB only (no stall/flush duplicates).
module rv_wb_stage
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
(
  input  mem_wb_t     mem_wb,
  output logic        rf_we,
  output reg_t        rf_rd,
  output word_t       rf_wdata,
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
  output word_t       ret_mem_rdata
);
  assign rf_we    = mem_wb.valid && mem_wb.reg_we;
  assign rf_rd    = mem_wb.rd;
  assign rf_wdata = mem_wb.wb_data;

  assign ret_valid     = mem_wb.valid;
  assign ret_pc        = mem_wb.pc;
  assign ret_insn      = mem_wb.raw_insn;
  assign ret_expanded_insn = mem_wb.insn;
  assign ret_ilen_bytes = mem_wb.ilen_bytes;
  assign ret_rd_we     = mem_wb.valid && mem_wb.reg_we && (mem_wb.rd != 5'd0);
  assign ret_rd        = mem_wb.rd;
  assign ret_rd_wdata  = mem_wb.wb_data;
  assign ret_mem_re    = mem_wb.valid && mem_wb.ld_re;
  assign ret_mem_we    = mem_wb.valid && mem_wb.st_we;
  assign ret_mem_addr  = mem_wb.mem_addr;
  assign ret_mem_be    = mem_wb.st_be;
  assign ret_mem_wdata = mem_wb.st_wdata;
  assign ret_mem_rdata = mem_wb.ld_rdata;
endmodule
