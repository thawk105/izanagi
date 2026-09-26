## 所見

1. **must-fix — 計測の有効対を作れない。** 裁定は A を clean main、B を実装差分付きの tree とし、collection 一致を要求する（[s4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s4-ruling.md:47)）。しかし B の commit は新規 test node を追加している（[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1128)）。分析器は固定 collection との不一致、または A/B 間の不一致で走・対を無効にする（[t2273lc_ab_analyze.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:90)、[同ファイル](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:428)）。**放置すると 3 有効対に達せず、land 判定は不能。** 系列投入前に、B 固有の node 1 件を明示した計測裁定の erratum と、その差だけを許す厳密な照合を用意する。

2. **should — M5 の kill は事前登録した単一理由に帰属しない。** 全件 copytree 変異は ignored file と除外対象 receipt の両方を写す（[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1142)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1148)）。最初の集合 assert は両方の混入で失敗しうる（[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1185)）。**放置すると「ignored file が原因で kill」とは証明できない。** ignored file の不在を先に単独で assert するか、変異表に複数理由と記す。

3. **should — shard 配置差が性能差に混ざりうる。** 分析器は shard 別 selected 一致を算出するが（[t2273lc_ab_analyze.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:197)）、有効性判定には使わない（[同ファイル](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:430)）。**放置すると W₀ の変化を実装効果として過大または過小評価しうる。** 所見 1 の erratum で、共通 node の shard 配置差を判定条件にするか、差が出た対を個別に解釈する規則を固定する。

## 変異表

| 変異 | kill node・観測点 | 単一理由か |
|---|---|---|
| M1 | 既存の実 builder test、`visible_copy.call_count == builder.call_count`（[test file](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1120)） | **はい。** fixture が module global を `_bases` に差し替え、その後 fork するため、子の builder も同じ instance を参照する（[test file](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1062)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1123)）。 |
| M2 | 新規 test、2 回目の tracked bytes（[test file](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1183)） | はい。source 変更後の直接複製を検出する。 |
| M3 | 新規 test、実関数の呼出し回数（[test file](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1179)） | はい。再生成なら 2 回になる。 |
| M4 | 新規 test、snapshot との mtime（[test file](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1187)） | はい。後続の direct との比較も同じ mtime 理由。 |
| M5 | 新規 test、regular file 集合（[test file](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1185)） | **いいえ。** ignored file と receipt が同時に混入する。 |

## 総括

**NO-GO（現行の計測系列）。** A/B の collection 一致条件が実装差分と両立せず、測定判定に到達できない。  
共有写しの lock・marker・残骸処理、別 key の builder、単独走分岐、および既存の `complete.json` glob・consumer AST・全件性検査への明白な破綻は静的検査では見つからなかった。新規 test の source と書込先は tmp 配下である。  
実測テストは行っていない。親の焦点走に加え、計測条件の erratum と M5 の帰属修正が必要。