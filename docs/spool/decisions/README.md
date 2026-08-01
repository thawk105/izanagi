# decisions fragment

`docs/decisions.md` へ追記する設計判断。共通規則は `docs/spool/README.md` を正本とする。

本文の H2 は**すべて** `## {{D:slug}}. <題>` の形でなければならない。1 fragment に複数の D を置ける。

```markdown
---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-02
wave: dev-wave-parallel-docs-spool
seq: 2
---

## {{D:parallel-doc-spool}}. 台帳記録を fragment + fold にする

**決定:** canonical 3 台帳は fold だけが変更する。wave は `docs/spool/` へ fragment を書く。

**理由:**
- 採番は統合の瞬間にしか確定しない (D70 決定 5)。fold はその瞬間を機械化したものである。

**却下した選択肢:**
- wave 中の先行採番 — 予約とみなせないため衝突が残る。
- `docs/tmp_*` — 破棄可能と誤読される。未 fold fragment は正本である。
```

## 規則

- **題の末尾に `(YYYY-MM-DD)` を書かない。** canonical の日付は fold が実行時点で付ける。
- D 番号は書かない。`{{D:slug}}` だけを書く。
- 同じ wave の worklog / failures fragment からは `{{D:slug}}` で参照できる。
- 既存の D を参照するときは実番号 (`D118` 等) で書く。
- 本文の書き方 (決定 / 理由 / 却下した選択肢) は `docs/decisions.md` 既存エントリに合わせる。
- D70 の自己汚染を避けるため、決定本文に**有効な `[T-数字]` を例示しない**。
