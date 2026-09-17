## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| child-green の参照順 | 実装済み・未実走 | 期待列と docstring を更新 |
| D987 の参照順 | 実装済み・未実走 | 期待列と docstring を更新 |
| fix-6 exact 変異表の維持 | 確認済み | 全20件の anchor・行番号が不変。一致数1・置換後構文OK |

## 変更した test (新旧の期待列と理由)

`test_land_accepts_child_green_tip_runner_change_with_main_digest`

- 旧：`[tip, repo.base]`
- 新：`[tip, repo.base, tip, repo.base]`
- 理由：登録前 static と lock 内の完全 receipt 検証が、それぞれ tested-tip → tested-main の順に参照するため。

`test_d987_rejects_final_runner_change_before_provenance_rc16`

- 旧：`[locked_main, tested_main]`
- 新：`[tip, tested_main, locked_main, tested_main]`
- 理由：登録前 static が tested-tip → tested-main を参照し、その後 lock 内の前進 merge runner 検査が locked-main → tested-main を参照して拒否するため。完全 receipt 再検証には到達しません。

両 docstring に h′ による登録前参照の理由を追記しました。順序は親のログと一致しています。`provenance_calls == []`、rc／status／reason／flag を含む他の assertion と実装は変更していません。

## 実走結果

試行コマンド：

```text
python3 tools/run_tests.py orchestrator/tests/test_dev_wave_land.py -q
```

`qstat -Q preflight rc=1` により runner rc16、`child_started=false`。**pytest は未起動です。**

成功した検査：

- Python 構文解析
- exact 変異20件の静的検査（M4b は fix-6 の訂正版を維持）
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- `git diff --check`

## 総括

指定2テストの期待列と docstring の修正は完了しました。**実装済み・未実走**です。commit・報告ファイルは作成していません。
