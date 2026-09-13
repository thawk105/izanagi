## 実装したもの

- `orchestrator/campaign/b10_backoff_static_tail_formal.py`：spec/hash 検証、設定生成、loader、統計解析、cohort 判定、report、CLI を追加。
- `orchestrator/tests/test_b10_backoff_static_tail_formal.py`：拒否例、数値検算、5 probe、cohort 正例・変異試験、自走 harness を追加。

**実装途中・未検証です。完成品として扱えません。**

## 実走結果

実行対象：`orchestrator/tests/test_b10_backoff_static_tail_formal.py` 全体、`-n 0`。

- runner：rc=16。
- 原因：`qstat -Q` が rc=1。
- 子テストは未起動。緑を確認した nodeid はありません。
- 全追加テストは「実装済み・未実走」です。
- 制約 meta-test、自走 harness、既存系列の回帰試験も未実走です。

## 意図的な赤 (未 land 依存)

実走前に想定した finding 集合：

- `test_probe_2_*`：整数カウンタ API・WAL 保存経路の未 land。
- `test_probe_4_*`：`loop.run_campaign` の correctness 転送の未 land。
- cohort 正例・probe 3/5：上記共有経路への依存。
- caller 在庫・所要台帳：子 C の登録更新待ち。

**実際の赤理由は未確認です。これ以外を未 land 依存として免責していません。**

## 波及可能性の静的列挙

- caller 在庫：`test_campaign.py`、`test_official_perf_closure.py`、`test_p3_build_authority_cli.py`、`test_ccbench_spawn_sites.py`。
- テスト制約：`acceptance_duration_ledger.json`、`test_real_repo_serialization.py`、campaign import 制約。網羅調査は未完了です。
- 共有依存：runner、pipeline、loop、campaign lock、admission、WAL、既存 verifier fixture。
- 着手前の探索は正しさ記録が各 cell 1 本、性能 rep の整数カウンタなし。既存 driver は旧3系列を受理し、新 formal 系列を受理しません。

## 守れなかったこと

`tools/run_tests.py` が所有外に次を生成しました。

`output/pegasus-dispatch/ca55274312a2ab8fc9a6015c3780759b/receipt.json`

所有 path 制約への違反を認識した時点で、指定どおり作業を停止しました。削除などの追加変更もしていません。

## 総括

所有2ファイルに実装とテストを追加しました。  
テストはインフラ障害で起動せず、正しさは未確認です。  
runner による所有外ファイル生成のため、境界指示に従って停止しました。  
commit、文書編集、本走投入、新規性能計測は行っていません。