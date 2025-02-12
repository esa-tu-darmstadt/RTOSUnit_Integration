module cv32e40p_tb_top (
    // Clock and Reset
    input logic clk_i,
    input logic rst_ni,

    input logic pulp_clock_en_i,  // PULP clock enable (only used if COREV_CLUSTER = 1)
    input logic scan_cg_en_i,  // Enable all clock gates for testing

    // Core ID, Cluster ID, debug mode halt address and boot address are considered more or less static
    input logic [31:0] boot_addr_i,
    input logic [31:0] mtvec_addr_i,
    input logic [31:0] dm_halt_addr_i,
    input logic [31:0] hart_id_i,
    input logic [31:0] dm_exception_addr_i,

    // Instruction memory interface
    output logic        instr_req_o,
    input  logic        instr_gnt_i,
    input  logic        instr_rvalid_i,
    output logic [31:0] instr_addr_o,
    input  logic [31:0] instr_rdata_i,

    // rtos unit memory iface
    output logic        ctx_mem_wr_en_o,
    output logic [31:0] ctx_mem_wr_addr_o,
    output logic [31:0] ctx_mem_wr_data_o,

    output logic ctx_mem_rd_rq_valid_o,
    output logic [31:0] ctx_mem_rd_rq_addr_o,

    input logic ctx_mem_rd_resp_valid_i,
    input logic [31:0] ctx_mem_rd_data_i,

    // Data memory interface
    output logic        data_req_o,
    input  logic        data_gnt_i,
    input  logic        data_rvalid_i,
    output logic        data_we_o,
    output logic [ 3:0] data_be_o,
    output logic [31:0] data_addr_o,
    output logic [31:0] data_wdata_o,
    input  logic [31:0] data_rdata_i,

    // Interrupt inputs
    input  logic [31:0] irq_i,  // CLINT interrupts + CLINT extension interrupts
    output logic        irq_ack_o,
    output logic [ 4:0] irq_id_o,

    // Debug Interface
    input  logic debug_req_i,
    output logic debug_havereset_o,
    output logic debug_running_o,
    output logic debug_halted_o,

    // CPU Control Signals
    input  logic fetch_enable_i,
    output logic core_sleep_o
);


// Register Read Logic
logic [4:0] reg_read_addr_cold_u_to_c;          // reg_read_addr_cold
logic [31:0] reg_read_data_cold_data_c_to_u;    // reg_read_data_cold_data

// Register Write Logic
logic [36:0] reg_write_cold_u_to_c;             // reg_write_cold
logic RDY_reg_write_cold_u_to_c;                // RDY_reg_write_cold

// Cold Registers Logic
logic [927:0] cold_regs_in_c_to_u;              // cold_regs_in
logic [927:0] cold_regs_w_u_to_c;               // cold_regs_w
logic RDY_cold_regs_w_u_to_c;                   // RDY_cold_regs_w

// Hot Register Write Logic
logic [11:0] reg_hot_write_trace_addrs_c_to_u;    // reg_hot_write_trace_addr

// Memory Write Logic
logic EN_mem_wr_c_to_u;                         // EN_mem_wr
logic [63:0] mem_wr_u_to_c;                     // mem_wr
logic RDY_mem_wr_u_to_c;                        // RDY_mem_wr

// Memory Read Address Logic
logic RDY_mem_rd_addr_u_to_c;                   // RDY_mem_rd_addr

// Mstatus and Mepc Logic
logic [31:0] mstatus_out_u_to_c;                // mstatus_out
logic [31:0] mepc_out_u_to_c;                   // mepc_out

// Bank Switching Logic
logic switch_bank_o_u_to_c;                     // switch_bank_o

// Mret Logic
logic EN_mret_c_to_u;                           // EN_mret
logic mret_u_to_c;                              // mret
logic RDY_mret_u_to_c;                          // RDY_mret

// CSR Write Logic
logic write_csrs_u_to_c;                        // write_csrs

// Trap Logic
logic [31:0] trap_mstatus_c_to_u;               // trap_mstatus
logic [31:0] trap_mepc_c_to_u;                  // trap_mepc
logic [31:0] trap_mcause_c_to_u;                // trap_mcause
logic EN_trap_c_to_u;                           // EN_trap
logic RDY_trap_u_to_c;                          // RDY_trap

