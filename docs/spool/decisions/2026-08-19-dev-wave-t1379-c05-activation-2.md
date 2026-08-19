---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t1379-c05-activation
seq: 2
---

## {{D:c05-authority-deferred}}. C05 activation は§5 記入・schedule artifact commit を含めず、権威の実体配線完了まで scope 外とする

**決定:** 8c 条件5 (C05) の activation (契約反転・`_MACHINE_EVALUATORS` 登録・
`DECIDER_VERSION` bump・凍結世代発行) は実施するが、§5 `master_seed` の記入と
`output/s8c-preregistration/schedule.v1.json` の commit は本改訂単位に含めず、
`run_trial -> load_schedule -> verify_schedule -> consume_schedule -> launch` の配線と
権威 (`WORKLOADS`/`ROLE_FILES`/`ROLE_CONTRACTS`/`GATING_SPEC`/descriptor binding) の
実体供給が完了する別 wave (T-1380) まで scope 外として保留する。

**理由:**
- §5 の記入規約は「seed だけを先に固定しない」と定める。`master_seed` を記入するなら
  同じ改訂単位で `schedule.v1.json` の bytes も確定させる必要があるが、その bytes は
  authority の digest に依存する。
- production 側の権威解決関数 (`p3_autonomous_workload_trial.py` の
  `_load_s8c_schedule_authority` 相当) は現状明示的に unavailable を送出し、意味の
  定義された本物の authority をこの wave の scope 内だけで構築する経路が無い。
  `p3_autonomous_workload_trial.py` の `WORKLOADS` 定数は探索用 (ycsb-a/b/c) であり、
  正式な H1/H2 (rr80/rr20、`s8b_holdout_freeze.py` 定義) とも一致しない。
- テスト fixture 相当の暫定 authority で `schedule.v1.json` を正式 artifact として commit
  すると、将来 T-1380 が本物の authority を使った際に artifact bytes が再現不能になり、
  「seed だけ先に固定した」ことと実質的に同じ結果になる。
- `_evaluate_c05` は静的到達可能性検査であり、artifact/authority の中身の正当性を
  問わない。§5・artifact を保留しても、C05 の activation 自体 (契約反転・registry 登録・
  DECIDER_VERSION bump・凍結世代発行) は独立に完結できる。

**却下した選択肢:**
- 暫定 authority (test helper 相当の 18-key mapping) を明示的に provisional と
  marking した上で 6 項目全部を実装する — 機械的に暫定性を拒否できる仕組みが無く、
  正式 artifact として repo に残ってしまう。段3 の敵対相談 2 本が独立に不採用を推奨した。
- T-1380 の配線・権威供給を本 wave の scope へ先取りして含める — D529 が定める
  不可分の改訂単位 (契約反転・registry 登録・DECIDER_VERSION bump・凍結世代発行) を
  大きく超える新設作業になり、規律5 (段階導入・盛らない) に反する。
