## 実装内容

所有された3ファイルだけを変更しました。

- [patch C](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-a/patches/cicada-adaptive-counterfactual.patch:1)
  - cap 判定を `elapsed / clocks_per_us_ >= cap_us` へ変更。
  - `clocks_per_us_ == 0` なら更新判定を止める防護を追加。
  - `CCBENCH_BACKOFF_TRACE_TERMINAL_US`、既定値0、`#ifndef`、値域 `static_assert` を追加。
  - `start_time_`、`terminal_recorded_`、count-closed terminal event をすべて `#if BACKOFF_TRACE` 内へ追加。
  - terminal 後は controller 更新、LCG、割当、追加 event を止め、worker と `extime` は継続。
  - stdout trace を v3、正規化 schema を v4 とする出力へ変更。
  - patch 対象は `cmake/Options.cmake` と `include/backoff.hh` の2ファイルのみ。
- [patches README](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-a/patches/README.md:286)
  - option 表、cap、terminal、raw v3、schema v4、summary 契約を追随。
- [遷移テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-a/orchestrator/tests/test_dynamic_backoff_transitions.py:1090)
  - 実 patch 適用後ソース、実 C++ driver、実 `g++ -E -P` を使う検査を追加。
  - patch C の2-path集合、適用段階、stdout v3 pin を更新。

新しい patch identity は次のとおりです。

- `counterfactual_patch_sha256`: `b5649becded2ad62d015d94263b3e4b3e32f8c271892647e6567772c234dad5f`
- `patch_stack_sha256`: `790a6e7bfdb2b78ea1a05a242acbfeabbe16a07d3f30e6e6148909a7ac59fdb8`

## clocks_per_us_ の0経路

0になる経路は実在します。Silo は `DEFINE_uint64(clocks_per_us, 2100, ...)` を定義しますが、main は gflags のコマンドライン値を受理してから `chkArg()` を呼び、`chkArg()` には下限検査がありません。したがって `--clocks_per_us=0` が到達可能です。

count-window 経路では `check_update_backoff_at()` が即座に false を返し、terminal 側も0を拒否するため、新設した整数除算へ到達しません。

## trace の逐語書式

通常 event の raw stdout は次の順序です。

```text
IZANAGI_BACKOFF_TRACE v=3 seq=<N> tsc=<TSC> window_us=<US> window_commits=<COMMITS> trigger=<0|1|2> backoff_before=<B0> backoff_after=<B1> gradient_sign=<-1|0|1> step_us=<STEP> ceiling_us=<CEILING> ceiling_changed=<0|1> parity_branch=<-1|0|1> recommended_delta_sign=<-1|0|1> assigned_invert=<0|1> inversion_realized=<0|1> both_actions_feasible=<0|1> terminal_flush=0
```

terminal event は次の形です。raw `trigger=3` を unit B parser が `trigger="terminal"` へ写像します。

```text
IZANAGI_BACKOFF_TRACE v=3 seq=<N> tsc=<TSC> window_us=<US> window_commits=<COMMITS> trigger=3 backoff_before=<B> backoff_after=<B> gradient_sign=0 step_us=<STEP> ceiling_us=<CEILING> ceiling_changed=0 parity_branch=-1 recommended_delta_sign=0 assigned_invert=-1 inversion_realized=0 both_actions_feasible=0 terminal_flush=1
```

summary は次の順序です。

```text
IZANAGI_BACKOFF_TRACE_SUMMARY v=3 updates=<N> retained=<R> dropped=<D> flushes=<F>
```

- `updates`: 通常 event 数。terminal を含まない。
- `retained`: ring に保持された通常 event 数。
- `dropped`: ring 上書きで失った通常 event 数。
- `flushes`: terminal event 数。
- schema v4 の適格 run は `retained=updates`、`dropped=0`、`flushes=1`。
- terminal の `seq` は `updates` と等しく、全 event は0から連続します。
- unit B の正規化後 schema は `izanagi-dynamic-backoff-trace/v4`。既存 schema v3 は継続受理対象です。

## 新設検査と殺す変異

| 検査 | 赤にする1行変異 |
|---|---|
| `test_count_window_cap_comparison_is_overflow_safe` | `elapsed / clocks_per_us_ >= cap_us` を旧乗算式へ戻す |
| `test_patch_c_pins_trace_stdout_version_three` | raw event または summary の `v=3` を `v=2` に戻す |
| `test_terminal_deadline_static_assert_rejects_out_of_domain_values` | terminal 値域 `static_assert` の比較を恒真化する |
| `test_terminal_instrumentation_preprocesses_completely_out_of_trace_zero` | `terminal_recorded_` などを `#if BACKOFF_TRACE` の外へ移す |
| `test_terminal_is_recorded_once_and_remains_the_last_event` | `if (terminal_recorded_)` の防護を削除する |
| `test_terminal_does_not_update_backoff_advance_lcg_or_assign` | terminal handler 後の `return;` を無効化し通常更新へ落とす |
| `test_terminal_recorded_guard_precedes_all_terminal_eligibility_checks` | `return true;` を `return false;` に変えて再記録を許す |

