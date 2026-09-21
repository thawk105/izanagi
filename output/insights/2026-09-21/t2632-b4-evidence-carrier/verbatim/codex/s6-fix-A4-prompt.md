単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage6-ruling.md — **段 6 裁定。§4.2 の修正だけを行う**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/probe_duplicate_fixed.py — 親の probe (修正案を当てた fixture の写し。これと同じ呼び方にする)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py — **所有 file (編集対象、tracked でも編集してよい)**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/commit_receipt_support.py — `log_receipted_commit` の `tags` 引数 (読むだけ、編集しない)。読めなければ即停止

## 作業

本 wave で追加した helper `_base_selected_commit` の `commit_receipt_support.log_receipted_commit(...)` 呼出しに `tags=("legacy", "s2")` を足し、
受領証の検証証拠を helper が書く 2 件の `verify_done` (tag `legacy` / `s2`) と一致させる。これ以外は変えない。

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない。** 所有 1 file 以外の file を作成・編集しない。production と共有 fixture (`commit_receipt_support.py`) は変えない。
- **既存テストの期待値を変更しない。** 基準 commit `36fb14a3d` にある test は触らない。編集してよいのは本 wave で追加した helper の上の 1 呼出しだけ。
- **テストを走らせない。** 親が計算ノードで走らせる。報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile`) は行ってよい。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更前の呼出しと、受領証の証拠が WAL の verify と一致しなかった理由 (静的)
2. 変更した箇所 (関数名・行)
3. 静的検査の結果 (コマンドと rc)
4. helper を使う他 test (`test_base_provenance_keeps_all_attempt_records`) への影響の自己点検
5. 未実走であることの明記と、親が走らせるべき nodeid
最後に `## 総括` を置く。
