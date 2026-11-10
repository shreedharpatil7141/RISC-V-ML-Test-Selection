`timescale 1ns/1ps

package rv_stage8_pkg;
  parameter integer RV_S8_MEM_BYTES = 65536;
  parameter integer RV_S8_MAX_SCENARIOS = 16;
  parameter logic [31:0] RV_S8_SEED_DEFAULT = 32'h8a71_0008;
  typedef struct packed {
    logic valid;
    logic [31:0] pc;
    logic [31:0] raw;
    logic [4:0] ilen;
  } rv_s8_retirement_t;
  typedef struct packed {
    logic valid;
    logic [31:0] pc;
    logic [31:0] raw;
    logic [31:0] cause;
    logic [31:0] tval;
  } rv_s8_trap_t;
endpackage

interface rv_s8_memory_if(input logic clk);
  import rv_stage8_pkg::*;
  logic [31:0] imem_addr, imem_addr_next, imem_rdata, imem_rdata_next;
  logic imem_valid, imem_next_valid;
  logic [31:0] dmem_addr, dmem_wdata, dmem_rdata;
  logic dmem_re, dmem_valid, dmem_atomic_commit;
  logic [3:0] dmem_we;
  logic [31:0] words [0:(RV_S8_MEM_BYTES/4)-1];
endinterface

interface rv_s8_observe_if(input logic clk);
  logic rst_n;
  logic ret_valid;
  logic [31:0] ret_pc, ret_raw, ret_expanded;
  logic [4:0] ret_ilen;
  logic trap_valid;
  logic [31:0] trap_pc, trap_raw, trap_cause, trap_tval;
  logic csr_access, csr_commit;
  logic [31:0] csr_pc, csr_raw;
  logic [11:0] csr_addr;
  logic [31:0] csr_old, csr_new;
  logic atomic_commit, atomic_read, atomic_write;
  logic [31:0] atomic_pc, atomic_raw, atomic_addr;
  logic [3:0] atomic_be;
  logic md_start, md_busy, md_done, md_abort;
  logic [31:0] md_pc, md_raw;
endinterface

module rv_s8_memory_driver(
  rv_s8_memory_if bus,
  input logic rst_n,
  output integer oob_errors,
  output integer store_writes,
  output integer atomic_commits,
  output integer atomic_writes
);
  import rv_stage8_pkg::*;
  string image_path;
  wire imem_oob = (bus.imem_addr[31:16] != 16'h0);
  wire imem_next_oob = (bus.imem_addr_next[31:16] != 16'h0);
  wire dmem_oob = (bus.dmem_addr[31:16] != 16'h0);
  assign bus.imem_valid = !imem_oob;
  assign bus.imem_next_valid = !imem_next_oob;
  assign bus.imem_rdata = imem_oob ? 32'b0 : bus.words[bus.imem_addr[15:2]];
  assign bus.imem_rdata_next = imem_next_oob ? 32'b0 : bus.words[bus.imem_addr_next[15:2]];
  assign bus.dmem_valid = !dmem_oob;
  assign bus.dmem_rdata = dmem_oob ? 32'b0 : bus.words[bus.dmem_addr[15:2]];

  initial begin
    oob_errors = 0;
    store_writes = 0;
    atomic_commits = 0;
    atomic_writes = 0;
    for (integer i = 0; i < RV_S8_MEM_BYTES/4; i++) bus.words[i] = 32'b0;
    if (!$value$plusargs("HEX=%s", image_path))
      $fatal(1, "STAGE8_MEMORY missing +HEX image");
    $readmemh(image_path, bus.words);
  end

  always @(posedge bus.clk) begin
    if (rst_n) begin
      if ((bus.dmem_re || (|bus.dmem_we)) && dmem_oob) oob_errors = oob_errors + 1;
      if (bus.dmem_atomic_commit) begin
        atomic_commits = atomic_commits + 1;
        if (!bus.dmem_re || !bus.dmem_valid || ((|bus.dmem_we) && bus.dmem_we != 4'b1111))
          oob_errors = oob_errors + 1;
        if (|bus.dmem_we) atomic_writes = atomic_writes + 1;
      end
      if (bus.dmem_re && (|bus.dmem_we) && !bus.dmem_atomic_commit)
        oob_errors = oob_errors + 1;
      if ((|bus.dmem_we) && !dmem_oob) begin
        if (!bus.dmem_atomic_commit) store_writes = store_writes + 1;
        if (bus.dmem_we[0]) bus.words[bus.dmem_addr[15:2]][7:0] <= bus.dmem_wdata[7:0];
        if (bus.dmem_we[1]) bus.words[bus.dmem_addr[15:2]][15:8] <= bus.dmem_wdata[15:8];
        if (bus.dmem_we[2]) bus.words[bus.dmem_addr[15:2]][23:16] <= bus.dmem_wdata[23:16];
        if (bus.dmem_we[3]) bus.words[bus.dmem_addr[15:2]][31:24] <= bus.dmem_wdata[31:24];
      end
    end
  end
endmodule

module rv_s8_interrupt_driver(
  input logic clk, rst_n, enabled,
  input integer schedule_pc, input integer level_mask, input integer wait_div,
  input integer timing_mode,
  input logic [31:0] core_pc, if_pc, id_pc,
  input logic if_valid, id_valid, mie, trap_taken, div_busy, div_start,
  output logic irq_msip, irq_mtip, irq_meip,
  output logic fired, seen
);
  always @(posedge clk) begin
    if (!rst_n) seen <= 1'b0;
    else if (enabled && trap_taken) seen <= 1'b1;
  end
  always @(negedge clk) begin
    if (!rst_n) begin
      irq_msip <= 1'b0; irq_mtip <= 1'b0; irq_meip <= 1'b0; fired <= 1'b0;
    end else if (enabled) begin
      if (seen) begin irq_msip <= 1'b0; irq_mtip <= 1'b0; irq_meip <= 1'b0; end
      else if (!fired && schedule_pc >= 0 &&
          ((timing_mode == 0 && core_pc == schedule_pc) ||
           (timing_mode == 1 && wait_div != 0 && id_valid && id_pc == schedule_pc && div_busy && !div_start) ||
           (timing_mode == 2 && wait_div == 0 && !mie && if_valid && if_pc == schedule_pc) ||
           (timing_mode == 2 && wait_div == 0 && id_valid && id_pc == schedule_pc))) begin
        irq_msip <= level_mask[0]; irq_mtip <= level_mask[1]; irq_meip <= level_mask[2]; fired <= 1'b1;
      end
    end
  end
endmodule

module rv_s8_retirement_monitor(rv_s8_observe_if obs, output integer event_count);
  always @(posedge obs.clk) begin
    if (!obs.rst_n) event_count <= 0;
    else if (obs.ret_valid) begin
      if (!(obs.ret_ilen inside {5'd2, 5'd4}))
        $fatal(1, "STAGE8_RETIRE invalid length pc=%08x len_bytes=%0d len_bits=%0d length_port_bits=5 raw_bits=32 canonical_bits=32 raw=%08x canonical=%08x",
               obs.ret_pc, obs.ret_ilen, int'(obs.ret_ilen)*8, obs.ret_raw, obs.ret_expanded);
      if (obs.ret_ilen == 5'd2 &&
          (obs.ret_raw[1:0] == 2'b11 || obs.ret_raw[31:16] != 16'b0 ||
           obs.ret_expanded[1:0] != 2'b11))
        $fatal(1, "STAGE8_RETIRE malformed 16-bit record pc=%08x len_bytes=%0d len_bits=%0d length_port_bits=5 raw_bits=32 canonical_bits=32 raw=%08x raw_low16=%04x raw_high16=%04x canonical=%08x",
               obs.ret_pc, obs.ret_ilen, int'(obs.ret_ilen)*8, obs.ret_raw,
               obs.ret_raw[15:0], obs.ret_raw[31:16], obs.ret_expanded);
      if (obs.ret_ilen == 5'd4 &&
          (obs.ret_raw[1:0] != 2'b11 || obs.ret_expanded[1:0] != 2'b11))
        $fatal(1, "STAGE8_RETIRE malformed 32-bit record pc=%08x len_bytes=%0d len_bits=%0d length_port_bits=5 raw_bits=32 canonical_bits=32 raw=%08x raw_low16=%04x raw_high16=%04x canonical=%08x",
               obs.ret_pc, obs.ret_ilen, int'(obs.ret_ilen)*8, obs.ret_raw,
               obs.ret_raw[15:0], obs.ret_raw[31:16], obs.ret_expanded);
      event_count <= event_count + 1;
    end
  end
endmodule

module rv_s8_trap_monitor(rv_s8_observe_if obs, output integer event_count);
  always @(posedge obs.clk) begin
    if (!obs.rst_n) event_count <= 0;
    else if (obs.trap_valid) begin
      if (obs.ret_valid && obs.ret_pc == obs.trap_pc)
        $fatal(1, "STAGE8_TRAP fault retired pc=%08x raw=%08x", obs.trap_pc, obs.trap_raw);
      event_count <= event_count + 1;
    end
  end
endmodule

module rv_s8_csr_monitor(rv_s8_observe_if obs, output integer access_count, output integer commit_count);
  always @(posedge obs.clk) begin
    if (!obs.rst_n) begin access_count <= 0; commit_count <= 0; end
    else begin
      if (obs.csr_access) access_count <= access_count + 1;
      if (obs.csr_commit) begin
        if (!obs.ret_valid || obs.csr_pc != obs.ret_pc || obs.csr_raw != obs.ret_raw)
          $fatal(1, "STAGE8_CSR unauthorized/misaligned commit pc=%08x raw=%08x", obs.csr_pc, obs.csr_raw);
        commit_count <= commit_count + 1;
      end
    end
  end
endmodule

module rv_s8_atomic_monitor(rv_s8_observe_if obs, output integer commit_count, output integer write_count);
  always @(posedge obs.clk) begin
    if (!obs.rst_n) begin commit_count <= 0; write_count <= 0; end
    else if (obs.atomic_commit) begin
      if (!obs.atomic_read || ((obs.atomic_write) && obs.atomic_be != 4'b1111) ||
          ((!obs.atomic_write) && (|obs.atomic_be)))
        $fatal(1, "STAGE8_ATOMIC malformed effect pc=%08x raw=%08x be=%x", obs.atomic_pc, obs.atomic_raw, obs.atomic_be);
      commit_count <= commit_count + 1;
      if (obs.atomic_write) write_count <= write_count + 1;
    end
  end
endmodule

module rv_s8_divider_monitor(rv_s8_observe_if obs, output integer start_count,
                             output integer done_count, output integer abort_count);
  logic active;
  always @(posedge obs.clk) begin
    if (!obs.rst_n) begin active <= 1'b0; start_count <= 0; done_count <= 0; abort_count <= 0; end
    else begin
      if (obs.md_start) begin
        if (active) $fatal(1, "STAGE8_DIV overlapping start pc=%08x", obs.md_pc);
        active <= 1'b1; start_count <= start_count + 1;
      end
      if (obs.md_abort) begin
        if (!active || obs.md_done) $fatal(1, "STAGE8_DIV invalid abort pc=%08x", obs.md_pc);
        active <= 1'b0; abort_count <= abort_count + 1;
      end else if (obs.md_done) begin
        if (!active) $fatal(1, "STAGE8_DIV completion without active operation pc=%08x", obs.md_pc);
        active <= 1'b0; done_count <= done_count + 1;
      end
    end
  end
endmodule
