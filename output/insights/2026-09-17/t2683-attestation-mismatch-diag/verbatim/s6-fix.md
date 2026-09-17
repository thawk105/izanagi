## 総括

N1〜N3 を指定の test file だけに実装しました。**実装済み・未実走**です。構文確認は成功し、既存 assertion・期待値は変更していません（assertion の AST 比較で確認）。driver・docs・他 file の編集、commit、git 状態変更は行っていません。

## 変更一覧

対象: [orchestrator/tests/test_t126_qualification_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_t126_qualification_driver.py)

| 変更した test 関数 | file 内の行・変更内容 |
|---|---|
| `test_t2683_run_attest_closure_wires_child_helper_and_rejection_message` | **611行**: 子分岐 body 直下。**619行**: 子 helper の exact keyword。**624行**: 非ゼロ分岐 body 直下。**631行**: message helper の exact keyword。既存の個数 assertion は609・610行に保持。 |
| `test_t2683_parent_message_unreadable_sidecar_is_best_effort` | **540行**: `monkeypatch.context()`。544行の wrapper は `.mismatch.json` のみ失敗させ、他は元の `Path.exists` へ委譲。550行の既存 assertion・期待値は不変。 |
| `test_t2683_mismatch_preserves_all_comparison_rows` | **401行**: 読取り前に `assert sidecar.is_file()` を追加。 |
| `test_t2683_empty_comparisons_writes_rejected_sidecar` | **454行**: 読取り前に `assert sidecar.is_file()` を追加。 |

## 実走

- 保存後の `ast.parse` による構文確認: **成功**。
- 指定の pytest コマンド: **PreToolUse hook が Pegasus ログインノードでの実行を拒否**。親による計算ノード再走が必要です。
- 既存ログの65 passedは修正前の結果です。

## M10/M11 の赤根拠

- **M10**: 固定文字列は `ast.Call` ではないため `raises` が空となり、610行の `assert len(raises) == 1` が赤になります。
- **M11**: インライン復帰で `_run_attestation_child` を引数とする exit 呼出しが消え、609行の `assert len(exits) == 1` が赤になります。

いずれも静的根拠であり、変異実走結果ではありません。

## 懸念

修正後の pytest・変異実走は未確認です。受理集合、揮発 payload の期待値、fixture の hash には触れていません。
