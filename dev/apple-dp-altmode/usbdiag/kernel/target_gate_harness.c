/*
 * Metadata-only adapters and synthetic FDT fixtures for pinned OF fragments.
 * No driver body after the first probe marker is compiled into this harness.
 * The inserted OF/generation logic is extracted verbatim, not modeled here.
 * Reference and lock bookkeeping cannot establish kernel concurrency safety.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <limits.h>
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

#define MAX_NODES 96
#define MAX_PROPERTIES 192
#define MAX_DEPTH 8
#define MAX_CALLS 132
#define MAX_RECORDS 128

struct kobject { unsigned int references; };
struct property {
  const char *name;
  int length;
  const void *value;
  struct property *next;
};
struct device_node {
  const char *full_name;
  struct property *properties;
  struct device_node *parent, *child, *sibling;
  struct kobject kobj;
};
struct device { struct device_node *of_node; };
struct platform_device { struct device dev; };
struct dwc3_apple;
struct apple_atcphy;

static struct device_node nodes[MAX_NODES];
static struct property properties[MAX_PROPERTIES];
static size_t node_count, property_count;
static struct device_node *of_root, *of_aliases;
static unsigned int reference_gets, reference_puts, live_references;
static unsigned int lock_depth, lock_entries;
static int devtree_lock;
static char records[MAX_RECORDS][384];
static unsigned int record_count;

static void metadata_released(void)
{
  assert(lock_depth == 0 && live_references == 0);
  for (size_t index = 0; index < node_count; index++)
    assert(nodes[index].kobj.references == 1);
}

static struct kobject *kobject_get(struct kobject *object)
{
  assert(object && object->references >= 1);
  object->references++;
  reference_gets++;
  live_references++;
  return object;
}

static void kobject_put(struct kobject *object)
{
  assert(object && object->references > 1 && live_references > 0);
  object->references--;
  reference_puts++;
  live_references--;
}

static void lock_enter(int *lock)
{
  assert(lock == &devtree_lock && lock_depth == 0);
  lock_depth = 1;
  lock_entries++;
}

static void lock_leave(int *lock)
{
  assert(lock == &devtree_lock && lock_depth == 1);
  lock_depth = 0;
}

#define raw_spin_lock_irqsave(lock, flags) \
  do { (flags) = 0; lock_enter(lock); } while (0)
#define raw_spin_unlock_irqrestore(lock, flags) \
  do { (void)(flags); lock_leave(lock); } while (0)

typedef _Atomic int atomic_t;
#define ATOMIC_INIT(value) (value)
#define static_assert _Static_assert

static int atomic_inc_return(atomic_t *counter)
{
  /* A corrected gate must release metadata references before publishing IDs. */
  metadata_released();
  return atomic_fetch_add(counter, 1) + 1;
}

static int atomic_fetch_add_unless(atomic_t *counter, int amount, int unless)
{
  int previous = atomic_load(counter);
  while (previous != unless &&
         !atomic_compare_exchange_weak(counter, &previous, previous + amount)) {}
  return previous;
}

static void log_info(const char *format, ...)
  __attribute__((format(printf, 1, 2)));
static void log_info(const char *format, ...)
{
  metadata_released();
  assert(record_count < MAX_RECORDS);
  va_list arguments;
  va_start(arguments, format);
  int size = vsnprintf(records[record_count], sizeof(records[0]), format, arguments);
  va_end(arguments);
  assert(size > 0 && size < (int)sizeof(records[0]));
  assert(records[record_count][size - 1] == '\n');
  record_count++;
}
#define pr_info(...) log_info(__VA_ARGS__)

struct device_node *of_node_get(struct device_node *node);
void of_node_put(struct device_node *node);
struct device_node *of_find_node_opts_by_path(const char *path, const char **opts);
bool of_machine_compatible_match(const char *const *compats);

/* Preserve the pinned kernel's signed-length comparisons without rewriting them. */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wsign-compare"
/* @PINNED_OF_FRAGMENTS@ */
#pragma GCC diagnostic pop

/* @PINNED_PRODUCER_FRAGMENTS@ */

static const char board_good[] = "apple,j413\0apple,t8112\0apple,arm-platform";
static const char board_upper[] = "APPLE,J413";
static const char board_later[] = "apple,t8112\0APPLE,J413";
static const char board_j313[] = "apple,j313";
static const char board_t8112[] = "apple,t8112";
static const char board_suffix[] = "apple,j413x";

