---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-22
wave: dev-wave-t2853-repro-package-estimate
seq: 2
---

## 再発

### F473

- **再発: 2026-09-22** — [T-2853] 再現パッケージ初段の段 4 で、段 3 相談 B の「D2160 保全系列の verifier.json が 0 B の走は 4 件」を、親が自前で打った awk の件数 3 で「誤り」と裁定した。awk は見出し 1 行の集計 log に `NR>2` を掛けており、先頭のデータ行 (`calib/fixed-10-balanced/extime-10`) を構造的に必ず落とす道具だった (本文の型 2「抽出器が端の要素を構造的に落とした」と同じ)。段 6 の read-only レビューが log の走別行を数え直して must-fix で逆転させ、insight `output/insights/2026-09-22/t2853-repro-package-estimate/README.md` §12 に erratum を書いた (段 4 裁定の逐語は保存)。子の数値指摘を覆す裁定の根拠にした自前の数を、母集合 (どの行から数えたか) を確かめずに使った点が本型の再発で、再発検知 (敵対レビューが親の数値を再現コマンドで確かめる) がそのまま働いた。
