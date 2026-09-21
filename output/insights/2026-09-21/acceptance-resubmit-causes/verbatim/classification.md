## 試行ごとの分類表

| entry | wave | 試行 | 門番待ち (分) | 外側 wall (分) | 待ち手 | test | 結果 | 分類 | 備考 |
|---|---|---|---|---|---|---|---|---|---|
| 1779 | t2797-b5-contrast | final | 2.3 | 7.6 | 有 | 有 | red-own | A 自分起因の赤 | test_ccbench_spawn_sites 2 件 (process 起動点の exact 目録) → fix4 517fd5451 |
| 1779 | t2797-b5-contrast | final2 | 2.4 | 12.1 | 有 | 有 | green | E rc=23 型 (記録 commit 後の tip 変更) | 緑 tip 088bbdec7 の後に記録 commit cf1c90e1f → land rc=23 → final3 |
| 1779 | t2797-b5-contrast | final3 | 2.3 | 22.9 | 有 | 有 | green | (最終緑) | landed 05:26 |
| 1777 | t2817-acceptance-bottleneck-3 | ref | 2.9 | 11.6 | 有 | 有 | green | (診断の参照走、再投入ではない) | wave の測定対象 (handoff-final §1.3)。会計から除外、一覧には残す |
| 1777 | t2817-acceptance-bottleneck-3 | final | 2.6 | 9.7 | 有 | 有 | red-nonattr | B 非帰属の赤 (hold 未登録) | test_t2620_orphan_mixed_is_rejected 1 件 (/proc 走査の競走、entry 1724 で同型観測)、単独再走 1 passed |
| 1777 | t2817-acceptance-bottleneck-3 | final2 | (中止) | — | 無 | 無 | aborted | (投入前中止、走なし) | gate 行 1 本のみ、会計から除外 |
| 1777 | t2817-acceptance-bottleneck-3 | final3 | 4.2 | 12.1 | 有 | 有 | red-nonattr | B 非帰属の赤 (hold 未登録) | test_t810_coordinator 2 件 (worktree 登録消失、entry 1756 T-2766 で記録の型; 03:19 に T-2814 が land)、単独再走 45 passed |
| 1777 | t2817-acceptance-bottleneck-3 | final4 | 2.5 | 22.8 | 有 | 有 | green | (最終緑) | land 初回 rc=23 は監査列の順序 (--reverse 抜け) で argv 修正のみ、受入再投入なし |
| 1776 | t2810-g1-launch-validation | final | 5.9 | 4.8 | 有 | 無 | infra | G 分類外: 受入基盤 (collection 段の receipt memo lock timeout → 兄弟 shard 中断 → orphan hold) | test 0 件走行、非帰属 (job dir acceptance-red-final-1.md)、orphan 終端待ち → hold 退避 → 同一内容再投入 |
| 1776 | t2810-g1-launch-validation | final2 | 2.6 | 11.8 | 有 | 有 | green | (最終緑) |  |
| 1775 | t2814-cleanup-command | final-1 | 12.4 | 0.8 | 有 | 無 | postcheck | D4 待ち手の postcheck (child 起動前の main 包含再検査で停止) | gate-acceptance-loop.sh が attempt 2 を自動投入 |
| 1775 | t2814-cleanup-command | final-2 | 2.0 | 24.5 | 有 | 有 | green | (最終緑) |  |
| 1770 | t2344-closure-stage | final | 2.9 | 12.3 | 有 | 有 | red-own | A 自分起因の赤 | test_formal_loader_rejects_real_exploration 1 件 (受理集合の変化) → fix 2 |
| 1770 | t2344-closure-stage | final2 | 1.8 | 12.3 | 有 | 有 | green | (最終緑) |  |
| 1769 | t2803-provenance-receipt | final | 2.5 | 11.4 | 有 | 有 | green | H 分類外: 緑後に main が受入道具 (runner/waiter/reds checker/land) を変えて前進 → land script rc=92 → 取り込み後の再投入 (F524) | tested main 1cc303534 → land 時 main 6305f2d05 |
| 1769 | t2803-provenance-receipt | final2 | 2.4 | 0.1 | 無 | 無 | merge-preflight | D3 親 chain script の起動前 merge の message preflight 赤 (取り込む main が実装面を含み merge message に role=author が無い) | 待ち手起動なし。親が Codex 署名付き merge を作って再投入 |
| 1769 | t2803-provenance-receipt | final3 | 2.3 | 21.8 | 有 | 有 | green | (最終緑) |  |
| 1768 | t2804-provenance-timeout-contract | final-1 | 2.6 | 1.2 | 有 | 無 | postcheck | D4 待ち手の postcheck (child 起動前の main 包含再検査で停止) | gate-acceptance-loop.sh が attempt 2 を自動投入 |
| 1768 | t2804-provenance-timeout-contract | final-2 | 2.5 | 9.9 | 有 | 有 | green | (最終緑) |  |
| 1767 | t2243-collection-diag | final att1 | 2.9 | 1.3 | 有 | 無 | postcheck | D4 待ち手の postcheck (child 起動前の main 包含再検査で停止) | run-acceptance-gated.sh が attempt 2 を自動投入 |
| 1767 | t2243-collection-diag | final att2 | 2.5 | 9.8 | 有 | 有 | green | (最終緑) |  |
| 1761 | paper-story-20260920b | final | 80.6 | 2.0 | 有 | 無 | terminal-merge | D1 待ち手の post-claim merge の terminal-merge (実競合) | reason=terminal-merge、親が固定 SHA で main を merge して再投入 |
| 1761 | paper-story-20260920b | final2 | 18.5 | 12.2 | 有 | 有 | green | (最終緑) |  |
| 1759 | cleanup-backup-loss-record | final | 8.8 | 19.6 | 有 | 有 | red-nonattr | B 非帰属の赤 (hold 未登録) | test_real_repo_upgrade_writer_drains_overlapping_reader_stream[legacy] 1 件 ('blocked'=='upgraded'、同居負荷の競走)、非帰属判定は handoff のみ (worklog 記録なし)、焦点走 2/2 緑 |
| 1759 | cleanup-backup-loss-record | final2 | 38.9 | 0.1 | 無 | 無 | merge-conflict | D2 親 chain script の起動前 merge の実競合 | output/insights/2026-09-19/k2-loop-round3/README.md (T-2795 の追記節と衝突)、待ち手起動なし、親が両方保持で merge |
| 1759 | cleanup-backup-loss-record | final3 | 6.8 | 12.1 | 有 | 有 | green | (最終緑) |  |
| 1758 | t2153-witness-requested-us | final att1 | 4.2 | 2.5 | 有 | 無 | postcheck | D4 待ち手の postcheck (child 起動前の main 包含再検査で停止) | behind=53 の起動前 merge の後、run-acceptance-gated.sh が attempt 2 を自動投入 |
| 1758 | t2153-witness-requested-us | final att2 | 2.3 | 9.3 | 有 | 有 | green | (最終緑) |  |

