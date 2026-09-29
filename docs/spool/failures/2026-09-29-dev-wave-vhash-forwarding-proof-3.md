---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-forwarding-proof
seq: 3
---

## 再発

### F810

- **再発: 2026-09-29** — dev-wave-vhash-forwarding-proof の wave 用 worktree で、`tools/dev_wave_submodule_init.py --worktree <ABS>` の 1 回目が **`ERROR: invalid-run: detail={'label': 'git', 'kind': 'timeout'}`** の rc=1 になった (本エントリの既載の再発はどれも `update-no-fetch` で、timeout を直接観測していなかった。今回は tool 自身が git の timeout を報告した)。2 回目は 57 秒かかって `runtime-io-failure: detail={'label': 'submodule', 'kind': 'update-no-fetch'}` の rc=1。その後 `git -c protocol.file.allow=always submodule update --init --recursive` を直接実行して rc=0 になったが、入れ子の googletest が未初期化 (`git submodule status --recursive` で `-`) のまま残り、同じ command の 2 回目で揃った。同時刻に別 session の `git worktree add` が 5 本並走し (load average 176)、本 wave の `git worktree add` 自体も 1 回目は checkout 中の `システムコール割り込み` (EINTR) で `fatal: cannot create directory` になって作り直した。既載の「`_GIT_TIMEOUT_S = 30` が submodule 段全体に配られ、高負荷の新規 worktree では収まらない」という候補と整合する観測である。恒久対応は引き続き未実施。
