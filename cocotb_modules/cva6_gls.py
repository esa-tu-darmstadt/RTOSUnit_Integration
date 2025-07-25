import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly
from cocotb.clock import Clock
from memutil import MemView, HierarchicalMemView, BytearrayMemView
import sys
import os
import mmap
import logging
import amba

# TODO: also check epc address and mstatus
rf_state = {}
async def check_reg_str_rst(dut):
    while(os.environ.get('SCHED') == "HW" or os.environ.get('STORE') == "HW"):
        await FallingEdge(dut.clk_i)

        if (dut.ctx_trap.value == 1):
            # get and save current state
            rf = dut.cva6.issue_stage_i.i_issue_read_operands.i_ariane_regfile.i_ariane_regfile_1.mem_rd.value
            ctx = dut.u_mkRTOSUnitSynth.r_ctxUnit_ctx_ids.value
            rf_state[int(ctx)] = rf
            # check for wrong causes
            await FallingEdge(dut.clk_i)
            if dut.ctx_mcause.value != 0x80000007 and dut.ctx_mcause.value != 0xb:
                print(f"Shady interrupt cause {hex(dut.ctx_mcause.value)}! Abort!")
                sys.stdout.flush()
                raise Exception()

        if (dut.ctx_mret.value == 1):
            await FallingEdge(dut.clk_i) # wait additional cycle (needed for preload)
            # get current state
            rf = dut.cva6.issue_stage_i.i_issue_read_operands.i_ariane_regfile.i_ariane_regfile_1.mem_rd.value
            ctx = dut.u_mkRTOSUnitSynth.r_ctxUnit_ctx_ids.value
            # if state has already been saved, compare and lint
            if int(ctx) in rf_state:
                golden = rf_state[int(ctx)]
                if rf != golden:
                    print("mismatch between current rf and suspended rf:")
                    print("expected: ", end = "")
                    print(hex(golden))
                    print("got     : ", end = "")
                    print(hex(rf))
                    sys.stdout.flush()
                    raise Exception()
            if int(ctx) == 0:
                print("Restoring from zero! Abort!")
                sys.stdout.flush()
                raise Exception()

async def reset_dut(clk, reset_n, duration_ns):
    reset_n.value = 0
    await Timer(duration_ns, units="ns")
    await FallingEdge(clk)
    reset_n.value = 1
    reset_n._log.debug("Reset complete")

async def simulate_clint(dut, mem, dbg = False):
    addr_mtime = 0x4000BFF8
    addr_mtimecmp = 0x40004000

    while True:

        await FallingEdge(dut.clk_i)
        if os.environ.get('SCHED') == "HW" and dut.ctx_trap.value == 1 and  dut.ctx_mcause.value == 0x80000007:
            mem[addr_mtime:addr_mtime+8] = b'\x00' * 8
        
        await RisingEdge(dut.clk_i)

        mtime    = int.from_bytes(mem[addr_mtime:addr_mtime+8], 'little')
        mtimecmp = int.from_bytes(mem[addr_mtimecmp:addr_mtimecmp+8], 'little')

        if (mtime >= mtimecmp):
            dut.time_irq_i.value = 1
            if dbg:
                print("Trigger irq")
        else:
            dut.time_irq_i.value = 0

        # advance counter
        mem[addr_mtime:addr_mtime+8] = int.to_bytes(mtime+1, 8, 'little')

async def memory_sim_rtosunit(dut, mem, dbg = False):
    while True:
        await FallingEdge(dut.clk_i)
        # check WE if available
        ena = dut.EN_ctx_mem_access.value
        we  = dut.ctx_mem_wr_en.value
        data_ctx_w = dut.ctx_mem_wr_data.value
        addr_ctx = dut.ctx_mem_addr.value

        # elapsing writes
        if ena == 1 and we == 1:
            if dbg:
                print(f"RTOSUnit write: {hex(addr_ctx)} : {hex(data_ctx_w)}")
                sys.stdout.flush()

            mem[addr_ctx:addr_ctx+4] = int.to_bytes(int(data_ctx_w), 4, 'little')

        await RisingEdge(dut.clk_i)

        if ena == 1:
            dut.ctx_mem_rd_resp_valid.value = not we
            dut.ctx_mem_rd_data.value = int.from_bytes(mem[addr_ctx:addr_ctx+4], "little")
        else:
            dut.ctx_mem_rd_resp_valid.value = 0

async def wait_for_irq(dut, mem, dbg = False):
    while True:
        await RisingEdge(dut.clk_i)

        addr_irq = 0x11004000
        irq      = int.from_bytes(mem[addr_irq:addr_irq+4], 'little')

        if (irq != 0):
            print("got irq!")
            return
        

