`timescale 1ns/1ps
// rv_decoder.sv - Field extraction and RV32I legality check.
// Stage 1: only RV32I + FENCE + ECALL/EBREAK are legal. M/A/C/Zicsr/Zifencei/MRET
// are reported illegal until their stages are implemented.
module rv_decoder
  import rv32_pkg::*;
#(
  parameter bit ENABLE_A = 1'b0,
  parameter bit ENABLE_Z = 1'b0
)
(
  input  word_t insn,
  output logic [6:0] opcode,
  output reg_t       rd,
  output reg_t       rs1,
  output reg_t       rs2,
  output logic [2:0] funct3,
  output logic [6:0] funct7,
  output logic       illegal,
  output logic       is_ecall,
  output logic       is_ebreak,
  output logic       is_fence,
  output logic       is_m,
  output logic       is_a
);
  assign opcode = insn[6:0];
  assign rd     = insn[11:7];
  assign rs1    = insn[19:15];
  assign rs2    = insn[24:20];
  assign funct3 = insn[14:12];
  assign funct7 = insn[31:25];

  always_comb begin
    illegal   = 1'b0;
    is_ecall  = 1'b0;
    is_ebreak = 1'b0;
    is_fence  = 1'b0;
    is_m      = 1'b0;
    is_a      = 1'b0;

    if (insn[1:0] != 2'b11) begin
      illegal = 1'b1;  // 16-bit (C) encodings unsupported until Stage 4
    end else begin
      case (opcode)
        OPC_LUI, OPC_AUIPC, OPC_JAL: illegal = 1'b0;

        OPC_JALR: illegal = (funct3 != 3'b000);

        OPC_BRANCH: illegal = (funct3 == 3'b010) || (funct3 == 3'b011);

        OPC_LOAD: illegal = !((funct3 == 3'b000) || (funct3 == 3'b001) ||
                              (funct3 == 3'b010) || (funct3 == 3'b100) ||
                              (funct3 == 3'b101));

        OPC_STORE: illegal = !((funct3 == 3'b000) || (funct3 == 3'b001) ||
                               (funct3 == 3'b010));

        OPC_OP_IMM: begin
          if (funct3 == 3'b001)
            illegal = (funct7 != 7'b0000000);                       // SLLI
          else if (funct3 == 3'b101)
            illegal = !((funct7 == 7'b0000000) || (funct7 == 7'b0100000)); // SRLI/SRAI
        end

        OPC_OP: begin
          if (funct7 == 7'b0000000)
            illegal = 1'b0;
          else if (funct7 == 7'b0100000)
            illegal = !((funct3 == 3'b000) || (funct3 == 3'b101)); // SUB/SRA only
          else if (funct7 == 7'b0000001) begin
            illegal = 1'b0;
            is_m = 1'b1;
          end else
            illegal = 1'b1;                                         // M ext: Stage 3
        end

        OPC_AMO: begin
          is_a = ENABLE_A && (insn[14:12] == 3'b010) &&
                 ((insn[31:27] == 5'b00010 && insn[24:20] == 5'b0) ||
                  insn[31:27] == 5'b00011 || insn[31:27] == 5'b00001 ||
                  insn[31:27] == 5'b00000 || insn[31:27] == 5'b00100 ||
                  insn[31:27] == 5'b01100 || insn[31:27] == 5'b01000 ||
                  insn[31:27] == 5'b10000 || insn[31:27] == 5'b10100 ||
                  insn[31:27] == 5'b11000 || insn[31:27] == 5'b11100);
          illegal = !is_a;
        end

        OPC_MISC_MEM: begin
          if (funct3 == 3'b000) is_fence = 1'b1;
          else if (ENABLE_Z && insn == 32'h0000_100F) is_fence = 1'b1;
          else illegal = 1'b1;
        end

        OPC_SYSTEM: begin
          if      (insn == INSN_ECALL)  is_ecall  = 1'b1;
          else if (insn == INSN_EBREAK) is_ebreak = 1'b1;
          else if (ENABLE_Z && (funct3 inside {3'b001,3'b010,3'b011,3'b101,3'b110,3'b111})) begin
            if ((insn[31:20] == 12'h800) || (insn[31:20] == 12'h801)) illegal = 1'b0;
            else if ((insn[31:20] == 12'hCC0) &&
                     ((funct3 == 3'b010) || (funct3 == 3'b011) ||
                      (funct3 == 3'b110) || (funct3 == 3'b111)) &&
                     (insn[19:15] == 5'd0)) illegal = 1'b0;
            else illegal = 1'b1;
          end
          else                          illegal   = 1'b1;           // MRET and unsupported CSRs: Stage 7
        end

        default: illegal = 1'b1;
      endcase
    end
  end
endmodule
