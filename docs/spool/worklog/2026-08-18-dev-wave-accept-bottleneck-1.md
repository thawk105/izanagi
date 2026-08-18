---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-accept-bottleneck
seq: 1
title: 受入全走の wall は real-repo 直列鎖 + 約 26 秒の固定費で決まると実測した — work unit の並べ替え仮説は実装したうえで対測定で反証 (実装差分ゼロ、branch worktree-dev-wave-accept-bottleneck)
---

## 本文

依頼は「受入全走のボトルネックを特定し改善する。リワードハック禁止。テストなどは cpu コアを
全力で使い潰せていることが望ましい」。**結論は実装差分ゼロで、理由は改善案が実測で反証されたこと
である。** 一次資料は `output/insights/2026-08-18_acceptance-wall-cost-structure/`。

**受入全走の cost 構造を 14 走で初めて確定した。** gen_S 計算ノード (割当 48 CPU、`-n 48`、
`--dist loadgroup`) で `wall = real-repo 直列鎖 + 約 26 秒の固定費` が 14 走すべてで成立する。
鎖は 77.5〜94.9 秒 (69 件) で wall の 74〜78% を占め、`wall − 鎖長` は 20.6〜28.8 秒に収まる。
実効並列度は 59%。**遊んでいるコアは鎖が構造的に作っている**のであって、
worker 不足でも配布順でもない。

**親の中心仮説が 2 度とも誤りだった。** 第 1 版は「work unit は collection 順 FIFO で配られ、
s8c 群 (75.45 秒の鎖) は 12859 unit 中 10248 番目から始まる」としたが、
`--loadscope-reorder` の既定が True で workqueue は件数降順に並ぶため、3 群は既に先頭にある。
段 2 が設計した hoist は完全な no-op だった。第 2 版は「件数降順は所要時間の代理として不適切で、
閾値 20 秒の 17 unit を所要時間降順で先頭へ出せば完全 LPT (78.8〜83.7 秒) に到達する」としたが、
これも反証された。設計判断は {{D:acceptance-wall-model}}、経緯は {{F:xdist-default-option-missed}}。

**反証は実装したうえで対測定で行った。** 段 5・段 6 で実装を完成させ (marker が宣言 17/17 の
一致を報告することも確認)、同一 branch 上で編集面 5 file を commit 間で切り替えて
A/B を交互に 6 走した。ノード速度を除いた `wall − 鎖長` は A 26.24 秒 / B 25.86 秒で
**0.38 秒差 = 効果ゼロ**。決定的なのは B の直列総和が A より 495 秒 (15%) 大きいのに
`wall − 鎖長` が同じ点で、鎖以外の仕事は 47 worker 上で完全に鎖の下へ隠れている。

**最初に出した非対 8 走の比較はノードが完全に交絡していた** (before = bnode037 x3 / bnode025、
after = bnode002 x2 / bnode088 / bnode085)。これを根拠に採否を決めず、対測定で置き換えた。

**段 3・段 6 の敵対検証が親を 4 度止めた。** (1) 段 3 レンズ B が「1 unit ずつ配る模型は実 xdist の
先読みと一致しない」を BLOCKER として親の「完全 LPT と同値」を撤回させた。(2) 段 3 レンズ A が
`pytest_configure` で `loadscopereorder` を切る案を、workqueue が controller の `config.option`
だけで決まることを根拠に BLOCKER とし、`run_tests.py` 側へ移させた。(3) 段 3 レンズ B が
「宣言が空・全 stale のとき 113.70 秒へ悪化する」を BLOCKER とし、親は fallback 分岐ではなく
規則そのもの (残りを件数降順) で退化を消した。(4) 段 6 レンズ B が示した解釈表
「99〜108 秒なら no-op 経路の可能性が高い」は、実測 106〜113 秒に対して正しく発火した。

**不採用にした実装の所在。** commit `5e49ac7a` として一度作り、対測定の後に破棄した。逐語は
repo 外の job dir へ保全した。段 6 の敵対レビュー 2 本は BLOCKER 0 / MUST-FIX 計 17 件を出しており、
仮に効果があってもその修正なしでは land できない状態だった。

**効かないと実測で確定した手。** work unit の配布順の変更、worker 数を増やす (48 は gen_S の
per-job 上限で receipt の `CPU Number Max: 48` が実測)、worker 数を減らす (`-n 32` は模型で悪化)。

**工数。** codex 子 8 本 (plan x2、consult x4、author x1、fix x1、review x2)、すべて accepted。
model = `gpt-5.6-luna`、reasoning = `max`。親の実測 = gen_S への dispatch 14 走 + 焦点走 2 回。

## 次の一手差分

### 新規

- {{T:acceptance-fixed-overhead}} **P2・新規**: 受入全走の固定費 約 26 秒 (`wall − real-repo 鎖長`、
  14 走で 20.6〜28.8 秒) の内訳を測り、削減可否を判定する。48 worker が各自 12951 件を
  collection する費用が主因と見ているが未分解。単一 process の collection は実測 4.08 秒。
  正本 = `output/insights/2026-08-18_acceptance-wall-cost-structure/`
