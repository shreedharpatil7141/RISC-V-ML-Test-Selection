`timescale 1ns/1ps
// rv32_pkg.sv - Shared RV32I types, opcodes and control enums.
// Dependencies: none (compile first).
package rv32_pkg;

  typedef logic [31:0] word_t;
  typedef logic [4:0]  reg_t;

  // ---- Base opcodes (insn[6:0]) ----
  localparam logic [6:0] OPC_LUI      = 7'b0110111;
  localparam logic [6:0] OPC_AUIPC    = 7'b0010111;
  localparam logic [6:0] OPC_JAL      = 7'b1101111;
  localparam logic [6:0] OPC_JALR     = 7'b1100111;
  localparam logic [6:0] OPC_BRANCH   = 7'b1100011;
  localparam logic [6:0] OPC_LOAD     = 7'b0000011;
  localparam logic [6:0] OPC_STORE    = 7'b0100011;
  localparam logic [6:0] OPC_OP_IMM   = 7'b0010011;
  localparam logic [6:0] OPC_OP       = 7'b0110011;
  localparam logic [6:0] OPC_MISC_MEM = 7'b0001111;
  localparam logic [6:0] OPC_SYSTEM   = 7'b1110011;
  localparam logic [6:0] OPC_AMO      = 7'b0101111;

  // ---- Fixed full encodings ----
  localparam word_t INSN_ECALL  = 32'h0000_0073;
  localparam word_t INSN_EBREAK = 32'h0010_0073;

  // ---- ALU operation select ----
  typedef enum logic [3:0] {
    ALU_ADD  = 4'd0,
    ALU_SUB  = 4'd1,
    ALU_SLL  = 4'd2,
    ALU_SLT  = 4'd3,
    ALU_SLTU = 4'd4,
    ALU_XOR  = 4'd5,
    ALU_SRL  = 4'd6,
    ALU_SRA  = 4'd7,
    ALU_OR   = 4'd8,
    ALU_AND  = 4'd9
  } alu_op_e;

  // ---- ALU operand A select ----
  typedef enum logic [1:0] {
    A_RS1  = 2'd0,
    A_PC   = 2'd1,
    A_ZERO = 2'd2
  } alu_a_sel_e;

  // ---- Write-back data select ----
  typedef enum logic [1:0] {
    WB_ALU = 2'd0,
    WB_MEM = 2'd1,
    WB_PC4 = 2'd2
  } wb_sel_e;

  // ---- Stage-1 halt causes (no trap CSRs until Stage 7) ----
  // Core stops retiring and reports the cause; numeric values are
  // implementation-defined (NOT RISC-V mcause values).
  typedef enum logic [3:0] {
    HALT_NONE          = 4'd0,
    HALT_ECALL         = 4'd1,
    HALT_EBREAK        = 4'd2,
    HALT_ILLEGAL       = 4'd3,
    HALT_LOAD_MISALIGN = 4'd4,
    HALT_STORE_MISALIGN= 4'd5,
    HALT_FETCH_MISALIGN= 4'd6,
    HALT_LOAD_ACCESS   = 4'd7,
    HALT_STORE_ACCESS  = 4'd8,
    HALT_FETCH_ACCESS  = 4'd9
  } halt_cause_e;

endpackage
