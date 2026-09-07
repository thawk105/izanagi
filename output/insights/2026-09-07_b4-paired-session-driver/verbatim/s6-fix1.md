## 実装した内容

- [floor_pair_driver.py:2589](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4paired-fix1/orchestrator/campaign/floor_pair_driver.py:2589): finalizer の旧 `後続 role` を `後続 side session` へ変更。判定挙動は不変。
- [test_floor_pair_driver.py:490](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4paired-fix1/orchestrator/tests/test_floor_pair_driver.py:490): v3 構造で schema だけが literal `floor-pair-spec/v2` の spec を拒否する負例を追加。
- [test_floor_pair_driver.py:508](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4paired-fix1/orchestrator/tests/test_floor_pair_driver.py:508): schema だけが literal `floor-pair-plan/v1` の plan を canonical plan 検査が拒否する負例を追加。
- [test_floor_pair_driver.py:1713](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4paired-fix1/orchestrator/tests/test_floor_pair_driver.py:1713): 旧テスト名の `remaining_roles` を `remaining_side_session` へ変更。
- [test_floor_pair_driver.py:2316](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4paired-fix1/orchestrator/tests/test_floor_pair_driver.py:2316): v3 構造で schema だけが literal `floor-pair-window/v2` の window を拒否する負例を追加。
- summary は [floor_pair_driver.py:3005](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4paired-fix1/orchestrator/campaign/floor_pair_driver.py:3005) で生成するだけで loader・再検証器がなく、既存の literal 出力 pin は [test_floor_pair_driver.py:2158](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4paired-fix1/orchestrator/tests/test_floor_pair_driver.py:2158) にあるため、拒否負例は追加していない。
- dataclass、必須 field path、schema 定数は変更しておらず、関連 meta-test の更新は不要。

## 実走した検査

- pytest nodeid: なし。射影外の test runner を使わず、親の実走へ委ねた。
- 次の nodeid は実装済み・未実走:
  - `orchestrator/tests/test_floor_pair_driver.py::test_loader_rejects_v2_schema_on_v3_shaped_spec`
  - `orchestrator/tests/test_floor_pair_driver.py::test_plan_v1_schema_is_rejected_with_current_plan_shape`
  - `orchestrator/tests/test_floor_pair_driver.py::test_finalizer_rejects_v2_schema_on_v3_shaped_window`
  - `orchestrator/tests/test_floor_pair_driver.py::test_measure_exception_runs_post_probe_drops_remaining_side_session_and_continues`
- 対象 2 ファイルを `ast.parse` し、構文検査は成功。
- 対象 2 ファイルへの `git diff --check` は成功。`git diff --name-only` も指定された 2 ファイルだけ。

## 赤の内訳

無い。ただし pytest は未実走のため、suite 全体の赤なしは未確認。

## 波及可能性

- `load_frozen_spec`、plan exact 検査、window finalizer の受理・拒否集合は変更しておらず、所有外 caller への実行時波及はない。
- finalizer の旧エラー文言を完全一致で検査する外部 consumer があれば文字列変更の影響を受ける。
- 旧 nodeid `test_measure_exception_runs_post_probe_drops_remaining_roles_and_continues` を直接指定する外部ジョブは追随が必要。
- 共有 fixture `_document_only`、`_prepare_spec`、`_run_production` は利用のみで変更していない。
- summary consumer と成果物 schema には変更なし。

## 総括

real 所見 2 件に限定して指定 2 ファイルを修正した。  
旧 schema の負例は spec・plan・window に追加し、summary は検証入口がないため追加していない。  
既存期待値、受理・拒否挙動、測定 callable 経路は変更していない。  
commit は作成していない。  
pytest は実装済み・未実走で、親による実走が必要。