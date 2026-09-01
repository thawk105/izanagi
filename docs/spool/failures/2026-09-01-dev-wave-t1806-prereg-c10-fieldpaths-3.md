---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1806-prereg-c10-fieldpaths
seq: 3
---

## 再発

### F67

- **再発: 2026-09-01** — 承認済み裁定 D967 の前提 (契約 JSON と判定器の変更で既存 campaign が
  `E1-stale` になる) を、親が段 1 brief の不変条件として書いた。**近因は F67 本文の
  「worktree の凍結写しを読んだ」ではない** — supersede した D1163 は親が読んだのと同じ台帳に
  在り、日付も D967 の翌日だった。欠けたのは「実装しようとしている裁定の前提が、
  後続の裁定に覆されていないか」を主題で検索する手順である。親は D967 の本文と実装は測ったが、
  D967 を supersede する裁定を探さなかった。段 3 の敵対レンズが独立コンテキストで
  `artifact_admission` の現行実装を読み、D1163 が当該拒否経路を撤去済みであることを
  突き止めて反証した。親は D1163 の本文・実装コメント・tracked `campaign.lock` 32 件のうち
  閉包 hash を持つもの 0 件を独立に実測して確認した。実装前に是正したため実害なし。
  F67 の恒久対応である起動 gate の `INFO:` 行は乖離 commit 数しか見ないため、この近因には効かない。
