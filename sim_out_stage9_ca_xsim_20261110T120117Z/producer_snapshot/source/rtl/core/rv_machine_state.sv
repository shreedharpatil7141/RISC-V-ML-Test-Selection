`timescale 1ns/1ps
// M-mode architectural CSR bank. CSR writes are accepted only from an
// authorized retirement point; traps and MRET have priority over CSR writes.
module rv_machine_state
  import rv32_pkg::*;
#(
  parameter bit ENABLE_A = 1'b0,
  parameter bit ENABLE_C = 1'b0
)(
  input logic clk, rst_n,
  input logic [11:0] raddr,
  input logic [2:0] irq_levels,
  output word_t rdata,
  output logic irq_pending,
  output logic [4:0] irq_cause,
  input logic csr_we,
  input logic [11:0] csr_waddr,
  input word_t csr_wdata,
  input logic retired,
  input logic trap_enter,
  input logic trap_interrupt,
  input word_t trap_pc,
  input logic [4:0] trap_cause,
  input word_t trap_value,
  input logic mret,
  output word_t mepc_value,
  output word_t trap_target,
  output word_t mret_target,
  output logic mstatus_mie
);
  localparam word_t CUSTOM_ID = 32'h5354_4736;
  localparam word_t MISA_VALUE = 32'h4000_1100 | (ENABLE_A ? 32'h1 : 0) | (ENABLE_C ? 32'h4 : 0);
  word_t mstatus, mie, mtvec, mepc, mcause, mtval, mscratch;
  word_t mcycle, mcycleh, minstret, minstreth, scratch0, scratch1;
  word_t pending;

  always_comb begin
    pending = {20'b0, irq_levels[2], 3'b0, irq_levels[1], 3'b0, irq_levels[0], 3'b0};
    irq_pending = 1'b0;
    irq_cause = 5'd0;
    if (mstatus[3]) begin
      if (mie[11] && pending[11]) begin irq_pending = 1'b1; irq_cause = 5'd11; end
      else if (mie[3] && pending[3]) begin irq_pending = 1'b1; irq_cause = 5'd3; end
      else if (mie[7] && pending[7]) begin irq_pending = 1'b1; irq_cause = 5'd7; end
    end
    rdata = 32'b0;
    case (raddr)
      12'h300: rdata = mstatus;
      12'h301: rdata = MISA_VALUE;
      12'h304: rdata = mie;
      12'h305: rdata = mtvec;
      12'h340: rdata = mscratch;
      12'h341: rdata = mepc;
      12'h342: rdata = mcause;
      12'h343: rdata = mtval;
      12'h344: rdata = pending;
      12'hB00: rdata = mcycle;
      12'hB80: rdata = mcycleh;
      12'hB02: rdata = minstret;
      12'hB82: rdata = minstreth;
      12'h800: rdata = scratch0;
      12'h801: rdata = scratch1;
      12'hCC0: rdata = CUSTOM_ID;
      default: rdata = 32'b0;
    endcase
  end
  assign mepc_value = mepc;
  assign mstatus_mie = mstatus[3];
  assign trap_target = (mtvec & 32'hffff_fffc) |
                       ((trap_interrupt && mtvec[1:0] == 2'b01) ? {25'b0,trap_cause,2'b00} : 32'b0);
  assign mret_target = mepc & (ENABLE_C ? 32'hffff_fffe : 32'hffff_fffc);

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mstatus <= 32'h0000_1800; mie <= 0; mtvec <= 0; mepc <= 0;
      mcause <= 0; mtval <= 0; mscratch <= 0;
      mcycle <= 0; mcycleh <= 0; minstret <= 0; minstreth <= 0;
      scratch0 <= 0; scratch1 <= 0;
    end else begin
      if (csr_we && csr_waddr == 12'hB00) mcycle <= csr_wdata;
      else if (csr_we && csr_waddr == 12'hB80) mcycleh <= csr_wdata;
      else {mcycleh,mcycle} <= {mcycleh,mcycle} + 64'd1;
      if (csr_we && csr_waddr == 12'hB02) minstret <= csr_wdata;
      else if (csr_we && csr_waddr == 12'hB82) minstreth <= csr_wdata;
      else if (retired) {minstreth,minstret} <= {minstreth,minstret} + 64'd1;
      if (trap_enter) begin
        mstatus <= (32'h0000_1800 | (mstatus[3] ? 32'h80 : 0));
        mepc <= trap_pc & (ENABLE_C ? 32'hffff_fffe : 32'hffff_fffc);
        mcause <= {trap_interrupt,26'b0,trap_cause};
        mtval <= trap_value;
      end else if (mret) begin
        mstatus <= (32'h0000_1800 | (mstatus[7] ? 32'h8 : 0) | 32'h80);
      end else if (csr_we) begin
        case (csr_waddr)
          12'h300: mstatus <= 32'h0000_1800 | (csr_wdata & 32'h88);
          12'h304: mie <= csr_wdata & 32'h888;
          12'h305: mtvec <= {csr_wdata[31:2], (csr_wdata[1:0] <= 1 ? csr_wdata[1:0] : 2'b00)};
          12'h340: mscratch <= csr_wdata;
          12'h341: mepc <= csr_wdata & (ENABLE_C ? 32'hffff_fffe : 32'hffff_fffc);
          12'h342: mcause <= csr_wdata;
          12'h343: mtval <= csr_wdata;
          12'h800: scratch0 <= csr_wdata;
          12'h801: scratch1 <= csr_wdata;
          default: ;
        endcase
      end
    end
  end
endmodule
