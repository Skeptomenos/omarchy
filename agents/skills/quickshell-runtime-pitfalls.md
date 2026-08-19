# Quickshell Runtime Pitfalls

Constraints and known failure modes when developing shell plugins on this machine
(quickshell 0.3.0-2, Arch Linux ARM aarch64 / Asahi M2, Qt 6.11.1). Two upstream
quickshell bugs make the shell fragile during plugin iteration; both were confirmed
here on 2026-08-19 with core-dump forensics. Read this together with
[`shell-dev.md`](shell-dev.md).

## Pitfall 1: plugin hot-reload plants a delayed use-after-free

Every save of a local plugin triggers `Local plugin changed, reloading: <id>`, which
destroys and recreates IpcHandlers. Before the guard below landed, every reload
stranded a freed handler for target `osd` (`shell/plugins/osd/Osd.qml`) in the
registry. A recurring warning for one target on each reload is the signature
(see "Reading the duplicate warning" below):

```
WARN scene: QML IpcHandler at .../Osd.qml[...]: Handler was registered but will not
be used because another handler is registered for target osd
```

The SIGSEGV detonates **later** — sometimes minutes later — when the freed hash
memory gets reused; IPC calls in between can keep succeeding. Upstream:
[quickshell#898](https://github.com/quickshell-mirror/quickshell/issues/898)
(forensics from this machine are in a comment there); related: #956, #950, #963.

**Root cause (proven 2026-08-19, minimal repro in quickshell 0.3.0):**
`IpcHandler::~IpcHandler()` calls `findObjectGeneration(this)`, which returns
null during QML destruction, so the destructor **silently skips deregistration**
(`src/io/ipchandler.cpp`, `updateRegistration`). The registry keeps a dangling
pointer; the next handler for the same target is rejected as a duplicate.
Services escape because their `enabled` bindings flip false while the context
is still alive. The exposed case is a **keepLoaded panel** whose IpcHandler
dies through plugin-reload teardown.

Severity: the registry does not only *read* the stale pointer. `deregisterHandler`
promotes `knownHandlers.first()` into the active map and ends with
`handler->registeredState = ...` — a **write** through the pointer. A stranded
freed handler can therefore be promoted and written to, which corrupts allocator
metadata and crashes later in unrelated code. See
[basecamp/omarchy#7362](https://github.com/basecamp/omarchy/issues/7362), the
same trigger on x86_64 crashing in glib and QV4 GC.

### Reading the duplicate warning: two different patterns

The warning alone does not prove a leak. Tell them apart by shape:

- **Accumulation (the bug).** One target warns again on *every* plugin reload,
  indefinitely. Only `osd` did this here — 28 warnings across two days, one per
  reload, until the guard landed.
- **Transient overlap (benign).** Many targets warn in the *same second*, once,
  then never again. A synchronized bar rebuild registers the new widgets before
  the old ones deregister. Ten `omarchy.*` bar and panel targets did this in five
  one-second bursts on 2026-08-18, then stopped; the registry stayed healthy and
  every target kept working.

Verify with `quickshell -p <shell dir> ipc show`: healthy output lists each
target once, with its full function list and no empty-name entries.

**Working guard** (validated; apply to any keepLoaded panel's IpcHandler, and
remove once quickshell deregisters correctly on destruction):

```qml
IpcHandler {
  target: "..."
  Component.onDestruction: enabled = false
}
```

A non-keepLoaded panel that happens to be **open** during a plugin reload has
the same exposure; add the guard when adding an IpcHandler to any panel entry
point.

Do not:

- assume a crash was caused by the QML you just saved — if the crash stack ends in
  `IpcServerConnection` / socket `readyRead`, check the log for an earlier
  duplicate-handler warning instead
- keep relying on shell IPC after the duplicate warning appeared — restart the
  shell cleanly first
- rapid-fire saves; batch edits so the reload churn stays low

## Pitfall 2: IPC-requested restarts abort and stack instances

`Exiting due to IPC request` → in-place relaunch → qFatal
`Quickshell's log filter has been installed twice. This is a bug.` → SIGABRT.
So every IPC-driven restart in a dev loop produces a crash report, and each aborted
relaunch leaves live sibling processes behind. Symptoms of stacked instances:

- `Could not register app ID: Connection already associated with an application ID`
- `Could not register notification server at org.freedesktop.Notifications`
- `An instance of this configuration is already running`
- several live `quickshell` processes plus unreaped zombies under the launcher

Recovery: kill **all** quickshell processes and start the shell fresh (or log
out/in). Do not keep issuing IPC restarts into a launcher that has already aborted
once — it compounds.

## Constraints

- Plugin ids: the `omarchy.` prefix is reserved for first-party plugins.
  `PluginRegistry` rejects it and `summon` then fails with "unknown plugin". Use a
  personal prefix (e.g. `david.keyboard-preview`). An id change needs a full shell
  restart, not a hot reload.
- A local plugin must be enabled before `summon` will show it
  (`summon: plugin not enabled, not summoning: <id>` otherwise).

## Crash triage on this machine

- Reports: `~/.cache/quickshell/crashes/<run-id>/report.txt` plus the full session
  log `log.qslog.log`. The qslog is a binary format — plain `grep` silently misses
  text; pipe through `strings` first.
- Cores: `coredumpctl list` / `info`. A top of `raise` + `SI_TKILL` is quickshell's
  crash handler re-raising; the real fault context sits below the signal trampoline
  frame (`<signal handler called>` in gdb).
- The binary is stripped and Arch Linux ARM publishes no debug packages or
  debuginfod, so symbolize by module offset (`quickshell + 0x...`) and instruction
  patterns, not names.
- The memory bugs themselves are upstream quickshell bugs; file them at
  quickshell-mirror/quickshell, not basecamp/omarchy. What *does* belong to
  Omarchy is its own shell QML — the `Component.onDestruction` guard and the
  plugin-reload path that triggers the bug (see basecamp/omarchy#7362).
