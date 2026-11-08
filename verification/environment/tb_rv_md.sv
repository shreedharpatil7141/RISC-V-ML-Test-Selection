`timescale 1ns/1ps
// Independent reference: shift/add multiplication and restoring division.
// No multiplication, division, or remainder operators are used in the model.
module tb_rv_md;
  logic [2:0] f3;
  logic [31:0] a, b, y;
  logic [31:0] vectors [0:11];
  int errors=0, checks=0;
  rv_md_comb dut(.funct3(f3),.a(a),.b(b),.y(y));

  function automatic logic [63:0] mul_ref(input logic [63:0] x,input logic [63:0] z);
    logic [63:0] acc, shifted;
    acc=0; shifted=x;
    for(int i=0;i<64;i++) begin
      if(z[i]) acc=acc+shifted;
      shifted=shifted<<1;
    end
    return acc;
  endfunction

  function automatic logic [31:0] md_ref(input logic [2:0] op,input logic [31:0] x,input logic [31:0] z);
    logic [63:0] xx,zz,p;
    logic [31:0] nx,nz,q,r;
    logic [32:0] rem_ext;
    logic negq, negr;
    xx={{32{x[31]}},x}; zz={{32{z[31]}},z};
    case(op)
      0: begin p=mul_ref({32'b0,x},{32'b0,z}); return p[31:0]; end
      1: begin p=mul_ref(xx,zz); return p[63:32]; end
      2: begin p=mul_ref(xx,{32'b0,z}); return p[63:32]; end
      3: begin p=mul_ref({32'b0,x},{32'b0,z}); return p[63:32]; end
      default: begin
        if(op==4 || op==6) begin nx=x[31]?((~x)+1'b1):x; nz=z[31]?((~z)+1'b1):z; end
        else begin nx=x; nz=z; end
        if(nz==0) begin if(op==4||op==5) return 32'hffff_ffff; else return x; end
        if((op==4||op==6) && x==32'h8000_0000 && z==32'hffff_ffff) begin
          if(op==4) return 32'h8000_0000; else return 0;
        end
        q=0; r=0;
        for(int i=31;i>=0;i--) begin
          rem_ext={r, nx[i]};
          if(rem_ext >= {1'b0,nz}) begin rem_ext=rem_ext-{1'b0,nz}; q[i]=1'b1; end
          r=rem_ext[31:0];
        end
        negq=(x[31]^z[31]) && (op==4);
        negr=x[31] && (op==6);
        if(op==4) return negq ? ((~q)+1'b1) : q;
        if(op==5) return q;
        if(op==6) return negr ? ((~r)+1'b1) : r;
        return r;
      end
    endcase
  endfunction

  task automatic check(input logic [2:0] op,input logic [31:0] x,z);
    logic [31:0] expected;
    expected=md_ref(op,x,z); f3=op; a=x; b=z; #1; checks++;
    if(y !== expected) begin errors++; $display("FAIL md op=%0d a=%h b=%h got=%h exp=%h",op,x,z,y,expected); end
  endtask

  initial begin
    vectors[0]=0; vectors[1]=1; vectors[2]=32'hffff_ffff; // 0, +1, -1 / unsigned max
    vectors[3]=32'h8000_0000; vectors[4]=32'h7fff_ffff;
    vectors[5]=32'hffff_fffe; vectors[6]=32'h0000_0002;
    vectors[7]=32'h4000_0000; vectors[8]=32'hc000_0000;
    vectors[9]=32'h0000_ffff; vectors[10]=32'hffff_0000; vectors[11]=32'h8000_0001;
    // Cartesian edge matrix exercises every operation, sign pairing and product boundary.
    for(int i=0;i<12;i++) for(int j=0;j<12;j++)
      for(int op=0;op<8;op++) check(op[2:0],vectors[i],vectors[j]);
    $display("MD_UNIT_RESULT: %s checks=%0d errors=%0d",errors==0?"PASS":"FAIL",checks,errors);
    $finish;
  end
endmodule