// Custom Instruction Logic
logic [2:0] custom_inst_funct3_c_to_u;          // custom_inst_funct3
logic [31:0] custom_inst_id_c_to_u;             // custom_inst_id
logic [31:0] custom_inst_prio_c_to_u;           // custom_inst_prio
logic EN_custom_inst_c_to_u;                    // EN_custom_inst
logic [32:0] custom_inst_u_to_c;                // custom_inst
logic RDY_custom_inst_u_to_c;                   // RDY_custom_inst

// memory bus arbitration
assign EN_mem_wr_c_to_u = (~ctx_mem_rd_rq_valid_o) & ~data_req_o;
assign ctx_mem_wr_en_o = (~data_req_o) & RDY_mem_wr_u_to_c;
assign ctx_mem_wr_addr_o = mem_wr_u_to_c[63:32];
assign ctx_mem_wr_data_o = mem_wr_u_to_c[31:0];
assign ctx_mem_rd_rq_valid_o = (~data_req_o) & RDY_mem_rd_addr_u_to_c & (~ctx_mem_wr_en_o);

// write request separation
logic [4:0] reg_write_cold_addr;
logic [31:0] reg_write_cold_data;
assign reg_write_cold_addr = reg_write_cold_u_to_c[36:32];
assign reg_write_cold_data = reg_write_cold_u_to_c[31:0];

cv32e40p_top #(
    .FPU                      ( 0 ),
    .FPU_ADDMUL_LAT           ( 0 ),
    .FPU_OTHERS_LAT           ( 0 ),
    .ZFINX                    ( 0 ),
    .COREV_PULP               ( 0 ),
    .COREV_CLUSTER            ( 0 ),
    .NUM_MHPMCOUNTERS         ( 1 )
) u_core (
    // Clock and reset
    .rst_ni                   (rst_ni),
    .clk_i                    (clk_i),
    .scan_cg_en_i             (scan_cg_en_i),

    // Special control signals
    .fetch_enable_i           (fetch_enable_i),
    .pulp_clock_en_i          (pulp_clock_en_i),
    .core_sleep_o             (core_sleep_o),

    // Configuration
    .boot_addr_i              (boot_addr_i),
    .mtvec_addr_i             (mtvec_addr_i),
    .dm_halt_addr_i           (dm_halt_addr_i),
    .dm_exception_addr_i      (dm_exception_addr_i),
    .hart_id_i                (hart_id_i),

    // Instruction memory interface
    .instr_addr_o             (instr_addr_o),
    .instr_req_o              (instr_req_o),
    .instr_gnt_i              (instr_gnt_i),
    .instr_rvalid_i           (instr_rvalid_i),
    .instr_rdata_i            (instr_rdata_i),

    // Data memory interface
    .data_addr_o              (data_addr_o),
    .data_req_o               (data_req_o),
    .data_gnt_i               (data_gnt_i),
    .data_we_o                (data_we_o),
    .data_be_o                (data_be_o),
    .data_wdata_o             (data_wdata_o),
    .data_rvalid_i            (data_rvalid_i),
    .data_rdata_i             (data_rdata_i),

     // Interrupt interface
    .irq_i                    (irq_i),
    .irq_ack_o                (irq_ack_o),
    .irq_id_o                 (irq_id_o),

    // Debug interface
    .debug_req_i              (debug_req_i),
    .debug_havereset_o        (debug_havereset_o),
    .debug_running_o          (debug_running_o),
    .debug_halted_o           (debug_halted_o),

    // ctx operations
    .ctx_en_op_o(EN_custom_inst_c_to_u),
    .ctx_op_funct3_o(custom_inst_funct3_c_to_u),
    .ctx_rs1_id_o(custom_inst_id_c_to_u),
    .ctx_rs2_prio_o(custom_inst_prio_c_to_u),
    .ctx_rd_write_data_i(custom_inst_u_to_c),
    .ctx_mret_o(EN_mret_c_to_u),
    .ctx_trap_o(EN_trap_c_to_u),

    // ctx reg access
    .reg_read_addr_cold_i(reg_read_addr_cold_u_to_c),
    .reg_read_data_cold_data_o(reg_read_data_cold_data_c_to_u),

    .reg_write_addr_cold_i(reg_write_cold_addr),
    .reg_write_data_cold_data_i(reg_write_cold_data),
    .reg_write_we_cold_i(RDY_reg_write_cold_u_to_c),

    // ctx stuff
    .ctx_mcause_o(trap_mcause_c_to_u),
    .ctx_mstatus_o(trap_mstatus_c_to_u),
    .ctx_mepc_o(trap_mepc_c_to_u),
    .ctx_switch_bank_i(switch_bank_o_u_to_c),

    .ctx_csr_wr_we_i(write_csrs_u_to_c),
    .ctx_csr_wr_mepc_i(mepc_out_u_to_c),
    .ctx_csr_wr_mstatus_i(mstatus_out_u_to_c),

    .ctx_stall_mret_i(~RDY_mret_u_to_c),

    .ctx_reg_hot_write_trace_o(reg_hot_write_trace_addrs_c_to_u)
);

