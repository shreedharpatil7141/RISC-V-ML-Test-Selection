// tb_rv_units.sv - Unit tests: rv_alu, rv_branch_cmp, rv_imm_gen, rv_regfile, rv_lsu.
// Expected values are computed with formulations independent of the RTL.
// Deterministic Xorshift32 PRNG is used for reproducible test data.

`timescale 1ns/1ps

module tb_rv_units;

  import rv32_pkg::*;

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

  // ---------- ALU ----------

  word_t a, b, y;
  alu_op_e op;

  rv_alu u_alu (
    .a(a),
    .b(b),
    .op(op),
    .y(y)
  );

  function automatic word_t alu_exp(
    input int k,
    input word_t x,
    input word_t z
  );

    longint sx_, sz_;

    sx_ = longint'($signed(x));
    sz_ = longint'($signed(z));

    case (k)
      0: return word_t'(longint'(x) + longint'(z));
      1: return word_t'(longint'(x) - longint'(z));
      2: return word_t'(longint'(x) * (64'd1 << z[4:0]));
      3: return (sx_ < sz_) ? 32'd1 : 32'd0;
      4: return (longint'(x) < longint'(z)) ? 32'd1 : 32'd0;
      5: return x ^ z;
      6: return word_t'(longint'(x) / (64'd1 << z[4:0]));

      7: begin
        longint d;
        d = 64'd1 << z[4:0];

        if (sx_ >= 0)
          return word_t'(sx_ / d);
        else
          return word_t'(-((-sx_ + d - 1) / d));
      end

      8: return x | z;
      9: return x & z;

      default: return 32'h0;
    endcase

  endfunction

  localparam int NC = 8;

  word_t corners [NC] = '{
    32'h00000000,
    32'h00000001,
    32'hFFFFFFFF,
    32'h7FFFFFFF,
    32'h80000000,
    32'h0000001F,
    32'h00000020,
    32'hDEADBEEF
  };


  // ---------- Branch compare ----------

  logic [2:0] bf3;
  logic btaken;

  rv_branch_cmp u_bc (
    .a(a),
    .b(b),
    .funct3(bf3),
    .taken(btaken)
  );


  // ---------- Immediate generator ----------

  word_t insn, imm;

  rv_imm_gen u_imm (
    .insn(insn),
    .imm(imm)
  );


  // ---------- Register file ----------

  logic rf_we;
  reg_t waddr, ra1, ra2;
  word_t wdata, rd1, rd2;

  logic clk = 0;

  always #5 clk = ~clk;

  rv_regfile u_rf (
    .clk(clk),
    .we(rf_we),
    .waddr(waddr),
    .wdata(wdata),
    .rs1_addr(ra1),
    .rs2_addr(ra2),
    .rs1_data(rd1),
    .rs2_data(rd2)
  );


  // ---------- Load/store unit ----------

  logic [2:0] lf3;
  logic l_ld, l_st;

  word_t laddr, lsdata, lrdata;
  word_t lwdata, lload;

  logic [3:0] lbe;
  logic lmis;

  rv_lsu u_lsu (
    .funct3(lf3),
    .is_load(l_ld),
    .is_store(l_st),
    .addr(laddr),
    .store_data(lsdata),
    .mem_rdata(lrdata),
    .be(lbe),
    .mem_wdata(lwdata),
    .load_data(lload),
    .misaligned(lmis)
  );


  // ---------- Shadow register file ----------

  word_t shadow [32];


  // ---------- Deterministic Xorshift32 PRNG ----------

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


  // ============================================================
  // TEST EXECUTION
  // ============================================================

  initial begin

    // Initialize deterministic PRNG.
    rng_state = 32'h00005eed;


    // ----------------------------------------------------------
    // ALU TESTS
    // Corners x corners x operations, plus random tests.
    // ----------------------------------------------------------

    for (int k = 0; k < 10; k++) begin

      op = alu_op_e'(k);

      for (int i = 0; i < NC; i++) begin
        for (int j = 0; j < NC; j++) begin

          a = corners[i];
          b = corners[j];

          #1;

          chk(
            y === alu_exp(k, a, b),
            $sformatf(
              "ALU op=%0d a=%h b=%h got=%h exp=%h",
              k, a, b, y, alu_exp(k, a, b)
            )
          );

        end
      end

      for (int n = 0; n < 2000; n++) begin

        a = rnd();
        b = rnd();

        #1;

        chk(
          y === alu_exp(k, a, b),
          $sformatf(
            "ALU op=%0d a=%h b=%h got=%h exp=%h",
            k, a, b, y, alu_exp(k, a, b)
          )
        );

      end

    end


    // ----------------------------------------------------------
    // BRANCH COMPARATOR TESTS
    // ----------------------------------------------------------

    for (int n = 0; n < 4000; n++) begin

      logic exp_t;

      a = (n < NC*NC) ? corners[n % NC] : rnd();

      b = (n < NC*NC)
          ? corners[(n / NC) % NC]
          : ((n % 7 == 0) ? a : rnd());

      for (int f = 0; f < 8; f++) begin

        bf3 = f[2:0];

        #1;

        case (f)

          0: exp_t = (a == b);
          1: exp_t = (a != b);

          4: exp_t =
            (longint'($signed(a)) < longint'($signed(b)));

          5: exp_t =
            (longint'($signed(a)) >= longint'($signed(b)));

          6: exp_t =
            (longint'(a) < longint'(b));

          7: exp_t =
            (longint'(a) >= longint'(b));

          default: exp_t = 1'b0;

        endcase

        chk(
          btaken === exp_t,
          $sformatf(
            "BR f3=%0d a=%h b=%h",
            f, a, b
          )
        );

      end

    end


    // ----------------------------------------------------------
    // IMMEDIATE GENERATOR TESTS
    // ----------------------------------------------------------

    for (int n = 0; n < 5000; n++) begin

      logic [31:0] r;
      logic [11:0] i12;
      logic [12:0] b13;
      logic [20:0] j21;
      logic [19:0] u20;

      reg_t f_rd, f_rs1, f_rs2;
      logic [2:0] f3_;

      r = rnd();

      i12 = r[11:0];
      b13 = {r[12:1], 1'b0};
      j21 = {r[20:1], 1'b0};
      u20 = r[31:12];

      f_rd  = reg_t'(rnd());
      f_rs1 = reg_t'(rnd());
      f_rs2 = reg_t'(rnd());
      f3_   = 3'(rnd());


      // I-type: OP-IMM

      insn = {
        i12, f_rs1, f3_, f_rd, OPC_OP_IMM
      };

      #1;

      chk(
        imm === {{20{i12[11]}}, i12},
        $sformatf("IMM I %h", insn)
      );


      // I-type: LOAD

      insn = {
        i12, f_rs1, f3_, f_rd, OPC_LOAD
      };

      #1;

      chk(
        imm === {{20{i12[11]}}, i12},
        $sformatf("IMM L %h", insn)
      );


      // I-type: JALR

      insn = {
        i12, f_rs1, f3_, f_rd, OPC_JALR
      };

      #1;

      chk(
        imm === {{20{i12[11]}}, i12},
        $sformatf("IMM JR %h", insn)
      );


      // S-type

      insn = {
        i12[11:5],
        f_rs2,
        f_rs1,
        f3_,
        i12[4:0],
        OPC_STORE
      };

      #1;

      chk(
        imm === {{20{i12[11]}}, i12},
        $sformatf("IMM S %h", insn)
      );


      // B-type

      insn = {
        b13[12],
        b13[10:5],
        f_rs2,
        f_rs1,
        f3_,
        b13[4:1],
        b13[11],
        OPC_BRANCH
      };

      #1;

      chk(
        imm === {{19{b13[12]}}, b13},
        $sformatf("IMM B %h", insn)
      );


      // U-type: LUI

      insn = {
        u20, f_rd, OPC_LUI
      };

      #1;

      chk(
        imm === {u20, 12'h000},
        $sformatf("IMM LUI %h", insn)
      );


      // U-type: AUIPC

      insn = {
        u20, f_rd, OPC_AUIPC
      };

      #1;

      chk(
        imm === {u20, 12'h000},
        $sformatf("IMM AUIPC %h", insn)
      );


      // J-type: JAL

      insn = {
        j21[20],
        j21[10:1],
        j21[11],
        j21[19:12],
        f_rd,
        OPC_JAL
      };

      #1;

      chk(
        imm === {{11{j21[20]}}, j21},
        $sformatf("IMM J %h", insn)
      );

    end


    // ----------------------------------------------------------
    // REGISTER FILE TESTS
    // ----------------------------------------------------------

    for (int i = 0; i < 32; i++)
      shadow[i] = 32'h00000000;

    rf_we = 0;
    waddr = 0;
    wdata = 0;
    ra1 = 0;
    ra2 = 0;

    for (int n = 0; n < 3000; n++) begin

      @(negedge clk);

      waddr = reg_t'(rnd());
      wdata = rnd();

      rf_we = (rnd() % 4 != 0);

      ra1 = (n % 5 == 0)
            ? waddr
            : reg_t'(rnd());

      ra2 = reg_t'(rnd());

      #1;

      // Asynchronous read: check old value before write edge.

      chk(
        rd1 === shadow[ra1] &&
        rd2 === shadow[ra2],
        $sformatf("RF read-before-write n=%0d", n)
      );

      @(posedge clk);

      #1;

      if (rf_we && waddr != 0)
        shadow[waddr] = wdata;

      chk(
        rd1 === shadow[ra1] &&
        rd2 === shadow[ra2],
        $sformatf("RF read-after-write n=%0d", n)
      );

      chk(
        rd1 !== 32'bx,
        "RF x-check"
      );

    end

    chk(1'b1, "regfile ran");

    ra1 = 0;
    ra2 = 0;

    #1;

    chk(
      rd1 === 32'h00000000 &&
      rd2 === 32'h00000000,
      "RF x0 reads zero"
    );


    // ----------------------------------------------------------
    // LOAD/STORE UNIT TESTS
    // ----------------------------------------------------------

    for (int n = 0; n < 6000; n++) begin

      int sz;
      int ofs;

      word_t exp_w;
      word_t exp_ld;

      logic [3:0] exp_be;
      bit exp_mis;


      // Select load/store width.

      lf3 = ((n % 3) == 0)
            ? 3'b000
            : ((n % 3) == 1)
              ? 3'b001
              : 3'b010;


      // Include unsigned load variants.

      if ((n % 2) == 1) begin

        case (n % 5)

          0: lf3 = 3'b100;
          1: lf3 = 3'b101;

          default: ;

        endcase

      end


      laddr  = rnd();
      lsdata = rnd();
      lrdata = rnd();

      l_ld = (n % 2) == 1;
      l_st = !l_ld;

      #1;

      ofs = int'(laddr[1:0]);

      sz = (lf3[1:0] == 2'd0)
           ? 1
           : (lf3[1:0] == 2'd1)
             ? 2
             : 4;

      exp_mis = (ofs % sz) != 0;


      chk(
        lmis === exp_mis,
        $sformatf(
          "LSU misalign f3=%0d addr=%h",
          lf3, laddr
        )
      );


      // STORE TESTS

      if (l_st && !exp_mis) begin

        exp_be = 4'b0000;
        exp_w = 32'h00000000;

        for (int k = 0; k < sz; k++) begin

          exp_be[ofs + k] = 1'b1;

          exp_w[8*(ofs + k) +: 8] =
            lsdata[8*k +: 8];

        end


        chk(
          lbe === exp_be,
          $sformatf(
            "LSU be f3=%0d ofs=%0d got=%b exp=%b",
            lf3, ofs, lbe, exp_be
          )
        );


        // Only enabled lanes must match.

        for (int k = 0; k < 4; k++) begin

          if (exp_be[k]) begin

            chk(
              lwdata[8*k +: 8] === exp_w[8*k +: 8],
              $sformatf(
                "LSU wdata lane %0d f3=%0d ofs=%0d",
                k, lf3, ofs
              )
            );

          end

        end

      end


      // LOAD TESTS

      if (l_ld && !exp_mis) begin

        logic [31:0] raw;

        raw = 32'h00000000;

        for (int k = 0; k < sz; k++) begin

          raw[8*k +: 8] =
            lrdata[8*(ofs + k) +: 8];

        end


        case (lf3)

          3'b000:
            exp_ld = {{24{raw[7]}}, raw[7:0]};

          3'b001:
            exp_ld = {{16{raw[15]}}, raw[15:0]};

          3'b010:
            exp_ld = raw;

          3'b100:
            exp_ld = {24'h000000, raw[7:0]};

          3'b101:
            exp_ld = {16'h0000, raw[15:0]};

          default:
            exp_ld = raw;

        endcase


        chk(
          lload === exp_ld,
          $sformatf(
            "LSU load f3=%0d addr=%h rdata=%h got=%h exp=%h",
            lf3, laddr, lrdata, lload, exp_ld
          )
        );

      end

    end


    // LSU idle check.

    l_ld = 0;
    l_st = 0;
    lf3 = 3'b010;
    laddr = 32'h00000001;

    #1;

    chk(
      lmis === 1'b0,
      "LSU no misalign when idle"
    );


    // ----------------------------------------------------------
    // FINAL RESULT
    // ----------------------------------------------------------

    $display(
      "UNIT_RESULT: %s checks=%0d errors=%0d",
      (errors == 0) ? "PASS" : "FAIL",
      checks,
      errors
    );

    $finish;

  end

endmodule