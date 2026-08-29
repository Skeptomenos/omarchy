# Fixed E execution boundary: zero-child RED contract

Status: authored, not yet executed. This checkpoint adds only the next RED
runner. It does not add a production launch, run the 424-command workload, or
open `main()`, `operational_policy()`, or `finalize_operational_result()`.

## Scope and holds

This is an unprivileged offline A2 test. All candidate-image, assembly, staging,
sudo, reboot, cable, device, recovery-rehearsal, live-system, sysfs, module-load,
and boot-file holds remain active. The runner executes no workload child. It
does not create either module root, either cpio stream, an empty modprobe
configuration, or a real E-control result.

The current accepted subject is `run_e_control.py` at SHA-256
`70f369f87942b6ca6826c808536353ae0cc400123204040b9c005995ab43c3e3`.
It remains unchanged for this RED. Its three operational APIs must continue to
raise exactly `E_CONTROL_RECIPE_UNAVAILABLE` before, during, and after the test.
Each authenticated AST body must contain only its docstring and the unconditional
one-statement `raise RecipeError("E_CONTROL_RECIPE_UNAVAILABLE")`. No read,
write, process, policy, or other side effect can precede the refusal.

## Harness versus production bindings

The RED harness has nine task inputs because `/inputs/test` is the runner. Its
predicted read-only mount total is 594: 582 frozen runtime entries, the fixed
proof/isolation/smoke files, and nine task inputs. This is not the production
input count.

The later production invocation has exactly these eight task bindings:

| Binding | Fixed content |
|---|---|
| `/inputs/recipe` | The reviewed `run_e_control.py`. |
| `/inputs/subject` | Directory containing only pinned `e_control.py`. |
| `/inputs/contract` | Directory containing only pinned `image_contract.py`. |
| `/inputs/assembly` | Directory containing only pinned `prepare_image.py`. |
| `/inputs/control` | Directory containing only pinned `verify_control.py`. |
| `/inputs/helper` | Directory containing only pinned `cpio_image.py`. |
| `/inputs/base` | Exact E image, 19,191,513 bytes, SHA-256 `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae`. |
| `/inputs/index-inputs` | Directory containing only the three pinned original depmod inputs. |

The production prediction is exactly 593 read-only mounts: 582 runtime mounts,
three fixed proof/isolation/smoke mounts, and eight task mounts. The twelve
historical generated-index/dump fixtures are absent. No candidate module or
image is an input.

The fixed production command is:

```text
/usr/bin/python3.14 -I -S -B /inputs/recipe
```

It runs as UID/GID 1001, from `/work`, with umask `077`, no capabilities, no
network route, and only `/work` and `/tmp` writable. The fixed launcher-set
environment is `PATH=/usr/bin:/bin`, `LC_ALL=C`, `TMPDIR=/tmp`, and
`PYTHONDONTWRITEBYTECODE=1`; bubblewrap also supplies `PWD=/work`. The mode is
`E_NO_CHANGE_OFFLINE`. No caller can
select a source path, identity, mode, command, base, index set, output root,
timeout, cap, fixture, candidate, or alternate control.

## Three controlled assertion REDs

The runner authenticates the recipe, all five source files, E, the three index
inputs, the fixed proof file, and exact input membership before unittest runs.
It executes the authenticated pure E selector and exact 424-command planner.
The runner independently reconstructs the full ordered plan and requires exact
tuple equality before it associates positional output caps. Allowlist membership
alone is insufficient. Every command must also pass the separately tested fixed
allowlist. None can be a Python self-check. Setup/import/authentication,
identity, plan, or ordering failure is an error, not accepted RED.

Setup has two authenticated paths. The accepted 144-node baseline manifest uses
the existing harness preload sequence: load `prepare_image`, verify its nested
`verify_control` and `cpio_image` modules, then load `t1_image_contract`,
`e_control`, and the recipe. The exact future manifest does not preload any of
those five dependency modules. It loads only the recipe as `e_recipe` while all
five names are absent. The recipe's exact self-bootstrap then authenticates and
loads all five sources. Setup retrieves `e_control` from `sys.modules` and
requires every loaded module's `__file__` to equal its fixed input path. The
`future_subject` branch value is derived only from equality with the
authenticated future manifest. It is not a caller input. Both paths restore the
original isolated `sys.path` in the same outer `finally` block.

Before it executes the authenticated recipe, the runner parses and vets its AST.
It stores a normalized AST SHA-256 manifest for all 144 accepted top-level nodes.
Each existing import, assignment, class, function, and the final guarded `main()`
call must keep its exact normalized AST. This freezes import forms and aliases,
annotations, defaults, decorators, class bodies, `_require()`, `_sha256()`,
`_structural_identity()`, all existing helpers, all three closed operational
APIs, the accepted `ctypes.CDLL(None, use_errno=True)` binding, and the exact
three `renameat2` attribute assignments. A future source cannot remove, change,
duplicate, or rebind an accepted node.

