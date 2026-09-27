## 所見表

| # | 重大度 | file・節 | 記述と問題 | 一次資料 |
|---|---|---|---|---|
| 1 | must-fix | [新 insight §0・§6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2868-mocc-g2/output/insights/2026-09-27/t2868-mocc-g2-cause/README.md:17)、[worklog「完了」](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2868-mocc-g2/docs/spool/worklog/2026-09-27-dev-wave-t2868-mocc-g2-1.md:27) | 「literal 差し込みの意味の変更は排除」は範囲が広すぎる。排除できたのは、照合した patch による validation・lock・hook の**直接変更**だけ。待ち時間が並行実行の結果を変える経路は残る。 | [段4裁定 A3](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/s4-ruling.md)、[probe の patch_check](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/probe/t2868_recheck.py:143) |
| 2 | must-fix | [新 insight §0・§6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2868-mocc-g2/output/insights/2026-09-27/t2868-mocc-g2-cause/README.md:23) | 「候補にも同じ率」「原因は候補の内容ではなく」は断定できない。stock の陽性は literal が**必要条件でない**ことを示すが、候補での寄与や率の同等性は示さない。本文自身も非有意は同等性の証明でないと認めている。論文用の結論もこの範囲にそろえるべき。 | [反復行](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/rh-verify-lines.tsv)、[段B反復行](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/stageB-verify-lines.tsv)：6/119 対 3/109、Fisher 両側 p＝0.5029 |
| 3 | should | [新 insight §4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2868-mocc-g2/output/insights/2026-09-27/t2868-mocc-g2-cause/README.md:103) | writer の publish を「1261〜1262 行」とする行番号が違う。そこは `#if TRACE` と hook 条件。publish の atomic store は **1259〜1260 行**。 | [transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2868-mocc-g2/external/ccbench/cc/mocc/transaction.cc:1259) |
| 4 | should | [新 insight §0・§4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2868-mocc-g2/output/insights/2026-09-27/t2868-mocc-g2-cause/README.md:20) | (iii)「支持」は静的候補との整合を表すならよいが、実測が本体欠陥を hook 誤記録より選別したようにも読める。両者は未分離。「実装側で残る候補」と明示するのが正確。 | [段4裁定 A2/B6](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/s4-ruling.md)、[probe の raw 抽出](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/probe/t2868_recheck.py:191)：trace 内の整合を検査 |
| 5 | should | [新 insight §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2868-mocc-g2/output/insights/2026-09-27/t2868-mocc-g2-cause/README.md:118)、[t2849 §10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2868-mocc-g2/output/insights/2026-09-27/t2849-mocc-conn/README.md:154)、[worklog 新規T](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2868-mocc-g2/docs/spool/worklog/2026-09-27-dev-wave-t2868-mocc-g2-1.md:33) | 「約3〜5%」を cell の安定した失敗率として読むと精度を過大評価する。観測値は追加 stock **3/74＝4.1%**、旧走を含む **3/109＝2.8%**で、後者の95%正確区間は **0.6〜7.8%**。観測率と母率の不確かさを分けて書くべき。 | [両反復行](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/stageB-verify-lines.tsv)、[段4裁定 A6](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/s4-ruling.md) |

## 検算して一致した項目

- 段Aの6件について、保全 dir、commit 数、literal 値、2取引と thread、両辺の key・読んだ版・次の書込版と書き手を、[一次 compact JSON](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/recheck-compact.json)と照合した。候補6件と stock 3件の witness は各2辺とも `holds=true`。版差の内訳も1が6件、2が2件、3が1件で一致。
- 段Bの16 slot の campaign ID は[ledger の events](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/stageB/cohort/read-heavy/controls/block-1/events/)と一致。反復行から候補 **6/119**、追加 stock **3/74**、旧 stock **0/30**を確認。旧走の別枠5反復を足した **0/35** は段4裁定の記録と整合する。
- 率、Clopper–Pearson 95%区間、Fisher 両側 p＝**0.5029**、旧 stock 0/35 の確率 **0.3765**、commit 数の各範囲は記載の丸めと一致。
- Elapse は **1,242＋11,450＋1,100＝13,792秒＝3.8311 node 時間**で一致。[段A](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/stageA.log)、[段B各 job](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/stageB/evidence/block-1/job.stderr)、[再検査](/work/1/SFC/tanab/tmp/t2868-mocc-g2-20260927/stageB2.log)を照合した。
- verifier 同版・同 witness、trace 内の2辺、X/I/P 0、patch の hole 外差分0という記録は要約と一致。(i) の**記録された trace に限る**限定、(ii') の必要条件否定、(iv) の未検証は probe の射程と合う。
- コードの **1033〜1063、1035〜1038、1049、1271行**は現物と一致。t2849 は§10の追記だけで旧§0〜§9は変更されず、reject・判定の書換えは見当たらない。trace 走の commit 数も性能値としては使っていない。
- worklog の未分離事項は新規Tへ明記され、択一(a)〜(c)は insight §6と一致。「合成候補の誤りを捕まえた例には使えない」という方向も一致する。ただし所見2の因果断定は修正が必要。

## 検算できなかった項目と理由

- 旧 stock の別枠 **5反復**の生の WAL 行。射影された `rh-verify-lines.tsv` にあるのは30反復で、5反復は段4裁定による確認にとどまる。
- trace 保全の **35 GB**、pin C と原本の差分が `#if TRACE` 内だけであること、既往 T-1892・T-2774・T-2779 の件数。対応する原本は今回の必読射影に含まれない。
- hook が実際の読取版を忠実に記録したか、および本体欠陥と hook 誤記録の分離。保全 trace と同じ意味論を共有する静的再検査では検証できない。

## 総括

主要な件数・witness・統計値・計算時間は一致した。修正が必要なのは、patch 照合から「意味変更を排除」と広げた点と、非有意な率比較から候補の原因まで断定した点である。writer の publish 行番号も訂正が要る。元の reject と t2849 の判定は保持され、残件の新規Tへの移管も確認できた。