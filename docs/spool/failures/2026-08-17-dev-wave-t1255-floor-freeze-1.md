---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1255-floor-freeze
seq: 1
---

## 再発

### F140

- **再発: 2026-08-17** — 床値 v2 protocol の実 artifact を 1 件発行して commit した直後、
  焦点走 12 file が `test_real_seal_protocol_to_floor_official_core_e2e@real-repo` で赤になった。
  コードは 1 行も変えていない。**直前の段 6 敵対レビューは「発行後に赤くなる既存 node は 0 件」を
  file:line の根拠つきで断定していた** (index / resolver を直接読む node を横断検索し、
  該当 3 node がいずれも 2 件 index を許容することを示していた)。実測は 1 件だった。
  レビューの検索は「供給した protocol が admission で拒否される」形の破断を捉えられていない。
  **不可逆操作 (実 artifact 発行) の後の再走は、レビューの網羅断定があっても省けない。**
  本 wave では再走させて land 前に検出した (near miss)。

### F141

- **再発: 2026-08-17** — 同型の単一要素前提を床値 protocol の解決器で踏んだ。
  `resolve_current_floor_protocol` は「現行 env 契約に一致する record が exact 1 件」を要求しており、
  versioned artifact を 1 件発行した瞬間に候補が 2 件になって fail-closed した。
  こちらは偶然でなく D460 が意図した fail-closed だが、**成果物が増えるのは正常な運用であり、
  増えた瞬間に選択が止まる**という帰結は F141 と同じである。
  **F141 の再発検知が「実 repo を対象に同型の単一要素前提が他に無いことは静的に確認した」と
  書いていた点は、本 wave の実測で覆った。** 当時の静的確認は `next(glob(...))` という
  実装形を手掛かりにしており、「index を走査して exact 1 件を要求する」形は同じ族に見えていなかった。
  恒久対応は現行契約候補の中でだけ HEAD の ccbench pin で曖昧性を解く規則
  ({{D:floor-protocol-head-pin-disambiguation}}) で、変異 M10 が検出器になる
  (曖昧時に先頭候補へ倒す変異が 8 node に殺される)。
