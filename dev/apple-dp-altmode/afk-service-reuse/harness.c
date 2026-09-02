#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef int64_t s64;
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uintptr_t dma_addr_t;

typedef struct {
  bool held;
} spinlock_t;

struct completion {
  bool done;
};

#define AFK_MAX_CHANNEL 16
#define MAX_PENDING_CMDS 16
#define ESHUTDOWN 108
#define ENOMEM 12
#define ETIMEDOUT 110
#define GFP_KERNEL 0
#define MSEC_PER_SEC 1000
#define EPIC_TYPE_COMMAND 3
#define EPIC_CAT_COMMAND 0x30
#define DECLARE_COMPLETION_ONSTACK(name) struct completion name = { 0 }
#define spin_lock_irqsave(lock, flags) do { harness_spin_lock(lock); (flags) = 0; } while (0)
#define spin_unlock_irqrestore(lock, flags) do { (void)(flags); harness_spin_unlock(lock); } while (0)
#define spin_lock(lock) harness_spin_lock(lock)
#define spin_unlock(lock) harness_spin_unlock(lock)
#define bitmap_empty(map, count) ((void)(count), (map)[0] == 0)
#define WARN_ON(condition) (condition)
#define READ_ONCE(value) (value)
#define WRITE_ONCE(destination, value) ((destination) = (value))
#define trace_dcpavserv_init(dcp, unit) do { (void)(dcp); (void)(unit); } while (0)
#define dev_err(device, format, ...) do { (void)(device); (void)(format); } while (0)

struct apple_epic_service;
struct apple_dcp_afkep;

static void harness_spin_lock(spinlock_t *lock);
static void harness_spin_unlock(spinlock_t *lock);
static bool harness_spin_trylock(spinlock_t *lock);

struct apple_epic_service_ops {
  const char name[32];
  bool reusable;
};

struct epic_cmd_info {
  uint16_t tag;
  void *rxbuf;
  void *txbuf;
  uintptr_t rxbuf_dma;
  uintptr_t txbuf_dma;
  size_t rxlen;
  size_t txlen;
  u32 retcode;
  bool done;
  bool free_on_ack;
  struct completion *completion;
};

struct apple_epic_service {
  const struct apple_epic_service_ops *ops;
  struct apple_dcp_afkep *ep;
  struct epic_cmd_info cmds[MAX_PENDING_CMDS];
  unsigned long cmd_map[1];
  u8 cmd_tag;
  spinlock_t lock;
  u32 external_users;
  u32 channel;
  bool enabled;
  bool torndown;
  bool retirement_requested;
  void *cookie;
  struct {
    void *entry;
    u8 *scratch;
  } debugfs;
};

struct dcpavserv {
  bool enabled;
  spinlock_t lock;
  struct completion enable_completion;
  u32 unit;
  struct apple_epic_service *service;
};

struct apple_dcp {
  void *dev;
  struct dcpavserv dcpavserv;
};

struct apple_dcp_afkep {
  struct apple_dcp *dcp;
  struct apple_epic_service services[AFK_MAX_CHANNEL];
  u32 num_channels;
};

struct epic_cmd {
  u32 retcode;
  uint64_t rxbuf;
  uint64_t txbuf;
  u32 rxlen;
  u32 txlen;
  u8 rxcookie;
  u8 txcookie;
};

static struct apple_epic_service *harness_command_service;
static int harness_send_result;
static int harness_send_count;
static bool harness_attempt_teardown;
static bool harness_teardown_blocked;
static bool harness_teardown_transitioned;

static void harness_spin_lock(spinlock_t *lock)
{
  if (lock->held)
    abort();
  lock->held = true;
}

static void harness_spin_unlock(spinlock_t *lock)
{
  if (!lock->held)
    abort();
  lock->held = false;
}

static bool harness_spin_trylock(spinlock_t *lock)
{
  if (lock->held)
    return false;
  lock->held = true;
  return true;
}

static void bitmap_release_region(unsigned long *map, u8 index, int order)
{
  (void)order;
  map[0] &= ~(1UL << index);
}

static int bitmap_find_free_region(unsigned long *map, u32 count, int order)
{
  (void)order;
  for (u32 index = 0; index < count; index++) {
    if (!(map[0] & (1UL << index))) {
      map[0] |= 1UL << index;
      return (int)index;
    }
  }

  return -28;
}

