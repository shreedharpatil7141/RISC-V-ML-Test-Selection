`timescale 1ns/1ps
// Wrapper timing, handshake, reset, back-to-back, and every divider abort position.
module tb_rv_md_exec;
  logic clk=0, rst_n=0, start=0, abort=0;
  logic [2:0] funct3=0;
  logic [31:0] a=0,b=0,y;
  logic ready,accepted,busy,done,aborted;
  integer errors=0, checks=0, abort_checks=0;
  rv_md_exec dut(.clk(clk),.rst_n(rst_n),.start(start),.abort(abort),.funct3(funct3),
                 .a(a),.b(b),.ready(ready),.accepted(accepted),.busy(busy),
                 .done(done),.aborted(aborted),.y(y));
  always #5 clk=~clk;

  task automatic normal_div(input logic [2:0] op,input logic [31:0] x,z,expected);
    integer accepted_count, done_count, busy_count;
    begin
      accepted_count=0; done_count=0; busy_count=0;
      @(negedge clk); funct3=op; a=x; b=z; abort=0; start=1; #1;
      if (!ready || !accepted || !busy || done) begin errors++; $display("FAIL wrapper start"); end
      accepted_count++ ; busy_count++;
      @(posedge clk); #1;
      for (int i=0;i<32;i++) begin
        @(negedge clk);
        if (!busy || done || accepted) begin errors++; $display("FAIL wrapper RUN i=%0d",i); end
        busy_count++;
        if (i==2) start=0; // holding start through early RUN must not cause another acceptance
        @(posedge clk); #1;
      end
      @(negedge clk);
      if (busy || !done || y !== expected) begin errors++; $display("FAIL wrapper FIN op=%0d got=%h expected=%h",op,y,expected); end
      done_count++;
      @(posedge clk); #1;
      if (!ready || busy || done || accepted) begin errors++; $display("FAIL wrapper FIN exit"); end
      if (accepted_count!=1 || done_count!=1 || busy_count!=33) begin
        errors++; $display("FAIL wrapper counts start=%0d done=%0d busy=%0d",accepted_count,done_count,busy_count);
      end
      // Return just after the FIN->IDLE edge. The next normal_div call starts
      // on the very next negedge, checking immediate back-to-back acceptance.
      checks++;
    end
  endtask

  task automatic abort_at(input integer position);
    integer prior_errors;
    begin
      prior_errors=errors;
      @(negedge clk); funct3=3'b100; a=32'h1234_5678; b=7; start=1; abort=0;
      if (position==0) begin
        abort=1; #1;
        if (accepted || busy || done) begin errors++; $display("FAIL abort0 accepted/busy/done"); end
        @(posedge clk); #1;
        if (!ready || done || busy) begin errors++; $display("FAIL abort0 state"); end
        @(negedge clk); start=0; abort=0;
      end else begin
        #1;
        if (!accepted) begin errors++; $display("FAIL abort start position=%0d",position); end
        @(posedge clk); #1; start=0;
        for (int c=1;c<position;c++) begin @(posedge clk); #1; end
        // At C33 the ordinary FIN pulse is present, but abort must suppress it.
        abort=1; #1;
        if (!aborted || done) begin errors++; $display("FAIL abort pulse position=%0d done=%0b aborted=%0b",position,done,aborted); end
        @(posedge clk); #1;
        if (!ready || done || busy) begin errors++; $display("FAIL abort did not return IDLE position=%0d",position); end
        @(negedge clk); abort=0;
      end
      repeat (2) begin
        @(posedge clk); #1;
        if (done || busy || !ready) begin errors++; $display("FAIL stale completion after abort position=%0d",position); end
      end
      checks++; abort_checks++;
      $display("MD_ABORT_BIN: pos=%0d hit=%0d",position,(errors==prior_errors)?1:0);
    end
  endtask

  initial begin
    repeat (3) @(posedge clk); @(negedge clk) rst_n=1;

    // Combinational multiply stays one EX cycle and never starts/occupies divider.
    @(negedge clk); funct3=3'b000; a=7; b=9; start=0; #1;
    if (y!==32'd63 || busy || done || accepted) begin errors++; $display("FAIL MUL wrapper one-cycle"); end
    funct3=3'b001; a=32'hffff_fff9; b=2; #1;
    if (y!==32'hffff_ffff || busy || done) begin errors++; $display("FAIL MULH wrapper"); end
    funct3=3'b010; a=32'h8000_0000; b=32'hffff_ffff; #1;
    if (y!==32'h8000_0000 || busy || done) begin errors++; $display("FAIL MULHSU wrapper"); end
    funct3=3'b011; a=32'hffff_ffff; b=32'hffff_ffff; #1;
    if (y!==32'hffff_fffe || busy || done) begin errors++; $display("FAIL MULHU wrapper"); end
    checks += 4;

    normal_div(3'b100,32'hffff_ff9c,7,32'hffff_fff2); // -100 / 7 = -14
    normal_div(3'b110,32'hffff_ff9c,7,32'hffff_fffe); // -100 % 7 = -2
    normal_div(3'b101,32'hffff_ff9c,7,32'h2492_4916);
    normal_div(3'b111,32'hffff_ff9c,7,2);
    normal_div(3'b100,32'h8000_0000,32'hffff_ffff,32'h8000_0000);
    normal_div(3'b110,32'h8000_0000,32'hffff_ffff,0);
    normal_div(3'b100,32'h8765_4321,0,32'hffff_ffff);
    normal_div(3'b110,32'h8765_4321,0,32'h8765_4321);
    // Adjacent accepted operations: no extra dead cycle between FIN and next IDLE start.
    normal_div(3'b100,100,9,11);
    normal_div(3'b110,100,9,1);

    // Reset while active clears the partial operation and prevents stale done.
    @(negedge clk); funct3=3'b100; a=12345; b=19; start=1; abort=0;
    @(posedge clk); #1; start=0;
    repeat (7) @(posedge clk);
    @(negedge clk) rst_n=0; #1;
    if (!ready || busy || done) begin errors++; $display("FAIL reset did not clear divider"); end
    @(posedge clk); #1; @(negedge clk) rst_n=1;
    repeat (3) begin @(posedge clk); #1; if (done || busy) begin errors++; $display("FAIL reset stale done"); end end
    checks++;

    for (int pos=0; pos<=33; pos++) abort_at(pos);
    $display("MD_EXEC_RESULT: %s checks=%0d errors=%0d abort_positions=%0d",errors==0?"PASS":"FAIL",checks,errors,abort_checks);
    $finish;
  end
endmodule
