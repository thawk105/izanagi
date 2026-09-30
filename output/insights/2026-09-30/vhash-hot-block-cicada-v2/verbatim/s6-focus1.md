| 所見 | 判定 | 根拠 file:line | 1 行の説明 |
|---|---|---|---|
| A1 | closed | [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:828) | B2 と計器版から旧予測を除き、到達・変更・commit・検出を観測値として分類する。 |
| A2 | closed | [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:729) | 裁定どおり、三つ組の多重集合で changed/read と committed/commit end を完全照合する。 |
| A3 | partial | [stale-gap patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-post-stale-gap.patch:62)、[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:581) | 4 回の再試行と未確定件数の必須行は実装されたが、先頭 pointer の一致だけでは列の途中の変更を検出できない。 |
| A4 | partial | [stale-hot patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-post-stale-hot.patch:47) | 物理列から確定版を探す変更は入ったが、新たにたどる古い版の寿命が保証されていない。 |
| A5 | closed | [親の一次資料](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/plan.md:15) | stock と共通の寿命前提への依存を明記している。裁定どおりコード変更なし。 |
| B1 | closed | [作図](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/tools/plotting/plot_vhash_cicada_hot_block.py:153)、[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/tests/test_plot_vhash_hot_block.py:301) | 入力 Path の上書きを解消し、実際の `_save()` と provenance を検査する test を追加した。 |
| B2 | closed | [作図](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/tools/plotting/plot_vhash_cicada_hot_block.py:82) | 腕ごとの色・marker と fig-ro の GC ごとの線種を分けた。 |
| B4 | closed | [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/orchestrator/campaign/vhash_cicada_hot_block.py:37) | 固定 flag と旧 patch 分岐を削り、post 用 patch を直接指定した。 |

### F1: stale-gap の列途中への挿入を見逃す

**重大度: must-fix。** [比較走査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-post-stale-gap.patch:62) は走査前後の `latest_` だけを見る。一方、[stock の挿入](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:521) は途中の `next_` に CAS できる。先頭が同じまま新しい適格版が挿入されても `determined=true` となり、changed を過少計数しうる。**推奨:** 走査経路の変更も検出できる同期または再検証を入れ、検出不能なら undetermined に数える。

### F2: post-B1 が GC 対象の古い版をたどりうる

**重大度: must-fix。** [B1 の追加走査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/patches/broken-cicada-vhash-post-stale-hot.patch:47) は選択版の `next_` を読み、status を参照する。[GC](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-v2/external/ccbench/cc/cicada/transaction.cc:831) はその `next_` 以下を切り離して回収できる。選択版が GC anchor の場合、追加走査の対象には選択版自身の寿命論証が及ばず、解放済み版を参照しうる。**推奨:** 古い版の保持を保証してからたどるか、回収と同期して安全な場合だけ変異する。

## 総括

**NO-GO。** A3・A4 に上記の未解決点がある。stale-gap の C++ 出力書式と driver の必須 parse は一致し、件数は分類記録に残る。差分は裁定対象の 7 ファイルに収まり、既存検査の削除や COUNT・trace 計器の perf build への流入は静的には見つからなかった。追加 test は照合と保存処理を検査するが、F1・F2 の並行動作は検査していない。build・テスト・計測は実行していない。