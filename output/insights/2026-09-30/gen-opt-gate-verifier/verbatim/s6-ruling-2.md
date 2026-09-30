# 段 6 裁定 2 — 生死確認 live-1 で見つかった D5 の欠陥と取り直し

- 実測: `runs/live-1/` (request 37910.nqsv、bnode010、2026-09-30 13:41〜13:50 JST、Elapse 547 s)。判定器 = wave 木 68bdbe41b (判定器の bytes は 7052d64d9 と同一)。U1 tip dcb9a41f3。要約は `summarize_live.py runs/live-1` の出力。
- 事前登録 (prereg.md §3) との照合: S = match、B = match (D1(b1) = B1 committed が両 workload で一致)、N = descriptive、**X = mismatch** (両 workload とも D1・D2a・D2b 全項 0、到達不能 0、発生条件あり、巡回 0 だが `D5 = fail` で certified でない)。
- 原因 (real、判定器の欠陥): `_gate_d5` の include 検査の正規表現が `#include "ycsb.hh"` しか受けず、実物の `cc/silo/ycsb_silo.cc` 18 行目 `#include "../../include/ycsb.hh"` を不成立とした。test の fixture が実物と違う簡略形だったため段 5・6 の test と review が見逃した (test double が production の形を写していない)。
- 処置: fix-u2c (Codex author) で include の path を `cc/silo/` から解決し `<root>/include/ycsb.hh` と同じ file のときだけ成立にする (照合は緩めない)。fixture を実物の形に直し、別 file に解決する include の負例を足す。
- 取り直し: 修正後の判定器を統合した wave 木から、4 条件を新しい run (live-2) で取り直す。live-1 の結果は当時の判定器 (D5 の欠陥あり) での事実として残し、一次資料に両方を載せる (規律 7)。X の live-1 の不一致は prereg どおり「不一致」と記録し、事後に一致へ書き換えない。
- 事前登録の変更はしない (D5 成立は元から X の期待に入っている)。
