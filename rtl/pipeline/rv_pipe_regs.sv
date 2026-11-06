`timescale 1ns/1ps
// rv_pipe_regs.sv - IF/ID, ID/EX, EX/MEM, MEM/WB registers with stall/flush control.
//   kill     : fault resolved in MEM, or already halted -> squash IF/ID, ID/EX, EX/MEM
//   redirect : taken branch/jump in EX -> squash IF/ID and ID/EX
//   stall    : load-use -> hold IF/ID, insert bubble into ID/EX
// MEM/WB always loads mem_wb_next (its valid is already 0 for a faulting instruction).
// Bubbles are all-zero structs (valid=0, cause=HALT_NONE).
module rv_pipe_regs
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
(
  input  logic    clk,
  input  logic    rst_n,
  input  logic    stall,
  input  logic    redirect,
  input  logic    kill,
  input  if_id_t  if_id_next,
  input  id_ex_t  id_ex_next,
  input  ex_mem_t ex_mem_next,
  input  mem_wb_t mem_wb_next,
  output if_id_t  if_id,
  output id_ex_t  id_ex,
  output ex_mem_t ex_mem,
  output mem_wb_t mem_wb
);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      if_id  <= '0;
      id_ex  <= '0;
      ex_mem <= '0;
      mem_wb <= '0;
    end else begin
      mem_wb <= mem_wb_next;

      if (kill) ex_mem <= '0;
      else      ex_mem <= ex_mem_next;

      if (kill || redirect || stall) id_ex <= '0;
      else                           id_ex <= id_ex_next;

      if (kill || redirect) if_id <= '0;
      else if (!stall)      if_id <= if_id_next;
    end
  end
endmodule
