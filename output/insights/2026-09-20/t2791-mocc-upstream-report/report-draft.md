# Draft issue body for the ccbench upstream repository — observation report only (not sent; [T-2791])

**Status of this file.** English draft of a GitHub issue body. It has not been sent. Sending is a human decision (D2148 item 13, D16).
Every sentence carries a tag `[S-nn]`; `evidence-map.md` in this directory maps each tag to the primary source (path and SHA-256).
Strip the tags before posting. Do not add factual claims when editing; re-check against `evidence-map.md` instead.

---

## Title

`mocc: G2 (write-skew-shaped) cycles reported by an external serializability checker under trace-enabled builds (witness off, BACK_OFF=0 and =1) — observation report, no root cause, no fix proposed`

## Summary

[S-01] While running the `mocc` protocol under a trace-enabled observation build on our fork branch, an external serializability checker that we maintain reported, in a small fraction of 3-second YCSB runs, a dependency-graph cycle of length 2 whose two edges are both anti-dependencies (rw) — i.e. a G2 / write-skew-shaped anomaly under Adya's classification.
[S-02] The experiments summarized here reported 21 such signal runs in total (this count excludes one earlier pilot observation of the same shape mentioned in our August 26 record, which is not part of any tabulated experiment), and every one of them has the same shape: exactly one cycle, length 2, both edges rw, the two transactions committed in the same epoch with adjacent or near-adjacent tids (differing by 1 in 20 of the 21 pairs and by 2 in one pair), and every integrity counter of the trace at zero.
[S-03] The signal was reported only in producer configurations with our "payload-lineage witness" instrumentation switched off, under both `BACK_OFF=0` and `BACK_OFF=1`; in every configuration with that witness switched on we observed 0 signal runs (0/40, 0/40, 0/56 and 0/56 with the first witness, 0/60 and 0/60 with a lighter witness, and 0/1 in each of two single pilot cells).
[S-04] We have **not** determined whether this is (1) a property of the `mocc` implementation, (2) an artifact of our trace hooks (a recording or attribution mistake), or (3) a violation of a modelling assumption in our checker; these three branches remain open.
[S-05] We are **not** proposing a fix, and we have not run upstream `master` itself — all runs used commits on our fork branch; [S-14] below gives a static comparison of `cc/mocc/transaction.cc` at the base fork commit `e9e477ca` against our local `master` mirror, and the instrumentation, diagnostic and light-witness variants built on top of it are described separately.
[S-06] We report this so that the maintainers are aware of the observation and can judge whether it deserves attention; we are happy to share raw traces and the checker's output on request.

## Scope of this report

[S-07] This report contains observations and their limits only: counts of runs in which our checker reported a G2 signal, the exact build and workload conditions, the shape of the reported cycles, a static reading of the code that is *consistent* with the observation, and the things we did not establish.
[S-08] It does not claim a root cause, does not propose a code change, does not claim that the 0-signal configurations are free of the phenomenon, and does not treat non-significant differences between configurations as evidence of equivalence.
[S-09] None of the numbers below are performance numbers: every run used a trace-enabled (`CCBENCH_TRACE=1`) build, and commit counts mentioned below are only a measure of how many commits the checker examined.

## Environment and build

### Code under test

