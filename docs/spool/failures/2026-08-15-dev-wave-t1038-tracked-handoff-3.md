---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-t1038-tracked-handoff
seq: 3
---

## 再発

### F286

- **再発: 2026-08-15** — `docs/handoff/dev-wave-t971-swo-oracle-floor.md` が main へ landed し、
  背景 job の wave が起動時 rc=1 になった。`952fd45d` が main で直接撤去して応急処置している。
  2026-08-13 の `a3168d85` に続く 2 例目で、同 F が「次に wave が handoff を land した時点で
  同じ赤が再発する」と書いた予告どおりである。checker 側の恒久対応を本 wave で実装した。

### F155

- **再発: 2026-08-15** — 変異 harness を通さない素の焦点走
  (`python3 tools/run_tests.py orchestrator/tests/test_check_wave_startup.py -rf -q`) が
  login node で 3 回連続 rc=16 (`bounded scope の memory.max / memory.oom.group を走行中に
  attest できない`) になった。同じ command は 34 分前には成功しており、テスト結果ではない。
  `--force-dispatch` を足して計算ノードへ回したところ 95 passed / 0 failed で完走した。
  既存の恒久対応 (先例と同じ runner argv を使う) で足り、新しい手順は足さない。

## supersede 追記

- F286 **supersede: 2026-08-15** — 恒久対応の「未実施」は解消した。{{D:handoff-main-provenance}} に従い `_check_worktree_handoff` が main landed handoff を通し、untracked と不適格 index record を拒否する。再発検知は `orchestrator/tests/test_check_wave_startup.py` の 26 node (変異 M01 が完全集合で KILLED)。
