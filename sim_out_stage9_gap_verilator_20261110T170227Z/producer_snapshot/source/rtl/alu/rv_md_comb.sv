`timescale 1ns/1ps
// Combinational RV32M arithmetic for the single-cycle golden core.
// Divide/remainder are behavioral operators here; iterative implementation is deferred.
module rv_md_comb (
  input  logic [2:0]  funct3,
  input  logic [31:0] a,
  input  logic [31:0] b,
  output logic [31:0] y
);
  logic signed [63:0] a_ss, b_ss, b_su;
  logic signed [63:0] prod_ss;
  logic signed [63:0] prod_su;
  logic        [63:0] prod_uu;
  always_comb begin
    // Explicit 64-bit operands keep expression sizing unambiguous in simulators.
    a_ss = {{32{a[31]}}, a};
    b_ss = {{32{b[31]}}, b};
    b_su = $signed({32'b0, b});
    prod_ss = a_ss * b_ss;
    prod_su = a_ss * b_su;
    prod_uu = {32'b0, a} * {32'b0, b};
    case (funct3)
      3'b000: y = prod_uu[31:0];
      3'b001: y = prod_ss[63:32];
      3'b010: y = prod_su[63:32];
      3'b011: y = prod_uu[63:32];
      3'b100: begin
        if (b == 0) y = 32'hffff_ffff;
        else if (a == 32'h8000_0000 && b == 32'hffff_ffff) y = a;
        else y = $signed(a) / $signed(b);
      end
      3'b101: y = (b == 0) ? 32'hffff_ffff : a / b;
      3'b110: begin
        if (b == 0) y = a;
        else if (a == 32'h8000_0000 && b == 32'hffff_ffff) y = 0;
        else y = $signed(a) % $signed(b);
      end
      default: y = (b == 0) ? a : a % b;
    endcase
  end
endmodule
