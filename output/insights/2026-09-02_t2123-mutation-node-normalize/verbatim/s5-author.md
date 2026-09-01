## 変更前の挙動

- 接尾辞なし期待は collection を通るが、接尾辞付き失敗と一致せず `MISMATCH`。
- 接尾辞付き期待は raw collection 照合で起動前拒否。
- fanout verifier も raw 比較のため同じ不整合を持つ。
- `PARSE_ERROR`、完全一致、観測 node の raw 保存は維持されていた。

## 実装した内容

- [mutation_harness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2123-author/tools/mutation_harness.py:1237)

  - `_match_key` が test 名部分だけへ `rfind("@") > rfind("]")` を適用。
  - 初回 collection、resume、flaky-hold の両側を同じ key で比較。
  - path 内の `@`、parametrize ID 内の `@` は保持。

- [mutation_fanout_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2123-author/tools/mutation_fanout_contract.py:297)

  - 同じ `_match_key` を追加し、失敗集合との完全一致に使用。
  - collection 実在検査を両側 key 比較へ変更。
  - raw 重複検査を残し、正規化後の重複拒否も追加。

`_normalize_node`、抽出器、`mutation_fanout.py`、完全一致判定、抽出ゼロ時の `PARSE_ERROR` は変更していません。

## 追加・変更したテスト

- harness 実 xdist 経路で M1、M2、M7、M8。
- 実在 literal による M3、M4、M9。
- group 正規化後の strict superset と抽出ゼロで M5、M6。
- fanout merge proof chain で M10、M12、M13。
- fanout spec の raw／正規化後重複拒否で M11。
- flaky-hold の base、接尾辞付き、無関係 node の policy 対。
- 既存テストの期待値、xfail、skip は変更していません。

## 実走した nodeid と結果

pytest が実際に開始した nodeid は 0 件です。

新設 nodeid 群を `tools/run_tests.py` 経由で2回投入しましたが、いずれも `qstat -Q` がソケット作成に失敗し、child 未起動の rc=16 でした。したがって緑とは報告しません。

静的検査は以下が rc=0 です。

- 変更5ファイルの `py_compile`
- `git diff --check`
- 編集対象確認。差分は許可された5ファイルだけ

## 未実走のもの

実装済み・未実走です。

- 変更した3テストファイルの焦点走／全体走
- `test_mutation_fanout.py`、`test_mutation_worktree.py`、`test_pytest_failure_digest.py`
- 制約 meta-test の `test_pegasus_dispatch_compute.py`、`test_campaign.py`、`test_login_headroom.py`、`test_t338_submission_gate_unit5.py`、`test_official_perf_closure.py`
- M1〜M13 の変異本走
- 全受入走

repo-wide走査を再検索し、上記以外の候補は `tools/` を対象外にするかテストディレクトリを除外しており、追加の関連 meta-test は見つかりませんでした。

## 波及可能性の静的列挙

- `mutation_worktree.py` が live harness を実行する経路。
- `mutation_fanout.py` が fanout contract の split／merge を呼ぶ経路。
- harness の fresh collection、resume、terminal record 再導出、flaky-hold policy。
- fanout の親／shard spec 検査、collection 再照合、現行・history record 再導出。
- harness テストの共有一時 repo fixtureには `xdist_group` markerを追加。ただし通常 `_argv` は xdist を有効化しないため、既存 nodeid は変わらない設計です。
- fanout fixture builder は期待、失敗、status、collection の表記を明示できるよう拡張しました。

## 総括

T-2123 は指定された5ファイル内で実装済みです。変更後は接尾辞あり／なしの双方を比較時だけ同形化し、完全一致とraw証拠を維持します。

ただしテスト infrastructure が child 起動前に失敗したため未実走であり、closedとは申告しません。commit、add、stash、文書編集は行っていません。