---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1116-nonattrib-checker
seq: 2
---

## {{D:touch-not-sufficient-for-non-attribution}}. 受入赤の非帰属を「wave が test file を触っていない」で決めない

**決定:** 受入全走の赤について、`tested_main..wave_tip` の差分が当該 node の test file を
含まないことを、その赤が wave の差分に帰属しないことの十分条件として採らない。
非帰属の判定は D371 のとおり再実行で決め、差分 path の非接触は補助的な絞り込みにしか使わない。

**理由:**
- 単独 node 再走は全走 (分散走行) でのみ再現する赤を構造的に再現できない。原因が test file か
  否かは、この観測では区別できない。
- 実際に、wave が production code だけ、`conftest.py` だけ、共有 fixture だけ、pytest plugin
  だけを変更しても全走限定の赤を作れる。いずれの経路でも単独再走は tested main 側でも
  wave tip 側でも緑になり、test file は未接触のままである。
- 差分到達可能性の完全な写像 (import 閉包、fixture、plugin、subprocess、共有 filesystem を
  含むもの) は現 repo に存在しない。それが無い状態で非接触を非帰属の証明に使うと、
  「謳うだけで発火しない保証」になる。
- `git diff --name-only A..B` は tree の差だけを見るため、endpoint tree が同じなら空になる。
  空 path 集合を安全証明として読むと、履歴・commit identity に依存する赤を受理する。

**却下した選択肢:**
- 非接触を非帰属の十分条件として採る — 上記 4 経路が受理集合へ入る。受理集合を広げる方向の
  変更を、閉包になっていない述語で正当化することになる (規律 2)。
- 単独再走を N 回繰り返す — 分散走行の文脈を再現しないので観測が変わらず、費用だけが N 倍になる。
- 赤の test file 全体を再走する — 同 file 内の別失敗を帰属へ混ぜるうえ、cross-file の順序汚染と
  worker 間競合はやはり再現しない。