## wave ごとの追加 wall

追加 wall = (最終緑の finished − 最初の試行の門番開始) − (最終緑 1 試行の門番待ち + 外側 wall)。再試行分 (門番待ち + 外側 wall の和) と試行間の残差 (親の判定・fix・記録 commit・land 試行などが入るが本資料では内訳を裏付けない) に分ける。参照走 (T-2817 ref) と投入前中止 (T-2817 final2) は除外。

| entry | wave | 試行数 | うち待ち手起動 | うち test 実行 | 最初の門番開始 | 最終緑 finished | 総受入 wall (分) | 最終緑 1 試行 (分) | 追加 wall (分) | うち再試行分 (分) | うち門番待ち (分) | うち外側 wall (分) | うち試行間の残差 (分) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1779 | t2797-b5-contrast | 3 | 3 | 3 | 2026-09-21 04:19:16 | 2026-09-21 05:20:47 | 61.5 | 25.2 | 36.3 | 24.3 | 4.7 | 19.6 | 11.9 |
| 1777 | t2817-acceptance-bottleneck-3 | 3 | 3 | 3 | 2026-09-21 02:57:13 | 2026-09-21 03:58:52 | 61.6 | 25.4 | 36.3 | 28.6 | 6.8 | 21.7 | 7.7 |
| 1776 | t2810-g1-launch-validation | 2 | 2 | 1 | 2026-09-21 03:06:22 | 2026-09-21 03:41:01 | 34.6 | 14.4 | 20.2 | 10.7 | 5.9 | 4.8 | 9.5 |
| 1775 | t2814-cleanup-command | 2 | 2 | 1 | 2026-09-21 02:34:17 | 2026-09-21 03:15:00 | 40.7 | 26.5 | 14.2 | 13.2 | 12.4 | 0.8 | 1.0 |
| 1770 | t2344-closure-stage | 2 | 2 | 2 | 2026-09-20 23:32:53 | 2026-09-21 00:14:58 | 42.1 | 14.1 | 28.0 | 15.2 | 2.9 | 12.3 | 12.8 |
| 1769 | t2803-provenance-receipt | 3 | 2 | 2 | 2026-09-20 23:14:08 | 2026-09-21 00:06:54 | 52.8 | 24.1 | 28.7 | 16.4 | 4.9 | 11.4 | 12.3 |
| 1768 | t2804-provenance-timeout-contract | 2 | 2 | 1 | 2026-09-20 23:09:17 | 2026-09-20 23:26:31 | 17.2 | 12.4 | 4.8 | 3.8 | 2.6 | 1.2 | 1.0 |
| 1767 | t2243-collection-diag | 2 | 2 | 1 | 2026-09-20 22:51:02 | 2026-09-20 23:07:30 | 16.5 | 12.3 | 4.2 | 4.2 | 2.9 | 1.3 | -0.0 |
| 1761 | paper-story-20260920b | 2 | 2 | 1 | 2026-09-20 19:45:19 | 2026-09-20 21:44:12 | 118.9 | 30.6 | 88.2 | 82.6 | 80.6 | 2.0 | 5.6 |
| 1759 | cleanup-backup-loss-record | 3 | 2 | 2 | 2026-09-20 19:55:43 | 2026-09-20 21:29:14 | 93.5 | 18.8 | 74.7 | 67.4 | 47.7 | 19.7 | 7.3 |
| 1758 | t2153-witness-requested-us | 2 | 2 | 1 | 2026-09-20 21:11:36 | 2026-09-20 21:29:53 | 18.3 | 11.6 | 6.7 | 6.7 | 4.2 | 2.5 | 0.0 |
| 合計 (11 wave) | | | | | | | | | 342.3 | 273.1 | 175.7 | 97.4 | 69.2 |