static void complete(struct completion *completion)
{
  completion->done = true;
}

static void init_completion(struct completion *completion)
{
  completion->done = false;
}

static void reinit_completion(struct completion *completion)
{
  completion->done = false;
}

static unsigned long msecs_to_jiffies(unsigned long milliseconds)
{
  return milliseconds;
}

static unsigned long wait_for_completion_timeout(
  struct completion *completion,
  unsigned long timeout)
{
  (void)completion;
  (void)timeout;
  return 1;
}

static void *dma_alloc_coherent(
  void *device,
  size_t size,
  dma_addr_t *dma_address,
  int flags)
{
  void *allocation;

  (void)device;
  (void)flags;
  allocation = calloc(1, size ? size : 1);
  *dma_address = (dma_addr_t)allocation;
  return allocation;
}

static void dma_free_coherent(
  void *device,
  size_t size,
  void *allocation,
  dma_addr_t dma_address)
{
  (void)device;
  (void)size;
  (void)dma_address;
  free(allocation);
}

static u32 cpu_to_le32(u32 value)
{
  return value;
}

static uint64_t cpu_to_le64(uint64_t value)
{
  return value;
}

static int afk_send_epic(
  struct apple_dcp_afkep *ep,
  u32 channel,
  u16 tag,
  int type,
  int category,
  u8 subtype,
  const void *payload,
  size_t payload_length)
{
  (void)ep;
  (void)channel;
  (void)tag;
  (void)type;
  (void)category;
  (void)subtype;
  (void)payload;
  (void)payload_length;
  harness_send_count++;

  if (harness_attempt_teardown) {
    if (!harness_spin_trylock(&harness_command_service->lock)) {
      harness_teardown_blocked = true;
    } else {
      harness_command_service->torndown = true;
      harness_teardown_transitioned = true;
      harness_spin_unlock(&harness_command_service->lock);
    }
  }

  return harness_send_result;
}

static struct apple_epic_service *
afk_epic_prepare_service_current(struct apple_dcp_afkep *ep)
{
  u32 ch_idx;

  if (ep->num_channels >= AFK_MAX_CHANNEL)
    return NULL;

  ch_idx = ep->num_channels++;
  return &ep->services[ch_idx];
}

static struct apple_epic_service *
afk_epic_prepare_service_unsafe(struct apple_dcp_afkep *ep)
{
  struct apple_epic_service *service;
  u32 ch_idx;

  for (ch_idx = 0; ch_idx < ep->num_channels; ch_idx++)
    if (!ep->services[ch_idx].enabled)
      goto prepare;

  if (ep->num_channels >= AFK_MAX_CHANNEL)
    return NULL;

  ch_idx = ep->num_channels++;

prepare:
  service = &ep->services[ch_idx];
  memset(service, 0, sizeof(*service));
  return service;
}

static int afk_epic_reserve_command_unsafe(struct apple_epic_service *service)
{
  return bitmap_find_free_region(service->cmd_map, MAX_PENDING_CMDS, 0);
}

AFK_CANDIDATE_HELPER_BODY

static const struct apple_epic_service_ops reusable_av_ops = {
  .name = "dcpav-service-epic",
  .reusable = true,
};

static const struct apple_epic_service_ops reusable_dp_ops = {
  .name = "dcpdp-service-epic",
  .reusable = true,
};

static const struct apple_epic_service_ops ordinary_ops = {
  .name = "ordinary-service",
  .reusable = false,
};

static void require(bool condition, const char *message)
{
  if (condition)
    return;

  fprintf(stderr, "FAIL: %s\n", message);
  exit(EXIT_FAILURE);
}

static void reset_send_probe(struct apple_epic_service *service, int result)
{
  harness_command_service = service;
  harness_send_result = result;
  harness_send_count = 0;
  harness_attempt_teardown = false;
  harness_teardown_blocked = false;
  harness_teardown_transitioned = false;
}

static void initialize_service(
  struct apple_epic_service *service,
  struct apple_dcp_afkep *ep,
  const struct apple_epic_service_ops *ops,
  u32 channel)
{
  service->ops = ops;
  service->ep = ep;
  service->channel = channel;
  service->enabled = true;
}

static void mark_teardown(struct apple_epic_service *service)
{
  service->torndown = true;
}

