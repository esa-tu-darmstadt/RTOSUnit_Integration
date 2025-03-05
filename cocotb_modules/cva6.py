import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly
from cocotb.clock import Clock
import sys
import os
import mmap
import logging
import amba

async def reset_dut(reset_n, duration_ns):
    reset_n.value = 0
    await Timer(duration_ns, units="ns")
    reset_n.value = 1
    reset_n._log.debug("Reset complete")

async def simulate_clint(dut, mem, dbg = False):
    while True:
        await RisingEdge(dut.clk_i)

        addr_mtime = 0x4000BFF8
        addr_mtimecmp = 0x40004000

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

    logging.disable()

    # tie off unused signals
    dut.boot_addr_i.value = 0
    dut.hart_id_i.value = 0
    dut.irq_i.value = 0
    dut.ipi_i.value = 0
    dut.debug_req_i.value = 0

    mem_bin = open(f"{os.getcwd()}/freertos/build/RTOSDemo32.bin", "rb").read()
    mem = mmap.mmap(-1, 0x40100000)
    mem[:] = b'\x00' * len(mem)
    mem[0:len(mem_bin)] = mem_bin

    print("done loading memory")

    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    cocotb.start_soon(simulate_clint(dut, mem, False))
    irq = cocotb.start_soon(wait_for_irq(dut, mem, True))

    amba.AXI4Slave(dut, "m_axi_ctrl", dut.clk_i, dut.rst_ni, mem, big_endian=False)

    # reset core
    await reset_dut(dut.rst_ni, 400)
    dut._log.debug("After reset")
    print("rst done")
    sys.stdout.flush()
    

    # wait for finished
    await irq
    print("tst done")
    sys.stdout.flush()
