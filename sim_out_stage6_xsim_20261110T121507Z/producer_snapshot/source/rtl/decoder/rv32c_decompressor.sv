`timescale 1ns/1ps
// Standalone RV32C v2.0 integer decompressor (Stage 4.2).
// This block does not fetch, execute, or retire instructions.
module rv32c_decompressor (
  input  logic [15:0] raw_halfword,
  output logic [31:0] expanded_insn,
  output logic [7:0]  length_bits,
  output logic        is_compressed,
  output logic        is_32bit_prefix,
  output logic        unsupported_length,
  output logic        illegal,
  output logic        hint
);
  function automatic logic [31:0] enc_i(
    input logic [31:0] imm,
    input logic [4:0] rs1,
    input logic [2:0] funct3,
    input logic [4:0] rd,
    input logic [6:0] opcode
  );
    enc_i = {imm[11:0], rs1, funct3, rd, opcode};
  endfunction

  function automatic logic [31:0] enc_r(
    input logic [6:0] funct7,
    input logic [4:0] rs2,
    input logic [4:0] rs1,
    input logic [2:0] funct3,
    input logic [4:0] rd
  );
    enc_r = {funct7, rs2, rs1, funct3, rd, 7'h33};
  endfunction

  function automatic logic [31:0] enc_s(input logic [31:0] imm,
    input logic [4:0] rs2, input logic [4:0] rs1);
    enc_s = {imm[11:5], rs2, rs1, 3'b010, imm[4:0], 7'h23};
  endfunction

  function automatic logic [31:0] enc_b(input logic [31:0] imm,
    input logic [4:0] rs2, input logic [4:0] rs1, input logic [2:0] funct3);
    enc_b = {imm[12], imm[10:5], rs2, rs1, funct3,
             imm[4:1], imm[11], 7'h63};
  endfunction

  function automatic logic [31:0] enc_j(input logic [31:0] imm,
    input logic [4:0] rd);
    enc_j = {imm[20], imm[10:1], imm[11], imm[19:12], rd, 7'h6f};
  endfunction

  logic [1:0] quadrant;
  logic [2:0] funct3;
  logic [4:0] rd, rs2;
  logic [4:0] rdp, rs1p, rs2p;
  logic [31:0] imm;
  logic [31:0] uimm;
  logic [1:0] caop;
  logic [2:0] nnn;

  always_comb begin
    expanded_insn = 32'b0;
    length_bits = 8'b0;
    is_compressed = 1'b0;
    is_32bit_prefix = 1'b0;
    unsupported_length = 1'b0;
    illegal = 1'b0;
    hint = 1'b0;
    quadrant = raw_halfword[1:0];
    funct3 = raw_halfword[15:13];
    rd = raw_halfword[11:7];
    rs2 = raw_halfword[6:2];
    rdp = {2'b01, raw_halfword[4:2]};
    rs1p = {2'b01, raw_halfword[9:7]};
    rs2p = {2'b01, raw_halfword[4:2]};
    imm = 32'b0;
    uimm = 32'b0;
    caop = raw_halfword[6:5];
    nnn = raw_halfword[14:12];

    // Instruction-length classification is independent of C legality.
    if (raw_halfword[1:0] != 2'b11) begin
      length_bits = 8'd16;
      is_compressed = 1'b1;
    end else if (raw_halfword[4:2] != 3'b111) begin
      length_bits = 8'd32;
      is_32bit_prefix = 1'b1;
    end else if (raw_halfword[5:0] == 6'b011111) begin
      length_bits = 8'd48;
      unsupported_length = 1'b1;
    end else if (raw_halfword[6:0] == 7'b0111111) begin
      length_bits = 8'd64;
      unsupported_length = 1'b1;
    end else if (raw_halfword[6:0] == 7'b1111111) begin
      if (nnn == 3'b111) begin
        length_bits = 8'd0; // reserved prefix: length >=192 is not exact here
      end else begin
        length_bits = 8'd80 + {1'b0, nnn, 4'b0000};
      end
      unsupported_length = 1'b1;
    end else begin
      length_bits = 8'd0;
      unsupported_length = 1'b1;
    end

    if (is_compressed) begin
      illegal = 1'b0;
      hint = 1'b0;
      case (quadrant)
        2'b00: begin
          case (funct3)
            3'b000: begin // C.ADDI4SPN
              uimm = {22'b0, raw_halfword[10:7], raw_halfword[12:11],
                      raw_halfword[5], raw_halfword[6], 2'b00};
              if (uimm == 0) illegal = 1'b1;
              else expanded_insn = enc_i(uimm, 5'd2, 3'b000, rdp, 7'h13);
            end
            3'b010, 3'b110: begin // C.LW/C.SW
              uimm = {25'b0, raw_halfword[5], raw_halfword[12:10],
                      raw_halfword[6], 2'b00};
              if (funct3 == 3'b010)
                expanded_insn = enc_i(uimm, rs1p, 3'b010, rdp, 7'h03);
              else
                expanded_insn = enc_s(uimm, rs2p, rs1p);
            end
            default: illegal = 1'b1; // FP, RV64-only, reserved
          endcase
        end
        2'b01: begin
          case (funct3)
            3'b000: begin // C.ADDI / C.NOP / HINT
              imm = {{26{raw_halfword[12]}}, raw_halfword[12], raw_halfword[6:2]};
              if (rd == 0) begin
                if (imm == 0) expanded_insn = 32'h00000013;
                else begin hint = 1'b1; expanded_insn = 32'h00000013; end
              end else if (imm == 0) begin
                hint = 1'b1; expanded_insn = 32'h00000013;
              end else expanded_insn = enc_i(imm, rd, 3'b000, rd, 7'h13);
            end
            3'b001, 3'b101: begin // C.JAL (RV32) / C.J
              imm = {{20{raw_halfword[12]}}, raw_halfword[12], raw_halfword[8],
                     raw_halfword[10:9], raw_halfword[6], raw_halfword[7],
                     raw_halfword[2], raw_halfword[11], raw_halfword[5:3],
                     1'b0};
              expanded_insn = enc_j(imm, funct3 == 3'b001 ? 5'd1 : 5'd0);
            end
            3'b010: begin // C.LI
              imm = {{26{raw_halfword[12]}}, raw_halfword[12], raw_halfword[6:2]};
              if (rd == 0) begin hint = 1'b1; expanded_insn = 32'h00000013; end
              else expanded_insn = enc_i(imm, 5'd0, 3'b000, rd, 7'h13);
            end
            3'b011: begin
              if (rd == 2) begin // C.ADDI16SP
                imm = {{22{raw_halfword[12]}}, raw_halfword[12], raw_halfword[4:3],
                       raw_halfword[5], raw_halfword[2], raw_halfword[6], 4'b0000};
                if (imm == 0) illegal = 1'b1;
                else expanded_insn = enc_i(imm, 5'd2, 3'b000, 5'd2, 7'h13);
              end else begin // C.LUI
                imm = {{14{raw_halfword[12]}}, raw_halfword[12], raw_halfword[6:2], 12'b0};
                if ({raw_halfword[12], raw_halfword[6:2]} == 0) illegal = 1'b1;
                else if (rd == 0) begin hint = 1'b1; expanded_insn = 32'h00000013; end
                else expanded_insn = {imm[31:12], rd, 7'h37};
              end
            end
            3'b100: begin
              case (raw_halfword[11:10])
                2'b00, 2'b01: begin // C.SRLI/C.SRAI, RV32 shamt[5] custom
                  if (raw_halfword[12]) illegal = 1'b1;
                  else if (raw_halfword[6:2] == 0) begin
                    hint = 1'b1; expanded_insn = 32'h00000013;
                  end else begin
                    imm = {21'b0, (raw_halfword[11:10] == 2'b01), 5'b0,
                           raw_halfword[6:2]};
                    expanded_insn = enc_i(imm, rs1p, 3'b101, rs1p, 7'h13);
                  end
                end
                2'b10: begin // C.ANDI
                  imm = {{26{raw_halfword[12]}}, raw_halfword[12], raw_halfword[6:2]};
                  expanded_insn = enc_i(imm, rs1p, 3'b111, rs1p, 7'h13);
                end
                2'b11: begin // C.SUB/XOR/OR/AND; RV64 slots unsupported
                  if (raw_halfword[12]) illegal = 1'b1;
                  else begin
                    case (caop)
                      2'b00: expanded_insn = enc_r(7'h20, rs2p, rs1p, 3'b000, rs1p);
                      2'b01: expanded_insn = enc_r(7'h00, rs2p, rs1p, 3'b100, rs1p);
                      2'b10: expanded_insn = enc_r(7'h00, rs2p, rs1p, 3'b110, rs1p);
                      2'b11: expanded_insn = enc_r(7'h00, rs2p, rs1p, 3'b111, rs1p);
                    endcase
                  end
                end
              endcase
            end
            3'b110, 3'b111: begin // C.BEQZ/C.BNEZ
              imm = {{23{raw_halfword[12]}}, raw_halfword[12], raw_halfword[6:5],
                     raw_halfword[2], raw_halfword[11:10], raw_halfword[4:3], 1'b0};
              expanded_insn = enc_b(imm, 5'd0, rs1p,
                                    funct3 == 3'b110 ? 3'b000 : 3'b001);
            end
            default: illegal = 1'b1;
          endcase
        end
        2'b10: begin
          case (funct3)
            3'b000: begin // C.SLLI
              if (raw_halfword[12]) illegal = 1'b1;
              else if (rd == 0 || raw_halfword[6:2] == 0) begin
                hint = 1'b1; expanded_insn = 32'h00000013;
              end else begin
                imm = {27'b0, raw_halfword[6:2]};
                expanded_insn = enc_i(imm, rd, 3'b001, rd, 7'h13);
              end
            end
            3'b010: begin // C.LWSP
              uimm = {24'b0, raw_halfword[3:2], raw_halfword[12],
                      raw_halfword[6:4], 2'b00};
              if (rd == 0) illegal = 1'b1;
              else expanded_insn = enc_i(uimm, 5'd2, 3'b010, rd, 7'h03);
            end
            3'b100: begin // C.JR/MV/EBREAK/JALR/ADD
              if (!raw_halfword[12] && rs2 == 0) begin
                if (rd == 0) illegal = 1'b1;
                else expanded_insn = enc_i(32'b0, rd, 3'b000, 5'd0, 7'h67);
              end else if (!raw_halfword[12] && rs2 != 0) begin
                if (rd == 0) begin hint = 1'b1; expanded_insn = 32'h00000013; end
                else expanded_insn = enc_r(7'h00, rs2, 5'd0, 3'b000, rd);
              end else if (raw_halfword[12] && rs2 == 0 && rd == 0) begin
                expanded_insn = 32'h00100073;
              end else if (raw_halfword[12] && rs2 == 0) begin
                expanded_insn = enc_i(32'b0, rd, 3'b000, 5'd1, 7'h67);
              end else if (rd == 0) begin
                hint = 1'b1; expanded_insn = 32'h00000013;
              end else expanded_insn = enc_r(7'h00, rs2, rd, 3'b000, rd);
            end
            3'b110: begin // C.SWSP
              uimm = {24'b0, raw_halfword[8:7], raw_halfword[12:9], 2'b00};
              expanded_insn = enc_s(uimm, rs2, 5'd2);
            end
            default: illegal = 1'b1; // floating point / RV64-only
          endcase
        end
        default: illegal = 1'b1;
      endcase
      if (illegal) begin
        expanded_insn = 32'b0;
        hint = 1'b0;
      end
    end else if (unsupported_length) begin
      // No expanded instruction for a prefix requiring >32 bits.
      expanded_insn = 32'b0;
    end else begin
      // A 32-bit prefix is classified here; the following parcel supplies
      // the full instruction outside this standalone halfword interface.
      expanded_insn = 32'b0;
    end
  end
endmodule
