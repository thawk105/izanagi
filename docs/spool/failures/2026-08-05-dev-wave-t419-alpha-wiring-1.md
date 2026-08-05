---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t419-alpha-wiring
seq: 1
---

## 新規

### {{F:self-stat-not-thread-stat}}. pin した thread ではなく thread-group leader を検査する設計を裁定した [説明と実装の食い違い]

- 事象: 親が段 1 brief の provisional 裁定 (P4) で「pin が効いたことを `/proc/self/stat` の
  走行 CPU で検査する」と書き、段 2 プランもそれを採用した。`sched_setaffinity(0, ...)` は
  呼び出し **thread** に作用するのに、`/proc/self/stat` は thread-group leader の stat である。
  worker thread から probe すると pin した thread ではない task を検査することになり、
  誤拒否になるか、leader が偶然 target 上にいると壊れた pin 検査へ偽の裏付けを与える。
- 根本原因: 非認証の因果実験 probe が単一 thread 前提で `/proc/self/stat` を読んでいたのを、
  前提ごと本番へ移そうとした。移植元の暗黙の前提 (単一 thread) を本番の実行文脈で再確認しなかった。
- 恒久対応: {{D:thread-self-stat-for-pin-check}} で `/proc/thread-self/stat` を正本とし、
  `test_current_processor_reads_thread_self_stat` が thread stat と leader stat に異なる
  processor を書いた fixture で leader 側を読むと落ちることを固定する。
- 再発検知: 上記テストに加え、pre 検査・post 検査を独立に消す変異 (M06a / M06b) が
  それぞれ単一の負例で kill されることを変異台帳で確認する。

### {{F:pin-check-gap-during-wait}}. 検査と観測の間に待機区間を挟み、検査済みの状態が崩れうる窓を作った [恒真ゲート]

- 事象: 段 5 実装は pin mask の exact 検査を `sched_setaffinity` の直後に置き、その後に最大 50 ms の
  interval 待機を挟んでから読んでいた。待機中に affinity が広げられても、pre/post の瞬間だけ
  target 上にいれば両検査を通り、exact pin でない snapshot が α として受理されえた。
  「検査した」ことと「観測時点でその状態である」ことがずれていた。
- 根本原因: 検査の位置を「状態を作った直後」で決め、「その状態に依存する観測の直前」で決めなかった。
- 恒久対応: {{D:thread-self-stat-for-pin-check}} で mask の exact 検査を待機の直後・観測の直前へ置く。
  `test_probe_alpha_rejects_affinity_widened_during_interval_wait` が、待機中に affinity を広げつつ
  走行 CPU は target を返す fake で拒否を固定する。
- 再発検知: mask 検査だけを消す変異 (M05) が、noop set の負例と待機中拡大の負例の 2 本で kill される
  ことを変異台帳で確認する。

## 再発

### F113

- **再発: 2026-08-05** — 方式 α の変異事前登録に偽 kill が 3 件あった。(a) CPU 集合 drift の負例が
  期待 CPU を欠落させており、集合一致検査を消しても直後の添字参照が `KeyError` になって赤いまま
  だった。(b) reader 外れ値の fixture が事前計算した target 列に従って高値を移しており、巡回を
  同一 CPU へ壊しても意味検査が落ちなかった。(c) 静穏正例の K ベクトルが完全一致していたため、
  「全 read の完全一致を要求する」過剰拒否変異を検出できなかった。いずれも段 6 の敵対レビュー 2 本が
  harness 走行**前**に指摘し、fixture を余分 CPU 追加・実走行 CPU 由来・帯内変動ありへ直してから
  走らせた。恒久対応どおりレビューのレンズに「その負例が赤くなる理由は 1 つか」を入れていたため
  1 巡を無駄にせずに済んだ。
