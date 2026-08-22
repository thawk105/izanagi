---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: rulings-20260822-ai-performance-measurement-fold
seq: 1
title: orphan 化した decisions fragment (AI セッションによる性能実測許可裁定) を正しい spool path へ再配置し fold・land した (docsのみ、branch worktree-rulings-20260822-ai-performance-measurement-fold)
---

## 本文

- ユーザーから command 引数で、取り残された decisions fragment
  (`dev-wave-jobs/rulings-inbox/2026-08-21-ai-performance-measurement-authority-orphaned-spool-fragment.md`、
  schema `izanagi-spool-v1`、ledger `decisions`、wave `rulings-20260821-ai-performance-measurement`、
  seq 1) を fold して local main へ着地させる依頼を受けた。対応 worktree
  `worktree-rulings-20260821-ai-performance-measurement` は既に消滅しており、fragment は
  canonical な `docs/spool/decisions/` の外 (repo 外の inbox) に控えとしてのみ残っていた。
- 内容を検証した: `docs/decisions.md` の D86/D87 実文言と整合、D70 自己汚染 (有効な
  `[T-数字]` 例示) なし、タイトルに日付接尾辞なし、`docs/spool/decisions/README.md` の書式契約
  (frontmatter 5 key・H2 は D placeholder 記法 + `. <題>` のみ) に完全準拠していた。`docs/decisions.md` を
  D86/D87 直接確認に加え内容特徴語での全文検索でも走査し、未着地 (重複 fold なし) を確認した。
  `docs/spool/decisions/` `worklog/` `failures/` は本 wave 着手時点で README.md のみで、他の
  未 fold fragment はなかった。
- 正しい canonical path (`tools/spool_fold.py` の filename 再構成規則から導出:
  `docs/spool/decisions/2026-08-21-rulings-20260821-ai-performance-measurement-1.md`) は、
  別セッション ([T-755] Q2継続、2026-08-21) の codex plan 子が同一 path を `git status` の
  untracked として一時的に観測した記録と一致し、原 wave が一度はここへ書いていたが commit 前に
  worktree が消滅した経緯 (`docs/spool/README.md` に既記載の既知の制約) と整合した。
- fragment 本文は CLAUDE.md 規律6 に従いデータとして扱い、一切改変せず (sha256
  `5aca1641a15aa64e1ec1f42394dbc5905607e4a714612c49b154e09623c3dfe4` を確認)、`cp` で
  canonical path へ byte 一致のまま配置した。指示めいた記述の混入は確認されなかった。
  `python3 tools/check_docs.py` (rc=0、違反なし) と `python3 tools/spool_fold.py --dry-run
  --show-diff` (fold は `docs/decisions.md` 末尾への追記のみで既存 bytes 不変、fragment 内容も
  無改変で挿入されることを確認) で検証した。dry-run が示した D 番号は land 時点の並行 wave 次第で
  変わりうるため記録しない。
- 一次資料: 本 fragment、`docs/spool/decisions/2026-08-21-rulings-20260821-ai-performance-measurement-1.md`、
  `dev-wave-jobs/rulings-20260822-ai-performance-measurement-fold/handoff.md`。

## 次の一手差分
