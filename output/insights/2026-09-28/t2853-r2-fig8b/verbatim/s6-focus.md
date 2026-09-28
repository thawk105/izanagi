## 前巡所見の対応表

| ID | 判定 | 根拠 |
|---|---|---|
| A-F1 | closed | provenance 2 本の `reproduction.command` は実在する R2 出力親の wrapper を指す。`argv` と command は一致し、`r2-single` の引数は各 R2 group と報告ディレクトリを選ぶ。wrapper の SHA-256 も [README §5.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/README.md:240) と一致した。静的確認であり、再実行はしていない。 |
| B-F1 | partial | 冒頭の結論、worklog、phase3 はいずれも「fig8 形を 2 枚」「fig8b 形は描画拒否」と明記し、存在しない図を完成品に数える読み違いは解消した。ただし fig8b 形の図自体は未生成。 |
| B-F2 | closed | 最終 argv と provenance 2 本が insight にあり、wrapper は記載された R2 出力親 `tools/` に実在する。PNG・provenance 各 2 本は原本と bytes 一致した。 |
| B-F3 | closed | [README §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/README.md:255) は測定 **実測 1.40**、受入全走 **見積り 0.25**、合計 **見積りを含む約 1.65 node 時間**と分けている。 |
| B-F4 | partial（nit） | 冒頭の結論から主要結果にたどれるようになった。一方、周辺の実行記録は本文に残る。放置時の影響は読み手が結果を探す手間に限られる。 |

## 新規所見

成果物を変える新規の誤り・回帰は見つからなかった。結論、[worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/docs/spool/worklog/2026-09-29-dev-wave-t2853-r2-fig8b-1.md:10)、[phase3 の T-2853 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/docs/phase3.md:41) は、2 group × 3 job、verdict、費用、非合成、fig8b 形の描画拒否について本文と整合する。「飽和しない」への読み替えもない。

## 総括

**GO — fig8b 形の描画拒否を明示した再測定記録として。** fig8b 形の図を含む完成品としては未達である。

照合値：Elapse は `838/837/836/841/836/842` 秒、合計 **5,030 秒 = 1.3972 node 時間（表示 1.40）**。両 group の原報告は `not-observed-in-any-workload`、各 18/18 区間 `declining`、`performance_certified: false`。wrapper SHA-256 は `c6aa81179999b7f5f8c89fd3de146b7e5c7dccfddf39106697a41ef940296d27`。図の原本ハッシュは次のとおりで、insight の PNG・provenance はそれぞれ原本と bytes 一致した。

| R2 | PNG | provenance | PDF（repo 外原本） |
|---|---|---|---|
| a | `063849886e2c1e7b34a370e291c0b94910e1ad50894c21859164fcd233409e85` | `b8f00334ba780e84e52aaf487d2857ef0eb7069488ea11566085c26d3710fe99` | `f6bd629dfa57a08f7f307bb528ae4444c5e3edccc0735357cb57fd89ca2acb55` |
| b | `4b43456fd084684b73472b366b966bcd621c44a148ae251e5e0f7cd6d0c835e0` | `f5342a43e17d99b7c78c84cc8f6ad4dccc8f5f77c6d21df9aa736caa5108187a` | `70bff3b2f7a5cd2006876d0b899c2539a994b093158cebbb385d477cefed5042` |