---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: dev-wave-comsys2026-t2864-refs-sec7
seq: 2
---

## 新規

### {{F:defined-term-scope-conflict}}. 論文稿へ新しい事実を足したとき、同じ稿が別の節で狭く定義した用語 (certified) をその事実に使い、定義と食い違った (near miss) [手順漏れ]

- 事象: [T-2864] の ComSys 原稿の改訂 3 で、親が 7 節 (a) に「TPC-C の trace 1 本が判定器で certified に届いた」と書いた。原稿は概要と 3.3 節で certified を
  「YCSB の point read / write の trace 上の判定」と定義している。親は限界節の「判定器が担保するのは YCSB に限った」だけを「本稿の評価で」と限って食い違いを消したつもりだったが、
  定義文 2 か所は見なかった。段 6 の Codex read-only レビューが must-fix として捕まえ、7 節 (a) を「直列化可能と判定され」へ直した (land 前、成果物への実害なし)。
  同型の 1 例目は論文ストーリー 2026-09-23 版の段 6 must-fix (certified の保証範囲を YCSB に無条件で限る文が TPC-C 段 1 の certified と矛盾、worklog entry 1853)。
- 根本原因: 事実の範囲を広げる改訂で、食い違いうる箇所を「同じ事実を書いた文」だけから探し、その語を定義している文を探さなかった。
- 恒久対応: 新しい検査は足さない。memory `defined-term-scope-check-before-adding-facts` (稿へ事実を足す前に、使う判定語 (certified など) の定義文を稿の中で grep し、定義を越えるなら語を替える)。
- 再発検知: 段 6 の独立レビューで「定義語の全出現を定義と照合せよ」を検査項目に入れる (本 wave の焦点再レビューの検査 1 と同形)。
