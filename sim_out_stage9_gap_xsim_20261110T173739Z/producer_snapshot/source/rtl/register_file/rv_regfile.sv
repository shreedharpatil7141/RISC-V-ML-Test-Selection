`timescale 1ns/1ps
// rv_regfile.sv - 32x32 register file, 2 async read ports, 1 sync write port.
// x0 reads as zero and ignores writes. Registers start at 0 in simulation
// (architecturally undefined at reset; zeroed for deterministic traces).
module rv_regfile
  import rv32_pkg::*;
(
  input  logic  clk,
  input  logic  we,
  input  reg_t  waddr,
  input  word_t wdata,
  input  reg_t  rs1_addr,
  input  reg_t  rs2_addr,
  output word_t rs1_data,
  output word_t rs2_data
);
  word_t regs [32];

  initial begin
    for (int i = 0; i < 32; i++) regs[i] = 32'h0;
  end

  always_ff @(posedge clk) begin
    if (we && (waddr != 5'd0)) regs[waddr] <= wdata;
  end

  assign rs1_data = (rs1_addr == 5'd0) ? 32'h0 : regs[rs1_addr];
  assign rs2_data = (rs2_addr == 5'd0) ? 32'h0 : regs[rs2_addr];
endmodule
