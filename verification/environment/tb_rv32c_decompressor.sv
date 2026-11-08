`timescale 1ns/1ps
module tb_rv32c_decompressor;
  logic [15:0] raw_halfword;
  logic [31:0] expanded_insn;
  logic [7:0] length_bits;
  logic is_compressed, is_32bit_prefix, unsupported_length, illegal, hint;
  string vector_path;
  integer fd, rc, count, mismatches;
  integer legal_count, hint_count, illegal_count, prefix32_count, unsupported_count;
  integer anchor_count;
  logic [15:0] exp_raw;
  logic [7:0] exp_length;
  logic exp_compressed, exp_prefix32, exp_unsupported, exp_illegal, exp_hint;
  logic [31:0] exp_expanded;
  bit terminal_emitted;

  rv32c_decompressor dut (.*);

  task automatic fail_and_fatal(input string reason);
    begin
      if (!terminal_emitted) begin
        terminal_emitted = 1'b1;
        $display("RV32C_DECOMPRESS_UNIT FAIL halfwords=%0d mismatches=%0d anchors=%0d reason=%s",
          count, mismatches, anchor_count, reason);
      end
      $fatal(1, "RV32C_DECOMPRESS_UNIT fatal: %s", reason);
    end
  endtask

  task automatic check_anchor(input logic [15:0] raw,
      input logic [31:0] expanded, input logic expected_illegal,
      input logic expected_hint, input logic expected_compressed,
      input logic expected_prefix32, input logic expected_unsupported,
      input logic [7:0] expected_length);
    begin
      raw_halfword = raw;
      #1;
      anchor_count = anchor_count + 1;
      if (expanded_insn !== expanded || illegal !== expected_illegal ||
          hint !== expected_hint || is_compressed !== expected_compressed ||
          is_32bit_prefix !== expected_prefix32 ||
          unsupported_length !== expected_unsupported ||
          length_bits !== expected_length) begin
        mismatches = mismatches + 1;
        $display("ANCHOR_DIFF raw=%04x expected_exp=%08x expected_ill=%0b expected_hint=%0b expected_c=%0b expected_32=%0b expected_unsup=%0b expected_len=%0d actual_exp=%08x actual_ill=%0b actual_hint=%0b actual_c=%0b actual_32=%0b actual_unsup=%0b actual_len=%0d",
          raw, expanded, expected_illegal, expected_hint, expected_compressed,
          expected_prefix32, expected_unsupported, expected_length,
          expanded_insn, illegal, hint, is_compressed, is_32bit_prefix,
          unsupported_length, length_bits);
      end
    end
  endtask

  initial begin
    count = 0; mismatches = 0; anchor_count = 0;
    legal_count = 0; hint_count = 0; illegal_count = 0;
    prefix32_count = 0; unsupported_count = 0;
    terminal_emitted = 1'b0;
    if (!$value$plusargs("VECTORS=%s", vector_path)) begin
      fail_and_fatal("missing +VECTORS path");
    end
    fd = $fopen(vector_path, "r");
    if (fd == 0) begin
      fail_and_fatal("cannot open vector file");
    end
    while (!$feof(fd)) begin
      rc = $fscanf(fd, "%h %h %d %d %d %d %d %h\n",
        exp_raw, exp_length, exp_compressed, exp_prefix32,
        exp_unsupported, exp_illegal, exp_hint, exp_expanded);
      if (rc == 8) begin
        if (exp_raw !== count[15:0]) begin
          fail_and_fatal("vector ordering/coverage error");
        end
        raw_halfword = exp_raw;
        #1;
        count = count + 1;
        if (exp_compressed && exp_illegal) illegal_count = illegal_count + 1;
        else if (exp_compressed && exp_hint) hint_count = hint_count + 1;
        else if (exp_compressed) legal_count = legal_count + 1;
        else if (exp_prefix32) prefix32_count = prefix32_count + 1;
        else if (exp_unsupported) unsupported_count = unsupported_count + 1;
        if (expanded_insn !== exp_expanded || length_bits !== exp_length ||
            is_compressed !== exp_compressed || is_32bit_prefix !== exp_prefix32 ||
            unsupported_length !== exp_unsupported || illegal !== exp_illegal ||
            hint !== exp_hint) begin
          mismatches = mismatches + 1;
          if (mismatches <= 25)
            $display("VECTOR_DIFF n=%0d raw=%04x exp_len=%0d exp_c=%0b exp_32=%0b exp_unsup=%0b exp_illegal=%0b exp_hint=%0b exp_word=%08x got_len=%0d got_c=%0b got_32=%0b got_unsup=%0b got_illegal=%0b got_hint=%0b got_word=%08x",
              count-1, exp_raw, exp_length, exp_compressed, exp_prefix32,
              exp_unsupported, exp_illegal, exp_hint, exp_expanded,
              length_bits, is_compressed, is_32bit_prefix, unsupported_length,
              illegal, hint, expanded_insn);
        end
      end else if (rc != -1) begin
        fail_and_fatal("malformed vector row");
      end
    end
    $fclose(fd);
    if (count != 65536) begin
      fail_and_fatal("vector count is not 65536");
    end

    // Independently hand-derived anchors: expansion, class, and length.
    check_anchor(16'h0001, 32'h00000013, 0, 0, 1, 0, 0, 16); // C.NOP
    check_anchor(16'h0085, 32'h00108093, 0, 0, 1, 0, 0, 16); // C.ADDI x1,1
    check_anchor(16'h0040, 32'h00410413, 0, 0, 1, 0, 0, 16); // C.ADDI4SPN x8,4
    check_anchor(16'h717d, 32'hff010113, 0, 0, 1, 0, 0, 16); // C.ADDI16SP -16
    check_anchor(16'h6405, 32'h00001437, 0, 0, 1, 0, 0, 16); // C.LUI x8,1
    check_anchor(16'h5ffc, 32'h07c7a783, 0, 0, 1, 0, 0, 16); // C.LW x15,124(x15)
    check_anchor(16'hdffe, 32'h0ff12e23, 0, 0, 1, 0, 0, 16); // C.SWSP x31,252
    check_anchor(16'h2009, 32'h002000ef, 0, 0, 1, 0, 0, 16); // C.JAL +2
    check_anchor(16'hc009, 32'h00040163, 0, 0, 1, 0, 0, 16); // C.BEQZ x8,+2
    check_anchor(16'h9282, 32'h000280e7, 0, 0, 1, 0, 0, 16); // C.JALR x5
    check_anchor(16'h8405, 32'h40145413, 0, 0, 1, 0, 0, 16); // C.SRAI x8,1
    check_anchor(16'h0081, 32'h00000013, 0, 1, 1, 0, 0, 16); // C.ADDI HINT
    check_anchor(16'h0000, 32'h00000000, 1, 0, 1, 0, 0, 16); // reserved zero
    check_anchor(16'h0003, 32'h00000000, 0, 0, 0, 1, 0, 32); // 32-bit prefix
    check_anchor(16'h001f, 32'h00000000, 0, 0, 0, 0, 1, 48); // unsupported length
    check_anchor(16'hffff, 32'h00000000, 0, 0, 0, 0, 1, 0);  // >=192-bit prefix

    if (!terminal_emitted) begin
      if (mismatches != 0) begin
        fail_and_fatal("vector or hand-anchor mismatch");
      end else begin
        terminal_emitted = 1'b1;
        $display("RV32C_DECOMPRESS_UNIT PASS halfwords=%0d mismatches=0 anchors=%0d legal=%0d hint=%0d illegal=%0d prefix32=%0d unsupported_length=%0d",
          count, anchor_count, legal_count, hint_count, illegal_count,
          prefix32_count, unsupported_count);
        $finish;
      end
    end
  end
endmodule
