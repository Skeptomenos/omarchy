// SPDX-License-Identifier: GPL-2.0
/*
 * Userspace boundary adapters for exact TIPD function bodies.
 * Opaque kernel types have deliberately non-ABI shims. API scripts specify
 * returns, not hardware behavior. Only bounded log-reservation fixture threads
 * are permitted; there is no file, device, or network access.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <libfdt.h>

typedef uint8_t u8;
typedef uint16_t u16, __le16;
typedef uint32_t u32, __le32;
typedef uint64_t u64;
typedef int (*irq_handler_t)(int, void *);
#define __packed __attribute__((packed))
#define __must_check
#define __force
#define unlikely(value) (value)
#define UL(value) value##UL
#define ULL(value) value##ULL
#define BITS_PER_TYPE(type) (sizeof(type) * CHAR_BIT)
#define type_max(type) ((type)~(type)0)
#define const_true(value) (value)
#define BUILD_BUG_ON_ZERO(value) ((int)sizeof(struct { int : -!!(value); }))
static void *checked_container(const void *pointer, size_t offset, size_t bytes,
                               const char *type);
#define container_of(pointer, type, member) \
  ((type *)checked_container(pointer, offsetof(type, member), sizeof(type), #type))
#define le16_to_cpu(value) ((u16)(value))
#define le32_to_cpu(value) ((u32)(value))

struct fwnode_handle { int unused; };
struct device;
struct mutex { bool held; };
struct work_struct { void (*function)(struct work_struct *); };
struct delayed_work { struct work_struct work; bool pending; };
struct typec_capability { int unused; };
struct power_supply_desc { int unused; };
struct completion { int unused; };
enum power_supply_usb_type { SHIM_UNUSED_POWER_SUPPLY_TYPE };
struct gpio_desc { int unused; };
struct typec_port { int unused; };
struct typec_partner { int unused; };
struct typec_altmode { int unused; };
struct typec_mux { int unused; };
struct usb_role_switch { int unused; };
struct power_supply { int unused; };

_Static_assert(__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__, "little-endian pinned target");

/* @PINNED_DEFINITIONS@ */
/* @OF_FIXTURE@ */
/* @PINNED_TIPD_HEADER@ */

typedef struct { _Atomic int value; } atomic_t;
#define ATOMIC_INIT(initial) { .value = (initial) }

static int __attribute__((unused)) atomic_read(const atomic_t *counter)
{
  metadata_released();
  return atomic_load_explicit(&counter->value, memory_order_relaxed);
}

static void __attribute__((unused)) atomic_set(atomic_t *counter, int value)
{
  metadata_released();
  atomic_store_explicit(&counter->value, value, memory_order_relaxed);
}

static int __attribute__((unused)) atomic_cmpxchg(atomic_t *counter, int old, int next)
{
  metadata_released();
  atomic_compare_exchange_strong_explicit(&counter->value, &old, next,
                                          memory_order_seq_cst, memory_order_seq_cst);
  return old;
}

static struct { uintptr_t begin; size_t bytes; } object_ranges[8];
static size_t object_count, wrapper_conversions;

static void remember_object(void *pointer, size_t bytes)
{
  assert(pointer && bytes > 0 && bytes <= 16384 && object_count < 8);
  object_ranges[object_count].begin = (uintptr_t)pointer;
  object_ranges[object_count++].bytes = bytes;
}

static void forget_object(void *pointer)
{
  for (size_t i = 0; i < object_count; i++) {
    if (object_ranges[i].begin == (uintptr_t)pointer) {
      object_ranges[i] = object_ranges[--object_count];
      return;
    }
  }
  assert(!"unregistered allocation");
}

