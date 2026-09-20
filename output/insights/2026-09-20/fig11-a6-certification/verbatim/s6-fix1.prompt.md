単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (fix の正本。所見ごとの採否と対応、変異事前登録の改訂): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/s6-adjudication.md
- レビュー A (過剰・削除) の本文: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/codex/review-A.md
- レビュー B (正しさ境界・整合) の本文: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/codex/review-B.md
- 段 4 裁定 (plan v2。段 6 裁定が上書きする箇所以外は有効): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/s4-adjudication.md
- 自分 (author) の前回報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/codex/author.md
- 編集対象 1 (生成器。現在の HEAD は author の終端 commit と同じ内容): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/tools/plotting/plot_a2_certification.py
- 編集対象 2 (test): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/orchestrator/tests/test_plot_a2_certification.py
- caption_source の稿 (§0 主判定文「文を分けたまま使う」、§2.3 abort 率の代表 rep 規則、§4 限定 2・4 (i)〜(v)・6): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/docs/paper-story/results/2026-09-18-a6-certification-reject.md
- A-6 権威 bytes: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json
- A-6 raw manifest: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json
- 親が生成した現行 fig11 provenance (caption の現状。この file は編集禁止。着地 test の直接照合の設計に使う): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/scratch/fig11_a6_certification_reject.provenance.json

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

段 5 で自分が書いた論文図生成器 (matplotlib) と test に、段 6 の設計レビュー 2 本の所見を当てる fix である。セキュリティでも攻撃でもない。
変更は「A-6 caption の文言 (abort 率の代表 rep 規則、正しさ文の分割と限定の補足、時刻の出所、限定 2 の外挿禁止)」と「fig11 着地 test の直接照合の追加」と「固定文 test の追随」だけで、
受理集合・判定経路・A-2 (fig5/6/7) の出力は 1 byte も変えない。

# 依頼 — 段 6 レビュー所見 B-1 / B-2 / B-3(1) / 対応表の 2 点を実装する (段 6 裁定の「対応」欄が正本)

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_a2_certification.py`
2. `orchestrator/tests/test_plot_a2_certification.py`
3. `probe-fig11/` (untracked、scratch 図の置き場。既存の 3 file は上書きしてよい)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` / `git merge` を一度も実行しない。commit は親が行う。
- docs を編集しない (`docs/` 配下の全 file、`tools/plotting/README.md`、`tools/plotting/FIGURE_CONVENTIONS.md`、`docs/handoff/` への file 作成を含む)。`docs/paper-story/figures/` へ file を作らない。`output/` 配下へ書かない。
- 他の生成器・他の test file・`orchestrator/tests/conftest.py`・`orchestrator/campaign/*` を編集しない。入力 JSON と稿を編集しない。
- **既存 test の期待値を変えない。** 反転・緩和・skip 化・削除を禁じる。赤なら実装側が誤りとする。期待値が誤りと考えるなら実装を変えず報告して止める。
  例外は段 6 裁定が名指す自分の新設 test の固定文 (`test_a6_caption_contains_fixed_literals` の literal と、その派生) だけで、これは caption の変更に追随させる。
- A-2 (fig5 / fig6 / fig7) の caption・artist・provenance 射影を変えない (`test_a2_current_full_caption_is_unchanged_for_landed_fig6` と fig5/fig7 の着地 test が緑のまま)。
- 受理集合を変えない (`STUDY_PROFILES`、`6 × N`、一意検査、`2 × N` axes、`validate_repo_closure` 本体は不変)。新しい gate・台帳・一般化を足さない。
- `tools/run_tests.py` と `python -m pytest` は sandbox では走らない。使わない。

## 作る物 1 — 生成器の A-6 caption (`_caption` の A-6 枝だけ)

段 6 裁定の B-1 / B-2 / 対応表の 2 点を当てる。新しい A-6 caption の骨格 (値は data から書式化、`Figure N.` の N は prefix から。**固定文は下線部を逐語**):

