## 変更

- [parser](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix2/tools/pegasus/probes/t2187_adaptive_const_probe.py:1285): raw v3 の terminal を 0 件、または末尾 1 件だけ受理。summary は terminal 件数から exact に導出。
- [metadata](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix2/tools/pegasus/probes/t2187_adaptive_const_probe.py:3110): cohort 1 の束縛へ `backoff_trace_terminal_us == 0` を追加。
- [parser tests](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix2/orchestrator/tests/test_t2187_adaptive_const_probe.py:1957): terminal 0、末尾 1、2 件、中間位置、summary 4 値、cohort 1 terminal 軸を検査。
- [spawn-site pin](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix2/orchestrator/tests/test_ccbench_spawn_sites.py:2911): 現物から再導出し `proven-unreachable=34`、同じ新 define が到達する s8b は `covered=38` に更新。未被覆失敗は 0。
- certification の表・gate・exact 4 cell は変更していません。

## 受理集合の復元と限定

raw v3 の `terminal_positions` を `[]` または `[len(events)-1]` に限定しました。

- terminal 0 件: `updates=retained=len(events)`、`dropped=0`、`flushes=0`
- terminal 1 件: `updates=retained=len(events)-1`、`dropped=0`、`flushes=1`

これにより terminal 値 0 の cohort 1 と legacy 診断走行が同じ raw v3 parser を通ります。raw v1/v2 の既存分岐は無変更で、その受理 test も通過しました。

緩めたのは terminal 0 件の受理だけです。正規表現、version と field の対応、terminal field の sentinel、非 terminal field、非空 event、連続 seq、単調 tsc、summary 全辞書一致は変更していません。terminal 2 件以上と末尾以外は引き続き拒否します。

## test が殺す変異

- `test_parse_backoff_trace_accepts_exact_v3_terminal_contract_only`: terminal ありの `updates` または `retained` を `len(events)` に変えると赤。
- `test_parse_backoff_trace_accepts_v3_without_terminal_and_pins_summary`: terminal 0 件を拒否する、`flushes` を 1 にする、または summary 比較を部分一致へ緩めると赤。
- `test_parse_backoff_trace_rejects_two_or_nonfinal_v3_terminals_at_position_gate`: terminal 位置 gate を削除、または複数 terminal を許すと赤。
- `test_counterfactual_artifacts_record_exact_preregistration_sha_only_on_exact_axes`: cohort 1 の `backoff_trace_terminal_us == 0` 条件を削除すると、terminal 値 1 の一軸 near-miss に SHA が付き赤。
- `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`: patch C から新 terminal define を除くと件数が 33、37へ戻り赤。

## 負例の到達確認

- terminal 2 件と中間 terminal の fixture は、正規表現、version、各 event field、連続 seq、単調 tsc を満たしています。例外文を terminal 位置 gate に限定して照合したため、別検査による先行拒否ではありません。
- terminal 0 件の summary 負例は、4 key を一度に一つだけ変更し、summary exact 検査の例外文まで到達しました。
- cohort 1 metadata 負例は terminal 値だけを 0 から 1 へ変更しています。

## 実走

`tools/run_tests.py` では次の 6 nodeid を指定しましたが、queue preflight `rc=16`、`child_started=false` でした。ラッパー経路では実装済み・未実走です。同じ nodeid は後続の自走 full-file 内で実走済みです。

- `test_parse_backoff_trace_accepts_v1_and_exact_v2`
- `test_parse_backoff_trace_accepts_exact_v3_terminal_contract_only`
- `test_parse_backoff_trace_accepts_v3_without_terminal_and_pins_summary`
- `test_parse_backoff_trace_rejects_two_or_nonfinal_v3_terminals_at_position_gate`
- `test_counterfactual_artifacts_record_exact_preregistration_sha_only_on_exact_axes`
- `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`

自走 harness の範囲と結果:

- `test_t2187_adaptive_const_probe.py` 全体: 125 passed
- `test_ccbench_spawn_sites.py` 全体: 44 passed
- `test_dynamic_backoff_transitions.py` 全体: 77 passed。実 emitter から実 parser の nodeid を含む
- cohort 1 analysis test 全体: 25 passed
- cohort 2 analysis test 全体: 17 passed
- plot consumer test 全体: 30 passed
- `check_codex_agents.py`、`check_docs.py`、`git diff --check`: passed
- 差分内の U+0300 から U+036F: なし

build、benchmark、性能計測は担当外のため未実走です。

## 所有外への波及

静的に確認した参照面です。

- caller: `t2187_adaptive_const_probe.pbs`、driver `main`
- producer 結合: `test_dynamic_backoff_transitions.py`
- cohort 1 consumer: `backoff_counterfactual_analysis.py` と対応 test
- cohort 2 consumer: `backoff_counterfactual_cohort2_analysis.py` と対応 test
- plot consumer: `plot_dynamic_backoff.py` と対応 test
- 共有 fixture: cohort 2 analysis と plot の synthetic trace fixture
- 運用参照: `admission_registry.json`、`test_hooks.py`
- spawn-site の AST 行番号 pin は parser を行数不変で直したため、3375 と 3749 のままです。

## 所有外で触らなかったもの

- `patches/cicada-adaptive-counterfactual.patch` と `test_dynamic_backoff_transitions.py`: fix-1 所有。既存結合 test の実走だけ行いました。
- cohort 2 analysis、plot、各 test、plot README: fix-3 所有。
- `t2187_adaptive_const_probe.pbs`: 所有外で、terminal 値の分岐は既に契約どおりでした。
- `docs/` と両事前登録: 凍結済みで編集禁止。
- handoff、worklog、commit、git add、branch、push: 実施していません。

最終的な変更 path は指定された 3 ファイルだけです。

## 総括

直した所見: FX1、FX4、FX7を修正し、certification の exact 4 cell は不変。  
実走結果: 所有 test 169件と所有外 consumer test 149件が passed。  
残っている赤: test failure はなし。受入ラッパーだけ queue infrastructure failure の `rc=16`。