static struct apple_epic_service *find_enabled_service(
  struct apple_dcp_afkep *ep,
  u32 channel)
{
  for (u32 index = 0; index < ep->num_channels; index++)
    if (ep->services[index].enabled && ep->services[index].channel == channel)
      return &ep->services[index];

  return NULL;
}

static void require_stale_state_cleared(const struct apple_epic_service *service)
{
  require(service->ops == NULL, "stale ops pointer survived reuse");
  require(service->ep == NULL, "stale endpoint pointer survived reuse");
  require(service->cmd_map[0] == 0, "stale command bitmap survived reuse");
  require(service->cmd_tag == 0, "stale command tag survived reuse");
  require(service->cmds[0].tag == 0, "stale command entry tag survived reuse");
  require(service->cmds[0].rxbuf == NULL, "stale command receive buffer survived reuse");
  require(service->cmds[0].txbuf == NULL, "stale command transmit buffer survived reuse");
  require(service->cmds[0].completion == NULL, "stale command completion survived reuse");
  require(service->cmds[0].rxlen == 0, "stale command receive length survived reuse");
  require(service->cmds[0].txlen == 0, "stale command transmit length survived reuse");
  require(!service->cmds[0].done, "stale command completion state survived reuse");
  require(!service->cmds[0].free_on_ack, "stale command acknowledgement state survived reuse");
  require(service->external_users == 0, "stale external user count survived reuse");
  require(service->channel == 0, "stale channel survived reuse");
  require(!service->enabled, "reused service started enabled");
  require(!service->torndown, "stale teardown state survived reuse");
  require(!service->retirement_requested, "stale retirement request survived reuse");
  require(service->cookie == NULL, "stale owner cookie survived reuse");
  require(service->debugfs.entry == NULL, "stale debugfs entry survived reuse");
  require(service->debugfs.scratch == NULL, "stale debugfs scratch survived reuse");
}

static void exercise_stock_generation_failure(void)
{
  struct apple_dcp_afkep ep = { 0 };

  for (u32 generation = 0; generation < 10; generation++) {
    for (u32 member = 0; member < 2; member++) {
      struct apple_epic_service *service = afk_epic_prepare_service_current(&ep);

      if (!service) {
        fprintf(stderr, "CAPACITY: generation=%u member=%u slots=%u\n",
          generation, member, ep.num_channels);
        exit(EXIT_FAILURE);
      }
      service->enabled = false;
    }
  }
}

static void exercise_unsafe_disabled_pending_reuse(void)
{
  struct apple_dcp_afkep ep = { 0 };
  struct apple_epic_service *pending = afk_epic_prepare_service_current(&ep);

  require(pending != NULL, "unsafe setup allocation failed");
  initialize_service(pending, &ep, &reusable_dp_ops, 41);
  pending->torndown = true;
  pending->retirement_requested = true;
  pending->enabled = false;
  pending->cmd_map[0] = 1;
  pending->cmds[0].tag = 0x700;

  struct apple_epic_service *reused = afk_epic_prepare_service_unsafe(&ep);

  if (reused == pending && pending->cmd_map[0] == 0) {
    fputs("UNSAFE_REUSE: disabled pending slot erased\n", stderr);
    exit(EXIT_FAILURE);
  }
  require(false, "unsafe candidate unexpectedly preserved the pending slot");
}

static void exercise_unsafe_post_teardown_send(void)
{
  struct apple_dcp dcp = { 0 };
  struct apple_dcp_afkep ep = { .dcp = &dcp };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);
  int send_count = 0;

  require(service != NULL, "unsafe send service allocation failed");
  initialize_service(service, &ep, &reusable_av_ops, 45);
  dcpavserv_init(service, "dcpav-service-epic", NULL, 0);

  struct apple_epic_service *user = dcpavserv_get(&dcp.dcpavserv);

  require(user == service, "unsafe send owner acquisition failed");
  mark_teardown(service);
  dcpavserv_teardown(service);

  if (afk_epic_reserve_command_unsafe(service) >= 0)
    send_count++;
  dcpavserv_put(user);

  if (send_count == 1 && service->cmd_map[0] == 1 && service->enabled) {
    fputs("UNSAFE_SEND: post-teardown command stranded retirement\n", stderr);
    exit(EXIT_FAILURE);
  }
  require(false, "unsafe command admission unexpectedly rejected teardown state");
}

