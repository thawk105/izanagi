---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-mocc-g2-observation-results
seq: 1
---

## 再発

### F1

- **再発: 2026-09-20 (near-miss、単独 results 稿 wave `dev-wave-mocc-g2-observation-results`)** — 稿 §1.5 の B2〜B4 の `result.json` の
  `started_at` / `finished_at` を、B1 の実値と NQSV 要約から**推定**して書いた (B2 06:50:20 / B3 06:55:41 / B4 06:50:35 UTC。実値は
  06:50:16 / 06:55:37 / 06:50:29)。commit 前の機械照合 (job dir の使い捨て script が稿の全数値を一次資料から再抽出して突き合わせる、
  T-2674 の恒久対応) が捕まえ、実値へ直した。同じ wave で専用 handoff の節見出しの時刻も 2 回推定で書き (07:30 / 07:55、実測は
  07:24 以後 / 07:42 直前)、`date` の実測で訂正した。転写対象が「隣の block の値からの外挿」へ広がった顕在化。稿・README・insight
  には推定値は残っていない。恒久対応は memory (`timestamps-from-date-or-mtime-not-estimation`) から変更なし — 表の各 cell は
  現物 field から機械抽出し、機械照合を commit 前に必ず 1 回通す。
