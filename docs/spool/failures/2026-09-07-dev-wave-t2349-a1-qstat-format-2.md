---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2349-a1-qstat-format
seq: 2
---

## supersede 追記

- F852 **supersede: 2026-09-07** — 恒久対応が指していた [T-2349] を実施した。`_observe_qstat_visibility` は共有 leaf `orchestrator/scheduler_nqsv.py` の `target_bound_qstat_state_result` で state を正規化し、canonical が `QUE` / `RUN` のときだけ受理する。execution queue 行は広い候補 regex で stdout 全体から数え、ちょうど 1 本かつ唯一の `Request ID:` 行より後方であることを確かめてから厳格書式 (`@nqsv`、`(Execution Queue)`、`gen_S`) で検証する。終端側は受理を広げず、実機の可視出力が終端と判定されないことを試験で固定し、消失枝は A-2 と同じ 1 行 fullmatch と対象 ID 束縛で締めた。実機 `qstat -f` の逐語 4 種 (Running / Pre-running / Queued / 不存在) を `orchestrator/tests/fixtures/paper_story_a1/` に fixture 化し、正例・負例は production 関数を通す。変異 11/11 KILLED (SURVIVED 0)。記録は `output/insights/2026-09-07_t2349-a1-qstat-format/`。
