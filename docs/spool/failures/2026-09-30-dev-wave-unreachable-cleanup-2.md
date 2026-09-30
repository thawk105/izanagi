---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-unreachable-cleanup
seq: 2
---

## 新規

### {{F:ruled-rescue-not-executed}}. 裁定済みの救出が 9 日実行されず、台帳の喪失下界を過ぎた 2 object が消えた [手順漏れ]

- 事象: D2200 項 2 (2026-09-21) は `audit-20260921-*` 21 件を「AI が救出 ref を作って `rescued`」と裁定したが、実行 ([T-2829]) は持ち越しのまま 9 日経った。2026-09-30 に実行したとき `bebeb887d48d…` と `c2ae05befdbf…` の 2 件は `git cat-file` で不在だった (19:2x と 21:43 JST の 2 回)。台帳は両件を loose・喪失下界 9/23・9/21 と記録しており、下界の経過が通知 (`pending-ledger-entry` の deadline-passed) で見えていた。
- 根本原因: 救出の裁定と ref の作成が別手番に分かれ、ref の作成が「記帳の実行手番」として次の一手に積まれた。持ち越し項目は優先度 P3 の掃除として後回しになり、喪失下界は待たない。
- 恒久対応: 救出を裁定したら同じ手番で ref を張る (ref は working tree も main も変えず、D2065 のとおり費用が小さい)。記憶 `ruled-rescue-pin-immediately` に置いた。本 wave は捨て候補 130 件も分類前に固定したまま承認待ちにした (D1115 と md_1)。
- 再発検知: `python3 tools/check_branch_rescue.py --ledger-check` の `pending-ledger-entry` (deadline-passed) を、救出裁定済みの entry について 0 件に保つ。