// Instantiate mkRTOSUnitSynth
mkRTOSUnitSynth u_mkRTOSUnitSynth (
    .CLK                        (clk_i),                      // Clock input
    .RST_N                      (rst_ni),                    // Reset input

    // Register Read Logic
    .reg_read_addr_cold         (reg_read_addr_cold_u_to_c), // reg_read_addr_cold
    .reg_read_data_cold_data    (reg_read_data_cold_data_c_to_u), // reg_read_data_cold_data

    // Register Write Logic
    .EN_reg_write_cold          (RDY_reg_write_cold_u_to_c), // EN_reg_write_cold
    .reg_write_cold             (reg_write_cold_u_to_c),    // reg_write_cold
    .RDY_reg_write_cold         (RDY_reg_write_cold_u_to_c), // RDY_reg_write_cold

    // Cold Registers Logic
    .cold_regs_in               (cold_regs_in_c_to_u),      // cold_regs_in
    .cold_regs_w                (cold_regs_w_u_to_c),       // cold_regs_w
    .RDY_cold_regs_w            (RDY_cold_regs_w_u_to_c),   // RDY_cold_regs_w

    // Hot Register Write Logic
    .reg_hot_write_trace_addrs   (reg_hot_write_trace_addrs_c_to_u), // reg_hot_write_trace_addr

    // Memory Write Logic
    .EN_mem_wr                  (EN_mem_wr_c_to_u),         // EN_mem_wr
    .mem_wr                     (mem_wr_u_to_c),            // mem_wr
    .RDY_mem_wr                 (RDY_mem_wr_u_to_c),        // RDY_mem_wr

    // Memory Read Address Logic
    .EN_mem_rd_addr             (ctx_mem_rd_rq_valid_o),    // EN_mem_rd_addr
    .mem_rd_addr                (ctx_mem_rd_rq_addr_o),       // mem_rd_addr
    .RDY_mem_rd_addr            (RDY_mem_rd_addr_u_to_c),   // RDY_mem_rd_addr

    // Memory Read Data Logic
    .mem_rd_data_d              (ctx_mem_rd_data_i),     // mem_rd_data_d
    .EN_mem_rd_data             (ctx_mem_rd_resp_valid_i),    // EN_mem_rd_data

    // Mstatus and Mepc Logic
    .mstatus_out                (mstatus_out_u_to_c),       // mstatus_out
    .mepc_out                   (mepc_out_u_to_c),          // mepc_out

    // Bank Switching Logic
    .switch_bank_o              (switch_bank_o_u_to_c),     // switch_bank_o

    // Mret Logic
    .EN_mret                    (EN_mret_c_to_u),           // EN_mret
    .mret                       (mret_u_to_c),              // mret
    .RDY_mret                   (RDY_mret_u_to_c),          // RDY_mret

    // CSR Write Logic
    .write_csrs                 (write_csrs_u_to_c),        // write_csrs

    // Trap Logic
    .trap_mstatus               (trap_mstatus_c_to_u),      // trap_mstatus
    .trap_mepc                  (trap_mepc_c_to_u),         // trap_mepc
    .trap_mcause                (trap_mcause_c_to_u),       // trap_mcause
    .EN_trap                    (EN_trap_c_to_u),           // EN_trap
    .RDY_trap                   (RDY_trap_u_to_c),          // RDY_trap

    // Custom Instruction Logic
    .custom_inst_funct3         (custom_inst_funct3_c_to_u),// custom_inst_funct3
    .custom_inst_id             (custom_inst_id_c_to_u),    // custom_inst_id
    .custom_inst_prio           (custom_inst_prio_c_to_u),  // custom_inst_prio
    .EN_custom_inst             (EN_custom_inst_c_to_u),    // EN_custom_inst
    .custom_inst                (custom_inst_u_to_c),       // custom_inst
    .RDY_custom_inst            (RDY_custom_inst_u_to_c)    // RDY_custom_inst
);



endmodule
