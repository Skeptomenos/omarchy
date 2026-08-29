# Fixed E execution boundary and operational pre-execution contract

Status: corrected after two fail-closed production attempts. `run-f2yoto48`
exposed a gzip timestamp mismatch. `run-noq24xg7` proved the exact
`/usr/bin/gzip -n` bytes and then exposed kmod 34.2's single trailing ASCII
space on each `insmod` lookup line. Both attempts completed all 424 children
and stopped before publication. The helper now accepts exactly one trailing
space on `insmod` lines and no trailing space on `builtin ecb`. Controlled RED
`run-mnmz924l` and GREEN `run-2f6yexwm` cover that correction. Four fresh
toolchain-v5 zero-production-child sandboxes then passed 25/25 focused methods.
The current `run_e_control.py` SHA-256 is
`1be81904b29c69cb24fae86208c62fb30e830eca46250978a65d8ed19db8de77`.
The current helper SHA-256 is
`686d59e63166df1bef1afad27998a6d58f4c28b6b4439b6ccd607b56471268ca`.
The source remains inside the contained offline A2-A4 gate. All image-build,
load, stage, boot, sudo, reboot, cable, device, recovery-rehearsal, live-system,
sysfs, and boot-file holds remain active.

## Operational recipe under review

The sole execution entry is the fixed no-argument `main()`. It calls the
private `_run_operational_control()` sequence. The public `operational_policy()`
only authenticates the exact inputs and returns the fixed policy. The public
`finalize_operational_result()` always raises
`E_CONTROL_DIRECT_FINALIZE_UNAVAILABLE`. A caller cannot publish evidence
without the private execute-and-validate sequence.

The recipe keeps the accepted authenticated five-source bootstrap. It keeps the
exact eight production task inputs, 593 predicted read-only mounts, UID/GID
1001, `/work`, umask `077`, fixed environment, fixed 424-command order, 270
second control limit, 30 second per-child limit, and `E_NO_CHANGE_OFFLINE`
mode. It has no argument, environment, override, retry, repair, candidate, or
alternate-root input.

The only approved launcher is the reviewed `sandbox.py` at SHA-256
`62d3c8224cdf2add93a96195f2d35da232086b7074911c92346cd3200beee827`.
The only approved runtime is toolchain-v5. Its 582-entry manifest SHA-256 is
`5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0`.
Compared with v4, v5 changes one runtime entry only: the clean packaged
`/usr/lib/libgcrypt.so.20.7.2` entry becomes
`/usr/lib/libgcrypt.so.20.8.8`. No other runtime entry, launcher behavior, or
containment rule can change. A different launcher, manifest, entry count, or
additional library delta stops the gate before the recipe runs.

The fixed sequence is:

1. Require the exact initial `/work` membership. Authenticate the recipe, five
   source files, E base, and exact three-file index-input directory with
   no-follow bounded reads and before/open/after identity checks.
2. Reconstruct E. Require the exact early and main streams, 200-module model,
   three aliases, nine symbols, fixed built-ins, and exact 424-command plan.
3. Create the empty configuration, early stream, main stream, control root, and
   lookup root at fixed paths. Creation is exclusive. Existing or unexpected
   output stops the recipe.
4. Run the fixed plan once through the accepted `Commands` boundary. Child 4
   is exactly `/usr/bin/gzip -n` and receives the exact main stream as stdin.
   Bare `/usr/bin/gzip` is not approved. The positional stdout caps,
   one-byte stderr cap, 128 KiB report cap, and 270/30 second limits are fixed.
   The recipe does not retry, clean, repair, or replace partial output.
5. Collect all 424 records with bounded no-follow reads. Require exact command
   identity, status `ok`, return code zero, `observed_bytes == retained_bytes`,
   empty stderr, positive PID, `killed == false`, and `reaped == true`.
