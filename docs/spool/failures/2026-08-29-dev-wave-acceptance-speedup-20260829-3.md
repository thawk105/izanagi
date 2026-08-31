---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-acceptance-speedup-20260829
seq: 3
---

## 新規

### {{F:tmpdir-mixed-regime-lock-fragmentation}}. 一時領域の既定だけを変える案が、明示指定した session と混在したときに排他を無効化しかけた [誤前提] [検出力]

- 事象: 受入高速化のため「実効 `TMPDIR` が未設定のときだけ共有 filesystem 上の安定 root を
  既定にし、明示 `TMPDIR=/tmp` は尊重する」という plan を段 2 が起草した。段 3 の敵対レビューが、
  **この 2 種類の session が同時に同じ tree または repo を触ると互いに排他しなくなる**ことを
  指摘した。片方は `/tmp` 上の lock を、もう片方は共有 root 上の lock を取るため、
  同じ資源に対する lock identity が 2 つに割れる。現状は両者とも `/tmp` を使うので、
  これは**現行保証からの退行**である。実装前に捕まえたので実害は出ていない。
- 根本原因: **既定値だけを変える設計を「後方互換だから安全」と扱った。** 実際には、
  lock identity を一時領域の path から導いている限り、一時領域の値が分岐すること自体が
  排他の分割を意味する。plan は per-run root が lock identity を壊すことは正しく見抜いていたが、
  **同じ理屈が「明示と既定の混在」にも当てはまることを見落とした。** 正しい設計は
  correctness lock の置き場を `TMPDIR` から分離し、canonical な repo / tree identity から
  一意に導くことである。
- **提案されていたテストでは検出できなかった。** plan が新設予定だった検査は
  「同じ安定 root 同士」の組しか対照に持たず、混在の負例が無かった。
  性能目的の変更に対して、同種の設定を共有する組だけで排他を検査すると、
  設定が分岐する経路の破れは恒真に通る。
- 恒久対応: {{D:acceptance-tmpdir-axis-refuted}} で当該案そのものを不採用として閉じた。
  将来この族 (一時領域・lock 置き場・既定値の分岐) を再訪する場合の必須検査として、
  **異なる設定の 2 process を同時起動し、同じ lock identity を得るか実排他になることを
  確かめる混在負例**を対照に入れる。同種設定同士の対照だけを根拠にしない。
- 再発検知: 一時領域や lock 置き場の既定を変える提案が出た時点で、
  `orchestrator/campaign/patchharness.py` と `tools/mutation_harness.py` の lock path 導出を読み、
  設定が分岐しうる全組合せを列挙する。1 組でも lock identity が割れるなら設計を変える。

## 再発

### F473

- **再発: 2026-08-29** — 親が同じ probe 出力の**別 column を混ぜて**比・差・処理量を書いた。
  提示した表は median column なのに、本文の「Lustre は `/tmp` の 240 倍速い」
  「小 file の絶対差は 1.4 秒」「総処理量は約 107 fsync/s」は wall column から計算していた。
  median column で整合する値はそれぞれ 358.8 倍、0.908 秒、110.1 fsync/s である。
  どちらの column も実観測であり捏造ではないが、**出所を混ぜた点が F473 の型**である
  (数を出す前に「この数の母集合と除外は何か」を明示していない)。
  段 3 の敵対レビューが指摘し、親が再計算して訂正した。結論は変わらない
  (当該軸は計算ノードの実測で棄却済み)。複数 column を持つ probe 出力では、
  比・差・throughput を同じ column から採り、どの column かを明記する。
