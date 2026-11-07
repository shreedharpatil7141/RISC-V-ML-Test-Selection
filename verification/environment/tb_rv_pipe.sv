// tb_rv_pipe.sv - Stage 2 system testbench for rv_core_pipe (5-stage pipeline).
// Derived from tb_rv_core.sv (Stage 1, XSim-validated); same plusargs, memory model, trace format.
// Extra output lines: STATS (stalls/redirects/cycles) and COV (16 pipeline event counters).
// Plusargs: +HEX=<file> (required) +TRACE=<file> +EXPECT_CAUSE=<n> (default 1=ECALL)
//           +CHECK_GP=<0|1> (default 1: require x3==1 on ECALL) +TIMEOUT=<cycles>
// Unified 64 KiB memory, combinational read, synchronous byte-enable write.
// Prints exactly one "TEST_RESULT: PASS|FAIL ..." line. Trace format matches scripts/simulation/rv32i_iss.py.
`timescale 1ns/1ps
module tb_rv_pipe #(
  parameter bit USE_ITERATIVE_M = 1'b0
);
  import rv32_pkg::*;

  localparam int MEM_WORDS = 16384;   // 64 KiB

  logic clk = 1'b0;
  logic rst_n = 1'b0;
  always #5 clk = ~clk;

  word_t mem [0:MEM_WORDS-1];

  word_t imem_addr, imem_rdata, dmem_addr, dmem_wdata, dmem_rdata;
  logic dmem_re;
  logic [3:0] dmem_we;
  logic halted;
  halt_cause_e halt_cause;
  word_t halt_pc;
  logic ret_valid, ret_rd_we, ret_mem_re, ret_mem_we;
  word_t ret_pc, ret_insn, ret_rd_wdata, ret_mem_addr, ret_mem_wdata, ret_mem_rdata;
  reg_t ret_rd;
  logic [3:0] ret_mem_be;

  logic dbg_stall, dbg_redirect, dbg_assert_fail;
  logic [15:0] dbg_events;

  rv_core_pipe #(.USE_ITERATIVE_M(USE_ITERATIVE_M)) dut (
    .clk(clk), .rst_n(rst_n),
    .imem_addr(imem_addr), .imem_rdata(imem_rdata),
    .dmem_addr(dmem_addr), .dmem_re(dmem_re), .dmem_we(dmem_we), .dmem_wdata(dmem_wdata), .dmem_rdata(dmem_rdata),
    .halted(halted), .halt_cause(halt_cause), .halt_pc(halt_pc),
    .ret_valid(ret_valid), .ret_pc(ret_pc), .ret_insn(ret_insn),
    .ret_rd_we(ret_rd_we), .ret_rd(ret_rd), .ret_rd_wdata(ret_rd_wdata),
    .ret_mem_re(ret_mem_re), .ret_mem_we(ret_mem_we), .ret_mem_addr(ret_mem_addr),
    .ret_mem_be(ret_mem_be), .ret_mem_wdata(ret_mem_wdata), .ret_mem_rdata(ret_mem_rdata),
    .dbg_stall(dbg_stall), .dbg_redirect(dbg_redirect), .dbg_events(dbg_events), .dbg_assert_fail(dbg_assert_fail)
  );

  // ---------------- Memory model ----------------
  int oob_errors = 0;
  wire imem_oob = (imem_addr[31:16] != 16'h0);
  wire dmem_oob = (dmem_addr[31:16] != 16'h0);
  assign imem_rdata = imem_oob ? 32'h0 : mem[imem_addr[15:2]];
  assign dmem_rdata = dmem_oob ? 32'h0 : mem[dmem_addr[15:2]];

  always @(posedge clk) begin
    if (rst_n) begin
      if (!halted && imem_oob) oob_errors++;
      if ((dmem_re || (|dmem_we)) && dmem_oob) oob_errors++;
      if (|dmem_we && !dmem_oob) begin
        if (dmem_we[0]) mem[dmem_addr[15:2]][7:0]   <= dmem_wdata[7:0];
        if (dmem_we[1]) mem[dmem_addr[15:2]][15:8]  <= dmem_wdata[15:8];
        if (dmem_we[2]) mem[dmem_addr[15:2]][23:16] <= dmem_wdata[23:16];
        if (dmem_we[3]) mem[dmem_addr[15:2]][31:24] <= dmem_wdata[31:24];
      end
    end
  end

  // ---------------- Trace ----------------
  int trace_fd = 0;
  longint instret = 0;

  function automatic int be_size(input logic [3:0] be);
    case (be)
      4'b0001, 4'b0010, 4'b0100, 4'b1000: return 1;
      4'b0011, 4'b1100:                   return 2;
      4'b1111:                            return 4;
      default:                            return 0;
    endcase
  endfunction

  function automatic int be_lane(input logic [3:0] be);
    for (int i = 0; i < 4; i++) if (be[i]) return i;
    return 0;
  endfunction

  always @(posedge clk) begin
    if (rst_n && ret_valid) begin
      automatic int    st_n = 0;
      automatic word_t st_d = 32'h0;
      automatic word_t st_a = 32'h0;
      automatic word_t rdv  = 32'h0;
      automatic int    rdn  = 0;
      instret++;
      if (ret_mem_we) begin
        st_n = be_size(ret_mem_be);
        st_a = ret_mem_addr;
        st_d = ret_mem_wdata >> (8 * be_lane(ret_mem_be));
        if (st_n == 1) st_d = st_d & 32'hFF;
        else if (st_n == 2) st_d = st_d & 32'hFFFF;
      end
      if (ret_rd_we) begin rdn = int'(ret_rd); rdv = ret_rd_wdata; end
      if (trace_fd != 0)
        $fdisplay(trace_fd, "%08x %08x %02d %08x %0d %08x %08x", ret_pc, ret_insn, rdn, rdv, st_n, st_a, st_d);
    end
  end

  // ---------------- Pipeline statistics / event coverage ----------------
  longint stall_cnt = 0;
  longint redirect_cnt = 0;
  longint ev_cnt [0:15];

  initial begin
    for (int e = 0; e < 16; e++) ev_cnt[e] = 0;
  end

  always @(posedge clk) begin
    if (rst_n) begin
      if (dbg_stall)    stall_cnt++;
      if (dbg_redirect) redirect_cnt++;
      for (int e = 0; e < 16; e++)
        if (dbg_events[e]) ev_cnt[e]++;
    end
  end

  // ---------------- Main sequence ----------------
  string hex_file, trace_file;
  int    expect_cause = 1;
  int    check_gp = 1;
  int    timeout = 2000000;
  int    cycles = 0;
  bit    pass;
  word_t gp_val;

  initial begin
integer plusarg_ok;
    if (!$value$plusargs("HEX=%s", hex_file)) begin
      $display("TEST_RESULT: FAIL (+HEX not given)");
      $finish;
    end
   plusarg_ok = $value$plusargs("EXPECT_CAUSE=%d", expect_cause);
   plusarg_ok = $value$plusargs("CHECK_GP=%d", check_gp);
   plusarg_ok = $value$plusargs("TIMEOUT=%d", timeout);
    if ($value$plusargs("TRACE=%s", trace_file)) trace_fd = $fopen(trace_file, "w");

    for (int i = 0; i < MEM_WORDS; i++) mem[i] = 32'h0;
    $readmemh(hex_file, mem);

    repeat (3) @(posedge clk);
    @(negedge clk) rst_n = 1'b1;

    while (!halted && cycles < timeout) begin
      @(posedge clk);
      cycles++;
    end
    @(negedge clk);

    gp_val = dut.u_rf.regs[3];
    pass = halted && (int'(halt_cause) == expect_cause) && (oob_errors == 0);
    if (check_gp != 0 && expect_cause == int'(HALT_ECALL)) pass = pass && (gp_val == 32'h1);
    if (dbg_assert_fail) pass = 1'b0;

    if (trace_fd != 0) begin
      $fdisplay(trace_fd, "HALT %0d %08x", int'(halt_cause), halt_pc);
      for (int r = 1; r < 32; r++) $fdisplay(trace_fd, "REG %0d %08x", r, dut.u_rf.regs[r]);
      for (int a = 16'h4000; a < 16'h6000; a += 4)
        if (mem[a >> 2] != 32'h0) $fdisplay(trace_fd, "MEM %08x %08x", a, mem[a >> 2]);
      $fclose(trace_fd);
    end

    $display("STATS stalls=%0d redirects=%0d cycles=%0d instret=%0d assert_fail=%0d",
             stall_cnt, redirect_cnt, cycles, instret, dbg_assert_fail);
    $display("COV %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",
             ev_cnt[0], ev_cnt[1], ev_cnt[2], ev_cnt[3], ev_cnt[4], ev_cnt[5], ev_cnt[6], ev_cnt[7],
             ev_cnt[8], ev_cnt[9], ev_cnt[10], ev_cnt[11], ev_cnt[12], ev_cnt[13], ev_cnt[14], ev_cnt[15]);
    $display("TEST_RESULT: %s hex=%s cause=%0d expect=%0d gp=0x%0h instret=%0d cycles=%0d oob=%0d%s",
             pass ? "PASS" : "FAIL", hex_file, int'(halt_cause), expect_cause, gp_val, instret, cycles,
             oob_errors, halted ? "" : " TIMEOUT");
    $finish;
  end
endmodule
