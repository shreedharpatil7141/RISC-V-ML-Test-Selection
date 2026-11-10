`timescale 1ns/1ps

module tb_rv_stage8_components;
  logic clk = 1'b0;
  logic rst_n = 1'b0;
  always #5 clk = ~clk;
  rv_s8_memory_if mem_bus(clk);
  logic [31:0] imem_addr=0, imem_addr_next=0, dmem_addr=0, dmem_wdata=0;
  logic dmem_re=0, dmem_atomic_commit=0;
  logic [3:0] dmem_we=0;
  integer oob_errors, store_writes, atomic_commits, atomic_writes;
  assign mem_bus.imem_addr=imem_addr;
  assign mem_bus.imem_addr_next=imem_addr_next;
  assign mem_bus.dmem_addr=dmem_addr;
  assign mem_bus.dmem_wdata=dmem_wdata;
  assign mem_bus.dmem_re=dmem_re;
  assign mem_bus.dmem_we=dmem_we;
  assign mem_bus.dmem_atomic_commit=dmem_atomic_commit;
  rv_s8_memory_driver memory(mem_bus,rst_n,oob_errors,store_writes,atomic_commits,atomic_writes);

  logic irq_msip, irq_mtip, irq_meip, irq_fired, irq_seen;
  logic [31:0] core_pc=32'h40;
  logic trap_taken=0, div_busy=0, div_start=0;
  rv_s8_interrupt_driver irq(clk,rst_n,1'b1,32'h40,3,0,0,core_pc,32'b0,32'b0,
                             1'b0,1'b0,1'b0,trap_taken,div_busy,div_start,
                             irq_msip,irq_mtip,irq_meip,irq_fired,irq_seen);

  rv_s8_observe_if obs(clk);
  integer retire_count, trap_count, csr_access_count, csr_commit_count;
  integer atomic_count, atomic_write_count, div_start_count, div_done_count, div_abort_count;
  rv_s8_retirement_monitor retire_mon(obs,retire_count);
  rv_s8_trap_monitor trap_mon(obs,trap_count);
  rv_s8_csr_monitor csr_mon(obs,csr_access_count,csr_commit_count);
  rv_s8_atomic_monitor atomic_mon(obs,atomic_count,atomic_write_count);
  rv_s8_divider_monitor divider_mon(obs,div_start_count,div_done_count,div_abort_count);

  initial begin
    obs.rst_n=0; obs.ret_valid=0; obs.ret_pc=0; obs.ret_raw=0; obs.ret_expanded=0; obs.ret_ilen=0;
    obs.trap_valid=0; obs.trap_pc=0; obs.trap_raw=0; obs.trap_cause=0; obs.trap_tval=0;
    obs.csr_access=0; obs.csr_commit=0; obs.csr_pc=0; obs.csr_raw=0; obs.csr_addr=0; obs.csr_old=0; obs.csr_new=0;
    obs.atomic_commit=0; obs.atomic_read=0; obs.atomic_write=0; obs.atomic_pc=0; obs.atomic_raw=0; obs.atomic_addr=0; obs.atomic_be=0;
    obs.md_start=0; obs.md_busy=0; obs.md_done=0; obs.md_abort=0; obs.md_pc=0; obs.md_raw=0;
    repeat(2) @(negedge clk); rst_n=1; obs.rst_n=1;
    if (mem_bus.imem_rdata !== 32'h00000013) $fatal(1,"STAGE8_UNIT image read mismatch");
    @(negedge clk); #1;
    if (!(irq_msip && irq_mtip && !irq_meip && irq_fired)) $fatal(1,"STAGE8_UNIT interrupt schedule mismatch");
    dmem_addr=32'h4000; dmem_wdata=32'h12345678; dmem_we=4'hf; @(posedge clk); #1; dmem_we=0;
    if (mem_bus.dmem_rdata !== 32'h12345678) $fatal(1,"STAGE8_UNIT memory write/read mismatch");
    dmem_addr=32'h4004; dmem_wdata=32'h89abcdef; dmem_re=1; dmem_we=4'hf; dmem_atomic_commit=1;
    @(posedge clk); #1; dmem_we=0; dmem_atomic_commit=0; dmem_re=0;
    if (mem_bus.dmem_rdata !== 32'h89abcdef) $fatal(1,"STAGE8_UNIT atomic memory effect mismatch");
    @(negedge clk); obs.ret_valid=1; obs.ret_pc=0; obs.ret_raw=32'h00000001;
    obs.ret_expanded=32'h00000013; obs.ret_ilen=2;
    obs.csr_access=1; obs.csr_commit=1; obs.csr_pc=0; obs.csr_raw=32'h00000001;
    obs.atomic_commit=1; obs.atomic_read=1; obs.atomic_write=1; obs.atomic_be=4'hf;
    obs.md_start=1; obs.md_pc=4; obs.md_raw=32'h0262c233;
    @(negedge clk); obs.ret_valid=1; obs.ret_pc=4; obs.ret_raw=32'h00100093;
    obs.ret_expanded=32'h00100093; obs.ret_ilen=4;
    obs.csr_access=0; obs.csr_commit=0; obs.atomic_commit=0; obs.md_start=0;
    @(negedge clk); obs.ret_valid=0; obs.trap_valid=1; obs.trap_pc=8; obs.trap_raw=32'h00000073; obs.md_done=1;
    @(negedge clk); obs.trap_valid=0; obs.md_done=0;
    obs.md_start=1; obs.md_pc=8;
    @(negedge clk); obs.md_start=0; obs.md_abort=1;
    @(negedge clk); obs.md_abort=0;
    #1;
    if (oob_errors != 0 || store_writes != 1 || atomic_commits != 1 || atomic_writes != 1)
      $fatal(1,"STAGE8_UNIT memory protocol counters mismatch");
    if (retire_count != 2 || trap_count != 1 || csr_access_count != 1 || csr_commit_count != 1 ||
        atomic_count != 1 || atomic_write_count != 1 || div_start_count != 2 || div_done_count != 1 || div_abort_count != 1)
      $fatal(1,"STAGE8_UNIT monitor counts mismatch");
    $display("STAGE8_COMPONENT_UNIT PASS memory=1 irq=1 retire=2 mixed_width=1 trap=1 csr=1 atomic=1 divider=1");
    $finish;
  end
endmodule

module tb_rv_stage8_bad_retire;
  logic clk=0;
  always #5 clk=~clk;
  rv_s8_observe_if obs(clk);
  integer event_count, bad_kind;
  rv_s8_retirement_monitor monitor(obs,event_count);
  initial begin
    obs.rst_n=0; obs.ret_valid=0; obs.ret_pc=32'h20; obs.ret_raw=0; obs.ret_expanded=32'h00000013; obs.ret_ilen=0;
    if (!$value$plusargs("BAD_RETIRE_KIND=%d",bad_kind)) $fatal(1,"STAGE8_NEGATIVE missing BAD_RETIRE_KIND");
    repeat(2) @(negedge clk); obs.rst_n=1;
    @(negedge clk);
    obs.ret_valid=1;
    case (bad_kind)
      1: begin obs.ret_ilen=3; obs.ret_raw=32'h00000001; end
      2: begin obs.ret_ilen=2; obs.ret_raw=32'h00000003; end
      3: begin obs.ret_ilen=2; obs.ret_raw=32'h00010001; end
      4: begin obs.ret_ilen=4; obs.ret_raw=32'h00000001; end
      default: $fatal(1,"STAGE8_NEGATIVE unsupported BAD_RETIRE_KIND=%0d",bad_kind);
    endcase
    @(negedge clk); $display("STAGE8_NEGATIVE_CHECK FAILED_TO_REJECT kind=%0d",bad_kind); $finish;
  end
endmodule

module tb_rv_stage8_bad_csr;
  logic clk=0;
  always #5 clk=~clk;
  rv_s8_observe_if obs(clk);
  integer access_count, commit_count;
  rv_s8_csr_monitor monitor(obs,access_count,commit_count);
  initial begin
    obs.rst_n=0; obs.ret_valid=0; obs.ret_pc=0; obs.ret_raw=0;
    obs.csr_access=0; obs.csr_commit=0; obs.csr_pc=0; obs.csr_raw=0;
    repeat(2) @(negedge clk); obs.rst_n=1; obs.csr_commit=1; obs.csr_pc=32'h20; obs.csr_raw=32'h30509073;
    @(negedge clk); $display("STAGE8_NEGATIVE_CHECK FAILED_TO_REJECT"); $finish;
  end
endmodule
