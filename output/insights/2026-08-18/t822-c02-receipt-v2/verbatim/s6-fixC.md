## 追加した対照

[orchestrator/tests/test_s8c_acceptance_receipt_v2.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:369) に追加した。

Nodeid:

`orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_trial_report_arm_execution_mismatch_is_rejected_after_reference_hashes_match`

report の `arm_execution.content_digest_sha256` だけを変更し、変更後 bytes から受領証の `report_sha256` を再計算している。期待する例外は次の全文へ `^...$` で固定した。

`[receipt-arm-binding] trial report arm_execution differs from receipt`

## 単一理由性の論証

- 受領証の `arm_execution` は変更していないため、`expected_arm_execution` は元の正しい値のまま。
- report の descriptor、cell、launch binding、trial metadata は変更していない。
- descriptor digest は受領証由来の値と照合されるため、descriptor 再導出検査を通る。
- report の変更後 bytes から `report_sha256` を更新して受領証を書き直しており、参照 hash 検査を通る。
- journal とその hash は不変であり、run-start は受領証由来の期待値と一致する。
- binding digest も受領証内の正しい三つ組から再導出できる。

したがって通常実装では、report echo の比較だけが拒否理由になる。

変異 `if False and report.get("arm_execution") != expected_arm_execution:` を適用すると、この唯一の拒否が消える。後続検査は report echo を再検査せず、受領証由来の binding digest と journal を検査するため全て通る。その結果 `pytest.raises` が「例外なし」で失敗し、この対照は確実に赤くなる。

## 検査と対照の棚卸し

[s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/campaign/s8c_acceptance_receipt.py) の対象 `_fail` 全22出現を棚卸しした。「有」は当該理由を直接期待する負の対照を示す。

| 行 | 拒否理由 | 直接対照 |
|---:|---|---|
| 273 | `{label}.input_schema_version differs` | 無 |
| 437 | `v2 trials are not the closed six arm cells` | 無 |
| 445 | `{holdout} content digests are not pairwise distinct` | 有: `test_pairwise_collision_is_rejected_after_binding_recalculation` |
| 623 | `{label} root is not an object` | 無 |
| 629 | `attempt journal is not newline terminated` | 無 |
| 634 | `attempt journal line {index} is not an object` | 無 |
| 655 | `v2 trial arm_execution is absent` | 無。ただし公開 parser が v2 trial の非 `None` を先に保証する防御分岐 |
| 660 | `trial report trial_id differs from receipt` | 無 |
| 662 | `trial report measurement_head differs from receipt` | 無 |
| 667 | `trial report status differs from receipt` | 無 |
| 671 | `origin_terminal_projection presence differs from receipt` | 無 |
| 679 | `origin_terminal_projection is not an object` | 無 |
| 686 | `origin_terminal_projection differs from receipt` | 有: `test_origin_terminal_projection_is_retained_and_reverified` |
| 699 | `trial report arm cell differs from receipt` | 無 |
| 703 | `trial report cells are not a zero/one list` | 無 |
| 709 | `trial report cell descriptor is absent` | 無 |
| 712 | `trial report descriptor cell is not bound` | 無 |
| 718 | `cell descriptor content digest differs from receipt` | 有: `test_receipt_digest_divergence_is_attributed_to_report_descriptor` |
| 723 | `trial report arm_execution differs from receipt` | 有: 今回追加した対照 |
| 734 | `arm binding digest differs from receipt inputs` | 有: `test_binding_digest_is_rederived_from_self_consistent_three_way_claim` |
| 741 | `attempt journal run-start is not unique` | 無 |
| 743 | `run-start arm_execution differs from report and receipt` | 有: `test_run_start_mismatch_is_rejected_after_reference_hashes_match` |

今回追加分以外にも、直接の負の対照がない出現は16件ある。そのうち行655は公開入力から到達しない防御分岐で、残る15件は構成可能な直接対照が未整備。ただし指定された1件以外はscope外のため編集していない。

## 総括

- 変更ファイル: テスト1ファイルのみ
- production/docs変更: なし
- commit: なし
- `git diff --check`: 成功
- `check_codex_agents.py`: 成功
- `check_docs.py`: 成功
- 追加nodeid: **実装済み・未実走**
  - `tools/run_tests.py` で単独走を試みたが、Pegasus dispatch の `qstat -Q` preflight失敗により `rc=16`。テスト本体は実行されていない。