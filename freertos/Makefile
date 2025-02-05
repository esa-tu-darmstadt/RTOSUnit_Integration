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

CFLAGS = 

ifeq ($(SCHED),HW)
	CFLAGS += -D HWSCHED
endif

ifeq ($(LOAD),HW)
	CFLAGS += -D HWLOAD
endif

ifeq ($(STORE),HW)
	CFLAGS += -D HWSTORE
endif

XLEN ?= 32
CROSS   ?= riscv32-unknown-elf-
CC      = $(CROSS)gcc
CPP     = $(CROSS)cpp
OBJCOPY = $(CROSS)objcopy
OBJDUMP = $(CROSS)objdump
ARCH    = $(CROSS)ar
DEBUG ?= 0 

MARCH = rv32im_zicsr
MABI = ilp32
STACK_SIZE = 300

BUILD_DIR       = build
RTOS_SOURCE_DIR = $(abspath ./FreeRTOS-Kernel)
RTOS_BENCH_DIR = $(abspath ./RTOSBench)
RTOS_SUPPORT_DIR = $(abspath ./bench_support)

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
	-D NB_ITER=1
LDFLAGS = -nostartfiles \
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

all: bsv_binaries $(BUILD_DIR)/RTOSDemo$(XLEN).dump

bsv_binaries: $(BUILD_DIR)/RTOSDemo$(XLEN).bin
	python3 ./hexConverter.py $(BUILD_DIR)/RTOSDemo$(XLEN).bin -o $(BUILD_DIR)/RTOSDemo -b 0x80000

$(BUILD_DIR)/RTOSDemo$(XLEN).dump: $(BUILD_DIR)/RTOSDemo$(XLEN).axf
	$(OBJDUMP) -D $^ > $@

$(BUILD_DIR)/RTOSDemo$(XLEN).bin: $(BUILD_DIR)/RTOSDemo$(XLEN).axf
	$(OBJCOPY) -O binary $^ $@

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
