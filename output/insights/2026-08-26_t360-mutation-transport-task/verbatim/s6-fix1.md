## 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| `hashlib` import 欠落 | closed | importを追加。2か所の `sha256` 参照が解決することをASTで確認 |
| 未実装hook契約の11 node | closed | 指定された11 nodeだけを削除。非対象nodeと既存期待値は維持 |
| 現行hook挙動の回帰pin | closed | `PEGASUS_LOGIN`を指定した直接probeと回帰関数の直接呼び出しが成功 |
| 描画外62失敗の後段結果 | partial | 全件を静的分類したが、`NameError`解消後のassertionはpytest未実走 |
| 非対象テストへの影響 | closed | 非対象のテスト、assertion、期待値は削除・変更していない |

## 直した内容

- [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_pegasus_dispatch_compute.py:9)
  - `import hashlib`を追加。
  - `_Scheduler`内の参照は123行、`_job_run_with_mocked_child`内は3981行。

- [test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_hooks.py:3959)
  - `[python-m-pytest]`正例1 nodeを削除。
  - 指定された境界負例9 nodeを削除。
  - compute site-gate契約テスト1 nodeを削除。
  - `[pytest]`正例と既存の`direct-trampoline`、`direct-python-m-pytest`負例は維持。

## 描画されなかった62赤の扱い

焦点ログを機械的に分類しました。

- 62件中10件は`test_hooks.py`で、すべて今回削除対象のnodeでした。描画済みの`shell-recursion`を加えると指定11 nodeになります。
- 残る52件は`test_pegasus_dispatch_compute.py`の48関数です。
- 48関数すべてが、`hashlib.sha256`を使う`_job_run_with_mocked_child`または`_Scheduler`経路を通ることをASTで確認しました。未分類は0件です。
- 焦点ログ全体のdispatcher側66失敗についても、58関数すべてが同じ2経路の和集合に入りました。

「importだけで後段assertionもすべて成功する」とは仮定していません。静的に閉じたのは`NameError`への到達経路までであり、解消後に別の実赤が現れないことは親の実走確認が必要です。

## 追加した回帰テスト

[test_hooks.py:3993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t360-mutation-transport-task/orchestrator/tests/test_hooks.py:3993)に1 node追加しました。

名前とdocstringの両方で、望ましい仕様の主張ではなく現状のpinであることを明記しています。固定する挙動は次の通りです。

- `generic -- pytest`を許可。
- 未知taskの`unknown -- pytest`を許可。
- 任意task名の`cmake --build`を許可。
- `generic -- python3.10 -m pytest`はinterpreter residual走査で拒否。

将来hookが未知taskや内側argvを境界づければ許可assertionが赤になり、`python -m pytest`を正規gatewayとして許可すれば拒否assertionが赤になります。

## 未実走

pytestは指示どおり実行しておらず、緑とは報告しません。

実施した非pytest検査は次の通りです。

- 両対象ファイルのAST parse成功。
- 追加回帰関数をpytestを介さず直接呼び出して成功。
- `guard_bash.decide(..., repo_root, site="PEGASUS_LOGIN")`の直接probe成功。
- `git diff --check`成功。

## 止めたこと

- 期待値が誤りだと自己判断した項目はありません。
- `hooks/guard_bash.py`を含む実装側は変更していません。
- `xfail`、`skip`、fixture hash差し込みは行っていません。
- `git add`、commit、push、branch操作、Web検索は行っていません。

## 総括

所有対象2ファイルだけを修正し、import欠落、指定11 nodeの削除、現行hook挙動を固定する1 nodeの追加を完了しました。残る確認事項は、親によるpytest実走で`NameError`後に別の赤が現れないかを確認することです。