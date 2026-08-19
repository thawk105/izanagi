# 変更点

- [s8c_preregistration.py:874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:874): exact schema の位置付けを docstring に追記。
- [test_s8c_preregistration_invariant.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/tests/test_s8c_preregistration_invariant.py:608): 生きた doc bytes を `n=1` の canonical JSON へ 1 回だけ置換する positive control を追加。`H1.n` / `n-range` と `FILLED` を exact assert。

# 実走結果

pytest は実走していない。`git diff --check` と AST 構文確認は成功。

# 残る懸念

親による pytest・変異検査・受入全走が必要。commit は作成していない。

# 波及の静的列挙

production parser の既存判定・`Section5Finding` は変更なし。docs/output は未変更。所有外の既存 core test 差分には触れていない。

## 総括

F1/F2 の指定修正を完了。  
positive control は置換空振りを検出する。  
単一違反軸と canonical key 順を維持している。  
実装済み・未実走。