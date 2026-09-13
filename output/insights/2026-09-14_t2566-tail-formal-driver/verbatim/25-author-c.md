## 更新した登録簿

### `test_official_perf_closure.py`

- `_REVIEWED_PERF_FILES`：新 module を1ファイル追加。
- `_REVIEWED_PREDICATES`：`load_formal_campaign → use_perf_from_receipt` を1件追加。現物の呼出しは `orchestrator/campaign/b10_backoff_static_tail_formal.py:424`。
- 旧レビュー表の `validate_perf_observation` 呼出しは現物にありません。

### `test_p3_build_authority_cli.py`

`MACHINE_CALLERS` に新 module を `BACKOFF_SWEEP` として追加。同 production file の `:745` が context 作成、`:747` が generator receipt 発行です。

### `test_ccbench_spawn_sites.py`

同 production file の subprocess 呼出しを AST と現物から数え、計2件追加しました。

- `:227` `_git`：safe 側に1件。全5呼び元は読み取り専用 Git 問い合わせ。
- `:726` `scheduler_coordinates`：non-CCBench 側に1件。qstat によるジョブ情報取得。

Git の二重登録はありません。

### `test_campaign.py`

同 production file の `:761` にある `run_workload → run_campaign` 1箇所を両在庫へ追加しました。

- `expected_inventory`：総数20→21。
- `expected_run_calls`：総数16→17。
- 関数名・変数名・在庫構造を維持しています。

## 触らなかった登録簿と理由

- 両 guard 群：AST 走査と既存登録が完全一致。削除・変更なし。
- `_BENCH_AUTHORITIES`、evaluate 総数5：直接呼出しの追加なし。
- manual-build 系：新 module 全文に `--build` なし。
- spawn gateway・bounded clients・diagnostic 在庫：追加対象なし。
- 所要台帳：`.tmp` と親の成果物ディレクトリに成功 JUnit がなく、追記なし。推定値は使用していません。

## 実走結果

以下のパスは `orchestrator/tests/` 配下です。指定の自走 harness と単独関数呼出しで実行しました。

| 実走対象 | 結果 | rc |
|---|---:|---:|
| `test_official_perf_closure.py` 全 nodeid | 7件成功 | 0 |
| `test_p3_build_authority_cli.py` 全 nodeid | 19件成功 | 0 |
| `test_ccbench_spawn_sites.py` 全 nodeid | 47件成功 | 0 |
| `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed` | 成功 | 0 |

campaign 単独実行の初回は `skiputil` の import 失敗で rc=1、テスト本体は未到達。検索パス修正後の再実行は成功しました。

campaign の残りと新 formal テストは今回未実走です。`git diff --check` は rc=0。

## 守れなかったこと

無し。

## 総括

所有する登録簿4ファイルを更新しました。  
件数は現在の実 call site から数え直しました。  
関連74件が成功し、期待値の緩和はありません。  
所要台帳は成功 JUnit 待ちとして親へ返します。  
commit・docs・所有外のソース編集は行っていません。