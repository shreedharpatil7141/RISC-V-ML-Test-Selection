`timescale 1ns/1ps
// rv_alu.sv - Integer ALU. Shift amount is b[4:0].
module rv_alu
  import rv32_pkg::*;
(
  input  word_t   a,
  input  word_t   b,
  input  alu_op_e op,
  output word_t   y
);
  always_comb begin
    case (op)
      ALU_ADD:  y = a + b;
      ALU_SUB:  y = a - b;
      ALU_SLL:  y = a << b[4:0];
      ALU_SLT:  y = {31'b0, ($signed(a) < $signed(b))};
      ALU_SLTU: y = {31'b0, (a < b)};
      ALU_XOR:  y = a ^ b;
      ALU_SRL:  y = a >> b[4:0];
      ALU_SRA:  y = word_t'($signed(a) >>> b[4:0]);
      ALU_OR:   y = a | b;
      ALU_AND:  y = a & b;
      default:  y = 32'h0;
    endcase
  end
endmodule
