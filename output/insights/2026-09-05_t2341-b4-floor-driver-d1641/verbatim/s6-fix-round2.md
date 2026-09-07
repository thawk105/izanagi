F3 を閉じました。対象 node は `finalize_floor` ではなく validator を直接呼び、因果 gate の完全な文言だけを期待します。[test_floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:2429)

静的確認:

- artifact の regular file、JSONL、record 数、header exact 検査を通過。
- session の ID/count、順序、metadata、status 閉集合検査を通過。
- forged record は exact fields、空 measurement arrays、null probe/binary、非空 dropped cause を満たし、`not_run_sample_dropped` に再導出される。
- status 再導出一致、fatal 未発生、先行 drop 不在まで通り、[因果 gate](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/campaign/floor_pair_driver.py:2296) だけが例外を送出する。
- gate を外すと dropped 0 / complete 0 の terminal exact 検査も通り validator が正常 return するため、`pytest.raises` が赤になる。下流 `_median` には到達しない。
- `git diff --check` 成功。commit は作成していません。

## 総括
- 変更 file: `orchestrator/tests/test_floor_pair_driver.py`、本巡 +5/-2 行
- 変更後 node: `test_not_run_sample_dropped_without_prior_failure_is_rejected`
- 自走結果: 175 passed / 0 failed、失敗 nodeid なし
- production file は本巡では 1 byte も変更していません
- fixture、terminal、他 node、所有外 file は変更していません