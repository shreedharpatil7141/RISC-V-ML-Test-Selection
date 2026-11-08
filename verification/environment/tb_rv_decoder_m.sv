`timescale 1ns/1ps
module tb_rv_decoder_m;
  import rv32_pkg::*;
  logic [31:0] insn;
  logic [6:0] opcode, funct7;
  logic [2:0] funct3;
  reg_t rd,rs1,rs2;
  logic illegal,ecall,ebreak,fence,is_m;
  int errors=0;
  rv_decoder dut(.insn(insn),.opcode(opcode),.rd(rd),.rs1(rs1),.rs2(rs2),.funct3(funct3),.funct7(funct7),.illegal(illegal),.is_ecall(ecall),.is_ebreak(ebreak),.is_fence(fence),.is_m(is_m));
  initial begin
    for (int f7=0; f7<128; f7++) for (int f3=0; f3<8; f3++) begin
      insn=(f7<<25)|(2<<20)|(1<<15)|(f3<<12)|(5<<7)|OPC_OP; #1;
      if (is_m !== (f7==1) || illegal !== !((f7==0)||(f7==1)||(f7==32 && (f3==0||f3==5)))) errors++;
    end
    $display("DECODER_M_RESULT: %s checks=1024 errors=%0d",errors==0?"PASS":"FAIL",errors);
    $finish;
  end
endmodule