static void *checked_container(const void *pointer, size_t offset, size_t bytes,
                               const char *type)
{
  uintptr_t address = (uintptr_t)pointer;
  assert(address >= offset);
  uintptr_t start = address - offset;
  for (size_t i = 0; i < object_count; i++) {
    uintptr_t base = object_ranges[i].begin;
    size_t available = object_ranges[i].bytes;
    if (start >= base && start - base <= available && bytes <= available - (start - base)) {
      if (!strcmp(type, "struct tipd_t1_cd321x")) wrapper_conversions++;
      return (void *)start;
    }
  }
  assert(!"container exceeds the selected real allocation");
  return NULL;
}

struct event { const char *operation; int64_t a, b, c, d, e; };
static struct event ledger[1024];
static size_t event_count;
static char records[128][385];
static size_t record_count;
static pthread_mutex_t record_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t record_condition = PTHREAD_COND_INITIALIZER;
static bool reorder_records, second_record_seen;
static struct tps6598x *active_tps;
static struct cd321x *active_cd;
static struct device test_device;
static struct fwnode_handle connector;
static struct gpio_desc reset_gpio;
static struct usb_role_switch role_switch;
static struct typec_port port;
static struct typec_partner partner;
static struct typec_altmode dp_alt, tbt_alt;
static struct typec_mux mux;
static struct power_supply psy;
static int data_sentinel;
static void *system_power_efficient_wq = &data_sentinel;

enum failpoint {
  OK, GPIO, VID_READ, VID_ZERO, POWER_SWITCH, MODE_READ, PATCH_INIT,
  MASK_WRITE, STATUS_READ, ROLE_GET, PSY_REGISTER, PORT_REGISTER,
  POWER_READ, DATA_READ, IRQ_REQUEST
};
enum init_flags {
  RESET_PRESENT = 1, TPS25750 = 2, NO_POWER_CALLBACK = 4, PATCH_MODE = 8,
  ATTACHED = 16, CONNECTOR_PRESENT = 32, IRQ_PRESENT = 64, WAKEUP = 128,
  CONNECT_ERROR = 256, DISPATCH_DURING_IRQ = 512, CLEANUP_ERROR = 1024,
  SCHEDULE_FALSE = 2048
};
static struct {
  enum failpoint failure;
  unsigned int flags;
  enum usb_role old_role;
  int role_result, mux_result;
  bool partner_error;
  unsigned int init_depth;
  unsigned int worker_dispatches;
} script;

static void event(const char *operation, int64_t a, int64_t b, int64_t c,
                  int64_t d, int64_t e)
{
  assert(event_count < sizeof(ledger) / sizeof(ledger[0]));
  ledger[event_count++] = (struct event){operation, a, b, c, d, e};
}

static void check_tps(struct tps6598x *tps)
{
  assert(tps == active_tps);
}

static void check_device(struct device *dev)
{
  assert(dev == &test_device);
}

static struct mutex *mutex_enter(struct mutex *lock)
{
  assert(lock == &active_tps->lock && !lock->held);
  lock->held = true;
  event("lock", 0, 0, 0, 0, 0);
  return lock;
}

static void mutex_leave(struct mutex **slot)
{
  assert(*slot == &active_tps->lock && (*slot)->held);
  (*slot)->held = false;
  event("unlock", 0, 0, 0, 0, 0);
}

#define guard(kind) struct mutex *held_mutex __attribute__((cleanup(mutex_leave))) = mutex_enter
#define to_delayed_work(pointer) container_of(pointer, struct delayed_work, work)

static void collect_info(const char *format, ...) __attribute__((format(printf, 1, 2)));
static void collect_info(const char *format, ...)
{
  metadata_released();
  char message[385];
  va_list arguments;
  va_start(arguments, format);
  int size = vsnprintf(message, sizeof(message), format, arguments);
  va_end(arguments);
  assert(size > 0 && size + 2 <= 384 && message[size - 1] == '\n');
  assert(pthread_mutex_lock(&record_mutex) == 0);
  const char *sequence = strstr(message, "\"seq\":");
  assert(sequence);
  unsigned long value = strtoul(sequence + strlen("\"seq\":"), NULL, 10);
  assert(value >= 1 && value <= 128);
  while (reorder_records && value == 1 && !second_record_seen)
    assert(pthread_cond_wait(&record_condition, &record_mutex) == 0);
  assert(record_count < 128);
  memcpy(records[record_count], message, (size_t)size + 1);
  record_count++;
  if (reorder_records && value == 2) {
    second_record_seen = true;
    assert(pthread_cond_broadcast(&record_condition) == 0);
  }
  assert(pthread_mutex_unlock(&record_mutex) == 0);
}
#define pr_info(...) collect_info(__VA_ARGS__)

