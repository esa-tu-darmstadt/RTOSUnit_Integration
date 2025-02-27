#!/usr/bin/python3
import os
import subprocess
import concurrent.futures
from generate_tapasco_folders import configs, tapasco_dir
import shutil

top_dir = "cadence_rtl"

folder_prefix = "cores/cv32e40p"
files = ["rtl/include/cv32e40p_apu_core_pkg.sv",
            "rtl/include/cv32e40p_fpu_pkg.sv",
            "rtl/include/cv32e40p_pkg.sv",
            "rtl/cv32e40p_if_stage.sv",
            "rtl/cv32e40p_cs_registers.sv",
            "rtl/cv32e40p_register_file_ff.sv",
            "rtl/cv32e40p_load_store_unit.sv",
            "rtl/cv32e40p_id_stage.sv",
            "rtl/cv32e40p_aligner.sv",
            "rtl/cv32e40p_decoder.sv",
            "rtl/cv32e40p_compressed_decoder.sv",
            "rtl/cv32e40p_fifo.sv",
            "rtl/cv32e40p_prefetch_buffer.sv",
            "rtl/cv32e40p_hwloop_regs.sv",
            "rtl/cv32e40p_mult.sv",
            "rtl/cv32e40p_int_controller.sv",
            "rtl/cv32e40p_ex_stage.sv",
            "rtl/cv32e40p_alu_div.sv",
            "rtl/cv32e40p_alu.sv",
            "rtl/cv32e40p_ff_one.sv",
            "rtl/cv32e40p_popcnt.sv",
            "rtl/cv32e40p_apu_disp.sv",
            "rtl/cv32e40p_controller.sv",
            "rtl/cv32e40p_obi_interface.sv",
            "rtl/cv32e40p_prefetch_controller.sv",
            "rtl/cv32e40p_sleep_unit.sv",
            "rtl/cv32e40p_core.sv",

            "rtl/cv32e40p_top.sv",

            "rtl/../bhv/cv32e40p_sim_clock_gate.sv",
            "rtl/../bhv/include/cv32e40p_tracer_pkg.sv"
]

files_abs = [ "simulation_wrappers/cv32e40p_tb_top.sv",
                "RTOSUnit/build/verilog/mkRTOSUnitSynth.v",
                "/opt/cad/bluespec/latest/lib/Verilog/FIFO2.v"]

base_cdns_dir = "/scratch/new-scratch/Cadence/HWRtos_cv32e40p/"

if __name__ == "__main__":
    for dirname, config in configs.items():
        cdns_flow_dir = os.path.join(base_cdns_dir, dirname)
        os.system(f"cp -r {os.path.join(base_cdns_dir, "template")} {cdns_flow_dir}")
        cdns_flow_rtl_dir = os.path.join(cdns_flow_dir, "cdns_pnr/design_data/rtl")

        if dirname == "vanilla":
            folder_prefix_loc = folder_prefix + "_vanilla"
        else:
            os.system(f"{config} make clean ctxunit")
            for f in files_abs:
                shutil.copy(f, cdns_flow_rtl_dir)
            shutil.copy("cores/cv32e40p/rtl/cv32e40p_register_file_multiplex.sv", cdns_flow_rtl_dir)
            folder_prefix_loc = folder_prefix

        for f in files:
            shutil.copy(os.path.join(folder_prefix_loc, f), cdns_flow_rtl_dir)

