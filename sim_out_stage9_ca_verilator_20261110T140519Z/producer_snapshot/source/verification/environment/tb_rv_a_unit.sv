`timescale 1ns/1ps
module tb_rv_a_unit;
  import rv32_pkg::*;
  logic [4:0] funct5;
  logic [31:0] old_word, source_word, new_word;
  logic [31:0] insn;
  logic [6:0] opcode, funct7;
  reg_t rd, rs1, rs2;
  logic [2:0] funct3;
  logic illegal, ecall, ebreak, fence, is_m, is_a;
  int errors=0, checks=0;
  rv_a_unit dut(.*);
  rv_decoder #(.ENABLE_A(1'b1)) decode_dut(
    .insn(insn), .opcode(opcode), .rd(rd), .rs1(rs1), .rs2(rs2), .funct3(funct3),
    .funct7(funct7), .illegal(illegal), .is_ecall(ecall), .is_ebreak(ebreak),
    .is_fence(fence), .is_m(is_m), .is_a(is_a));
  function automatic logic supported(input logic [4:0] f5);
    case(f5)
      5'b00010,5'b00011,5'b00001,5'b00000,5'b00100,5'b01100,5'b01000,
      5'b10000,5'b10100,5'b11000,5'b11100: return 1'b1;
      default: return 1'b0;
    endcase
  endfunction
  task automatic check(input logic [4:0] op, input logic [31:0] oldv,
                       input logic [31:0] src, input logic [31:0] expected);
    begin
      funct5=op; old_word=oldv; source_word=src; #1; checks++;
      if (new_word !== expected) begin
        errors++; $display("A_UNIT_DIFF op=%02x old=%08x src=%08x expected=%08x actual=%08x",op,oldv,src,expected,new_word);
      end
    end
  endtask
  initial begin
    int legality_checks, legality_legal;
    legality_checks=0; legality_legal=0;
    for (int f5=0; f5<32; f5++) for (int f3=0; f3<8; f3++)
      for (int r2=0; r2<2; r2++) for (int order=0; order<4; order++) begin
        logic expected_legal;
        insn=(f5<<27)|((order&1)<<26)|(((order>>1)&1)<<25)|(r2<<20)|
             (2<<15)|(f3<<12)|(1<<7)|7'h2f;
        expected_legal=(f3==2) && supported(f5) && ((f5!=2)||(r2==0));
        #1; legality_checks++;
        if (expected_legal) legality_legal++;
        if ((is_a !== expected_legal) || (illegal !== !expected_legal)) begin
          errors++; $display("A_LEGALITY_DIFF raw=%08x expected_legal=%0d actual_is_a=%0d illegal=%0d",insn,expected_legal,is_a,illegal);
        end
      end
    check(5'b00001,32'h80000000,32'h7fffffff,32'h7fffffff);
    check(5'b00000,32'h7fffffff,32'h1,32'h80000000);
    check(5'b00100,32'h80000000,32'h7fffffff,32'hffffffff);
    check(5'b01100,32'h80000000,32'h7fffffff,32'h00000000);
    check(5'b01000,32'h80000000,32'h7fffffff,32'hffffffff);
    check(5'b10000,32'h80000000,32'h7fffffff,32'h80000000);
    check(5'b10100,32'h80000000,32'h7fffffff,32'h7fffffff);
    check(5'b11000,32'h80000000,32'h7fffffff,32'h7fffffff);
    check(5'b11100,32'h80000000,32'h7fffffff,32'h80000000);
    if (legality_checks!=2048 || legality_legal!=84) begin errors++; $display("A_LEGALITY_TOTAL_DIFF checks=%0d legal=%0d",legality_checks,legality_legal); end
    if(errors) $fatal(1,"RV32A_UNIT FAIL checks=%0d legality_checks=%0d errors=%0d",checks,legality_checks,errors);
    $display("RV32A_LEGALITY_UNIT PASS checks=%0d legal=%0d errors=0",legality_checks,legality_legal);
    $display("RV32A_UNIT PASS checks=%0d errors=0",checks); $finish;
  end
endmodule
