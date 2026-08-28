// SPDX-License-Identifier: GPL-2.0
/* Source-helper checks only. No kernel ABI, scheduling, or hardware model. */
#if TIPD_T1_PRESENT
static void quoted(const char *text);
static void fill_payload(struct cd321x *cd, unsigned int bias);

struct guarded_object {
  unsigned char *allocation;
  struct tps6598x *tps;
  size_t bytes;
};

static struct guarded_object diagnostic_object(const struct tipd_data *data, size_t bytes)
{
  assert(bytes >= sizeof(struct tps6598x) && bytes <= 16384);
  unsigned char *allocation = calloc(1, bytes + 32);
  assert(allocation);
  memset(allocation, 0xa5, 16);
  memset(allocation + 16 + bytes, 0xa5, 16);
  struct tps6598x *tps = (void *)(allocation + 16);
  remember_object(tps, bytes);
  tps->dev = &test_device;
  tps->data = data;
  tps->role_sw = &role_switch;
  tps->port = &port;
  tps->psy = &psy;
  if (bytes >= sizeof(struct cd321x)) {
    struct cd321x *cd = (void *)tps;
    cd->port_altmode_dp = &dp_alt;
    cd->port_altmode_tbt = &tbt_alt;
    cd->mux = &mux;
    cd->update_work.work.function = cd321x_update_work;
    fill_payload(cd, 0);
  }
  return (struct guarded_object){allocation, tps, bytes};
}

static void diagnostic_activate(struct guarded_object object)
{
  active_tps = object.tps;
  active_cd = object.bytes >= sizeof(struct cd321x) ? (void *)object.tps : NULL;
}

static void diagnostic_free(struct guarded_object object)
{
  for (size_t i = 0; i < 16; i++)
    assert(object.allocation[i] == 0xa5 && object.allocation[16 + object.bytes + i] == 0xa5);
  forget_object(object.tps);
  free(object.allocation);
}

static void diagnostic_report(const char *name, const struct tipd_t1_context *contexts,
                               size_t count, const int *outcomes, size_t outcome_count)
{
  metadata_released();
  assert(reference_gets == reference_puts && count <= 16 && outcome_count <= 4);
  printf("{\"case\":");
  quoted(name);
  printf(",\"counts\":[%d,%d,%d],\"refs\":[%u,%u],\"conversions\":%zu,"
         "\"wrapper_offset\":%zu,\"tail_offset\":%zu,\"prefix_bytes\":%zu,"
         "\"wrapper_bytes\":%zu,\"bounds\":true,\"contexts\":[",
         atomic_read(&tipd_t1_generations), atomic_read(&tipd_t1_workers),
         atomic_read(&tipd_t1_sequence), reference_gets, reference_puts, wrapper_conversions,
         offsetof(struct tipd_t1_cd321x, cd321x), offsetof(struct tipd_t1_cd321x, generation),
         sizeof(struct cd321x), sizeof(struct tipd_t1_cd321x));
  for (size_t i = 0; i < count; i++) {
    if (i) putchar(',');
    printf("[%u,%u]", contexts[i].gen, contexts[i].worker);
  }
  printf("],\"outcomes\":[");
  for (size_t i = 0; i < outcome_count; i++) {
    if (i) putchar(',');
    printf("%d", outcomes[i]);
  }
  printf("],\"records\":[");
  for (size_t i = 0; i < record_count; i++) {
    if (i) putchar(',');
    quoted(records[i]);
  }
  printf("],\"ledger\":[");
  for (size_t i = 0; i < event_count; i++) {
    if (i) putchar(',');
    putchar('[');
    quoted(ledger[i].operation);
    printf(",%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64 "]",
           ledger[i].a, ledger[i].b, ledger[i].c, ledger[i].d, ledger[i].e);
  }
  printf("]}\n");
}

struct record_thread {
  struct tipd_t1_context context;
  struct tps6598x *tps;
};

static void *diagnostic_thread(void *opaque)
{
  struct record_thread *thread = opaque;
  for (unsigned int i = 0; i < 64; i++)
    tipd_t1_cache(thread->context, thread->tps);
  return NULL;
}

static void assert_same_events(const struct event *before, size_t count)
{
  assert(event_count == count);
  for (size_t i = 0; i < count; i++)
    assert(!strcmp(ledger[i].operation, before[i].operation) &&
           ledger[i].a == before[i].a && ledger[i].b == before[i].b &&
           ledger[i].c == before[i].c && ledger[i].d == before[i].d &&
           ledger[i].e == before[i].e);
}

