`timescale 1ns/1ps
// Exhaustive W=8 and boundary/deterministic-random W=32 divider verification.
module tb_rv_div_iter;
  logic clk = 1'b0;
  logic rst_n = 1'b0;
  always #5 clk = ~clk;

  logic start8, abort8; logic [2:0] op8; logic [7:0] a8, b8, y8;
  logic ready8, accepted8, busy8, done8, aborted8;
  logic start32, abort32; logic [2:0] op32; logic [31:0] a32, b32, y32;
  logic ready32, accepted32, busy32, done32, aborted32;
  integer errors8 = 0, errors32 = 0;
  integer checks8 = 0, checks32 = 0;

  rv_div_iter #(.W(8)) u8 (
    .clk(clk), .rst_n(rst_n), .start(start8), .abort(abort8), .funct3(op8),
    .dividend(a8), .divisor(b8), .ready(ready8), .accepted(accepted8),
    .busy(busy8), .done(done8), .aborted(aborted8), .result(y8)
  );
  rv_div_iter #(.W(32)) u32 (
    .clk(clk), .rst_n(rst_n), .start(start32), .abort(abort32), .funct3(op32),
    .dividend(a32), .divisor(b32), .ready(ready32), .accepted(accepted32),
    .busy(busy32), .done(done32), .aborted(aborted32), .result(y32)
  );

  function automatic logic [7:0] ref8(input logic [2:0] op, input logic [7:0] a, b);
    integer signed sa, sb, signed_value;
    integer unsigned ua, ub, unsigned_value;
    begin
      if (op[0] == 1'b0) begin
        sa = {24'b0,a}; if (a[7]) sa = sa - 256;
        sb = {24'b0,b}; if (b[7]) sb = sb - 256;
        if (b == 0) begin
          if (!op[1]) return 8'hff;
          else return a;
        end
        if (op[1] && a == 8'h80 && b == 8'hff) return 8'h00;
        if (!op[1] && a == 8'h80 && b == 8'hff) return 8'h80;
        signed_value = op[1] ? (sa % sb) : (sa / sb);
        return signed_value[7:0];
      end else begin
        ua = integer'(a); ub = integer'(b);
        if (ub == 0) begin
          if (!op[1]) return 8'hff;
          else return a;
        end
        unsigned_value = op[1] ? (ua % ub) : (ua / ub);
        return unsigned_value[7:0];
      end
    end
  endfunction

  function automatic logic [31:0] ref32(input logic [2:0] op, input logic [31:0] a, b);
    longint signed sa, sb, signed_value;
    longint unsigned ua, ub, unsigned_value;
    begin
      if (op[0] == 1'b0) begin
        sa = $signed({{32{a[31]}},a});
        sb = $signed({{32{b[31]}},b});
        if (b == 0) begin
          if (!op[1]) return 32'hffff_ffff;
          else return a;
        end
        if (op[1] && a == 32'h8000_0000 && b == 32'hffff_ffff) return 32'h0000_0000;
        if (!op[1] && a == 32'h8000_0000 && b == 32'hffff_ffff) return 32'h8000_0000;
        signed_value = op[1] ? (sa % sb) : (sa / sb);
        return signed_value[31:0];
      end else begin
        ua = {32'b0, a}; ub = {32'b0, b};
        if (ub == 0) begin
          if (!op[1]) return 32'hffff_ffff;
          else return a;
        end
        unsigned_value = op[1] ? (ua % ub) : (ua / ub);
        return unsigned_value[31:0];
      end
    end
  endfunction

  task automatic transact8(input logic [2:0] op, input logic [7:0] a, b);
    logic [7:0] expected;
    begin
      expected = ref8(op, a, b);
      @(negedge clk); op8=op; a8=a; b8=b; start8=1; abort8=0; #1;
      if (!accepted8 || !busy8 || done8) begin errors8++; $display("FAIL W8 accept op=%0d a=%h b=%h",op,a,b); end
      @(posedge clk); #1; start8=0;
      @(negedge clk); a8=~a; b8=~b; op8=op ^ 3'b001; // live pins must not affect latched operation
      for (int k=0; k<8; k++) begin
        if (!busy8 || done8 || accepted8) begin errors8++; $display("FAIL W8 RUN timing op=%0d a=%h b=%h iter=%0d",op,a,b,k); end
        @(posedge clk); #1;
      end
      @(negedge clk);
      checks8++;
      if (!done8 || busy8 || y8 !== expected) begin
        errors8++; $display("FAIL W8 result/timing op=%0d a=%h b=%h got=%h exp=%h",op,a,b,y8,expected);
      end
      @(posedge clk); #1;
      if (!ready8 || done8 || busy8 || accepted8) begin errors8++; $display("FAIL W8 FIN exit"); end
    end
  endtask

  task automatic transact32(input logic [2:0] op, input logic [31:0] a, b);
    logic [31:0] expected;
    begin
      expected = ref32(op, a, b);
      @(negedge clk); op32=op; a32=a; b32=b; start32=1; abort32=0; #1;
      if (!accepted32 || !busy32 || done32) begin errors32++; $display("FAIL W32 accept op=%0d a=%h b=%h",op,a,b); end
      @(posedge clk); #1; start32=0;
      @(negedge clk); a32=~a; b32=~b; op32=op ^ 3'b001;
      for (int k=0; k<32; k++) begin
        if (!busy32 || done32 || accepted32) begin errors32++; $display("FAIL W32 RUN timing op=%0d iter=%0d",op,k); end
        @(posedge clk); #1;
      end
      @(negedge clk);
      checks32++;
      if (!done32 || busy32 || y32 !== expected) begin
        errors32++; $display("FAIL W32 result/timing op=%0d a=%h b=%h got=%h exp=%h",op,a,b,y32,expected);
      end
      @(posedge clk); #1;
      if (!ready32 || done32 || busy32 || accepted32) begin errors32++; $display("FAIL W32 FIN exit"); end
    end
  endtask

  task automatic run_exhaustive8;
    begin
      for (int a=0; a<256; a++)
        for (int b=0; b<256; b++)
          for (int op=4; op<8; op++) transact8(op[2:0], a[7:0], b[7:0]);
    end
  endtask

  task automatic run_wide32;
    logic [31:0] v[0:11];
    logic [31:0] rng, ra, rb;
    begin
      v[0]=0; v[1]=1; v[2]=32'hffff_ffff; v[3]=32'h8000_0000;
      v[4]=32'h7fff_ffff; v[5]=32'hffff_fffe; v[6]=2; v[7]=32'h4000_0000;
      v[8]=32'hc000_0000; v[9]=32'h0000_ffff; v[10]=32'hffff_0000; v[11]=32'h8000_0001;
      for (int i=0; i<12; i++) for (int j=0; j<12; j++)
        for (int op=4; op<8; op++) transact32(op[2:0], v[i], v[j]);
      rng=32'h5eed_3141;
      for (int i=0; i<256; i++) begin
        rng = rng * 32'd1664525 + 32'd1013904223; ra=rng;
        rng = rng * 32'd1664525 + 32'd1013904223; rb=rng;
        for (int op=4; op<8; op++) transact32(op[2:0], ra, rb);
      end
    end
  endtask

  initial begin
    start8=0; abort8=0; op8=4; a8=0; b8=0;
    start32=0; abort32=0; op32=4; a32=0; b32=0;
    repeat (3) @(posedge clk);
    @(negedge clk) rst_n=1;
    fork
      run_exhaustive8();
      run_wide32();
    join
    $display("DIV_ITER_RESULT: %s W8_checks=%0d W8_errors=%0d W32_checks=%0d W32_errors=%0d",
             (errors8==0 && errors32==0) ? "PASS" : "FAIL", checks8, errors8, checks32, errors32);
    $finish;
  end
endmodule
