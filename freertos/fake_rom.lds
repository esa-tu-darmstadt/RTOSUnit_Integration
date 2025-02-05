ENTRY(_start)
OUTPUT_ARCH(riscv)

MEMORY
{
	IMEM (x) : ORIGIN = 0, LENGTH = 0x80000
	DMEM (rw) : ORIGIN = 0x80000, LENGTH = 0x70000
}

SECTIONS
{
	PROVIDE (_stack_top = ORIGIN(DMEM)+LENGTH(DMEM));
	PROVIDE (_heap_end = ORIGIN(DMEM)+LENGTH(DMEM));
	PROVIDE (_dexie_ctrl_address = 0x11000000);
	.text.init : {
	      * (.text.init);
	} >IMEM AT >IMEM

	.text.irq : ALIGN(0x100) {
	      * (.text.freertos_risc_v_trap_handler);
		  * (.text.trap_handler)
	} >IMEM AT >IMEM

	.text : {
	      * (.text*);
	} >IMEM AT >IMEM

	/* Place small read-only data close to instructions */
	.srodata : {
		  * (.srodata*);
	} >DMEM AT >DMEM

	.rodata : {
		  * (.rodata*);
	} >DMEM AT >DMEM

	/* start of data memory */
	/* small data sections first */
	.sdata : {
		  * (.sdata*);
	} >DMEM AT >DMEM

	.sbss : {
		 * (.sbss*);
	} > DMEM AT >DMEM

	.data : {
	      * (.data*);
	} >DMEM AT >DMEM

	.bss : {
	     * (.bss*);
	} > DMEM AT >DMEM
	PROVIDE ( _heap_start = .);
}
