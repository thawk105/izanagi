# 段 1 brief — [T-1396] 判定器 C04 の到達対象へ reject_started_trial を足す

## scope

判定器 `orchestrator/campaign/s8c_preregistration_evidence.py` の `_evaluate_c04` が見る
reachable target を 2 件から 3 件へ増やし、契約 JSON
`s8c_preregistration_evidence_contract.v1.json` の condition 4 が要求する
`run_trial preflight -> reject_started_trial` を実際に検査させる。
併せて期待集合 `orchestrator/tests/test_s8c_preregistration_predicates.py` に
「3 件目が欠けたら C04 が UNSATISFIED になる」負例を足す。編集面はこの 2 file だけ。

## 確定済みユーザー裁定

- D1292 (2026-08-29 /rulings 全件、推奨どおり裁定)。実装待ち。
- 本題の実装だけを行う。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外 (`DW-G05`)。

## 実測した前提 (brief 前)

- 契約は 3 件、判定器は 2 件。現状の C04 はほぼ恒真である (D1292 の理由と一致)。
- production の呼び先は実在し到達可能である。
  `p3_autonomous_workload_trial.py:4602` の `run_trial` → 同 :1430
  `_reject_registered_lifecycle_duplicate` → 同 :1432 `trial_registry.reject_started_trial`
  (定義は `trial_registry.py:4796`)。
- read-only probe で、3 件目を足しても現行 main (`0e02169b0`) の C04 は
  `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のままである。
  したがって `current_commit_snapshot` の C04 期待値は変わらない。
- `s8c_preregistration_evidence.py` は `campaign_lock.py` の contract loader / enforcement
  source 一覧に載る HEAD blob 束縛 file である。

## 不変条件

- (I1) 規律 2 — 判定を緩める向きの変更をしない。C04 の受理集合は**狭くなる**方向にだけ動く。
- (I2) 既存テストの期待値を変えない。ただし共有 fixture `TOKEN_ONLY_C04` は 3 件目の
  呼び先を持つ形へ拡張してよい (契約が要求する形へ揃えるため。緩和ではない)。
- (I3) 正例は実体を名指しする。「`reject_started_trial` という名前の関数がある」ではなく、
  現行 repo の `run_trial` から `trial_registry.reject_started_trial` へ到達することを
  `current_commit_snapshot` 系の実 repo 検査で示す。両層 stub で通る緑にしない (F649)。
- (I4) 負例は 3 件目だけを落とす。1・2 件目は残したまま C04 が UNSATISFIED
  (`crash-policy-cell-partial`) になることを示す。既存 `nc_c04_partial_crash_survives` は
  1 件目を落とす負例なので、これとは別に足す。
- (I5) 契約 JSON は編集しない。判定器を契約へ揃えるのであって逆ではない。

## (P1) 親の provisional 裁定 — 攻撃対象

- (P1-a) 3 件目の対象は `(registry_path, "reject_started_trial")` の 1 つとし、
  `_functions(registry)` 側の存在検査も `forbid_trial_restart` と同じ形で足す。
  reason code は既存の `crash-policy-cell-partial` / `restart-guard-absent` を再利用し
  新設しない。
- (P1-b) `TOKEN_ONLY_C04` の拡張形は「preflight で `reject_started_trial()` を呼ぶ
  `run_trial` 冒頭」とする。契約文言の "run_trial preflight" に合わせる。
- (P1-c) 実 repo の到達検査は既存の `current_commit_snapshot` 経路で足り、新しい実 repo
  検査を新設しない。

## 成果物の形

- `s8c_preregistration_evidence.py` の `_evaluate_c04` に 1 target 追加 + registry 側の存在検査。
- `test_s8c_preregistration_predicates.py` に負例 1 件 (と必要なら `TOKEN_ONLY_C04` の拡張)。
- 同じ commit に入れる。docs 記録は spool fragment。

## 並列分割方針

編集面が 2 file、変更行が十数行の一枚岩なので段 5 の実装子は 1 単位とする。
`s8c_preregistration_evidence.py` は HEAD blob 束縛なので、段 6 の子を起動する前に
親が統合 commit する。焦点走も統合 commit 後に行う (未 commit だと contract-loader-drift で偽赤)。
