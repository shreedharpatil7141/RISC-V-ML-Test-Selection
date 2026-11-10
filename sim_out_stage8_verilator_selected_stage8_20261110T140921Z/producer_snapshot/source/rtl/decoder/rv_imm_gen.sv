`timescale 1ns/1ps
// rv_imm_gen.sv - Immediate generator for I/S/B/U/J formats.
module rv_imm_gen
  import rv32_pkg::*;
(
  input  word_t insn,
  output word_t imm
);
  always_comb begin
    case (insn[6:0])
      OPC_OP_IMM, OPC_LOAD, OPC_JALR:
        imm = {{20{insn[31]}}, insn[31:20]};
      OPC_STORE:
        imm = {{20{insn[31]}}, insn[31:25], insn[11:7]};
      OPC_BRANCH:
        imm = {{19{insn[31]}}, insn[31], insn[7], insn[30:25], insn[11:8], 1'b0};
      OPC_LUI, OPC_AUIPC:
        imm = {insn[31:12], 12'b0};
      OPC_JAL:
        imm = {{11{insn[31]}}, insn[31], insn[19:12], insn[20], insn[30:21], 1'b0};
      default:
        imm = 32'h0;
    endcase
  end
endmodule
