---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2141-rejection-durability
seq: 3
---

## 新規

### {{F:mutation-harness-killed-leaves-mutated-tree}}. 変異 harness が外側から殺され、作業ツリーに変異を残したまま終わった [手順漏れ] [観測者効果]

- 事象: 変異 probe の走行中に session が終了し、`tools/mutation_harness.py` の process が消えた。
  復元されないまま `orchestrator/campaign/p3_b4_raw_record_producer.py` に最後の変異 (N10 の
  `fsync` 失敗時の切り戻し除去) が残っていた。待ち手の通知は「停止」としか言わず、
  台帳 `mutation-probe-ledger-2.json` は 9 件分が書かれていたため、通知だけを見ると
  「途中まで終わった走行」に見えた。
- 根本原因: harness の復元は signal handler で行うため、catch できない終了 (SIGKILL、
  process group ごとの teardown) では発火しない。DW-M05 は「signal 復元を fail-closed で
  強制する」とだけ書いており、この射程外があることを書いていなかった。
- 恒久対応: memory `mutation-harness-kill-leaves-mutated-tree` に、中断後は次の操作の前に
  `git status --porcelain` と `pgrep -f mutation_harness` を対で見て、変異が残っていれば
  `DW-O19` の `git checkout --` で復元する義務を書いた。**docs への収容は byte 予算に阻まれた。**
  D730/D782 の手順で既存記述の削減を試したが `docs/dev-wave/**` の L1.5 予算 9696 bytes に
  対して 228 bytes 不足し、独立 3 例に達しないため例外収容もせず、上限も引き上げなかった。
- 再発検知: 中断のたびに `git status --porcelain` と `pgrep -f mutation_harness` を対にして見る。
  台帳の件数や待ち手の rc を走行の生死判定に使わない。

## 再発

### F819

- **再発: 2026-09-03** — 段 5 実装子の投げ文に書いた作業ツリー path が親側の worktree で、
  投入先の author worktree と食い違っていた。今回は子が sandbox の read-only を自分で検出し、
  正しい author worktree へ書いたため実害は出ず near miss で止まった。
  親が `DW-O02` の現行版 (「prompt の repo path は投入先 worktree のもの」) を読んだのは
  段 5 投入後だった。

### F810

- **再発: 2026-09-03** — `tools/dev_wave_submodule_init.py` の 1 回目が
  `runtime-io-failure: update-no-fetch` で落ちた。fix1 の worktree では 2 回目で成功し、
  fix2 の worktree では 2 回連続で落ちて 3 回目で成功した。回数は固定ではない。