[S-10] Fork: `thawk105/ccbench`, lineage `izanagi-trace`, whose base is upstream tag `v1.1.0` (commit `d9ffac18`).
[S-11] Producer commits that showed the signal: `058d0c4e5f237d88ec1c2ebe0739113d82906e47` (trace hooks only, no witness code) and `e9e477ca1b55348ab4530de0b1cf663ce4555290` (tip of our hook branch `izanagi-t1943-mocc-g2-readfrom-witness`, trace hooks plus the witness code, which is a no-op unless an environment variable enables it at run time).
[S-12] The lighter witness used in the last experiment is commit `5b02546fcd7b0302c8c92b6e05957541c9660902` (branch `izanagi-t1943-mocc-g2-witlight`, parent `e9e477ca`, touches `cc/mocc/transaction.cc` only, +26/−6); the measured source for that experiment was `e9e477ca` plus the instrumentation patch plus a patch reproducing that commit's change, and it matches `e9e477ca` + that commit + the instrumentation patch byte-for-byte apart from `#line` lines.
[S-13] At the time of writing, these hook branches had not been pushed to GitHub; the submodule pin our project currently uses for ccbench is `511c9538e4e8efa54b45cda62e72389ed3b706ec` (`v1.1.0-126-g511c9538`), and `e9e477ca` is a candidate pin that has not been adopted.
[S-14] Difference from upstream `master`: comparing `cc/mocc/transaction.cc` at `e9e477ca` against our local mirror of `origin/master` (`50c7946d`, "Merge pull request #118", committed 2026-06-28; the mirror's fetch date is not recorded) gives 141 insertions and 0 deletions, and every non-blank inserted line lies inside an `#if TRACE` … `#endif` block; we have not checked later `master` commits and we have not run `master` itself.
[S-15] Terminology used below: an *arm* is one build/runtime configuration, and a *block* is a group of runs executed on one node (in the rotated experiments each block interleaves all arms). An additional instrumentation patch (`instr-mocc-lock-coverage.patch`, SHA-256 `e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48`, +65/−0 in `cc/mocc/transaction.cc`, again `#if TRACE`-guarded) was applied in most arms; it adds lock-coverage and write-set-permutation assertions that our checker uses to certify a zero-cycle run; in the one direct comparison we have (same producer, witness off) the checker reported 3/40 signal runs without the patch and 2/40 with it (one-sided Fisher p = 0.500), which does not establish that the patch has no effect.

### Build and workload

[S-16] Baseline configure defines, with the `BACK_OFF=1` substitution described next: `-DCMAKE_BUILD_TYPE=Release -DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=0 -DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0` (the two later experiments also passed `-DCCBENCH_CCACHE=OFF`); `RWLOCK` is defined unconditionally for `mocc` by `cc/mocc/CMakeLists.txt` on this branch.
[S-17] The `BACK_OFF=1` arms replaced only `-DCCBENCH_BACK_OFF=1` (one earlier `BACK_OFF=1` block additionally carried `-DCCBENCH_KEY_SORT=0 -DCCBENCH_TEMPERATURE_RESET_OPT=1`, which are the defaults on this branch).
[S-18] Toolchain: `/usr/bin/x86_64-linux-gnu-gcc-11` / `g++-11`; index: Masstree (default).
[S-19] Workload (identical in every run): `ycsb` with `-ycsb_tuple_num=10000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3`.
[S-20] Hardware: compute nodes of a shared HPC cluster, one node per block, 48 worker threads; the CPU model is not recorded in the artifacts we cite, and we did not verify that a node was ours alone beyond the runner's own single-tenancy check.
[S-21] Each run is one 3-second `ycsb` execution followed by an offline pass of the checker over that run's per-thread trace; binaries were rebuilt per node (so binary hashes differ between nodes while the source hash, defines and toolchain match).

### What the trace records and what the checker assumes

[S-22] The trace hooks (all under `#if TRACE`) write, per worker thread, one `C` line per commit in `writePhase()` (`txid thid epoch tid |read_set| |write_set|`), one `R` line per read-set element with the tidword `(epoch, tid)` the transaction captured for that record at read time, and one `W` line per write-set element with the commit tidword that `writePhase()` is about to store; these lines are emitted after the commit tidword is computed and before the record bodies and tidwords are actually updated.
[S-23] The checker builds Adya's Direct Serialization Graph over committed transactions — ww (a wrote V, b wrote the next version), wr (a wrote V, b read V), rw (a read V, b wrote the version immediately after V) — and reports any cycle; a cycle containing at least one rw edge is labelled G2.
[S-24] Its modelling assumption is that, per key, the recorded tidwords form a total order that identifies the producing transaction uniquely (it also checks that the trace has no duplicate versions, no orphan reads, no missing txids and, with the instrumentation patch, no lock-coverage or write-set-permutation violations; all of these were zero in every signal run).
[S-25] Branch (3) above — "a violation of a modelling assumption in our checker" — refers to this per-key version-order assumption; we have not proven it for `mocc` from the code, and the checker cannot distinguish that case from branches (1) and (2) using the trace alone.

### The "witness" instrumentation

[S-26] To find out where a reader's value came from, we added an optional "payload-lineage witness": when enabled by an environment variable, each UPDATE stamps the writer's txid into the first 8 bytes of the record body, and the reader side logs which txid's stamp it observed, so that a reported rw edge can be checked against the stamp the reader actually saw: `supported` means the producer inferred from the recorded read version agrees with the producer decoded from the payload stamp, `contradicted` means they disagree.
[S-27] The first version of the witness writes its log line immediately after the tidword store and before `unlockCLL()`, i.e. inside the write-lock hold; the lighter version moves that post-store output after the unlock, but decoding, a possible abort and a push onto a vector remain between the tidword store and the unlock, and the initial or capacity-growing reservation of that vector also occurs while write locks are held — the timing effect of either version was not measured.
[S-28] In every run with either witness enabled the checker reported no cycle, so the witness never produced a single `supported` / `contradicted` verdict; **the origin of the value read in a signal run has therefore never been confirmed by this mechanism** (see "What we did not establish").

## Observations

### A. Witness off, `BACK_OFF=0` — the signal reproduces

| Date (2026) | Producer | Instrumentation patch | Witness | Signal runs / runs | 95% Clopper–Pearson |
|---|---|---|---|---|---|
| 08-26 | `058d0c4e` | no | code absent | **5 / 42** | [0.040, 0.256] |
| 09-18 | `058d0c4e` | no | code absent | **2 / 40** | [0.006, 0.169] |
| 09-18 | `e9e477ca` | no | off | **3 / 40** | [0.016, 0.204] |
| 09-18 | `e9e477ca` | yes | off | **2 / 40** | [0.006, 0.169] |
| 09-18 | `e9e477ca` | yes | off | **5 / 120** | [0.014, 0.095] |
| 09-19 | `e9e477ca` + light witness code | yes | off | **1 / 60** | [0.0004, 0.089] |

[S-29] The first row is the original observation (42 independent submissions of one run each); the four 09-18 rows come from two later experiments in which arms were rotated round-robin inside each node; the last row is from the lighter-witness experiment with the witness disabled at run time.
[S-30] For the two September 18 rows without the instrumentation patch, the current checker labels zero-cycle runs `indeterminate` rather than `certified` (the patch's assertions are required for its `certified` status), so their denominators are all runs, not certified runs; the counts of signal runs are unaffected, and these labels concern individual trace checks, not any certification of `mocc`.
[S-31] The rates are per fixed 3-second run, not per commit; commit counts per run differ between arms (in the first 09-18 experiment the per-run averages were about 797,000 for `058d0c4e`, 785,000 and 711,000 for the two witness-off `e9e477ca` arms, and 542,000 for the witness-on arm; in the 09-19 experiment the witness-on arms averaged 0.86 and 0.85 of their witness-off counterparts), so these are not comparisons at equal exposure.

### B. Witness on, `BACK_OFF=0` — no signal observed

| Date (2026) | Producer | Instrumentation patch | Witness | Signal runs / runs | 95% Clopper–Pearson |
|---|---|---|---|---|---|
| 08-28 | `e9e477ca` | no | first version, on | 0 / 1 | — |
| 09-18 | `e9e477ca` | yes | first version, on | **0 / 40** | [0, 0.088] |
| 09-18 | `e9e477ca` + diagnostic patch (see D) | yes | first version, on | 0 / 40 | [0, 0.088] |
| 09-18 | `e9e477ca` | yes | first version, on (pilot cell) | 0 / 1 | — |
| 09-19 | `e9e477ca` + light witness code | yes | light version, on | **0 / 60** | [0, 0.060] |

[S-32] The direct on/off comparisons available are 0/40 vs 2/40 (first witness, same node blocks, one-sided Fisher p = 0.247) and 0/60 vs 1/60 (light witness, same node blocks, p = 0.500); pooling the three witness-off arms of the 09-18 experiment (7/120) against the witness-on arm (0/40) gives p = 0.128; none of these is significant, and the design power of the light-witness comparison under its own assumptions was 0.105.
[S-33] These zeros are compatible with an observer effect of the witness (for the first witness, its output inside the write-lock hold lengthens the interval between the tidword store and the unlock — see the static reading below), but also with sampling variability, i.e. not having drawn a rare event in 40 or 60 runs; the data do not distinguish those explanations, and we do not claim that the witness suppresses the phenomenon.

### C. `BACK_OFF=1`

| Date (2026) | Producer | Witness | Signal runs / runs | 95% Clopper–Pearson |
|---|---|---|---|---|
| 09-18 | `e9e477ca` (+ instrumentation) | first version, on | 0 / 56 | [0, 0.064] |
| 09-18 | `e9e477ca` + diagnostic patch | first version, on | 0 / 56 | [0, 0.064] |
| 09-18 | `e9e477ca` (+ instrumentation) | off | **2 / 120** | [0.002, 0.059] |
| 09-19 | `e9e477ca` + light witness code | light version, on | 0 / 60 | [0, 0.060] |
| 09-19 | `e9e477ca` + light witness code | off | **1 / 60** | [0.0004, 0.089] |

[S-34] With the witness off, the signal also appeared under `BACK_OFF=1` (2/120 and 1/60); against the witness-off `BACK_OFF=0` arm of the same experiment (5/120) the one-sided Fisher p is 0.223, so this sample does not detect a lower rate under backoff, and it does not show equality either.
[S-35] The two `BACK_OFF=1` signal runs of the 09-18 experiment both fell in the same node block (2/30 there, 0/30 in each of the other three); we do not draw a node or time effect from that.

### D. A diagnostic intervention (observation only; not a proposed fix)

[S-36] To see whether the two code locations named in the static reading below are *involved*, we ran one arm with a small diagnostic patch (SHA-256 `8a25bd0a5687437269c720cb34a4b26024a6f1f119adf1c16281d455b9ecaa1d`, 37 lines) that adds two extra rejection conditions: on the cold (OCC) read path, abort with `ERROR_LOCK_FAILED` if the record's rwlock counter reads `W_LOCKED`; and in `validation()`, after the rwlock counter check of a read-set element, re-read the tidword and abort if its epoch or tid changed.
[S-37] Witness off, `BACK_OFF=0`, same node blocks as the 5/120 arm: the diagnostic arm reported **0 / 120** (Clopper–Pearson upper bound 0.030); one-sided Fisher against 5/120 gives p = 0.030 uncorrected for the two comparisons pre-registered in that experiment.
[S-38] We read this only as "in this fixed setting, an intervention that bundles those two extra rejections is consistent with a lower signal rate"; the two changes were bundled, so their individual contributions are not separated, the p value is a single uncorrected comparison, and 0/120 does not show a rate of zero.
[S-39] **We are not proposing this patch as a fix**: it narrows the accepted set of executions rather than explaining the observation, it does not tell branches (1), (2) and (3) apart, and it was never run with the witness on and a signal present.

### E. Shape of the 21 reported cycles

[S-40] All 21 signal runs (5 + 7 + 7 + 2 across the four experiments) report `total_cycles = 1`, phenomenon G2, cycle length 2, both edges of type rw only, and zero on every integrity counter (orphan reads, duplicate versions, duplicate or missing txids, write-version mismatch, framing, lock-coverage, write-intent and permutation violations); across the archived checker outputs the summary flag `integrity.clean` is `true` in 16 runs and `false` in 5 — the 16 include the five August 26 runs, which had no instrumentation patch and were checked by the checker version of that date (before the patch's evidence became a requirement on 2026-09-03), and the 5 `false` are the runs from the two uninstrumented arms of the first September 18 experiment, checked by the current version, whose `clean` requires the patch's evidence to be present in the source in addition to zero counters; these archived flags are therefore not a uniform re-evaluation under one checker version, and in the 5 `false` runs the flag does not indicate a detected violation.
[S-41] In all 21 the two transactions' commit versions are in the same epoch; the tids differ by 1 in 20 pairs and by 2 in one pair (run B2/069 of the second September 18 experiment); where thread ids were checked (all 5 of 08-26, all 7 of the first 09-18 experiment, and one pair of the second) the two transactions ran on different threads.
[S-42] Every key involved has a small id (the largest is `0x55` in a table of 10,000 records; `0x0`, `0x1` and `0x2` recur), i.e. the keys that are hottest under zipf 0.9; two of the 21 cycles (one on 08-26, one on 09-19) have one edge justified by two keys, the rest have one key per edge.
[S-43] The raw per-thread traces of all 21 signal runs are preserved (48 files per run) with SHA-256 manifests; the traces of non-signal runs were not kept.

## What we did not establish

[S-44] **No root cause.** The signal runs show that our checker's graph contains a cycle; they do not show which of (1) the `mocc` implementation, (2) our trace hooks, or (3) our checker's per-key version-order assumption is responsible, and the shape of the cycles (which is the same under every producer) does not discriminate between them.
[S-45] **The origin of the read value in a signal run was never confirmed.** The witness mechanism built for that purpose never fired on a signal run, because every run with the witness enabled reported no cycle; so we cannot say whether the reader in a signal run saw the pre-image or the post-image body.
[S-46] **Zero counts are not absence.** The two-sided 95% Clopper–Pearson upper bounds for 0/40, 0/56 and 0/60 are 0.088, 0.064 and 0.060 respectively; these samples do not establish a zero signal rate.
[S-47] **Non-significant differences are not equivalence.** The witness on/off, backoff, and diagnostic comparisons all rest on small counts; only the diagnostic comparison reaches p < 0.05 and only uncorrected.
[S-48] **Not tested on `master`.** All producers are fork commits; we have only the static diff statement in [S-14] about how `cc/mocc/transaction.cc` relates to `master`.
[S-49] **Not a performance measurement.** Everything here is a `CCBENCH_TRACE=1` build with trace output on every commit.
[S-50] **Statistics are descriptive.** Clopper–Pearson intervals and Fisher tests assume independent, identically distributed runs; runs on the same node, rotation order and time-of-day effects are not modelled, and no multiple-comparison correction was applied across experiments.
[S-51] **Binaries differ per node**, and we did not verify instruction-level identity between builds; identity is at the level of source hash, configure defines and toolchain.

## A static reading of the code (consistent with the observation; not a demonstrated mechanism)

[S-52] Line numbers refer to `cc/mocc/transaction.cc` at `e9e477ca`; we verified them against that file, and we have not observed the execution order described here in any run.
[S-53] *Cold-record read path* (`read_internal()`, lines 316–356): the reader loads the tidword (line 320), spins while `rwlock_.ldAcqCounter() == W_LOCKED` (line 322), checks `absent`, copies the body, re-loads the tidword (line 350) and accepts if the two tidwords are equal; lock state is not part of the tidword, so a writer that acquires the write lock and starts `memcpy` (line 1169) after the counter check but stores the new tidword (line 1195) only after the reader's second load leaves the reader with the old tidword — we call this ordering (i), and the code does not exclude it.
[S-54] *Validation* (`validation()`, lines 1008–1039): for each read-set element the transaction first compares the stored tidword with the current one (loads at line 1010) and then, separately, checks that the rwlock counter is not `W_LOCKED` unless the record is in the transaction's own write set (`searchWriteSet(...) == nullptr`, lines 1024–1025); if a writer's tidword store (line 1195) and its `unlockCLL()` (line 1207) both fall between those two loads, both checks pass — ordering (ii), which the code also does not exclude.
[S-55] The following is a conditional reconstruction of our internal example, stated from its explicit operation specification: W reads the old value of y and writes only x; R reads the old value of x and writes only y, with x ≠ y; both reads finish before the other transaction updates the corresponding record; both records are read on the cold (OCC) path with empty read-lock lists (RLL); W locks x and validates y before R locks y; R then locks y and validates x, its version check preceding W's tidword store while its counter check follows W's store and unlock — under these assumptions, ordering (ii) could allow both transactions to commit without a body inconsistency, with both edges of the resulting cycle rw. We have not demonstrated this ordering in any reported signal run.
[S-56] Ordering (i) alone cannot reach commit without (ii), because validation would then see either a changed tidword or `W_LOCKED`.
[S-57] The "same epoch, tid + 1" pattern seen in 20 of the 21 reported cycles is, in this interleaving, a consequence of `max_rset_` (line 1038) and the commit-tid rule (max + 1), not a necessity, and agreement in shape is not evidence for this reading over branches (2) and (3).
[S-58] The observer-effect hypothesis for the witness rests on the same reading: the first witness inserts its output between line 1195 and line 1207, lengthening exactly the interval that R's two loads must straddle in (ii).
[S-59] We did not measure that interval, and we did not observe (i) or (ii) directly; the diagnostic patch in section D targets these two locations, which is why its result is reported, and why it still does not identify the mechanism.

## Reproduction materials (available on request)

[S-60] Per-run records (build bindings, configure defines, source-file SHA-256, binary SHA-256, workload argv, checker JSON), the checker's JSON for each signal run, the raw per-thread traces of the 21 signal runs with manifests, the diagnostic patch and the light-witness commit as a self-contained git bundle.
[S-61] The checker (Python, Adya DSG construction and cycle search) is in our project repository; the experiment runners are preserved in our experiment archives, with textual copies in the repository, and are available with the reproduction materials; the trace format is documented in the fork's `include/trace.hh`.

## What we are not asking for

[S-62] We are not asking for a code change, a review of a patch, or confirmation of a bug; we are reporting an observation that we could not resolve on our side so that the maintainers know it exists.
[S-63] If the maintainers know of a reason why the per-key version-order assumption in [S-24] does not hold for `mocc`, or of a known behaviour of the RWLOCK validation path that explains the shape in section E, that would tell us which branch to pursue; if not, no action is expected.
