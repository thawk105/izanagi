実装は完了していますが、pytest は infrastructure 障害により未実走です。

- [floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/campaign/floor_pair_driver.py:51): schema v2、固定 policy、標本単位 drop、fatal 分離、status／terminal 再検証、campaign 単位5%判定、summary監査情報を実装。
- [test_floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2341-author/orchestrator/tests/test_floor_pair_driver.py:561): M1〜M20を観測する正負例を配置。59/2、59/3、40/2、177/8、177/9、campaign局所性、empty stratum、candidate 0、reference 0などを含みます。
- actual `run_window` / `finalize_floor` を直接通した手動 diagnostic は全対象シナリオで成功。構文検査、`git diff --check`、結合文字検査も成功。
- `measure_point` は1呼出し、位置引数4個と既存 keyword集合を維持。3件のsource inventoryも静的にexact一致。
- repo内のspec/window/summary schema consumer、production caller、共有fixtureは所有2ファイル外に0件。meta-test 3ファイルはsource inventoryのみです。
- create-only、HEAD/blob/source束縛、固定probe argv、upper ≥ 1非丸め、live site/env、adapter非差込、plan順・ID/count exactは不変です。
- commit、docs、所有外ファイルの変更はありません。runnerが作った失敗receiptは確認後に除去しました。

## 総括

- 変更: production +623/-122行、test +635/-23行の2ファイル。
- test: 新規21 node、既存14 node更新、静的collection見込み161 node。
- pytest範囲: `orchestrator/tests/test_floor_pair_driver.py`。
- pytest結果: child未起動、passed 0 / failed 0、runner rc=16。
- 未実走理由: Pegasus `qstat -Q` preflight rc=1によるdispatch infrastructure failure。
- 所有外波及: repo内caller・共有fixture・schema consumerなし。source inventoryのみ3件。
- 未実装: scope内なし。裁定パッケージ記載のscope外項目は変更していません。