## 実装結果

裁定 B/E の範囲を実装しました。

- verifier に optional commit witness、both-or-none、構造化 `delta`、CLI flag を追加。
- pipeline に厳格 stdout parser、`_TraceRunResult`、YCSB allowlist、残骸 trace 拒否、batch 拒否、新 abort reason 3種を追加。
- S2 calibration から CLI witness を結線。
- critic、abort reason contract、renderer を追随。
- ladder は凍結 `verifier.json` を変更せず、raw stdout と `stats.txns` の外側 gate を追加。
- `_run_trace` の全既存 consumer・共有 fixture を属性アクセスへ更新。
- docs、`external/ccbench`、output、凍結成果物は未変更。commit・`git add` も未実施。CCBench pin は `d706650cdb31e442bef45b9b4216951d4fb40969` のままです。

主要箇所は [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:227)、[core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/core.py:18)、[model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/model.py:102)、[silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:832) です。

## Before / After

Before:

- verifier は末尾 txn・thread file 全欠落を検知できない場合があった。
- pipeline は stdout の commit counter、workload 種別、既存 trace 残骸を検査しなかった。
- batch commit の帰属不能や witness 異常を構造化できなかった。

After:

- witness なし API は判定、辞書 key・順序・値・notes、text 出力とも従来同一。
- witness 付きは、既存 integrity 条件に `len(dedup txns) == expected_commits` を純粋な連言として追加。
- pipeline は一意な非負整数の main/batch counter、batch 0、YCSB binary、空 trace_dir を必須化。
- mismatch 比較は verifier 一箇所だけで実施。
- ladder の凍結 JSON は不変のまま、実データ `480595 == 480595` を外側で照合。

## テスト状況

pytest は実行開始前に基盤側で停止したため、緑は主張しません。

試行した範囲:

- `orchestrator/tests/test_verifier.py` 全体
- 変更した9テストファイルの `--collect-only`
- `test_verifier.py::test_commit_count_witness_accepts_complete_trace`
- meta-test `test_mutation_harness.py::test_expected_node_must_exist_in_pytest_collection`

すべて `tools/run_tests.py` 経由で試行しましたが、`qstat -Q preflight rc=1` で停止しました。原因は sandbox 内での `NQSconnect: Can't create socket` です。local 実行も user cgroup の安全余裕が runner 最小予算を下回り選択されませんでした。

したがって、新設・改名テストはすべて「実装済み・未実走」です。対象には以下を含みます。

- verifier: tail-gap 反転、file 削除、完全 trace、構造化結果、byte/text 不変、既存 integrity 連言、CLI 4系統。
- pipeline: stdout 異常4系統、batch 非0、非YCSB、残骸 trace、新 reason 3種、tail-loss 結線、完全一致 COMMIT。
- ladder: mismatch fixture、既存実データ。
- critic/S8: witness 診断保持、non-serializable＋unclean、closed reason。
- S2: `--expected-commits` CLI 結線。

赤の内訳は pytest failure 0件、pytest 実行開始 0件です。基盤停止のみです。

代替確認は成功しています。

- `git diff --check`
- 変更20 Python file の AST parse
- 変更9 test module の import
- verifier shape・tail witness・strict parser・ladder実データの manual smoke
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

## 波及面

静的検索で更新した取り残し候補:

- `p3_s4_red._fixture_run_trace`
- `test_campaign` の通常・multipass fixture
- `test_s1_direct_comparison` と `test_s8b_oracle_driver` の共有 mock
- S2 calibration CLI
- critic、S8 abort reason consumer
- ladder driver/evidence fixture

意図的に変更していない面:

- ladder 内の witness なし `verify_trace_dir` 呼び出し
- coverage 系4 driver
- replay/guided に残る既存 witness なし WAL
- FN-2
- 同名だが別実装の coverage `_run_trace` 群

repo 外で private `_run_trace` の位置 tuple を利用する consumer があれば、`_TraceRunResult` の属性アクセスへの追随が必要です。

## 総括

裁定 B/E のコードとテスト実装は完了し、禁止対象には触れていません。ただし pytest と meta-test は Pegasus/sandbox 基盤障害で未実走のため、検証状態は closed ではありません。