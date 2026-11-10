`timescale 1ns/1ps
// Fixed-latency radix-2 restoring divider. No early-out or fused operation.
module rv_div_iter #(
  parameter int W = 32,
  parameter int COUNT_W = (W < 2) ? 1 : $clog2(W)
) (
  input  logic             clk,
  input  logic             rst_n,
  input  logic             start,
  input  logic             abort,
  input  logic [2:0]       funct3,       // 100 DIV, 101 DIVU, 110 REM, 111 REMU
  input  logic [W-1:0]     dividend,
  input  logic [W-1:0]     divisor,
  output logic             ready,
  output logic             accepted,
  output logic             busy,         // start-accept cycle plus all RUN cycles
  output logic             done,         // one FIN cycle, suppressed by abort
  output logic             aborted,      // active accepted operation aborted this cycle
  output logic [W-1:0]     result
);
  localparam logic [1:0] S_IDLE = 2'd0, S_RUN = 2'd1, S_FIN = 2'd2;
  logic [1:0] state;
  logic [COUNT_W-1:0] iteration;
  logic quotient_mode_q;
  logic negate_quotient_q, negate_remainder_q;
  logic divide_zero_q, signed_overflow_q;
  logic [W-1:0] dividend_orig_q, divisor_abs_q, quotient_q, remainder_q;
  logic [W:0] shifted_remainder, divisor_ext, remainder_next;
  logic [W-1:0] quotient_next;

  assign ready    = (state == S_IDLE);
  assign accepted = ready && start && !abort;
  assign busy     = ((state == S_RUN) || accepted) && !abort;
  assign done     = (state == S_FIN) && !abort;
  assign aborted  = abort && (state != S_IDLE);

  always_comb begin
    shifted_remainder = {remainder_q[W-1:0], quotient_q[W-1]};
    divisor_ext       = {1'b0, divisor_abs_q};
    remainder_next    = shifted_remainder;
    quotient_next     = {quotient_q[W-2:0], 1'b0};
    if (shifted_remainder >= divisor_ext) begin
      remainder_next = shifted_remainder - divisor_ext;
      quotient_next[0] = 1'b1;
    end

    if (divide_zero_q) begin
      result = quotient_mode_q ? {W{1'b1}} : dividend_orig_q;
    end else if (signed_overflow_q) begin
      result = quotient_mode_q ? {1'b1, {(W-1){1'b0}}} : {W{1'b0}};
    end else if (quotient_mode_q) begin
      result = negate_quotient_q ? -quotient_q : quotient_q;
    end else begin
      result = negate_remainder_q ? -remainder_q : remainder_q;
    end
  end

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state              <= S_IDLE;
      iteration          <= '0;
      quotient_mode_q    <= 1'b0;
      negate_quotient_q  <= 1'b0;
      negate_remainder_q <= 1'b0;
      divide_zero_q      <= 1'b0;
      signed_overflow_q  <= 1'b0;
      dividend_orig_q    <= '0;
      divisor_abs_q      <= '0;
      quotient_q         <= '0;
      remainder_q        <= '0;
    end else if (abort) begin
      // Abort wins in IDLE, RUN, and FIN. FIN's done is suppressed combinationally.
      state              <= S_IDLE;
      iteration          <= '0;
      divide_zero_q      <= 1'b0;
      signed_overflow_q  <= 1'b0;
    end else begin
      case (state)
        S_IDLE: if (start) begin
          quotient_mode_q    <= !funct3[1];
          negate_quotient_q  <= !funct3[0] && (dividend[W-1] ^ divisor[W-1]);
          negate_remainder_q <= !funct3[0] && dividend[W-1];
          divide_zero_q      <= (divisor == '0);
          signed_overflow_q  <= !funct3[0] &&
                                (dividend == {1'b1, {(W-1){1'b0}}}) &&
                                (divisor == {W{1'b1}});
          dividend_orig_q    <= dividend;
          divisor_abs_q      <= (!funct3[0] && divisor[W-1]) ? -divisor : divisor;
          quotient_q         <= (!funct3[0] && dividend[W-1]) ? -dividend : dividend;
          remainder_q        <= '0;
          iteration          <= '0;
          state              <= S_RUN;
        end
        S_RUN: begin
          quotient_q  <= quotient_next;
          remainder_q <= remainder_next[W-1:0];
          if (iteration == W-1) begin
            state <= S_FIN;
          end else begin
            iteration <= iteration + 1'b1;
          end
        end
        S_FIN: state <= S_IDLE;
        default: state <= S_IDLE;
      endcase
    end
  end
endmodule