static void dev_err(struct device *dev, const char *format, ...)
{
  check_device(dev);
  assert(!strcmp(format, "Invalid DP pin assignment\n") ||
         !strcmp(format, "failed to register partner\n"));
  event("error", !strcmp(format, "Invalid DP pin assignment\n") ? 1 : 2, 0, 0, 0, 0);
}

static void dev_warn(struct device *dev, const char *format, ...)
{
  check_device(dev);
  assert(!strcmp(format, "%s: failed to register partner\n") ||
         !strcmp(format, "Unable to find the interrupt, switching to polling\n"));
  event("warning", !strcmp(format, "%s: failed to register partner\n") ? 1 : 2, 0, 0, 0, 0);
}

static int dev_err_probe(struct device *dev, int error, const char *format)
{
  check_device(dev);
  assert(!strcmp(format, "failed to get reset GPIO\n"));
  event("gpio_error", error, 0, 0, 0, 0);
  return error;
}

static struct gpio_desc *devm_gpiod_get_optional(struct device *dev, const char *name,
                                                enum gpiod_flags flags)
{
  check_device(dev);
  assert(!strcmp(name, "reset") && flags == GPIOD_OUT_LOW);
  event("gpio_get", flags, 0, 0, 0, 0);
  if (script.failure == GPIO) return ERR_PTR(-EIO);
  return script.flags & RESET_PRESENT ? &reset_gpio : NULL;
}

static void msleep(unsigned int duration)
{
  event("sleep", duration, 0, 0, 0, 0);
}

static bool device_is_compatible(struct device *dev, const char *compatible)
{
  check_device(dev);
  assert(!strcmp(compatible, "ti,tps25750"));
  event("device_compatible", 0, 0, 0, 0, 0);
  return !!(script.flags & TPS25750);
}

static int tps6598x_read32(struct tps6598x *tps, u8 reg, u32 *value)
{
  check_tps(tps);
  assert(reg == TPS_REG_VID);
  event("vid_read", reg, 0, 0, 0, 0);
  if (script.failure == VID_READ) return -EIO;
  *value = script.failure == VID_ZERO ? 0 : 0x1234;
  return 0;
}

static int cd321x_switch_power_state(struct tps6598x *tps, u8 state)
{
  check_tps(tps);
  event("power_switch", state, 0, 0, 0, 0);
  return script.failure == POWER_SWITCH ? -EIO : 0;
}

static int tps6598x_check_mode(struct tps6598x *tps)
{
  check_tps(tps);
  event("mode_read", 0, 0, 0, 0, 0);
  if (script.failure == MODE_READ) return -EIO;
  return script.flags & PATCH_MODE ? TPS_MODE_PTCH : TPS_MODE_APP;
}

static int cd321x_init(struct tps6598x *tps)
{
  check_tps(tps);
  event("patch_init", 0, 0, 0, 0, 0);
  return script.failure == PATCH_INIT ? -EIO : 0;
}

static int tps6598x_write64(struct tps6598x *tps, u8 reg, u64 value)
{
  check_tps(tps);
  assert(reg == TPS_REG_INT_MASK1 && (value == 0 || value == tps->data->irq_mask1));
  event("mask_write", reg, value, 0, 0, 0);
  if (value && script.failure == MASK_WRITE) return -EIO;
  if (!value && script.flags & CLEANUP_ERROR) return -EBUSY;
  return 0;
}

