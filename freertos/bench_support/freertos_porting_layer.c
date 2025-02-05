#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <FreeRTOS.h>
#include <task.h>
#include <semphr.h>
#include <queue.h>
#include "porting_layer.h"

void vSendString(const char* string) {}

// implemented in FreeRTOS RISC-V portASM.S
extern void freertos_risc_v_trap_handler(void);

#ifdef TRACING
#include "trace.h"
#endif

void no_initialize_test(no_task_entry_t init_function) {
    // initialize trap handler
	const int addr_and_mode = (int)freertos_risc_v_trap_handler | 0x0; // 0x0 is direct mode
	__asm__(
		"csrw mtvec, %0"
		:
		: "r" (addr_and_mode)
	);
    // Initialize hardware and peripherals, if any (not applicable for spike)
    // Initialize FreeRTOS and start the test task
    init_function(NULL);
    vTaskStartScheduler();
}

no_task_handle_t no_create_task(no_task_entry_t task_entry, char task_name[4], unsigned int prio) {
    no_task_handle_t task_handle;
    xTaskCreate(task_entry, (const char* const)task_name, configMINIMAL_STACK_SIZE, NULL, prio, &task_handle);
    return task_handle;
}

void no_task_yield() {
    taskYIELD();
}

void no_task_suspend(no_task_handle_t task) {
    vTaskSuspend(task);
}

void no_task_suspend_self() {
    vTaskSuspend(NULL);
}

void no_task_resume(no_task_handle_t task) {
    vTaskResume(task);
}

void no_task_delay(unsigned int ticks) {
    vTaskDelay(ticks);
}

void no_init_timer() {
    // Timer initialization not required for FreeRTOS on Spike
}

void no_disable_timer() {
    // Timer disabling not required for FreeRTOS on Spike
}

void no_reset_timer() {
    // Timer reset not required for FreeRTOS on Spike
}

no_time_t no_add_times(const no_time_t* base, unsigned int ticks) {
    no_time_t new_time = *base + ticks;
    return new_time;
}

uint64_t read_rdcycle_safe() {
    uint32_t cycle_low, cycle_high1, cycle_high2;

    asm volatile (
        "1:\n"
        "   rdcycleh    %0\n"			// Read upper 32-bits (cycle_high1)
        "   rdcycle     %1\n"			// Read lower 32-bits (cycle_low)
        "   rdcycleh    %2\n"			// Read upper 32-bits again (cycle_high2)
        "   bne         %0, %2, 1b"		// If the high bits changed, retry
        : "=&r" (cycle_high1), "=&r" (cycle_low), "=&r" (cycle_high2)
    );

    // Combine high and low parts into a 64-bit cycle count
    return ((uint64_t)cycle_high1 << 32) | cycle_low;
}

no_time_t no_time_get() {
	volatile no_time_t counter_value;
	counter_value = read_rdcycle_safe();
	//asm volatile ("rdcycle %0" : "=r" (counter_value));
	//asm volatile ("rdinstret %0" : "=r" (counter_value));		// behaves the same way as rdcycle
	return counter_value;
//    return xTaskGetTickCount();
}

long no_time_diff(const no_time_t* t1, const no_time_t* t2) {
    return (*t2 - *t1);
}

void no_sem_create(no_sem_t* sem, int current_value) {
    *sem = xSemaphoreCreateCounting(50, current_value);
}

void no_sem_wait(no_sem_t* sem) {
    xSemaphoreTake(*sem, portMAX_DELAY);
}

void no_sem_signal(no_sem_t* sem) {
    xSemaphoreGive(*sem);
}

void no_mutex_create(no_mutex_t* mutex) {
    *mutex = xSemaphoreCreateMutex();
}

void no_mutex_acquire(no_mutex_t* mutex) {
    xSemaphoreTake(*mutex, portMAX_DELAY);
}

void no_mutex_release(no_mutex_t* mutex) {
    xSemaphoreGive(*mutex);
}

void no_event_create(no_event_t* event) {
    *event = xEventGroupCreate();
}

void no_event_set(no_event_t* event) {
    xEventGroupSetBits(*event, 0x01);
}

void no_event_reset(no_event_t* event) {
    xEventGroupClearBits(*event, 0x01);
}

void no_event_wait(no_event_t* event) {
    xEventGroupWaitBits(*event, 0x01, pdTRUE, pdFALSE, portMAX_DELAY);
}

void no_mq_create(no_mq_t* mq, unsigned int length, unsigned int msgsize) {
    *mq = xQueueCreate(length, msgsize);
}

void no_mq_send(no_mq_t* mq, unsigned int msg) {
    xQueueSend(*mq, &msg, portMAX_DELAY);
}

void no_mq_receive(no_mq_t* mq) {
    unsigned int msg;
    xQueueReceive(*mq, &msg, portMAX_DELAY);
}

void no_serial_write(const char* string) {
    //printf("%s\n", string);
}

void no_cycle_reset_counter() {
    // Counter reset not required for FreeRTOS on Spike
}

unsigned int no_cycle_get_count() {
    return xTaskGetTickCount();
}

void no_single_result_report(char* prefix, int64_t value) {
    //printf("%s%lld\n", prefix, value);
    // todo calc prefix
//	char buf[strlen(prefix) + 20 + 1 + 8]; // size of prefix + max size of value + end + buffer
//	sprintf(buf, "%s%lld", value);
//	vSendString(buf);
}

void no_result_report(int64_t max, int64_t min, int64_t average) {
	asm ("nop");
    //printf("max=%lld\nmin=%lld\naverage=%lld\n", max, min, average);
//	char buf[20 + 3 * 20 + 1 + 8]; // 3 * max size of value +  + buffer
//	sprintf(buf, "max=%lld\nmin=%lld\naverage=%lld", max, min, average);
//	vSendString(buf);
}

#ifdef TRACING
void no_tracing_write_event(int ev_id) {
    // Implement tracing logic here if necessary
}

void no_tracing_report() {
    // Implement tracing report logic here if necessary
}
#endif

void vApplicationMallocFailedHook( void )
{

}


void vApplicationStackOverflowHook( TaskHandle_t pxTask, char *pcTaskName )
{
	( void ) pcTaskName;
	( void ) pxTask;

}