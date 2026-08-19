## 修正

- site 解決を [`p3_autonomous_workload_trial.py:3638`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:3638) で一度だけ行い、build gate と予約 gate に同一値を渡すよう修正。flag 推定を削除。
- malformed `__notes__` を新しい list に差し替え、元例外を再送出するよう [`p3_autonomous_workload_trial.py:3469`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/p3_autonomous_workload_trial.py:3469) を修正。
- `restart_forbidden` の consumer を [`trial_registry.py:1868`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/campaign/trial_registry.py:1868) の `record_trial_start_once` に追加。`reject_started_trial` の durable start-row 拒否は維持。
- compute/OTHER site、note 病的ケース、restart 拒否、初回起動の対照を追加・補正。docs・契約・record は未変更。

## 呼び出し回数の影響

- [`test_public_run_trial_scope_preserves_t276_worker_gate`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/tests/test_p3_autonomous_workload_trial.py:2331) の `iter((OTHER, PEGASUS_COMPUTE))` は、do_build=True で従来どおり「preflight → `_run_workload`」の2回・同順序。
- `_assert_workload_campaign_uses_site_contract`（722行、利用テスト858/873行）は `_run_workload` 直接呼出しのため新規 preflight 呼出しなし。
- `test_clean_dry_pass_still_admitted_on_pegasus` は別 module の `run_one_iteration`、`test_campaign.py` の iterator は `_resolve_site` であり影響なし。
- 新規 no-build 対照は compute が1回、OTHER が preflight＋worker の2回を確認。
- 予約拒否既存テストには実 site=PEGASUS_COMPUTE の pin を追加したが、期待値は反転していない。

## 恒真化していないことの確認

- `test_indeterminate_note_fallback_replaces_non_list_and_reraises_original` は `__notes__="not-a-list"`、`add_note=None`、両 bookkeeping failure を注入し、同一の元例外が `raise cause` されることを確認する。
- `record_trial_start_once` の新対照は、flag 後なら `[lifecycle-restart-forbidden]` になることを検査する。consumer がなければ durable append の `[lifecycle-start-once]` となるため検出可能。
- 空 ledger での `reject_started_trial` → 初回 start も確認し、正当な初回起動の過剰拒否がないことを確認する。

## 実走

- `python3 -m py_compile`（本体・変更テスト4ファイル）: 成功。
- `git diff --check`: 成功。
- 焦点 nodeid 走は `tools/run_tests.py` 経由で実行を試みたが、`qstat -Q preflight rc=1`、`Pegasus dispatch infrastructure failure`（rc=16）で child pytest 未起動。したがって以下は実装済み・未実走。

  `test_run_trial_reservation_rejects_each_live_binding_mismatch_before_launch`、`test_reservation_error_stays_outside_run_trial_crash_terminalizer`、`test_run_trial_no_build_uses_actual_compute_site_for_reservation`、`test_run_trial_no_build_other_site_is_not_overrejected_by_transport_opt_in`、`test_public_run_trial_scope_preserves_t276_worker_gate`、2つの既存 terminal failure 対照、note 対照、`test_registered_admission_and_lifecycle_are_non_certifying_and_start_once`。

## 停止・未達

- Pegasus dispatch 基盤の認証/キュー観測障害により pytest の緑確認は未達。
- commit は作成していない。変更はコードとテストの4ファイルのみ。

## 総括

3件の must-fix を独立に実装した。  
予約 gate は実 site を共有する。  
病的 note でも元例外を失わない。  
`restart_forbidden` は実際の start consumer で拒否する。