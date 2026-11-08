// tb_rv_pipe_stage4.sv - Stage 3.4 system testbench for iterative M pipeline.
// Derived from tb_rv_core.sv (Stage 1, XSim-validated); same plusargs, memory model, trace format.
// Extra output lines: STATS (stalls/redirects/cycles) and COV (16 pipeline event counters).
// Plusargs: +HEX=<file> (required) +TRACE=<file> +EXPECT_CAUSE=<n> (default 1=ECALL)
//           +CHECK_GP=<0|1> (default 1: require x3==1 on ECALL) +TIMEOUT=<cycles>
// Unified 64 KiB memory, combinational read, synchronous byte-enable write.
// Prints exactly one "TEST_RESULT: PASS|FAIL ..." line. Trace format matches scripts/simulation/rv32i_iss.py.
`timescale 1ns/1ps
module tb_rv_pipe_stage4 #(
  parameter bit USE_ITERATIVE_M = 1'b1,
  parameter bit ENABLE_C = 1'b0
);
  import rv32_pkg::*;

  localparam int MEM_WORDS = 16384;   // 64 KiB

  logic clk = 1'b0;
  logic rst_n = 1'b0;
  always #5 clk = ~clk;

  word_t mem [0:MEM_WORDS-1];

  word_t imem_addr, imem_addr_next, imem_rdata, imem_rdata_next, dmem_addr, dmem_wdata, dmem_rdata;
  logic imem_valid, imem_next_valid;
  logic dmem_re, dmem_valid;
  logic [3:0] dmem_we;
  logic halted;
  halt_cause_e halt_cause;
  word_t halt_pc;
  logic ret_valid, ret_rd_we, ret_mem_re, ret_mem_we;
  word_t ret_pc, ret_insn, ret_expanded_insn, ret_rd_wdata, ret_mem_addr, ret_mem_wdata, ret_mem_rdata;
  logic [4:0] ret_ilen_bytes, halt_ilen_bytes;
  word_t halt_raw_insn;
  reg_t ret_rd;
  logic [3:0] ret_mem_be;

  logic dbg_stall, dbg_redirect, dbg_assert_fail;
  logic dbg_md_start, dbg_md_busy, dbg_md_done, dbg_md_abort_started;
  logic dbg_m_issue, dbg_m_complete, dbg_m_squash_redirect, dbg_m_fault_start_suppressed;
  logic [31:0] dbg_m_pc, dbg_m_insn, dbg_m_operand_a, dbg_m_operand_b;
  logic [1:0] dbg_m_fwd_a, dbg_m_fwd_b, dbg_m_squash_fault, dbg_m_loaduse;
  logic [15:0] dbg_events;
  longint md_starts=0, md_dones=0, busy_cycles=0, md_aborts_started=0;

  rv_core_pipe #(.USE_ITERATIVE_M(USE_ITERATIVE_M), .ENABLE_C(ENABLE_C)) dut (
    .clk(clk), .rst_n(rst_n),
    .imem_addr(imem_addr), .imem_addr_next(imem_addr_next), .imem_rdata(imem_rdata),
    .imem_valid(imem_valid), .imem_rdata_next(imem_rdata_next), .imem_next_valid(imem_next_valid),
    .dmem_addr(dmem_addr), .dmem_re(dmem_re), .dmem_we(dmem_we), .dmem_wdata(dmem_wdata), .dmem_rdata(dmem_rdata), .dmem_valid(dmem_valid),
    .halted(halted), .halt_cause(halt_cause), .halt_pc(halt_pc),
    .halt_raw_insn(halt_raw_insn), .halt_ilen_bytes(halt_ilen_bytes),
    .ret_valid(ret_valid), .ret_pc(ret_pc), .ret_insn(ret_insn),
    .ret_expanded_insn(ret_expanded_insn), .ret_ilen_bytes(ret_ilen_bytes),
    .ret_rd_we(ret_rd_we), .ret_rd(ret_rd), .ret_rd_wdata(ret_rd_wdata),
    .ret_mem_re(ret_mem_re), .ret_mem_we(ret_mem_we), .ret_mem_addr(ret_mem_addr),
    .ret_mem_be(ret_mem_be), .ret_mem_wdata(ret_mem_wdata), .ret_mem_rdata(ret_mem_rdata),
    .dbg_stall(dbg_stall), .dbg_redirect(dbg_redirect), .dbg_events(dbg_events), .dbg_assert_fail(dbg_assert_fail),
    .dbg_md_start(dbg_md_start), .dbg_md_busy(dbg_md_busy), .dbg_md_done(dbg_md_done),
    .dbg_md_abort_started(dbg_md_abort_started),
    .dbg_m_issue(dbg_m_issue), .dbg_m_complete(dbg_m_complete),
    .dbg_m_pc(dbg_m_pc), .dbg_m_insn(dbg_m_insn),
    .dbg_m_operand_a(dbg_m_operand_a), .dbg_m_operand_b(dbg_m_operand_b),
    .dbg_m_fwd_a(dbg_m_fwd_a), .dbg_m_fwd_b(dbg_m_fwd_b),
    .dbg_m_squash_redirect(dbg_m_squash_redirect), .dbg_m_squash_fault(dbg_m_squash_fault),
    .dbg_m_fault_start_suppressed(dbg_m_fault_start_suppressed), .dbg_m_loaduse(dbg_m_loaduse)
  );

  // ---------------- Memory model ----------------
  int oob_errors = 0;
  wire imem_oob = (imem_addr[31:16] != 16'h0);
  wire dmem_oob = (dmem_addr[31:16] != 16'h0);
  assign imem_rdata = imem_oob ? 32'h0 : mem[imem_addr[15:2]];
  assign imem_valid = !imem_oob;
  assign imem_rdata_next = (imem_addr_next[31:16] != 16'h0) ? 32'h0 : mem[imem_addr_next[15:2]];
  assign imem_next_valid = (imem_addr_next[31:16] == 16'h0);
  assign dmem_rdata = dmem_oob ? 32'h0 : mem[dmem_addr[15:2]];
  assign dmem_valid = !dmem_oob;

  always @(posedge clk) begin
    if (rst_n) begin
      if (!ENABLE_C && !halted && imem_oob) oob_errors++;
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
      if (trace_fd != 0) begin
        if (ENABLE_C)
          $fdisplay(trace_fd, "I %08x %08x %02d %08x %02d %08x %0d %08x %08x", ret_pc,
                    ret_insn, ret_ilen_bytes, ret_expanded_insn, rdn, rdv, st_n, st_a, st_d);
        else
          $fdisplay(trace_fd, "%08x %08x %02d %08x %0d %08x %08x", ret_pc, ret_insn, rdn, rdv, st_n, st_a, st_d);
      end
    end
  end

  // ---------------- Pipeline statistics / event coverage ----------------
  longint stall_cnt = 0;
  longint redirect_cnt = 0;
  longint ev_cnt [0:15];
  integer mcov_fd = 0;
  integer mcov_error = 0;
  string mcov_file;
  logic previous_md_done = 1'b0;

  initial begin
    for (int e = 0; e < 16; e++) ev_cnt[e] = 0;
  end

  always @(posedge clk) begin
    if (rst_n) begin
      if (dbg_md_start) md_starts++;
      if (dbg_md_done) md_dones++;
      if (dbg_md_busy) busy_cycles++;
      if (dbg_md_abort_started) md_aborts_started++;
      if (dbg_stall)    stall_cnt++;
      if (dbg_redirect) redirect_cnt++;
      for (int e = 0; e < 16; e++)
        if (dbg_events[e]) ev_cnt[e]++;
    end
  end

  // Optional Stage 3.5 side channel. Architectural TRACE rows above remain
  // unchanged; these records distinguish EX issue/completion, WB retirement,
  // and instructions removed by redirect/fault before issue.
  always @(posedge clk) begin
    if (rst_n && mcov_fd != 0) begin
      if (dbg_m_issue)
        $fdisplay(mcov_fd, "M %08x %08x %08x %08x %0d %0d", dbg_m_pc, dbg_m_insn,
                  dbg_m_operand_a, dbg_m_operand_b, dbg_m_fwd_a, dbg_m_fwd_b);
      if (dbg_m_issue) $fdisplay(mcov_fd, "EV ISSUE %08x %08x", dbg_m_pc, dbg_m_insn);
      if (dbg_m_complete) $fdisplay(mcov_fd, "EV COMPLETE %08x %08x", dbg_m_pc, dbg_m_insn);
      if (ret_valid && ret_insn[6:0] == 7'h33 && ret_insn[31:25] == 7'h01)
        $fdisplay(mcov_fd, "EV RETIRE %08x %08x", ret_pc, ret_insn);
      if (dbg_m_squash_redirect)
        $fdisplay(mcov_fd, "EV SQUASH_REDIRECT %08x %08x", dut.if_id.pc, dut.if_id.insn);
      if (dbg_m_squash_fault[0])
        $fdisplay(mcov_fd, "EV SQUASH_FAULT_IDEX %08x %08x", dut.id_ex.pc, dut.id_ex.insn);
      if (dbg_m_squash_fault[1])
        $fdisplay(mcov_fd, "EV SQUASH_FAULT_IFID %08x %08x", dut.if_id.pc, dut.if_id.insn);
      if (dbg_m_fault_start_suppressed)
        $fdisplay(mcov_fd, "EV FAULT_DIV_SUPPRESS %08x %08x", dbg_m_pc, dbg_m_insn);
      if (dbg_m_loaduse[0])
        $fdisplay(mcov_fd, "EV LOAD_USE_RS1 %08x %08x", dut.if_id.pc, dut.if_id.insn);
      if (dbg_m_loaduse[1])
        $fdisplay(mcov_fd, "EV LOAD_USE_RS2 %08x %08x", dut.if_id.pc, dut.if_id.insn);
      if (dbg_md_start && previous_md_done)
        $fdisplay(mcov_fd, "EV DIV_CONSECUTIVE %08x %08x", dbg_m_pc, dbg_m_insn);
    end
    if (rst_n) previous_md_done <= dbg_md_done;
    else previous_md_done <= 1'b0;
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
    if (trace_fd != 0 && ENABLE_C) $fdisplay(trace_fd, "TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data");
    if ($value$plusargs("MCOV=%s", mcov_file)) begin
      mcov_fd = $fopen(mcov_file, "w");
      if (mcov_fd == 0) begin mcov_error = 1; $display("MCOV_OPEN_FAIL: %s", mcov_file); end
    end

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
    if (dbg_assert_fail || mcov_error) pass = 1'b0;

    if (trace_fd != 0) begin
      if (ENABLE_C) $fdisplay(trace_fd, "STOP %08x %08x %02d %0d", halt_pc, halt_raw_insn, halt_ilen_bytes, int'(halt_cause));
      $fdisplay(trace_fd, "HALT %0d %08x", int'(halt_cause), halt_pc);
      for (int r = 1; r < 32; r++) $fdisplay(trace_fd, "REG %0d %08x", r, dut.u_rf.regs[r]);
      for (int a = 16'h4000; a < 16'h6000; a += 4)
        if (mem[a >> 2] != 32'h0) $fdisplay(trace_fd, "MEM %08x %08x", a, mem[a >> 2]);
      $fclose(trace_fd);
    end
    if (mcov_fd != 0) $fclose(mcov_fd);

    $display("MD_STATS starts=%0d dones=%0d busy_cycles=%0d aborts_started=%0d",
             md_starts, md_dones, busy_cycles, md_aborts_started);
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