static void exercise_unsafe_reserve_teardown_send(void)
{
  struct apple_dcp_afkep ep = { 0 };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);
  unsigned long flags;
  int reservation;

  require(service != NULL, "unsafe race service allocation failed");
  initialize_service(service, &ep, &reusable_dp_ops, 47);
  reset_send_probe(service, 0);
  harness_attempt_teardown = true;

  spin_lock_irqsave(&service->lock, flags);
  reservation = afk_epic_reserve_command_locked(service);
  spin_unlock_irqrestore(&service->lock, flags);
  require(reservation == 0, "unsafe race command reservation failed");

  afk_send_epic(service->ep, service->channel, 0,
    EPIC_TYPE_COMMAND, EPIC_CAT_COMMAND, 0, NULL, 0);

  if (harness_teardown_transitioned && harness_send_count == 1) {
    fputs("UNSAFE_RACE: teardown transitioned between reserve and send\n", stderr);
    exit(EXIT_FAILURE);
  }
  require(false, "unsafe reserve-teardown-send race unexpectedly serialized");
}

static void exercise_ten_two_service_generations(void)
{
  struct apple_dcp dcp = { 0 };
  struct apple_dcp_afkep ep = { .dcp = &dcp };

  for (u32 generation = 0; generation < 10; generation++) {
    struct apple_epic_service *av = afk_epic_prepare_service(&ep);
    struct apple_epic_service *dp;

    require(av != NULL, "AV service allocation failed before generation ten");
    initialize_service(av, &ep, &reusable_av_ops, generation * 2 + 1);
    dcpavserv_init(av, "dcpav-service-epic", NULL, 0);

    dp = afk_epic_prepare_service(&ep);
    require(dp != NULL, "DP service allocation failed before generation ten");
    initialize_service(dp, &ep, &reusable_dp_ops, generation * 2 + 2);

    mark_teardown(av);
    dcpavserv_teardown(av);
    require(dcp.dcpavserv.service == NULL, "AV owner pointer survived teardown");
    mark_teardown(dp);
    dcpdpserv_teardown(dp);
  }

  require(ep.num_channels == 2, "quiescent generations grew the service high-water mark");
}

static void exercise_disabled_but_pending_not_reused(void)
{
  struct apple_dcp_afkep ep = { 0 };
  struct apple_epic_service *pending = afk_epic_prepare_service(&ep);

  require(pending != NULL, "pending service allocation failed");
  initialize_service(pending, &ep, &reusable_dp_ops, 61);
  pending->torndown = true;
  pending->retirement_requested = true;
  pending->enabled = false;
  pending->cmd_map[0] = 1;
  pending->cmds[0].tag = 0xb00;

  struct apple_epic_service *next = afk_epic_prepare_service(&ep);

  require(next != NULL, "fresh slot allocation failed for disabled pending service");
  require(next != pending, "disabled pending service was reused");
  require(pending->cmd_map[0] == 1, "disabled pending command map was erased");
  require(pending->cmds[0].tag == 0xb00, "disabled pending command tag was erased");
}

static void exercise_enabled_torndown_late_reply(void)
{
  struct apple_dcp_afkep ep = { 0 };
  struct apple_epic_service *pending = afk_epic_prepare_service(&ep);

  require(pending != NULL, "late-reply service allocation failed");
  initialize_service(pending, &ep, &reusable_dp_ops, 71);
  pending->torndown = true;
  pending->retirement_requested = true;
  pending->cmd_map[0] = 1;
  pending->cmds[0].tag = 0xc00;

  require(find_enabled_service(&ep, 71) == pending,
    "enabled torn-down service stopped resolving before its late reply");

  struct apple_epic_service *next = afk_epic_prepare_service(&ep);

  require(next != pending, "enabled torn-down service was reused before its late reply");
  afk_epic_release_command_locked(pending, 0);
  require(!pending->enabled, "final command release did not retire the service");
  require(find_enabled_service(&ep, 71) == NULL,
    "retired service remained visible after the final reply");

  struct apple_epic_service *reused = afk_epic_prepare_service(&ep);

  require(reused == pending, "retired service was not reused after its final reply");
  require_stale_state_cleared(reused);
}

