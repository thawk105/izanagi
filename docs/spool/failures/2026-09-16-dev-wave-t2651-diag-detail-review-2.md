---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2651-diag-detail-review
seq: 2
---

## 再発

### F945

- **再発: 2026-09-16** — 診断本文保持の敵対レビュー wave (docs と計測成果物のみ) の受入で
  2 回続けて同型が出た。attempt 1 は 2 件 (24,084 passed / 68 skipped / 2 error)、attempt 2 は
  1 件 (24,085 passed / 68 skipped / 1 error)。setup traceback の Git argv は既報と同一で、
  `git -C <wave worktree> ls-files --others --exclude-standard -z` の 30.0 秒 TimeoutExpired。
  同 file の単独再走 (`run_tests.py`、1417.nqsv) は **51 passed / 21.04 秒 / rc=0** で非再現。
  wave の変更は docs と計測成果物だけで、当該 fixture・probe・Git 呼出しは変更していない。
  **既報と違うのは負荷の水準である。** 既報の再発は load average 68〜110 の高負荷だったが、
  本 wave の attempt 1 投入時は load **20.59 / 25.90 / 46.33** (下降局面) と低かった。
  代わりに**同時に走る受入の待ち手が多かった** — wrapper を除いた実体 (`/proc/<pid>/comm` が
  `python3`) で attempt 1 投入時 **5 本**、attempt 2 投入時 **4 本**。赤の件数は 2 件 → 1 件と減った。
  同じ worktree で同 argv を単独で測ると、未追跡は **0 件**なのに wall **16.7 秒**
  (user 0.023 秒 / sys 0.817 秒) で、ほぼすべてが I/O 待ちだった。
  これは「負荷の数値より、同時に走る受入の本数 (共有 filesystem の競合) が効く」ことと整合するが、
  **2 点の観測であり因果の分離ではない。** 恒久対応は既報のまま変えず、timeout 拡大・stub 化・
  除外・hold 登録・gate 新設は行わず、`DW-O18` に従って受入を再走した。
