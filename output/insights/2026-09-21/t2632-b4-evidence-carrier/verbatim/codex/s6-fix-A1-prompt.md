単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage6-ruling.md — **段 6 裁定 (本作業の正本)。§2 の 4 項だけを直す**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage4-ruling.md — 段 4 裁定とプラン v2 (実装子契約の前提)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s6-review-A.md — 段 6 レビュー A (A2・A3・A4・A7 の根拠)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s6-review-B.md — 段 6 レビュー B (B4・B6 の根拠)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s5-author-A.md — 前段の実装子 A の最終報告。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f1.log — 親の焦点走の生 log (失敗 12 件の traceback)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/campaign/p3_s4_loop.py — **所有 file 1 (編集対象、tracked でも編集してよい)**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py — **所有 file 2 (編集対象)**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_b4_closed_critic.py — **所有 file 3 (編集対象は launcher positive test の評価 stub だけ)**。読めなければ即停止

## 作業 (段 6 裁定 §2 の 4 項)

1. **A2:** `main()` の `canonical_b4_proposal_sha256(...)` 呼出しで `B4ProtocolError` が出たら、mode を問わず `initial_proposal_sha256 = None` として
   走行を続ける。docstring (または直近の comment) に「canonical 化できない proposal は hash=null」と書く。回帰 test を 1 つ足す: 非 B-4 で
   `planner.uncertainty` に NaN を持つ proposal が従来どおり評価へ進み、report の entry の `initial_proposal_sha256` が null になる (実 `main` を通す)。
2. **A3 / A4:** `_load_provenance` の docstring を「原本が不在で `.corrupt.*` がある場合だけ停止する」へ、`_append_provenance_entry` の docstring の
   bootstrap の説明を「WAL に履歴が残る bootstrap は再実行を拒否する」へ限定する。挙動は変えない。
3. **A7 / B6:** 本 wave で追加した test の fixture 不具合を直す — `test_base_provenance_corrupt_report_stops` は既存の `reports/` を作り直さない
   (`exist_ok=True` か作成行の削除)、`test_base_provenance_duplicate_reuses_selected_attempt` / `test_base_provenance_keeps_all_attempt_records` は
   `STAGE_VERIFY_DONE` など使う定数を import する、`test_base_provenance_inputs_do_not_read_report` は lock と WAL を持つ admitted campaign を用意する
   (既存の admitted campaign fixture があれば再利用する)。
4. **A7 / B4:** `test_p3_b4_closed_critic.py::test_launcher_positive_uses_real_factory_and_real_base_main_for_commit` の評価 stub が返す certified の出力を、
   実物の certified と同じ形にする — 同一 attempt ID の `build_start` と `commit` を campaign の WAL に記録し、その attempt ID を `records["commit"]` に載せる。
   **この test の assert・期待 rc・期待される commit 内容・stub 以外の fixture は変えない。**

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない。** 所有 3 file 以外の file を作成・編集しない。`p3_b4_prerun_caller.py` とその test、sort / trigger driver、`artifact_admission.py`、
  `campaign_lock.py`、共有 fixture (`campaign_lock_test_support.py`、`conftest.py`) には触れない。
- **既存テストの期待値を変更しない。** ここでいう既存テストは、この worktree の基準 commit `36fb14a3d` に既にある test である。反転・緩和・skip・削除・
  `in` 検査への置換を禁じる。既存テストが赤なら実装側が誤りとして扱い、期待値が誤りだと判断した場合は実装も変えずに報告して止める。
  例外は 2 つだけ: (a) 本 wave で追加した未 land の test (`test_base_provenance_*`、`test_main_provenance_*`、`test_direct_drive_provenance_*`) は編集対象、
  (b) 上の作業 4 の stub 出力の形。
- **本番の attempt 検査 (`_wal_attempt_provenance` の「certified / duplicate / rejected で attempt ID が無ければ停止」) を緩めない。**
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、test file の自走 harness のいずれも使わない)。親が計算ノードで焦点走を行う。
  報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile` の 3 file) は行ってよい。
- 期待値に揮発値 (時刻・乱数 attempt ID・HEAD の SHA) を焼き込まない。機構の正例・負例は実体を通し、依存先を stub しない (評価本体の stub は既存 fixture の定型に限る)。
- 新設・改名した test が既存の制約 meta-test に触れないかを自分で洗い出して静的に確認する (親の名指しを網羅と見なさない)。
- 指示外の受理集合を変えない。規律 2 を緩めない。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更前の挙動 (4 項それぞれ)
2. 変更した file と箇所 (関数名・行)
3. 静的検査の結果 (実行したコマンドと rc)
4. 既存 test の期待値を変えていないことの自己点検 (特に `test_p3_b4_closed_critic.py` の差分が stub 出力に限られること)
5. 所有外への波及の静的列挙
6. 未実走であることの明記と、親が走らせるべき nodeid の候補 (前回の失敗 12 件 + 新設 test)
7. 段 6 裁定 §3 の変異 S15 と、段 4 の S4・S5・S6・S8・S13・S14 について、fix 後の位置と単一理由性の自己点検
最後に `## 総括` を置く。