static void exercise_owner_release_order(void)
{
  struct apple_dcp dcp = { 0 };
  struct apple_dcp_afkep ep = { .dcp = &dcp };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);

  require(service != NULL, "owner service allocation failed");
  initialize_service(service, &ep, &reusable_av_ops, 81);
  dcpavserv_init(service, "dcpav-service-epic", NULL, 0);

  struct apple_epic_service *user = dcpavserv_get(&dcp.dcpavserv);

  require(user == service, "owner acquisition failed");
  service->cmd_map[0] = 1;
  mark_teardown(service);
  dcpavserv_teardown(service);
  require(dcp.dcpavserv.service == NULL, "owner pointer was not cleared during teardown");
  require(service->cookie == NULL, "service owner cookie was not cleared during teardown");
  require(service->enabled, "service retired while a transient user and command remained");

  afk_epic_release_command_locked(service, 0);
  require(service->enabled, "service retired before its transient user released it");

  struct apple_epic_service *next = afk_epic_prepare_service(&ep);

  require(next != service, "service was reused while its transient user remained");
  dcpavserv_put(user);
  require(!service->enabled, "last transient-user release did not retire the service");

  struct apple_epic_service *reused = afk_epic_prepare_service(&ep);

  require(reused == service, "service was not reused after owner and user release");
  require_stale_state_cleared(reused);
}

static void exercise_mismatched_owner_teardown(void)
{
  struct apple_dcp dcp = { 0 };
  struct apple_dcp_afkep ep = { .dcp = &dcp };
  struct apple_epic_service *old = afk_epic_prepare_service(&ep);
  struct apple_epic_service *current;

  require(old != NULL, "old owner service allocation failed");
  initialize_service(old, &ep, &reusable_av_ops, 86);
  old->cookie = &dcp.dcpavserv;

  current = afk_epic_prepare_service(&ep);
  require(current != NULL, "current owner service allocation failed");
  initialize_service(current, &ep, &reusable_av_ops, 87);
  dcp.dcpavserv.enabled = true;
  dcp.dcpavserv.service = current;

  mark_teardown(old);
  dcpavserv_teardown(old);

  require(dcp.dcpavserv.service == current,
    "old teardown cleared the current owner pointer");
  require(dcp.dcpavserv.enabled, "old teardown disabled the current owner");
  require(old->cookie == NULL, "old teardown retained its stale owner cookie");
  require(!old->enabled, "old quiescent service did not retire");

  struct apple_epic_service *reused = afk_epic_prepare_service(&ep);

  require(reused == old, "old service was not reusable after cookie retirement");
  require(dcp.dcpavserv.service == current,
    "old slot reuse changed the current owner pointer");
}

static void exercise_deferred_free_order(void)
{
  struct apple_dcp_afkep ep = { 0 };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);
  void *rxbuf;
  void *txbuf;

  require(service != NULL, "deferred-free service allocation failed");
  initialize_service(service, &ep, &reusable_dp_ops, 88);
  service->torndown = true;
  service->retirement_requested = true;
  service->cmd_map[0] = 1;
  service->cmds[0].rxbuf = (void *)(uintptr_t)0x66;
  service->cmds[0].txbuf = (void *)(uintptr_t)0x77;
  rxbuf = service->cmds[0].rxbuf;
  txbuf = service->cmds[0].txbuf;

  afk_epic_release_command_locked(service, 0);
  require(!service->enabled, "deferred-free service did not retire after map release");

  struct apple_epic_service *reused = afk_epic_prepare_service(&ep);

  require(reused == service, "deferred-free service was not reused");
  require(reused->cmds[0].rxbuf == NULL, "reused service retained receive buffer state");
  require(reused->cmds[0].txbuf == NULL, "reused service retained transmit buffer state");
  require(rxbuf == (void *)(uintptr_t)0x66, "local receive buffer ownership was lost");
  require(txbuf == (void *)(uintptr_t)0x77, "local transmit buffer ownership was lost");
}

static void exercise_post_teardown_command_rejected(void)
{
  struct apple_dcp dcp = { 0 };
  struct apple_dcp_afkep ep = { .dcp = &dcp };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);
  u8 input = 0x12;
  u8 output = 0;

  require(service != NULL, "command admission service allocation failed");
  initialize_service(service, &ep, &reusable_av_ops, 89);
  dcpavserv_init(service, "dcpav-service-epic", NULL, 0);

  struct apple_epic_service *user = dcpavserv_get(&dcp.dcpavserv);

  require(user == service, "command admission owner acquisition failed");
  mark_teardown(service);
  dcpavserv_teardown(service);
  reset_send_probe(service, 0);

  int result = afk_send_command(service, 0, &input, sizeof(input),
    &output, sizeof(output), NULL);

  require(result == -ESHUTDOWN, "post-teardown command was not rejected");
  require(harness_send_count == 0, "post-teardown command reached the send boundary");
  require(service->cmd_map[0] == 0, "rejected command changed the command bitmap");
  require(service->enabled, "service retired before the acquired user released it");

  dcpavserv_put(user);
  require(!service->enabled, "rejected command prevented retirement after final put");
}

