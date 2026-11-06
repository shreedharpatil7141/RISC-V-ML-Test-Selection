// tb_rv_pipe_units.sv - Unit tests for rv_forward_unit and rv_hazard_unit (Stage 2).
// Part A: exhaustive over a reduced register space (regs 0..3, all flag combinations).
// Part B: 200k Xorshift32 random vectors over the full 5-bit register space (biased towards matches).
// Expected values use a different formulation (explicit scalar function) from the RTL.
// Deterministic Xorshift32 PRNG (no $urandom: unsupported in XSim).

`timescale 1ns/1ps

module tb_rv_pipe_units;

  import rv32_pkg::*;
  import rv_pipe_pkg::*;

  int errors = 0;
  int checks = 0;

  task automatic chk(input bit ok, input string msg);
    checks++;
    if (!ok) begin
      errors++;
      if (errors < 20)
        $display("FAIL: %s", msg);
    end
  endtask

  // ---------- DUTs ----------

  reg_t ex_rs1, ex_rs2;
  logic exmem_valid, exmem_reg_we, exmem_is_load;
  reg_t exmem_rd;
  logic memwb_valid, memwb_reg_we;
  reg_t memwb_rd;
  fwd_sel_e fwd_a, fwd_b;
  logic a_exmem_match, a_memwb_match, b_exmem_match, b_memwb_match;

  rv_forward_unit u_fwd (
    .ex_rs1(ex_rs1),
    .ex_rs2(ex_rs2),
    .exmem_valid(exmem_valid),
    .exmem_reg_we(exmem_reg_we),
    .exmem_is_load(exmem_is_load),
    .exmem_rd(exmem_rd),
    .memwb_valid(memwb_valid),
    .memwb_reg_we(memwb_reg_we),
    .memwb_rd(memwb_rd),
    .fwd_a(fwd_a),
    .fwd_b(fwd_b),
    .a_exmem_match(a_exmem_match),
    .a_memwb_match(a_memwb_match),
    .b_exmem_match(b_exmem_match),
    .b_memwb_match(b_memwb_match)
  );

  logic id_valid, id_uses_rs1, id_uses_rs2, ex_valid, ex_mem_re, stall;
  reg_t id_rs1, id_rs2, ex_rd;

  rv_hazard_unit u_haz (
    .id_valid(id_valid),
    .id_rs1(id_rs1),
    .id_rs2(id_rs2),
    .id_uses_rs1(id_uses_rs1),
    .id_uses_rs2(id_uses_rs2),
    .ex_valid(ex_valid),
    .ex_mem_re(ex_mem_re),
    .ex_rd(ex_rd),
    .stall(stall)
  );

  // ---------- Expected-value models ----------

  function automatic int exp_fwd(
    input int rs,
    input bit e_valid, input bit e_we, input bit e_ld, input int e_rd,
    input bit m_valid, input bit m_we, input int m_rd
  );
    int r;
    r = 0;                                   // 0 none, 1 EX/MEM, 2 MEM/WB
    if (rs != 0) begin
      if (m_valid && m_we && (m_rd == rs)) r = 2;
      if (e_valid && e_we && !e_ld && (e_rd == rs)) r = 1;   // younger producer overrides
    end
    return r;
  endfunction

  function automatic bit exp_stall(
    input bit i_valid, input bit u1, input bit u2, input int r1, input int r2,
    input bit e_valid, input bit e_ld, input int e_rd
  );
    bit s;
    s = 0;
    if (i_valid && e_valid && e_ld && (e_rd != 0)) begin
      if (u1 && (r1 == e_rd)) s = 1;
      if (u2 && (r2 == e_rd)) s = 1;
    end
    return s;
  endfunction

  // ---------- PRNG ----------

  logic [31:0] rng_state = 32'h00005eed;

  function automatic word_t rnd();
    logic [31:0] x;
    begin
      x = rng_state;
      x = x ^ (x << 13);
      x = x ^ (x >> 17);
      x = x ^ (x << 5);
      rng_state = x;
      rnd = x;
    end
  endfunction

  task automatic check_fwd(input string tag);
    int ea, eb;
    begin
      #1;
      ea = exp_fwd(int'(ex_rs1), exmem_valid, exmem_reg_we, exmem_is_load, int'(exmem_rd),
                   memwb_valid, memwb_reg_we, int'(memwb_rd));
      eb = exp_fwd(int'(ex_rs2), exmem_valid, exmem_reg_we, exmem_is_load, int'(exmem_rd),
                   memwb_valid, memwb_reg_we, int'(memwb_rd));
      chk(int'(fwd_a) == ea, $sformatf("%s fwd_a rs1=%0d got=%0d exp=%0d", tag, ex_rs1, int'(fwd_a), ea));
      chk(int'(fwd_b) == eb, $sformatf("%s fwd_b rs2=%0d got=%0d exp=%0d", tag, ex_rs2, int'(fwd_b), eb));
    end
  endtask

  task automatic check_haz(input string tag);
    bit es;
    begin
      #1;
      es = exp_stall(id_valid, id_uses_rs1, id_uses_rs2, int'(id_rs1), int'(id_rs2),
                     ex_valid, ex_mem_re, int'(ex_rd));
      chk(stall === es, $sformatf("%s stall got=%0d exp=%0d rs1=%0d rs2=%0d ex_rd=%0d", tag, stall, es, id_rs1, id_rs2, ex_rd));
    end
  endtask

  initial begin

    rng_state = 32'h00005eed;

    // ------------------------------------------------------
    // Part A: exhaustive over regs 0..3
    // ------------------------------------------------------

    for (int a = 0; a < 4; a++) begin
      for (int b = 0; b < 4; b++) begin
        for (int er = 0; er < 4; er++) begin
          for (int mr = 0; mr < 4; mr++) begin
            for (int f = 0; f < 32; f++) begin

              ex_rs1 = a[4:0];
              ex_rs2 = b[4:0];
              exmem_rd = er[4:0];
              memwb_rd = mr[4:0];
              exmem_valid = f[0];
              exmem_reg_we = f[1];
              exmem_is_load = f[2];
              memwb_valid = f[3];
              memwb_reg_we = f[4];
              check_fwd("exh");

              id_rs1 = a[4:0];
              id_rs2 = b[4:0];
              ex_rd = er[4:0];
              id_valid = f[0];
              id_uses_rs1 = f[1];
              id_uses_rs2 = f[2];
              ex_valid = f[3];
              ex_mem_re = f[4];
              check_haz("exh");

            end
          end
        end
      end
    end

    // ------------------------------------------------------
    // Part B: random vectors, full register space
    // ------------------------------------------------------

    for (int n = 0; n < 200000; n++) begin

      logic [31:0] r1, r2;
      r1 = rnd();
      r2 = rnd();

      ex_rs1 = r1[4:0];
      ex_rs2 = r1[9:5];
      exmem_rd = (r1[12:10] == 3'd0) ? r1[4:0] : r1[17:13];       // bias: often equals rs1
      memwb_rd = (r1[20:18] == 3'd0) ? r1[9:5] : r1[25:21];       // bias: often equals rs2
      exmem_valid = r2[0];
      exmem_reg_we = r2[1] | r2[5];
      exmem_is_load = r2[2];
      memwb_valid = r2[3];
      memwb_reg_we = r2[4] | r2[6];
      check_fwd("rnd");

      id_rs1 = r1[4:0];
      id_rs2 = r1[9:5];
      ex_rd = (r1[12:10] == 3'd0) ? r1[4:0] : ((r1[15:13] == 3'd0) ? r1[9:5] : r1[20:16]);
      id_valid = r2[7] | r2[8];
      id_uses_rs1 = r2[9];
      id_uses_rs2 = r2[10];
      ex_valid = r2[11] | r2[12];
      ex_mem_re = r2[13] | r2[14];
      check_haz("rnd");

    end

    $display(
      "PIPE_UNIT_RESULT: %s checks=%0d errors=%0d",
      (errors == 0) ? "PASS" : "FAIL",
      checks,
      errors
    );

    $finish;

  end

endmodule
