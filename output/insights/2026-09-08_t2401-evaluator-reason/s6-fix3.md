## 直した内容

- [test_s8c_preregistration_core.py:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py:507): 共通の armed 状態と、disarmed 時の `repr(instance)`、`repr(type(instance))`、`type(instance).__name__` の安全性 assertion を追加。
- [test_s8c_preregistration_core.py:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py:519): 診断呼び出し中だけ arm し、`finally` で必ず disarm する context manager を追加。
- [test_s8c_preregistration_core.py:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py:536): reason 系 fixture を、armed 時だけ欠落、非文字列、`SystemExit`、`KeyboardInterrupt` になるよう変更。
- [test_s8c_preregistration_core.py:569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py:569): 型名系 fixture を、armed 時だけ例外送出または非文字列返却するよう変更。
- [test_s8c_preregistration_core.py:2940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py:2940): 対象の診断呼び出しだけを arm 区間で囲んだ。

## 固定している命題が変わっていないこと

- `_MissingReason`: armed 時は reason 取得不能となり、診断専用 sentinel に倒れる。
- `_NonStringReason`: armed 時は非文字列 reason となり、診断専用 sentinel に倒れる。
- path 様 reason: sentinel に倒れ、path は診断に現れない。
- 長すぎる reason: sentinel に倒れる。
- `_HostileReason`: armed 時の `SystemExit` を漏らさず sentinel に倒れ、detail も現れない。
- 不正 charset の型名: exception type sentinel に倒れる。
- 長すぎる型名: exception type sentinel に倒れる。
- `_HostileType`: armed 時の `SystemExit` を漏らさず exception type sentinel に倒れる。
- `_NonStringType`: armed 時の非文字列型名は exception type sentinel に倒れる。
- `_KeyboardInterruptType`: armed 時の例外を漏らさず exception type sentinel に倒れる。
- `_KeyboardInterruptReason`: armed 時の例外を漏らさず reason sentinel に倒れる。
- 12 件の `ERROR`、`evaluator-exception`、空 evidence、detail・message・path の非漏出に関する既存期待値は変更していない。

## 失敗時に pytest が整形できることの確認

[test_s8c_preregistration_core.py:2979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py:2979) の `assert diagnostics == ...` を一時的に `!=` へ反転し、自走 harness を実行した。

結果は `rc=1`、`4 failed / 415 passed`。`hostile-type-name` と `non-string-type-name` を含む全失敗について通常の traceback と `FAILED` 要約行が出力され、`INTERNALERROR` は発生しなかった。

確認後に `==` へ戻した。最終 `git diff` でも反転が残っていないことを確認済み。

## 実走した nodeid と結果

`PYTHONPATH=. python3 orchestrator/tests/test_s8c_preregistration_core.py`

- 最終結果: `419 passed in 18.10s`、`rc=0`
- reason 系 5 nodeid: すべて PASSED
- 型名系 4 nodeid: すべて PASSED
- `test_diagnostic_type_guard_catches_keyboard_interrupt`: PASSED
- `test_diagnostic_reason_guard_catches_keyboard_interrupt`: PASSED
- 同ファイルの残り全 nodeid: PASSED

## production 無変更の確認

- HEAD: `f3c6f1c9d2`
- `git diff --name-only`: `orchestrator/tests/test_s8c_preregistration_core.py` のみ
- `git diff --quiet -- orchestrator/campaign/s8c_preregistration.py`: `rc=0`
- production コード、新規ファイル、docs、他 test file は変更していない。
- `git add`、commit、push は実施していない。

## 未了・懸念

なし。

## 総括

敵対 fixture の危険な挙動を診断呼び出し中だけに限定し、例外時にも必ず解除されるよう修正した。固定済みの診断命題と production コードは変更せず、正常走行と失敗時の pytest 整形を実測確認した。