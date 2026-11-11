module alu_control (
    input  logic [2:0] alu_op,
    input  logic [2:0] fn3,
    input  logic [6:0] imm11_5,
    input  logic       fn7_5,
    output logic [4:0] control_out
);
    localparam logic [4:0] ADD  = 5'b00000, SUB  = 5'b00001, XOR  = 5'b00010,
                           OR   = 5'b00011, AND  = 5'b00100, SLL  = 5'b00101,
                           SRL  = 5'b00110, SRA  = 5'b00111, SLT  = 5'b01000,
                           SLTU = 5'b01001, BEQ  = 5'b01010, BNE  = 5'b01011,
                           BLT  = 5'b01100, BGE  = 5'b01101, BLTU = 5'b01110,
                           BGEU = 5'b01111;

    always_comb begin
        control_out = ADD;
        case (alu_op)
            3'b000: case (fn3) // R-type
                3'b000: control_out = fn7_5 ? SUB : ADD;
                3'b001: control_out = SLL;
                3'b010: control_out = SLT;
                3'b011: control_out = SLTU;
                3'b100: control_out = XOR;
                3'b101: control_out = fn7_5 ? SRA : SRL;
                3'b110: control_out = OR;
                3'b111: control_out = AND;
            endcase
            3'b001: case (fn3) // I-type ALU
                3'b000: control_out = ADD;
                3'b001: control_out = SLL;
                3'b010: control_out = SLT;
                3'b011: control_out = SLTU;
                3'b100: control_out = XOR;
                3'b101: control_out = (imm11_5 == 7'h20) ? SRA : SRL;
                3'b110: control_out = OR;
                3'b111: control_out = AND;
            endcase
            3'b100: case (fn3) // Branch
                3'b000:  control_out = BEQ;
                3'b001:  control_out = BNE;
                3'b100:  control_out = BLT;
                3'b101:  control_out = BGE;
                3'b110:  control_out = BLTU;
                3'b111:  control_out = BGEU;
                default: control_out = ADD;
            endcase
            default: control_out = ADD; // load, store, JAL/LUI, other
        endcase
    end
endmodule
