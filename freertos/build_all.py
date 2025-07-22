import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

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

    "HW-S_HW-PL-HW-Sc" : "LOAD=HW STORE=HW SCHED=HW LATCH=LD DIRTY=N"
}

progs = {}
sizes = {}

import os
for prog in ["semaphore/sem_workload", "mutex/mutex_workload", "mq/mq_workload"]:
    for name, flags in configs.items():
        #os.system(f"make TEST={prog} {flags} clean all")
        prog_ = prog.replace("/", "_")
        #os.system(f"cp -f build/RTOSDemo32.axf all_builds/{prog_}_{flags.replace(" ", "_")}.axf")
        #os.system(f"riscv32-unknown-elf-objdump -h all_builds/{prog_}_{flags.replace(" ", "_")}.axf > all_builds/{prog_}_{flags.replace(" ", "_")}.hdr")

        dump_file = open(f"all_builds/{prog_}_{flags.replace(" ", "_")}.hdr", "r")
        size = 0
        for l in dump_file:
            if not ".text" in l:
                continue

            size = size + int(l.split()[2], 16)

        sizes[name] = size

    progs[prog_] = sizes.copy()

print(progs)
print(pd.DataFrame(progs))
print(pd.DataFrame(progs).melt(ignore_index=False, var_name="test", value_name="bytes"))
df = pd.DataFrame(progs).melt(ignore_index=False, var_name="test", value_name="bytes").reset_index().rename(columns={'index': 'config'})

sns.barplot(df, hue="test", y="bytes" x="config")
plt.show()