enum fixture_kind {
  FRONT, UPPER_BOARD, LATER_BOARD, WRONG_BOARD, SOC_ONLY_BOARD, BOARD_SUFFIX,
  MISSING_COMPAT, REAR, OTHER, BRIDGE, SOC_UNIT, SOC_CASE, FOREIGN,
  MISSING_TARGET, NULL_NODE, NULL_ROOT, NULL_BOTH, NULL_MISSING_TARGET,
  LEADING_ZERO, ADDRESS_SUFFIX, ADDRESS_PREFIX, ADDRESS_CHANGE, NAME_CASE,
  RETRIES, REJECT_BETWEEN, CAP, INTERLEAVED
};

struct fixture_case { const char *name; enum fixture_kind kind; };
static const struct fixture_case cases[] = {
  {"front_target", FRONT}, {"uppercase_board", UPPER_BOARD},
  {"later_compatible_board", LATER_BOARD}, {"wrong_board_j313", WRONG_BOARD},
  {"soc_only_board", SOC_ONLY_BOARD}, {"board_suffix", BOARD_SUFFIX},
  {"missing_compatible", MISSING_COMPAT}, {"rear_port", REAR},
  {"other_parent", OTHER}, {"bridge_soc", BRIDGE}, {"soc_unit", SOC_UNIT},
  {"soc_case", SOC_CASE}, {"foreign_same_path", FOREIGN},
  {"missing_target", MISSING_TARGET}, {"null_node", NULL_NODE},
  {"null_root", NULL_ROOT}, {"null_root_and_node", NULL_BOTH},
  {"null_node_missing_target", NULL_MISSING_TARGET},
  {"leading_zero_address", LEADING_ZERO}, {"address_suffix", ADDRESS_SUFFIX},
  {"name_prefix", ADDRESS_PREFIX}, {"changed_address", ADDRESS_CHANGE},
  {"name_case", NAME_CASE}, {"probe_retries", RETRIES},
  {"reject_between_retries", REJECT_BETWEEN}, {"cap_via_probe", CAP},
  {"interleaved_components", INTERLEAVED}
};

static void fdt_ok(int result)
{
  assert(result >= 0);
}

static void leaf(void *blob, const char *name, const char *tag)
{
  fdt_ok(fdt_begin_node(blob, name));
  fdt_ok(fdt_property_string(blob, "test-id", tag));
  fdt_ok(fdt_end_node(blob));
}

static void pair(void *blob, const char *dwc3_tag, const char *atc_tag)
{
  leaf(blob, "usb@502280000", dwc3_tag);
  leaf(blob, "phy@503000000", atc_tag);
}