@cocotb.test()
async def run_program(dut):
    """Run binary."""

    #logging.disable()

    # tie off unused signals
    dut.boot_addr_i.value = 0
    dut.hart_id_i.value = 0
    dut.irq_i.value = 0
    dut.ipi_i.value = 0
    dut.debug_req_i.value = 0
    dut.shift_enable.setimmediatevalue(0)
    dut.test_mode.setimmediatevalue(0)
    dut.m_axi_ctrl_RDATA.setimmediatevalue(0)
    dut.time_irq_i.setimmediatevalue(0)

    dut.m_axi_ctrl_AWREADY.setimmediatevalue(0)
    dut.m_axi_ctrl_WREADY.setimmediatevalue(0)
    dut.m_axi_ctrl_BVALID.setimmediatevalue(0)
    dut.m_axi_ctrl_BID.setimmediatevalue(0)

    dut.m_axi_ctrl_BRESP.setimmediatevalue(0)
    dut.m_axi_ctrl_ARREADY.setimmediatevalue(0)
    dut.m_axi_ctrl_RVALID.setimmediatevalue(0)
    dut.m_axi_ctrl_RID.setimmediatevalue(0)

    dut.m_axi_ctrl_RRESP.setimmediatevalue(0)
    dut.m_axi_ctrl_RLAST.setimmediatevalue(0)
    dut.m_axi_ctrl_RVALID.setimmediatevalue(0)
    dut.m_axi_ctrl_RID.setimmediatevalue(0)

    #dut.ctx_mem_rd_resp_valid.setimmediatevalue(0)
    #dut.ctx_mem_rd_data.setimmediatevalue(0)
    dut.rst_ni.setimmediatevalue(1)

    if 'external_interrupt' in dut._sub_handles:
        irq_signal = dut.external_interrupt
        dut.external_interrupt.setimmediatevalue(0)
    if 'interrupt' in dut._sub_handles:
        irq_signal = dut.interrupt
        dut.interrupt.setimmediatevalue(0)
    if 'timer_interrupt' in dut._sub_handles:
        dut.timer_interrupt.setimmediatevalue(0)

    if 'm_axi_rlast' in dut._sub_handles:
        dut.m_axi_rlast.setimmediatevalue(0)
    if 'm_axi_ctrl_RLAST' in dut._sub_handles:
        dut.m_axi_ctrl_RLAST.setimmediatevalue(0)
    if 'VSS' in dut._sub_handles:
        dut.VSS.setimmediatevalue(0)
        dut.VDD.setimmediatevalue(1)
    if 'shift_enable' in dut._sub_handles:
        dut.shift_enable.setimmediatevalue(0)
        dut.test_mode.setimmediatevalue(0)
    if 'DFT_sdi_1' in dut._sub_handles:
        dut.DFT_sdi_1.setimmediatevalue(0)
    if 'SI1' in dut._sub_handles:
        dut.SI1.setimmediatevalue(0)
    if 'm_bram_data_dout' in dut._sub_handles:
        dut.m_bram_data_dout.setimmediatevalue(0)
        dut.m_bram_instr_dout.setimmediatevalue(0)


    dut.ctx_mem_rd_resp_valid.setimmediatevalue(0)
    dut.ctx_mem_rd_data.setimmediatevalue(0)
    dut.SI1.setimmediatevalue(0)


    mem_bin = open(f"{os.getcwd()}/freertos/build/RTOSDemo32.bin", "rb").read()
    # mem = mmap.mmap(-1, 0x40100000)
    mem = bytearray(len(mem_bin))
    # mem[:] = b'\x00' * len(mem)
    mem[0:len(mem_bin)] = mem_bin

    print("done loading memory")

    cocotb.start_soon(Clock(dut.clk_i, 2, units="ns").start())
    cocotb.start_soon(simulate_clint(dut, mem, False))
    irq = cocotb.start_soon(wait_for_irq(dut, mem, True))
    cocotb.start_soon(memory_sim_rtosunit(dut, mem, True))
    #cocotb.start_soon(check_reg_str_rst(dut))

    memsi = amba.AXI4Slave(dut, "m_axi_ctrl", dut.clk_i, HierarchicalMemView([]), big_endian=False, enable_prints=False, artificial_write_delay=0, artificial_read_delay=0)
    memview = BytearrayMemView(mem, 0, 0x40100000, 0, auto_resize=True)
    memsi.memview.children.append(memview)

    # reset core
    await reset_dut(dut.clk_i, dut.rst_ni, 16)
    dut._log.debug("After reset")
    print("rst done")
    sys.stdout.flush()
    

    # wait for finished
    await irq
    print("tst done")
    sys.stdout.flush()