static bool tps6598x_read_status(struct tps6598x *tps, u32 *status)
{
  check_tps(tps);
  event("status_read", 0, 0, 0, 0, 0);
  if (script.failure == STATUS_READ) return false;
  *status = script.flags & ATTACHED ? TPS_STATUS_PLUG_PRESENT : 0;
  return true;
}

static struct fwnode_handle *device_get_named_child_node(struct device *dev, const char *name)
{
  check_device(dev);
  assert(!strcmp(name, "connector"));
  event("connector_get", 0, 0, 0, 0, 0);
  return script.flags & CONNECTOR_PRESENT ? &connector : NULL;
}

static void fw_devlink_purge_absent_suppliers(struct fwnode_handle *node)
{
  assert(node == &connector);
  event("purge_suppliers", 0, 0, 0, 0, 0);
}

static struct usb_role_switch *fwnode_usb_role_switch_get(struct fwnode_handle *node)
{
  assert(node == &connector || node == NULL);
  event("role_get", !!node, 0, 0, 0, 0);
  return script.failure == ROLE_GET ? ERR_PTR(-517) : &role_switch;
}

static int devm_tps6598_psy_register(struct tps6598x *tps)
{
  check_tps(tps);
  event("psy_register", 0, 0, 0, 0, 0);
  if (script.failure == PSY_REGISTER) return -EIO;
  tps->psy = &psy;
  return 0;
}

static void cd321x_update_work(struct work_struct *work);

static int cd321x_register_port(struct tps6598x *tps, struct fwnode_handle *node)
{
  check_tps(tps);
  assert(node == &connector || node == NULL);
  event("port_register", !!node, 0, 0, 0, 0);
  active_cd->update_work.work.function = cd321x_update_work;
  if (script.failure == PORT_REGISTER) return -EIO;
  tps->port = &port;
  active_cd->port_altmode_dp = &dp_alt;
  active_cd->port_altmode_tbt = &tbt_alt;
  active_cd->mux = &mux;
  active_cd->connector_fwnode = node;
  active_cd->state = (struct typec_mux_state){.mode = TYPEC_STATE_SAFE};
  return 0;
}

static bool tps6598x_read_power_status(struct tps6598x *tps)
{
  check_tps(tps);
  event("power_read", 0, 0, 0, 0, 0);
  if (script.failure == POWER_READ) return false;
  tps->pwr_status = 12;
  return true;
}

static bool cd321x_read_data_status(struct tps6598x *tps)
{
  check_tps(tps);
  event("data_read", 0, 0, 0, 0, 0);
  if (script.failure == DATA_READ) return false;
  tps->data_status = TPS_DATA_STATUS_DATA_CONNECTION | TPS_DATA_STATUS_DP_CONNECTION |
    TPS_DATA_STATUS_USB2_CONNECTION | CD321X_DATA_STATUS_HPD_LEVEL;
  return true;
}

static unsigned long msecs_to_jiffies(unsigned int milliseconds)
{
  /* Unit is retained as a labelled millisecond delay, not simulated wall time. */
  return milliseconds;
}

static bool cancel_delayed_work(struct delayed_work *work)
{
  assert(work == &active_cd->update_work);
  event("cancel_update", active_tps->status, active_cd->update_status.status,
        active_cd->update_status.status_changed, 0, 0);
  bool previous = work->pending;
  work->pending = false;
  return previous;
}

static bool schedule_delayed_work(struct delayed_work *work, unsigned long delay)
{
  assert(work == &active_cd->update_work && work->work.function == cd321x_update_work);
  event("schedule_update", delay, 0, 0, 0, 0);
  work->pending = true;
  return !(script.flags & SCHEDULE_FALSE);
}

static void tps6598x_poll_work(struct work_struct *work)
{
  (void)work;
  assert(!"unextracted polling body must never be dispatched");
}

