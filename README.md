# RTOSUnit Integration

Open-source artifact for the ASPLOS '26 paper:

> **Co-Exploration of RISC-V Processor Microarchitectures and FreeRTOS Extensions for Lower Context-Switch Latency**
> Markus Scheck\*, Tammo Mürmann\*, Andreas Koch
> Technical University of Darmstadt
> \*Both authors contributed equally.

[Paper (PDF)](https://www.esa.informatik.tu-darmstadt.de/assets/publications/materials/2026/2026_ASPLOS_MS_TFM.pdf) | [DOI](https://doi.org/10.1145/3779212.3790141)

## Overview

RTOSUnit is a configurable hardware acceleration unit that reduces context-switch latency and jitter in embedded real-time systems running FreeRTOS on RISC-V processors. By offloading context storing, loading, and/or task scheduling to tightly-coupled hardware, RTOSUnit achieves up to 76% reduction in mean context-switch latency and can eliminate jitter entirely on selected cores.

This repository integrates RTOSUnit with two RISC-V processor cores and provides the full simulation infrastructure (cocotb + Verilator) to reproduce the paper's results. The NaxRiscv implementation is maintained in a separate repository.

### Supported Processors

| Core | Type | Pipeline | Bus Protocol |
|---|---|---|---|
| **CV32E40P** | MCU-class, in-order | 4-stage | OBI |
| **CVA6** | Application-class, OoO write-back | 6-stage | AXI |
| **NaxRiscv** | Superscalar, full OoO | Variable | AXI (w/ cache) |

NaxRiscv implementation: https://github.com/RTOSUnit/NaxRiscv

### RTOSUnit Configurations

Configurations are named by letter codes for features offloaded to hardware:

| Letter | Feature | Description |
|---|---|---|
| **S** | Store | HW context storing via alternate register file + background FSM |
| **L** | Load | HW context loading via restore FSM |
| **T** | Task Scheduling | HW ready/delay lists with priority-sorted queues |
| **D** | Dirty Bits | Skip saving unmodified registers |
| **O** | Load Omission | Skip loading if same task is re-selected |
| **P** | Preloading | Speculatively preload the likely-next context |

Evaluated & tested combinations: (S), (SL), (T), (ST), (SLT), (SD), (SDL), (SDT), (SDLT), (SDLO), (SDLOT), (SPLOT). **(vanilla)** = unmodified software baseline.

## Repository Structure

```
├── freertos/                   FreeRTOS firmware build
│   ├── FreeRTOS-Kernel/        Submodule: modified FreeRTOS kernel
│   ├── RTOSBench/              Submodule: RTOS benchmark suite
│   ├── bench_support/          Porting layer (cycle counting, trap init)
│   ├── Makefile                Cross-compilation (riscv32-unknown-elf-gcc)
│   ├── start.S                 RISC-V boot code
│   └── fake_rom.lds            Linker script (512K code + 448K data)
├── RTOSUnit/                   Submodule: Bluespec HW context-switch accelerator
├── cores/
│   ├── cv32e40p/               Submodule: modified CV32E40P core
│   └── cva6/                   Submodule: modified CVA6 core
├── cocotb_modules/             Python simulation testbenches
│   ├── cv32e40p.py             CV32E40P simulation driver
│   ├── cva6.py                 CVA6 simulation driver
│   ├── amba.py                 AXI bus protocol implementation
│   └── memutil.py              Memory modeling utilities
├── simulation_wrappers/        SystemVerilog testbench top-levels
├── Makefile                    Top-level build orchestration
├── Makefile_cv32e40p           CV32E40P cocotb/Verilator simulation
├── Makefile_cva6               CVA6 cocotb/Verilator simulation
├── util/plot_logs.py           Result visualization
└── .gitlab-ci.yml              CI pipeline (parametric test matrices)
```

## Dependencies

- RISC-V GNU Toolchain (RV32IM, `riscv32-unknown-elf-`)
- Verilator
- Python 3 with cocotb, cocotb\_bus, cocotbext-axi
- Bluespec Compiler (for building RTOSUnit from source)
- Optional: RV32E embedded toolchain for `EMBEDDED_ABI=Y`

A Docker image with all dependencies is available:

```bash
docker pull jhvjkcyyfdxghjk/multicontext_ci:latest
```

## Quick Start

### Clone with submodules

```bash
git clone --recursive https://github.com/esa-tu-darmstadt/RTOSUnit_Integration.git
cd RTOSUnit_Integration
```

### Run a simulation (CV32E40P, software baseline)

```bash
LOAD=SW STORE=SW SCHED=SW TEST=context-switch/round_robin make cv32e40p
```

### Run with full hardware acceleration (SLT)

```bash
LOAD=HW STORE=HW SCHED=HW TEST=context-switch/round_robin make cv32e40p
```

### Run on CVA6

```bash
LOAD=HW STORE=HW SCHED=HW TEST=context-switch/round_robin make cva6
```

Cycle counts are printed as `TOOK <cycles>` lines in the simulation output.

## Configuration

The FreeRTOS firmware build is controlled by environment variables:

### Required

| Variable | Values | Description |
|---|---|---|
| `LOAD` | `SW` / `HW` | Software vs. hardware register load |
| `STORE` | `SW` / `HW` | Software vs. hardware register store |
| `SCHED` | `SW` / `HW` | Software vs. hardware task scheduling |
| `TEST` | path | Benchmark test (e.g., `context-switch/round_robin`) |

### Optional

| Variable | Values | Default | Description |
|---|---|---|---|
| `DIRTY` | `Y`/`N` | `N` | Dirty-bit tracking |
| `LATCH` | `NO`/`LD`/`ST` | `NO` | Partial register latching |
| `TCB` | `SW`/`HW` | `SW` | Hardware TCB management |
| `EMBEDDED_ABI` | `Y`/`N` | `N` | RV32E 16-register ABI |
| `DUAL_PORT` | `Y`/`N` | `N` | Dual-port memory interface |
| `DEBUG` | `0`/`1` | `0` | Debug build (`-Og -ggdb3`) |

### Available Benchmarks

From [RTOSBench](https://github.com/RTOSUnit/RTOSBench):

- `context-switch/round_robin`
- `mq/mq`, `mq/mq_processing`, `mq/mq_workload`
- `mutex/mutex`, `mutex/mutex_processing`, `mutex/mutex_workload`, `mutex/mutex_pip`
- `semaphore/sem`, `semaphore/sem_prio`, `semaphore/sem_processing`, `semaphore/sem_workload`

## Build Targets

```bash
make freertos       # Build FreeRTOS firmware only
make ctxunit        # Compile RTOSUnit (Bluespec -> Verilog)
make cv32e40p       # Full pipeline: firmware + RTOSUnit + CV32E40P simulation
make cva6           # Full pipeline: firmware + RTOSUnit + CVA6 simulation
make gls_cv32e40p   # Gate-level simulation (CV32E40P)
make gls_cva6       # Gate-level simulation (CVA6)
make clean          # Clean firmware build
make clean_sim      # Clean simulation artifacts
```

## Related Repositories

All under the [RTOSUnit](https://github.com/RTOSUnit) organization:

| Repository | Description |
|---|---|
| [RTOSUnit](https://github.com/RTOSUnit/RTOSUnit) | Context Management IP (Bluespec) |
| [NaxRiscv](https://github.com/RTOSUnit/NaxRiscv) | NaxRiscv processor with RTOSUnit integration |
| [FreeRTOS](https://github.com/RTOSUnit/FreeRTOS) | Modified FreeRTOS kernel with HW context-switch support |
| [RTOSBench](https://github.com/RTOSUnit/RTOSBench) | RTOS benchmark suite |
| [cv32e40p](https://github.com/RTOSUnit/cv32e40p) | Modified CV32E40P with RTOSUnit interface |
| [cva6](https://github.com/RTOSUnit/cva6) | Modified CVA6 with RTOSUnit interface |
| [SpinalHDL](https://github.com/RTOSUnit/SpinalHDL) | SpinalHDL fork (for NaxRiscv) |

## Citation

```bibtex
@inproceedings{scheck2026rtosunit,
  author    = {Scheck, Markus and M\"{u}rmann, Tammo and Koch, Andreas},
  title     = {Co-Exploration of RISC-V Processor Microarchitectures and FreeRTOS Extensions for Lower Context-Switch Latency},
  booktitle = {Proceedings of the 30th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 2 (ASPLOS '26)},
  year      = {2026},
  location  = {Pittsburgh, PA, USA},
  publisher = {ACM},
  doi       = {10.1145/3779212.3790141}
}
```

## Acknowledgments

This work was supported by the German Federal Ministry of Research, Technology and Space in the project "Scale4Edge" (grant: 16ME0139).

## License

This project is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License ([CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)).