6. Validate archive listings, exact gzip output, four payloads, both
   `modprobe --show-config` dumps at children 10-11, all 200 filename and
   dependency lookups, three aliases, nine symbols, exact regenerated indexes,
   retained indexes, and the known `modules.symbols.bin` exception.
7. Create the header and evidence with exclusive writes, then capture their
   exact bytes and identities. After those two files exist, re-read every input,
   re-collect every record, re-read both bounded module roots, recheck the early,
   main, and empty-config files, and require exact input, record, root, leaf,
   materialized-file, header, evidence, and `/work` identity and membership.
8. Construct the result and acceptance in memory after that final sweep. Write
   the result only to the fixed
   `/work/e-control-result.pending` path. Re-read and verify that pending file
   while `/work/e-control-result.json` is absent. Rename pending to final with
   the existing no-replace helper as the last fallible operation. Return the
   precomputed acceptance without any post-rename check or mutation.

The header, evidence, result, and acceptance state offline no-change only. They
set image creation, module load, staging, boot, and candidate-module binding to
false. Failure preserves partial output for review. It never converts partial
output into acceptance.

The recipe, semantic, structural, and execution runners are pinned to the exact
candidate source. Their focused checks remain zero-child. They may
inspect the read-only execution policy, fixed planner, authenticated bootstrap,
bounded collector, structural fixture, semantic fixture, private-entry source
shape, and direct-finalizer refusal. They do not invoke `main()`,
`operational_policy()` in a nine-input harness, or any workload child. The
corrected revision passed 25/25 focused dynamic methods after its static parse,
compile, source-shape, mutation, and diff checks. The
[second-attempt and lookup-correction evidence](../../../../docs/evidence/dev-147-e-operational-second-attempt-lookup-grammar-2026-08-30.md)
owns the current run directories, hashes, results, and containment facts. The
[first-attempt and gzip-correction evidence](../../../../docs/evidence/dev-147-e-operational-first-attempt-gzip-determinism-2026-08-29.md) and
[dated round-3 evidence](../../../../docs/evidence/dev-147-e-operational-preexecution-gate-2026-08-29.md)
remains the pre-attempt history. The correction result is zero-child evidence.
It is not an operational no-change PASS.

The structural runner uses only the distinct `/work/e-control-structural-*`
fixture namespace. The semantic runner uses only the distinct
`/work/e-control-semantic-fixture-*` roots, streams, configuration, records, and
result. Those fixture files model observations and always state zero executed
children and no fresh proof. No accepted zero-child run created the production
`/work/control-root`, `/work/lookup-root`, `/work/e-early.cpio`,
`/work/e-main.cpio`, `/work/empty-modprobe.conf`,
`/work/e-control-children-e1`, real header or evidence, pending result, or final
`/work/e-control-result.json`.

The execution runner requires the exact 230-node full-module top-level
membership, count, and order. It also authenticates the complete 83-node
operational block with per-node normalized AST hashes and exact order. It retains
the accepted baseline and fixed bootstrap/collector templates. A closed
internal call graph must make every operational helper reachable from the fixed
private entry, except the two intentional public policy/refusal functions. The
runner requires the exact validator order, fixed constants and positional caps,
one `Commands` constructor site, two fixed `runner.run` AST sites, the complete
input/output resweep, and the exact pending-to-final publication tail. Static
negative mutations change a cap, substitute the launcher, reorder validators,
remove an input resweep, write the final path directly, break pending
verification, and add work after rename. Every mutation must fail the contract.
Two more mutations insert an executable call and rebind `Commands` immediately
before `ExecutionPolicy`; both must fail the full-module boundary.

