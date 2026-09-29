## 総括

担当範囲の F1・F2・F3・F6・F9・F10・F13・F16 と M3 強化を実装しました。score の固定 endpoint 照合、auditor veto の preview と拒否記録、部分 retry の初期点履歴、単位終了時の系列確定を修正しています。commit は作成していません。

## 変更 file と行数

- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/campaign/p3_s4_loop_policy.py): +75 / −63 行
- [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/tests/test_p3_s4_loop_policy.py): +109 行

## 実装した interface

`load_proposal_file(..., preview_auditor=False)` を追加しました。対照の `--preview-diff` と `--record-reject` は `{coder}` と `{coder, auditor}` を受け、auditor があれば既存の `policy_gate(..., write=False)` で判定します。record-reject の `a` は `open_opportunity(ledger)`、単位の未終端 slot は `series_state(ledger)` から取得します。`run_contrast_unit` は最後に `close_series_if_done(ledger)` を呼びます。seed slot にも `critic_digest` を記録します。

## テスト

追加した検査は、基点 commit と既定 campaign identity の比較、proposal 改変時の rc=2 と `slot-start` 不在、固定 endpoint の identity、seed 部分 retry の履歴、auditor veto です。`py_compile` と `git diff --check` は通過しました。`python3 tools/run_tests.py orchestrator/tests/test_p3_s4_loop_policy.py` は **qstat 事前確認の失敗で rc=16** となり、テスト本体は未実走です。

## 所有外への波及

台帳側の `open_opportunity`・`close_series_if_done` と、launcher が書く `endpoint-fixed` の直下 field に依存します。round と report は今回の所有外です。inventory 対象を検索し、既存の caller 数を変える修正はありません。

## 変異の位置

| 変異 | 壊す位置 | 検出する test |
|---|---|---|
| M1 | `p3_s4_loop_policy.py:94` | `test_contrast_initial_points_and_machine_arm_provenance` |
| M2 | `p3_s4_loop_policy.py:608` | `test_contrast_cfg_keeps_default_identity_and_separates_attempts` |
| M3 | `p3_s4_loop_policy.py:190` | `test_contrast_none_preserves_base_commit_identity` |
| M4 | `p3_s4_loop_policy.py:253` | `test_machine_origin_can_write_only_after_shared_gate` |
| M5 | `p3_s4_loop_policy.py:767` | `test_contrast_unit_rejects_changed_proposal_before_slot_start` |
| M6 | `p3_s4_loop_pegasus.sh:252` | `test_policy_contrast_requires_exclusive_absolute_unit` |

## 未解決・報告して止めたこと

台帳側 API の統合後に実走が必要です。今回のテストランナーは dispatch infrastructure failure により起動できていません。