裁定 B を履行し、[test_coder_effect_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/tests/test_coder_effect_gate.py:151) から対象テストを decorator・5 parameters・本体ごと削除しました。production predicate、adapter、先行変更 2 枚、docs は変更せず、commit も作成していません。

静的確認:

- `git diff --check` 通過。対象ファイルの差分は 14 行削除のみ。
- 全 import・`_CATEGORY_PROBES` などの module-level 定数は残存テストから引き続き参照されています。
- Python の `compile()` による構文確認は成功。
- 指定された無条件ループ拒否側の姉妹テスト 4 件はすべて残存。
- 削除された parameter は 5 個なので、collected node は正確に 5 件減ります。
- production consumer の `p3_s4_loop.py` とその consumer test は削除対象 node を参照しておらず、受理集合も不変です。

波及検索では、削除 node の live な consumer、固定総 node 数を要求する meta-test、固定 file 集合への登録は見つかりませんでした。`test_plain_runner_coverage.py` は全 `test_*.py` の自走 harness を検査しますが、ファイルと `__main__` は残るため影響なしです。`test_pytest_collection_config.py` は収集範囲を検査しますが総 node 数は固定していません。削除 node は過去の T-316 mutation ledger 2 枚に履歴として残っていますが、これらを現 checkout と照合する live consumer はありません。

失われる検出力は、通常 `for`、range-for、data-dependent `while`、`while (0)`、空の通常 `for` を将来 gate が拒否するようになった場合に検出する 5 件です。直接の受け皿はありません。

実走は `python3 tools/run_tests.py orchestrator/tests/test_coder_effect_gate.py --collect-only -q` を試行しましたが、pytest 起動前に Pegasus dispatch の `qstat -Q preflight rc=1`、runner `rc=16` で停止しました。実行 node は 0 件で、緑・closed とは申告しません。

## 総括

- 削除結果: 対象テストを decorator・5 parameters・本体ごと完全削除。
- 減った node 数: 5 件。
- 波及: live consumer／固定 node 数 meta-test への影響なし。
- file 集合 meta-test: ファイルと自走 harness が残るため影響なし。
- production predicate／受理集合: 変更なし。
- 実走: runner `rc=16` のため未実走（実装済み・未実走）。
- commit・docs・adapter変更: なし。