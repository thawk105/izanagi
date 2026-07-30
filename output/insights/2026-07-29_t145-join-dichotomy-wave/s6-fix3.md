stale PGID ownershipの第3・最終修正を完了しました。

- 変更: [`test_dev_waves_integration.py`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145-author/orchestrator/tests/test_dev_waves_integration.py:1781)
  - TERM直前の所有条件を `process.poll() is None` のみに変更
  - KILL直前にも同じ確認を追加
  - parent-side primary exception単独ではgroup signalしない
  - exit raceは既存helperの `ProcessLookupError` 許容を維持
- 最終修正差分: `1 file changed, 3 insertions(+), 2 deletions(-)`
- HEAD→working tree: `1 file changed, 678 insertions(+), 26 deletions(-)`
- index: 開始時から不変の `+291/-24`
- status: `MM orchestrator/tests/test_dev_waves_integration.py`
- production、docs、output、index、commitは未変更

Focused pytestはrepo root cwdでrc=0でした。

- pure parser/control: 14 PASS
- isolation meta-test: 3 PASS
- long-path node: 1 SKIP
- 合計: `17 passed, 1 skipped`
- SKIP理由: `sandbox does not permit AF_UNIX bind through /proc/self/fd`
- このSKIPはgreenに含めていません

追加検査は `check_codex_agents.py`、`check_docs.py`、`git diff HEAD --check` がすべてrc=0です。

残るNOT_RUN:

- capability gate以降のreal socket roundtrip、実SignalRelay束縛、serve lifecycle、producer/parent mapping
- timeout時のTERM/KILL強制発火control
- M1〜M6 mutation
- M7: `NOT_RUN(design-invalid)`
- nested session一般containment

output size limit、専用FD、producer/parser追加control、M7 telemetry、nested session一般containmentは指定どおり実装していません。

## 総括

指定された第3・最終修正は完了です。残るblockerは実行環境のAF_UNIX capability不足で、real long-path経路がSKIPのため未実証であることです。mutationを含む段6全体の完了判定はまだ未完了です。