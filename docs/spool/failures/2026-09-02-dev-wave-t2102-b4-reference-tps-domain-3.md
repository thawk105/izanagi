---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2102-b4-reference-tps-domain
seq: 3
---

## 再発

### F810

- **再発: 2026-09-02** — wave worktree と fix 子 worktree の 2 回とも 1 回目が
  `update-no-fetch` で rc=1 になった。本 wave では**根本原因の候補を特定した**。
  `tools/dev_waves/git_state.py` の `_GIT_TIMEOUT_S` は 30 で、
  `update_submodules_no_fetch` はその deadline を submodule config の読取・URL 解決・
  `submodule update` の**全体**に配る。この repository の新規 worktree は checkout だけで
  数分かかるため (`git worktree add` が 19,754 file で 2 分を超える)、初回の
  submodule checkout が 30 秒に収まらない。同じ argv
  (`git -c protocol.file.allow=always submodule update --init --recursive --no-fetch`) を
  長い窓で走らせてから tool を再実行すると、work が済んでいるため即座に rc=0 になる。
  これは「2 回目で通る」という既知の観測とも整合する。**未確定な点も書く** — 本 wave は
  timeout を直接観測しておらず、生の errno も捕らえていない。tool の `DevWavesError` は
  失敗種別を潰すため、observed なのは「無制限の窓なら同じ argv が rc=0 で完走する」ことと、
  「その完走後は tool が即 rc=0 になる」ことである。恒久対応は引き続き未実施で、
  deadline を submodule 段だけ分離するか detail を厚くするかは裁定待ちである。
