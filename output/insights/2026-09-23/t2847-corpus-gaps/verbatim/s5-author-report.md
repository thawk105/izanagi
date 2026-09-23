## 総括
新規 [test_verifier_corpus_gaps.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847-corpus-unit/orchestrator/tests/test_verifier_corpus_gaps.py) に以下を実装しました。

- `test_f03_same_version_double_read`
- `test_f06_different_version_double_read`
- `test_b06_wr_only_cycle_is_g1c`

`py_compile` 成功。自走は **3 PASS・0 FAIL・0 SKIP、rc 0**。期待値との不一致はありません。

## 規約の洗い出し
以下を静的に確認しました。meta-test 自体は未実走です。

- `test_plain_runner_coverage.py`：命名・自走 harness を満たし、pytest 専用 allowlist 追加不要。
- `test_pytest_collection_config.py`：収集対象となり、除外設定は不要。
- `test_campaign_import_invariant.py`：正規 namespace を使用。
- `test_real_repo_serialization.py`：実 repo のデータ読み取り・共有 fixture 利用がなく、reader 登録不要。
- README：pytest fixture 非依存、FAIL/ERROR/SKIP 分離、一時領域の finally 後始末に対応。

## 所有外への波及
変更要求は無し。helper・合成 source・trace を新ファイル内に閉じ、既存テストを import していません。git status でも新規ファイル1本のみ。index・履歴への書込みは行っていません。

## 変更前の受理・拒否挙動
現行 verifier が F03 を認証済み serializable、F06 を G2、B06 を G1c と判定することを、手導出の辺・多重度・理由とともに固定しました。verifier 本体と受理集合は変更していません。