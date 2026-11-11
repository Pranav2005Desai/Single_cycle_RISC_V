module register_file (
    input  logic [4:0]  rs1_sel, rs2_sel,
    input  logic        reg_write,
    input  logic        clk,
    input  logic        reset,
    input  logic [31:0] wb_data,
    input  logic [4:0]  rd_sel,
    output logic [31:0] rs1_data, rs2_data
);
    logic [31:0] register [31:0];

    always_ff @(posedge clk or posedge reset) begin
        if (reset) begin
            for (int i = 0; i < 32; i++) register[i] <= 32'd0;
        end else if (reg_write && rd_sel != 5'd0) begin
            register[rd_sel] <= wb_data;
        end
    end

    assign rs1_data = (rs1_sel == 5'd0) ? 32'd0 : register[rs1_sel];
    assign rs2_data = (rs2_sel == 5'd0) ? 32'd0 : register[rs2_sel];
endmodule
