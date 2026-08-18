---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-accept-bottleneck
seq: 3
---

## 新規

### {{F:xdist-default-option-missed}}. 依存 plugin の既定値を確かめず wave の中心仮説を組み立てた [手順漏れ] [計測汚染]

- 事象: 親は `xdist/scheduler/loadscope.py` の workqueue 構築を読み、
  「work unit は collection 順 FIFO で配られる」として brief と段 2 プランを組み立てた。
  実際には `xdist/plugin.py` の `--loadscope-reorder` が既定 True で、workqueue は件数降順に並ぶ。
  3 群は最初から行列の先頭にあり、段 2 が設計した hoist は完全な no-op だった。
  段 3 の敵対相談が指摘するまで、親は brief・プラン・敵対相談 2 本ぶんの子を誤った前提で走らせた。
- 根本原因: 分岐の**中身**だけを読み、分岐を選ぶ `config.option` の既定値を読まなかった。
  同じ file 内の `if self.config.option.loadscopereorder:` を見ていながら、
  その option の定義元 (`plugin.py` の `addoption(..., default=True)`) へ辿らなかった。
- 恒久対応: {{D:acceptance-wall-model}}。外部 plugin の挙動を前提にする wave では、
  分岐条件となる option / 環境変数の**既定値の定義元**を読むまで brief を確定しない。
- 再発検知: 提案が「現行挙動と異なる」ことを、実装前に忠実模型で現行形と提案形の
  両方を出して差が非ゼロであることで示す。差ゼロなら no-op として段 4 で止める。

### {{F:node-confounded-ab-comparison}}. 改善の可否をノードが交絡した非対比較で判定しかけた [計測汚染]

- 事象: 実装後の効果判定に、実装前 4 走 (bnode037 x3 / bnode025) と実装後 4 走
  (bnode002 x2 / bnode088 / bnode085) の比較を用いた。両 arm のノード集合は完全に素で、
  実装後の直列総和は 1〜2 割大きかった。この比較だけでは「遅くなった」も「変わらない」も言えない。
- 根本原因: 計算ノードの割当を制御できない環境で、arm ごとにまとめて走らせた。
  ノード差は同一コードで 116 秒対 200 秒級の記録がある既知の外乱である。
- 恒久対応: 同一 branch 上で編集面を commit 間で切り替え、A/B を交互に投入する対測定を正本にする。
  ノード速度に依存しない正規化量 (`wall − 直列鎖長`) を主指標に併記する。
- 再発検知: 判定に使う走行の実行ホストを receipt から列挙し、arm 間でホスト集合が素なら
  その比較を採否根拠にしない。
