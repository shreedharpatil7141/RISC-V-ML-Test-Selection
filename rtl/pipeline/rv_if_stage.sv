`timescale 1ns/1ps
// rv_if_stage.sv - Instruction fetch: PC register and fetch of imem_rdata.
// PC update priority: halted (hold) > redirect > stall (hold) > pc+4.
module rv_if_stage
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
#(
  parameter word_t RESET_PC = 32'h0000_0000
) (
  input  logic   clk,
  input  logic   rst_n,
  input  logic   stall,
  input  logic   redirect,
  input  word_t  redirect_target,
  input  logic   halted,
  output word_t  imem_addr,
  input  word_t  imem_rdata,
  output if_id_t if_id_next
);
  word_t pc;
  assign imem_addr = pc;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)        pc <= RESET_PC;
    else if (halted)   pc <= pc;
    else if (redirect) pc <= redirect_target;
    else if (!stall)   pc <= pc + 32'd4;
  end

  assign if_id_next.valid = 1'b1;
  assign if_id_next.pc    = pc;
  assign if_id_next.insn  = imem_rdata;
endmodule
