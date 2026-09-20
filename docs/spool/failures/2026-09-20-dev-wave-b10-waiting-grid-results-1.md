---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-b10-waiting-grid-results
seq: 1
---

## 再発

### F1

- **再発: 2026-09-20 (near-miss、単独 results 稿 wave `dev-wave-b10-waiting-grid-results`)** — B-10 待ち方 grid の results 稿で、
  (1) §1.3 / §3 の「3 workload は別 job・別 node・別日」を record・受領証でなく記録 insight (`output/insights/2026-09-05/t1905-b10-report/README.md`
  §2) の同文から転写した。一次資料では write-heavy の 45 record に `execution_host` が無く (`not-recorded-legacy-v2` は report driver の射影)、
  受領証・job 結果にも host が無いので、別 node かは確定できない。(2) 題名と §2.7 で D1678 / insight の要約「内側 (32) か境界を跨ぐ (4)」を
  「内側か境界上」と言い換え、境界を跨ぐ 4 cell の区間の一部が等価域 ±3.0% の外にある事実 (例: write-heavy μ 2 の区間 [−3.29%, +4.78%]) を
  弱めた。(3) §2.6 の説明文「μ が大きいほど abort 率が下がり throughput が下がる」は表の値に当たらず書いた一般化で、write-heavy の
  throughput は μ 2 → 5 で上がる (最大は μ 5 または 10)。3 件とも段 6 の独立 read-only レビューが must-fix で捕まえ、凍結前に一次資料の値へ
  直した (実害なし。稿・README・insight に誤りは残っていない)。親の機械照合 (稿の 135 行の表・54 対差・36 cell の効果と区間・sha256 を
  一次資料から再計算) は数値を全件一致させていたが、**数値を説明する散文の量化 (「別 node」「境界上」「単調に下がる」) は照合の射程外**だった。
  転写対象が「記録 insight の要約文の無批判な継承」と「表を見ずに書いた単調性」へ広がった顕在化。恒久対応は memory
  (`verbatim-projection-cut-by-heading-not-line-range` / `timestamps-from-date-or-mtime-not-estimation` と同じ族) から変更なし —
  散文の量化 (「すべて」「単調」「別 X」「上」) は書く前に表・record から機械で確かめ、要約文は一次資料の field 名 (`equivalence_relation`
  の値、`execution_host` の有無) で言い直す。段 6 の独立レビューは docs-only でも省かない (`DW-C00`)。
