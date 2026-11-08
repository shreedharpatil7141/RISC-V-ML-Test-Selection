`timescale 1ns/1ps
// IF fetches an aligned word plus its successor. ENABLE_C permits a parcel PC,
// expands 16-bit instructions, and assembles 32-bit instructions across words.
module rv_if_stage
  import rv32_pkg::*;
  import rv_pipe_pkg::*;
#(
  parameter word_t RESET_PC = 32'h0000_0000,
  parameter bit ENABLE_C = 1'b0
) (
  input  logic   clk,
  input  logic   rst_n,
  input  logic   stall,
  input  logic   redirect,
  input  word_t  redirect_target,
  input  logic   halted,
  output word_t  imem_addr,
  output word_t  imem_addr_next,
  input  word_t  imem_rdata,
  input  logic   imem_valid,
  input  word_t  imem_rdata_next,
  input  logic   imem_next_valid,
  output if_id_t if_id_next
);
  word_t pc;
  logic [15:0] parcel;
  logic [7:0] length_bits;
  logic c_compressed, c_prefix32, c_long, c_illegal, c_hint;
  word_t expanded, raw, execution_insn;
  logic [4:0] instruction_bytes;
  halt_cause_e fetch_cause;

  assign imem_addr = {pc[31:2], 2'b00};
  assign imem_addr_next = imem_addr + 32'd4;
  assign parcel = pc[1] ? imem_rdata[31:16] : imem_rdata[15:0];

  rv32c_decompressor u_decompress (
    .raw_halfword(parcel), .expanded_insn(expanded), .length_bits(length_bits),
    .is_compressed(c_compressed), .is_32bit_prefix(c_prefix32),
    .unsupported_length(c_long), .illegal(c_illegal), .hint(c_hint)
  );

  always_comb begin
    instruction_bytes = ENABLE_C ? 5'd2 : 5'd4;
    execution_insn = imem_rdata;
    raw = imem_rdata;
    fetch_cause = HALT_NONE;
    if (ENABLE_C) begin
      if (pc[0]) begin
        instruction_bytes = 5'd0;
        execution_insn = 32'b0;
        raw = 32'b0;
        fetch_cause = HALT_FETCH_MISALIGN;
      end else if (!imem_valid) begin
        instruction_bytes = 5'd0;
        execution_insn = 32'b0;
        raw = 32'b0;
        fetch_cause = HALT_FETCH_ACCESS;
      end else if (c_compressed) begin
        instruction_bytes = 5'd2;
        execution_insn = expanded;
        raw = {16'b0, parcel};
        if (c_illegal) fetch_cause = HALT_ILLEGAL;
      end else if (c_prefix32) begin
        instruction_bytes = 5'd4;
        if (pc[1]) begin
          raw = {imem_rdata_next[15:0], parcel};
          execution_insn = raw;
          if (!imem_next_valid) begin
            execution_insn = 32'b0;
            fetch_cause = HALT_FETCH_ACCESS;
          end
        end else begin
          raw = imem_rdata;
          execution_insn = imem_rdata;
        end
      end else begin
        instruction_bytes = (length_bits == 0) ? 5'd0 : (length_bits >> 3);
        execution_insn = 32'b0;
        raw = {16'b0, parcel};
        fetch_cause = HALT_ILLEGAL;
      end
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)        pc <= RESET_PC;
    else if (halted)   pc <= pc;
    else if (redirect) pc <= redirect_target;
    else if (!stall)   pc <= pc + instruction_bytes;
  end

  always_comb begin
    if_id_next = '0;
    if_id_next.valid = 1'b1;
    if_id_next.pc = pc;
    if_id_next.raw_insn = raw;
    if_id_next.insn = ENABLE_C ? execution_insn : imem_rdata;
    if_id_next.ilen_bytes = instruction_bytes;
    if_id_next.cause = ENABLE_C ? fetch_cause : HALT_NONE;
  end
endmodule
