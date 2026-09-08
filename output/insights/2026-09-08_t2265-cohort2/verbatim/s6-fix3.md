## 実装結果

- FX1: [plot_dynamic_backoff.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix3/tools/plotting/plot_dynamic_backoff.py:749) で schema v4 の terminal 0 件または末尾 1 件を受理し、0 件時の summary を exact 検査するよう修正しました。
- FX5: [cohort 2 解析器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix3/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:41) に aggregate stack SHA を pin し、top-level と全 row で検査します。
- FX8: [解析テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix3/orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py:397) を、raw v3 stdout を実 producer parser に通してから解析器へ渡す形へ変更しました。
- FX9: [plotting README](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-fix3/tools/plotting/README.md:188) に schema v4、exact grid、summary、identity、観測長の入力条件を追記しました。cohort 2 の出図には観測長 6 秒の performance JSON が6〜7本必要で、本 wave は未計測であることも明記しました。
- CLI mode は追加していません。commit、git add、branch 操作、push も行っていません。

## 実走結果

pytest の実走 nodeid は 0 件です。

次の2ファイル全体を `tools/run_tests.py` で起動しましたが、`qstat -Q` preflight に失敗し、`rc=16`、`child_started=false` でした。

- `orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py`
- `orchestrator/tests/test_plot_dynamic_backoff.py`

したがって、両ファイルの全 nodeid は実装済み・未実走です。collect-only も同じ理由で未実行でした。直接 pytest は repository の実行規律に従い実施していません。

実走できた静的検査は以下です。

- `python3 tools/check_codex_agents.py`: passed
- `python3 tools/check_docs.py`: passed
- `git diff --check`: passed
- 変更した4 Python file の AST parse: passed
- 所有5ファイルの U+0300〜U+036F scan: 0 件

## FX1 の受理集合

緩めた条件は schema v4 の terminal 件数だけです。

- terminal 0 件: `updates = retained = len(events)`、`dropped = 0`、`flushes = 0`
- terminal 1 件: 従来どおり末尾限定、`updates = retained = 通常 event 数`、`dropped = 0`、`flushes = 1`
- terminal 2 件以上または途中の terminal: 引き続き拒否
- nonempty events、event field、count closure、exact summary key、extime、grid、identity の検査は維持

変更箇所は `contract["terminal_contract"]`、すなわち schema v4 専用分岐内だけです。v2/v3 の pre-v4 summary 分岐、11-field cell、extime 3、grid 判定は無変更です。

cohort 1 の plot 受理集合が変わっていない静的根拠は、v3 contract・cell literal・field count・extime 3 のコードに差分がなく、変更が v4 分岐内だけであることです。また cohort 1 解析器とテストへの `git diff --quiet` は `rc=0` でした。回帰テスト自体は実装済み・未実走です。

## patch_stack_sha256

pin 値は次のとおりです。

`790a6e7bfdb2b78ea1a05a242acbfeabbe16a07d3f30e6e6148909a7ac59fdb8`

worktree 内の patch A/B/C の実 bytes を `sha256sum` し、producer と同じ以下の canonical byte列を SHA-256 化して導出しました。

- prefix: `izanagi-patch-stack/v1\n`
- 各行: `<repo-relative path> <実 patch SHA-256>\n`
- 順序: A、B、C

さらに producer の `_patch_stack_identity()` が返す値とも一致することを確認しました。

## test が殺す変異

| test | 赤にする1行変異 |
|---|---|
| `test_missing_terminal_makes_whole_primary_inconclusive_without_replacement` | producer parser を `terminal_positions != [len(events)-1]` に戻す、または解析器から `terminal_not_closed` 判定を削る |
| `test_patch_stack_sha256_is_exact_at_top_and_row_bindings` | `_validate_build_bindings` の expected から `patch_stack_sha256` の1行を削る、または欠落・不一致を許す |
| `test_cohort2_literal_pins_are_independent_of_fixture_helpers` | `PATCH_STACK_SHA256` を1文字変更する、または実 patch bytes 由来の canonical hash と異なる値へ替える |
| `test_cohort2_plot_accepts_zero_terminal_with_exact_summary` | terminal 位置条件を「末尾1件必須」へ戻す、または terminal 0 件でも `events[:-1]` を通常 event とする |
| `test_cohort2_zero_terminal_requires_exact_summary` | `flushes`、`updates`、`retained`、`dropped` のいずれかの exact 比較を削除・緩和する |

## 所有外への波及可能性

静的に列挙した caller・fixture・consumer は以下です。

- producer/parser: `tools/pegasus/probes/t2187_adaptive_const_probe.py`
- producer transport: `tools/pegasus/probes/t2187_adaptive_const_probe.pbs`
- parser consumer tests: `test_t2187_adaptive_const_probe.py`
- emitter/parser 結合 fixture と test: `test_dynamic_backoff_transitions.py`
- test-file 自走 meta-test: `test_plain_runner_coverage.py`
- plot を参照する凍結文書: `docs/dynamic-backoff-preregistration.md`
- cohort 2 解析器の production caller: repo 内では見つからず、直接 consumer は今回の解析テストだけ
- plot の in-repo Python caller:今回の plot test 以外は見つからず、公開 CLI と README が利用面

## 所有外なので触らなかったもの

- producer parser、PBS、関連テスト: fix-2 所有。現 worktree の parser はまだ terminal 0 件を拒否します。
- patch C と emitter 結合テスト: fix-1 所有。
- cohort 1 解析器とテスト: 明示的な変更禁止対象。
- `docs/` の事前登録と実装契約: 凍結・所有外。
- worklog、handoff、phase 文書: 記録作業は担当外で、許可された5 pathにも含まれません。
- 診断-only CLI mode: scope 外裁定に従い追加していません。

## 総括

- 直した所見: FX1 の plot 側、FX5、FX8 の解析器テスト側、FX9 を指定5ファイルだけで修正しました。
- 実走結果: pytest は `rc=16`、`child_started=false` のため全 nodeid が実装済み・未実走、静的検査はすべて通過しました。
- 残っている赤: 実測された赤はありませんが、fix-2 未統合の現 parser では producer 結合 node が失敗する状態であり、統合後の実走確認が残ります。