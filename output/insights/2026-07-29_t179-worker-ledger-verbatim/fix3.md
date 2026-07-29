fix3 の5件はすべて `closed` です。docs・`tools/check_codex_output.py` は未変更、commit / git add / push は行っていません。

### 対応表

| # | 状態 | 実装・検証 |
|---|---|---|
| 1 | `closed` | reasoning 欠落を0扱い、4 fieldのみ必須化。[ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:147)、正例 [test](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:377) |
| 2 | `closed` | 4必須 field の負値を `malformed_usage` 化。[ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:166)、[test](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:392) |
| 3 | `closed` | `段6` / `fix[2]` / `後の` 間の半角・全角空白を許容。[ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:45)、[test](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:861) |
| 4 | `closed` | model/effort 不一致を `inconsistent_turn_context` 化。object直下も読取。[ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:269)、[test](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:799) |
| 5 | `closed` | 全meta収集後、いずれかのcwd一致でfile選択。[ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:719)、契約コメント [ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:733)、[tests](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:709) |

meta不明fileは、cwd filter時には帰属不能として選外に置き、そのfileの壊れ行を無関係waveへ波及させません。filterなしでは従来どおり malformed/missing meta を報告します。

### 追加・変更テスト

追加nodeid:

- `test_legacy_usage_without_reasoning_and_null_info_passes_strict`
- `test_negative_required_usage_fields_fail_closed`
- `test_later_matching_meta_selects_file_and_keeps_its_issues`
- `test_meta_unknown_file_is_ignored_only_when_cwd_filter_cannot_select_it`
- `test_inconsistent_turn_context_fails_closed`
- `test_object_level_turn_context_model_and_effort_are_read`

変更nodeid:

- `test_each_usage_field_is_required` — 必須4 field、4 parameter
- `test_stage_rules_follow_wave_stage_not_role_words` — 指定4形＋全角空白形を追加

追加fixture:

- [legacy_usage.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/legacy_usage.json:1)
- [negative_usage.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/negative_usage.json:1)
- [turn_context_inconsistent.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/turn_context_inconsistent.json:1)
- [turn_context_object_level.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/turn_context_object_level.json:1)
- [meta_order.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/meta_order.json:1)
- [meta_unknown.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/meta_unknown.json:1)

### 実走結果

- `orchestrator/tests/test_codex_worker_ledger.py`: **79 passed / 0 failed**、0.48秒
- `orchestrator/tests/test_check_codex_output.py`: **18 passed / 0 failed**、0.14秒
- 両ファイル統合走: **97 passed / 0 failed**
- F42 meta-test 2ファイル: **6 passed / 0 failed**
- `tools/check_codex_agents.py`: rc=0
- `tools/check_docs.py`: rc=0、違反なし

赤はありません。fixture内で期待した strict rc=2 はすべてテスト成功として検証済みです。

実626 rolloutに対する再構成も strict rc=0、issues空でした。

- sessions: **10**
- model_calls: **434**
- cli_reported: **2,757,982**
- plan **224,150**
- consult **392,185**
- author **171,736**
- review **544,553**
- fix **605,734**
- focus **819,624**

既存8パターンの `plan/consult/author/fix/fix/review/focus/focus` は `test_stage_rules_follow_wave_stage_not_role_words` が逐件固定しています。加えて `test_stage_rules_keep_fix2_author_in_fix_and_focus_specific` が `段6の fix2 implementation author → fix` を固定しています。

## 総括

5件すべて閉じました。健全な旧usage形は受理しつつ、負値・turn context不一致・選択対象file内の破損に対する検出力は落としていません。親が確認すべき点は、追加6 fixtureの統合、実rollout再走値、meta不明fileをfilter時に選外とする明示契約です。外部コードcallerは静的検索で存在せず、波及面は当該CLI・テスト・将来のT-180〜T-184 consumerに限定されます。