static void exercise_reserve_teardown_send_serialized(void)
{
  struct apple_dcp dcp = { 0 };
  struct apple_dcp_afkep ep = { .dcp = &dcp };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);
  u8 input = 0x34;
  u8 output = 0;
  unsigned long flags;
  int result;

  require(service != NULL, "serialized send service allocation failed");
  initialize_service(service, &ep, &reusable_av_ops, 90);
  dcpavserv_init(service, "dcpav-service-epic", NULL, 0);

  struct apple_epic_service *user = dcpavserv_get(&dcp.dcpavserv);

  require(user == service, "serialized send owner acquisition failed");
  reset_send_probe(service, 0);
  harness_attempt_teardown = true;

  result = afk_send_command(user, 0, &input, sizeof(input),
    &output, sizeof(output), NULL);

  require(result == 0, "serialized command failed");
  require(harness_send_count == 1, "serialized command missed the send boundary");
  require(harness_teardown_blocked,
    "teardown acquired the service during the send boundary");
  require(!harness_teardown_transitioned,
    "teardown transitioned the service before the send boundary");
  require(service->cmd_map[0] == 0,
    "successful serialized command retained its bitmap slot");

  spin_lock_irqsave(&service->lock, flags);
  mark_teardown(service);
  spin_unlock_irqrestore(&service->lock, flags);
  dcpavserv_teardown(service);
  require(service->enabled, "serialized service retired before final put");
  dcpavserv_put(user);
  require(!service->enabled, "serialized service did not retire after final put");
}

static void exercise_send_failure_cleanup(void)
{
  struct apple_dcp dcp = { 0 };
  struct apple_dcp_afkep ep = { .dcp = &dcp };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);
  u8 input = 0x56;
  u8 output = 0;
  unsigned long flags;
  int result;

  require(service != NULL, "send failure service allocation failed");
  initialize_service(service, &ep, &reusable_dp_ops, 91);
  reset_send_probe(service, -5);
  harness_attempt_teardown = true;

  result = afk_send_command(service, 0, &input, sizeof(input),
    &output, sizeof(output), NULL);

  require(result == -5, "send failure result was not preserved");
  require(harness_send_count == 1, "failed command missed the send boundary");
  require(harness_teardown_blocked,
    "teardown acquired the service during the failed send boundary");
  require(!harness_teardown_transitioned,
    "teardown transitioned the service during the failed send boundary");
  require(service->cmd_map[0] == 0,
    "failed send retained its command bitmap slot");
  require(!service->lock.held, "failed send retained the service lock");

  spin_lock_irqsave(&service->lock, flags);
  mark_teardown(service);
  spin_unlock_irqrestore(&service->lock, flags);
  dcpdpserv_teardown(service);
  require(!service->enabled, "failed send prevented later retirement");
}

static void exercise_active_command_admitted(void)
{
  struct apple_dcp_afkep ep = { 0 };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);

  require(service != NULL, "active command service allocation failed");
  initialize_service(service, &ep, &reusable_dp_ops, 90);

  int reservation = afk_epic_reserve_command_locked(service);

  require(reservation == 0, "active command was rejected");
  require(service->cmd_map[0] == 1, "active command did not reserve its bitmap slot");
  afk_epic_release_command_locked(service, (u8)reservation);
  require(service->cmd_map[0] == 0, "active command release retained its bitmap slot");
}

static void exercise_only_opted_in_ops_reused(void)
{
  struct apple_dcp_afkep ep = { 0 };
  struct apple_epic_service *ordinary = afk_epic_prepare_service(&ep);

  require(ordinary != NULL, "ordinary service allocation failed");
  initialize_service(ordinary, &ep, &ordinary_ops, 91);
  ordinary->torndown = true;
  ordinary->enabled = false;
  afk_service_request_retirement(ordinary);

  struct apple_epic_service *next = afk_epic_prepare_service(&ep);

  require(next != ordinary, "service without reuse opt-in was reused");
}