The runner also contains complete normalized-AST reference templates for every
new GREEN node. It compares each new node's full `ast.dump()` to its reference.
It does not use name-presence, call-name allowlists, or heuristic predicate
searches as the security boundary. The templates fix signatures, annotations,
decorators, constants, statements, predicates, calls, dataflow, branches,
loops, returns, and exception handling for all fixed-source, policy, bounded
reader, record-root, tree, and collector nodes. Any extra top-level node is
rejected.

The future top-level order is exact. The unchanged standard imports remain
first. The existing `RecipeError` class and `_require()` function move unchanged
to the early authenticated block. They appear once, after the standard imports
and before the fixed-source constants, helpers, bootstrap definition, and sole
bootstrap call. This move makes `_require()` usable when the bootstrap runs.
The sole `_bootstrap_fixed_sources()` call then runs before the unchanged
`cpio_image`, `prepare_image`, and `verify_control` imports. All other accepted
nodes keep their relative order. The new policy, cap, bounded-reader, tree, and
collector nodes have one fixed insertion point immediately before the existing
`operational_policy()` node. The unchanged `if __name__ == "__main__": main()`
guard appears exactly once and remains last.

The exact loader template uses `source = Path(path)` and
`os.open(source, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)`.
It directly enforces regular mode `0600`, UID/GID 1001, one link,
`0 < st_size <= 128 KiB`, before/open/after identity, the exact
`read(FIXED_SOURCE_BYTES + 1)`, `len(raw) == st_size <= FIXED_SOURCE_BYTES`,
and `hashlib.sha256(raw).hexdigest() == digest`. The actual capped `raw` bytes
flow into `exec(compile(raw, str(source), "exec"), module.__dict__)`. The exact
template constructs the module as `type(os)(name)` and publishes it through
`os.sys.modules[name]` only after all metadata, identity, length, and hash
checks. No alternate branch, decoy predicate, or different call graph can
match the reference.

After valid setup, exactly these three methods must fail at their named missing
boundary:

1. `test_a_fixed_self_bootstrap_is_missing` requires a no-argument fixed
   five-source bootstrap. It must authenticate all five literal paths and
   hashes. It first executes `prepare_image`, whose accepted internal loader
   authenticates and loads `verify_control` and `cpio_image`. It then verifies
   those exact module files and directly loads `t1_image_contract` and
   `e_control`. The bootstrap therefore makes exactly three direct fixed-loader
   calls, in exact order, as `*FIXED_SOURCE_INPUTS[2]`, `[3]`, and `[4]`, while
   authenticating all five exact entries. The loader permits only bounded
   regular single-link sources. It uses no-follow reads capped at 128 KiB plus
   one byte. Full identity and hash checks precede module construction, `os.sys.modules`,
   and `exec`. The loader call graph excludes path widening, dynamic import,
   process, and file-mutation APIs. The fixed bootstrap may only snapshot
   `os.sys.path` once and restore that exact tuple once in the outer `finally` block around all three loader calls. It must also snapshot `dict(os.sys.modules)` before loading. An inner `except Exception` must clear and update `os.sys.modules` from that exact snapshot, then use a bare re-raise. A wrong-digest probe must refuse as
   `E_CONTROL_SOURCE_INVALID` before module publication. One reachable
   top-level bootstrap call must run before the first fixed dependency import.
   The runner captures the original isolated `sys.path` before setup loading.
   Both setup and a zero-child direct import probe must restore it exactly and leave no `/inputs` entry. The direct probe saves, restores, and verifies the complete pre-probe `sys.modules` mapping by key and object identity. A second probe corrupts the contract-source digest so import fails after the nested assembly loader has started. Before the harness cleanup runs, it proves that the subject's exception handler already restored the complete pre-bootstrap module mapping and that the subject's `finally` already restored the isolated path. Harness cleanup remains a final containment guard only. Separate wrong-digest calls use both an all-zero digest and a one-nibble flip of the correct digest for each of the three direct source entries `[2]`, `[3]`, and `[4]`. Later GREEN-only fixtures under the META root prove one valid source and refuse wrong mode, hard link, symlink, and 128-KiB overflow without a process.
2. `test_b_exact_execution_policy_is_missing` requires a frozen
   `ExecutionPolicy` returned by no-argument `operational_execution_policy()`.
   It binds the exact command, environment, eight bindings, identity, working
   directory, umask, mount arithmetic, 424-child count, 270-second internal
   budget, 30-second child cap, and unchanged 280/285-second outer limits. Every constructor keyword value in the authenticated function must be one `Name` or `Constant`; calls, attributes, subscripts, comprehensions, and computed expressions are rejected before the function is invoked.
