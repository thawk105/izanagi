---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2256-verifier-serial
seq: 1
title: [T-2256] 直列性検査の親側の辺結合を task 順連結 + run 単位 set.update に変え 68 万 read-heavy を 18.2→12.6 s (1.45 倍)、判定は sha256 で不変を確認 (コード + docs + insight、branch worktree-dev-wave-t2256-verifier-serial、変異 8 本 KILLED + 等価 1 本 SURVIVED)
---

## 本文

- 親に残る直列部 (前 wave 実測で全体の 38.6%、並列度 16 で飽和) のうち辺の結合だけを縮めた。設計判断は {{D:verifier-serial-merge-concat-and-run-update}}。
- 採用: P1 (子の辺列を task 番号順に連結、旧 heapq.merge を置換) + P2 (子が source 初出順に run へ群化、親は set.update で投入)。撤回: P3 (dense 配列 Tarjan、SCC 3.15→5.65 s)、P4+P5 (鍵の大域 id で producer 0.94→2.98 s)。撤回差分は wave job dir の unit3-rejected.patch に退避し repo に入れていない。
- 実測 (Pegasus login node、共有・非専有、CPython 3.10.12、PYTHONHASHSEED=0、旧新交互): 680k/16w n=3 中央値 総 18.22→12.60 s、辺構築 11.42→6.17 s、判定 result_to_dict の sha256 は全 trace・並列度 1/16/48 で旧新一致。Amdahl 直列部 S 16.25→10.51 s (同系列、T1 は n=1 2 点近似)。
- レビュー B の指摘で P2 単独比較を追加実測 (P1 だけの木 vs P1+P2、n=3): 総 14.37→12.99 s (3 走とも速い)、Pss は P1 単独比 +4〜5%・旧 baseline 比 −8%。write-heavy 170k-wh は総 wall 差なし。記録の転記・中央値誤りは生台帳から機械生成した表へ差し替えた。
- 段 6 レビュー 2 本: A (判定同一性) GO must-fix 0、B (実効性・記録) NO-GO must-fix 6 は全件記録指摘でコード意味論欠陥 0。裁定は wave job dir の ruling-stage6.md。B-10 12 時間枠は「入る」と書けず包絡 10.7〜14.3 時間 (境界をまたぐ、保証しない、D1529 但し書き継承)。
- 変異: probe で実赤 node を採り final spec に KILLED 期待で固定。negative 8 本 (M1/M2/M3/M4/M5/M8b/M9/M6p) 全 KILLED、等価変異 E1 は SURVIVED、baseline 緑。M8b (完全性検査の緩和) は計算ノードで 4 赤で KILLED し、レビュー A の環境依存懸念を実機で否定。M6p は撤回した M6 の代替 anchor。

## 次の一手差分

### 完了

- [T-2256] 直列性検査の親側の辺結合を縮め、判定同一性を sha256 と変異で確認して受入・land した。
  remaining: none
  base: a1716c2e18630e95149c85d9960af364b57b54e07d5068e2233ebac987682b8e

### 新規

- {{T:verifier-writer-only-key-global-id}} **P3・新規**: 直列性検査の鍵の大域 id を writer を持つ鍵に限り、writer 無しを sentinel として子で扱う (親の read 全走査を避ける、本 wave の P4 撤回理由)。producer 構築の直列部 (0.9 s) が対象。
- {{T:verifier-scc-serial-shrink}} **P3・新規**: 直列性検査の SCC の直列部 (約 3 s) を縮める。登録 pass を持つ dense 化は本 wave で遅かったので、登録 pass を持たない形だけを候補にする。
- {{T:verifier-edge-helper-direct-tests}} **P3・新規**: 直列性検査の `_ordered_complete_edge_outcomes` へ重複 task_index・欠落・空集合を直接渡す単体テストと、edge-worker 失敗テストへ子 PID marker を足す (段 6 レビュー A の should)。