`Figure N. A-6 formal certification attempt <attempt> (outer status: <status>). The single workload campaign was request <request> on <host>, campaign claim recorded at <created_utc>; with one policy workload, the outer status is that workload's verdict itself. The top row shows all five trace-disabled performance samples per cell; short bars are medians, and diamonds with error bars are sample means with t-distribution 95% confidence intervals. The gray dashed line is the workload's no-backoff median and the effect denominator. The median effect copied from certification is <label> (<workload>) fixed <BACKOFF_FIXED> us <effect:.4f>%. M tps means million transactions per second. Mean confidence intervals describe samples; they are not confidence intervals for effects, decisions, or medians, and this artifact makes no significance decision. The displayed outer status is the protocol status based on the predefined median ratio<median_note>. This is one attempt of five samples per cell; it does not decide a between-run floor exceedance, repeated-attempt reproducibility, or research success or failure, and it does not show that stock is best for read-heavy or that static backoff is harmful for read-heavy in general. The value is not extrapolated to other read ratios, machines, CCBench pins, or concurrency-control protocols. The bottom row is a descriptive leading indicator: one abort-rate observation per cell, taken from the repetition whose throughput is closest to the median (the runner's representative-repetition rule), with no confidence interval and no causal mechanism claim. Correctness comes from separate trace-enabled runs: all <n> cells were certified. This is not a performance certification. The performance reject does not withdraw that correctness evidence. That evidence is limited: L01 limits it to point-key traces; under D1257 the correctness argv was not independently recorded; artifact hashes alone are not compile-out proof (the evidence is source-routed); and src_token equality does not by itself establish semantic identity of the whole translation unit (limitations (i) to (v) of the results note). <gate_note> Conditions: <threads> threads, <records:,> records, Zipf <skew>, read-modify-write disabled, max operations <max_ope>, <extime> s, <reps> repetitions, CCBench pin <pin>, no perf, trace-disabled performance. The same-sign B-10 read-heavy blocks are a historical concordance under nearby conditions, not an independent reproduction, and are not pooled here; the A-2 attempts measured other workloads and are neither pooled nor compared as before/after.`

`<median_note>` は既存どおり (`outer_status == "reject"` かつ effect < 0 のときだけ `: the adopted cell's median did not exceed the stock cell's median`)。
`<n>` は `len(data['cells'])`。A-6 の suptitle / 脚注 / correctness 行は変えない。A-2 枝は 1 文字も変えない。

## 作る物 2 — test の追随と着地 test の直接照合

- `test_a6_caption_contains_fixed_literals` の literal を新 caption に追随させる。少なくとも次を逐語で検査する:
  `with one policy workload, the outer status is that workload's verdict itself` /
  `Correctness comes from separate trace-enabled runs: all 2 cells were certified. This is not a performance certification. The performance reject does not withdraw that correctness evidence.` /
  `one abort-rate observation per cell, taken from the repetition whose throughput is closest to the median (the runner's representative-repetition rule)` /
  `src_token equality does not by itself establish semantic identity of the whole translation unit` /
  `The value is not extrapolated to other read ratios, machines, CCBench pins, or concurrency-control protocols.` /
  `campaign claim recorded at` /
  既存の B-10 / A-2 文と CI 文と「This is one attempt of five samples per cell; …」文。
  禁止語 test に `aggregate abort-rate` を足す (A-6 caption に "aggregate" を残さない)。
- `test_landed_fig11_repo_closure_and_caption_when_present` に直接照合を足す (段 6 裁定 A-3 / B-3 (1)): provenance の `tracked_inputs` の certification 行の path から tracked certification.json を読み、
  `provenance["study"] == cert["study"]`、`provenance["outer_status"] == cert["status"]`、`provenance["effects"] == cert["effects"]`、
  `[c["median_tps"] for c in provenance["cells"]] == [c["performance"]["median_tps"] for c in cert["cells"]]`、
  `{r["path"] for r in provenance["external_inputs"]} == set(raw_manifest["files"])` (raw_manifest は tracked_inputs の raw_manifest 行の path から読む) を assert する。
  `test_landed_fig11_rejects_all_missing_outputs` は不変。
- 他の既存 test は変えない。

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_a2_certification.py` (self-run harness)。着地 test (`test_landed_fig11_repo_closure_and_caption_when_present`) は fig11 が unit worktree に無いので赤 = 期待赤。それ以外が全部 passed であること。
   pytest が起動できなければ、対象 test 関数を直接呼び出し (`tmp_path` は `tempfile.mkdtemp()`) fixture が成立するか、検査を一時除去して赤化するかまで確かめ `DIRECT_CALL_PASS` / `DID NOT RAISE` で報告する。
2. 実データの再生成: `python3 tools/plotting/plot_a2_certification.py --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b --certification output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json --raw-manifest output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json probe-fig11/fig11_a6_certification_reject` が rc=0 で 3 成果物を出し、caption が上の骨格どおりで、値 (median 2・effect・abort 率 2) が前回と同じであること。新 caption 全文を報告に写す。
3. fig5 / fig6 / fig7 の着地 provenance を `validate_repo_closure(prov, REPO)` に通し例外が無いこと (A-2 不変)。
4. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py` と、前回洗い出した収集契約の meta-test。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない)

## 所見ごとの対応表
B-1 / B-2 / B-3(1) / 対応表 2 点 (時刻の出所、限定 2) の各々について closed / partial / regressed と、対応した file・関数・test 名。
## 実走した検査
nodeid と passed / failed / skipped 件数、実データ再生成の rc と新 caption 全文、fig5/6/7 の closure 結果。
## 受理・拒否の含意
この fix で受理する入力と拒否する入力が変わらないことを 2 文で。通る正例 1 つ。
## 所有外への波及
静的列挙 (無ければ「無し」と根拠)。
## 変異事前登録への対応
段 6 裁定の改訂表 (m5 の新 anchor = 「This is not a performance certification.」文の削除) について、どの test が殺すか。
## 総括
5 行以内。
