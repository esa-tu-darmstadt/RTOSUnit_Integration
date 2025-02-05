
.PHONY: freertos
freertos:
	cd freertos && make

.PHONY: clean
clean:
	cd freertos && make clean

.PHONY: piccolo
piccolo: freertos
	cd RTOSUnit && make

.PHONY: ctxunit
ctxunit:
	cd RTOSUnit && TOP_MODULE=mkRTOSUnitSynth MAIN_MODULE=RTOSUnit make SIM_TYPE=VERILOG compile_top

.PHONY: cv32e40p
cv32e40p: freertos ctxunit
	make -f Makefile_cv32e40p