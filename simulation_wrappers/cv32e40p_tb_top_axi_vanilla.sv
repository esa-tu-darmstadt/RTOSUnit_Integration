module cv32e40p_tb_top_axi (
    // Clock and Reset
    input logic clk_i,
    input logic rst_ni,

    // Instruction memory interface
    output logic        m_axi_instr_arvalid,
    input  logic        m_axi_instr_arready,
    output logic [31:0] m_axi_instr_araddr,
    output logic        m_axi_instr_rready,
    input  logic        m_axi_instr_rvalid,
    input  logic [31:0] m_axi_instr_rdata,

    output logic        m_axi_instr_awvalid,
    input  logic        m_axi_instr_awready,
    output logic [31:0] m_axi_instr_awaddr,
    output logic        m_axi_instr_wvalid,
    input  logic        m_axi_instr_wready,
    output logic [31:0] m_axi_instr_wdata,
    input  logic        m_axi_instr_bvalid,
    output logic        m_axi_instr_bready,

    // Data memory interface
    output logic        m_axi_data_arvalid,
    input  logic        m_axi_data_arready,
    output logic [31:0] m_axi_data_araddr,
    output logic        m_axi_data_rready,
    input  logic        m_axi_data_rvalid,
    input  logic [31:0] m_axi_data_rdata,

    output logic        m_axi_data_awvalid,
    input  logic        m_axi_data_awready,
    output logic [31:0] m_axi_data_awaddr,
    output logic        m_axi_data_wvalid,
    input  logic        m_axi_data_wready,
    output logic [31:0] m_axi_data_wdata,
    output logic [ 3:0] m_axi_data_wstrb,
    input  logic        m_axi_data_bvalid,
    output logic        m_axi_data_bready,

    // Interrupt inputs
    input  logic [31:0] irq_i  // CLINT interrupts + CLINT extension interrupts
);

logic        data_req_c;
logic        data_gnt_c;
logic        data_rvalid_c;
logic        data_we_c;
logic [ 3:0] data_be_c;
logic [31:0] data_addr_c;
logic [31:0] data_wdata_c;
logic [31:0] data_rdata_c;

logic        instr_req_o_c;
logic        instr_gnt_i_c;
logic        instr_rvalid_i_c;
logic [31:0] instr_addr_o_c;
logic [31:0] instr_rdata_i_c;

assign m_axi_instr_arvalid = instr_req_o_c;
assign instr_gnt_i = m_axi_instr_arready;
assign instr_addr_o_c = m_axi_instr_araddr;
assign m_axi_instr_rready = 1;
assign instr_rvalid_i_c = m_axi_instr_rvalid;
assign instr_rdata_i_c = m_axi_instr_rdata;

assign data_gnt_c = m_axi_data_arready & m_axi_data_awready & m_axi_data_wready;
assign m_axi_data_arvalid = data_req_c & !data_we_c;
assign m_axi_data_araddr = data_addr_c;
assign m_axi_data_rready = 1;
assign data_rvalid_c = m_axi_data_rvalid | m_axi_data_bvalid;
assign data_rdata_c = m_axi_data_rdata;

assign m_axi_data_awvalid = data_req_c & data_we_c;
assign m_axi_data_awaddr = data_addr_c;
assign m_axi_data_wvalid = data_req_c & data_we_c;
assign m_axi_data_wdata = data_wdata_c;
assign m_axi_data_bready = 1;
assign m_axi_data_wstrb = data_be_c;

// tieoff
assign m_axi_instr_awvalid = 0;
assign m_axi_instr_awaddr = 0;
assign m_axi_instr_wvalid = 0;
assign m_axi_instr_wdata = 0;
assign m_axi_instr_bready = 0;

cv32e40p_top u_core (
    // Clock and reset
    .rst_ni                   (rst_ni),
    .clk_i                    (clk_i),
    .scan_cg_en_i             (1),

    // Special control signals
    .fetch_enable_i           (1),
    .pulp_clock_en_i          (1),
    .core_sleep_o             (),

    // Configuration
    .boot_addr_i              (0),
    .mtvec_addr_i             ('h100),
    .dm_halt_addr_i           (0),
    .dm_exception_addr_i      (0),
    .hart_id_i                (0),

    // Instruction memory interface
    .instr_addr_o             (instr_addr_o_c),
    .instr_req_o              (instr_req_o_c),
    .instr_gnt_i              (instr_gnt_i_c),
    .instr_rvalid_i           (instr_rvalid_i_c),
    .instr_rdata_i            (instr_rdata_i_c),

    // Data memory interface
    .data_addr_o              (data_addr_c),
    .data_req_o               (data_req_c),
    .data_gnt_i               (data_gnt_c),
    .data_we_o                (data_we_c),
    .data_be_o                (data_be_c),
    .data_wdata_o             (data_wdata_c),
    .data_rvalid_i            (data_rvalid_c),
    .data_rdata_i             (data_rdata_c),

     // Interrupt interface
    .irq_i                    (irq_i),
    .irq_ack_o                (irq_ack_o),
    .irq_id_o                 (irq_id_o),

    // Debug interface
    .debug_req_i              (0),
    .debug_havereset_o        (),
    .debug_running_o          (),
    .debug_halted_o           ()

);


endmodule
