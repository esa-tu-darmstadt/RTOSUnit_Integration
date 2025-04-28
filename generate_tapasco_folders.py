#!/usr/bin/python3
import os

top_dir = "tapasco-workspaces"
tapasco_dir = "/scratch/ms/S4E/piccolo_multi_context_support/testbenches-vanilla/tapasco"

configs = {
    "vanilla"          : "LOAD=SW STORE=SW SCHED=SW LATCH=NO DIRTY=N",
    "HW-S"             : "LOAD=SW STORE=HW SCHED=SW LATCH=NO DIRTY=N",
    "HW-S_HW-L"        : "LOAD=HW STORE=HW SCHED=SW LATCH=NO DIRTY=N",
    "HW-Sc"            : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N",
    "HW-S_HW-Sc"       : "LOAD=SW STORE=HW SCHED=HW LATCH=NO DIRTY=N",
    "HW-S_HW-L-HW-Sc"  : "LOAD=HW STORE=HW SCHED=HW LATCH=NO DIRTY=N",

    "HW-SD"            : "LOAD=SW STORE=HW SCHED=SW LATCH=NO DIRTY=Y",
    "HW-SD_HW-L"       : "LOAD=HW STORE=HW SCHED=SW LATCH=NO DIRTY=Y",
    "HW-SD_HW-Sc"      : "LOAD=SW STORE=HW SCHED=HW LATCH=NO DIRTY=Y",
    "HW-SD_HW-L-HW-Sc" : "LOAD=HW STORE=HW SCHED=HW LATCH=NO DIRTY=Y",

    "HW-S_HW-PL-HW-Sc" : "LOAD=HW STORE=HW SCHED=HW LATCH=LD DIRTY=N",

    "HW-Sc4"           : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=4",
    "HW-Sc8"           : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=8",
    "HW-Sc12"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=12",
    "HW-Sc16"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=16",
    "HW-Sc20"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=20",
    "HW-Sc24"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=24",
    "HW-Sc28"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=28",
    "HW-Sc32"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=32",
    "HW-Sc40"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=40",
    "HW-Sc48"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=48",
    "HW-Sc56"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=56",
    "HW-Sc64"          : "LOAD=SW STORE=SW SCHED=HW LATCH=NO DIRTY=N LISTLEN=64"
}

if __name__ == "__main__":
    for dirname, config in configs.items():
        cudir = os.path.abspath(os.path.join(top_dir, dirname))
        os.makedirs(cudir, exist_ok=True)
        os.system(f"pushd {cudir} && {tapasco_dir}/tapasco-init.sh && popd")
        os.system(f"{config} make ctxunit")
        os.system(f"pushd tapasco-riscv && . {cudir}/tapasco-setup.sh && make clean { 'cv32e40p_ctx_pe' if dirname != "vanilla" else 'cv32e40p_pe' } && popd")