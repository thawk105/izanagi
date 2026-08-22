---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: worktree-dev-wave-t1479-known-violation-merge-authorship
seq: 1
---

## {{D:combined-diff-triviality-not-exit-code}}. merge commitの実装面著作判定は`--exit-code`でなくcombined diffの本文空判定で行う

**決定:** `_commit_paths()`のmerge分岐で、各parentとの非空diff交差 (候補path集合) が
実際に実装面著作かを判定する最終ステップは、`git diff-tree --cc --no-renames
--no-commit-id -p <commit> -- <path>` の出力 (raw bytes) が空かどうかで行う。
`git diff-tree --cc --exit-code` のrc値は使わない。

**理由:**
- 段2プランは`--exit-code`案だったが、段3敵対レンズが「`--exit-code`は自明性を反映しない」
  と指摘し、親が使い捨てrepoで実測したところ、**真に衝突を解消した (両parentと異なる内容の)
  mergeでも`--exit-code`は常にrc=0を返す**という欠陥を確認した。この案のまま実装していたら
  merge著作検出そのものが機能しなくなっていた。
- combined diffのcompaction (`--cc`) は「少なくとも1つのparentと一致するhunk」を省略する。
  したがって出力本文 (`-p`) が空 = 全hunkが省略された = どのparentとも異なる内容が無い、
  という関係は成り立つが、`--exit-code`はこの本文の有無と別のrc規約を持つため代用できない。
- raw bytesのまま比較しUTF-8 decodeしない設計にしたのは、実プロジェクト全履歴(1295 merge中
  241候補)で46件が`text=True`のUTF-8 strict decodeでUnicodeDecodeErrorになる別の実装バグを
  段6レビューで発見したため。日本語を含むcombined diffのレンダラがmulti-byte文字境界で
  出力を打ち切ることがある。

**却下した選択肢:**
- `git diff-tree --cc --exit-code` のrc判定 — 上記の通り常にrc=0を返すため不採用。
- combined diff出力を`text=True`でdecodeして比較 — 実データでUnicodeDecodeErrorが発生するため不採用。

## {{D:defer-preflight-fix}}. `_message_file_paths()` (commit前preflight) の同型修正は本waveの scope 外とする

**決定:** commit前の`--message-file`検査が使う`_message_file_paths()`は、`_commit_paths()`
と同じpairwise-intersection構造を持ち理論上同型の偽陽性を起こしうるが、本waveでは修正しない。

**理由:**
- `_message_file_paths()`はまだ存在しないcommitを対象にするため、判定には使い捨てcommit
  object (またはそれに類する一時構築物) の生成が要る。段6の敵対レビュー2本が独立に
  「`tools/audit_dangling_commits.py`の到達可能性監査へ副作用しうる」と指摘し、親が
  実装を読んで安全な隔離 (専用object store等) が未設計であることを確認した。
- 一方で、land/記録のrc判定に使われるのは`_commit_paths()` (post-hoc、commit確定後の
  監査) であり、本wave の修正だけで「known-violation台帳が新規に反復増加する」という
  ユーザー依頼の根本原因には対処できている。preflightの残存は「commit前の意図しない
  警告」に留まり、fail-closedな誤検出ではあるがland可否には影響しない。

**却下した選択肢:**
- 同一waveで両方修正する — 使い捨てcommit objectの安全な隔離設計は追加のplan/review
  サイクルを要し、規律5 (段階導入・盛らない) に反する。
- `_message_file_paths()`を`_commit_paths()`と同じロジックへ単純委譲する — 対象commitが
  未確定のためAPI形状が異なり、単純委譲では成立しない。
