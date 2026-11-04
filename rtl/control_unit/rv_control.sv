`timescale 1ns/1ps
// rv_control.sv - Main control decode (single-cycle).
// All side-effect controls are zero for illegal/system/fence instructions.
module rv_control
  import rv32_pkg::*;
(
  input  logic [6:0] opcode,
  input  logic [2:0] funct3,
  input  logic [6:0] funct7,
  input  logic       illegal,
  output logic       reg_we,
  output alu_a_sel_e a_sel,
  output logic       b_imm,     // 1: ALU B = imm, 0: ALU B = rs2
  output alu_op_e    alu_op,
  output logic       mem_re,
  output logic       mem_we,
  output wb_sel_e    wb_sel,
  output logic       is_branch,
  output logic       is_jal,
  output logic       is_jalr
);
  // funct3 -> ALU op for OP/OP-IMM; alt = funct7[5] (SUB / SRA)
  function automatic alu_op_e f3_to_alu(input logic [2:0] f3, input logic alt);
    case (f3)
      3'b000:  return alt ? ALU_SUB : ALU_ADD;
      3'b001:  return ALU_SLL;
      3'b010:  return ALU_SLT;
      3'b011:  return ALU_SLTU;
      3'b100:  return ALU_XOR;
      3'b101:  return alt ? ALU_SRA : ALU_SRL;
      3'b110:  return ALU_OR;
      default: return ALU_AND;
    endcase
  endfunction

  always_comb begin
    reg_we    = 1'b0;
    a_sel     = A_RS1;
    b_imm     = 1'b0;
    alu_op    = ALU_ADD;
    mem_re    = 1'b0;
    mem_we    = 1'b0;
    wb_sel    = WB_ALU;
    is_branch = 1'b0;
    is_jal    = 1'b0;
    is_jalr   = 1'b0;

    if (!illegal) begin
      case (opcode)
        OPC_LUI:   begin reg_we = 1'b1; a_sel = A_ZERO; b_imm = 1'b1; end
        OPC_AUIPC: begin reg_we = 1'b1; a_sel = A_PC;   b_imm = 1'b1; end
        OPC_JAL:   begin reg_we = 1'b1; is_jal = 1'b1;  wb_sel = WB_PC4; end
        OPC_JALR:  begin reg_we = 1'b1; is_jalr = 1'b1; b_imm = 1'b1; wb_sel = WB_PC4; end
        OPC_BRANCH: is_branch = 1'b1;
        OPC_LOAD:  begin reg_we = 1'b1; b_imm = 1'b1; mem_re = 1'b1; wb_sel = WB_MEM; end
        OPC_STORE: begin b_imm = 1'b1; mem_we = 1'b1; end
        OPC_OP_IMM: begin
          reg_we = 1'b1; b_imm = 1'b1;
          // ADDI/SLTI/... ignore funct7; only SRLI/SRAI use funct7[5]
          alu_op = f3_to_alu(funct3, (funct3 == 3'b101) ? funct7[5] : 1'b0);
        end
        OPC_OP: begin
          reg_we = 1'b1;
          alu_op = f3_to_alu(funct3, funct7[5]);
        end
        default: ; // FENCE, ECALL, EBREAK: no architectural side effects here
      endcase
    end
  end
endmodule
