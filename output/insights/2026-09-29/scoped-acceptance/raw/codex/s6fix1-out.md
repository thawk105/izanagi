## 所見ごとの対応

- 既存の forward-main 検査関数を元の 3 引数に戻し、縮小受領証の blob 比較を別関数に分けました。指定された既存テスト 4 ケースの直接呼び出しは通過しました。
- 分類と選択の照合を blob 全体の bytes 部分文字列に変更し、鍵を v2.1 に更新しました。`"insights"` の選択規則も指定の 2 種類の引用形に合わせました。
- MS5・MS6・MS9、MF1〜MF3、blob→symlink の型変更を確認するテストを追加しました。

## 変えた新 test の期待

既存の期待値は変更していません。新 test の `test_scoped_forward_main_blob_drift_rejected` は、分離した縮小受領証用関数を呼ぶよう変更しました。

## 実走結果

`tools/run_tests.py` は queue 事前確認で rc=16 となり、pytest の子プロセスは起動していません。pytest の緑は未確認です。代替の直接呼び出しでは、追加した主要テスト、指定された既存 4 ケース、scoped forward-main の 6 blob drift ケースが通過しました。MF1〜MF3 と MS5・MS6・MS9 は、一時的な変異で期待どおり赤化しました。

`check_codex_agents.py`、`check_docs.py`、構文チェック、`git diff --check` は通過しました。

## 所有外への波及

静的に確認した caller は既存の `test_dev_wave_land.py` の forward-main spy と、`dev_wave_wait.py`・縮小 launcher・`run_tests.py` の scoped 経路です。共有 fixture は `test_dev_wave_land.py` の合成 repo と `conftest.py`、consumer test は既存の land・runner 関連テストです。所有外ファイルは編集していません。

## 総括

許可された 4 ファイルを修正し、commit は作成していません。残る確認は、queue が利用可能になってからの pytest 実走です。