static void build_fdt(void *blob, size_t bytes, enum fixture_kind kind, bool dwc3)
{
  const char *board = board_good;
  size_t board_bytes = sizeof(board_good);
  if (kind == UPPER_BOARD) {
    board = board_upper;
    board_bytes = sizeof(board_upper);
  } else if (kind == LATER_BOARD) {
    board = board_later;
    board_bytes = sizeof(board_later);
  } else if (kind == WRONG_BOARD) {
    board = board_j313;
    board_bytes = sizeof(board_j313);
  } else if (kind == SOC_ONLY_BOARD) {
    board = board_t8112;
    board_bytes = sizeof(board_t8112);
  } else if (kind == BOARD_SUFFIX) {
    board = board_suffix;
    board_bytes = sizeof(board_suffix);
  }
  fdt_ok(fdt_create(blob, (int)bytes));
  fdt_ok(fdt_finish_reservemap(blob));
  fdt_ok(fdt_begin_node(blob, ""));
  if (kind != MISSING_COMPAT)
    fdt_ok(fdt_property(blob, "compatible", board, (int)board_bytes));

  fdt_ok(fdt_begin_node(blob, "soc"));
  /* Decoys precede the real targets to exercise traversal reference release. */
  leaf(blob, "usb@5022800000", "decoy_dwc3");
  leaf(blob, "phy@5030000000", "decoy_atc");
  leaf(blob, "usb@382280000", "rear_dwc3");
  leaf(blob, "phy@383000000", "rear_atc");
  const char *dwc3_name = "usb@502280000";
  const char *atc_name = "phy@503000000";
  if (kind == LEADING_ZERO) {
    if (dwc3) dwc3_name = "usb@0502280000";
    else atc_name = "phy@0503000000";
  } else if (kind == ADDRESS_SUFFIX) {
    if (dwc3) dwc3_name = "usb@502280000-extra";
    else atc_name = "phy@503000000-extra";
  } else if (kind == ADDRESS_PREFIX) {
    if (dwc3) dwc3_name = "xusb@502280000";
    else atc_name = "xphy@503000000";
  } else if (kind == ADDRESS_CHANGE) {
    if (dwc3) dwc3_name = "usb@502280001";
    else atc_name = "phy@503000001";
  } else if (kind == NAME_CASE) {
    if (dwc3) dwc3_name = "USB@502280000";
    else atc_name = "PHY@503000000";
  }
  bool missing_target = kind == MISSING_TARGET || kind == NULL_MISSING_TARGET;
  if (!missing_target || !dwc3)
    leaf(blob, dwc3_name, "front_dwc3");
  if (!missing_target || dwc3)
    leaf(blob, atc_name, "front_atc");
  fdt_ok(fdt_end_node(blob));

  fdt_ok(fdt_begin_node(blob, "other"));
  pair(blob, "other_dwc3", "other_atc");
  fdt_ok(fdt_end_node(blob));
  fdt_ok(fdt_begin_node(blob, "bridge"));
  fdt_ok(fdt_begin_node(blob, "soc"));
  pair(blob, "bridge_dwc3", "bridge_atc");
  fdt_ok(fdt_end_node(blob));
  fdt_ok(fdt_end_node(blob));
  fdt_ok(fdt_begin_node(blob, "soc@0"));
  pair(blob, "unit_dwc3", "unit_atc");
  fdt_ok(fdt_end_node(blob));
  fdt_ok(fdt_begin_node(blob, "Soc"));
  pair(blob, "case_dwc3", "case_atc");
  fdt_ok(fdt_end_node(blob));
  fdt_ok(fdt_end_node(blob));
  fdt_ok(fdt_finish(blob));
  assert(fdt_check_header(blob) == 0);
}

static struct device_node *metadata_from_fdt(const void *blob)
{
  struct device_node *parents[MAX_DEPTH] = {0};
  struct device_node *root = NULL;
  int depth = -1;
  int offset = fdt_next_node(blob, -1, &depth);
  while (offset >= 0 && depth >= 0) {
    assert(depth < MAX_DEPTH && node_count < MAX_NODES);
    struct device_node *node = &nodes[node_count++];
    int name_length;
    node->full_name = fdt_get_name(blob, offset, &name_length);
    assert(node->full_name && name_length >= 0);
    assert(!strchr(node->full_name, '/'));
    node->kobj.references = 1;
    node->parent = depth ? parents[depth - 1] : NULL;
    if (node->parent) {
      struct device_node **slot = &node->parent->child;
      while (*slot) slot = &(*slot)->sibling;
      *slot = node;
    } else {
      assert(!root);
      root = node;
    }
    parents[depth] = node;
    struct property **slot = &node->properties;
    int property_offset = fdt_first_property_offset(blob, offset);
    while (property_offset >= 0) {
      assert(property_count < MAX_PROPERTIES);
      int length;
      const struct fdt_property *source =
        fdt_get_property_by_offset(blob, property_offset, &length);
      assert(source && length >= 0);
      struct property *property = &properties[property_count++];
      property->name = fdt_string(blob, (int)fdt32_to_cpu(source->nameoff));
      assert(property->name);
      property->length = length;
      property->value = source->data;
      *slot = property;
      slot = &property->next;
      property_offset = fdt_next_property_offset(blob, property_offset);
    }
    assert(property_offset == -FDT_ERR_NOTFOUND);
    offset = fdt_next_node(blob, offset, &depth);
  }
  assert(root && (depth < 0 || offset == -FDT_ERR_NOTFOUND));
  return root;
}

static struct device_node *tagged_node(size_t begin, size_t end, const char *tag)
{
  struct device_node *found = NULL;
  for (size_t index = begin; index < end; index++) {
    for (struct property *property = nodes[index].properties;
         property; property = property->next) {
      if (!strcmp(property->name, "test-id") &&
          !strcmp(property->value, tag)) {
        assert(!found);
        found = &nodes[index];
      }
    }
  }
  assert(found);
  return found;
}

