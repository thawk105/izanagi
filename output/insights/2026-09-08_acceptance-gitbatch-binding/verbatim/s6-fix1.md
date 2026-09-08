## 実装結果

- [p3_b4_wiring_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/gitbatch-author/orchestrator/campaign/p3_b4_wiring_probe.py:427)
  - `ls-tree -r -z <40 hex> -- <literal pathspec...>` と exact `cat-file --batch` のみ追加許可。
  - 空、絶対 path、`.` / `..`、NUL、重複、他 magic、非 hex commit を拒否。
  - 旧 `cat-file blob <commit>:<path>` は削除。
  - env、repo root、caller stack 制約は維持。
- [test_p3_b4_wiring_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/gitbatch-author/orchestrator/tests/test_p3_b4_wiring_probe.py:91) に新旧 argv の正負例を追加。
- [test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/gitbatch-author/orchestrator/tests/test_t671_source_binding.py:786) に p3 caller inventory を追加し、[ls-tree framing 7 負例](/work/1/SFC/tanab/izanagi/.codex/worktrees/gitbatch-author/orchestrator/tests/test_t671_source_binding.py:1021)を追加。
- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/gitbatch-author/orchestrator/tests/test_artifact_admission.py:2313) の 2 fake に到達 marker、missing branch の exact 1 回検査と対象 path 検査を追加。
- [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/gitbatch-author/orchestrator/tests/acceptance_duration_ledger.json:1) は add-only updater で 13 node を登録。`nodeid_count` は 19935 から 19948。

旧形については、`mocc_trace_pair.py` と `mocc_trace_pair_anchor.py` が発行するのは `cat-file blob <oid>` であり `<commit>:<path>` ではありません。また p3 probe から両 module への実行経路もありません。probe 窓内で実在するのは `_load_runtime` から capture へ入る新 batch 経路だけでした。

## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| D-01 | closed | 新 2 形の直接検査と actual main 3 driver、計 5 node が緑 |
| D-02 | closed | p3 の `_load_runtime` caller を exact inventory に追加。t671 全 302 node 緑 |
| C-05 | closed | 指定された framing 7 負例を追加し全件緑 |
| C-06 | closed | 2 fake の到達を固定。artifact admission 全 146 node 緑 |

## 検査

| 範囲 | 結果 |
|---|---|
| D-01 焦点 | 5 passed、60 deselected。allowlist 正負 2 nodeと baseline `base` / `sort` / `trigger` |
| `test_p3_b4_wiring_probe.py` 全体 | 65 node 中 64 passed、1 failed |
| `test_t671_source_binding.py` 全体 | 302 passed |
| `test_artifact_admission.py` 全体 | 146 passed |
| `test_ccbench_spawn_sites.py` 全体 | 44 passed |
| `test_acceptance_schedule_order.py` 全体 | 79 passed |
| `test_plain_runner_coverage.py` 全体 | 3 passed |
| `git diff --check` | 緑 |

`run_tests.py` は queue preflight rc=16 で子を起動しなかったため、自走 harness に切り替えました。

p3 全体の唯一の赤は `test_source_and_test_are_the_only_non_output_worktree_changes` です。この既存 gate は未 commit 差分を p3 の 2 path に限定しますが、F1 は同時に `test_t671_source_binding.py` と `test_artifact_admission.py` を正規所有しています。期待値は変更しておらず、p3 suite 全体を緑とは申告しません。

## 静的波及

- production caller: `ident.py`、`artifact_admission.py`、p3 `_load_runtime`。
- private `_run_git` consumer: `mocc_trace_pair.py`、`mocc_trace_pair_anchor.py`。probe 窓へ将来導入された場合、その別 argv は引き続き拒否されます。
- 共有 fixture: `campaign_lock_test_support.py`、`test_layer3_report.py` の `_iter_blobs` 利用。
- consumer test: `test_p3_b4_raw_record_producer.py`、`test_s1_report.py` の capture/live verification。
- production binding/parser 自体は変更していないため、主な波及面は p3 audit allowlist と malformed fixture の検査強化です。

## 差分

```text
orchestrator/campaign/p3_b4_wiring_probe.py        |  21 +++-
orchestrator/tests/acceptance_duration_ledger.json |  15 ++-
orchestrator/tests/test_artifact_admission.py      |  16 ++-
orchestrator/tests/test_p3_b4_wiring_probe.py      | 108 +++++++++++++++++++++
orchestrator/tests/test_t671_source_binding.py     |  81 +++++++++++++++-
5 files changed, 235 insertions(+), 6 deletions(-)
```

所有外の Git 管理 file は変更しておらず、commit も作成していません。

## 総括

- D-01、D-02、C-05、C-06 はすべて closed。
- D-01 の必須 5 node と残る指定 suite は緑。
- p3 全体のみ、複数所有 path と両立しない既存 worktree-scope gate 1 件が赤。
- 変更は所有 5 path、commit なし。