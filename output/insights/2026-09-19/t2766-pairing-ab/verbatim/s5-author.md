## 実装

所有の 5 file に実装しました。docs 編集・git 操作・commit は行っていません。

- [conftest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-unit-impl/orchestrator/tests/conftest.py:1788)：`_acceptance_pairing_opted_in`、`_pair_initial_distribution_units`、reorder と collection hook の witness 配線。
- [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-unit-impl/tools/pegasus/dispatch_compute.py:131)：tests task の allowlist に env を追加。
- [test_acceptance_schedule_order.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-unit-impl/orchestrator/tests/test_acceptance_schedule_order.py:1767)：G12、実 scheduler 配布検査、JUnit 転送、hold／選択集合／suffix 保全検査。既存テストの期待値は変更していません。
- [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-unit-impl/orchestrator/tests/test_pegasus_dispatch_compute.py:6260)：exact pin 更新と request 伝播テスト。
- [t2766_ab_analyze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-unit-impl/probe-t2766/t2766_ab_analyze.py)：独立 witness 検算、走表・対表、3 種の中央値、事前登録判定、JSON／Markdown 出力、`--selftest`。未追跡のままです。

## 検査と波及

`--selftest` は **PASS**。合成 JUnit／report／ledger による witness 正負例、隣接対、中央値、判定各枝、tip 不一致・欠落 shard・走数上限を検査しました。5 file の構文検査も成功しました。

pytest は **未実走**です。

- 指定の直接起動：`guard_bash` が拒否。
- `tools/run_tests.py` 経由の対象 2 file：`qstat -Q preflight rc=1`、runner rc=16、`child_started=false`。
- 追加 meta-test の試行も同じ起動前障害。実走 nodeid はありません。**passed 0 / failed 0 は未起動を意味します。**

制約検査候補として G4／G9、dispatcher の AST inventory、hold inventory、collection config、growth／flaky hold、real-repo serialization を洗い出しました。meta-test 試行の末尾 nodeid には余分な `.py` があり、再実行時の正名は `test_suite_conftest_does_not_wire_tmpdir_to_tmpfs` です。

静的検索では、reorder の既存直接呼出しは同テスト内に 8 箇所、ほかに G6／G10 の二引数 wrapper がありました。既定引数と A 側の二引数呼出しを維持しています。`TASKS["tests"]` の overlay consumer、exact pin、`hold_inventory` も確認しました。inventory は既存 key の静的投影で、変更不要です。

## 総括

上記 5 file の実装は完了、pytest による検証は未完了です。G1〜G12、dispatch テスト、追加 meta-test、変異 M1〜M6、実受入 A/B は未実走であり、closed とはしません。

A の現行挙動は、hold・shard 選択後の cost 順 reorder と identity 検査です。既存 option gate・identity 検査を変更せず、未設定／空文字について固定期待 collection、identity、marker、property、selected を検査する負例を追加しました。ただし一致の動的確認は未実走です。

既知の限界として、初期 3 item の worker の 2 個目は partner とは限らず、初期 2 item の worker の 3 個目も rest になり得ます。この反例を実 scheduler テストに明記しました。

実行制約：hook が直接 pytest 起動を拒否し、wrapper も dispatch 事前確認で停止しました。失敗試行が生成した `output/pegasus-dispatch/` の receipt 等は、保護 hook が退避を拒否したため残っています。