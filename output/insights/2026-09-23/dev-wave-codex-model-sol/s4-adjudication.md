# 段 4 裁定とプラン v2 (軽量版、段 2・3 なし)

入力: brief.md。段 2・3 は DW-C00 の軽量版で省略 (設計択一なし・正しさ防壁非該当・受理集合は model 名の値だけ)。

## plan v2

1. 親: docs/dev-wave/operations.md DW-O01 の `<model>` 行を `` `<model>`: 全段 `gpt-6-sol` (段 3 の 2 本も同じ)。 `` に置換し、wave branch へ docs-only commit (role=manager)。この commit を実装子 worktree の base とする。
2. Codex author 1 本 (所有 = tools/check_docs.py、orchestrator/tests/test_check_docs.py、orchestrator/tests/test_dev_wave_launch_authority.py):
   - check_docs.py の `DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL` の slug を `gpt-6-sol` へ。
   - test_check_docs.py の `test_dev_wave_model_pin_rejects_dw_o01_authority_drift` の置換元 `"gpt-6-astra"` を `"gpt-6-sol"` へ (置換先 `gpt-5.6-terra` は据え置き。drift 注入が実在することは既存の `assert changed != text` が担保)。`test_dev_wave_model_pin_contract_is_time_invariant` の期待 literal を sol へ。
   - test_dev_wave_launch_authority.py の 2 か所の期待 model を `"gpt-6-sol"` へ。
   - 既存テストの期待値変更はユーザー裁定 (model 移行) の直接の帰結であり、DW-S05-B の「期待値を変えない」の例外として本裁定で許可する。他の期待値・assert は変えない。
3. 親: 焦点走 (上記 2 test file) を dispatch、変異 matrix、受入全走、記録 (decisions / worklog fragment)、land。

## gate の禁止と正例 (署名)

- 拒否: DW-O01 の model 行が `gpt-6-sol` 以外 (例 `gpt-6-astra`) のとき check_docs は `DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING` を出す。
- 通る正例: 現行 operations.md (sol 行 1 件) で check_docs rc=0「違反なし」。

## 変異事前登録 (実装後に単一理由性を確認し、probe で期待 node の完全集合を集めてから final)

| id | category | 位置 | 置換 | 期待 |
|---|---|---|---|---|
| m0 | positive | tools/check_docs.py の literal 定義直後 | コメント 1 行追加 (等価) | SURVIVED |
| m1 | negative | tools/check_docs.py `DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL` | `gpt-6-sol` → `gpt-6-astra` (実装だけ旧 model に戻る) | KILLED: 少なくとも test_dev_wave_model_pin_contract_is_time_invariant と実 repo を check する test (test_dev_wave_model_pins_accept_current_docs_contract 等) |
| m2 | negative | docs/dev-wave/operations.md DW-O01 行 | `gpt-6-sol` → `gpt-6-astra` (権威だけ旧 model に戻る) | KILLED: 少なくとも test_all_stage_models_match_independent_docs_cross_check、test_snapshot_and_derive_current_authority_positive、実 repo の check_docs test |

runner = `tools/run_tests.py --force-dispatch orchestrator/tests/test_check_docs.py orchestrator/tests/test_dev_wave_launch_authority.py -q -rf`。
期待 node の完全集合は、全件 SURVIVED 期待の初回 dispatch probe で観測して登録する (DW-M08)。
m2 は docs の変異だが、test が docs 権威を pin していることの検出力を示すために登録する (受理集合は model 名の値)。
