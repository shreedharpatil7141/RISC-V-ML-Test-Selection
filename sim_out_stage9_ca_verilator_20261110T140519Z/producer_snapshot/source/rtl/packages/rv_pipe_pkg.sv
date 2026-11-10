`timescale 1ns/1ps
// rv_pipe_pkg.sv - Pipeline register types and forwarding select for the 5-stage core.
// Dependencies: rv32_pkg (compile first).
package rv_pipe_pkg;
  import rv32_pkg::*;

  // IF/ID
  typedef struct packed {
    logic  valid;
    word_t pc;
    word_t raw_insn;
    word_t insn;
    logic [4:0] ilen_bytes;
    halt_cause_e cause;
  } if_id_t;

  // ID/EX
  typedef struct packed {
    logic        valid;
    word_t       pc;
    word_t       raw_insn;
    word_t       insn;
    logic [4:0]  ilen_bytes;
    reg_t        rd;
    reg_t        rs1;
    reg_t        rs2;
    logic        uses_rs1;
    logic        uses_rs2;
    word_t       rs1_data;   // register-file value (incl. WB->ID bypass)
    word_t       rs2_data;
    word_t       imm;
    logic [2:0]  funct3;
    alu_op_e     alu_op;
    logic        is_m;
    logic        is_a;
    alu_a_sel_e  a_sel;
    logic        b_imm;
    logic        reg_we;
    logic        mem_re;
    logic        mem_we;
    wb_sel_e     wb_sel;
    logic        is_branch;
    logic        is_jal;
    logic        is_jalr;
    logic        is_fencei;
    logic        is_csr;
    logic        is_mret;
    logic [11:0] csr_addr;
    word_t       csr_old;
    halt_cause_e cause;      // fault detected so far (resolved in MEM)
  } id_ex_t;

  // EX/MEM
  typedef struct packed {
    logic        valid;
    word_t       pc;
    word_t       raw_insn;
    word_t       insn;
    logic [4:0]  ilen_bytes;
    reg_t        rd;
    reg_t        rs2;
    logic        reg_we;
    logic [2:0]  funct3;
    logic        mem_re;
    logic        mem_we;
    logic        is_a;
    logic        csr_write;
    logic        is_mret;
    logic [11:0] csr_addr;
    word_t       csr_new;
    word_t       csr_source;
    word_t       alu_y;       // ALU result / mem address; pc+4 for JAL/JALR
    word_t       store_data;  // forwarded rs2
    halt_cause_e cause;
  } ex_mem_t;

  // MEM/WB
  typedef struct packed {
    logic        valid;
    word_t       pc;
    word_t       raw_insn;
    word_t       insn;
    logic [4:0]  ilen_bytes;
    reg_t        rd;
    logic        reg_we;
    word_t       wb_data;
    logic        ld_re;
    logic        st_we;
    logic        csr_write;
    logic        is_mret;
    logic [11:0] csr_addr;
    word_t       csr_new;
    word_t       csr_source;
    word_t       mem_addr;
    logic [3:0]  st_be;
    word_t       st_wdata;
    word_t       ld_rdata;
  } mem_wb_t;

  typedef enum logic [1:0] {
    FWD_NONE  = 2'd0,
    FWD_EXMEM = 2'd1,
    FWD_MEMWB = 2'd2
  } fwd_sel_e;

endpackage
