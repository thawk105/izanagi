## 総括

裁定 §1〜§4を実装し、§0 の T-1886 は実装していません。  
H1〜H7、fixture 別 loadgroup、shard 衝突辺、C1〜C3、9 変異 nodeid を追加しました。  
基準の期待赤は空ですが、焦点 pytest は child 起動前 rc=16 のため、実装済み・未実走です。  
禁止ファイルと `docs/` は無変更、commit 系操作も行っていません。

## 実装内容

- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/conftest.py:348)

  - T810 3 node と nested collection 2 node を parent reader 登録。
  - candidate、scan、snapshot fixture 用の fixture-owned lock factoryを追加。
  - controller prewarm 2 系統の実 endpoint を parent SH 内へ移動。
  - Git common-dir key と旧 worktree-root keyを、常に旧、新の順・同一 mode・共有 deadline で併取。
  - Git authority 環境を閉じ、解決失敗時の fallback は設けていません。

- fixture 配線

  - [invariant candidate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/test_s8c_preregistration_invariant.py:362): module scope、生成中 EX、全 consumer 寿命 SH。
  - [predicate fixtures](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/test_s8c_preregistration_predicates.py:199): snapshot は module SH、candidate は function scopeで EX→SH。
  - [repository scan](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/test_campaign_import_invariant.py:1075): module scope、`("read","read")`、6 consumer に新しい `campaign-repository-scan` group。

- [acceptance_shards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/tools/acceptance_shards.py:77)

  - 4 group 間の独立した K4、6 衝突辺を追加。
  - 衝突 group を同一 component へ union。
  - assignment closure gateでも衝突辺の同一 shard 性を再検査。
  - `_git_common_dir()` に閉じた Git 環境を追加。

- [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1886-realrepo-closure-split/orchestrator/tests/test_real_repo_serialization.py:3794)

  - C1: `matrix == independent exact golden` を component 検査より先に実施。
  - C2: 実在する4 fixture本体を直接実行し、builder/read/yield/teardown の lock contextを記録。
  - C3: 3 fixture group、計14 retained node と resource node集合の素性を検査。
  - 指定された9個の ASCII mutation IDを登録。

## 変異の単独診断性

7変異は、対応 param branch が直接 gateで停止し、その後の検査へ進まない構造を確認しました。赤理由はそれぞれ、mode/context、sibling key、旧 key取得、edge exact、prewarm contextの1点です。

`t810-live-reader-unregistered` と `nested-collection-node-unregistered` は、最終 access mapを原子的に変異させる場合は単独診断できます。ただし source literalを片側だけ削る変異では、conftest の inventory/partition import guardが対象 nodeより先に拒否します。この2件は親側 mutatorを原子的 map変異へ再照準する必要があります。

## 検査結果

実走対象として指定した範囲は以下です。

- `test_real_repo_serialization.py::test_real_repo_closure_mutations` 全9 instance
- `test_current_commit_snapshot_actual_fixture_owns_parent_reader_context`
- `test_real_repo_priority_order_is_literal_and_writers_follow_barrier`

`tools/run_tests.py` 経由で通常3回、collect-only 1回を試行しましたが、すべて `qstat -Q preflight rc=1`、`child_started=false`、rc=16でした。pytest nodeは0件実行です。

赤の内訳:

- 事前指定した基準赤: 0件
- pytest実装赤: 未観測
- dispatch infrastructure failure: 4走
- submodule index-lock由来のsandbox偽赤: 0件。child未起動のため発生していません。

静的検査は `git diff --check`、8 Python fileのAST parse、結合文字不在検査を通過しました。`tools/run_tests.py`、wait/land/checker、`docs/` の差分はありません。

波及面は、全95 resource nodeのlock取得、receipt/oracle prewarm consumer、変更した4 fixtureの15 consumer、全 acceptance shard割付です。選択・skip・期待値・受理集合は変更せず、排他と配置だけを強化しています。