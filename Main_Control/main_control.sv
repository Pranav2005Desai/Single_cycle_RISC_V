module main_control (
    input  logic [6:0] opcode,
    input  logic [2:0] fn3,        // unused by the control table
    output logic [1:0] memtoreg,
    output logic       branch,
    output logic       mux_inp,
    output logic       memread,
    output logic       memwrite,
    output logic       alusrc,
    output logic       reg_write,
    output logic [2:0] aluop
);
    // {memtoreg, branch, mux_inp, memread, memwrite, alusrc, reg_write, aluop}
    logic [10:0] ctrl;
    assign {memtoreg, branch, mux_inp, memread, memwrite, alusrc, reg_write, aluop} = ctrl;

    always_comb begin
        case (opcode)
            7'b0110011: ctrl = {2'b00, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b1, 3'b000}; // R-type
            7'b0010011: ctrl = {2'b00, 1'b0, 1'b0, 1'b0, 1'b0, 1'b1, 1'b1, 3'b001}; // I-type ALU
            7'b0000011: ctrl = {2'b01, 1'b0, 1'b0, 1'b1, 1'b0, 1'b1, 1'b1, 3'b010}; // Load
            7'b0100011: ctrl = {2'b11, 1'b0, 1'b0, 1'b0, 1'b1, 1'b1, 1'b0, 3'b011}; // Store
            7'b1100011: ctrl = {2'b00, 1'b1, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 3'b100}; // Branch
            7'b1101111: ctrl = {2'b10, 1'b0, 1'b0, 1'b0, 1'b0, 1'b1, 1'b1, 3'b110}; // JAL
            7'b1100111: ctrl = {2'b10, 1'b0, 1'b1, 1'b0, 1'b0, 1'b1, 1'b1, 3'b001}; // JALR
            7'b0110111: ctrl = {2'b10, 1'b0, 1'b0, 1'b0, 1'b0, 1'b1, 1'b1, 3'b110}; // LUI
            7'b0010111: ctrl = {2'b10, 1'b0, 1'b0, 1'b0, 1'b0, 1'b1, 1'b1, 3'b000}; // AUIPC
            default:    ctrl = 11'd0;
        endcase
    end
endmodule
