// SPDX-License-Identifier: GPL-2.0
/* Fixed, synthetic inputs only. The inserted driver bodies own all decisions. */
static int64_t argument(const char *text)
{
  char *end;
  errno = 0;
  int64_t value = strtoll(text, &end, 10);
  assert(!errno && *text && !*end && value >= -4096 && value <= UINT32_MAX);
  return value;
}

static void quoted(const char *text)
{
  putchar('"');
  for (const unsigned char *p = (const unsigned char *)text; *p; p++) {
    assert(*p < 128);
    if (*p == '"' || *p == '\\') {
      putchar('\\');
      putchar(*p);
    } else if (*p < 32) {
      printf("\\u%04x", *p);
    } else {
      putchar(*p);
    }
  }
  putchar('"');
}

static void fill_payload(struct cd321x *cd, unsigned int bias)
{
  cd->tps.partner_identity = (struct usb_pd_identity){
    .id_header = 10 + bias, .cert_stat = 11 + bias, .product = 12 + bias,
    .vdo = {13 + bias, 14 + bias, 15 + bias},
  };
  cd->dp_sid_status = (struct tps6598x_dp_sid_status_reg){
    .mode_status = 1, .status_tx = 21 + bias, .status_rx = 22 + bias,
    .configure = 23 + bias, .mode_data = 24 + bias,
  };
  cd->intel_vid_status = (struct tps6598x_intel_vid_status_reg){
    .mode_status = 2, .attention_vdo = 31 + bias, .enter_vdo = 32 + bias,
    .device_mode = 33 + bias, .cable_mode = 34 + bias,
  };
  cd->usb4_status = (struct tps6598x_usb4_status_reg){
    .mode_status = 3, .eudo = 41 + bias, .unknown = 42 + bias,
  };
}

static void print_snapshot(const struct cd321x_status *st)
{
  printf("[%" PRIu32 ",%" PRIu32 ",%" PRIu32 ",%" PRIu32 ",%" PRIu32,
         st->status, st->pwr_status, st->data_status,
         st->status_changed, st->data_status_changed);
  printf(",%" PRIu32 ",%" PRIu32 ",%" PRIu32 ",%" PRIu32 ",%" PRIu32 ",%" PRIu32,
         st->partner_identity.id_header, st->partner_identity.cert_stat,
         st->partner_identity.product, st->partner_identity.vdo[0],
         st->partner_identity.vdo[1], st->partner_identity.vdo[2]);
  printf(",%u,%" PRIu32 ",%" PRIu32 ",%" PRIu32 ",%" PRIu32,
         st->dp_sid_status.mode_status, st->dp_sid_status.status_tx,
         st->dp_sid_status.status_rx, st->dp_sid_status.configure,
         st->dp_sid_status.mode_data);
  printf(",%u,%" PRIu32 ",%u,%u,%u,%u,%" PRIu32 ",%" PRIu32 "]",
         st->intel_vid_status.mode_status, st->intel_vid_status.attention_vdo,
         st->intel_vid_status.enter_vdo, st->intel_vid_status.device_mode,
         st->intel_vid_status.cable_mode, st->usb4_status.mode_status,
         st->usb4_status.eudo, st->usb4_status.unknown);
}

static int connect_error(struct tps6598x *tps, u32 status)
{
  check_tps(tps);
  event("connect_error", status, 0, 0, 0, 0);
  return -EIO;
}

