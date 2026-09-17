---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2732-verifier-identity-rest
seq: 2
---

## 再発

### F106

- **再発: 2026-09-18** — [T-2732] wave。**変異 matrix の走行中** (baseline PASSED、E1 / N1 / N2 完了後) に、親が段 7 の準備として
  insight の逐語 file を wave worktree の `output/insights/2026-09-18/...` へ複製し、末尾空白検査のために `git add -N` (intent-to-add) を
  掛けた。`tools/mutation_harness.py` は次の変異の直前検査 `_assert_only_expected_dirt` (`git diff --quiet HEAD -- . :(exclude)<変異対象>`) で
  intent-to-add を「固定 HEAD 外の変更」として検出し rc=2 で中止した (変異対象 2 file は HEAD へ復元済み)。追加事実は 2 つ。
  (1) **書き込み先が `output/` でも harness の検査には掛かる** — 計測 job の dispatch 中に `output/` へ書く運用が通るのは job が投入時点の作業ツリーを見るためで、
  変異 harness は変異ごとに worktree 全体の tracked/index/untracked を固定 HEAD と照合する。(2) `git add -N` は「stage しない」つもりでも index を変える。
  復旧は index を戻して file を job dir へ退避 → `--resume` (sidecar を新 path へ複写、`--wrapper-attempt` を進める) で残りだけ走らせた。
  順序の固定 (走行前に記録を書き終える、走行中は repo 外だけで作業する) が対応であり、本 wave では insight README・fragment を job dir で下書きして
  変異完了後に worktree へ移した。
