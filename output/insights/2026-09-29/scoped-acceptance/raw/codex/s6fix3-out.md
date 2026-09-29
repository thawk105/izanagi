## 所見ごとの対応

MS8 が既存テストをすり抜ける問題に対し、[test_scoped_acceptance_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/scoped-acc-author/orchestrator/tests/test_scoped_acceptance_land.py:251) に `_gate` の直接テストを 2 件追加しました。変更はこのテストファイルの 23 行だけです。実装・既存テスト・docs は変更せず、commit も作成していません。

## 変えた新 test の期待

終了コード 1 では `ValueError`、終了コード 0 では元の argv、`rc: 0`、出力内容に対応する 64 桁の SHA-256 digest を期待します。

## 実走結果

`tools/run_tests.py` は queue 事前確認で rc=16 となり、**pytest は起動していません**。代替の直接呼び出しでは、新テスト 2 件と `test_dev_wave_land.py` の forward-main 回帰 4 件が通りました。MS8 を一時適用すると失敗側の新テストが `DID NOT RAISE ValueError` で赤化し、実装を元に戻した後は再び通りました。構文検査と `git diff --check` も通過しました。

## 所有外への波及

静的に確認した関連箇所は、caller の `dev_wave_wait.py`、受領証 consumer の `dev_wave_land.py`、共有の合成 repo を提供する `test_dev_wave_land.py`、選択対象の inventory を持つ `conftest.py` です。所有外ファイルは編集していません。

## 総括

fix3 のテスト追加と MS8 の赤化確認は完了しました。pytest の結果は queue 障害のため未確認です。