複数試行の wave = 11 (待ち手起動 2 回以上 = 11、test 実行 2 回以上 = 5)。

## 分類ごとの件数と再試行分の wall (分)

| 分類 | 件数 | うち待ち手起動 | うち test 実行 | 門番待ち (分) | 外側 wall (分) | 計 (分) |
|---|---|---|---|---|---|---|
| A 自分起因の赤 | 2 | 2 | 2 | 5.1 | 19.9 | 25.0 |
| B 非帰属の赤 (hold 未登録) | 3 | 3 | 3 | 15.6 | 41.3 | 57.0 |
| D1 待ち手の post-claim merge の terminal-merge (実競合) | 1 | 1 | 0 | 80.6 | 2.0 | 82.6 |
| D2 親 chain script の起動前 merge の実競合 | 1 | 0 | 0 | 38.9 | 0.1 | 39.0 |
| D3 親 chain script の起動前 merge の message preflight 赤 (取り込む main が実装面を含み merge message に role=author が無い) | 1 | 0 | 0 | 2.4 | 0.1 | 2.5 |
| D4 待ち手の postcheck (child 起動前の main 包含再検査で停止) | 4 | 4 | 0 | 22.1 | 5.7 | 27.9 |
| E rc=23 型 (記録 commit 後の tip 変更) | 1 | 1 | 1 | 2.4 | 12.1 | 14.5 |
| G 分類外: 受入基盤 (collection 段の receipt memo lock timeout → 兄弟 shard 中断 → orphan hold) | 1 | 1 | 0 | 5.9 | 4.8 | 10.7 |
| H 分類外: 緑後に main が受入道具 (runner/waiter/reds checker/land) を変えて前進 → land script rc=92 → 取り込み後の再投入 (F524) | 1 | 1 | 1 | 2.5 | 11.4 | 13.9 |
| C F1013 同型 (三軸語走査の出力 file が holdout hit) | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| F lease の失効 | 0 | 0 | 0 | 0.0 | 0.0 | 0.0 |

受入 1 試行で済んだ wave (9、job dir の attempt log と green receipt が各 1 本): 1778 branch-residue-cleanup, 1774 wall-decomp, 1773 paper-story-20260921, 1772 paper-abstract-conclusion-ja, 1766 t2807-b8-prerun, 1765 t2813-o26-inventory, 1764 k2-loop-originals-lost-downstream, 1763 fig13-b10-waiting-grid, 1762 paper-related-work-ja
