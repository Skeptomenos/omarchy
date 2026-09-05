#include <assert.h>
#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define __sched
#define TASK_UNINTERRUPTIBLE 0
#define ERESTARTSYS 512
#define current 0
#define DECLARE_SWAITQUEUE(name) int name = 0
#define raw_spin_lock_irqsave(lock, flags) ((void)(lock), (flags) = 0)
#define raw_spin_unlock_irqrestore(lock, flags) ((void)(lock), (void)(flags))
#define raw_spin_lock_irq(lock) ((void)(lock))
#define raw_spin_unlock_irq(lock) ((void)(lock))
#define swake_up_locked(wait, flags) ((void)(wait), (void)(flags))
#define signal_pending_state(state, task) ((void)(state), (void)(task), false)
#define __prepare_to_swait(head, wait) ((void)(head), (void)(wait))
#define __finish_swait(head, wait) ((void)(head), (void)(wait))
#define __set_current_state(state) ((void)(state))
#define might_sleep() ((void)0)
#define complete_acquire(x) ((void)(x))
#define complete_release(x) ((void)(x))

struct completion {
  unsigned int done;
  struct { int lock; } wait;
};

static struct completion *pending;
static long completion_tick;
static long now_tick;
static long schedule_timeout(long timeout);

#include "completion-extracted.c"

static long schedule_timeout(long timeout)
{
  assert(timeout > 0);
  if (completion_tick >= now_tick && completion_tick <= now_tick + timeout) {
    long remaining = timeout - (completion_tick - now_tick);
    now_tick = completion_tick;
    complete(pending);
    completion_tick = -1;
    return remaining;
  }
  now_tick += timeout;
  return 0;
}

static unsigned long run(long delay, unsigned long budget)
{
  struct completion done = {0};
  pending = &done;
  completion_tick = delay;
  now_tick = 0;
  return wait_for_completion_timeout(&done, budget);
}

int main(int argc, char **argv)
{
  assert(argc == 2);
  unsigned long candidate_budget = strtoul(argv[1], NULL, 10);
  assert(run(52, 50) == 0);
  assert(now_tick == 50);
  puts("PASS baseline: completion at tick52 exceeds budget50");
  fflush(stdout);
  if (run(52, candidate_budget) == 0) {
    fputs("FAIL delayed completion: candidate budget expired before tick52\n", stderr);
    return 1;
  }
  assert(now_tick == 52);
  assert(run(52, 100) == 48);
  assert(run(100, 100) == 1);
  assert(run(101, 100) == 0);
  assert(now_tick == 100);
  assert(run(-1, 100) == 0);
  assert(now_tick == 100);
  struct completion already_done = {0};
  complete(&already_done);
  assert(wait_for_completion_timeout(&already_done, 100) == 100);
  assert(already_done.done == 0);
  puts("PASS candidate: delayed, exact-deadline, beyond-deadline, absent, precompleted");
  return 0;
}