既存の CMake default、universal definition、trace-disabled 前処理検査も terminal option と field を検査対象へ拡張しました。

## 実走結果

- `python3 tools/run_tests.py orchestrator/tests/test_dynamic_backoff_transitions.py -q`
  - `rc=16`
  - `qstat -Q` preflight failure。子テストは未起動。
- 契約で許可された自走 harness:
  - `PYTHONPATH=. python3 orchestrator/tests/test_dynamic_backoff_transitions.py`
  - test file 全体77件を実走。
  - 76 passed、1 failed。
  - 新設・改訂した patch構造、適用段階、24 compile variant、cap、terminal、LCG、trace-off前処理検査はすべて通過。
  - patch C は pin単独とpin+Aを拒否し、pin+A+Bだけを受理。
- 残る失敗:
  - `test_emitter_stdout_parses_with_the_real_parser`
  - unit B 未統合の `_parse_backoff_trace()` が raw v3、`terminal_flush`、`flushes` をまだ受理しないため。
- 制約 meta-test:
  - `test_patch_define_inventory_matches_condition_gate_registry`: 1 failed。所有外 registry に `BACKOFF_TRACE_TERMINAL_US` が未登録。
  - `test_counterfactual_specs_are_exact`: 1 passed、113 deselected。
  - `test_screening_condition_requests_cover_exact_define_specs`: passed。
- `python3 tools/check_codex_agents.py`: passed。
- `python3 tools/check_docs.py`: passed。
- `git diff --check`: passed。
- U+0300からU+036Fの検査: 検出なし。
- build、benchmark、性能計測: 実装済み・未実走。本unitの担当外。

## 受理・拒否挙動

変更前は raw v1/v2だけを出力し、terminal optionと末尾閉鎖がなく、巨大capを乗算していました。

変更後は以下になります。

- patch適用段階の受理集合は不変。
- terminal option欠落は `#error`。
- trace有効時の負値・非整数 terminal期限は `static_assert` で拒否。
- terminal期限0は従来どおりterminal無効。
- raw stdout v3では全eventに `terminal_flush`、summaryに `flushes`が必須。
- 期限後の最初のcount閉鎖だけをterminal化し、二度目のterminalとterminal後の通常eventを拒止。
- 現行unit B parserは新raw v3を拒否するため、統合前は意図的に赤。

## 所有外への波及

静的に確認した波及先です。

- unit B:
  - `tools/pegasus/probes/t2187_adaptive_const_probe.py`
  - 同 `.pbs`
  - `orchestrator/tests/test_t2187_adaptive_const_probe.py`
  - `orchestrator/tests/test_ccbench_spawn_sites.py`
  - raw v3 parser、trigger 3、terminal field、summary、schema v4、CMake引数の追随が必要。
- registry:
  - `orchestrator/campaign/condition_meaning_gate.py`
  - `orchestrator/campaign/screening_driver.py`
  - `orchestrator/tests/test_condition_meaning_gate.py`
  - `orchestrator/tests/test_screening_driver.py`
  - terminal define、inert値0、exact spec/defaultの追加が必要。
- unit C:
  - cohort 2解析器、plot、各consumer testはschema v4と新patch identityへの追随が必要。
- cohort 1:
  - `backoff_counterfactual_analysis.py` と既存成果物の旧patch hash、schema v3は歴史的束縛として変更してはいけません。
- `source_digest.py`:
  - allowlistは既に patch C の2対象を許可するため変更不要。
- patch hash consumer:
  - probe、plot、artifact identityの `counterfactual_patch_sha256` と `patch_stack_sha256` が更新対象です。

## 所有外なので触らなかったもの

- `common/runner.hh`: allowlist外であり、契約上禁止。
- patch A、patch B: 既存campaignと認証の束縛を保持するため。
- unit Bとunit Cの全ファイル: 所有分割外。
- condition registry、screening defaultsと各test: 必要な波及ですが所有外。
- `source_digest.py`: allowlist拡張が不要かつ禁止。
- `docs/`、凍結事前登録、cohort 1解析器: bytesと歴史的受理を保持するため。
- commit、git add、branch操作、push: 実施していません。

## 総括

実装: overflow-safe cap比較、trace限定count-closed terminal、raw v3/schema v4、READMEと実物検査を所有3ファイルへ実装。  
実走結果: 所有test fileは77件中76 passed、checkersとdiff検査はpassed。  
残っている赤: unit B parser未追随の1件と、所有外condition registry未登録のmeta-test 1件。