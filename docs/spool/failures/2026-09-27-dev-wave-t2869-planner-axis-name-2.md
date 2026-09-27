---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-27
wave: dev-wave-t2869-planner-axis-name
seq: 2
---

## 再発

### F801

- **再発: 2026-09-27 (near miss、受入前)** — [T-2869] wave で base digest と fold dry-run のために `git checkout main -- docs/` で台帳を借り、
  `git checkout HEAD -- docs/` と main にだけ在る archive file の `rm` で戻したところ、その file が index に `A` のまま残った (`git status --short` で `AD` / `A`)。
  2 回とも (借用時点の main が 1 fold ずつ進み、残った file は `worklog-phase3-0927-1882-1884.md` と `worklog-phase3-0927-1885.md`) commit 前の `git status` で気づき、
  `git restore --staged` で外した。気づかなければ次の `git commit` が main の archive file を wave branch へ混ぜていた。根本原因は本項と同じく
  `git checkout <ref> -- <path>` が index と作業ツリーの両方を書くことで、`docs/spool/worklog/README.md` の復元手順が作業ツリーの除去しか書いていなかった。
  恒久対応: 同 README の借用手順へ、index から外す手順と `git status --short` が空であることの確認を足した。
