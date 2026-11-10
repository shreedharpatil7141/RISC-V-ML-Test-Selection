`timescale 1ns/1ps

module tb_rv_core_stage8;
  tb_rv_core #(.ENABLE_A(1'b1), .ENABLE_Z(1'b1), .ENABLE_M(1'b1),
               .USE_STAGE8_IRQ_DRIVER(1'b1), .ENABLE_STAGE8_MONITORS(1'b1)) core();
endmodule

module tb_rv_pipe_stage8;
  tb_rv_pipe_stage4 #(.ENABLE_A(1'b1), .ENABLE_Z(1'b1), .ENABLE_M(1'b1),
                      .USE_STAGE8_IRQ_DRIVER(1'b1), .ENABLE_STAGE8_MONITORS(1'b1)) pipe();
endmodule
