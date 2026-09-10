## 直した内容

- [floor_pair_driver.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:22): module docstring と `NOT_PROVEN` を、blob 一致と真の祖先だけを保証する文言へ更新。tree 同値の主張を削除。
- [floor_pair_driver.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:581): `_git_parents` と `_git_changed_paths` を削除し、`git merge-base --is-ancestor` を使う `_git_is_ancestor` を追加。rc=0/1/その他と起動失敗・timeoutを正規化。
- [floor_pair_driver.py:1212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1212): `loaded_head` の一回解決を維持。
- [floor_pair_driver.py:1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1237): spec bytes と解決済み `loaded_head` の blob 比較を維持。
- [floor_pair_driver.py:1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1285): `source_commit == loaded_head` と非祖先を拒否。
- [floor_pair_driver.py:3078](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:3078): summary の `proof_limitations` に更新済み `NOT_PROVEN` を反映。
- [test_floor_pair_driver.py:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:307): 模擬 Git fixture を stdout なしの祖先判定 rc 模擬へ変更。
- [test_floor_pair_driver.py:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:481): 実 Git で `C → H(spec) → H2(無関係)` を受理する正例を追加。
- [test_floor_pair_driver.py:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:507): 別系統 commit、spec blob 改変の実 Git 負例を追加。
- [test_floor_pair_driver.py:904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:904): rc、起動失敗、timeout の helper テストを更新。
- [test_floor_pair_driver.py:1225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:1225): temporary Git replacement refで等値状態を実現し、loader が拒否する実 Git 負例を追加。production に `--no-replace-objects` は追加していない。
- [test_ccbench_spawn_sites.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_ccbench_spawn_sites.py:113): 消えた2 siteを除き、`_git_is_ancestor` の1 siteを登録。

## 削除した test とその理由

1. `test_real_git_spec_and_another_path_in_freeze_commit_are_rejected`
   - spec 以外の changed path を拒否する、廃止済みの「spec 1 path 差分」判定だけに固有。
2. `test_real_git_spec_and_ignored_gitlink_in_freeze_commit_are_rejected`
   - `diff-tree --ignore-submodules=none` による gitlink 差分判定だけに固有。
3. `test_real_git_merge_commit_at_loaded_head_is_rejected`
   - `loaded_head` に唯一の親を要求する、廃止済み判定だけに固有。

## 変更後の挙動

`source_commit` が `loaded_head` の真の祖先で、spec bytes がその `loaded_head` の tracked blob と一致すれば受理します。したがって、freeze commit `H` の後に無関係な `H2`、複数 commit、merge、submoduleを含む任意の変更が積まれても受理可能です。

次は拒否します。

- `source_commit == loaded_head`
- `source_commit` が別系統などで祖先でない
- spec bytes が `loaded_head` の blob と不一致
- `expected_sha256` 不一致

calibration・build receipt の blob 比較、実行時/finalizerの `loaded_head` 統一、schema/key集合は変更していません。

## 実走した検査

- 上記新規・更新 nodeid群と `test_blob_queries_use_the_once_resolved_loaded_head`、spawn inventory test:
  - `tools/run_tests.py` rc=16
  - `qstat -Q` 失敗により child 未起動。テスト自体は未実走。
- 同 nodeid群の `--collect-only`:
  - rc=16、同じく child 未起動。
- 3ファイルの AST parse: rc=0
- `git diff --check`: rc=0

したがって状態は「実装済み・未実走」です。

## 波及可能性

tree 同値を前提とする保証はなくなり、祖先間の変更内容は無制限になります。spawn inventory は新しい実 subprocess site と一致するよう更新しました。指定された issuer production/test ファイルには触れていません。

## 未了・判断を仰ぐ点

pytest の再実走が必要です。ログインノードの実効 headroom が不足し、計算ノード dispatch は `qstat -Q` で失敗しました。判断事項はありません。

## 総括

D1774どおり、束縛を「唯一の親＋spec-only差分」から真の祖先へ変更しました。  
spec blob一致と strict ancestor の2保証だけを残しています。  
変更は指定3ファイルのみで、commitは作成していません。  
静的検査は通過、pytestは基盤都合で未実走です。