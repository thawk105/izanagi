## 変更前の挙動

`_git` は時間制限なしでGitの完了を待ち、rc=0・非0とも終了コードとstdout/stderrのbytesを返していました。停止したGitを時間超過で拒否する仕組みはありませんでした。

## 実装した内容

指定2ファイルだけを編集しました。`_GIT_TIMEOUT_S = 300.0`、keyword-onlyの`timeout_s`、原因例外を保持する`TrialRegistryError`への変換を追加しました。既存16呼び出しは二引数のままです。300秒は暫定運用値です。

## 追加したテスト

- T1：`exec sleep 2`のPATH shimを0.25秒で打ち切り、例外と原因を検査。
- T2・T3：production既定値でrc=0／23と出力bytesを検査。
- T4：recorderで既定値300.0の実伝達を検査。

静的に構文、トップレベル関数名の一意性、4関数の`test_`命名を確認しました。`test_plain_runner_coverage.py`の自走契約、`pytest.ini`の収集設定、growth hold・共有repo分類を確認し、既存ハーネスを維持しています。

## 実走結果

**実装済み・未実走**です。全体715秒のハーネスは予算外と判断しました。追加4件の合計5秒以内も未確認です。

親が実走すべきnodeid：

```text
orchestrator/tests/test_trial_registry.py::test_git_timeout_raises_operational_error_with_cause
orchestrator/tests/test_trial_registry.py::test_git_timeout_preserves_success_result
orchestrator/tests/test_trial_registry.py::test_git_timeout_preserves_nonzero_result
orchestrator/tests/test_trial_registry.py::test_git_timeout_default_reaches_subprocess_run
```

`git diff --check`は応答待ちを中断したため未確認です。探索したルートの`conftest.py`、`pyproject.toml`、`setup.cfg`は不在で未確認です。

## 波及可能性の静的列挙

- caller：producerのlaunch・attempt処理、`reflux_origin_binding`の再検証などへ、時間超過時に既存の業務例外が伝播します。
- fixture：既存の登録repo・attempt構築も300秒上限の影響を受けます。新設4件はそれらに依存せず、共有fixtureは変更していません。
- consumer test：producer、attempt registry equivalence、reflux、acceptance receipt、preregistration関連の回帰確認が必要です。
- 上限はGit呼び出し1回単位です。履歴loop全体、`flock`、file I/O、`fsync`は制限しません。attempt予約は`started_monotonic`設定前で、孫processは残り得ます。

## 総括

裁定どおり実装しました。docs編集・commit・push・branch操作は行っていません。実走、所要時間、変異検証は親に引き継ぎます。