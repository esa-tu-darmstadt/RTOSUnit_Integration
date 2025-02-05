/**
 * This testcase uses FreeRTOS as a real time operating system.
 * It requires DExIEs context switching capability as well as 
 * indirect calls to work. Indirect calls are used by the timer
 * to call the registered callback function (timer1_callback or timer2_callback).
 * 
 * Two timers and semaphores are created. Each timer gives its semaphore when its callback
 * function is called. A task is created that gives a third semaphore. Another task is created 
 * and waits for all three semaphores to be given. If it can take all semaphores then we signal 
 * the success to DExIE. If either of the two semaphores are not given within 10 ticks, 
 * we signal an error to DExIE.
*/
#include "FreeRTOS.h"
#include "task.h"
#include "timers.h"
#include "semphr.h"
#include "../customTests/rv_pe.h"

// implemented in FreeRTOS RISC-V portASM.S
extern void freertos_risc_v_trap_handler(void);

TimerHandle_t timer1;
TimerHandle_t timer2;

TaskHandle_t task1;

SemaphoreHandle_t semaphore1;
SemaphoreHandle_t semaphore2;
SemaphoreHandle_t semaphore3;

void error() {
    writeToCtrl(RETL, -1);
    setIntr();
}

void success() {
    writeToCtrl(RETL, 0);
    setIntr();
}

void timer1_callback(TimerHandle_t timer) 
{
	xSemaphoreGive(semaphore1);
	return;
}

void timer2_callback(TimerHandle_t timer) 
{
	xSemaphoreGive(semaphore2);
	return;
}

 void dexieTask ( void * parameters) 
 {
	// blocks and waits for the semaphores to be set from both timers and the task
	if(xSemaphoreTake(semaphore1, 10) && xSemaphoreTake(semaphore2, 10) && xSemaphoreTake(semaphore3, 10))
		success();
	else
		error();

	// neither dexie_success() nor dexie_error() can return
 }

  void dexieGiveTask ( void * parameters) 
 {
	vTaskDelay(2);
	xSemaphoreGive(semaphore3);
	while(1) {  }
 }

int main()
{
	// install FreeRTOS's trap handler
	const int addr_and_mode = (int)freertos_risc_v_trap_handler | 0x0; // 0x0 is direct mode
	__asm__(
		"csrw mtvec, %0"
		:
		: "r" (addr_and_mode)
	);

	// create two semaphores that the task will take and the timers will give
	semaphore1 = xSemaphoreCreateBinary();
	semaphore2 = xSemaphoreCreateBinary();
	semaphore3 = xSemaphoreCreateBinary();

	// create a new task that waits for semaphores
	xTaskCreate(dexieTask, "dexie task", 128, 0, 2, &task1);

	// Register timers. The callback functions are called through in icall
	// from the timer task.
	timer1 = xTimerCreate("Timer 1", 1, pdFALSE, (void*)0, timer1_callback);
	timer2 = xTimerCreate("Timer 2", 2, pdFALSE, (void*)0, timer2_callback);

	// start timers, wait 1 / 2 ticks for timer1 / timer2 to start
	xTimerStart(timer1, portMAX_DELAY);
	xTimerStart(timer2, portMAX_DELAY);

	// create a task that gives the third semaphore
	xTaskCreate(dexieGiveTask, "task2", 128, 0, 2, NULL);
	
    vTaskStartScheduler();
    return 0;
}

void vApplicationMallocFailedHook( void )
{
	taskDISABLE_INTERRUPTS();
	error(); // does not return
}


void vApplicationStackOverflowHook( TaskHandle_t pxTask, char *pcTaskName )
{
	( void ) pcTaskName;
	( void ) pxTask;

	taskDISABLE_INTERRUPTS();
	error(); // does not return
}
