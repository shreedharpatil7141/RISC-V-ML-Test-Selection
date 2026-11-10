`timescale 1ns/1ps
// Pipeline M execution wrapper: one-cycle multiply and fixed-latency iterative divide.
module rv_md_exec (
  input  logic        clk,
  input  logic        rst_n,
  input  logic        start,       // one accepted request for DIV/DIVU/REM/REMU
  input  logic        abort,
  input  logic [2:0]  funct3,
  input  logic [31:0] a,
  input  logic [31:0] b,
  output logic        ready,
  output logic        accepted,
  output logic        busy,
  output logic        done,
  output logic        aborted,
  output logic [31:0] y
);
  logic [31:0] mul_y, div_y;

  rv_mul u_mul (.funct3(funct3), .a(a), .b(b), .y(mul_y));
  rv_div_iter #(.W(32)) u_div (
    .clk(clk), .rst_n(rst_n), .start(start && funct3[2]), .abort(abort),
    .funct3(funct3), .dividend(a), .divisor(b), .ready(ready), .accepted(accepted),
    .busy(busy), .done(done), .aborted(aborted), .result(div_y)
  );
  assign y = funct3[2] ? div_y : mul_y;
endmodule
