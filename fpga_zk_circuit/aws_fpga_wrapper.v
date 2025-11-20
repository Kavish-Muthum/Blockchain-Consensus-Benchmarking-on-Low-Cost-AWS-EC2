/*
 * AWS FPGA Shell Wrapper
 * 
 * This wraps the ZK arithmetic circuit to interface with AWS FPGA Shell.
 * The AWS FPGA Shell provides a standardized interface for custom logic.
 */

module cl_zk_arithmetic (
    input wire [1:0] sh_cl_rst,
    input wire sh_cl_clk_500,
    
    // AWS FPGA Shell Interface (simplified)
    input wire [31:0] cl_sh_awaddr,
    input wire cl_sh_awvalid,
    output reg sh_cl_awready,
    
    input wire [31:0] cl_sh_wdata,
    input wire cl_sh_wvalid,
    output reg sh_cl_wready,
    
    output reg [31:0] sh_cl_rdata,
    output reg sh_cl_rvalid,
    input wire cl_sh_rready,
    
    // Custom ZK interface
    output reg zk_done,
    output reg [255:0] zk_result
);

    // Instantiate ZK arithmetic module
    wire zk_start;
    wire [255:0] zk_a, zk_b, zk_modulus;
    wire [1:0] zk_op;
    wire zk_result_valid;
    wire [255:0] zk_result_internal;
    
    zk_arithmetic zk_core (
        .clk(sh_cl_clk_500),
        .rst_n(~sh_cl_rst[0]),
        .start(zk_start),
        .done(zk_done),
        .a(zk_a),
        .b(zk_b),
        .modulus(zk_modulus),
        .op(zk_op),
        .result(zk_result_internal),
        .result_valid(zk_result_valid)
    );
    
    // Simple register interface
    // Register map:
    // 0x00: Control (start operation)
    // 0x04: Operation select
    // 0x08-0x0F: Input A (256 bits = 8 x 32-bit registers)
    // 0x10-0x17: Input B
    // 0x18-0x1F: Modulus
    // 0x20-0x27: Result (read-only)
    // 0x28: Status (read-only)
    
    reg [31:0] reg_control;
    reg [1:0] reg_op;
    reg [255:0] reg_a, reg_b, reg_modulus;
    
    assign zk_start = reg_control[0];
    assign zk_op = reg_op;
    assign zk_a = reg_a;
    assign zk_b = reg_b;
    assign zk_modulus = reg_modulus;
    
    always @(posedge sh_cl_clk_500) begin
        if (sh_cl_rst[0]) begin
            reg_control <= 32'b0;
            reg_op <= 2'b0;
            reg_a <= 256'b0;
            reg_b <= 256'b0;
            reg_modulus <= 256'b0;
            sh_cl_awready <= 1'b0;
            sh_cl_wready <= 1'b0;
            sh_cl_rvalid <= 1'b0;
            sh_cl_rdata <= 32'b0;
            zk_result <= 256'b0;
        end else begin
            // Write handling (simplified)
            if (cl_sh_awvalid && cl_sh_wvalid) begin
                case (cl_sh_awaddr[7:0])
                    8'h00: reg_control <= cl_sh_wdata;
                    8'h04: reg_op <= cl_sh_wdata[1:0];
                    8'h08: reg_a[31:0] <= cl_sh_wdata;
                    8'h0C: reg_a[63:32] <= cl_sh_wdata;
                    8'h10: reg_a[95:64] <= cl_sh_wdata;
                    8'h14: reg_a[127:96] <= cl_sh_wdata;
                    8'h18: reg_a[159:128] <= cl_sh_wdata;
                    8'h1C: reg_a[191:160] <= cl_sh_wdata;
                    8'h20: reg_a[223:192] <= cl_sh_wdata;
                    8'h24: reg_a[255:224] <= cl_sh_wdata;
                    // Similar for b and modulus...
                endcase
                sh_cl_awready <= 1'b1;
                sh_cl_wready <= 1'b1;
            end
            
            // Read handling
            if (cl_sh_rready) begin
                case (cl_sh_awaddr[7:0])
                    8'h20: sh_cl_rdata <= zk_result_internal[31:0];
                    8'h24: sh_cl_rdata <= zk_result_internal[63:32];
                    8'h28: sh_cl_rdata <= {30'b0, zk_done, zk_result_valid};
                    default: sh_cl_rdata <= 32'b0;
                endcase
                sh_cl_rvalid <= 1'b1;
            end
            
            if (zk_result_valid) begin
                zk_result <= zk_result_internal;
            end
        end
    end

endmodule

