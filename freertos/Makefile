# setup
# Check if the environment variables are set to 'SW' or 'HW'
ifeq ($(filter $(SCHED),SW HW),)
$(error SCHED must be set to either 'SW' or 'HW'.)
endif

ifeq ($(filter $(LOAD),SW HW),)
$(error LOAD must be set to either 'SW' or 'HW'.)
endif

ifeq ($(filter $(STORE),SW HW),)
$(error STORE must be set to either 'SW' or 'HW'.)
endif

TFM_ABI ?= N
ifeq ($(filter $(TFM_ABI),Y N),)
$(error STORE must be set to either 'Y' or 'N'.)
endif


CFLAGS = 
LDFLAGS = 

ifeq ($(SCHED),HW)
	CFLAGS += -D HWSCHED -D HWSCHED_CLINT
endif

ifeq ($(LOAD),HW)
	CFLAGS += -D HWLOAD
endif

ifeq ($(TCB),HW)
	CFLAGS += -D TCB_HW
endif

ifeq ($(STORE),HW)
	CFLAGS += -D HWSTORE
endif

ifeq ($(RV32I_CV32RT),Y)
	CFLAGS += -D RV32I_CV32RT
endif

XLEN ?= 32

ifeq ($(TFM_ABI),N)
# GCC
CROSS   ?= riscv32-unknown-elf-
CC      = $(CROSS)gcc
CPP     = $(CROSS)cpp
OBJCOPY = $(CROSS)objcopy
OBJDUMP = $(CROSS)objdump
ARCH    = $(CROSS)ar

ifeq ($(EMBEDDED_ABI),Y)
  MARCH = rv32em_zicsr
  MABI = ilp32e
  CROSS = $(RISCV_EMBEDDED_CC)
  CFLAGS += -D __riscv_32e
else
  MARCH = rv32im_zicsr
  MABI = ilp32
endif

CFLAGS += -DMY_SHITTY_TARGET="\"\""

else

# CLANG
CROSS   ?= /scratch/tfm/llvm-project/build/bin/
CC      = $(CROSS)clang
CPP     = $(CROSS)clang++
OBJCOPY = $(CROSS)llvm-objcopy
OBJDUMP = $(CROSS)llvm-objdump
ARCH    = $(CROSS)llvm-ar
# TODO do not hardcode
CFLAGS += -isystem /scratch/tfm/isax-tools-integration/testbenches/freertos/picolibc/build/install/picolibc/riscv32-unknown-elf/include

MARCH = rv32im_zicsr_ztf32m
MABI = ilp32tfm32

# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf7m\""
# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf8m\""
# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf9m\""
# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf10m\""
# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf11m\""
# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf12m\""
# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf13m\""
# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf14m\""
# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf15m\""
# CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf16m\""
CFLAGS += -DMY_SHITTY_TARGET="\"arch=+ztf32m\""
CFLAGS += -DTFM_ABI

# TODO do not hardcode
LDFLAGS += 	-L/scratch/tfm/isax-tools-integration/testbenches/freertos/picolibc/build/install/picolibc/riscv32-unknown-elf/lib/
endif

DEBUG ?= 0

STACK_SIZE = 300

BUILD_DIR       = build
RTOS_SOURCE_DIR = $(abspath ./FreeRTOS-Kernel)
RTOS_BENCH_DIR = $(abspath ./RTOSBench)
RTOS_SUPPORT_DIR = $(abspath ./bench_support)

CTX_BASE ?= f0000

CPPFLAGS = \
	-DportasmHANDLE_INTERRUPT=handle_trap \
	-I . -I ../Common/include \
	-I ${RTOS_SUPPORT_DIR}/include \
	-I $(RTOS_SOURCE_DIR)/include \
	-I $(RTOS_SOURCE_DIR)/portable/GCC/RISC-V \
	-I $(RTOS_SOURCE_DIR)/portable/GCC/RISC-V/chip_specific_extensions/RV32I_CLINT_no_extensions
CFLAGS  += -march=$(MARCH) -mabi=$(MABI) -mcmodel=medany \
	-Wall \
	-fmessage-length=0 \
	-ffunction-sections \
	-fdata-sections \
	-fno-builtin-printf \
	-fno-zero-initialized-in-bss \
	-D NB_ITER=20 \
	-D NB_WORKLOAD_TASK=2 \
	-D CTX_BASE=0x$(CTX_BASE)
LDFLAGS += -nostartfiles \
	-march=$(MARCH) -mabi=$(MABI) -mcmodel=medany \
	-Xlinker --gc-sections \
	-Xlinker --defsym=__stack_size=$(STACK_SIZE) \
	-fno-zero-initialized-in-bss

ifeq ($(DEBUG), 1)
    CFLAGS += -Og -ggdb3
else
    CFLAGS += -O3
endif

SRCS = \
	${RTOS_BENCH_DIR}/tests/${TEST}.c \
	${RTOS_SUPPORT_DIR}/freertos_porting_layer.c \
	$(RTOS_SOURCE_DIR)/event_groups.c \
	$(RTOS_SOURCE_DIR)/list.c \
	$(RTOS_SOURCE_DIR)/queue.c \
	$(RTOS_SOURCE_DIR)/stream_buffer.c \
	$(RTOS_SOURCE_DIR)/tasks.c \
	$(RTOS_SOURCE_DIR)/timers.c \
	$(RTOS_SOURCE_DIR)/portable/MemMang/heap_4.c \
	$(RTOS_SOURCE_DIR)/portable/GCC/RISC-V/port.c

ASMS = start.S \
	$(RTOS_SOURCE_DIR)/portable/GCC/RISC-V/portASM.S

OBJS = $(SRCS:%.c=$(BUILD_DIR)/%$(XLEN).o) $(ASMS:%.S=$(BUILD_DIR)/%$(XLEN).o)
DEPS = $(SRCS:%.c=$(BUILD_DIR)/%$(XLEN).d) $(ASMS:%.S=$(BUILD_DIR)/%$(XLEN).d)

all: bsv_binaries $(BUILD_DIR)/RTOSDemo$(XLEN).dump $(BUILD_DIR)/RTOSDemo$(XLEN)_num.dump

bsv_binaries: $(BUILD_DIR)/RTOSDemo$(XLEN).bin
	python3 ./hexConverter.py $(BUILD_DIR)/RTOSDemo$(XLEN).bin -o $(BUILD_DIR)/RTOSDemo -b 0x80000

$(BUILD_DIR)/RTOSDemo$(XLEN).dump: $(BUILD_DIR)/RTOSDemo$(XLEN).axf
	$(OBJDUMP) -D $^ > $@
$(BUILD_DIR)/RTOSDemo$(XLEN)_num.dump: $(BUILD_DIR)/RTOSDemo$(XLEN).axf
	$(OBJDUMP) -D -M numeric $^ > $@

$(BUILD_DIR)/RTOSDemo$(XLEN).bin: $(BUILD_DIR)/RTOSDemo$(XLEN).axf
	$(OBJCOPY) -O binary $^ $@
	truncate -s 1048576 $@

$(BUILD_DIR)/RTOSDemo$(XLEN).axf: $(OBJS) Makefile
	$(CC) $(LDFLAGS) $(OBJS) -Tfake_rom.lds -o $@

$(BUILD_DIR)/%$(XLEN).o: %.c Makefile
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@

$(BUILD_DIR)/%$(XLEN).o: %.S Makefile
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@

clean:
	rm -rf $(BUILD_DIR)

-include $(DEPS)
