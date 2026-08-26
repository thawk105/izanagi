---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-b10-overthrottle-grid
seq: 6
title: 静的 backoff 量が実際に効くことを保証し、計算ノードの取得経路を通した (コード + テスト、branch worktree-dev-wave-b10-overthrottle-grid)
---

## 本文

**投入前に 2 つの欠陥を捕まえた。どちらも実機で走らせて初めて分かる型である。**

**1. 静的量が効いていなかった。** `BACKOFF_FIXED` は CCBench 本体に無く patch が供給する
flag だが、この wave の driver は patch を当てていなかった。**CMake は未定義の `-D` を
黙って無視する**ので、そのまま投入すれば 29 の静的点がすべて stock 適応 backoff の測定になり、
過抑制の開始点もピーク位置も決まらない。診断指標は出るので既存の守りでは捕まらない。
**別 wave が同型を先に踏んで警告してくれたことで、4 時間枠を 3 本使う前に気づけた。**
族一般化の裁定は先に踏んだ wave が上げる (この wave は独立 2 例目)。

親が tracked 3 campaign を集計したところ**当時は効いていた** —
`BACK_OFF=1` の 7 点が binary も throughput も 7/7 相異で、ピーク位置は
`s1_expected_goldens.py` の `EXPECTED_BACKOFF` と完全一致した。
**保証していたのは driver ではなく起動時の作業ツリーの状態だった**という点が重要である。

対処は patch 適用に加えて**効いたことの正例検査**を置いた。「当てたから効いたはず」を
正例にしない。異なる要求量が異なる binary を生むことを固定し、計測を 1 点も始める前に
全点を build して相異を検査する。並行 wave が `CMakeCache.txt` 経由で書いて実機で止まった
(build cache は binary だけを publish し CMake の中間ツリーは残らない) ので、その形は避けた。
`nm` 等の外部 command も使わない — 計測起動を関数名で pin する在庫に当たるためである。

**2. 計算ノードは外部 network へ直結できない。** 依存の取得に proxy が要る。
`buildcache._fetchcontent_git_environment()` が `GIT_` 変数を落として git config を無効化するので、
**env 変数が唯一の経路**である。job body で export し、外部取得を伴う事実と取得先が pin されている
事実を receipt へ残した。

**受入所要台帳の網羅率**は別 wave が先に直して着地させていたので、台帳は main 側を採った。
この wave 固有の貢献である追加のみの更新経路 (`--add-only`) だけを残す。次に閾値を割ったとき、
凍結期待を書き換えずに越えられる。

## 次の一手差分

### carry

- [T-1940]
