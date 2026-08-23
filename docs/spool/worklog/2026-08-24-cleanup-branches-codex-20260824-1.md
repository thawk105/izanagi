---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: cleanup-branches-codex-20260824
seq: 1
title: cleanup-branches 全量棚卸しを実施し、既知 T-1000 の監査長時間化により安全側へ縮退した
---

## 本文

- `$cleanup-branches` の開始時 HEAD `4b53d1b7` で全量棚卸しを実施した。local branch は 45 本で ahead=0 が 28 本、ahead>0 が 17 本、worktree は primary を含め 37 本だった。検査・記録中に別 wave 2 本が land し、local main は `218a197d` へ前進した。
- 副 worktree はすべて本 Codex session が作成・所有したと証明できない foreign worktree で、13 本は locked、3 本は dirty だった。Codex overlay に従い全件を保持し、real prune も実行しなかった。`git worktree prune --dry-run --verbose` の preview は空だった。
- ahead=0 かつ unattached の候補は `_check` と `_localmain_sync` の 2 本だったが、必須の `tools/audit_dangling_commits.py --offrepo-root /work/1/SFC/tanab/dev-wave-jobs` が約 28 分・出力 0 bytes で完走しなかったため中断した。停止時は既知 [T-1000] と同じ実用時間問題に加え、off-repo 走査後の `_landed_reference_matches()` で共通 pattern ごとの `owner not in list` を反復していた。監査 rc 不成立として削除は 0 本に縮退した。
- remote branch 操作、push、worktree directory 削除、unlock、real prune は行っていない。

## 次の一手差分
