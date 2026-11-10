// tb_rv_core.sv - Stage 1 system testbench for rv_core_single.
// Plusargs: +HEX=<file> (required) +TRACE=<file> +EXPECT_CAUSE=<n> (default 1=ECALL)
//           +CHECK_GP=<0|1> (default 1: require x3==1 on ECALL) +TIMEOUT=<cycles>
// Unified 64 KiB memory, combinational read, synchronous byte-enable write.
// Prints exactly one "TEST_RESULT: PASS|FAIL ..." line. Trace format matches scripts/simulation/rv32i_iss.py.
`timescale 1ns/1ps
module tb_rv_core #(parameter bit ENABLE_C = 1'b0, parameter bit ENABLE_A = 1'b0, parameter bit ENABLE_Z = 1'b0, parameter bit ENABLE_M = 1'b0, parameter bit USE_STAGE8_IRQ_DRIVER = 1'b0, parameter bit ENABLE_STAGE8_MONITORS = 1'b0);
  import rv32_pkg::*;

  localparam int MEM_WORDS = 16384;   // 64 KiB

  logic clk = 1'b0;
  logic rst_n = 1'b0;
  always #5 clk = ~clk;

  word_t mem [0:MEM_WORDS-1];

  word_t imem_addr, imem_addr_next, imem_rdata, imem_rdata_next, dmem_addr, dmem_wdata, dmem_rdata;
  logic imem_valid, imem_next_valid, dmem_valid;
  logic irq_msip=1'b0, irq_mtip=1'b0, irq_meip=1'b0;
  int irq_pc=-1, irq_level_mask=0;
  logic irq_fired=1'b0, irq_seen=1'b0;
  logic dmem_re;
  logic dmem_atomic_commit;
  logic [3:0] dmem_we;
  logic halted;
  logic test_done=1'b0;
  logic ret_valid, ret_rd_we, ret_mem_re, ret_mem_we;
  word_t ret_mem_addr, ret_mem_wdata;
  wire done_store = ENABLE_M && ret_valid && ret_mem_we && ret_mem_addr == 32'h0000_fffc && ret_mem_wdata == 32'h5354_4737;
  word_t test_done_pc=0, test_done_raw=0;
  logic [4:0] test_done_ilen=0;
  halt_cause_e halt_cause;
  word_t halt_pc;
  word_t ret_pc, ret_insn, ret_raw_insn, ret_expanded_insn, ret_pc_next;
  word_t ret_rd_wdata, ret_mem_rdata;
  logic [4:0] ret_ilen_bytes;
  reg_t ret_rd;
  logic [3:0] ret_mem_be;

  rv_core_single #(.ENABLE_C(ENABLE_C || ENABLE_A || ENABLE_Z || ENABLE_M), .ENABLE_A(ENABLE_A), .ENABLE_Z(ENABLE_Z), .ENABLE_M(ENABLE_M)) dut (
    .clk(clk), .rst_n(rst_n),
    .imem_addr(imem_addr), .imem_addr_next(imem_addr_next), .imem_rdata(imem_rdata), .imem_valid(imem_valid),
    .imem_rdata_next(imem_rdata_next), .imem_next_valid(imem_next_valid),
    .dmem_addr(dmem_addr), .dmem_re(dmem_re), .dmem_we(dmem_we), .dmem_wdata(dmem_wdata), .dmem_rdata(dmem_rdata), .dmem_valid(dmem_valid), .dmem_atomic_commit(dmem_atomic_commit),
    .irq_msip(irq_msip), .irq_mtip(irq_mtip), .irq_meip(irq_meip),
    .halted(halted), .halt_cause(halt_cause), .halt_pc(halt_pc),
    .ret_valid(ret_valid), .ret_pc(ret_pc), .ret_insn(ret_insn),
    .ret_raw_insn(ret_raw_insn), .ret_expanded_insn(ret_expanded_insn),
    .ret_ilen_bytes(ret_ilen_bytes), .ret_pc_next(ret_pc_next),
    .ret_rd_we(ret_rd_we), .ret_rd(ret_rd), .ret_rd_wdata(ret_rd_wdata),
    .ret_mem_re(ret_mem_re), .ret_mem_we(ret_mem_we), .ret_mem_addr(ret_mem_addr),
    .ret_mem_be(ret_mem_be), .ret_mem_wdata(ret_mem_wdata), .ret_mem_rdata(ret_mem_rdata)
  );
  rv_s8_observe_if s8_observe(clk);
  assign s8_observe.rst_n = rst_n;
  assign s8_observe.ret_valid = ret_valid;
  assign s8_observe.ret_pc = ret_pc;
  assign s8_observe.ret_raw = ret_raw_insn;
  assign s8_observe.ret_expanded = ret_expanded_insn;
  assign s8_observe.ret_ilen = ret_ilen_bytes;
  assign s8_observe.trap_valid = dut.trap_enter || dut.irq_take;
  assign s8_observe.trap_pc = dut.pc;
  assign s8_observe.trap_raw = dut.raw_insn;
  assign s8_observe.trap_cause = {dut.irq_take,26'b0,(dut.irq_take ? dut.irq_cause : dut.architectural_cause)};
  assign s8_observe.trap_tval = dut.trap_value;
  assign s8_observe.csr_access = ret_valid && dut.csr_inst;
  assign s8_observe.csr_commit = ret_valid && dut.csr_inst && dut.csr_write;
  assign s8_observe.csr_pc = ret_pc;
  assign s8_observe.csr_raw = ret_raw_insn;
  assign s8_observe.csr_addr = dut.csr_addr;
  assign s8_observe.csr_old = dut.csr_old;
  assign s8_observe.csr_new = dut.csr_new;
  assign s8_observe.atomic_commit = dmem_atomic_commit;
  assign s8_observe.atomic_read = dmem_re;
  assign s8_observe.atomic_write = |dmem_we;
  assign s8_observe.atomic_pc = ret_pc;
  assign s8_observe.atomic_raw = ret_raw_insn;
  assign s8_observe.atomic_addr = dmem_addr;
  assign s8_observe.atomic_be = dmem_we;
  assign s8_observe.md_start = 1'b0; assign s8_observe.md_busy = 1'b0;
  assign s8_observe.md_done = 1'b0; assign s8_observe.md_abort = 1'b0;
  assign s8_observe.md_pc = ret_pc; assign s8_observe.md_raw = ret_raw_insn;
  integer s8_retire_events, s8_trap_events, s8_csr_accesses, s8_csr_commits;
  generate if (ENABLE_STAGE8_MONITORS) begin : g_stage8_monitors
    rv_s8_retirement_monitor retire_mon(s8_observe, s8_retire_events);
    rv_s8_trap_monitor trap_mon(s8_observe, s8_trap_events);
    rv_s8_csr_monitor csr_mon(s8_observe, s8_csr_accesses, s8_csr_commits);
    integer unused_atomic_commits, unused_atomic_writes;
    rv_s8_atomic_monitor atomic_mon(s8_observe, unused_atomic_commits, unused_atomic_writes);
  end endgenerate
  generate
    if (USE_STAGE8_IRQ_DRIVER) begin : g_stage8_irq
      rv_s8_interrupt_driver u_driver(
        .clk(clk), .rst_n(rst_n), .enabled(ENABLE_M), .schedule_pc(irq_pc),
        .level_mask(irq_level_mask), .wait_div(0), .timing_mode(0),
        .core_pc(dut.pc), .if_pc(32'b0), .id_pc(32'b0), .if_valid(1'b0), .id_valid(1'b0),
        .mie(1'b0), .trap_taken(dut.irq_take), .div_busy(1'b0), .div_start(1'b0),
        .irq_msip(irq_msip), .irq_mtip(irq_mtip), .irq_meip(irq_meip), .fired(irq_fired), .seen(irq_seen));
    end else begin : g_legacy_irq
      always @(posedge clk) if (rst_n && ENABLE_M && dut.irq_take) irq_seen <= 1'b1;
      always @(negedge clk) begin
        if (!rst_n) begin irq_msip<=0; irq_mtip<=0; irq_meip<=0; irq_fired<=0; end
        else if (ENABLE_M) begin
          if (irq_seen) begin irq_msip<=0; irq_mtip<=0; irq_meip<=0; end
          else if (!irq_fired && irq_pc >= 0 && dut.pc == irq_pc) begin
            irq_msip<=irq_level_mask[0]; irq_mtip<=irq_level_mask[1]; irq_meip<=irq_level_mask[2]; irq_fired<=1'b1;
          end
        end
      end
    end
  endgenerate

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
  assign imem_valid = !imem_oob;
  assign imem_next_valid = (imem_addr_next[31:16] == 16'h0);
  assign imem_rdata = imem_oob ? 32'h0 : mem[imem_addr[15:2]];
  assign imem_rdata_next = imem_next_valid ? mem[imem_addr_next[15:2]] : 32'h0;
  assign dmem_rdata = dmem_oob ? 32'h0 : mem[dmem_addr[15:2]];
  assign dmem_valid = !dmem_oob;

  always @(posedge clk) begin
    if (rst_n) begin
      if (!halted && imem_oob && !ENABLE_M) oob_errors++;
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
      automatic word_t before_addr=dut.reservation_valid ? dut.reservation_addr : 32'hffffffff;
      automatic word_t after_addr=before_addr;
      automatic logic writes=(|dmem_we);
      automatic integer sc_status=(dut.atomic_sc ? int'(dut.atomic_wb) : -1);
      if (dut.atomic_lr) after_addr=dmem_addr;
      else if (dut.atomic_sc || (writes && dut.reservation_valid && dmem_addr[31:2]==dut.reservation_addr[31:2])) after_addr=32'hffffffff;
      $fdisplay(acov_fd,"%08x\t%08x\t%s\t%0d\t%0d\t%0d\t%0d\t%0d\t%08x\t%s\t%08x\t%s\t%0d\t%0d\t%0d",
        dut.pc,dut.raw_insn,a_name(dut.raw_insn[31:27]),dut.raw_insn[26],dut.raw_insn[25],
        dut.rd,dut.rs1,dut.rs2,dmem_addr,dmem_re ? $sformatf("%08x",dmem_rdata) : acov_dash,
        dut.rs2_data,writes ? $sformatf("%08x",dmem_wdata) : acov_dash,sc_status,
        dut.reservation_valid ? int'(dut.reservation_addr) : -1,
        after_addr==32'hffffffff ? -1 : int'(after_addr));
    end
  end

  // ---------------- Trace ----------------
  int trace_fd = 0;
  int trap_fd = 0;
  int mcov_fd = 0;
  string trap_file;
  string mcov_file;
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
    if (rst_n && ENABLE_M && mcov_fd != 0 && ret_valid && dut.csr_inst && dut.csr_write)
      $fdisplay(mcov_fd,"Z CSR_WRITE %08x %08x %03x %08x %08x",ret_pc,ret_raw_insn,dut.csr_addr,dut.csr_old,dut.csr_new);
    if (rst_n && ENABLE_M && mcov_fd != 0 && ret_valid && ret_insn == INSN_MRET)
      $fdisplay(mcov_fd,"M MRET %08x %08x",ret_pc,ret_raw_insn);
    if (rst_n && ENABLE_M && mcov_fd != 0 && ret_valid && dut.csr_inst)
      $fdisplay(mcov_fd,"Z CSR_ACCESS %08x %08x %03x %08x %08x %08x %0d",
                ret_pc,ret_raw_insn,dut.csr_addr,dut.csr_source,dut.csr_old,dut.csr_new,dut.csr_write);
    if (rst_n && ENABLE_Z && mcov_fd != 0 && ret_valid && ret_insn == 32'h0000_100F)
      $fdisplay(mcov_fd,"Z FENCEI %08x %08x %0d %08x",ret_pc,ret_raw_insn,ret_ilen_bytes,ret_pc_next);
    if (rst_n && ENABLE_M && trap_fd != 0 && (dut.trap_enter || dut.irq_take))
      $fdisplay(trap_fd,"%08x\t%08x\t%08x\t%08x\t%08x",dut.pc,dut.raw_insn,
                {dut.irq_take,26'b0,(dut.irq_take ? dut.irq_cause : dut.architectural_cause)},
                dut.trap_value,dut.trap_target);
    if (rst_n && ret_valid) begin
      automatic int    st_n = 0;
      automatic word_t st_d = 32'h0;
      automatic word_t st_a = 32'h0;
      automatic word_t rdv  = 32'h0;
      automatic int    rdn  = 0;
      instret++;
      if (done_store) begin test_done<=1'b1; test_done_pc<=ret_pc; test_done_raw<=ret_raw_insn; test_done_ilen<=ret_ilen_bytes; end
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
      $fdisplay(trace_fd, "I %08x %08x %02d %08x %02d %08x %0d %08x %08x", ret_pc, ret_raw_insn, ret_ilen_bytes, ret_expanded_insn, rdn, rdv, st_n, st_a, st_d);
        else
          $fdisplay(trace_fd, "%08x %08x %02d %08x %0d %08x %08x", ret_pc, ret_insn, rdn, rdv, st_n, st_a, st_d);
      end
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
    if (!$value$plusargs("HEX=%s", hex_file)) begin
      $display("TEST_RESULT: FAIL (+HEX not given)");
      $finish;
    end
    void'($value$plusargs("EXPECT_CAUSE=%d", expect_cause));
    void'($value$plusargs("CHECK_GP=%d", check_gp));
    void'($value$plusargs("TIMEOUT=%d", timeout));
    void'($value$plusargs("IRQ_PC=%h", irq_pc));
    void'($value$plusargs("IRQ_LEVELS=%d", irq_level_mask));
    if ($value$plusargs("TRACE=%s", trace_file)) trace_fd = $fopen(trace_file, "w");
    if ($value$plusargs("TRAP=%s", trap_file)) begin
      trap_fd=$fopen(trap_file,"w");
      if(trap_fd==0) oob_errors++;
      else $fdisplay(trap_fd,"fault_pc\traw\tmcause\tmtval\ttarget");
    end
    if ($value$plusargs("MCOV=%s", mcov_file)) begin
      mcov_fd=$fopen(mcov_file,"w");
      if(mcov_fd==0) oob_errors++;
    end
    if ($value$plusargs("ACOV=%s", acov_file)) begin
      acov_fd=$fopen(acov_file,"w");
      if(acov_fd==0) begin oob_errors++; $display("ACOV_OPEN_FAIL: %s",acov_file); end
      else $fdisplay(acov_fd,"pc\traw\top\taq\trl\trd\trs1\trs2\taddress\told\tsource\tnew\tsc_status\treservation_before\treservation_after");
    end
    if (trace_fd != 0 && ENABLE_A) $fdisplay(trace_fd, "TRACE_V3 RV32IMAC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data atomic_sidecar");
    else if (trace_fd != 0 && ENABLE_C) $fdisplay(trace_fd, "TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data");

    for (int i = 0; i < MEM_WORDS; i++) mem[i] = 32'h0;
    $readmemh(hex_file, mem);

    repeat (3) @(posedge clk);
    @(negedge clk) rst_n = 1'b1;

    while (!(ENABLE_M ? (test_done || done_store) : halted) && cycles < timeout) begin
      @(posedge clk);
      cycles++;
    end
    @(negedge clk);

    gp_val = dut.u_rf.regs[3];
    pass = (ENABLE_M ? (test_done || done_store) : (halted && (int'(halt_cause) == expect_cause))) && (oob_errors == 0);
    if (check_gp != 0 && expect_cause == int'(HALT_ECALL)) pass = pass && (gp_val == 32'h1);

    if (trace_fd != 0) begin
      if (ENABLE_C || ENABLE_A || ENABLE_M)
        $fdisplay(trace_fd, "STOP %08x %08x %02d %0d", ENABLE_M ? test_done_pc + test_done_ilen : halt_pc,
                  ENABLE_M ? test_done_raw : dut.halt_raw_insn, ENABLE_M ? test_done_ilen : dut.halt_ilen_bytes,
                  ENABLE_M ? 0 : int'(halt_cause));
      $fdisplay(trace_fd, "HALT %0d %08x", ENABLE_M ? 0 : int'(halt_cause), ENABLE_M ? test_done_pc + test_done_ilen : halt_pc);
      for (int r = 1; r < 32; r++) $fdisplay(trace_fd, "REG %0d %08x", r, dut.u_rf.regs[r]);
      for (int a = 16'h4000; a < 16'h6000; a += 4)
        if (mem[a >> 2] != 32'h0) $fdisplay(trace_fd, "MEM %08x %08x", a, mem[a >> 2]);
      if (ENABLE_Z) begin
        $fdisplay(trace_fd, "CSR 800 %08x", dut.csr0);
        $fdisplay(trace_fd, "CSR 801 %08x", dut.csr1);
        $fdisplay(trace_fd, "CSR cc0 %08x", CSR_STAGE6_ID);
      end
      if (ENABLE_M) begin
        $fdisplay(trace_fd,"CSR 300 %08x",dut.u_machine.mstatus); $fdisplay(trace_fd,"CSR 301 %08x",(32'h40001100 | (ENABLE_A ? 32'h1 : 32'h0) | ((ENABLE_C || ENABLE_A || ENABLE_Z || ENABLE_M) ? 32'h4 : 32'h0)));
        $fdisplay(trace_fd,"CSR 304 %08x",dut.u_machine.mie); $fdisplay(trace_fd,"CSR 305 %08x",dut.u_machine.mtvec);
        $fdisplay(trace_fd,"CSR 340 %08x",dut.u_machine.mscratch); $fdisplay(trace_fd,"CSR 341 %08x",dut.u_machine.mepc);
        $fdisplay(trace_fd,"CSR 342 %08x",dut.u_machine.mcause); $fdisplay(trace_fd,"CSR 343 %08x",dut.u_machine.mtval);
        $fdisplay(trace_fd,"CSR b00 %08x",dut.u_machine.mcycle);
        $fdisplay(trace_fd,"CSR b02 %08x",dut.u_machine.minstret); $fdisplay(trace_fd,"CSR b80 %08x",dut.u_machine.mcycleh);
        $fdisplay(trace_fd,"CSR b82 %08x",dut.u_machine.minstreth); $fdisplay(trace_fd,"CSR 344 %08x",dut.u_machine.pending);
      end
      $fclose(trace_fd);
    end
    if(acov_fd!=0) $fclose(acov_fd);
    if(trap_fd!=0) $fclose(trap_fd);
    if(mcov_fd!=0) $fclose(mcov_fd);

    $display("ATOMIC_STATS commits=%0d writes=%0d", atomic_commits, atomic_writes);
    if (ENABLE_STAGE8_MONITORS)
      $display("STAGE8_COMPONENTS retire=%0d traps=%0d csr_access=%0d csr_commit=%0d", s8_retire_events, s8_trap_events, s8_csr_accesses, s8_csr_commits);
    $display("TEST_RESULT: %s hex=%s cause=%0d expect=%0d gp=0x%0h instret=%0d cycles=%0d oob=%0d%s",
             pass ? "PASS" : "FAIL", hex_file, ENABLE_M ? 0 : int'(halt_cause), expect_cause, gp_val, instret, cycles,
             oob_errors, (ENABLE_M ? (test_done || done_store) : halted) ? "" : " TIMEOUT");
    $finish;
  end
endmodule
