---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2486-ssh-cgroup-equivalence
seq: 2
---

## 再発

### F37

- **再発: 2026-09-09** — [T-2486] wave の親が wave worktree を
  `timeout 300 git worktree add ... | tail -20; echo "rc=$?"` で作り、表示された `rc=0` は
  `tail` のものだった。実際は `timeout` の SIGTERM で checkout が殺され (rc=143)、
  **worktree directory ごと消えて branch だけが残っていた**。
  **検査ではなく状態変更コマンドで、しかも「消滅」が「成功」に見えた点がこれまでの再発と違う。**
  直後の `git worktree list` に対象が無いことで検出し、timeout 無しの detach で作り直した
  (負荷 53 のログインノードでは 22,955 file の checkout が 5 分を超える)。
  実害は約 6 分の空転だけで、偽緑の記録には至っていない。
  **恒久対応を `DW-O20` へ 1 行統合しようとしたが、byte 予算で入らなかった** — 同節が
  1066 bytes となり単節予算 1000 bytes を 66 bytes 超えた。安全義務を削って詰めることはせず、
  実体は memory `enterworktree-fails-on-symlinked-cwd` に置いた
  (timeout を掛けない・rc を pipe へ通さない・timeout 無しの detach と `tail --pid` で待つ)。
  上限の引き上げは求めていない。
