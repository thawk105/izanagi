## 変更点

- **F1:** [tools/mutation_harness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:2391) の runner 結果処理を入れ替え、残存 job の hold 判定を HEAD・bytes 再検査より先にしました。[test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3614) に、残存 job と bytes 変更が同時に起きても hold を作り、M の HEAD と作業木を復元しない試験を追加しました。
- **F2:** [test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3489) に、runner が detached のまま HEAD を H へ動かす場合と touched bytes を変える場合を追加しました。どちらも record を返す前に拒否することを確認します。
- **F3:** [test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3514) の T5 を再照準しました。runner が branch を M に向けて HEAD を attached にした後に例外を出し、復元直前の検査が branch ref を動かさず停止することを確認します。

## 受理と拒否の含意

- **F1:** 残存 job の徴候がなく、runner 後も M が保たれた結果は引き続き受理します。残存 job と bytes 不一致が重なった結果は、復元せず hold として拒否します。正例は、dispatch が正常終了し、HEAD と touched bytes が M のままの実行です。
- **F2:** HEAD と bytes が M に一致する runner 結果は引き続き受理します。HEAD または touched bytes が変わった結果の拒否を新しい回帰試験で固定しました。正例は、detached HEAD=M のまま touched bytes も M blob に一致する実行です。
- **F3:** runner 例外後も detached のままなら、従来どおり安全な復元を受理します。attached HEAD での復元拒否を、復元直前の検査だけに到達する試験で固定しました。正例は、detached HEAD=M で runner が例外を出し、H へ復元する実行です。

## 波及

所有外 caller の呼び出し引数と戻り値、共有 `repo` fixture は変更していません。変更した実行順序は `_apply_mutation` の commit モードに限られ、file-swap の経路は同じです。F1 試験の `/output/` 除外設定は、その一時 fixture repo 内だけに置きました。wrapper・fanout、ledger policy、docs は変更していません。

## 変異 anchor 案の更新

以下の置換前 anchor は、現行 `tools/mutation_harness.py` 内で各 1 箇所です。`∅` は該当行の削除を表します。

| ID | 置換前 → 置換後 | 期待する赤 test |
|---|---|---|
| M1 | `if args.inject == "commit":` 改行 `    _assert_detached_head(repo)` → `if False:` 改行 `    _assert_detached_head(repo)` | `test_commit_attached_head_rejected_before_runner` |
| M2 | `if changed.returncode != 0 or set(changed.stdout.splitlines()) != set(mutated):` → `if changed.returncode != 0:` | `test_commit_post_commit_boundary_rejects_single_defect[extra-path]` |
| M3 | `if parents.returncode != 0 or parents.stdout.split() != [commit, head]:` → `if parents.returncode != 0:` | `test_commit_post_commit_boundary_rejects_single_defect[wrong-parent]` |
| M4 | `_assert_blob_bytes(repo, commit, mutated)` → ∅ | `test_commit_post_commit_boundary_rejects_single_defect[wrong-blob]` |
| M5 | `with _defer_cleanup_signals():` 改行 `    _assert_detached_head(repo)` → `with _defer_cleanup_signals():` | `test_commit_restore_refuses_attached_head_without_moving_branch` |
| M6 | `preserve = pending_stop is not None or hold_present` → `preserve = (pending_stop is not None or hold_present) and inject != "commit"` | `test_commit_orphan_hold_preserves_m_then_manual_resume`、`test_commit_dispatch_orphan_hold_precedes_post_runner_blob_check` |
| M7 | `if _commit_author(repo, head) == HARNESS_EMAIL:` → `if False:` | `test_residual_harness_commit_rejected_before_runner` |
| M8 | 下記の policy 定数 2 行 → file-swap 文言の 2 行 | `test_resume_rejects_injection_policy_mismatch` |
| M9 | 下記の runner 直後検査ブロック → 条件を `and False` にしたブロック | `test_commit_rejects_runner_drift_before_record[head]`、`[bytes]` |

M8 の逐語置換:

```python
COMMIT_SOURCE_POLICY = "fixed repo_head blob plus committed mutation HEAD/blob equality"
COMMIT_RESTORE_POLICY = "soft reset detached mutation commit then restore fixed repo_head blob"
```

→

```python
COMMIT_SOURCE_POLICY = "fixed repo_head blob plus startup/read-back equality"
COMMIT_RESTORE_POLICY = "write fixed repo_head text then exact read_text equality"
```

M9 の逐語置換。F1 の順序変更後、このブロックは `pending_stop` 判定の直後にあります。

```python
        if pending_stop is not None:
            raise pending_stop
        if inject == "commit":
            assert mutation_head is not None
            _assert_detached_head(repo)
            _assert_head(repo, mutation_head)
            _assert_blob_bytes(repo, mutation_head, mutated)
```

→

```python
        if pending_stop is not None:
            raise pending_stop
        if inject == "commit" and False:
            assert mutation_head is not None
            _assert_detached_head(repo)
            _assert_head(repo, mutation_head)
            _assert_blob_bytes(repo, mutation_head, mutated)
```

## 総括

**実装済み・未実走。** 変更量は harness 10 行、test 59 行で上限内です。AST 構文確認、`git diff --check`、M1〜M9 の anchor 一意性確認は通りました。テストの実走は依頼どおり親に委ねます。