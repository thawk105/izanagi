単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage6-ruling.md — **段 6 裁定。§4 erratum の「fixture の修正」だけを行う**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f2.log — 親の焦点走 f2 の生 log (失敗 1 件の本文)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s6-fix-A1.md — 前巡の fix 子の最終報告。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py — **所有 file (編集対象、tracked でも編集してよい)**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/p3_s4_loop.py — `_resolve_duplicate` / `_duplicate_snapshot` / `_wal_attempt_provenance` (読むだけ、編集しない)。読めなければ即停止

## 作業

`test_base_provenance_duplicate_reuses_selected_attempt` の fixture を、実在する WAL の形に直す。
失敗した先行 attempt (同 variant の `build_start` + `abort`、別の attempt ID) を、採用される certified attempt (`build_start` … `commit`) の**前**に書く。
`_resolve_duplicate` が `duplicate` を返し、report の entry の `build_attempt_id` が採用 commit の ID で、`wal_refs` が先行 attempt の record を
1 件も含まないことを assert する。「WAL record 数が増えない」など既存の assert は残す。先行 attempt の ID は採用 commit の ID と異なることを確かめる
(乱数 ID を期待値に焼き込まず、WAL から読んで比べる)。共有 helper `_base_selected_commit` を変えるなら、それを使う他の test
(`test_base_provenance_keeps_all_attempt_records` など) の意図が変わらないことを確かめる。

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない。** 所有 1 file 以外の file を作成・編集しない。production (`p3_s4_loop.py`) は変えない。
- **既存テストの期待値を変更しない。** 基準 commit `36fb14a3d` にある test は触らない。編集してよいのは本 wave で追加した未 land の test と、その helper だけ。
  反転・緩和・skip・削除・`in` 検査への置換を禁じる。
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、test file の自走 harness のいずれも使わない)。親が計算ノードで走らせる。
  報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile`) は行ってよい。
- 期待値に揮発値を焼き込まない。指示外の受理集合を変えない。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更前の fixture と、`_resolve_duplicate` が `aborted` を返した理由 (静的)
2. 変更した箇所 (関数名・行)
3. 静的検査の結果 (コマンドと rc)
4. 共有 helper を変えたなら、その helper を使う他 test への影響の自己点検
5. 未実走であることの明記と、親が走らせるべき nodeid
6. 変異 S3 (refs から attempt ID 条件を外す) と再照準後の S4 (commit 由来 ID を同 variant の最初の start の ID に置換) が、この test で単一の理由で落ちるかの自己点検
最後に `## 総括` を置く。
