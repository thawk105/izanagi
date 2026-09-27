## base での分類 (根拠 file:line)

base `ad114fba0` の `run_campaign` は `run_one_iteration` の 323 行にあり、**61 define すべて `proven-unreachable`** でした。`_benchmark_build_sinks` はこの呼出しを `campaign` sink として列挙します（[検査器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:947)）。`_sink_macro_inventory` は sink の `[genome]` を関数内の固定構成まで追い、scope 引数に依存しないため対象 macro を sink に含めません（同ファイル:2725）。その結果、`_sink_macro_reachability` が `proven-unreachable` と判定します（同ファイル:2753）。`coverage_for_sink` による `covered` でも、`_DEFERRED_GATE_MEMBERS` による `deferred` でもありません。

## 変更 file と要点 (file:line)

- [driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/campaign/p3_s4_loop_policy.py:319): 共通の計測オプションだけを helper に残し、`run_campaign` を stock（378 行）と候補（419 行）の各関数へ戻しました。候補の gate 後に計測する順序と、計測引数は維持しています。両 sink とも 61 件すべて `proven-unreachable`、未分類の失敗は 0 件です。
- [所有 test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-a/orchestrator/tests/test_p3_s4_loop_policy.py:438): stock の捕捉先を実際の `run_campaign` 呼出しへ移しました。stock flag、同一 attempt の abort rate、fitness の期待値は維持しています。

## 実走 (または未実走)

直接呼び出しで `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`、`test_define_sink_cross_product_has_no_unreviewed_ungated_member`、`test_define_sink_cross_product_t2520_certify_entry_removal`、`test_stock_genome_and_same_attempt_baseline` が通過しました。`check_codex_agents.py`、`check_docs.py`、`git diff --check` も通過しました。

`tools/run_tests.py` による pytest は `qstat -Q` の事前確認で rc=16 となり、子プロセスが起動しませんでした。**pytest としては未実走**です。

## 所有外への波及

`test_ccbench_spawn_sites.py` を含む所有外の file は編集していません。候補・stock・replay の呼出し元の変更もありません。

## 総括

R4 の 3 検査は直接呼び出しで通過し、driver の sink 分類は base と同じになりました。commit はしていません。