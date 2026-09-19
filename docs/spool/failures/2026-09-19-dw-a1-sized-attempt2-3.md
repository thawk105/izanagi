---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-19
wave: dw-a1-sized-attempt2
seq: 3
---

## 再発

### F29

- **再発: 2026-09-19** (A-1 sized attempt-0002 投入 wave、near miss)。段 1 前の前提実測で、親は
  `run_submit` の先頭 (`_validate_attempt_root` まで) と `_run_submit_v3` の末尾だけを読み、「attempt root が
  durable base 直下の未存在 dir なら attempt-0002 は成立」と brief に書いた。実際には `_run_submit_v3` の中程で
  `_assert_no_prior_v3_bench_start` (規律 2 由来、commit abff80d1b) が先行 attempt の bench 到達を検出して
  qsub 前に拒否する。測定 (code 読み) は正確だったが、**読んだ範囲が命題 (submit が qsub に達する) を覆って
  いなかった** — 部分抜粋から経路全体の成立を一般化した型。検出は段 3 の相談 B (手順レンズ) で、親が durable base の
  現物 (`bench-go.json`・ready 3 本・bench-start 3 本) と既存経路の 1 回実走 (rc 2、副作用なし) で確定した。
  再発検知どおりレンズが機能したので実害はなく、1 attempt の投入手続は submit 層で停止条件に達した。
  一次資料は `output/insights/2026-09-19/a1-sized-attempt2/README.md` §2。教訓: 別 program の起動物を
  「成立」と書く前に、入口から副作用点 (intent 書込・qsub) までの gate 呼び出しを**関数境界で全列挙**する。
