## 変更点

編集したのは [tools/mutation_harness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:45) と [orchestrator/tests/test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3342) の 2 ファイルです。harness は追加 154 行・削除 14 行、test は追加 278 行で、指定の規模上限内です。

| plan v2 | 実装箇所 |
|---|---|
| 1. CLI と既定値 | [parser:3183](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:3183) に `--inject {file-swap,commit}` を追加。既定値は `file-swap`。 |
| 2. 起動前検査 | [main:3297](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:3297) で残留 harness commit を両モードとも拒否し、commit モードで detached HEAD を要求。 |
| 3. commit 注入と M の検査 | [Git helper:709](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:709)、[_apply_mutation:2318](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:2318)。親・変更 path・blob bytes・clean・detached を runner 前に、HEAD・detached・blob bytes を runner 直後に確認。 |
| 4. 復元 | [復元 helper:763](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:763)。detached を再確認してから H または認められた M のみ復元し、元 bytes・H blob・clean・HEAD を検査。 |
| 5. orphan hold | [保全処理:2465](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:2465)、[復旧案内:3011](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:3011)。commit 専用 `source_state`、M の保全検査、手動復旧順を追加。 |
| 6. ledger | [作成:2546](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:2546)、[resume 照合:2803](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:2803)。v4 のまま commit 専用 policy 文言でモードを束縛。 |

| test | 追加した検査 |
|---|---|
| T1 | [3384](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3384)：偽 runner が実際の Git blob と disk bytes を比較。等価変異と値変異を対照。 |
| T2 | [3418](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3418)：attached HEAD を plan-only・実走で拒否。 |
| T3 | [3434](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3434)：余分な path、誤った親、誤った blob を個別に作成。 |
| T4 | [3470](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3470)：正常・非 0 rc・timeout 後の復元。 |
| T5 | [3489](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3489)：復元前に attached となった場合の branch ref 保全。 |
| T6 | [3506](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3506)：runner 中の signal 後の復元。 |
| T7 | [3534](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3534)：M の hold、再起動拒否、手動復元後の同モード resume。 |
| T8 | [3585](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3585)：両方向の resume モード不一致。 |
| T9 | [3602](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/orchestrator/tests/test_mutation_harness.py:3602)：残留 M を両モードの fresh・resume・plan-only で拒否。 |

## 変更前の受理・拒否挙動

既定値は `file-swap` で、従来の注入、`_restore_targets`、orphan 時の `mutation-left-in-place`、v4 ledger の `source_policy`・`restore_policy` の文字列を維持しました。既存 test の期待値は変更していません。新たに両モード共通で拒否するのは、HEAD の author email が harness identity である残留 commit です。

## 波及

`tools/mutation_worktree.py` と `tools/mutation_fanout*.py` は編集しておらず、`--inject` も追加転送していないため、これらの caller は既定の file-swap を使います。`orchestrator/tests/test_mutation_worktree.py`、`test_mutation_fanout*.py`、`test_t471_restore_bound.py` と共有 fixture も編集していません。既存の `_restore_targets` 呼び出しは file-swap 側に残しています。harness 本体の変更に伴う tool identity の hash 変化は、既存 ledger の resume 照合へ波及し得ます。

## 変異 anchor 案

以下は実装後コードの置換案です。期待する赤の test 名を併記します。**変異 probe は未実走**のため、単一理由性と赤の到達は親の実走で確定してください。

| ID | 一意に照準する置換前 → 置換後 | 期待する赤 |
|---|---|---|
| M1 | `if args.inject == "commit":\n            _assert_detached_head(repo)` → `if args.inject == "commit":\n            pass` | `test_commit_attached_head_rejected_before_runner` |
| M2 | `if changed.returncode != 0 or set(changed.stdout.splitlines()) != set(mutated):` → `if changed.returncode != 0:` | `test_commit_post_commit_boundary_rejects_single_defect[extra-path]` |
| M3 | `parents.returncode != 0 or parents.stdout.split() != [commit, head]` → `parents.returncode != 0`（[_assert_mutation_commit](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:748) 内） | `test_commit_post_commit_boundary_rejects_single_defect[wrong-parent]` |
| M4 | `_assert_blob_bytes(repo, commit, mutated)` → `pass`（[_assert_mutation_commit](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1418-unit-a/tools/mutation_harness.py:748) 内） | `test_commit_post_commit_boundary_rejects_single_defect[wrong-blob]` |
| M5 | `_assert_detached_head(repo)\n        current = _repo_head(repo)` → `current = _repo_head(repo)` | `test_commit_restore_refuses_attached_head_without_moving_branch` |
| M6 | `preserve = pending_stop is not None or hold_present` → `preserve = (pending_stop is not None or hold_present) and inject != "commit"` | `test_commit_orphan_hold_preserves_m_then_manual_resume` |
| M7 | `if _commit_author(repo, head) == HARNESS_EMAIL:\n            raise HarnessError("HEAD が mutation harness の残留 commit のため停止")` → `if False:\n            raise HarnessError("HEAD が mutation harness の残留 commit のため停止")` | `test_residual_harness_commit_rejected_before_runner` |
| M8 | `COMMIT_SOURCE_POLICY = "fixed repo_head blob plus committed mutation HEAD/blob equality"` と `COMMIT_RESTORE_POLICY = "soft reset detached mutation commit then restore fixed repo_head blob"` → それぞれ既定 file-swap の policy 文字列 | `test_resume_rejects_injection_policy_mismatch` |

## 総括

指定の 2 ファイルへの実装と T1〜T9 の追加は完了しました。構文解析、`git diff --check`、変更ファイルと行数の確認は済みです。**テスト・変異 probe・実 dispatch は未実走**です。残るリスクは、追加テストの実行結果と、実 dispatch で計算ノードが M の HEAD と bytes を観測するかの確認です。