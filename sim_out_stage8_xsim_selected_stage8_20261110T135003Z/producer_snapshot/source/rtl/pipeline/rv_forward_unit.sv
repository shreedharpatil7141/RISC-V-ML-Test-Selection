`timescale 1ns/1ps
// rv_forward_unit.sv - EX-stage operand forwarding selects.
// Priority: EX/MEM (youngest producer) over MEM/WB. x0 never forwarded.
// A load in EX/MEM is NOT forwarded from (data not ready): the hazard unit stalls instead.
module rv_forward_unit
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
(
  input  reg_t ex_rs1,
  input  reg_t ex_rs2,
  input  logic exmem_valid,
  input  logic exmem_reg_we,
  input  logic exmem_is_load,
  input  reg_t exmem_rd,
  input  logic memwb_valid,
  input  logic memwb_reg_we,
  input  reg_t memwb_rd,
  output fwd_sel_e fwd_a,
  output fwd_sel_e fwd_b,
  // match flags (also used for coverage / assertions)
  output logic a_exmem_match,
  output logic a_memwb_match,
  output logic b_exmem_match,
  output logic b_memwb_match
);
  logic exmem_prod, memwb_prod;
  assign exmem_prod = exmem_valid && exmem_reg_we && (exmem_rd != 5'd0) && !exmem_is_load;
  assign memwb_prod = memwb_valid && memwb_reg_we && (memwb_rd != 5'd0);

  assign a_exmem_match = exmem_prod && (exmem_rd == ex_rs1);
  assign a_memwb_match = memwb_prod && (memwb_rd == ex_rs1);
  assign b_exmem_match = exmem_prod && (exmem_rd == ex_rs2);
  assign b_memwb_match = memwb_prod && (memwb_rd == ex_rs2);

  assign fwd_a = a_exmem_match ? FWD_EXMEM : (a_memwb_match ? FWD_MEMWB : FWD_NONE);
  assign fwd_b = b_exmem_match ? FWD_EXMEM : (b_memwb_match ? FWD_MEMWB : FWD_NONE);
endmodule
