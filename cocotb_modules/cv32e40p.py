import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly
from cocotb.clock import Clock
import sys
import os

# preload memory model
memory = [0]*(0x100000)
mem_bin = open(f"{os.getcwd()}/freertos/build/RTOSDemo32.bin", "rb").read()
no_words = int(len(mem_bin)/4)
no_bytes = int(len(mem_bin))
for i in range(no_bytes):
    memory[i] = int(mem_bin[i])

async def flush(dut):
    await Edge(dut.clk_i)
    sys.stdout.flush()

async def reset_dut(reset_n, duration_ns):
    reset_n.value = 0
    await Timer(duration_ns, units="ns")
    reset_n.value = 1
    reset_n._log.debug("Reset complete")

async def memory_sim(dut, dbg_name, obi_prefix, dbg = False):
    while True:
        await FallingEdge(dut.clk_i)
        # check WE if available
        we = False if obi_prefix == "instr" else eval(f"dut.{obi_prefix}_we_o.value == 1")
        # read addr
        if eval(f"dut.{obi_prefix}_req_o.value") == 1:
            addr = eval(f"dut.{obi_prefix}_addr_o.value") & 0xfffffffc
            addr_pr = eval(f"dut.{obi_prefix}_addr_o.value")
            if dbg:
                print(f"{dbg_name} {"read" if not we else "write"}: 'h{int(addr_pr):08x} {"" if not we else f": 'h{int(eval(f"dut.{obi_prefix}_wdata_o.value")):016x} : 'h{int(eval(f"dut.{obi_prefix}_be_o.value")):01x}"}")
                sys.stdout.flush()
            next_vld = True
            if not we:
                try:
                    be = 0xf if obi_prefix == "instr" else eval(f"dut.{obi_prefix}_be_o.value")
                    nbl_0 = memory[addr]
                    nbl_1 = memory[addr+1]
                    nbl_2 = memory[addr+2]
                    nbl_3 = memory[addr+3]
                    next_r = nbl_0 + (nbl_1<<8) + (nbl_2<<16) + (nbl_3<<24)
                    if not we and dbg:
                        print(f"{dbg_name} read data: 'h{int(next_r):08x} : 'h{int(be):01x}")
                    sys.stdout.flush()
                    vld_addr = True
                except IndexError:
                    vld_addr = False

            # write
            if we:
                for i in range(4):
                    be = eval(f"dut.{obi_prefix}_be_o.value")[i]
                    addr_w = addr + i
                    data_w = eval(f"int(dut.{obi_prefix}_wdata_o.value).to_bytes(4, byteorder = 'little')")
                    if be:
                        try:
                            memory[addr_w] = data_w[i]
                        except:
                            # end simulation
                            if addr == 0x11004000:
                                print("got return")
                                return
                            else:
                                if dbg:
                                    print("UNKNOWN ADDRESS")
        else:
            next_vld = False
        await RisingEdge(dut.clk_i)
        # write data
        if next_vld:
            exec(f"dut.{obi_prefix}_rvalid_i.value = 1")
            if not we and vld_addr:
                exec(f"dut.{obi_prefix}_rdata_i.value = next_r")
                if dbg:
                    sys.stdout.flush()
        else:
            exec(f"dut.{obi_prefix}_rvalid_i.value = 0")

async def clint(dut, dbg_name, dbg = False):

    mtime = 0
    mtime_h = 0
    mtimecmp = 0
    mtimecmp_h = 0

    while True:
        await FallingEdge(dut.clk_i)
        # check WE if available
        we = (dut.data_we_o.value == 1)
        # read addr
        next_vld = True
        next_data = 0
        if dut.data_req_o.value == 1:
            addr = dut.data_addr_o.value
            if dbg:
                print(f"{dbg_name} {"read" if not we else "write"}: {hex(addr)}")
            if addr == 0x4000BFF8:
                next_data = mtime
            elif addr == 0x4000BFFC:
                next_data = mtime_h
            elif addr == 0x40004000:
                next_data = mtimecmp
            elif addr == 0x40004004:
                next_data = mtimecmp_h
            else:
                next_vld = False

            if we:
                if addr == 0x4000BFF8:
                    mtime = dut.data_wdata_o.value
                elif addr == 0x4000BFFC:
                    mtime_h = dut.data_wdata_o.value
                elif addr == 0x40004000:
                    mtimecmp = dut.data_wdata_o.value
                elif addr == 0x40004004:
                    mtimecmp_h = dut.data_wdata_o.value


        if os.environ.get('SCHED') == "HW" and dut.u_core.ctx_trap_o.value == 1 and  dut.u_core.ctx_mcause_o == 0x80000007:
            mtime = 0
            mtime_h = 0
            
        await RisingEdge(dut.clk_i)
        # write data
        if next_vld:
            dut.data_rdata_i.value = next_data

        # test condition
        if ((mtime_h << 32) + mtime) >= ((mtimecmp_h << 32) + mtimecmp):
            dut.irq_i.value = (1 << 7)
            if dbg:
                print("Trigger irq")
        else:
            dut.irq_i.value = 0

        # advance counter
        new_mtime = ((mtime_h << 32) + mtime) + 1
        mtime = new_mtime & 0xffffffff
        mtime_h = (new_mtime >> 32) & 0xffffffff

async def check_assertions(dut):
    await ReadOnly()
    if dut.u_core.core_i.cs_registers_i.ctx_mcause_o.value not in [0xb, 0x17, 0x0]:
        print("ERROR: invalid MCAUSE register value!")
        exit(-1)

@cocotb.test()
async def run_program(dut):
    """Run binary."""

    # tie off unused signals
    dut.pulp_clock_en_i.value = 1
    dut.scan_cg_en_i.value = 1
    dut.boot_addr_i.value = 0
    dut.mtvec_addr_i.value = 0x100
    dut.dm_halt_addr_i.value = 0
    dut.hart_id_i.value = 0
    dut.dm_exception_addr_i.value = 0
    dut.debug_req_i.value = 0
    dut.fetch_enable_i.value = 1
    dut.irq_i.value = 0

    # memory iface
    dut.instr_gnt_i.value = 1
    dut.data_gnt_i.value = 1
    dut.data_2_gnt_i.value = 1

    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    cocotb.start_soon(memory_sim(dut, "I", "instr"))
    cocotb.start_soon(clint(dut, "CLINT", False))
    cocotb.start_soon(check_assertions(dut))
    mem = cocotb.start_soon(memory_sim(dut, "D", "data"))
    cocotb.start_soon(memory_sim(dut, "D2", "data_2"))

    # reset core
    await reset_dut(dut.rst_ni, 500)
    dut._log.debug("After reset")

    # wait for finished
    await mem
