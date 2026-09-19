---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-19
wave: dev-wave-t2288-floor-pair-w1
seq: 2
---

## 再発

### F1

- **再発: 2026-09-19 (near miss)** — [T-2288] (b) の親が、repo 外 handoff の段 1 brief と段 4 裁定の見出し時刻を
  `date` で採らず会話の経過感覚から推定して書き (21:35 / 21:36 JST)、実投入の開始 (rr95 の launcher 開始
  `submit-rr95-w1.meta` = 21:32:09 JST、`submit-receipt.json` の `prepared_epoch` 1789821131 = 21:32:11 JST) より後の
  値になった。段 6 の read-only レビューが「事前判断と事後転記を区別できない」と指摘。brief・裁定を書いた実時刻は記録されて
  おらず handoff は版管理外なので、「brief は同 handoff 内に記録した `git rev-parse main` の `date -u` 出力 12:27:09Z より前、
  裁定は dry-run の meta 21:31:27 JST の後・21:32:09 JST の前」という順序は親の操作列の申告であって証拠から独立には確定
  できない (焦点再レビューの指摘)。handoff の見出しに erratum を付けて訂正した。2026-09-17 の [T-2491] で同じ型を踏み memory
  `timestamps-from-date-or-mtime-not-estimation` に恒久対応を書いたばかりで、これは知識の欠落ではなく既知規律の
  不適用による再発である。転写でも推定でも起きる (`日付` から `時刻` へ対象が広がった顕在化は 09-17 と同じ)。
  一次資料は `output/insights/2026-09-19/t2288-floor-pair-w1/README.md` の段 6 節 (所見 3) と同 dir `verbatim/s6-review.md`。
