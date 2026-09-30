## 変更

指定2ファイルの6箇所を base `3cb51f201` の値へ復元しました。L1.5上限は `9_696`、超過負例は `9_697` です。

変更前は予算検査で受理した9,697〜9,788 bytesを、変更後は拒否します。他の段5変更は維持し、テストの反転・skip・削除はありません。

## 確認 (grep・構文・実走した範囲)

- 指定のbase差分内：`9_788`／`9_789` はともに **0件**。
- 2ファイルのAST構文解析、`git diff --check`：成功。
- `python3 tools/check_docs.py`：実走、rc=1。
- `tools/run_tests.py orchestrator/tests/test_check_docs.py`：rc=16。`qstat -Q preflight rc=1`、`child_started=false` のためpytest未実走。

## 期待赤と回帰

`check_docs.py` は指定どおり期待赤6件のみでした。

- L1.5 footprint：`9793 > 9696`
- effort pin：DW-S02／S03／S05-A／S06-A／S06-Cの5件

同検査で期待外の回帰はありません。pytestでの回帰有無は未判定です。

## 総括

RB-1の修正完了。docs編集・commit・sub-agent起動はしていません。親のdocs統合後にpytestの実走確認が残ります。