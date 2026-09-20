---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2804-provenance-timeout-contract
seq: 3
---

## 再発

### F1

- **再発: 2026-09-20 (near miss、2 件)** — [T-2804] wave の親が、(1) 段 4 裁定 `s4-ruling.md` §2 項 5 の終端行 field 名 `deadline_margin_s` を段 5 author の prompt へ**手打ちで再記述**して `deadline_at_margin_s` に書き換え、実装とテストがそのまま裁定と食い違った (段 6 レビュー B が must-fix、A が should として捕捉、fix1 1 巡で裁定の名前へ揃えた。受理集合・値・順序は不変で診断行の名前だけの差)。(2) handoff と brief の見出し時刻 4 件 (21:03 / 21:20 / 21:31 / 21:33) を `date` を叩かず推定で書き、job dir の file mtime (21:01 / 21:08 / 21:17 / 21:18) で訂正した (worklog・insight へ写す前に閉じた)。型はどちらも「一次資料から転写せず手で書き直す」で F1 と同じ。恒久対応は変更なし (memory `timestamps-from-date-or-mtime-not-estimation`) に加え、裁定の literal を子の prompt へ再記述せず「裁定 file が正本」と指し、必要な逐語は file から機械的に切り出す (memory `ruling-literals-in-prompts-point-to-the-file`)。