The semantic zero-child runner separately checks the exact subject pin and the
83-node operational suffix AST SHA-256
`597131f931549deb081af6de5850d7f6e81d962ea9fac0dd3f6673686fd72418`.
Before it imports the recipe, it vets the authenticated source. The vet permits
only the exact imports, pure module assignments, exact frozen dataclasses, fixed
bootstrap definition and sole call, sole reviewed `ctypes` bindings, and the
sole final `__main__` guard. The runner authenticates its own bootstrap shape and
requires the pre-import source gate immediately before the sole subject
`load_source` call. It also protects the imported `e_control`, `math`, and
`NoReturn` bindings from later replacement. The publication scan covers the
complete prefix before `ExecutionPolicy`. It permits `os.open`, `write_new`, and
`os.sys.modules.update` only at the fixed authenticated loader, structural
reader, pending semantic publisher, and bootstrap rollback sites. Three negative source mutations insert
`runner.run(())`, `os.environ.update({})`, or a decoy `write_new(...)` call at
the semantic/operational boundary. Both the pre-import and publication gates
must reject every mutation. The separately authenticated operational suffix
keeps its legitimate fixed `runner.run` sites outside the prefix scan.

## First production attempt and correction

Fresh probe `run-8xph_o58` passed. The sole production attempt,
`run-f2yoto48`, then used exactly 593 read-only mounts. All 424 child reports
were complete and all 1,272 child triplet files were retained. Every child
reported status `ok`, return code zero, empty stderr, a positive PID, no kill,
and a completed reap. The recipe still exited 1 at
`_validate_archive_observation()` for child 4 with
`E_CONTROL_SEMANTIC_INVALID`.

The expected and observed gzip streams were both 19,181,273 bytes. The expected
SHA-256 was
`375aa35be0ea57fa8d3f79f20cfa70373742ba6e2afda409462497d0d96ad724`.
The observed SHA-256 was
`35ae12e147f556cd6fa5fadb7749acc69e8e60bf91593669c18e527b75070e8d`.
Only one-based bytes 5-8 differed. Retained E stored a zero modification time.
The observed stream stored `2026-08-29T17:04:07Z`, copied from the exact main
stream. The compressed payload and trailer were otherwise identical, and both
streams decompressed to SHA-256
`7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28`.

The fail-closed boundary worked. No control header, evidence, pending result,
final result, or fresh proof exists. Inputs stayed unchanged. No timeout
occurred. No process remains active. No retry ran.

The correction changes the fixed command identity only. It adds `-n`, which
the retained local GNU gzip help defines as no stored name or timestamp. Bare
gzip is now rejected by the helper and every focused command-plan check. The
semantic fixture changed only its child-4 report. Its size changed from 648 to
658 bytes. Its SHA-256 changed from
`75fec501f6e0ef237715a107ce81bfbca3064b6d11944ad9b768751785fd7c6b` to
`7d7060b4d09adeee70fa3b0eccacf75225912cb1289391a2722a705bed597642`.
The directly derived aggregate SHA-256 changed from
`68dd45eeeb9239b873c293b81cbbb5b7403d4ff0d5d1b5a32f3e27c14c92d44e` to
`5f80a3cf89e2c21e9f694cb8ed47a062aa44003f554ceb18f5de3fc87ea6ebf0`.

Corrective zero-child runs `run-voc0ceb9`, `run-q_c6c496`, `run-ng6qerzs`,
and `run-z2rki6ms` passed 16/16, 3/3, 3/3, and 3/3. They ran no workload child.
Independent QA runs `run-wdid9vqb`, `run-qv63ivbi`, `run-3sjaril5`, and
`run-r24xtx2w` repeated the same 25/25 zero-child result. Direct-helper QA
`run-kyar_nn2` passed 18/18 with 591 read-only mounts and 11 bounded fixture
children. Its exact `/usr/bin/gzip -n` header had zero MTIME. Its refusal test
rejected bare `/usr/bin/gzip` before child execution. These QA runs created no
E-derived production tree, production stream, child-e1, header, evidence,
pending, or final output. The helper run created synthetic ASCII fixture trees
at the exact names `/work/control-root` and `/work/lookup-root`. The linked
correction evidence records the exact pins.
That corrected production entry ran once as `run-noq24xg7`; its result is the
second fail-closed checkpoint below. No third production attempt is authorized
by these results.

## Second production attempt and lookup correction

