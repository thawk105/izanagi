---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2665-cleanup-removal-pgroup
seq: 3
---

## 再発

### F300

- **再発: 2026-09-17** — wave worktree を `--source-repo` にした `mutation_worktree.py --plan-only` が
  `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` (rc=125、child_rc 0 = harness の
  preflight は緑) で落ちた。親は走行中に repo へ書いていない。本エントリの 2026-08-25 追補どおり、対象 commit を
  持つ独立 clone (`git clone --no-checkout` + submodule URL を local module store へ向けた
  `submodule update --init`) を `--source-repo` にして probe / final とも `shared_snapshot_matches=true` /
  rc=0 で完走した。追補を `docs/dev-wave/mutation.md` の DW-M05 へ 1 行 (123 bytes) 収容しようとしたが、L1.5 層
  予算が 9,696 / 9,696 bytes で満杯のため入らず、収容は D782 の最小増分を要する別 wave へ送った。
