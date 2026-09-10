## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F3 symlink 防壁 fixture | partial | 2 node を追加し静的検査は成功。pytest child は未起動のため `closed` は申告しない |

## 足した fixture と node

[test_s8b_attempt_registry.py:1955](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-fix2/orchestrator/tests/test_s8b_attempt_registry.py:1955) に完全な v2 世代を指す 64 hex symlink fixture を追加した。

`test_complete_generation_directory_symlink_is_rejected_but_real_directory_mutates` は次を固定する。

- 負例: 列挙側の明示検査が `[s8b-attempt-registry-storage] generation directory is unsafe or incomplete` で拒否する。
- M5' 相当では、親 component 検査の `HoldoutAdmissionError` による拒否も確認できる。
- 正例: symlink を同じ bytes の実体 directory に戻すと、列挙と `_reserve` mutation が通る。

## 二重計上を検出する node

`test_unchecked_generation_symlink_would_double_count_one_registry_budget` を追加した。

- 最初に現行防壁による拒否を確認するため、防壁を壊した実装では counterfactual 検査前に赤になる。
- symlink 判定、lstat directory 判定、親 component 検査だけを無効化する。
- 実体と alias が同一 inode であり、両方が列挙されることを確認する。
- 実際の seeded replay に両 path を順次渡し、同じ 5 start が `5 → 10` と二重計上されることを固定した。

## 受理集合の変化

production コードは変更していない。現行の拒否挙動、schema、retryable 集合、v2 mutation、claim、resume、terminal projectionに変更はない。

## 波及の静的列挙

- 本 fix の編集は `test_s8b_attempt_registry.py` だけ。
- 所有外 callerへの新しい runtime 波及はない。
- 既存差分の静的 consumer は `trial_registry.py`、`s8b_holdout_admission.py`、`s8b_scheduler_accounting.py`、transitive の `p3_autonomous_workload_trial.py`。
- consumer test候補は `test_trial_registry.py`、`test_attempt_registry_core_equivalence.py`、holdout、launcher、scheduler、reflux、floor campaign各 test。
- 共有 fixture `s8b_floor_evidence_fixture.py` は未変更。
- 新規 test fileと importはなく、file集合 meta-testへの更新は不要。
- worktreeの変更は許可された5 fileのみ。`git add`、commit、branch、stashは未実施。

## 総括

- F3 の完全世代 symlink負例、実体 directory正例、二重計上 nodeを追加した。
- AST parseとnode定義確認、`git diff --check` は成功。
- 2 nodeを `tools/run_tests.py` へ渡したが、`qstat -Q preflight rc=1`、`child_started=false`、rc=16だった。
- 実走 nodeidは0件で、pytest緑は主張しない。
- runnerが生成した許可外 receipt directoryは除去済み。
- F3の状態は `partial`。