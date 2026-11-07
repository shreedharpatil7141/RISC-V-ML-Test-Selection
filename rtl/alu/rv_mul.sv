`timescale 1ns/1ps
// Combinational RV32M multiplier. funct3 000..011 selects MUL/MULH/MULHSU/MULHU.
module rv_mul (
  input  logic [2:0]  funct3,
  input  logic [31:0] a,
  input  logic [31:0] b,
  output logic [31:0] y
);
  logic signed [63:0] a_ss, b_ss, b_su;
  logic signed [63:0] product_ss, product_su;
  logic        [63:0] product_uu;

  always_comb begin
    a_ss = {{32{a[31]}}, a};
    b_ss = {{32{b[31]}}, b};
    b_su = $signed({32'b0, b});
    product_ss = a_ss * b_ss;
    product_su = a_ss * b_su;
    product_uu = {32'b0, a} * {32'b0, b};
    case (funct3)
      3'b000: y = product_uu[31:0];
      3'b001: y = product_ss[63:32];
      3'b010: y = product_su[63:32];
      default: y = product_uu[63:32];
    endcase
  end
endmodule
