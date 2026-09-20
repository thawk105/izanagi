---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-fig3b-arc-status
seq: 1
---

## 新規

### {{F:guessed-sha-in-git-ref-command}}. 40 hex の SHA を `rev-parse` の出力から写さず頭から推測で補完し、存在しない object を指す git 操作を投げた [捏造/幻覚] [手順漏れ]

- 事象: 2026-09-20 に独立 2 例。(1) [T-2790] wave で `git worktree add ... <sha>` の sha を短縮 sha から補完して存在しない object を
  fetch し、独立 clone を 1 回無駄にした。(2) 本 wave (fig3b) で変異用 clone の `git update-ref refs/heads/main <sha>` に推測の
  40 hex を書いて `nonexistent object` で失敗し、clone を作り直した。いずれも実害は clone 1 回の再作成で、成果物・判定は変わらない。
- 根本原因: 短縮 sha を見た後に 40 hex 引数を手で組み立てた (先頭 9 桁だけが本物で残りは埋め文字)。git は短縮 sha を受けるのに
  「40 hex 必須」という思い込みから補完した。
- 恒久対応: memory `worktree-discipline` (2026-09-20 追記「worktree add の sha は 40 hex を rev-parse から」) と
  `mutation-discipline` (update-ref 後の reset --hard)。行動規律: SHA を引数に書く command は、直前の `git rev-parse <ref>` の
  出力を逐語で写すか、短縮 sha をそのまま渡す (補完しない)。
- 再発検知: `nonexistent object` / `bad object` の失敗を見たら推測 SHA を疑い、`git rev-parse` の出力と比較する。
