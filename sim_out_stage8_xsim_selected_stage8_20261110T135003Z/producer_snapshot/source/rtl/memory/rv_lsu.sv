`timescale 1ns/1ps
// rv_lsu.sv - Load/store alignment, byte enables, sign extension, misalign detect.
// Memory is little-endian, word-organised with byte enables.
module rv_lsu
  import rv32_pkg::*;
(
  input  logic [2:0] funct3,     // load: 000 LB 001 LH 010 LW 100 LBU 101 LHU; store: 000 SB 001 SH 010 SW
  input  logic       is_load,
  input  logic       is_store,
  input  word_t      addr,
  input  word_t      store_data, // rs2
  input  word_t      mem_rdata,  // raw word at addr[31:2]
  output logic [3:0] be,         // store byte enables (valid when is_store)
  output word_t      mem_wdata,  // lane-aligned store data
  output word_t      load_data,  // extended load result
  output logic       misaligned
);
  logic [1:0] size;  // 0 byte, 1 half, 2 word
  logic [4:0] shift;
  word_t      shifted;

  assign size  = funct3[1:0];
  assign shift = {addr[1:0], 3'b000};
  assign shifted = mem_rdata >> shift;

  always_comb begin
    misaligned = 1'b0;
    if (is_load || is_store) begin
      if (size == 2'd1) misaligned = addr[0];
      else if (size == 2'd2) misaligned = (addr[1:0] != 2'b00);
    end
  end

  always_comb begin
    be        = 4'b0000;
    mem_wdata = store_data;
    case (size)
      2'd0: begin
        mem_wdata = {4{store_data[7:0]}};
        be        = 4'b0001 << addr[1:0];
      end
      2'd1: begin
        mem_wdata = {2{store_data[15:0]}};
        be        = addr[1] ? 4'b1100 : 4'b0011;
      end
      default: begin
        mem_wdata = store_data;
        be        = 4'b1111;
      end
    endcase
  end

  always_comb begin
    case (funct3)
      3'b000:  load_data = {{24{shifted[7]}},  shifted[7:0]};   // LB
      3'b001:  load_data = {{16{shifted[15]}}, shifted[15:0]};  // LH
      3'b100:  load_data = {24'b0, shifted[7:0]};               // LBU
      3'b101:  load_data = {16'b0, shifted[15:0]};              // LHU
      default: load_data = mem_rdata;                           // LW
    endcase
  end
endmodule