static void init_delayed_work(struct delayed_work *work, void (*function)(struct work_struct *))
{
  assert(work == &active_tps->wq_poll && function == tps6598x_poll_work);
  event("poll_init", 0, 0, 0, 0, 0);
  work->work.function = function;
}
#define INIT_DELAYED_WORK(work, function) init_delayed_work(work, function)

static bool queue_delayed_work(void *queue, struct delayed_work *work, unsigned long delay)
{
  assert(queue == system_power_efficient_wq && work == &active_tps->wq_poll);
  event("queue_poll", delay, 0, 0, 0, 0);
  work->pending = true;
  return !(script.flags & SCHEDULE_FALSE);
}

static const char *dev_name(struct device *dev)
{
  check_device(dev);
  return "synthetic-tipd";
}

static void dispatch_worker(void)
{
  assert(active_cd->update_work.pending && !active_tps->lock.held);
  active_cd->update_work.pending = false;
  script.worker_dispatches++;
  active_cd->update_work.work.function(&active_cd->update_work.work);
}

static int cd321x_interrupt(int irq, void *data)
{
  (void)irq;
  (void)data;
  assert(!"unextracted interrupt body must never be dispatched");
  return 0;
}

static int devm_request_threaded_irq(struct device *dev, int irq, irq_handler_t first,
                                    irq_handler_t second, unsigned long flags,
                                    const char *name, void *data)
{
  check_device(dev);
  assert(irq == 7 && !first && second == cd321x_interrupt &&
         flags == (IRQF_SHARED | IRQF_ONESHOT) &&
         !strcmp(name, "synthetic-tipd") && data == active_tps);
  event("irq_request", irq, flags, 0, 0, 0);
  if (script.flags & DISPATCH_DURING_IRQ) {
    assert(script.init_depth == 1);
    dispatch_worker();
  }
  return script.failure == IRQ_REQUEST ? -EIO : 0;
}

static void fwnode_handle_put(struct fwnode_handle *node)
{
  assert(node == &connector || node == NULL);
  event("connector_put", !!node, 0, 0, 0, 0);
}

static bool device_property_read_bool(struct device *dev, const char *name)
{
  check_device(dev);
  assert(!strcmp(name, "wakeup-source"));
  event("wakeup_read", 0, 0, 0, 0, 0);
  return !!(script.flags & WAKEUP);
}

static int devm_device_init_wakeup(struct device *dev)
{
  check_device(dev);
  event("wakeup_init", 0, 0, 0, 0, 0);
  return 0;
}

static int enable_irq_wake(unsigned int irq)
{
  assert(irq == 7);
  event("irq_wake", irq, 0, 0, 0, 0);
  return 0;
}

static void tps6598x_disconnect(struct tps6598x *tps, u32 status)
{
  check_tps(tps);
  event("generic_disconnect", status, 0, 0, 0, 0);
}

static void cd321x_unregister_port(struct tps6598x *tps)
{
  check_tps(tps);
  event("port_unregister", 0, 0, 0, 0, 0);
}

static void usb_role_switch_put(struct usb_role_switch *sw)
{
  assert(sw == &role_switch);
  event("role_put", 0, 0, 0, 0, 0);
}

static int cd321x_reset(struct tps6598x *tps)
{
  check_tps(tps);
  event("reset", 0, 0, 0, 0, 0);
  return script.flags & CLEANUP_ERROR ? -EBUSY : 0;
}

static enum usb_role usb_role_switch_get_role(struct usb_role_switch *sw)
{
  assert(sw == &role_switch);
  event("get_role", script.old_role, 0, 0, 0, 0);
  return script.old_role;
}

static int usb_role_switch_set_role(struct usb_role_switch *sw, enum usb_role role)
{
  assert(sw == &role_switch);
  event("set_role", role, script.role_result, 0, 0, 0);
  return script.role_result;
}