int main(int argc, char **argv)
{
  assert(argc >= 2);
#if TIPD_T1_PRESENT
  if (!strcmp(argv[1], "diagnostic")) return diagnostic_case(argc, argv);
#endif
  bool init_case = !strcmp(argv[1], "init") || !strcmp(argv[1], "init_cap");
  bool worker_case = !strcmp(argv[1], "worker") || !strcmp(argv[1], "worker_cap");
  bool mode_case = !strcmp(argv[1], "mode") || !strcmp(argv[1], "mode_cap");
  bool queue_case = !strcmp(argv[1], "queue");
  bool connect_case = !strcmp(argv[1], "connect");
  assert(init_case || worker_case || mode_case || queue_case || connect_case);
  assert((init_case && argc == 5) || (worker_case && argc == 18) ||
         (mode_case && argc == 8) || (queue_case && argc == 2) ||
         (connect_case && argc == 4));
  unsigned int metadata_kind = init_case ? argument(argv[4]) :
    worker_case ? argument(argv[17]) : mode_case ? argument(argv[7]) : 0;
  test_device.of_node = metadata_fixture(metadata_kind);
  /* Assert real fixture construction, not a handwritten production gate. */
  bool board_match = of_machine_is_compatible("apple,j413");
  struct device_node *lookup = of_find_node_by_path("/soc/i2c@235010000/usb-pd@3f");
  bool target_match = lookup && lookup == test_device.of_node;
  of_node_put(lookup);
  metadata_released();
  unsigned int precheck_gets = reference_gets, precheck_puts = reference_puts;

  size_t allocation_size = tipd_cd321x_data.tps_struct_size;
  assert(allocation_size >= sizeof(struct cd321x) && allocation_size <= 16384);
  unsigned char *allocation = calloc(1, allocation_size + 32);
  assert(allocation);
  memset(allocation, 0xa5, 16);
  memset(allocation + 16 + allocation_size, 0xa5, 16);
  active_cd = (struct cd321x *)(void *)(allocation + 16);
  remember_object(active_cd, allocation_size);
  active_tps = &active_cd->tps;
  active_tps->dev = &test_device;
  active_tps->data = &tipd_cd321x_data;
  active_tps->role_sw = &role_switch;
  active_tps->port = &port;
  active_tps->psy = &psy;
  active_cd->port_altmode_dp = &dp_alt;
  active_cd->port_altmode_tbt = &tbt_alt;
  active_cd->mux = &mux;
  active_cd->update_work.work.function = cd321x_update_work;
  fill_payload(active_cd, 0);
  struct cd321x_status snapshots[4];
  size_t snapshot_count = 0;
  struct tipd_data generic_data = tipd_cd321x_data;
  int result = 0;
  (void)&collect_info; /* No fabricated record when the control lacks diagnostics. */

#if TIPD_T1_PRESENT
  /* Partial-function cases use the real metadata initializer, not a fake gate. */
  if (!init_case || strstr(argv[1], "_cap")) {
    struct tipd_t1_context context = tipd_t1_initialize(active_tps);
    if (strstr(argv[1], "_cap"))
      for (unsigned int i = 0; i < 130; i++) tipd_t1_cache(context, active_tps);
    if (mode_case) (void)tipd_t1_start_worker(active_tps);
  }
#endif

  if (init_case) {
    script.failure = argument(argv[2]);
    script.flags = argument(argv[3]);
    assert(script.failure <= IRQ_REQUEST && script.flags <= 4095);
    active_tps->irq = script.flags & IRQ_PRESENT ? 7 : 0;
    if (script.flags & (NO_POWER_CALLBACK | CONNECT_ERROR)) {
      if (script.flags & NO_POWER_CALLBACK) generic_data.switch_power_state = NULL;
      if (script.flags & CONNECT_ERROR) generic_data.connect = connect_error;
      active_tps->data = &generic_data;
    }
    script.init_depth++;
    result = tipd_init(active_tps);
    script.init_depth--;
  } else if (worker_case) {
    active_cd->update_status.status = argument(argv[2]);
    active_cd->update_status.status_changed = argument(argv[3]);
    active_cd->update_status.data_status = argument(argv[4]);
    active_cd->update_status.data_status_changed = argument(argv[5]);
    active_tps->data_status = argument(argv[6]);
    script.old_role = argument(argv[7]);
    int partner_kind = argument(argv[8]);
    active_tps->partner = partner_kind == 0 ? NULL :
      partner_kind == 1 ? &partner : ERR_PTR(-EIO);
    unsigned int pwr_mode = argument(argv[9]);
    bool changed_identity = argument(argv[10]);
    active_cd->connector_fwnode = argument(argv[11]) ? &connector : NULL;
    script.partner_error = argument(argv[12]);
    script.role_result = argument(argv[13]);
    script.mux_result = argument(argv[14]);
    int alt = argument(argv[15]);
    active_cd->state.alt = alt == 1 ? &dp_alt : alt == 2 ? &tbt_alt : NULL;
    active_cd->state.mode = argument(argv[16]);
    active_cd->state.data = &data_sentinel;
    assert(script.old_role <= USB_ROLE_DEVICE && partner_kind <= 2 && pwr_mode <= 3);
    assert(alt <= 2 && active_cd->state.mode <= 8);
    active_cd->update_status.pwr_status = pwr_mode << 2;
    active_cd->update_status.partner_identity = active_tps->partner_identity;
    active_cd->cur_partner_identity = active_tps->partner_identity;
    if (changed_identity) active_cd->cur_partner_identity.id_header++;
    active_cd->update_status.dp_sid_status = active_cd->dp_sid_status;
    active_cd->update_status.intel_vid_status = active_cd->intel_vid_status;
    active_cd->update_status.usb4_status = active_cd->usb4_status;
    cd321x_update_work(&active_cd->update_work.work);
  } else if (mode_case) {
    struct cd321x_status st = {
      .data_status = argument(argv[2]), .dp_sid_status = active_cd->dp_sid_status,
      .intel_vid_status = active_cd->intel_vid_status, .usb4_status = active_cd->usb4_status,
    };
    int alt = argument(argv[3]);
    active_cd->state.alt = alt == 1 ? &dp_alt : alt == 2 ? &tbt_alt : NULL;
    active_cd->state.mode = argument(argv[4]);
    active_cd->state.data = argument(argv[5]) ? &data_sentinel : NULL;
    script.mux_result = argument(argv[6]);
    assert(alt <= 2 && active_cd->state.mode <= 8);
    cd321x_typec_update_mode(active_tps, &st);
  } else if (queue_case) {
    active_tps->status = TPS_STATUS_PLUG_PRESENT;
    active_tps->pwr_status = 12;
    active_tps->data_status = TPS_DATA_STATUS_USB2_CONNECTION | CD321X_DATA_STATUS_HPD_LEVEL;
    cd321x_queue_status(active_cd);
    snapshots[snapshot_count++] = active_cd->update_status;
    cd321x_queue_status(active_cd);
    snapshots[snapshot_count++] = active_cd->update_status;
    active_tps->status = 0;
    active_tps->data_status = 0;
    cd321x_queue_status(active_cd);
    active_tps->status = TPS_STATUS_PLUG_PRESENT;
    active_tps->pwr_status = 4;
    active_tps->data_status = TPS_DATA_STATUS_USB2_CONNECTION | CD321X_DATA_STATUS_HPD_LEVEL;
    fill_payload(active_cd, 100);
    cd321x_queue_status(active_cd);
    snapshots[snapshot_count++] = active_cd->update_status;
  } else {
    active_tps->pwr_status = 12;
    active_tps->data_status = TPS_DATA_STATUS_USB2_CONNECTION;
    active_cd->update_work.pending = !!argument(argv[2]);
    script.flags = argument(argv[3]) ? SCHEDULE_FALSE : 0;
    result = cd321x_connect(active_tps, TPS_STATUS_PLUG_PRESENT);
  }

  metadata_released();
  assert(reference_gets == reference_puts && !active_tps->lock.held && !script.init_depth);
  for (size_t i = 0; i < 16; i++)
    assert(allocation[i] == 0xa5 && allocation[16 + allocation_size + i] == 0xa5);
  printf("{\"scenario\":");
  quoted(argv[1]);
  printf(",\"result\":%d,\"board_match\":%s,\"target_match\":%s,"
         "\"precheck_refs\":[%u,%u],\"production_refs\":[%u,%u],\"ledger\":[",
         result, board_match ? "true" : "false", target_match ? "true" : "false",
         precheck_gets, precheck_puts, reference_gets - precheck_gets,
         reference_puts - precheck_puts);
  for (size_t i = 0; i < event_count; i++) {
    if (i) putchar(',');
    putchar('[');
    quoted(ledger[i].operation);
    printf(",%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64 "]",
           ledger[i].a, ledger[i].b, ledger[i].c, ledger[i].d, ledger[i].e);
  }
  printf("],\"records\":[");
  for (size_t i = 0; i < record_count; i++) {
    if (i) putchar(',');
    quoted(records[i]);
  }
  printf("],\"snapshot\":");
  print_snapshot(&active_cd->update_status);
  printf(",\"snapshots\":[");
  for (size_t i = 0; i < snapshot_count; i++) {
    if (i) putchar(',');
    print_snapshot(&snapshots[i]);
  }
  printf("],\"state\":[%u,%lu,%u],\"partner\":%d,\"identity\":%" PRIu32
         ",\"pending\":[%u,%u],\"dispatches\":%u,\"allocation_bounds\":true",
         active_cd->state.alt == &dp_alt ? 1U : active_cd->state.alt == &tbt_alt ? 2U : 0U,
         active_cd->state.mode, active_cd->state.data ? 1U : 0U,
         pointer_kind(active_tps->partner), active_cd->cur_partner_identity.id_header,
         active_cd->update_work.pending ? 1U : 0U, active_tps->wq_poll.pending ? 1U : 0U,
         script.worker_dispatches);
#if TIPD_T1_PRESENT
  struct tipd_t1_context tail = tipd_t1_current(active_tps);
  printf(",\"diagnostic_counts\":[%d,%d,%d],\"tail\":[%u,%u]}\n",
         atomic_read(&tipd_t1_generations), atomic_read(&tipd_t1_workers),
         atomic_read(&tipd_t1_sequence), tail.gen, tail.worker);
#else
  printf(",\"diagnostic_counts\":[0,0,0],\"tail\":[0,0]}\n");
#endif
  forget_object(active_cd);
  free(allocation);
  return 0;
}
