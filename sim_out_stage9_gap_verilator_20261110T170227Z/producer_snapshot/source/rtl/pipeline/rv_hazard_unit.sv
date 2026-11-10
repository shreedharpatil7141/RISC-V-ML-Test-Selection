`timescale 1ns/1ps
// rv_hazard_unit.sv - Load-use hazard detection (1-cycle stall).
// Stall when the instruction in ID needs a register that a load in EX will produce.
// Everything else is resolved by forwarding. Stall holds PC and IF/ID and bubbles ID/EX.
module rv_hazard_unit
  import rv32_pkg::*;
(
  input  logic id_valid,
  input  reg_t id_rs1,
  input  reg_t id_rs2,
  input  logic id_uses_rs1,
  input  logic id_uses_rs2,
  input  logic ex_valid,
  input  logic ex_mem_re,
  input  reg_t ex_rd,
  output logic stall
);
  assign stall = id_valid && ex_valid && ex_mem_re && (ex_rd != 5'd0) &&
                 ((id_uses_rs1 && (id_rs1 == ex_rd)) ||
                  (id_uses_rs2 && (id_rs2 == ex_rd)));
endmodule