## 実装した差分

- [s8c_preregistration.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:70): 両 sentinel に `<` と `>` を加え、各受理正規表現の表現域外に変更しました。正規表現自体は不変です。
- [s8c_preregistration.py:2337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py:2337): 診断の JSON 化と stderr 出力全体を `except Exception` で隔離しました。失敗を握り潰す理由もコメントで明記しています。
- [test_s8c_cli_entrypoints.py:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py:229): `RuntimeError` を直送する live evaluator の temporary repo fixture と oracle を追加しました。
- [test_s8c_preregistration_core.py:2686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py:2686): 捕捉集合、文字数・文字種境界、sentinel 表現域を固定するテストを追加しました。

## 追加したテスト

| scope 3 | 固定する命題 | テスト |
|---|---|---|
| 1 | evaluator 直送 `ValueError` が12件の exact fallbackと evaluator 側3 field診断になる | `test_default_registry_evaluator_value_error_remains_fail_closed` |
| 2 | 遅延 iterable の materialize 中の `TypeError` が12件の exact fallbackとなり、normalize 側 callsiteになる | `test_lazy_type_error_remains_fail_closed_at_normalization_callsite` |
| 3 | live evaluator 直送 `RuntimeError` の実 process CLIでstdout bytes、終了値、exact stderrを固定 | `test_live_evaluator_runtime_error_cli_preserves_stdout_and_diagnostic` の4 parameter node |
| 4 | reason・type名の128文字をそのまま受理し、129文字をsentinelへ倒す | `test_diagnostic_text_length_boundary_accepts_128_and_rejects_129` |
| 5 | `_` を含むreasonをsentinelへ倒す | `test_preregistration_reason_with_underscore_uses_sentinel` |
| 6 | stderrの`write`が`OSError`でも`main()`のstdoutと終了値が不変 | `test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_oserror` |
| 7 | 両sentinelが対応する受理正規表現に一致しない | `test_diagnostic_sentinels_are_outside_accepted_text_languages` |

## 実走した nodeid と結果

許可された自走 harness のみを使用しました。

- `PYTHONPATH=. python3 orchestrator/tests/test_s8c_cli_entrypoints.py`
  - 全15 node: `15 passed in 2.52s`
- `PYTHONPATH=. python3 orchestrator/tests/test_s8c_preregistration_core.py`
  - 全411 node: `411 passed in 45.08s`

追加nodeはすべて上記全走に含まれ、PASSしています。

- `orchestrator/tests/test_s8c_cli_entrypoints.py::test_live_evaluator_runtime_error_cli_preserves_stdout_and_diagnostic[text-path]`
- `...::test_live_evaluator_runtime_error_cli_preserves_stdout_and_diagnostic[text-module]`
- `...::test_live_evaluator_runtime_error_cli_preserves_stdout_and_diagnostic[json-path]`
- `...::test_live_evaluator_runtime_error_cli_preserves_stdout_and_diagnostic[json-module]`
- `...::test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_oserror`
- `orchestrator/tests/test_s8c_preregistration_core.py::test_lazy_type_error_remains_fail_closed_at_normalization_callsite`
- `...::test_default_registry_evaluator_value_error_remains_fail_closed`
- `...::test_diagnostic_text_length_boundary_accepts_128_and_rejects_129`
- `...::test_preregistration_reason_with_underscore_uses_sentinel`
- `...::test_diagnostic_sentinels_are_outside_accepted_text_languages`

## 受理・拒否の含意

受理側: `[a-z0-9-]` のみで128文字以下のreasonはそのまま通り、例えば `predicate-result-type` は診断へ同じ値で現れます。  
拒否側: 型・文字種・長さが表現域外の値は生値を載せず、受理正規表現と一致しないsentinelへ倒れます。

## 不変条件の自己検査

1. 受理集合: 受理正規表現と評価結果の生成は変更していません。
2. field集合: `ActivationReport`、`PredicateResult`、`EvidenceRef`は未変更です。
3. CLI stdout: stdout生成処理は未変更で、実 processのexact bytes比較がPASSしました。
4. 危険payload非包含: 新診断は固定callsiteと正規化済みfieldのみで、exact stderrにもdetail・path・tracebackはありません。
5. 新規file無し: 指定された既存3 fileだけを編集しました。
6. reason語彙: `ReasonCode`、`REASON_CODES`、`reason_code`値は未変更です。
7. fail-closed終端: 捕捉集合は`Exception`のままで、診断stderrの`OSError`でもstdoutと終了値が維持されることを実測しました。

## 未了・懸念

scope内の未了はありません。親側のrepository全走、統合、commitは未実施です。

## 総括

段6裁定のfix scope 1〜3だけを実装し、指定2 harnessの合計426 nodeがPASSしました。既存期待値の変更、追加file、docs編集、commit、pushは行っていません。