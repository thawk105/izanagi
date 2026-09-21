単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage6-ruling.md — **段 6 裁定。§4.1 の修正だけを行う**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f3.log — 親の焦点走 f3 の生 log (失敗 1 件)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s6-fix-A2.md — 前巡の fix 子の最終報告。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py — **所有 file (編集対象、tracked でも編集してよい)**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/artifact_admission.py — `require_persisted_certified_commit` (読むだけ、編集しない)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/p3_s4_loop.py — `_resolve_duplicate` / `_duplicate_snapshot` (読むだけ、編集しない)。読めなければ即停止

## 作業

本 wave で追加した helper `_base_selected_commit` が書く `verify_done` の payload を、`require_persisted_certified_commit` が certified と認める実物の形にする
(少なくとも `"anomalies": 0` を足す)。同関数の他の検査 (verdict・certified・workload tag・receipt の operation identity) も満たしているかを静的に確かめ、
足りない field があれば同じ helper の中で補う。`test_base_provenance_duplicate_reuses_selected_attempt` の assert は変えない。
helper を使う `test_base_provenance_keeps_all_attempt_records` の assert (期待 refs は WAL から計算) も変えない。

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない。** 所有 1 file 以外の file を作成・編集しない。production (`p3_s4_loop.py`・`artifact_admission.py`) は変えない。
- **既存テストの期待値を変更しない。** 基準 commit `36fb14a3d` にある test は触らない。編集してよいのは本 wave で追加した未 land の helper だけ。
  反転・緩和・skip・削除・`in` 検査への置換を禁じる。
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、test file の自走 harness のいずれも使わない)。親が計算ノードで走らせる。
  報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile`) は行ってよい。
- 期待値に揮発値を焼き込まない。指示外の受理集合を変えない。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. `require_persisted_certified_commit` の検査項目と、変更前の helper が満たしていなかった項目 (静的)
2. 変更した箇所 (関数名・行)
3. 静的検査の結果 (コマンドと rc)
4. helper を使う他 test への影響の自己点検
5. 未実走であることの明記と、親が走らせるべき nodeid
最後に `## 総括` を置く。
