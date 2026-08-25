---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1563-nproc-measurement
seq: 1
---

## {{D:acceptance-order-worker-independence}}. 受入の投入順が worker 数に依存しないことを検査で固定し、主張を大域の取り出し順に限定する

**決定:** 受入全走の work unit 投入順は worker 数に依存しない。この性質を、発火する検査 2 層で
固定する。層 1 は collection wrapper を通した完全 nodeid 列を 16 / 32 / 48 で exact 比較し、
層 2 は `LoadGroupScheduling` の global dequeue trace を比較する。両層とも、入力を全 arm で
同一に保ったまま worker 数依存の tie-break を注入する positive control を持つ。

**主張の射程を次へ限定する。** arm 間で同一なのは **最終 workqueue の大域取り出し順**だけである。
各 unit がどの worker へ渡るか、初期同期配布の幅、先取りの時刻、完了順は worker 数の効果そのもの
(mediator) であり、不変条件に含めない。「投入順まで完全に揃えた」と書いてはならない。

**理由:**
- D746 の並べ替えは worker 数を入力に取らない純関数であり、窓定数も literal である。
  shard 割付けも worker 数を読まない。よって性質としては既に成立している。
- しかし検査が無く、窓定数を worker 数から導く改訂が入れば静かに崩れる。崩れると worker 数の
  対測定が投入順の遊びを worker 数の効果として帰属し、既定値の再裁定が誤った値で確定する。
- 大域取り出し順より強い主張 (worker 割付けまで同一) は成立しない。制御できていないものを
  制御済みとして成果物へ記録しないため、射程を明示的に切る。

**却下した選択肢:**
- 検査を層 1 だけにする — wrapper の後段で順序が変わる経路を覆わない。
- positive control の初期列を arm ごとに変える — wrapper が完全 no-op でも control が通り、
  検出力を証明しない。
- 交絡として測定設計へ織り込む (揃えない側) — 揃っているのに交絡扱いすると、
  実在しない不確実性を成果物へ持ち込む。

## {{D:acceptance-nproc-study-estimand}}. 受入 worker 数の対測定は本番 shard を内部 shard 経路で測り、既定値は動かさない

**決定:** 受入全走の worker 数に関する対測定の estimand を次に固定する。

> 同一 PBS 割当・同一ノード・K=2 固定の内部 shard 実行における、`IZANAGI_TEST_NPROC` だけを
> 16 / 32 / 48 に変えたときの shard 別 runner wall。arm の outcome は 2 shard の wall の max。
> 主比較は block 内 paired difference。primary contrast は 32 対 48 とし、16 は secondary。

**この測定は既定 worker 数を変える根拠にしない。** 受領証へ機械可読な除外項として固定する。
既定値の再裁定はユーザー手番であり、D103 決定 (3) と D532 のどの範囲を supersede するのかを
併せて諮る。

**理由:**
- 受入全走は既定で 2 shard に分かれ、shard ごとに別ノードへ dispatch される。受入 wall は
  shard wall の max である。したがって 1 ノードで 1 shard を測ることが本番の量を測ることであり、
  D531 が要求する「同一割当内」も同時に満たす。
- 内部 shard 実行は追加 argv を拒否し、worker 数を `IZANAGI_TEST_NPROC` からのみ解決する。
  明示 `-n` は渡せない。
- D103 決定 (3) は既定を最大並列にするのがユーザー裁定に基づく方針であり「最大並列が最速だとは
  主張しない」と明記する。D532 は worker 数の増減を提案しないと定める。測定の解禁と既定値の
  再裁定は別の許可であり、親が後者を代行してはならない。

**却下した選択肢:**
- 分割せず 1 ノードで全 suite を走らせる — 本番と別の topology を測ることになり、
  結果を本番の既定値へ外挿できない。
- 2 ノード割当で shard 対を固定する — 内部 shard 経路で単一ノードのまま本番の量が測れるので不要。
- 分割前に測った単調性 (worker を減らすほど速い) を prior として設計に使う —
  並べ替えの着地で前提が変わっており、方向予測にも検出力の根拠にも使えない。
