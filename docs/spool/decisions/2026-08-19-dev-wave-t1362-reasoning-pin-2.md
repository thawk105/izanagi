---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: dev-wave-t1362-reasoning-pin
seq: 2
---

## {{D:dev-wave-author-fix-docs-bound}}. 段5 author・段6 fix の reasoning を review/focus と同じ docs 権威導出へ拡張する — D266/D275 の「parse対象を広げない」判断を再訪成立により supersede する

**決定:** `tools/dev_waves/launch_authority.py` の `derive_launch()` を拡張し、
`stage in ("author", "fix")` を `DW-S06-A`/`DW-S06-C` と同じ機構で `docs/dev-wave/workers.md`
の `DW-S05-A` 節から `effort` を導出し `effort_authority="docs"` を返すようにする。fix は
author と同一の section/value を再利用し (`DW-S06-B` の全文継承契約どおり)、fix 専用の
docs 節・正規表現は新設しない。`tools/codex_worker_launch.py`・`tools/dev_wave_codex.py` の
受理集合を review/focus/author/fix の4stageへ拡張し、`tools/check_docs.py` に
`DW-S02`/`DW-S03`/`DW-S06-A`/`DW-S06-C` と同型の `DW-S05-A` exact-pin を追加する。
これにより、caller (dev-wave親セッション、または将来の別 runner) が author/fix の codex
起動へ `--reasoning` を明示指定すること自体を構造的に禁止する。

**本決定は D266 (2026-08-10) の「段5のpin拡大は見送りで終端、再訪条件は当該節のdriftの実測」
という記述と、D275 (2026-08-11) の「parse対象は DW-S02/DW-S03/DW-S06-A/DW-S06-C の3節だけ、
DW-S05-A は parse しない」という決定、および D275 が却下した選択肢「段5のDW-S05-Aもparseする
— 見送り裁定の射程を侵し節書式を事実上凍結する」を、当該箇所に限り supersede する。**
両決定のその他の記述 (model導出・sandbox非導出・権威snapshotの契約等) は不変。

**理由:**
- 2026-08-18 /rulings 全件第8回 (worklog entry 671) が、D266/D275 の見送り根拠だった
  「実害が観測されていない」という前提を実測で覆した — docs を `max` と明記した後も、
  runner (dev-wave launcher/dispatcher の caller 側実引数) が `high` を渡し続ける事例が
  観測された。D266 自身が明記した再訪条件 (「当該節の drift の実測」) が、docs 文言自体の
  driftではなく caller 側の実引数 drift という形で成立した。
- 機械強制の対象を「reasoning のみ」に絞るのはユーザー裁定 (entry 671) の文言どおりであり、
  sandbox の docs-bound 化は scope 外として見送る (D275 の当該部分は不変)。

**却下した選択肢:**
- **check_docs.py 側だけで author/fix の reasoning=max を保証する** — docs テキストの exact-pin
  (D223/D243/D514 と同型) は「docs が max と書いてあること」しか保証せず、caller が実引数で
  別の値を渡す経路 (今回観測された実害そのもの) を塞がない。launcher/runner 側 (このwaveの
  実装対象) での機械強制と併用が必須。
- **fix 専用の docs 節・正規表現を新設する** — `DW-S06-B` が「段5の実装子契約を全文継承する」と
  既に定めており、fix だけ別の権威を持たせると第二の権威になる。
- **旧 (T-1362以前) の author/fix receipt の後方互換を無視し schema_version を bump する** —
  `check-receipt` は repo 内に自動呼び出し元が無い手動フォレンジック専用 CLI であり、
  呼び手ゼロの経路に備える schema 移行は規律5 (段階導入/盛らない) に反する。構造検査を
  `len(sections) not in (3, 4)` と `effort_authority in ("docs", "unbound")` の許容へ緩め、
  意味検査 (`_audit_receipt_value` の commit 由来再構成との厳密一致) は変更しない対応で十分。
