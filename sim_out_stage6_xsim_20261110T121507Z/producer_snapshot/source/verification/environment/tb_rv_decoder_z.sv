`timescale 1ns/1ps
module tb_rv_decoder_z;
  import rv32_pkg::*;
  word_t insn;
  logic [6:0] opcode, funct7;
  reg_t rd, rs1, rs2;
  logic [2:0] funct3;
  logic illegal, is_ecall, is_ebreak, is_fence, is_m, is_a;
  int checks=0, errors=0;

  rv_decoder #(.ENABLE_Z(1'b1)) dut (
    .insn(insn), .opcode(opcode), .rd(rd), .rs1(rs1), .rs2(rs2), .funct3(funct3),
    .funct7(funct7), .illegal(illegal), .is_ecall(is_ecall), .is_ebreak(is_ebreak),
    .is_fence(is_fence), .is_m(is_m), .is_a(is_a)
  );

  task automatic check_decode(input word_t bits, input logic expected_illegal, input string label);
    insn=bits; #1; checks++;
    if (illegal !== expected_illegal) begin
      errors++; $display("Z_DECODER_DIFF %s insn=%08x illegal=%b expected=%b",label,bits,illegal,expected_illegal);
    end
  endtask

  initial begin
    check_decode(32'h8000_9073,1'b0,"CSRRW scratch");
    check_decode(32'h8000_A073,1'b0,"CSRRS scratch");
    check_decode(32'h8000_B073,1'b0,"CSRRC scratch");
    check_decode(32'h8000_D073,1'b0,"CSRRWI scratch");
    check_decode(32'h8000_E073,1'b0,"CSRRSI scratch");
    check_decode(32'h8000_F073,1'b0,"CSRRCI scratch");
    check_decode(32'hCC00_2073,1'b0,"CSRRS read-only x0");
    check_decode(32'hCC00_30F3,1'b0,"CSRRC read-only x0");
    check_decode(32'hCC00_61F3,1'b0,"CSRRSI read-only zimm0");
    check_decode(32'hCC00_71F3,1'b0,"CSRRCI read-only zimm0");
    check_decode(32'hCC00_1073,1'b1,"CSRRW read-only write despite rd=x0");
    check_decode(32'hCC00_5073,1'b1,"CSRRWI read-only write despite zimm0");
    check_decode(32'hCC02_A0F3,1'b1,"CSRRS nonzero rs1 read-only write");
    check_decode(32'hCC00_E0F3,1'b1,"CSRRSI nonzero zimm read-only write");
    check_decode(32'hC000_2073,1'b1,"unimplemented-standard-counter");
    check_decode(32'h3000_20F3,1'b1,"unimplemented-machine-csr");
    check_decode(32'h0000_100F,1'b0,"FENCE.I");
    check_decode(32'h0000_900F,1'b1,"malformed-FENCE.I");
    if (errors==0) $display("STAGE6_DECODER_UNIT PASS checks=%0d errors=0",checks);
    else $display("STAGE6_DECODER_UNIT FAIL checks=%0d errors=%0d",checks,errors);
    $finish;
  end
endmodule
