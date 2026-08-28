# T1 sender record contract

This is the source contract for the selected TIPD diagnostic. It is not a capture result, binary identity, or receiver-delivery claim. The separate trace validator must also bind the exact future image/module evidence.

Every native INFO message is one ASCII JSON object plus newline, at most 384 bytes. Common fields are exactly `rev="dev147-tipddiag1-v1"`, `board="j413"`, `target="front_lower"`, `component="tipd"`, `seq`, `gen`, `worker`, `event`, and `phase`, plus only the event fields below. `seq` is 1–128. `gen` is a globally unique positive init generation, at most 2,147,483,647. `worker` is a globally unique positive worker ID with that generation, or zero for init/cache/queue. Rejected targets consume no counters. IDs are allocated before record sequence; their numeric order need not match sequence or print-arrival order.

Normal records use sequences 1–127. Reserving normal record 127 atomically reserves both 127 and 128. That invocation emits normal 127 and then `cap/end` with the same generation/worker, `limit=128`, and `reason="budget"`. Later records are suppressed. The global budget never resets across init attempts. Record 127 without 128 is incomplete even if 127 was an otherwise final terminal. Cross-thread print arrival may reorder sequence reservations. A cap does not complete an interrupted operation or authorize a negative claim.

| Event / phase | Additional fields |
|---|---|
| `init/begin` | None. This is core-init entry, not frontend probe entry. |
| `init/end` | `ret`: original signed 32-bit return; `reason`: `gpio`, `vid`, `power_state`, `mode`, `patch`, `mask`, `status`, `role`, `psy`, `port`, `power_read`, `data_read`, `irq`, `connect`, or `complete`. Only `complete` returns zero. |
| `cache/stored` | Boolean `plug`, `usb2`, `usb3`, `hpd`, `flip`, `device`; `power` is 0–3. These are existing cached facts. |
| `queue/queued` | The cache fields plus Boolean `disconnect` and `hpd_change`, from the copied queue snapshot and accumulated change masks. |
| `worker/begin` | The queue fields plus Boolean `connector` and `cached_device`. `device` is queued direction; `cached_device` is the current cached direction used by the original role decision. |
| `worker/end` | `reason`: `disconnected`, `partner_error`, or `complete`; `ret` is zero except the existing error-pointer value −4095 through −1 for `partner_error`, as bounded by the pinned `IS_ERR`/`PTR_ERR` contract. |
| `mux/begin` | `kind`: `safe`, `dp`, `tbt`, `usb4`, or `usb`; `mode`: respectively 0, 2–7, 2, 4, or 1. |
| `mux/returned` | The begin fields plus signed 32-bit `ret`. The caller still ignores it. |
| `mux/skip` | `kind`, `mode`, `reason`. `unchanged` uses the normal kind/mode. `invalid_dp_pin` uses `dp`/−1. `disconnected` and `partner_error` use `none`/−1 and mean not reached. |
| `role/begin` | `which`: `none` or `final`; `value`: 0, 1, or 2 (`USB_ROLE_NONE`, HOST, DEVICE). The `none` call has value zero. |
| `role/returned` | The begin fields plus signed 32-bit `ret`. Errors remain ignored. |
| `role/skip` | `which`, `value`, `reason`. `none`/0 uses `no_transition`. A not-reached `final` uses the already selected role and `disconnected` or `partner_error`. |
| `hpd/begin`, `hpd/returned` | Only `which`: `disconnected` or `connected`. This API is void; returned does not mean delivered or accepted. |
| `hpd/skip` | `which`, `reason`. Disconnected skips use `no_connector` or `level_high_unchanged`. Connected skips use `no_connector`, `level_low`, or the not-reached reasons `disconnected`/`partner_error`. |
| `cap/end` | `limit=128`, `reason="budget"`; sequence 128 only, paired with normal 127 as described above. |

Each uncapped worker follows begin → NONE-role pair/skip → disconnected-HPD pair/skip → mux pair/skip → final-role pair/skip → connected-HPD pair/skip → end. Both early terminals emit the three explicit not-reached skips before end. Invalid/unchanged/error mux paths do not suppress the final role or HPD decision. Each actual operation stays outside conditional log evaluation, and its original call count/order/locking and ignored returns remain unchanged.

Init may emit no cache/queue pair if detached or stopped earlier. Each reached `cd321x_queue_status` emits stored then queued, including later IRQ/poll updates after init end and unchanged snapshots. Coalescing means there is no one-to-one queue-to-worker mapping. Do not require globally adjacent cache/queue records or init end before worker begin. Missing entry, pair, tail, sequence, identity, or cap information stays inconclusive. No record contains a pointer, partner identity, raw register, filesystem identity, or new hardware read.