int main(int argc, char **argv)
{
  assert(argc == 3);
  bool dwc3 = !strcmp(argv[1], "dwc3");
  assert(dwc3 || !strcmp(argv[1], "atc"));
  const struct fixture_case *selected = NULL;
  for (size_t index = 0; index < sizeof(cases) / sizeof(cases[0]); index++)
    if (!strcmp(argv[2], cases[index].name)) selected = &cases[index];
  assert(selected);

  _Alignas(8) unsigned char blob[16384], foreign_blob[16384];
  build_fdt(blob, sizeof(blob), selected->kind, dwc3);
  of_root = metadata_from_fdt(blob);
  size_t primary_end = node_count;
  size_t selected_begin = 0, selected_end = primary_end;
  if (selected->kind == FOREIGN) {
    build_fdt(foreign_blob, sizeof(foreign_blob), FRONT, dwc3);
    (void)metadata_from_fdt(foreign_blob);
    selected_begin = primary_end;
    selected_end = node_count;
  }
  const char *group = "front";
  if (selected->kind == REAR) group = "rear";
  else if (selected->kind == OTHER || selected->kind == MISSING_TARGET ||
           selected->kind == NULL_MISSING_TARGET) group = "other";
  else if (selected->kind == BRIDGE) group = "bridge";
  else if (selected->kind == SOC_UNIT) group = "unit";
  else if (selected->kind == SOC_CASE) group = "case";
  char tag[32], rear_tag[32], peer_tag[32];
  assert(snprintf(tag, sizeof(tag), "%s_%s", group, argv[1]) > 0);
  assert(snprintf(rear_tag, sizeof(rear_tag), "rear_%s", argv[1]) > 0);
  assert(snprintf(peer_tag, sizeof(peer_tag), "front_%s", dwc3 ? "atc" : "dwc3") > 0);
  struct device_node *device_node = tagged_node(selected_begin, selected_end, tag);
  struct device_node *rear_node = tagged_node(0, primary_end, rear_tag);
  struct device_node *peer_node = tagged_node(0, primary_end, peer_tag);
  if (selected->kind == NULL_NODE || selected->kind == NULL_BOTH ||
      selected->kind == NULL_MISSING_TARGET) device_node = NULL;
  if (selected->kind == NULL_ROOT || selected->kind == NULL_BOTH) of_root = NULL;

  unsigned int calls = selected->kind == CAP ? MAX_CALLS :
    selected->kind == INTERLEAVED ? 4 :
    (selected->kind == RETRIES || selected->kind == REJECT_BETWEEN ? 3 : 1);
  unsigned int generations[MAX_CALLS], sequences[MAX_CALLS];
  metadata_released();
  for (unsigned int index = 0; index < calls; index++) {
    bool peer_call = selected->kind == INTERLEAVED && index % 2;
    bool call_dwc3 = peer_call ? !dwc3 : dwc3;
    struct platform_device device = {.dev = {.of_node =
      selected->kind == REJECT_BETWEEN && index == 1 ? rear_node :
      peer_call ? peer_node : device_node}};
    int generation = call_dwc3 ? dwc3_apple_probe(&device) : atcphy_probe(&device);
    assert(generation >= 0);
    generations[index] = (unsigned int)generation;
    sequences[index] = (unsigned int)atomic_load(call_dwc3 ?
      &dev147_dwc3_sequence : &dev147_atc_sequence);
    metadata_released();
    assert(reference_gets == reference_puts);
  }

  printf("{\"component\":\"%s\",\"case\":\"%s\",\"node_present\":%s,"
         "\"root_present\":%s,\"node_leaf\":",
         argv[1], selected->name, device_node ? "true" : "false",
         of_root ? "true" : "false");
  if (device_node) printf("\"%s\"", device_node->full_name);
  else fputs("null", stdout);
  printf(",\"reference_gets\":%u,\"reference_puts\":%u,\"live_references\":%u,"
         "\"lock_entries\":%u,\"lock_depth\":%u,\"generations\":[",
         reference_gets, reference_puts, live_references, lock_entries, lock_depth);
  for (unsigned int index = 0; index < calls; index++)
    printf("%s%u", index ? "," : "", generations[index]);
  fputs("],\"sequences\":[", stdout);
  for (unsigned int index = 0; index < calls; index++)
    printf("%s%u", index ? "," : "", sequences[index]);
  fputs("],\"records\":[", stdout);
  for (unsigned int index = 0; index < record_count; index++) {
    if (index) fputc(',', stdout);
    size_t length = strlen(records[index]);
    assert(fwrite(records[index], 1, length - 1, stdout) == length - 1);
  }
  fputs("]}\n", stdout);
  return fflush(stdout) ? EXIT_FAILURE : EXIT_SUCCESS;
}
