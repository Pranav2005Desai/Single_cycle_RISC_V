module id_stage (
    input  logic        clk,
    input  logic        reset,
    input  logic        stall,
    input  logic [31:0] instruction,
    input  logic [31:0] wb_data,
    output logic [31:0] rs1_data,
    output logic [31:0] rs2_data,
    output logic [31:0] imm_out,
    output logic [6:0]  opcode_out_d,
    output logic [6:0]  imm11_5,
    output logic [2:0]  fn3_out_d,
    output logic        fn7_5,
    output logic [2:0]  aluop,
    output logic [1:0]  memtoreg,
    output logic        branch,
    output logic        mem_write,
    output logic        mem_read,
    output logic        alu_src,
    output logic        mux_inp
);
    logic [4:0]  rs1, rs2, rd;
    logic [11:0] imm;
    logic [19:0] imm_uj;
    logic        reg_write;

    decoder u_decoder (
        .instruction(instruction),
        .rs1(rs1), .rs2(rs2), .rd(rd),
        .opcode(opcode_out_d), .imm11_5(imm11_5), .fn3(fn3_out_d),
        .imm(imm), .imm_uj(imm_uj), .fn7_5(fn7_5)
    );

    imm_generator u_imm_gen (
        .imm_input(imm), .fn3(fn3_out_d), .opcode(opcode_out_d),
        .imm_input_uj(imm_uj), .imm_output(imm_out)
    );

    main_control u_main_control (
        .opcode(opcode_out_d), .fn3(fn3_out_d),
        .memtoreg(memtoreg), .branch(branch), .mux_inp(mux_inp),
        .memread(mem_read), .memwrite(mem_write), .alusrc(alu_src),
        .reg_write(reg_write), .aluop(aluop)
    );

    register_file u_regfile (
        .rs1_sel(rs1), .rs2_sel(rs2),
        .reg_write(reg_write && !stall),
        .clk(clk), .reset(reset),
        .wb_data(wb_data), .rd_sel(rd),
        .rs1_data(rs1_data), .rs2_data(rs2_data)
    );
endmodule
