## 足したテスト

`orchestrator/tests/test_s8c_schedule.py:328` に追加。seed 不一致を拒否し、一致時は ordinal 0 の `ScheduleCell` を受理します。

## 変異が赤になる論証

`c05.m09` では `seed-beta` でも decode が成功し、`:335` の `pytest.raises` が失敗します。

## 既存への影響

指定テスト以外、production、docs、既存期待値、harness は未変更です。

## 実走状況

pytest は未実走。`git diff --check` のみ実行済みです。

## 総括

seed 検証経由を守るテストを追加しました。  
正例と負例を同一テストに含めています。  
変更ファイルは 1 件だけです。