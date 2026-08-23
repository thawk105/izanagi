---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-flaky-quarantine
seq: 1
---

## 新規

### {{F:merge-narrowing-misread}}. 別 wave の認証済み除外を絞り込みと誤認し、自分の stale 検査を毎回無効化していた [合成崩れ] [恒真ゲート]

- 事象: 本 wave が新設した flaky registry の「完全 collection か」判定が、main で先に着地した
  別 wave の恒久除外機構 (`orchestrator/test_selection_contract.py` の `SANCTIONED_EXCLUSIONS`)
  が runner へ渡す正当な `--ignore` を、ユーザーによる絞り込みと誤認していた。
  結果、**受入全走のたびに stale registry 検査が無効化される**。registry が腐っても検出されない。
- 根本原因: 両 wave が `orchestrator/tests/conftest.py` を独立に変更し、git の自動 merge が
  競合なしで通った。main 側は `_is_complete_growth_hold_collection` を
  認証済み runner token を差し引く形へ変えていたが、本 wave 側の sibling 判定は
  同じ `_COLLECTION_NARROWING_OPTIONS` を参照したまま差し引きを持たなかった。
  **textual に競合しないことは意味的に正しいことを保証しない。**
- 恒久対応: {{D:flaky-quarantine-node-id-registry}} の合成監査手順。両親が同じ実装面ファイルを
  変更した merge では Codex `role=author` の合成監査を行い、`DW-O17` の
  「実装面 path が両親と異なれば Codex role=author へ」を満たす。本件はその監査が
  実際に検出した。path 正規化と narrowing 判定は共通 helper
  (`_normalize_collection_path` / `_collection_narrowing_is_runner_owned`) へ寄せ、
  growth 側と flaky 側が同一の判定を通る。
- 再発検知: 監査が置いた局所 probe (通常全走 / 認証済み runner 除外付き / ユーザー `--ignore` 付き /
  contract fallback の各条件で growth・flaky の判定が一致すること)。

## 再発

### F57

- **再発: 2026-08-23** — 本エントリが 2026-07-30 から保留していた原因帰属が確定し、
  **隔離ではなく修理で閉じた。** [T-190] が着地させた失敗 artifact 保存により、
  受入全走の失敗 receipt が読めるようになった結果である。
  観測 (wave `dev-wave-t1472-provider-init-indeterminate` の受入 attempt8、
  tip `8cecaed08f0a151f8ff47ba437082ef0619627bf`、PBS request `938829.nqsv`、
  hostname `bnode010`、`60 failed, 14246 passed, 96 skipped in 399.38s`):
  `stop_reason='wall_clock_admission_bound_s'`、
  `receipt_limits={'wall_clock_admission_bound_s': Decimal('3.0')}`、
  `receipt_actuals={'wall_clock_s': Decimal('3.267585068')}`、
  `loadavg=(39.037109375, 18.74853515625, 7.84326171875)`。
  子プロセス側の指標は全て正常 (`codex_exit_code=0` / `validator_rc=0` /
  `evidence_status='complete'` / `metering_status='complete'` /
  `process_group_residual=0` / `termination_verified=True`)。
  **壊れていたのは被験体ではなく被験体を測る締切の側だった。**
  `orchestrator/tests/test_codex_worker_launch.py:1554` の helper `_base_command` は
  `max_wall: str = "3"` を既定に持ち、これを `--wall-clock-admission-bound-s` として渡す。
  これは**テストを速くするための fixture 値であって production の gate ではない**
  (production 既定は 3600 秒)。144 test を分類すると 7 件が wall 予算そのものを検査し、
  22 件が小さい wall を渡しながら**別の limit** (`max_model_calls`、`max_attempts`、
  metering、evidence 等) を検査していた。高負荷では wall が先に発火して
  `stop_reason` の assertion が壊れる。これが本エントリの正体である。
  対応: wall 以外を検査している 20 node の `max_wall` を、
  `_run_launcher_subprocess` の `timeout=10` より大きい値へ上げた。
  ハングの安全網はその 10 秒 timeout が引き続き担うため検出力を失わない。
  wall 自体を検査する 7 件と、意図的に極小値を渡す 2 件は変更していない。
  修理後の実測は request `939036.nqsv` で `170 passed in 6.55s`、rc=0。
  件数が走行ごとに揺れた点 (別 wave の観測で 15 件 → 10 件) も、
  負荷で発火するかどうかが決まるという説明と整合する。
  **なお「差分 約 1.94 秒 = 起動・計測・後始末の固定費」という読みは 1 走行 1 サンプルからの
  推論であり、確定していない。** 固定費が負荷に比例するのか特定の段に集中するのかは分離できていない。

## supersede 追記

- F57 **supersede: 2026-08-23** — 「pytest tmp は終了時に失われ失敗時 receipt / stop reason を保存していないため 3 秒超過そのものを根本原因と断定しない」という未確定は解消した。上記 2026-08-23 の再発項が receipt 逐語で断定を与えている。
- F373 **supersede: 2026-08-23** — 恒久対応「焦点走・受入走を起動する script で env -u FORCE_COLOR -u COLORTERM を前置する」は運用規律であり 3 度目の再発を防げなかったため、テスト側を環境非依存にする実装へ置き換えた (subprocess へ --color=no と NO_COLOR=1 を渡す)。同一 tree・同一コマンド・同一 ambient 環境で修理前 rc=1、修理後 rc=0 を実測している。
