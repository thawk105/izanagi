---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2067-exact-launch-validated
seq: 3
---

## 再発

### F350

- **再発: 2026-09-17** — 書き込み先は同じ (`output/insights/` の逐語複製 13 file) だが、落ちた検査は変異
  harness ではなく**受入 wrapper (`dev_wave_wait.py acceptance`) の走行後 clean-tree 検査 (`postrun-clean`)**で、
  rc=70・受領証なしになった。child の test 自体は完走 (2 failed / 24401 passed、赤は別原因で fix 済み) していたので、
  失われたのは受入 1 走分 (11 分) と再走である。親は「走行中に書いてよいのは `output/` 配下だけ」という
  dispatch の source identity の規則を受入 wrapper にも当てはめてしまった。**受入・変異を問わず、木を走行後に
  検査する wrapper が走っている間は、その worktree へ何も書かない** (逐語の配置は走行の終端後か、記録 commit の中で)。
