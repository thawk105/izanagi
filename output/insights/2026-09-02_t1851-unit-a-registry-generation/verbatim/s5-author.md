## 実装した内容

- [core](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/attempt_registry_core.py:1008): 検証済み seed を使う replay helper と `load_attempt_registry_with_budget_counts()` を追加。既存 API の signature・戻り型は維持。
- [profile](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_profile.py:156): v2 schema、5 軸 slot/codec、2 段 layout、空 retryable 集合、factory、session serializer を追加。
- [adapter](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:603): 世代列挙、現行 scheduler policy による profile 再構成、横断予算、path 世代次元、完全 slot identity 比較を実装。
- [adapter lock seam](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1238): `_atomic_update_locked()` を分離。prelock hook は外殻で一度だけ実行し、live-lock guard は追加していない。
- 15 test 関数、静的展開 22 node を追加。P1、P2、P3と各主要拒否の正例を含む。
- A2' の projection、非空 retryable 集合、schema 別 `_assert_profile()`、v2 mutation、claim v3、marker 経路は未実装。
- commit、git add、branch、stash は実施していない。

## 受理集合の変化

- 変更前: 公開 mutation は canonical v1 のみ。予算は当該 registry 内だけで計数。
- 狭まる: mutation 時に同一 freeze の全世代を replay し、横断予算超過、unsafe/incomplete 世代、未知 schema、protocol 不一致、現行 recovery policy 不一致を拒否。
- 広がる: path API が明示的な protocol 世代 path を返せる。v2 profile/codec は加法的に利用可能。
- 不変: clean な canonical v1 lifecycle、非 64 hex sibling の存在、既存 v1 retryable 空集合。
- v2 profile は公開 mutation で従来どおり `_assert_profile()` に拒否される。
- live fixture freeze の未知 policy を持つ合成 2 段 v1 が発見される場合、canonical v1 mutation も安全側に停止する。

## 走らせた検査

- `python3 tools/check_codex_agents.py`: 成功。
- `python3 tools/check_docs.py`: 成功。
- `git diff --check`: 成功。
- 対象 5 file の AST parse: 成功。
- production module の import smoke: 成功。
- import 禁止・repetition 導出 meta 面の静的検索: 違反 0。
- `tools/run_tests.py` を焦点 2 範囲と meta-test 3 nodeidへ実行したが、すべて `qstat -Q preflight rc=1`、`child_started=false`、rc=16。pytest node は一件も実走していないため、実装済み・未実走。
- runner が生成した receipt directory は除去済み。

## 波及の静的列挙

- `trial_registry.py` の `assert_registry_rows` callable 2 経路: signature 不変のため静的互換。
- `s8b_holdout_admission.py` と `s8b_scheduler_accounting.py`: v1 factory/layout/loader は不変。後者の権威値が履歴世代の trust root になる。
- `s8b_floor_attempt_launcher.py`: 既存 v1 reserve/terminal API は不変だが、unsafe または未知世代が同居すれば新しい fail-closed 拒否が波及する。
- `test_attempt_registry_core_equivalence.py`、holdout、launcher、campaign、scheduler consumer test は未実走。
- `p3_b4_*` は変更 symbol の直接 consumer ではない。
- 共有 fixture module は未変更。64 hex sibling や古い recovery policy を持つ fixture は新しい列挙規則の影響対象。

## 未完・親へ返す点

- queue 回復後、許可された 3 test file 全体と consumer 19 node、追加 meta-test を `tools/run_tests.py` 経由で実走する必要がある。
- 合成 2 段 v1 の旧 recovery authority を trust root に昇格するかは未裁定のまま。実装は段 4 裁定どおり fail-closed。
- `test_attempt_registry_core_equivalence.py` は許可対象だが変更不要と判断し、既存期待値を保持した。
- 変更 file は許可された 6 file 中の 5 fileだけで、所有外 file の変更はない。

## 総括

- A1' の S1〜S8を実装した。
- A2' の機能は混入させていない。
- diff scope と静的 checker は正常。
- pytest は Pegasus dispatch 障害により未実走。
- 親での実測と統合が必要な未完 checkpoint として返す。