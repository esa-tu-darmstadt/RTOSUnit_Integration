import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly
from cocotb.clock import Clock
from memutil import MemView, HierarchicalMemView, BytearrayMemView
import sys
import os
import mmap
import logging
import amba
from collections import deque

mem_delay = 0
# mem_delay = 10

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

async def reset_dut(reset_n, duration_ns):
    reset_n.value = 0
    await Timer(duration_ns, units="ns")
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
    mem_req_queue = deque([None] * mem_delay, maxlen=mem_delay + 1)

    while True:
        await FallingEdge(dut.clk_i)
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

        if not we and ena == 1:
            mem_req_queue.append(int.from_bytes(mem[addr_ctx:addr_ctx+4], "little"))
        else:
            mem_req_queue.append(None)

        await RisingEdge(dut.clk_i)

        mem_res = mem_req_queue.popleft()
        if mem_res is None:
            dut.ctx_mem_rd_resp_valid.value = False
        else:
            dut.ctx_mem_rd_resp_valid.value = True
            dut.ctx_mem_rd_data.value = mem_res




async def memory_sim_rd_cache(dut, mem, dbg = False):

    mem_req_queue = deque([], maxlen=mem_delay + 1)

    next_vld = False
    next_data = 0

    while True:
        await FallingEdge(dut.clk_i)
        rq = dut.read_req.value
        addr  = dut.read_addr.value

        # elapsing writes
        if rq == 1:
            if dbg:
                print(f"Core read: {hex(addr)}")
                sys.stdout.flush()

            next_data = int.from_bytes(mem[addr:addr+4], "little")
            next_vld = True
            mem_req_queue.append(int(dut.read_id.value))
        else:
            next_vld = False

        await RisingEdge(dut.clk_i)

        dut.read_resp.value = 1 if next_vld else 0
        dut.read_data.value = next_data
        if next_vld:
            dut.read_resp_id.value = mem_req_queue.popleft()

async def memory_sim_wr_cache(dut, mem, dbg = False):

    while True:
        await FallingEdge(dut.clk_i)
        we = dut.write_ena.value
        be = dut.write_be.value
        data = dut.write_data.value
        addr = dut.write_addr.value
        size = dut.write_size.value

        # elapsing writes
        if we == 1:
            if dbg:
                print(f"Core write: {hex(addr)} : {hex(data)} : {hex(be)} : {hex(size)}")
                sys.stdout.flush()

            for i in range(4):
                if be[i] == 1:
                    mem[addr+i] = int.to_bytes(int(data), 4, 'little')[i]


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

    mem_bin = open(f"{os.getcwd()}/freertos/build/RTOSDemo32.bin", "rb").read()
    mem = bytearray(0x40100000)
    mem[0:len(mem_bin)] = mem_bin

    print("done loading memory")

    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    cocotb.start_soon(simulate_clint(dut, mem, False))
    irq = cocotb.start_soon(wait_for_irq(dut, mem, False))
    cocotb.start_soon(memory_sim_rtosunit(dut, mem, False))
    cocotb.start_soon(memory_sim_wr_cache(dut, mem, True))
    cocotb.start_soon(memory_sim_rd_cache(dut, mem, True))
    #cocotb.start_soon(check_reg_str_rst(dut))

    memsi = amba.AXI4Slave(dut, "m_axi_ctrl", dut.clk_i, HierarchicalMemView([]), big_endian=False, enable_prints=False, artificial_write_delay=mem_delay, artificial_read_delay=mem_delay)
    memview = BytearrayMemView(mem, 0, 0x40100000, 0, auto_resize=True)
    memsi.memview.children.append(memview)

    # reset core
    await reset_dut(dut.rst_ni, 400)
    dut._log.debug("After reset")
    print("rst done")
    sys.stdout.flush()
    

    # wait for finished
    await irq
    print("tst done")
    sys.stdout.flush()
