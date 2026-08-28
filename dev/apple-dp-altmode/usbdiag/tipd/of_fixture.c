// SPDX-License-Identifier: GPL-2.0
/*
 * Bounded OF metadata seam. The path/compatibility/reference logic below is
 * inserted verbatim from pinned kernel sources. Real libfdt supplies leaves.
 * This models neither device registration nor kernel concurrent tree changes.
 */
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

static struct device_node nodes[64];
static struct property properties[128];
static size_t node_count, property_count;
static struct device_node *of_root, *of_aliases;
static unsigned int reference_gets, reference_puts, live_references, tree_depth;
static int devtree_lock;

static void metadata_released(void)
{
  assert(tree_depth == 0 && live_references == 0);
  for (size_t i = 0; i < node_count; i++)
    assert(nodes[i].kobj.references == 1);
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
  assert(object && object->references > 1 && live_references);
  object->references--;
  reference_puts++;
  live_references--;
}

static void tree_lock(int *lock)
{
  assert(lock == &devtree_lock && tree_depth == 0);
  tree_depth = 1;
}

static void tree_unlock(int *lock)
{
  assert(lock == &devtree_lock && tree_depth == 1);
  tree_depth = 0;
}

#define raw_spin_lock_irqsave(lock, flags) \
  do { (flags) = 0; tree_lock(lock); } while (0)
#define raw_spin_unlock_irqrestore(lock, flags) \
  do { (void)(flags); tree_unlock(lock); } while (0)

struct device_node *of_node_get(struct device_node *node);
void of_node_put(struct device_node *node);
struct device_node *of_find_node_opts_by_path(const char *path, const char **opts);
bool of_machine_compatible_match(const char *const *compats);

/* Preserve upstream signed-length comparisons without rewriting their bodies. */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wsign-compare"
/* @PINNED_OF@ */
#pragma GCC diagnostic pop

static void fdt_check(int value)
{
  assert(value >= 0);
}

static void fdt_leaf(void *blob, const char *name, const char *tag)
{
  fdt_check(fdt_begin_node(blob, name));
  fdt_check(fdt_property_string(blob, "test-id", tag));
  fdt_check(fdt_end_node(blob));
}

static void make_tree(void *blob, int bytes, unsigned int kind)
{
  static const char good[] = "apple,j413\0apple,t8112";
  static const char upper[] = "apple,t8112\0APPLE,J413";
  static const char wrong[] = "apple,j313";
  static const char suffix[] = "apple,j413x";
  static const char chip[] = "apple,t8112";
  const char *board = kind == 1 ? upper : kind == 2 ? wrong :
    kind == 12 ? suffix : kind == 13 ? chip : good;
  int length = kind == 1 ? sizeof(upper) : kind == 2 ? sizeof(wrong) :
    kind == 12 ? sizeof(suffix) : kind == 13 ? sizeof(chip) : sizeof(good);
  fdt_check(fdt_create(blob, bytes));
  fdt_check(fdt_finish_reservemap(blob));
  fdt_check(fdt_begin_node(blob, ""));
  fdt_check(fdt_property(blob, "compatible", board, length));
  if (kind == 18) fdt_check(fdt_begin_node(blob, "bridge"));
  fdt_check(fdt_begin_node(blob, kind == 14 ? "Soc" : kind == 15 ? "soc@0" : "soc"));
  fdt_check(fdt_begin_node(blob, kind == 16 ? "i2c@0235010000" :
                          kind == 17 ? "I2C@235010000" : "i2c@235010000"));
  fdt_leaf(blob, "usb-pd@3f0", "decoy");
  fdt_leaf(blob, "usb-pd@38", "rear");
  if (kind != 4) {
    const char *name = kind == 5 ? "usb-pd@03f" :
      kind == 6 ? "usb-pd@3F" : kind == 7 ? "usb-pd@3f-extra" :
      kind == 19 ? "usb-pd@3" : kind == 20 ? "usb-pd" :
      kind == 21 ? "Usb-pd@3f" : "usb-pd@3f";
    fdt_leaf(blob, name, "selected");
  }
  fdt_check(fdt_end_node(blob));
  fdt_check(fdt_end_node(blob));
  if (kind == 18) fdt_check(fdt_end_node(blob));
  fdt_check(fdt_begin_node(blob, "other"));
  fdt_check(fdt_begin_node(blob, "i2c@235010000"));
  fdt_leaf(blob, "usb-pd@3f", "other-parent");
  fdt_check(fdt_end_node(blob));
  fdt_check(fdt_end_node(blob));
  fdt_check(fdt_end_node(blob));
  fdt_check(fdt_finish(blob));
  assert(fdt_check_header(blob) == 0);
}

static struct device_node *read_tree(const void *blob)
{
  struct device_node *parents[8] = {0}, *root = NULL;
  int depth = -1, offset = fdt_next_node(blob, -1, &depth);
  while (offset >= 0 && depth >= 0) {
    assert(depth < 8 && node_count < 64);
    struct device_node *node = &nodes[node_count++];
    int length;
    node->full_name = fdt_get_name(blob, offset, &length);
    assert(node->full_name && length >= 0 && !strchr(node->full_name, '/'));
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
      assert(property_count < 128);
      const struct fdt_property *input =
        fdt_get_property_by_offset(blob, property_offset, &length);
      assert(input && length >= 0);
      struct property *property = &properties[property_count++];
      property->name = fdt_string(blob, (int)fdt32_to_cpu(input->nameoff));
      assert(property->name);
      property->length = length;
      property->value = input->data;
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

static struct device_node *tagged(size_t begin, const char *tag)
{
  struct device_node *found = NULL;
  for (size_t i = begin; i < node_count; i++)
    for (struct property *property = nodes[i].properties; property; property = property->next)
      if (!strcmp(property->name, "test-id") && !strcmp(property->value, tag)) {
        assert(!found);
        found = &nodes[i];
      }
  assert(found);
  return found;
}

static struct device_node *metadata_fixture(unsigned int kind)
{
  static _Alignas(8) unsigned char primary[8192], foreign[8192];
  assert(kind <= 22);
  make_tree(primary, sizeof(primary), kind);
  of_root = read_tree(primary);
  const char *tag = kind == 3 ? "rear" :
    kind == 4 || kind == 8 ? "other-parent" : "selected";
  struct device_node *selected = tagged(0, tag);
  if (kind == 9) {
    size_t begin = node_count;
    make_tree(foreign, sizeof(foreign), 0);
    (void)read_tree(foreign);
    selected = tagged(begin, "selected");
  }
  if (kind == 4 || kind == 10 || kind == 22) selected = NULL;
  if (kind == 11 || kind == 22) of_root = NULL;
  metadata_released();
  return selected;
}