Fresh probe `run-x65x28u0` passed with the exact eight inputs and 593 read-only
mounts. The one authorized gzip-corrected production attempt,
`run-noq24xg7`, then ran the fixed 424-child plan once. It exited 1 without a
timeout. All inputs stayed unchanged. Exactly 1,272 child triplet files exist.
Every child reported status `ok`, return code zero, retained bytes equal to
observed bytes, empty stderr, a positive unique PID, `killed: false`, and
`reaped: true`.

Child 4 used exact `/usr/bin/gzip -n`. Its SHA-256 is
`375aa35be0ea57fa8d3f79f20cfa70373742ba6e2afda409462497d0d96ad724`.
Its MTIME field is zero, and its decompressed SHA-256 is
`7be7b4b03367b5ce4b356fe35977edba6540af0a7df930dbff990286c9b98e28`.
Validation advanced to `e_control.ordered_lookup()` and stopped with
`LOOKUP_FORMAT`, wrapped as `E_CONTROL_OPERATIONAL_INVALID`. Across 212
dependency, alias, and symbol outputs, kmod 34.2 emitted 347 lines. Exactly 346
`insmod` lines have one trailing ASCII space before newline. The sole
`builtin ecb\n` line has none. Child 13, the first module lookup for `842`, was
the first comparison to expose the difference from the helper's old no-space
canonical form.

No header, evidence, pending result, final result, or fresh proof exists. The
retained control root has 214 files and the lookup root has 207 files. Compared
with `run-f2yoto48`, only child 4's command and stdout differ; the other 423
stdout files are byte-identical. No production process remains. No retry ran.

The direct-helper oracle first changed to the observed kmod grammar.
`run-mnmz924l` then recorded the controlled current-helper RED: 18 methods,
one expected assertion failure, zero errors or skips, 591 read-only mounts, and
11 bounded fixture children. The minimal helper change adds exactly one space
to canonical `insmod` lines. `run-2f6yexwm` passed 18/18 in 1.174 seconds. It
also rejects missing spaces, doubled spaces, a spaced builtin, altered paths,
reordering, duplicates, missing records, and extras.

Final SWE boundary runs `run-rte0vj2a`, `run-hgr5p8p1`, `run-trmsyl6z`, and
`run-lsiwy1ye` passed 16/16, 3/3, 3/3, and 3/3. They used 605, 594, 606, and
594 read-only mounts. They ran zero production children. The semantic aggregate
stayed exactly
`5f80a3cf89e2c21e9f694cb8ed47a062aa44003f554ceb18f5de3fc87ea6ebf0`.
Independent QA repeated the direct-helper suite in `run-i_x5ec4n` and the
four zero-production-child boundary suites in `run-ks9kn889`,
`run-81ol5s2v`, `run-_y7n3i3t`, and `run-bam09x3u`. The
[second-attempt evidence](../../../../docs/evidence/dev-147-e-operational-second-attempt-lookup-grammar-2026-08-30.md)
owns the production facts. The [independent QA evidence](../../../../docs/evidence/dev-147-e-lookup-correction-independent-qa-2026-08-30.md)
owns the fresh QA results. Final review passed with no blockers. There is no fresh
E-control PASS. Any third
production attempt requires a separate GO and a fresh v5 probe.

## Retained zero-child boundary history

Status: accepted RED and corrected zero-child GREEN. RED `run-0zk61la1`
produced the exact three controlled assertion failures. First GREEN
`run-_l2w9p_k` stopped on the retained Python 3.14 `Path`/`PosixPath` predicate
defect. Corrected GREEN `run-nr5woop4` passed all three methods. The
[dated evidence](../../../../docs/evidence/dev-147-e-execution-boundary-2026-08-29.md)
owns the exact hashes, results, and limits. Those checkpoints did not run the
424-command workload or open `main()`, `operational_policy()`, or
`finalize_operational_result()`.

## Current zero-child scope and holds

