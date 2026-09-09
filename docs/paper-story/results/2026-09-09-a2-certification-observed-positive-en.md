# A-2 formal certification results section — the attempt re-taken under the correct identity is `observed-positive` (English)

**This is not submission text.** It is a writer-facing controlled draft, bound to primary sources, for the
results section and tables of the paper. It is not the machine-projected evidence report defined by D12
(the numbers are transcribed from primary sources, and the prose contains the writer's judgement).

**This is the English rendering of `results/2026-09-07-a2-certification-observed-positive.md`.**
It adds no factual proposition to that draft. Every number, identifier, and timestamp below was read again
from the primary sources listed in §4 and matched against that draft's tables.

**This document is a frozen artifact of the `results/` series.** It is not updated after it is written.
The rule is stated in the "results 系列" section of `docs/paper-story/README.md`.

**This draft does not revise any existing draft in the series.** The series is append-only: the
2026-09-04 draft and the 2026-09-07 `reject` draft both remain unchanged, byte for byte. What those
record are facts about attempt `t2022-20260828c`, a **different attempt**. What this draft records are
facts about attempt `t2364-20260907b`, a **new attempt**, and it does not invalidate the earlier ones
(Absolute Discipline 7).

---

## 0. Positioning — what this writes, and what it does not

- **What it writes:** for the 4 cells of attempt `t2364-20260907b` (2026-09-07), the
  `cells[].performance.median_tps`, `effects`, and `status` held by the authoritative bytes; the
  conditions that actually took effect in those cells; what the status does and does not license;
  the tables; and the list of limitations.
- **What it does not write:** withdrawal of the earlier attempt's verdict (Discipline 7); a claim about
  the cause of the difference from the earlier series; a declaration that the research succeeded or
  failed (D12); any claim about read-heavy (not yet obtained, tracked as A-6); or a claim that this
  effect transfers to other workloads or other machines.
- **`observed-positive` is a status of the protocol, not a declaration of research success.** The
  protocol asks whether the median throughput of the adopted cell exceeds that of the stock cell in the
  same workload, as the logical conjunction over 2 workloads, and the answer was that it did.

---

## 1. What differs from the earlier attempt — the conditions being measured are different

The earlier attempt `t2022-20260828c` ran on a **stock CCBench tree to which the patch had not been
applied**. `BACKOFF_FIXED`, which supplies the static quantity, did appear in the cmake argv, but the
pinned CCBench has no matching option definition, so it never became a build condition; the only
condition difference that actually took effect was the enable/disable of the built-in backoff
(D1645, a recurrence of F707).

This attempt runs under the driver defined by D1644, which computes each cell's identity from a
**`src_token` bound to the pin plus the patch**. The driver evaluates `source_digest.resolve_evidence`
per cell against the patched, isolated tree, builds the expected value from that token, and requires
fail-closed that **stock cells be `stock` and adopted cells be non-`stock`**.

The primary-source `certification.json` records the following for all 4 cells.

| cell | role | `src_token` | `source_binding_status` |
|---|---|---|---|
| `rr5-stock` | stock | `stock` | `bound` |
| `rr5-fixed10` | adopted | `955b452a332d…` (non-`stock`) | `bound` |
| `rr50-stock` | stock | `stock` | `bound` |
| `rr50-fixed5` | adopted | `21def77c944b…` (non-`stock`) | `bound` |

**Therefore, for this attempt, the record licenses the statement that the adopted cells were built from
the tree with the patch applied.** That this could not be stated for the earlier attempt was exactly the
reason for the correction in D1645.

---

## 2. Results

### 2.1 Performance — in two independent campaigns, adopted exceeded stock

| workload | cell | role | requested genome | median (tps) | mean (tps) | 95% CI half-width | coefficient of variation | abort rate |
|---|---|---|---|---|---|---|---|---|
| rr5 (write-heavy) | `rr5-stock` | stock | `BACKOFF_FIXED=-1`, `BACK_OFF=0` | 2,438,295 | 2,462,838.6 | 99,765.6 | 0.0326 | 0.7845 |
| rr5 (write-heavy) | `rr5-fixed10` | adopted | `BACKOFF_FIXED=10`, `BACK_OFF=1` | 3,987,794 | 4,004,505.0 | 45,583.8 | 0.0092 | 0.3833 |
| rr50 (balanced) | `rr50-stock` | stock | `BACKOFF_FIXED=-1`, `BACK_OFF=0` | 3,756,230 | 3,808,422.0 | 138,475.2 | 0.0293 | 0.6850 |
| rr50 (balanced) | `rr50-fixed5` | adopted | `BACKOFF_FIXED=5`, `BACK_OFF=1` | 4,297,929 | 4,302,525.0 | 58,456.7 | 0.0109 | 0.4615 |

The effects on the median ratio are **+63.5485% for rr5 and +14.4213% for rr50**. The figure generator
recomputes these two independently from the primary sources and records that they agree with the
authoritative values (`authority_matches` is `true` for both entries of `effect_crosschecks`).

The outer status is the logical conjunction over the 2 workloads, and it is **`observed-positive`**.

**The confidence intervals of the means describe the samples; they are not confidence intervals for the
effects, for the decision, or for the medians.** This artifact makes no significance decision.

### 2.2 Correctness — all 4 cells certified, in separate runs

Correctness comes from separate trace-enabled runs. All 4 cells are `certified`, with 1 legacy
repetition observed and 5 repetitions observed on the performance side. **This is not a certification of
performance.** Under L01 this evidence is limited to point-key traces. Under D1257 the argv on the
correctness side is not independently recorded by the existing pipeline.

### 2.3 Measurement conditions

48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s,
5 repetitions, CCBench pin `511c953`, no perf, performance from a trace-disabled build.

The two campaigns are independent requests.

| workload | request | host | recorded time (UTC) |
|---|---|---|---|
| rr5 | `981476.nqsv` | `bnode077` | 2026-09-07T12:12:55.607184+00:00 |
| rr50 | `981477.nqsv` | `bnode085` | 2026-09-07T12:12:55.388302+00:00 |

The source commit on the izanagi side is `31ec382a7841e188e46f93e8de4261c964facfb2`.

---

## 3. Limitations (what this result does not say)

- **It says nothing about read-heavy.** That has not been obtained; it is tracked as A-6.
- **It does not claim transfer to other workloads, other machines, or other CCBench pins.** What was
  measured is these 2 workloads, this pin, and this machine only.
- **It does not withdraw the earlier attempt's verdict.** The earlier attempt is a different fact,
  measured under different conditions (a tree without the patch), and it remains on the record
  (Absolute Discipline 7). The two must not be read as a before-and-after comparison.
- **About the condition gate, only the record can be stated.** The raw manifest binds, for all 4 cells,
  canonical condition-admission records that report `use_class="paper"` and `admitted=true`, but the original
  supply and meaning records are not retained in the artifact. The statement is therefore not "the gate
  was applied and passed" but "receipts recording that are bound".
- **The abort rate is a descriptive leading indicator.** It is one aggregate value per cell; it carries
  no confidence interval and asserts no causal mechanism.
- **The vertical axes of the two workloads are scaled independently.** Panel heights must not be
  compared.

---

## 4. Primary sources

- Certification artifacts: `output/insights/2026-09-07_t2364-paper-story-a2-certification/`
  (`certification.json` is `paper-story-a2-certification-result/v4`;
  `raw-manifest.json` is `paper-story-a2-full-raw-manifest/v4`)
- Figure: `docs/paper-story/figures/fig6_a2_certification_observed_positive.png` / `.pdf` /
  `.provenance.json`
- Durable authority for the measurement: the WAL and raw cells of attempt `t2364-20260907b`
  (12 entries of root-relative path plus SHA-256 are recorded in `external_inputs` of the figure's
  provenance)
- The blocker that prevented the re-take, and its fix: commit `31ec382a7`
