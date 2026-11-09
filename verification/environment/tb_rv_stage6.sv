`timescale 1ns/1ps
module tb_rv_core_stage6;
  tb_rv_core #(.ENABLE_A(1'b1), .ENABLE_Z(1'b1)) core();
endmodule

module tb_rv_pipe_stage6;
  tb_rv_pipe_stage4 #(.ENABLE_A(1'b1), .ENABLE_Z(1'b1)) pipe();
endmodule
