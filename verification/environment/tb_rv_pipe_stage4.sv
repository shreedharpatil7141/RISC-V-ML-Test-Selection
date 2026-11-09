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
  parameter bit ENABLE_C = 1'b0,
  parameter bit ENABLE_A = 1'b0,
  parameter bit ENABLE_Z = 1'b0
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
  logic dmem_atomic_commit;
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

  rv_core_pipe #(.USE_ITERATIVE_M(USE_ITERATIVE_M), .ENABLE_C(ENABLE_C || ENABLE_A || ENABLE_Z), .ENABLE_A(ENABLE_A), .ENABLE_Z(ENABLE_Z)) dut (
    .clk(clk), .rst_n(rst_n),
    .imem_addr(imem_addr), .imem_addr_next(imem_addr_next), .imem_rdata(imem_rdata),
    .imem_valid(imem_valid), .imem_rdata_next(imem_rdata_next), .imem_next_valid(imem_next_valid),
    .dmem_addr(dmem_addr), .dmem_re(dmem_re), .dmem_we(dmem_we), .dmem_wdata(dmem_wdata), .dmem_rdata(dmem_rdata), .dmem_valid(dmem_valid), .dmem_atomic_commit(dmem_atomic_commit),
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
  longint atomic_commits = 0, atomic_writes = 0;
  integer acov_fd = 0;
  string acov_file;
  string acov_dash = "-";
  function automatic string a_name(input logic [4:0] f5);
    case(f5)
      5'b00010:return "lr.w"; 5'b00011:return "sc.w"; 5'b00001:return "amoswap.w";
      5'b00000:return "amoadd.w"; 5'b00100:return "amoxor.w"; 5'b01100:return "amoand.w";
      5'b01000:return "amoor.w"; 5'b10000:return "amomin.w"; 5'b10100:return "amomax.w";
      5'b11000:return "amominu.w"; 5'b11100:return "amomaxu.w"; default:return "reserved";
    endcase
  endfunction
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
      if (!(ENABLE_C || ENABLE_A) && !halted && imem_oob) oob_errors++;
      if ((dmem_re || (|dmem_we)) && dmem_oob) oob_errors++;
      if (dmem_atomic_commit) begin
        atomic_commits++;
        if (!dmem_re || !dmem_valid || ((|dmem_we) && dmem_we != 4'b1111)) oob_errors++;
        if (|dmem_we) atomic_writes++;
      end
      if (dmem_re && (|dmem_we) && !dmem_atomic_commit) oob_errors++;
      if (|dmem_we && !dmem_oob) begin
        if (dmem_we[0]) mem[dmem_addr[15:2]][7:0]   <= dmem_wdata[7:0];
        if (dmem_we[1]) mem[dmem_addr[15:2]][15:8]  <= dmem_wdata[15:8];
        if (dmem_we[2]) mem[dmem_addr[15:2]][23:16] <= dmem_wdata[23:16];
        if (dmem_we[3]) mem[dmem_addr[15:2]][31:24] <= dmem_wdata[31:24];
      end
    end
  end

  always @(posedge clk) begin
    if (rst_n && dmem_atomic_commit && acov_fd != 0) begin
      automatic word_t before_addr=dut.u_mem.reservation_valid ? dut.u_mem.reservation_addr : 32'hffffffff;
      automatic word_t after_addr=before_addr;
      automatic logic writes=(|dmem_we);
      automatic integer sc_status=(dut.u_mem.atomic_sc ? int'(dut.u_mem.atomic_wb) : -1);
      if (dut.u_mem.atomic_lr) after_addr=dmem_addr;
      else if (dut.u_mem.atomic_sc || (writes && dut.u_mem.reservation_valid && dmem_addr[31:2]==dut.u_mem.reservation_addr[31:2])) after_addr=32'hffffffff;
      $fdisplay(acov_fd,"%08x\t%08x\t%s\t%0d\t%0d\t%0d\t%0d\t%0d\t%08x\t%s\t%08x\t%s\t%0d\t%0d\t%0d",
        dut.ex_mem.pc,dut.ex_mem.raw_insn,a_name(dut.ex_mem.insn[31:27]),dut.ex_mem.insn[26],dut.ex_mem.insn[25],
        dut.ex_mem.insn[11:7],dut.ex_mem.insn[19:15],dut.ex_mem.insn[24:20],dmem_addr,
        dmem_re ? $sformatf("%08x",dmem_rdata) : acov_dash,dut.ex_mem.store_data,
        writes ? $sformatf("%08x",dmem_wdata) : acov_dash,sc_status,
        dut.u_mem.reservation_valid ? int'(dut.u_mem.reservation_addr) : -1,
        after_addr==32'hffffffff ? -1 : int'(after_addr));
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
        if (ENABLE_C || ENABLE_A)
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

  // Optional verification side channel. Architectural TRACE rows above remain
  // unchanged; these records distinguish EX issue/completion, WB retirement,
  // and instructions removed by redirect/fault before issue.
  always @(posedge clk) begin
    if (rst_n && mcov_fd != 0) begin
      // Stage 4 coverage lifecycle records are DUT-side observations. The
      // checker deduplicates retries caused by stalls using PC/raw/length.
      if ((ENABLE_C || ENABLE_A) && dut.if_id.valid)
        $fdisplay(mcov_fd, "C ATTEMPT %08x %08x %0d", dut.if_id.pc, dut.if_id.raw_insn, dut.if_id.ilen_bytes);
      if (ENABLE_A && dut.if_id.valid && dut.if_id.insn[6:0] == OPC_AMO)
        $fdisplay(mcov_fd, "A ATTEMPT %08x %08x", dut.if_id.pc, dut.if_id.raw_insn);
      if (ENABLE_Z && dut.if_id.valid &&
          (dut.if_id.insn[6:0] == OPC_SYSTEM || dut.if_id.insn == 32'h0000_100F))
        $fdisplay(mcov_fd, "Z ATTEMPT %08x %08x %0d", dut.if_id.pc, dut.if_id.raw_insn, dut.if_id.ilen_bytes);
      if ((ENABLE_C || ENABLE_A) && ret_valid)
        $fdisplay(mcov_fd, "C RETIRE %08x %08x %0d", ret_pc, ret_insn, ret_ilen_bytes);
      if (ENABLE_A && ret_valid && ret_insn[6:0] == OPC_AMO)
        $fdisplay(mcov_fd, "A RETIRE %08x %08x", ret_pc, ret_insn);
      if (ENABLE_Z && ret_valid &&
          (ret_insn[6:0] == OPC_SYSTEM || ret_insn == 32'h0000_100F))
        $fdisplay(mcov_fd, "Z RETIRE %08x %08x %0d", ret_pc, ret_insn, ret_ilen_bytes);
      // Sample the same pre-NBA MEM/WB record consumed by rv_core_pipe's
      // CSR state-update always_ff block. This is the single authorized commit
      // edge and produces one record for each committed CSR write.
      if (ENABLE_Z && dut.mem_wb.valid && dut.mem_wb.csr_write)
        $fdisplay(mcov_fd, "Z CSR_WRITE %08x %08x %03x %08x %08x", dut.mem_wb.pc, dut.mem_wb.raw_insn,
                  dut.mem_wb.csr_addr, dut.mem_wb.wb_data, dut.mem_wb.csr_new);
      if (ENABLE_Z && dut.fault && dut.ex_mem.insn[6:0] == OPC_SYSTEM)
        $fdisplay(mcov_fd, "Z CSR_FAULT %08x %08x %0d", dut.ex_mem.pc, dut.ex_mem.raw_insn,
                  int'(dut.fault_cause));
      if (ENABLE_Z && dut.redirect && dut.id_ex.is_fencei)
        $fdisplay(mcov_fd, "Z FENCEI %08x %08x %0d %08x", dut.id_ex.pc, dut.id_ex.raw_insn,
                  dut.id_ex.ilen_bytes, dut.redirect_target);
      if (ENABLE_Z && dut.redirect && dut.id_ex.is_fencei && dut.if_id.valid)
        $fdisplay(mcov_fd, "Z SQUASH_REDIRECT %08x %08x %0d", dut.if_id.pc,
                  dut.if_id.raw_insn, dut.if_id.ilen_bytes);
      if (ENABLE_Z && dut.redirect && dut.if_id.valid && dut.if_id.insn[6:0] == OPC_SYSTEM)
        $fdisplay(mcov_fd, "Z SQUASH_REDIRECT %08x %08x %0d", dut.if_id.pc,
                  dut.if_id.raw_insn, dut.if_id.ilen_bytes);
      if ((ENABLE_C || ENABLE_A) && dut.fault)
        $fdisplay(mcov_fd, "C FAULT %08x %08x %0d %0d", dut.ex_mem.pc, dut.ex_mem.raw_insn,
                  dut.ex_mem.ilen_bytes, int'(dut.fault_cause));
      if (ENABLE_A && dut.fault && dut.ex_mem.is_a)
        $fdisplay(mcov_fd, "A FAULT %08x %08x %0d", dut.ex_mem.pc, dut.ex_mem.raw_insn, int'(dut.fault_cause));
      if ((ENABLE_C || ENABLE_A) && dut.redirect && dut.if_id.valid)
        $fdisplay(mcov_fd, "C SQUASH_REDIRECT %08x %08x %0d", dut.if_id.pc, dut.if_id.raw_insn, dut.if_id.ilen_bytes);
      if (ENABLE_A && dut.redirect && dut.if_id.valid && dut.if_id.insn[6:0] == OPC_AMO)
        $fdisplay(mcov_fd, "A SQUASH_REDIRECT %08x %08x", dut.if_id.pc, dut.if_id.raw_insn);
      if ((ENABLE_C || ENABLE_A) && dut.fault && dut.id_ex.valid)
        $fdisplay(mcov_fd, "C SQUASH_FAULT %08x %08x %0d", dut.id_ex.pc, dut.id_ex.raw_insn, dut.id_ex.ilen_bytes);
      if (ENABLE_A && dut.fault && dut.id_ex.valid && dut.id_ex.is_a)
        $fdisplay(mcov_fd, "A SQUASH_FAULT %08x %08x", dut.id_ex.pc, dut.id_ex.raw_insn);
      if ((ENABLE_C || ENABLE_A) && dut.fault && dut.if_id.valid)
        $fdisplay(mcov_fd, "C SQUASH_FAULT %08x %08x %0d", dut.if_id.pc, dut.if_id.raw_insn, dut.if_id.ilen_bytes);
      if (ENABLE_A && dut.fault && dut.if_id.valid && dut.if_id.insn[6:0] == OPC_AMO)
        $fdisplay(mcov_fd, "A SQUASH_FAULT_IFID %08x %08x", dut.if_id.pc, dut.if_id.raw_insn);
      if ((ENABLE_C || ENABLE_A) && dbg_md_busy)
        $fdisplay(mcov_fd, "C DIV_HOLD %08x %08x %0d", dut.id_ex.pc, dut.id_ex.raw_insn, dut.id_ex.ilen_bytes);
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
    if ($value$plusargs("ACOV=%s", acov_file)) begin
      acov_fd=$fopen(acov_file,"w");
      if(acov_fd==0) begin mcov_error=1; $display("ACOV_OPEN_FAIL: %s",acov_file); end
      else $fdisplay(acov_fd,"pc\traw\top\taq\trl\trd\trs1\trs2\taddress\told\tsource\tnew\tsc_status\treservation_before\treservation_after");
    end
    if (trace_fd != 0 && ENABLE_A) $fdisplay(trace_fd, "TRACE_V3 RV32IMAC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data atomic_sidecar");
    else if (trace_fd != 0 && ENABLE_C) $fdisplay(trace_fd, "TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data");
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
      if (ENABLE_C || ENABLE_A) $fdisplay(trace_fd, "STOP %08x %08x %02d %0d", halt_pc, halt_raw_insn, halt_ilen_bytes, int'(halt_cause));
      $fdisplay(trace_fd, "HALT %0d %08x", int'(halt_cause), halt_pc);
      for (int r = 1; r < 32; r++) $fdisplay(trace_fd, "REG %0d %08x", r, dut.u_rf.regs[r]);
      if (ENABLE_Z) begin
        $fdisplay(trace_fd, "CSR 800 %08x", dut.csr0);
        $fdisplay(trace_fd, "CSR 801 %08x", dut.csr1);
        $fdisplay(trace_fd, "CSR cc0 %08x", CSR_STAGE6_ID);
      end
      for (int a = 16'h4000; a < 16'h6000; a += 4)
        if (mem[a >> 2] != 32'h0) $fdisplay(trace_fd, "MEM %08x %08x", a, mem[a >> 2]);
      $fclose(trace_fd);
    end
    if (mcov_fd != 0) $fclose(mcov_fd);
    if (acov_fd != 0) $fclose(acov_fd);

    $display("ATOMIC_STATS commits=%0d writes=%0d", atomic_commits, atomic_writes);
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