This is an unprivileged offline A2 test gate. All candidate-image, assembly,
staging, sudo, reboot, cable, device, recovery-rehearsal, live-system, sysfs,
module-load, and boot-file holds remain active. The runners execute no workload
child. The structural and semantic runners can create only their distinct
fixture roots, streams, configuration, records, headers, evidence, and result.
They do not create a production module root, production cpio stream, production
configuration, child record root, or real E-control result.

The RED subject was `run_e_control.py` at SHA-256
`70f369f87942b6ca6826c808536353ae0cc400123204040b9c005995ab43c3e3`.
The corrected zero-child GREEN subject was
`39496435f113c7d9256e5592effd3fece8c52b0e61b774e8283fe96eb84d4add`.
At that historical checkpoint, its three operational APIs
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

The retained RED subject stopped each method at its first missing-attribute assertion and created no synthetic loader or collector fixtures. The corrected GREEN crosses those assertions, runs the same static gates, and then runs zero-child dynamic probes. Before the collector call, the runner snapshots every path, cap, count, and policy global and requires exact equality with runner-owned literals. Spies replace only the bounded reader, record-root validator, and bounded-tree reader while the authenticated `_collect_operational_outputs()` function runs. They require exactly 1,272 indexed `child-NNN.stdout|stderr|json` reads with runner-owned positional caps, the three runner-owned fixed stream/config reads, one validator call, the exact two runner-owned tree calls, and exact identity-preserving wiring of all eight `RawControlFiles` fields. The policy snapshot must remain exactly unchanged immediately after the call. Only the three mocked helper attributes are restored, and their object identities are rechecked. Expected roots, paths, caps, and returned bytes never derive from mutable subject globals after the collector call. The spies touch no real operational path.

The corrected GREEN creates contained files only below `/work/e-control-execution-red`. It proves the bounded reader returns exact bytes and refuses a relative path, overflow, wrong mode, hard link, symlink, and directory. It proves exact UID/GID 1001 and single-link regular metadata through both the positive files and enforced AST comparisons. It temporarily redirects only `OPERATIONAL_RECORD_ROOT`, restores it in `finally`, and proves the exact 1,272-member record tree plus missing, extra, symlink, index, and suffix refusal. Independent bounded-tree fixtures prove the exact returned `TreeState` and refuse wrong path, extra/missing files, extra/missing directories, excessive depth, per-file overflow, aggregate overflow, symlink, hard link, wrong file mode, and wrong directory mode. Every invalid fixture raises exactly `E_CONTROL_OPERATIONAL_INVALID`. Operational APIs remain unconditionally closed before and after these probes.

All three methods first recheck the pure setup, exact 8/593 production model,
closed operational APIs, zero child directories, and absence of every real
output. The retained RED result is exactly three assertion failures, zero
errors, zero skips, unchanged inputs, and zero workload children. The corrected
GREEN result is exactly three passes, zero failures, errors, or skips, unchanged
inputs, and zero workload children.

Both retained runner revisions accept only the exact three test selectors shown
below. The RED revision postcheck accepted only the three ordered assertion
failures and exited 1. The current GREEN revision accepts only three passes,
zero failures, errors, or skips, and exits 0. Any other selection or result
exits 2.

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

The current corrected candidate implements the fixed operational sequence, but
the zero-child gate does not authorize or prove that sequence. Direct result
publication remains closed through `E_CONTROL_DIRECT_FINALIZE_UNAVAILABLE`.
Two previous candidates each ran `main()` once and failed closed. The current
lookup-corrected candidate's `main()` has not run. All live/manual holds remain
active.
Independent QA and final review are complete. A separate GO is still required.
A fresh toolchain-v5 containment probe must then pass before any
separately authorized third exact
eight-input, 593-mount, 424-child offline no-change attempt. Any source, runner,
launcher, manifest, setup, containment, input, command, child, output, or result
difference stops the gate. It does not trigger another retry, image build,
staging step, or manual action.
