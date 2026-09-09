## 実装結果

許可された3ファイルだけを変更しました。

- [patch C](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix1/patches/cicada-adaptive-counterfactual.patch)
  - `BACKOFF_TRACE_TERMINAL_US` の欠落検査と値域検査を `#if BACKOFF_TRACE` 内へ移動。
  - terminal を記録した呼出しだけ更新を停止。
  - 以後は handler が `false` を返して controller・LCG・割当を再開。
  - `if (!terminal_recorded_)` で通常 trace event の追加だけを抑止。
- [patches README](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix1/patches/README.md)
  - terminal 後も controller が継続する実態へ更新。
  - terminal 0件・1件双方の summary 契約を明記。
  - 認証を「exact 2 cell から exact 4 cell への制御された拡張」と訂正。
- [遷移テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix1/orchestrator/tests/test_dynamic_backoff_transitions.py)
  - trace無効・terminal defineなしの実 header compileを追加。
  - terminal後の controller・LCG・割当再開とtrace閉鎖を実 `leaderBackoffWork` seamで検査。
  - emitter-to-parser結合をterminal 0件・1件の2正例へ拡張。

新しい identity は以下です。

- `counterfactual_patch_sha256`: `4c04caa89244d74aa542a204bed0befae45b13616113cc5d734570c3aae7d2ff`
- `patch_stack_sha256`: `14ac8f00798d1b317854643e133c0b58543106e9c693f5c556f8b13edb591082`

## 実走結果

`tools/run_tests.py` に焦点nodeidを渡した走行は `qstat -Q` preflightで `rc=16`、子test未起動でした。そのため契約で許可されたself-run harnessを使用しました。

- `PYTHONPATH=. python3 orchestrator/tests/test_dynamic_backoff_transitions.py`
  - 全79件
  - 78 passed、1 failed
  - 以下の変更nodeは通過:
    - `test_trace_zero_compiles_without_terminal_deadline_define`
    - `test_terminal_is_recorded_once_and_remains_the_last_event`
    - `test_terminal_call_stops_once_then_controller_lcg_and_assignment_resume`
    - `test_terminal_recorded_guard_resumes_controller_before_eligibility_checks`
    - `test_emitter_stdout_parses_with_the_real_parser[terminal-1]`
  - `test_emitter_stdout_parses_with_the_real_parser[terminal-0]`だけ予定どおり赤。
- `PYTHONPATH=. python3 orchestrator/tests/test_ccbench_spawn_sites.py`
  - 全44件、43 passed、1 failed。
- `PYTHONPATH=. python3 orchestrator/tests/test_condition_meaning_gate.py`
  - 全114件 passed。
- `PYTHONPATH=. python3 orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py`
  - 全17件、16 passed、1 failed。
- `python3 tools/check_codex_agents.py`: passed。
- `python3 tools/check_docs.py`: passed。
- patch A→B→Cの適用dry-run: passed。
- `git diff --check`: passed。
- U+0300からU+036F: 検出なし。
- CCBench production全build・benchmark・性能計測: 実装済み・未実走。担当外です。

## 残っている赤

- `test_emitter_stdout_parses_with_the_real_parser[terminal-0]`
  - fix-2のFX1で、raw v3のterminal 0件と`flushes=0`をparserが受理すれば解消します。
- `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
  - 実値34に対して期待33。fix-2のFX7で件数pinを34へ追随すれば解消します。
- `test_cohort2_literal_pins_are_independent_of_fixture_helpers`
  - fix-1によるpatch C hash更新への未追随。fix-3のFX5実装時にcohort 2のpatch C／stack identityを更新すれば解消します。

また、plot側のterminal 0件受理はfix-3のFX1担当です。現行plot testにはこの正例がないため、今回の実走上の赤には現れていません。

## testが殺す変異

| test | 赤になる1行変異 |
|---|---|
| `test_trace_zero_compiles_without_terminal_deadline_define` | terminal欠落検査を囲む`#if BACKOFF_TRACE`を`#if 1`へ変える |
| `test_terminal_is_recorded_once_and_remains_the_last_event` | `if (!terminal_recorded_)`を削除し、terminal後も通常eventを記録する |
| `test_terminal_call_stops_once_then_controller_lcg_and_assignment_resume` | 記録済みguardの`return false`を`return true`へ戻す。LCG・controller・backoffが停止して赤になる |
| 同上 | policy割当条件の`== 1`を`== 0`へ変える。terminal後のbackoffが期待値102から外れる |
| `test_terminal_recorded_guard_resumes_controller_before_eligibility_checks` | `return false`を`return true`へ戻す |
| emitter結合`[terminal-0]` | summaryの`flushes`出力を固定1にする |
| emitter結合`[terminal-1]` | terminal記録時の`++izanagi_backoff_trace_flushes`を削除する |

## terminal 0件のraw出力

```text
IZANAGI_BACKOFF_TRACE v=3 seq=0 tsc=100 window_us=100 window_commits=100 trigger=0 backoff_before=100 backoff_after=101 gradient_sign=1 step_us=1 ceiling_us=1000 ceiling_changed=0 parity_branch=-1 recommended_delta_sign=1 assigned_invert=0 inversion_realized=0 both_actions_feasible=1 terminal_flush=0
IZANAGI_BACKOFF_TRACE_SUMMARY v=3 updates=1 retained=1 dropped=0 flushes=0
```

## 所有外への波及可能性

- caller:
  - `external/ccbench/cc/{cicada,d2pl,ermia,mocc,mvto,oze,si,silo,ss2pl,tictoc}/transaction.cc`
  - `external/ccbench/cc/ss2pl/ss2pl.cc`
  - いずれも共有`leaderBackoffWork`を呼ぶため、trace有効時のterminal後状態が変わります。
- 共有fixture:
  - `POLICY_DRIVER_SOURCE`
  - `_policy_defines`
  - `policy_binaries`
  - `patched_sources`
- consumer:
  - fix-2: `t2187_adaptive_const_probe.py`のraw v3 parserとそのtest。
  - fix-2: `test_ccbench_spawn_sites.py`のdefine件数pin。
  - fix-3: cohort 2解析器とtestのpatch identity。
  - fix-3: plotとplot testのterminal 0件受理。
  - condition registry／screening defaultsは現状整合し、対応test 114件は緑。
  - cohort 1解析器の旧hashは歴史的束縛なので更新対象ではありません。

## 所有外なので触らなかったもの

- `tools/pegasus/probes/t2187_adaptive_const_probe.py`と関連test: terminal 0件parserはfix-2所有。
- `orchestrator/tests/test_ccbench_spawn_sites.py`: 件数pinはfix-2所有。
- cohort 2解析器・解析test・plot・plot test・plot README: identityとterminal 0件consumerはfix-3所有。
- `patches/cicada-adaptive-dynamic.patch`、`cicada-adaptive-params.patch`: 明示的な変更禁止。
- `common/runner.hh`、`source_digest.py`: allowlist契約上変更不要かつ禁止。
- `docs/`、凍結事前登録、cohort 1解析器: bytesおよび歴史的受理集合を保持。
- commit、git add、branch操作、push: 未実施。

## 総括

直した所見: FX2・FX3・FX6・FX8のfix-1所有部分を3ファイルだけで修正。  
実走結果: 所有test全79件中78 passed、関連meta-testは157 passed・2 failed、checkers通過。  
残っている赤: fix-2のparser／件数pinが2件、fix-3のpatch identity追随が1件。