3. `test_c_bounded_operational_collector_is_missing` requires a no-argument,
   read-only operational collector and a two-argument no-follow bounded file
   reader. The reader uses the exact no-follow `os.open` dataflow. Its regular, mode, UID/GID, link, size, open-identity, after-read identity, and `len(raw) == st_size <= limit` predicates must each be a direct exact `_require(..., "E_CONTROL_OPERATIONAL_INVALID")` statement. Its only return is the authenticated `raw` bytes. The collector must have three explicit record reads per loop item:
   stdout under its indexed cap, stderr under the one-byte detection cap, and
   JSON under 128 KiB. All three calls must be inside the one exact 424-item
   loop and use the indexed fixed record path. The bound reader's actual
   `read()` argument is `limit + 1`; complete before/open/after identities must
   match. Separate bounded reads cover the empty config, early stream, and main
   stream. A no-follow record-root validator binds exactly 1,272 entries. A
   bounded tree helper traverses every leaf in each fixed root with limits of
   214/207 files, 48 directories, depth 16, 2 MiB per file, and 64 MiB in
   aggregate. The collector makes exactly two fixed tree calls. Neither helper
   can reach `snapshot()`, `read_regular()`, an unbounded traversal, a process,
   or a mutation API. The reader, record-path helper, record-root validator, bounded-tree reader, and collector each have a closed explicit call graph. Every call target is a named safe read-only helper or constructor. Unknown helpers, lambdas, process aliases, `read_bytes()`, plain `open()`, and existing unbounded readers are rejected.

The current accepted subject stops each method at its first missing-attribute assertion. Therefore the current RED creates no synthetic loader or collector fixtures. After a future implementation crosses that assertion, the same method first runs static gates and then runs zero-child dynamic probes. Before the collector call, the runner snapshots every path, cap, count, and policy global and requires exact equality with runner-owned literals. Spies replace only the bounded reader, record-root validator, and bounded-tree reader while the authenticated `_collect_operational_outputs()` function runs. They require exactly 1,272 indexed `child-NNN.stdout|stderr|json` reads with runner-owned positional caps, the three runner-owned fixed stream/config reads, one validator call, the exact two runner-owned tree calls, and exact identity-preserving wiring of all eight `RawControlFiles` fields. The policy snapshot must remain exactly unchanged immediately after the call. Only the three mocked helper attributes are restored, and their object identities are rechecked. Expected roots, paths, caps, and returned bytes never derive from mutable subject globals after the collector call. The spies touch no real operational path.

The future GREEN continuation then creates contained files only below `/work/e-control-execution-red`. It proves the bounded reader returns exact bytes and refuses a relative path, overflow, wrong mode, hard link, symlink, and directory. It proves exact UID/GID 1001 and single-link regular metadata through both the positive files and enforced AST comparisons. It temporarily redirects only `OPERATIONAL_RECORD_ROOT`, restores it in `finally`, and proves the exact 1,272-member record tree plus missing, extra, symlink, index, and suffix refusal. Independent bounded-tree fixtures prove the exact returned `TreeState` and refuse wrong path, extra/missing files, extra/missing directories, excessive depth, per-file overflow, aggregate overflow, symlink, hard link, wrong file mode, and wrong directory mode. Every invalid fixture must raise exactly `E_CONTROL_OPERATIONAL_INVALID`. Operational APIs remain unconditionally closed before and after these probes.

All three methods first recheck the pure setup, exact 8/593 production model,
closed operational APIs, zero child directories, and absence of every real
output. With the accepted subject, the intended result is exactly three
assertion failures, zero errors, zero skips, unchanged inputs, and zero workload
children.

The runner accepts only the exact three test selectors shown below. Its
postcheck accepts only three tests, three assertion failures in that same order,
zero errors, and zero skips. Any other selection or result exits 2, not 1.

The exact inner command is:

```text
/usr/bin/python3.14 -I -S -B /inputs/test EExecutionRedTests.test_a_fixed_self_bootstrap_is_missing EExecutionRedTests.test_b_exact_execution_policy_is_missing EExecutionRedTests.test_c_bounded_operational_collector_is_missing
```

## Explicit collector caps

The 424 stdout caps are fixed by command family:

| Children | Stdout cap |
|---:|---:|
| 0-1 | 1 KiB each for the early archive lists. |
| 2-3 | 64 KiB each for the main archive lists. |
| 4 | 19,181,273 bytes, the exact compressed E tail size. |
| 5-8 | Exact payload sizes: 1,213,760; 12,368; 66,512; and 20,312 bytes. |
| 9 | One byte; successful depmod must still produce empty stdout. |
| 10-11 | 128 KiB each for the two `modprobe --show-config` dumps. |
| 12-411 | Alternating 4 KiB filename and 64 KiB dependency caps. |
| 412-423 | 64 KiB each for three alias and nine symbol lookups. |

Every child uses a one-byte stderr detection cap and a 128 KiB JSON report cap.
The empty config cap is one byte. The exact early and main stream caps are
10,240 and 61,286,668 bytes. The record-root and tree limits above are part of
the same fixed policy; they are not caller parameters.
The existing `Commands` helper remains the only future process boundary. Its
active limit, kill, and reap behavior is already separately accepted. The new
collector only reads retained outputs. It cannot launch, retry, repair, delete,
rename, publish, or accept a partial control.

No GREEN implementation or workload execution is authorized by this document.
After an accepted RED, the next change may implement only these fixed launch
primitives while the three operational APIs and all live/manual holds remain
closed. A separate independent review is still required before any real child
runs.
