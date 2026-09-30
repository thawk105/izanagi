---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-vhash-interval-gc
seq: 1
title: Cicada の区間 GC (最小形・一般形) を試作し、正しさ検査と長い tx 負荷の同時刻計測をした (VHash md_18、コード + docs、branch worktree-dev-wave-vhash-interval-gc)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_18.txt` (dev-wave)。一次資料は `output/insights/2026-09-29/vhash-interval-gc/README.md`。設計判断は {{D:igc-prototype-design}}・{{D:igc-s8-positive-not-substituted}}。
- ユーザー指示: 計算量の確認 (2 node 時間以上) への回答は「進めていいんだけど、40ジョブに分割して６分で終わるのを目指して欲しい」。本計測は build 1 回 + 40 part に分け、6 分 01 秒・17 host で完了した。
- 結論の要約:
  - 案は既知 (最小形 = vDriver、一般形 = Steam・HANA・vDriver)。
  - 安全な物理再利用は作れず、計測は mode 1 (外すが走行中は再利用しない)。
  - 正常 3 腕は検査 30 走行で巡回 0。事前登録した壊し正例 (ronly_wait) は発火 0 で不成立。
  - throughput は install の lock 経路が支配する (min/stock 0.062〜0.692)。
  - 鎖・hop の腕間差は書き込み量の差と交絡する。
  - 長い read-only tx では境界の公開 0 で試作は無作動 (`vhash-readonly-gc-publish` と同じ機序)。
- 段 4 の親裁定が段 2・3 の安全側の推奨を 3 度覆し、4 巡の smoke を費やした ({{F:parent-ruling-overrode-safer-recommendations}})。
- 段 5 の B1-11 指示で S8 を言い換え、正例の判定を緩めた。段 6 レビュー 2 本が捕捉し、fix で戻した (F1 再発)。
- 段 6 レビューの採否: R1・B-01・R3 は fix。R2 は CLI の推論の穴だけ fix し、host・binary hash の照合は親が 1 回実データで確かめた (40 part・244 記録で一意)。R4・B-02・B-03・B-04 は一次資料の記述で扱った。
- セッション異常: main 取り込みの `merge --abort` で、Lustre の lstat 割り込みにより main 側の file が 1 つ未追跡で残った。main に同じ内容があることを照合してから削除した。

## 次の一手差分

### 新規

- {{T:igc-mode3-control}} **P2・新規 (VHash md_18 の続き)**: 区間 GC の剪定の効果と install 経路の費用を切り分ける。同じ build に `--cicada_igc_debug_mode=3` (剪定しない、install 経路は同じ) の腕を足し、stock・mode 3・最小形・一般形を同時刻に測る。一次資料 `output/insights/2026-09-29/vhash-interval-gc/README.md` §9 項 1。
- {{T:igc-with-ro-gcflag}} **P2・新規 (VHash md_18 の続き)**: `cicada-ro-gcflag-variant.patch` と区間 GC を重ね、長い read-only tx の cell で境界の公開と剪定が起きるか、stock の 2.2 GB の鎖がどこまで縮むかを測る。事前登録した壊し正例 (ronly_wait) もここで初めて発火しうる。同 §9 項 2。
- {{T:igc-lockfree-install-and-reuse}} **P3・新規**: 区間 GC の install を lock なしにする設計と、外した版の安全な再利用 (mode 0 の破損の根本原因の特定) を、小さなモデルでの検査から段 2 でやり直す。同 §9 項 3・4。
