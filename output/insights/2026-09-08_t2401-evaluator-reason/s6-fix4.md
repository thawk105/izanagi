## 直した内容

[test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py:586) のみ変更しました。

- `BaseException` を直接継承する `_DiagnosticGuardBaseException` を追加。
- type 抽出側と reason 抽出側の `KeyboardInterrupt` を専用型へ置換。
- fixture 名と test 名を `base_exception` に合わせて改名。
- reason 側の期待型名を `_BaseExceptionReason` に更新。
- `SystemExit` を使う既存負例は維持。

## 固定している命題が変わっていないこと

専用型は `Exception` を継承していないため、「`except Exception` では捕まらない例外」を引き続き検査しています。

両 test とも sentinel 診断および fail-closed の 12 件 `ERROR` report を固定しています。arm/disarm 構造と、disarmed 時の `repr()` 安全性 assertion も変更していません。

## rc=1 になることの確認

reason 側 test の期待型名を一時的に `_IntentionallyWrongReasonType` へ変えて自走 harness を実行しました。

- 結果: `1 failed, 418 passed`
- harness rc: `1`
- `INTERNALERROR`: なし
- session 中断および rc=2: なし
- 失敗 node: `test_diagnostic_reason_guard_catches_base_exception`

確認後に期待型名を `_BaseExceptionReason` へ戻しました。`git diff` には意図した専用型への置換と改名だけが残り、旧 `KeyboardInterrupt` 名と一時反転文字列は残っていません。`git diff --check` も rc=0 です。

## 実走した nodeid と結果

実行コマンド:

```text
PYTHONPATH=. python3 orchestrator/tests/test_s8c_preregistration_core.py
```

最終状態の結果:

```text
419 passed in 25.69s
rc=0
```

対象 nodeid を含む全 419 件が成功しました。

- `test_diagnostic_type_guard_catches_base_exception`: PASSED
- `test_diagnostic_reason_guard_catches_base_exception`: PASSED

## production 無変更の確認

`git status --short --untracked-files=all` の出力は次の 1 ファイルだけです。

```text
M orchestrator/tests/test_s8c_preregistration_core.py
```

production コード、新規ファイル、他の test、docs は変更していません。`git add`、commit、push も行っていません。

## 未了・懸念

未了・懸念はありません。

## 総括

専用の通常扱いされる `BaseException` subclass に置き換え、固定命題を維持したまま、意図的な失敗が rc=1 として安全に報告されることを確認しました。