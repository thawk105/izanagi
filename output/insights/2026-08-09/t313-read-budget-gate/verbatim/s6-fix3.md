## 総括

[orchestrator/tests/test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:2656) のみ修正しました。

- `all_sections_on_non_self_path`: 段 9 の `| 段 9 |U| … DW-O23 |` 全行を anchor 化。
- `range_marker_inside_annotation`: 段 1 の `| 段 1 |U| … DW-G01〜DW-G05 … |` 全行を anchor 化。
- `ascii_tilde_inside_url`: 同じ段 1 全行を anchor 化。
- 共通 helper で anchor と行内 fragment の `count == 1` を維持し、変更前後の差分が意図した1行だけであること、書込み後の内容一致も assert。
- finding の既存期待値は変更していません。前二者は段1 U edge 不一致、非 self-path は参照 cell grammar 不一致を引き続き要求します。
- production の [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py) は触っていません。したがって受理集合は不変で、変更は負例の変異注入方法だけです。
- docs、commit、stage、stash、branch 操作は行っていません。status 上の docs / production 差分は作業開始前から存在する親側変更です。

検査結果:

- `python3 -B tools/check_docs.py`: rc=0、`check_docs: 違反なし`
- `git diff --check -- orchestrator/tests/test_check_docs.py tools/check_docs.py`: rc=0
- pytest 3本: **実装済み・未実走**。この sandbox では緑を主張せず、親の計算ノード実走待ちです。