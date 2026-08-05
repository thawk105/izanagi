実装済み・未実走です。pytest の緑および `closed` は申告しません。

変更内容:

- [trigger_gate_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/trigger_gate_binding.py:98)
  - mask 順の正準述語 index を構築。
  - `mask_for_canonical_predicate()` を公開。
  - exact `str`、外側 whitespace、統一拒否診断を維持。
- [s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:89)
  - module 読み込み時に mask 0〜31 の name→mask index を構築。
  - emitter 名重複と `ident_all` 衝突を fail-closed 化。
  - `ident_all` を mask 31 alias として登録。
  - exact `str` 型を membership より先に検査。
  - 生成層と schema 層の双方へ束縛検査を接続。
  - `expected_names` は mask 順の固定 tuple。
- テストでは全32 mask、mask 31 の両名、外側 whitespace、型偽装、欠落名、両層の coordinated tamper、診断専用完全文言を追加しました。

実行済み検査:

- `python3 -m py_compile` — 変更4ファイル
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 禁止2 source と凍結 JSON の `git diff --exit-code`

すべて成功しました。pytest nodeid は `pegasus02` ログインノードのため実走していません。新設テストおよび meta-test `test_plain_runner_coverage.py` も親の計算ノード実測が必要です。commit / `git add` は実行していません。

所有外への診断到達可能性は `s1_verify_extime_calibration`、`s1_measurement_freeze`、`s1_direct_comparison`、`s8b_oracle_driver`、`t080_freeze_migration` と、それらの consumer test です。共有 fixture の `s1_expected_goldens.py`、凍結 JSON、`test_reflux_ir` の既存 golden は未変更です。`s8b_holdout_freeze` と downstream replay は本検査を直接通らず、裁定どおり scope 外です。

## 総括

- name↔predicate mask 束縛を生成層・schema 層へ実装した。
- M1〜M7 の kill 経路をテストへ組み込んだ。
- 静的検査は成功し、禁止ファイルと凍結 bytes は変更していない。
- pytest と meta-test は未実走であり、親の計算ノード検査が残る。
- 現行 official 受理集合は空のため、本検査は引き続き dormant gate である。