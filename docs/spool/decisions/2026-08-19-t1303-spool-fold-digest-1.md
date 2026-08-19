---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: t1303-spool-fold-digest
seq: 1
---

## {{D:base-digest-independent-loader}}. `--base-digest` は `plan_fold()` と loader を共有せず独立させる

**決定:** `tools/spool_fold.py --base-digest` の worklog+archive ロードは、`plan_fold()` の
8-file 読み込みと共有 helper へ抽出せず、`--base-digest` 専用の独立 loader
(`_load_base_digest_sources()`, worklog.md + archive/worklog-*.md の2種類だけを読む) にする。
`plan_fold()` 自体は1行も変更しない。

**理由:** 段2 codex plan は「2 helper (read+decode をまとめて抽出) への共有化」を提案したが、
段3 敵対相談 (正しさ境界レンズ) が具体的な反例を示した — `plan_fold()` の既存コードは
「全 file の raw read を先に完了してから decode する」2段階構造であり、複数 file が同時に
壊れている入力に対するエラー優先順位はこの順序に依存する。提案どおり read+decode をまとめた
helper へ置換すると、この優先順位が (検出されない形で) 変わりうることが具体的なシナリオ
(worklog を不正 UTF-8、`docs/decisions.md` を欠落) で示された。

`--base-digest` は本来 `docs/decisions.md`・`docs/failures.md`・`docs/phase3.md`・
receipt・`tools/spool_fold.py` 自身・`tools/check_docs.py` を一切必要としない (digest 解決に
使うのは worklog + worklog archive だけ) ため、8-file 読み込みと共有する動機自体が薄い。

D128 (「台帳への書き込みを land lock 内の fold へ一本化する」) の精神 — 書き込み経路
(`plan_fold()`/`apply_fold()`) の挙動を不用意に変えない — を、読み取り専用の新機能を足す
場面にも延長した判断である。

**却下した選択肢:**
- 2 helper (`_load_canonical_worklog`/`_load_archive_worklogs`) への抽出 — 上記の
  エラー優先順位ドリフトのリスクを完全には除けなかった。「raw read 全件完了後に decode する
  2段階契約を明文化・テストする」代替案も検討したが、独立 loader よりリスクが高く得るものが
  小さいと判断した。
- 1 helper へ全部まとめる (worklog+decisions+failures+phase+receipt+spool_fold.py 自身+
  check_docs.py の8 file をまとめて読む) — digest 解決に不要な6 file を読む理由がなく、
  むしろ drift/blast radius を増やす。

**一般化の射程:** 既存の重量級関数 (書き込み経路を持つ・複数 file を特定順序で読む) が持つ
データの一部だけを読み取り専用の新機能で使いたい場面では、「共有 helper 抽出で DRY にする」
より「対象読み取り専用機能に必要な最小集合だけを読む独立 loader を新設する」を既定にしてよい。
特に既存関数のエラー優先順位・副作用順序が複雑な場合はなおさら。