static int diagnostic_case(int argc, char **argv)
{
  assert(argc >= 3);
  const char *name = argv[2];
  struct tipd_t1_context contexts[16] = {0};
  int outcomes[4] = {0};
  size_t count = 0, outcome_count = 0;

  if (!strcmp(name, "guard")) {
    assert(argc == 5);
    char *end;
    unsigned long kind = strtoul(argv[3], &end, 10);
    assert(*argv[3] && !*end && kind <= 22);
    unsigned long variant = strtoul(argv[4], &end, 10);
    assert(*argv[4] && !*end && variant <= 4);
    test_device.of_node = metadata_fixture((unsigned int)kind);
    struct tipd_data copied = tipd_cd321x_data;
    const struct tipd_data *data = variant == 0 ? &tipd_cd321x_data :
      variant == 1 ? &tipd_sn201202x_data : variant == 4 ? NULL : &copied;
    if (variant == 3) copied.tps_struct_size = sizeof(struct tps6598x);
    size_t bytes = data ? data->tps_struct_size : sizeof(struct tps6598x);
    struct guarded_object object = diagnostic_object(data, bytes);
    diagnostic_activate(object);
    unsigned char before[16384];
    memcpy(before, object.tps, bytes);
    contexts[count++] = tipd_t1_initialize(object.tps);
    contexts[count++] = tipd_t1_current(object.tps);
    contexts[count++] = tipd_t1_start_worker(object.tps);
    tipd_t1_cache(contexts[0], object.tps);
    tipd_t1_end_worker(object.tps, contexts[2], "complete", 0);
    contexts[count++] = tipd_t1_current(object.tps);
    if (!contexts[0].gen) assert(!memcmp(before, object.tps, bytes));
    else assert(!memcmp(before, object.tps, sizeof(struct cd321x)));
    diagnostic_free(object);
  } else {
    test_device.of_node = metadata_fixture(0);
    struct guarded_object first = diagnostic_object(&tipd_cd321x_data,
                                                     tipd_cd321x_data.tps_struct_size);
    diagnostic_activate(first);
    if (!strcmp(name, "retry")) {
      assert(argc == 3);
      active_tps->irq = 7;
      script.failure = GPIO;
      script.flags = ATTACHED | CONNECTOR_PRESENT | IRQ_PRESENT | DISPATCH_DURING_IRQ;
      script.init_depth++;
      outcomes[outcome_count++] = tipd_init(active_tps);
      script.init_depth--;
      contexts[count++] = tipd_t1_current(active_tps);
      script.failure = OK;
      script.init_depth++;
      outcomes[outcome_count++] = tipd_init(active_tps);
      script.init_depth--;
      contexts[count++] = tipd_t1_current(active_tps);
      assert(!active_cd->update_work.pending && !active_tps->lock.held);
      struct guarded_object second = diagnostic_object(&tipd_cd321x_data,
                                                        tipd_cd321x_data.tps_struct_size);
      diagnostic_activate(second);
      active_tps->irq = 7;
      script.init_depth++;
      outcomes[outcome_count++] = tipd_init(active_tps);
      script.init_depth--;
      contexts[count++] = tipd_t1_current(active_tps);
      contexts[count++] = tipd_t1_current(first.tps);
      assert(!active_cd->update_work.pending && !active_tps->lock.held);
      diagnostic_free(second);
      diagnostic_activate(first);
    } else if (!strcmp(name, "cap_terminal")) {
      assert(argc == 3);
      contexts[count++] = tipd_t1_initialize(active_tps);
      contexts[count++] = tipd_t1_start_worker(active_tps);
      for (unsigned int i = 0; i < 126; i++) tipd_t1_cache(contexts[0], active_tps);
      tipd_t1_end_worker(active_tps, contexts[1], "complete", 0);
      assert(record_count == 128);
      for (unsigned int i = 0; i < 64; i++) tipd_t1_cache(contexts[0], active_tps);
    } else if (!strcmp(name, "parallel")) {
      assert(argc == 4 && (!strcmp(argv[3], "0") || !strcmp(argv[3], "1")));
      contexts[count++] = tipd_t1_initialize(active_tps);
      reorder_records = !strcmp(argv[3], "1");
      pthread_t threads[8];
      struct record_thread arguments[8];
      for (size_t i = 0; i < 8; i++) {
        arguments[i] = (struct record_thread){contexts[0], active_tps};
        assert(pthread_create(&threads[i], NULL, diagnostic_thread, &arguments[i]) == 0);
      }
      for (size_t i = 0; i < 8; i++) assert(pthread_join(threads[i], NULL) == 0);
      if (reorder_records) assert(second_record_seen);
    } else if (!strcmp(name, "limits")) {
      assert(argc == 3);
      atomic_set(&tipd_t1_generations, INT_MAX - 1);
      atomic_set(&tipd_t1_workers, INT_MAX - 1);
      contexts[count++] = tipd_t1_initialize(active_tps);
      cd321x_update_work(&active_cd->update_work.work);
      struct event before[1024];
      size_t previous_count = event_count, previous_records = record_count;
      memcpy(before, ledger, previous_count * sizeof(before[0]));
      event_count = 0;
      /* Exhaustion must not leave a stale worker ID for the mode logger. */
      atomic_set(&tipd_t1_storage(active_tps)->worker, 123);
      cd321x_update_work(&active_cd->update_work.work);
      assert_same_events(before, previous_count);
      assert(record_count == previous_records);
      contexts[count++] = tipd_t1_current(active_tps);
      /* Direct mode entry must also remain silent without an active worker. */
      struct cd321x_status state = {.data_status = TPS_DATA_STATUS_DATA_CONNECTION};
      cd321x_typec_update_mode(active_tps, &state);
      assert(record_count == previous_records);
      contexts[count++] = tipd_t1_initialize(active_tps);
      assert(atomic_read(&tipd_t1_generations) == INT_MAX);
    } else {
      assert(!"unapproved diagnostic case");
    }
    diagnostic_free(first);
  }
  assert(object_count == 0 && !script.init_depth);
  diagnostic_report(name, contexts, count, outcomes, outcome_count);
  return 0;
}
#endif
