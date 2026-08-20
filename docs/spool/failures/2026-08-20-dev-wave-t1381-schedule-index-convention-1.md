---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1381-schedule-index-convention
seq: 1
---

## 再発

### F174

- **再発: 2026-08-20** — [T-1381] wave の段6 post-change 変異再検証で、実装子 (Codex
  role=author) の未 commit docstring 変更が乗った tree に対し `git status --porcelain`
  の非空確認を怠って `git checkout -- <file>` で復元し、実装子の成果も巻き戻った。
  直後の `git diff --stat` で対象 file が消えていることを検知し、直前に取得済みの
  `git diff` 全文から docstring 2 箇所を Edit で verbatim 再現して完全復元した
  (復元後 diff が元の diff と byte 一致、test 再走で確認)。実害なし。F174 の恒久対応
  (「親が実編集 probe を行う前に `git status --porcelain` が空であることを確認する」
  「dev-wave 入口の `DW-O19` 条件へ『親の probe でも成立する』ことを明記する」) が
  未だ `DW-O19` 本文へ反映されていないことが 2 回目の再発で裏付けられた。