static void exercise_debugfs_state_blocks_reuse(void)
{
  struct apple_dcp_afkep ep = { 0 };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);

  require(service != NULL, "debugfs service allocation failed");
  initialize_service(service, &ep, &reusable_dp_ops, 101);
  service->torndown = true;
  service->debugfs.entry = (void *)(uintptr_t)0x11;
  service->debugfs.scratch = (u8 *)(uintptr_t)0x22;
  afk_service_request_retirement(service);
  require(service->enabled, "debugfs-bearing service retired");

  struct apple_epic_service *next = afk_epic_prepare_service(&ep);

  require(next != service, "debugfs-bearing service was reused");
  require(service->debugfs.entry == (void *)(uintptr_t)0x11,
    "debugfs entry was cleared before quiescence");
  require(service->debugfs.scratch == (u8 *)(uintptr_t)0x22,
    "debugfs scratch was cleared before quiescence");
}

static void exercise_stale_clear_after_quiescence(void)
{
  struct apple_dcp_afkep ep = { 0 };
  struct apple_epic_service *service = afk_epic_prepare_service(&ep);

  require(service != NULL, "stale-state service allocation failed");
  initialize_service(service, &ep, &reusable_dp_ops, 111);
  service->cmd_tag = 9;
  service->cmds[0].tag = 0xd00;
  service->cmds[0].rxbuf = (void *)(uintptr_t)0x33;
  service->cmds[0].txbuf = (void *)(uintptr_t)0x44;
  service->cmds[0].done = true;
  service->torndown = true;
  afk_service_request_retirement(service);
  require(!service->enabled, "quiescent stale-state service did not retire");

  struct apple_epic_service *reused = afk_epic_prepare_service(&ep);

  require(reused == service, "quiescent stale-state service was not reused");
  require_stale_state_cleared(reused);
}

static void exercise_all_live_slots_exhaust_safely(void)
{
  struct apple_dcp_afkep ep = { 0 };

  for (u32 index = 0; index < AFK_MAX_CHANNEL; index++) {
    struct apple_epic_service *service = afk_epic_prepare_service(&ep);

    require(service != NULL, "live-slot setup allocation failed");
    initialize_service(service, &ep, &reusable_dp_ops, index + 1);
  }

  require(afk_epic_prepare_service(&ep) == NULL,
    "allocator returned a slot while all services were live");
  require(ep.num_channels == AFK_MAX_CHANNEL,
    "safe capacity failure changed the service high-water mark");
}

int main(int argc, char **argv)
{
  if (argc != 2) {
    fprintf(stderr,
      "usage: %s stock|unsafe|unsafe-send|unsafe-race|candidate\n",
      argv[0]);
    return EXIT_FAILURE;
  }

  if (strcmp(argv[1], "stock") == 0) {
    exercise_stock_generation_failure();
    return EXIT_SUCCESS;
  }

  if (strcmp(argv[1], "unsafe") == 0) {
    exercise_unsafe_disabled_pending_reuse();
    return EXIT_SUCCESS;
  }

  if (strcmp(argv[1], "unsafe-send") == 0) {
    exercise_unsafe_post_teardown_send();
    return EXIT_SUCCESS;
  }

  if (strcmp(argv[1], "unsafe-race") == 0) {
    exercise_unsafe_reserve_teardown_send();
    return EXIT_SUCCESS;
  }

  if (strcmp(argv[1], "candidate") != 0) {
    fprintf(stderr, "unknown mode: %s\n", argv[1]);
    return EXIT_FAILURE;
  }

  exercise_ten_two_service_generations();
  exercise_disabled_but_pending_not_reused();
  exercise_enabled_torndown_late_reply();
  exercise_owner_release_order();
  exercise_mismatched_owner_teardown();
  exercise_deferred_free_order();
  exercise_post_teardown_command_rejected();
  exercise_reserve_teardown_send_serialized();
  exercise_send_failure_cleanup();
  exercise_active_command_admitted();
  exercise_only_opted_in_ops_reused();
  exercise_debugfs_state_blocks_reuse();
  exercise_stale_clear_after_quiescence();
  exercise_all_live_slots_exhaust_safely();
  puts("PASS: AFK opted-in quiescent service-slot reuse lifecycle");
  return EXIT_SUCCESS;
}
