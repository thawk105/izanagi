実装済み・未実走です。production の受理集合・検査順は変更していません。

変更箇所:

- [test_trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t470-t327-wiring/orchestrator/tests/test_trial_registry.py:620)
  - 欠落 trial 用 lifecycle fixture に registered `launch_admission` を追加。
  - report-count / trial-set 検査へ到達可能に修正。
- [test_s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t470-t327-wiring/orchestrator/tests/test_s8c_acceptance_receipt.py:194)
  - m13[lifecycle] の変異 anchor を、committed lifecycle prefix を維持する未commit append部分へ再照準。
  - `[receipt-history]` を通過し、`[receipt-reference-prefix]` が単独発火する入力へ分離。

静的照合では、F1〜F12の他の負例に新たな前段遮蔽は見つかりませんでした。F1はcompletenessを明示的に迂回、F4/F6/F9/F10はdirect APIまたはspyで対象gateを分離、F7/F8は正例、F11/F12は構造検査です。F2/F3/F5のlifecycle競合のみ今回解消しました。

検査:

- `python3 -m py_compile`：指定production/test 4ファイル成功
- `git diff --check`：成功
- pytest：Pegasusログインノードのため未実走
- 実走nodeid：0件
- commit / stage：未実施

所有外への波及可能性:

- `_write_acceptance_lifecycle` を共有するtrial registry負例は、欠落・foreign report時にfixture例外ではなくproduction gateまで進むようになります。
- m13の変更は`lifecycle` parameterだけに限定され、manifest・registry・report・journalケースには影響しません。
- production API・reason code・受理集合への波及はありません。

## 総括

| nodeid | 状態 | 対応 |
|---|---|---|
| `test_redundant_six_report_argument_count_defense_is_required` | partial（実装済み・未実走） | fallback admissionを追加し`[report-count]`へ到達 |
| `test_m20_report_trial_set_rejects_duplicate_or_foreign[duplicate]` | partial（実装済み・未実走） | 欠落trialのlifecycleをregistered admission付きで構築 |
| `test_m20_report_trial_set_rejects_duplicate_or_foreign[foreign]` | partial（実装済み・未実走） | foreign化後もfixture生成を完遂し`[trial-set]`へ到達 |
| `test_m13_reference_bytes_are_rehashed_not_self_compared[lifecycle]` | partial（実装済み・未実走） | append部分へ変異anchorを再照準 |

- 単一理由性の修正方針：選択肢2の「m13[lifecycle]の変異anchor再照準」を採用。履歴矛盾は既存の独立負例、prefix矛盾は今回のm13負例が担当します。
- 残る赤の見込み：静的には指定4件を解消見込みです。pytest未実走のため、計算ノード実測までは潜在的な赤を否定しません。