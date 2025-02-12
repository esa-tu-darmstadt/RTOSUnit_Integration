
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
	cd RTOSUnit && CPU_WRITE_PORTS=2 TOP_MODULE=mkRTOSUnitSynth MAIN_MODULE=RTOSUnit make SIM_TYPE=VERILOG compile_top

.PHONY: cv32e40p
cv32e40p: freertos ctxunit
	make -f Makefile_cv32e40p