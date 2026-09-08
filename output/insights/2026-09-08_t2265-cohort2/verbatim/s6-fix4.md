## 更新内容

- patch C: `4c04caa89244d74aa542a204bed0befae45b13616113cc5d734570c3aae7d2ff`
- patch stack: `14ac8f00798d1b317854643e133c0b58543106e9c693f5c556f8b13edb591082`

解析器とテストの literal のみ更新しました。

## 導出方法

[producer](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix4/tools/pegasus/probes/t2187_adaptive_const_probe.py:806) の `_patch_stack_identity` を確認しました。

- patch C は `patches/cicada-adaptive-counterfactual.patch` の実 bytes を `sha256sum` で算出。
- stack は `izanagi-patch-stack/v1\n` の後に A、B、C の順で `相対path sha256\n` を連結し、その UTF-8 bytes を SHA-256 化。
- A=`9b2153...f54b`、B=`f3fe6b...f824`、C=`4c04ca...d2ff` から上記集約値を得ました。

## 実走結果

対象 nodeid:

`orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py::test_cohort2_literal_pins_are_independent_of_fixture_helpers`

`tools/run_tests.py` 経由で試行しましたが、`qstat -Q` preflight が失敗し `rc=16`、`child_started=false` でした。したがって、実装済み・未実走です。

`git diff --check` は成功しています。

## pin の維持

[解析器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix4/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:33) と [テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix4/orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py:521) の固定 64 桁 literal だけを置換しました。実行時計算への変更、任意値の受理、比較処理の変更はありません。

## 総括

直した内容: patch C と patch stack の literal SHA-256 を現物準拠へ更新。  
実走結果: runner の dispatch infrastructure failure により実装済み・未実走。  
残っている赤: 指定 nodeid は未実走のため、赤解消は未確認。