## 総括

- snapshot 評価の共有化と 5 node の xdist group 化を実装しました。
- 独立 group 名 oracle と 5 node membership oracle を追加しました。
- 静的監査と `git diff --check` は通過し、tracked 差分は指定 2 ファイルだけです。
- テストは dispatch 基盤障害で child が起動せず、実装済み・未実走です。closed ではありません。

## 実装した変更

- [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1619-shared-setup/orchestrator/tests/test_s8c_preregistration_predicates.py:170)

  - fixture 内で snapshot commit の `evaluate_all` を一度だけ実行し、外側を tuple 化。
  - 対象 5 test に `s8c-predicate-snapshot` decorator を追加。
  - 既存 assert、literal、関数名、件数は不変。
  - exact-match の左辺だけを共有し、右辺は test 内で実 HEAD を独立評価。
  - C12 helper test は共有結果への ID map 適用へ変更。`_result` 自体は維持。

- [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1619-shared-setup/orchestrator/tests/test_real_repo_serialization.py:124)

  - group 名 golden と、手書きの 5 canonical node frozenset を追加。
  - [collection test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1619-shared-setup/orchestrator/tests/test_real_repo_serialization.py:1045) で実収集 membership との完全一致を検査。

commit、index 操作、docs、conftest、production、台帳、`REAL_REPO_SERIAL_NODES` の変更はありません。

## 実走結果

すべて `python3 tools/run_tests.py` 経由で投入しましたが、`qstat -Q preflight rc=1`、`child_started=false`、runner `rc=16` でテスト process は起動しませんでした。

- `orchestrator/tests/test_s8c_preregistration_predicates.py`

  - 通常、`-n 0`、`--force-dispatch -n 0` の各試行とも 0 passed / 0 failed、未実走。

- `test_real_repo_serialization.py` の指定 4 nodeid、および洗い出した marker shape/name meta-test 2 件

  - 0 passed / 0 failed、未実走。
  - 追加対象は `test_xdist_group_audit_rejects_synthetic_negative_controls` と `test_xdist_group_name_set_audit_rejects_isolated_negative_controls`。

テストの赤はありません。残っている `rc=16` は dispatch infrastructure に帰属し、差分に帰属する test failure ではありません。

非テスト静的検査は通過しました。

- predicates の 106 test 関数集合と全既存 assert AST が HEAD と一致。
- real-repo serialization の 42 test 関数集合が HEAD と一致。
- decorator 対象 5 件、fixture 内評価 1 回、exact test 内 HEAD 評価 1 回を確認。
- 独立 oracle の 5 literal node 完全一致、`git diff --check` 通過。

## 波及の静的列挙

- `current_commit_snapshot` の caller は対象 5 test のみで、全て同一 xdist group に所属します。
- `_result` は所有外の他 test が引き続き利用します。削除・改名・実装変更はありません。
- collection report と group 契約 test は新 group 名と 5-node component を観測します。
- shard 検査は新しい 5-node component を分割不可の単位として扱います。
- loadgroup scheduler は 5 node を同一 worker に配置します。
- `REAL_REPO_SERIAL_NODES` と共有 fixture closure は交差せず、real-repo decorator provenance と priority literal に変更はありません。
- ledger lookup は group suffix を除去するため key は不変です。台帳自体も未変更です。
- production callerおよび production predicate 評価には変更がありません。

## 受理集合の前後

変更前は、5 test が同じ snapshot を各自再評価し、独立 worker へ配置可能でした。各 test は既存の status、reason、evidence、SHA、完全等値条件で受理・拒否していました。

変更後も、その意味上の受理・拒否条件は同一です。評価済み immutable tuple を共有するだけで、exact-match の実 HEAD 側は独立評価を維持します。

意図して追加した構造上の拒否条件は、新 group の欠落、余分な member、group 名不一致です。それ以外の predicate、real-repo、shard priority、duration ledger の受理集合は変更していません。