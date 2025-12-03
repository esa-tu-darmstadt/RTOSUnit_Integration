
.PHONY: freertos
freertos:
	cd freertos && make clean && make

.PHONY: clean
clean:
	cd freertos && make clean

.PHONY: clean_sim
clean_sim:
	rm -rf sim_build

.PHONY: piccolo
piccolo: freertos
	cd RTOSUnit && CPU_WRITE_PORTS=1 PICCOLO=1 make

.PHONY: ctxunit
ctxunit:
	cd RTOSUnit && CV32E40P=1 CPU_WRITE_PORTS=2 TOP_MODULE=mkRTOSUnitSynth MAIN_MODULE=RTOSUnit make SIM_TYPE=VERILOG compile_top

.PHONY: cv32e40p
cv32e40p: clean_sim freertos ctxunit
	make -f Makefile_cv32e40p

.PHONY: clean_sim cva6
cva6: freertos ctxunit
	PYTHONPATH=${PWD}/cocotb_modules make -f Makefile_cva6

.PHONY: clean_sim gls_cv32e40p
gls_cv32e40p: freertos
	make -f Makefile_cv32e40p_gls clean all

.PHONY: clean_sim gls_cva6
gls_cva6: freertos
	make -f Makefile_cva6_gls clean all