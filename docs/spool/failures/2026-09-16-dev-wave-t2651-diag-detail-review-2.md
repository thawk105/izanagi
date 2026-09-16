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
  テストが走った 4 回すべてに同型が出た。attempt 1 は 2 件 (24,084 passed / 68 skipped)、
  attempt 2 は 1 件 (24,085 passed)、attempt 4 は 13 件 (24,072 passed、別に F976 が 1 件)、
  attempt 6 は 2 件 (24,117 passed)。setup traceback の Git argv は既報と同一で、
  `git -C <wave worktree> ls-files --others --exclude-standard -z` の 30.0 秒 TimeoutExpired。
  単独再走は 1 file で **51 passed / 21.04 秒 / rc=0** (1417.nqsv)、2 file で
  **269 passed / 111 秒 / rc=0** (1565.nqsv) といずれも非再現。
  wave の変更は docs と計測成果物だけで、当該 fixture・probe・Git 呼出しは変更していない。
  **既報と違うのは負荷の水準である。** 既報の再発は load average 68〜110 の高負荷だったが、
  本 wave の投入時 load は 20.59 / 25.90 / 46.33 (attempt 1)、29.70 / 24.85 / 24.80 (attempt 4)、
  50.85 / 39.64 / 35.14 (attempt 6) と低く、attempt 6 の終了時は 15.64 / 14.42 / 23.66 だった。
  代わりに**同時に走る受入の待ち手が多かった** — wrapper を除いた実体 (`/proc/<pid>/comm` が
  `python3`) で各 attempt の投入時に 4〜5 本。
  同じ worktree で同 argv を単独で測ると、未追跡は **0 件**なのに wall **16.7 秒**
  (user 0.023 秒 / sys 0.817 秒) で、ほぼすべてが I/O 待ちだった。素の走査が既に timeout の
  半分を使っているので、共有 filesystem に受入 4〜5 本分の競合が乗ると 30 秒を跨ぐ。
  これは「負荷の数値より、同時に走る受入の本数が効く」ことと整合するが、**因果の分離ではない。**
  恒久対応は既報のまま変えず、timeout 拡大・stub 化・除外・hold 登録・gate 新設は行わず、
  `DW-O18` に従って受入を再走した。attempt 3 は post-claim merge の競合 (別 wave が同じ
  DW-M07 是正を先に着地)、attempt 5 は postcheck の競走 (merge 中に main が進んだ) で、
  どちらもテストは走っていない。

### F976

- **再発: 2026-09-16** — 同 wave の受入 attempt 4 で
  `test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module`
  が setup error になった。本文は `real-repo lock deadline exceeded; fails-closed: resource=parent
  mode=write`、`holders=` は READ 2 本 (pid=4040008 / pid=4039887)、junit の `time` は **245.041 秒**で
  既報とほぼ同値。投入時 load は 29.70 / 24.85 / 24.80 で既報の表 (73〜117) より低く、
  同時走行の受入は wrapper 除外後で 4 本だった。単独再走は 2 file で 269 passed / rc=0 と非再現。
  当座の運用 (下降局面かつ 1 分値 50 以下で 1 回投げる) を満たしていたにもかかわらず出ており、
  **load の閾値だけでは避けられない**ことの 1 点になる。恒久対応は既報どおり未実施のまま、
  機構側の対処は決めていない。
