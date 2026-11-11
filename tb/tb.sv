`timescale 1ns/1ps
module tb;
    logic clk = 0, reset = 1, stall = 0;
    logic [31:0] instruction, mem_out, rs2_data, alu_out, address;
    logic mem_write, mem_read;
    logic [2:0] fn3;
    logic [6:0] opcode;

    single_cycle_riscv dut (.*);

    logic [31:0] imem [0:4095];
    logic [7:0]  dmem [0:65535];
    logic [1:0]  ctl  [0:9999];   // {reset, stall} per cycle
    integer ncyc, i, f;

    always #5 clk = ~clk;

    logic [31:0] iidx;
    assign iidx = (address - 32'h8000_0000) >> 2;
    assign instruction = (iidx < 32'd4096) ? imem[iidx[11:0]] : 32'h0000_0013;

    // data memory: little-endian, width/extension by fn3 (core does no load extension)
    logic [15:0] a;
    assign a = alu_out[15:0];
    always_comb begin
        case (fn3)
            3'b000: mem_out = {{24{dmem[a][7]}}, dmem[a]};
            3'b001: mem_out = {{16{dmem[a+1][7]}}, dmem[a+1], dmem[a]};
            3'b100: mem_out = {24'b0, dmem[a]};
            3'b101: mem_out = {16'b0, dmem[a+1], dmem[a]};
            default: mem_out = {dmem[a+3], dmem[a+2], dmem[a+1], dmem[a]};
        endcase
    end
    always_ff @(posedge clk) if (mem_write && !stall && !reset) begin
        dmem[a] <= rs2_data[7:0];
        if (fn3[1:0] != 2'b00) dmem[a+1] <= rs2_data[15:8];
        if (fn3[1:0] == 2'b10) begin dmem[a+2] <= rs2_data[23:16]; dmem[a+3] <= rs2_data[31:24]; end
    end

    initial begin
        for (i = 0; i < 4096; i++) imem[i] = 32'h0000_0013;
        for (i = 0; i < 65536; i++) dmem[i] = 8'h0;
        $readmemh("prog.hex", imem);
        $readmemh("ctl.hex", ctl);
        if (!$value$plusargs("N=%d", ncyc)) ncyc = 200;
        f = $fopen("rtl_trace.txt", "w");
        #1 reset = 1; #10;
        for (i = 0; i < ncyc; i++) begin
            @(negedge clk);
            {reset, stall} = ctl[i];
            #1;
            if (!reset) $fdisplay(f, "%0d %08x", i, address);
        end
        @(posedge clk); #1;
        for (i = 1; i < 32; i++) $fdisplay(f, "x%0d %08x", i, dut.u_id.u_regfile.register[i]);
        for (i = 0; i < 65536; i += 4)
            if ({dmem[i+3],dmem[i+2],dmem[i+1],dmem[i]} != 0)
                $fdisplay(f, "m%04x %02x%02x%02x%02x", i, dmem[i+3],dmem[i+2],dmem[i+1],dmem[i]);
        $fclose(f);
        $finish;
    end
endmodule
