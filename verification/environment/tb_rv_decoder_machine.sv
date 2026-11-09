`timescale 1ns/1ps
module tb_rv_decoder_machine;
  import rv32_pkg::*;
  word_t insn;
  logic [6:0] opcode, funct7;
  reg_t rd, rs1, rs2;
  logic [2:0] funct3;
  logic illegal, is_ecall, is_ebreak, is_fence, is_m, is_a;
  int checks=0, errors=0;

  rv_decoder #(.ENABLE_Z(1'b1), .ENABLE_M(1'b1)) dut (
    .insn(insn), .opcode(opcode), .rd(rd), .rs1(rs1), .rs2(rs2), .funct3(funct3),
    .funct7(funct7), .illegal(illegal), .is_ecall(is_ecall), .is_ebreak(is_ebreak),
    .is_fence(is_fence), .is_m(is_m), .is_a(is_a)
  );

  task automatic check_decode(input word_t bits, input logic expected_illegal, input string label);
    insn=bits; #1; checks++;
    if (illegal !== expected_illegal) begin
      errors++; $display("M_DECODER_DIFF %s insn=%08x illegal=%b expected=%b",label,bits,illegal,expected_illegal);
    end
  endtask

  initial begin
    check_decode(32'h3020_0073,1'b0,"MRET");
    check_decode(32'h3000_2073,1'b0,"mstatus-read");
    check_decode(32'h3010_20f3,1'b0,"misa-read");
    check_decode(32'h3010_1073,1'b1,"misa-CSRRW");
    check_decode(32'h3010_2073,1'b0,"misa-CSRRS-x0");
    check_decode(32'h3010_a073,1'b1,"misa-CSRRS-nonzero-zero-value");
    check_decode(32'h3010_e0f3,1'b1,"misa-CSRRSI-nonzero-zimm");
    check_decode(32'h3440_2073,1'b0,"mip-read");
    check_decode(32'h3440_1073,1'b1,"mip-write");
    check_decode(32'h3440_6073,1'b0,"mip-CSRRSI-zimm0");
    check_decode(32'hcc00_2073,1'b0,"custom-ID-read-suppressed");
    check_decode(32'hcc00_1073,1'b1,"custom-ID-write");
    check_decode(32'hcc10_2073,1'b1,"unimplemented-CC1");
    check_decode(32'h1020_0073,1'b1,"SRET-out-of-scope");
    check_decode(32'h1050_0073,1'b1,"WFI-out-of-scope");
    if (errors==0) $display("STAGE7_DECODER_UNIT PASS checks=%0d errors=0",checks);
    else $display("STAGE7_DECODER_UNIT FAIL checks=%0d errors=%0d",checks,errors);
    $finish;
  end
endmodule