static void drm_connector_oob_hotplug_event(struct fwnode_handle *node,
                                           enum drm_connector_status status)
{
  assert(node == &connector);
  event("hpd_call", status, 0, 0, 0, 0);
}

static int pointer_kind(const struct typec_partner *value)
{
  if (!value) return 0;
  if (IS_ERR(value)) return 2;
  assert(value == &partner);
  return 1;
}

static void typec_unregister_partner(struct typec_partner *value)
{
  assert(!IS_ERR(value));
  event("partner_unregister", pointer_kind(value), 0, 0, 0, 0);
}

static int typec_set_mode(struct typec_port *value, unsigned long mode)
{
  assert(value == &port);
  event("safe_mode", mode, 0, 0, 0, 0);
  return 0;
}

#define TYPEC_SETTER(name, type, label) \
  static void name(struct typec_port *value, type setting) \
  { \
    assert(value == &port); \
    event(label, setting, 0, 0, 0, 0); \
  }
TYPEC_SETTER(typec_set_pwr_opmode, enum typec_pwr_opmode, "pwr_mode")
TYPEC_SETTER(typec_set_pwr_role, enum typec_role, "pwr_role")
TYPEC_SETTER(typec_set_vconn_role, enum typec_role, "vconn")
TYPEC_SETTER(typec_set_orientation, enum typec_orientation, "orientation")
TYPEC_SETTER(typec_set_data_role, enum typec_data_role, "data_role")

static void power_supply_changed(struct power_supply *value)
{
  assert(value == &psy);
  event("power_changed", 0, 0, 0, 0, 0);
}

static struct typec_partner *typec_register_partner(struct typec_port *value,
                                                   const struct typec_partner_desc *desc)
{
  assert(value == &port && desc->accessory == TYPEC_ACCESSORY_NONE);
  /* Do not read fields the original caller leaves uninitialized. */
  event("partner_register", desc->usb_pd, !!desc->identity,
        desc->identity ? desc->identity->id_header : 0, script.partner_error, 0);
  return script.partner_error ? ERR_PTR(-EIO) : &partner;
}

static int typec_partner_set_identity(struct typec_partner *value)
{
  assert(value == &partner);
  event("identity_set", 0, 0, 0, 0, 0);
  return 0;
}

static int typec_mux_set(struct typec_mux *value, struct typec_mux_state *state)
{
  assert(value == &mux && state == &active_cd->state);
  int alt = state->alt == &dp_alt ? 1 : state->alt == &tbt_alt ? 2 : 0;
  assert(alt || !state->alt);
  uint32_t a = 0, b = 0, c = 0;
  if (alt == 1) {
    assert(state->data);
    struct typec_displayport_data data = *(struct typec_displayport_data *)state->data;
    a = data.status;
    b = data.conf;
  } else if (alt == 2) {
    assert(state->data);
    struct typec_thunderbolt_data data = *(struct typec_thunderbolt_data *)state->data;
    a = data.cable_mode;
    b = data.device_mode;
    c = data.enter_vdo;
  } else if (state->mode == TYPEC_MODE_USB4) {
    assert(state->data);
    struct enter_usb_data data = *(struct enter_usb_data *)state->data;
    a = data.eudo;
    b = data.active_link_training;
  } else {
    assert(!state->data);
  }
  event("mux_call", alt, state->mode, a, b, c);
  return script.mux_result;
}

static void cd321x_remove(struct tps6598x *tps)
{
  (void)tps;
  assert(!"remove is outside this extracted workload");
}
static void trace_cd321x_data_status(u32 status) { (void)status; }
static void trace_tps6598x_power_status(u16 status) { (void)status; }
static void trace_tps6598x_status(u32 status) { (void)status; }

/* @T1_HELPERS@ */
/* @PINNED_FUNCTIONS@ */
/* @PINNED_DATA_TABLE@ */
/* @DIAGNOSTIC_FIXTURE@ */
/* @FIXTURE_MAIN@ */
