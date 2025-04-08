
.PHONY: freertos
freertos:
	cd freertos && make clean && make

.PHONY: clean
clean:
	cd freertos && make clean

.PHONY: piccolo
piccolo: freertos
	cd RTOSUnit && CPU_WRITE_PORTS=1 PICCOLO=1 make

.PHONY: ctxunit
ctxunit:
	cd RTOSUnit && CV32E40P=1 CPU_WRITE_PORTS=2 TOP_MODULE=mkRTOSUnitSynth MAIN_MODULE=RTOSUnit make SIM_TYPE=VERILOG compile_top

.PHONY: cv32e40p
cv32e40p: freertos ctxunit
	make -f Makefile_cv32e40p

.PHONY: cva6
cva6: freertos ctxunit
	PYTHONPATH=${PWD}/cocotb_modules make -f Makefile_cva6

.PHONY: gls
gls: freertos
	make -f Makefile_cv32e40p_gls clean all