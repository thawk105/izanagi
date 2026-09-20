単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (設計の正本。plan v2 と変異事前登録を含む): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/s4-adjudication.md
- 親 brief (背景・不変条件・変更面の実アンカー表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/artifacts/s1-brief.md
- 作図規約の正本: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/tools/plotting/FIGURE_CONVENTIONS.md
- 編集対象 1 (生成器。in-place で一般化する): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/tools/plotting/plot_a2_certification.py
- 編集対象 2 (test。exact pin の更新と A-6 test の追加): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/orchestrator/tests/test_plot_a2_certification.py
- caption_source の稿 (固定文・限定の言い方の出所。§0 主判定文、§2.1 表、§2.2 正しさ、§2.3 abort 率、§3.1 B-10 との関係、§3.4 A-2 と集計しない、§4 限定 1〜12、§5.1 SHA-256 表): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/docs/paper-story/results/2026-09-18-a6-certification-reject.md
- A-6 権威 bytes: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json
- A-6 raw manifest: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json
- A-2 (fig6) の着地済み provenance (A-2 current-full の caption・tracked_inputs が不変であることの基準): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json
- fig10 の着地 test の型 (着地 bundle 3 file + README の caption 逐語 + 「## 着地 bytes の SHA-256」3 行の照合、全欠落は失敗) を参照する: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/orchestrator/tests/test_plot_b7_fixed5_regression.py
- producer (embedded policy の loader・`_validate_certification_cells`・`_parse_condition_gate_admissions`): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/orchestrator/campaign/paper_story_a2_certification.py
- A-6 durable authority (repo 外、読むだけ。root 直下に jobs/ receipts/ がある): /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/raw-manifest.json
- test の skip helper: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/orchestrator/tests/skiputil.py
- self-run harness の要件を課す meta-test: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig11-a6-unit-impl/orchestrator/tests/test_plain_runner_coverage.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

対象は研究用 repo の**論文図の生成器 (matplotlib) と、その単体 test の改修**である。セキュリティでも攻撃でもなく、外部入力は repo 内の tracked JSON と、SHA-256 で束縛された repo 外の測定記録 JSON だけである。「A-2 用に書かれた hash 束縛の certification 図生成器を、同じ protocol の別 study (A-6、workload 1 つ・cell 2 つ・file 6 つ) も描けるように in-place で一般化する。判定・値は再計算せず certification.json から写し、生成器は整合だけを fail-closed で検査する。A-2 (fig5/6/7) の出力は 1 byte も変えない」依頼だと理解して読むこと。

# 依頼 — fig11 (A-6 read-heavy certification reject、attempt a6-20260908b の exact 2 cell 図) のために生成器と test を改修する

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_a2_certification.py` (既存、in-place 一般化)
2. `orchestrator/tests/test_plot_a2_certification.py` (既存、exact pin 更新 + A-6 test 追加)
3. `probe-fig11/` (新規 dir、untracked のまま。実データで生成した scratch 図の置き場。親が job dir へ退避し repo には入れない)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` / `git merge` を一度も実行しない。commit は親が行う。
- docs を編集しない: `docs/` 配下の全 file (`docs/paper-story/figures/README.md`、`docs/paper-story/README.md`、`docs/paper-story/results/*`、`docs/handoff/` への file 作成を含む)、`tools/plotting/README.md`、`tools/plotting/FIGURE_CONVENTIONS.md`。
- `docs/paper-story/figures/` へ file を作らない (最終図は親が生成する)。`output/` 配下へ書かない。
- 他の生成器 (`plot_a1_sized_paired.py`、`plot_b7_fixed5_regression.py` など)、他の test file、`orchestrator/tests/conftest.py`、`orchestrator/tests/README.md`、`orchestrator/campaign/*` を編集しない。
- 入力 JSON (certification / raw-manifest / durable raw / fig6 provenance) と稿を編集しない。
- `tools/run_tests.py` と `python -m pytest` は sandbox では走らない。使わない。
- **既存 test の期待値を変えない。** 変えてよいのは段 4 裁定 plan v2 §2 が名指す exact pin (`test_tracked_authority_literals_and_run_readme_record_agree` の `len == 2` と entry 列挙、`test_t2364_canonical_current_full_measurements_load_without_override` の current-full 一覧) を **A-6 を加える方向へ広げる**ことだけ。A-2 fixture (`_fixture` / `_current_fixture`) が生む挙動・期待値は不変。fixture へ現行 hash を差し込む等でテストを甘くしない (F27)。機構の正例・負例は実体の関数を通し、依存先を stub しない (F649)。
- 生成器へ判定・効果の新規計算経路 (稿に無い閾値・補正・有意差) を足さない。既存の `effect_crosschecks` / median 再計算と一致検査だけにする。
- 受理集合の変更は裁定どおり「study の exact 2 件 (`paper-story-a2-certification` / `paper-story-a6-certification`) と、workload 数 N に比例する閉包 (6 × N file、N request、2 × N axes)」だけ。他の受理形 (第 3 の study、legacy profile の A-6、N=0 など) を足さない。

## 作る物 1 — `tools/plotting/plot_a2_certification.py` の in-place 一般化

段 4 裁定の「plan v2 §1」を正本とし、そこに書かれた定数 (`STUDY_PROFILES` exact 2 件、`CANONICAL_SHA256` の A-6 entry)、`_external_plan` の `6 × N` 閉包、`load_measurements` の study 受理と `N` 一意検査と top-level `study`、`_study_label` の互換既定、`_caption` の study 分岐 (**A-2 current-full の文字列は byte 一致で不変**、A-6 は裁定の骨格を逐語)、`make_figure` の `2 × N` panel と A-6 の suptitle / 脚注、`check_figure_layout` の一般化、`build_provenance` の A-6 caption_source 追加、を全部実装する。

A-6 caption の固定文は次を**逐語**で含めること (test でも逐語検査する):

1. `with one policy workload, the outer status is that workload's verdict itself`
2. `but this is not a performance certification, and the performance reject does not withdraw that correctness evidence`
3. `This is one attempt of five samples per cell; it does not decide a between-run floor exceedance, repeated-attempt reproducibility, or research success or failure, and it does not show that stock is best for read-heavy or that static backoff is harmful for read-heavy in general.`
4. `The same-sign B-10 read-heavy blocks are a historical concordance under nearby conditions, not an independent reproduction, and are not pooled here; the A-2 attempts measured other workloads and are neither pooled nor compared as before/after.`
5. `Mean confidence intervals describe samples; they are not confidence intervals for effects, decisions, or medians, and this artifact makes no significance decision.`

A-6 caption に次を書かない: `significant`、`superior`、`improvement`、`performance certified`、`reproduced`、`replicated`、`research failure`、`Top-row y axes are scaled independently by workload`、`older series`、`sign difference`。
「the adopted cell's median did not exceed the stock cell's median」は `outer_status == "reject"` かつ effect < 0 のときだけ書式化する (それ以外の status では書かない)。
A-6 の suptitle は `A-6 two-cell certification — trace-disabled performance`、脚注は `Single workload (read-heavy, rr95); abort axis is 0-1. Mean t95 CI is descriptive.`、`correctness:` 行の cell 数は data から。x tick は既存の `("no backoff", f"fixed {BACKOFF_FIXED} us")` のまま。figsize は 1 列で layout check が通る幅に調整してよい (A-2 の `(11.8, 7.6)` は不変)。

**A-2 の不変性の自己確認:** 改修後に fig6 の着地 provenance (`docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json`) を `validate_repo_closure(prov, REPO)` に通して例外が出ないこと (= A-2 current-full の `_caption` / `_artist_series` が byte 一致で不変) を、sandbox で `python3 -c` 相当の直接呼び出しで確認し、結果を報告に写す。fig5 / fig7 の provenance も同様に通す。

## 作る物 2 — `orchestrator/tests/test_plot_a2_certification.py` の改修

段 4 裁定の「plan v2 §2」を正本とし、列挙された test を全部書く。既存の `_current_fixture` を policy 源 (A-2 凍結 certification / A-6 凍結 certification の embedded policy) で parametrize して `_a6_fixture(tmp_path)` を作る (A-2 側の出力は不変)。A-6 fixture は実寸 (1 workload rr95 × 2 cell × 5 標本、WAL は `build_start` 2・`build_done` 2・`verify_done` 12・`bench_done` 2・`commit` 2、receipt は admission + source-evidence の 2 frame × 2 cell、manifest 6 file、request 1 件、study `paper-story-a6-certification`) で、本物の `load_measurements` / `make_figure` / `check_figure_layout` / `build_provenance` / `validate_repo_closure` / `main` を通す。
変異事前登録の表 (裁定末尾) の各 negative 変異を殺す test を、表の「期待」欄の名前が分かる形で置くこと (`test_a6_pin_drift_is_rejected`、`test_a6_rejects_six_file_closure_underflow_and_overflow`、`test_a6_provenance_tracks_caption_source_with_current_sha`、`test_layout_rejects_wrong_axes_count`、`test_a6_caption_contains_fixed_literals`、`test_unknown_study_is_rejected`、A-2 の request / created_utc 一意検査を殺す test (既存に無ければ `test_current_rejects_duplicate_workload_requests` を新設)、`test_landed_fig11_rejects_all_missing_outputs`、`test_a2_current_full_caption_is_unchanged_for_landed_fig6`)。
A-6 の実データ test (`test_a6_canonical_current_full_measurements_load_without_override` 相当。root 全欠は skip、部分欠は失敗、期待 median `[10088796, 9505248]`・effect `-0.057841193339621455` を certification.json の値と両方で照合) と、pin 表 exact test (`len == 3`、A-6 の 2 値が稿 §5.1 の表に逐語で現れる) を書く。
着地 test `test_landed_fig11_repo_closure_and_caption_when_present` は fig10 の同名 test と同型: bundle 3 file 実在 → `validate_repo_closure(prov, REPO)` → caption が `docs/paper-story/figures/README.md` に逐語で含まれる → README の fig11 節「## 着地 bytes の SHA-256」の 3 行 (`- \`<basename>\` SHA-256: \`<64 hex>\``) と現物一致 → provenance の `tracked_inputs` に稿の caption_source 行があり現 SHA-256 と一致。bundle 未着地は skip でなく失敗 (全欠落 1 ケースを別 test で検査)。**親が着地させるまでこの test は赤になる。それは期待赤であり、報告に「未着地のため赤」と書けばよい (xfail 化・skip 化しない)。**
末尾の `if __name__ == "__main__":` harness は既存のまま残す。

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_a2_certification.py` (self-run harness、pytest 経由)。sandbox で pytest が起動できなければ、最低限 test module を import して対象 test 関数を直接呼び出し (`tmp_path` は `tempfile.mkdtemp()` で代用)、fixture が成立するかを確かめ、さらに対象の検査を一時的に除去して期待どおり赤化するかまで確かめ、`DIRECT_CALL_PASS` / `DID NOT RAISE` の形で報告する。着地 test 以外が全部 passed であること。
2. 実データの全モード実走 (FIGURE_CONVENTIONS §10): `python3 tools/plotting/plot_a2_certification.py --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b --certification output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json --raw-manifest output/insights/2026-09-08_t2411-paper-story-a6-certification/raw-manifest.json probe-fig11/fig11_a6_certification_reject` が rc=0 で png / pdf / provenance.json の 3 成果物を出すこと。provenance の `effects.rr95`、`cells[].median_tps` 2 値、`cells[].abort_rate` 2 値、`correctness`、`tracked_inputs` の caption_source 行、`caption` を稿 §2.1 / §2.2 / §2.3 / §5.1 と照合し、その結果を報告に写す。A-2 側の回帰として fig6 の実 root (`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b`) で `load_measurements` が通り median 4 値が certification と一致することも確かめる (読めなければその旨を書く)。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py` と、test file の列挙・命名に制約を課す他の meta-test を自分で洗い出して走らせる (F42。親の名指しを網羅と見なさない)。
4. `python3 -m py_compile` 相当の構文確認。guard で拒否された command はその旨を書き、1 の自走結果を正とする。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない)

## 実装した物
file ごとの要点 (定数・検査・図の形・provenance の key・A-2 不変の確認結果)。
## 実走した検査
nodeid と passed / failed / skipped 件数。実データ実走の rc と 3 成果物の path、provenance と稿の照合結果 (median 2 値・effect・abort 率 2 値・correctness・caption_source SHA-256)。fig5/6/7 provenance の `validate_repo_closure` 結果。
## 未実走・期待赤
走らせられなかったもの、着地前に赤の test 名。
## 受理・拒否の含意
改修前の受理・拒否挙動 (A-6 入力は pin 表不在で拒否) と、改修後に受理する入力の形と拒否する入力 (各 1 文)、通る正例 1 つ。
## 所有外への波及
所有外の caller・共有 fixture・consumer test・列挙型 meta-test への影響の静的列挙 (無ければ「無し」と根拠)。
## 変異事前登録への対応
裁定の表の各 id について、どの test (nodeid) が殺すか。前後に同じ入力を拒否する層があって単一理由にならない変異があれば指摘。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
