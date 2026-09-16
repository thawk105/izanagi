## 所見への対応

cwd末尾の改行が失われるmust-fixを修正しました。**実装済み・未実走**です。

## 実装

`submit_certify.sh` の相対path絶対化だけを変更しました。

- `pwd -P && printf '.'` で末尾改行を保持。
- `pwd`の出力改行とsentinelだけを除去。
- `pwd`失敗は代入の終了コードへ伝播し、`set -e`で停止。
- 絶対入力、schema、qsub option、export specは維持。

## テスト

追加nodeid：

`orchestrator/tests/test_pegasus_calibration_workload.py::test_submitter_keeps_relative_job_script_bytes_from_newline_caller`

`output/`配下に改行付きcwdと改行なし兄弟を作り、異なるscriptを配置。fake qsubが読んだbytesと、pre-submit／receiptのhashを照合します。

helperには既定値付き表示照合オプションを追加。既存テスト・段5の6ケースの期待値は変更していません。

## 実走結果

以下は成功しました（pytest nodeid対象外）。

- `bash -n tools/pegasus/submit_certify.sh`
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

pytestの実走成功nodeidはありません。

## 波及の静的列挙

- caller：相対job-scriptの絶対化に限定。既定・絶対入力は従来どおり。
- 共有fixture：`_make_submit_clean_fixture`は未変更。fake qsub helperの既定動作・返却値も維持。
- consumer：`test_pegasus_tools.py`のsubmit契約、job側receipt照合は変更なし。
- 他submit：`submit_floor.sh`の出典参照に実装上の連動はありません。

## 残る赤と未実走

ランナーは `qstat -Q preflight rc=1` により**rc=16、child未起動**で停止しました。テスト失敗の判定には到達していません。

未実走範囲：

- `test_pegasus_calibration_workload.py` 全体
- `test_pegasus_tools.py` 全体
- 自ら選定した制約meta-test：
  - `test_real_repo_clean`
  - `test_real_repo_group_collection_exactly_matches_canonical_nodes`
  - `test_receipt_memo_consumer_inventory_and_optouts_are_complete`
  - `test_oracle_environment_consumer_inventory_and_registry_are_complete`

## 総括

所有2ファイルだけを編集しました。`git add`・commitは実行していません。親での実走確認が残っています。