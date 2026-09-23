## 1. 着手前の現行挙動

`_check_dev_wave_model_pins` は DW-O01 の可視 top-level に固定の model 権威行をちょうど 1 件要求し、その行以外の可視本文にある `gpt-` slug も同じ `DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING` にします。`snapshot_authority` は V2 行の `model` を読み、`derive_launch` が全段の model に使います。

base commit の docs は sol、変更前の `check_docs` literal は astra です。したがって model 検査の期待 finding 集合は `{DEV_WAVE_DW_O01_MODEL_AUTHORITY_FINDING}` です。実 repo を検査するテストと launch authority の二つの固定期待値テストも赤になる見込みです。一方、drift テストの合成 fixture は旧 literal から astra 行を作るため、変更前も置換が成立します。

## 2. 変更箇所

指定された 5 行だけを astra から sol に変更しました。

- [check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/sol-unit-a/tools/check_docs.py:368): 権威 literal。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/sol-unit-a/orchestrator/tests/test_check_docs.py:9126): drift の置換元。同ファイル 9412 行の固定期待 literal。
- [test_dev_wave_launch_authority.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/sol-unit-a/orchestrator/tests/test_dev_wave_launch_authority.py:261): 全段 model の集合。同ファイル 377 行の docs 独立照合リスト。

## 3. 静的検査

`git diff --check` は rc=0、3 ファイルの `ast.parse` は rc=0 でした。`rg -n -c 'gpt-6-astra'` は rc=1 で、所有 3 ファイルに残存はありません。差分と `git status` は指定の 3 ファイル、5 行のみです。

## 4. 制約 meta-test

workers・DW-O01 外・command の slug 禁止テスト、DW-O01 内の余分な slug と権威行の重複・不可視化を検出するテスト、`DEV_WAVE_MODEL_SLUG_RE` の期待値を確認しました。これらの述語と assert は未変更です。合成 fixture は literal を参照するため sol 行へ追随し、drift 注入元もそれに合わせて変更しています。V2 の不正 slug を拒否する launch authority テストにも変更はありません。

## 5. 段 4 の変異

- **m0:** 等価なコメント追加なので SURVIVED の見込み。
- **m1:** literal だけ astra に戻すと `test_dev_wave_model_pin_contract_is_time_invariant` と `test_dev_wave_model_pins_accept_current_docs_contract` が落とす見込み。
- **m2:** docs 行だけ astra に戻すと `test_all_stage_models_match_independent_docs_cross_check`、`test_snapshot_and_derive_current_authority_positive`、実 repo の check_docs テストが落とす見込み。

## 6. 所有外への波及

`tools/codex_worker_launch.py` は `snapshot_authority` と `derive_launch` を呼び、`test_codex_worker_launch.py` は導出値を receipt や argv と照合します。model の固定値は見つからず、docs 由来値へ追随します。`test_s8c_preregistration_invariant.py` は `check_docs.main()` の consumer です。growth hold・inventory は実 repo 検査の nodeid を参照しますが、nodeid は変わりません。共有 fixture の編集はありません。

## 7. 実走

**実装済み・未実走です。** 指示どおりテストも commit も実行していません。親の焦点走候補は `orchestrator/tests/test_check_docs.py`、`orchestrator/tests/test_dev_wave_launch_authority.py`、consumer の `orchestrator/tests/test_codex_worker_launch.py` です。

## 総括

sol への移行に必要な指定 5 行を変更し、余分な差分と所有 3 ファイル内の astra 残存がないことを静的に確認しました。