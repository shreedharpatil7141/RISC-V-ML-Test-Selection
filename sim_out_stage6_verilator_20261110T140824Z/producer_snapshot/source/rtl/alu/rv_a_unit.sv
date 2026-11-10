`timescale 1ns/1ps
// Combinational RV32A word operation. Transaction authorization and
// reservation ownership belong to the MEM-stage caller.
module rv_a_unit (
  input  logic [4:0]  funct5,
  input  logic [31:0] old_word,
  input  logic [31:0] source_word,
  output logic [31:0] new_word
);
  logic signed [31:0] old_s, source_s;
  always_comb begin
    old_s = old_word;
    source_s = source_word;
    case (funct5)
      5'b00001: new_word = source_word;                         // AMOSWAP
      5'b00000: new_word = old_word + source_word;               // AMOADD
      5'b00100: new_word = old_word ^ source_word;
      5'b01100: new_word = old_word & source_word;
      5'b01000: new_word = old_word | source_word;
      5'b10000: new_word = (old_s < source_s) ? old_word : source_word;
      5'b10100: new_word = (old_s > source_s) ? old_word : source_word;
      5'b11000: new_word = (old_word < source_word) ? old_word : source_word;
      5'b11100: new_word = (old_word > source_word) ? old_word : source_word;
      default:  new_word = 32'b0;
    endcase
  end
endmodule
