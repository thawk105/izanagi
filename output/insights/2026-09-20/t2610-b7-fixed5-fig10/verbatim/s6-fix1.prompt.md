単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (今回の fix の正本。採用した所見と処置、追加変異 m13 / m14): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/s6-adjudication.md
- レビュー A (所見の原文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/codex/s6-review-A.md
- レビュー B (所見の原文): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/codex/s6-review-B.md
- 段 4 裁定 (設計の正本、背景): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/s4-adjudication.md
- 生成器 (この worktree の現物。編集対象): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/tools/plotting/plot_b7_fixed5_regression.py
- test (この worktree の現物。編集対象。本 wave で新設した未 land の test なので期待値の変更可): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/orchestrator/tests/test_plot_b7_fixed5_regression.py
- caption_source の稿 (限定の言い方の出所。§1.4 規則 3・§4 項 3・項 12): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md
- 権威 bytes (`independent_observation_limits` の文言): /work/1/SFC/tanab/izanagi/.codex/worktrees/t2610-unit-fig10/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

対象は研究用 repo の論文図生成器 (matplotlib) とその単体 test に、**独立レビューで採用された局所修正 (文言の訂正 2 件、着地 test の束縛強化 1 件、境界 test 2 件、未使用定数 1 件) を当てる**依頼である。セキュリティでも攻撃でもない。設計 (pin 表・検査の集合・図の形・provenance の key) は変えない。

# 依頼 — [T-2610] fig10 生成器と test へ段 6 裁定の fix を当てる

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_b7_fixed5_regression.py`
2. `orchestrator/tests/test_plot_b7_fixed5_regression.py`
3. `probe-t2610/` (scratch。実データ生成の出力先。untracked のまま)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` を一度も実行しない。commit は親が行う。
- docs を編集しない: `docs/` 配下の全 file (`docs/paper-story/figures/README.md`、`docs/paper-story/README.md`、`docs/handoff/` への file 作成を含む)、`tools/plotting/README.md`。
- `docs/paper-story/figures/` の着地 file (fig10 の png / pdf / provenance.json) を書き換えない (親が再生成する)。`output/` 配下へ書かない。
- 所有外の全 file (他の生成器、他の test、conftest、入力 JSON、稿) を編集しない。
- 本 wave 以前から tracked の既存 test の期待値を変えない。本 wave の test file は編集対象だが、反転・緩和・skip 化・削除で緑にしない。赤なら実装側を直す。
- 受理集合を裁定の範囲外で変えない (pin 表、schema、検査の集合、図の形、provenance の key 集合は不変)。代役 (fixture) を通すために production を緩めない。
- `tools/run_tests.py` と `python -m pytest` は使わない。

## 作る物 (段 6 裁定の表の「処置」列を正本とする)

1. **`CAPTION_SCOPE` (A-1 / B-2):** 値を次の英文にする (逐語):
   `source of the recorded floor judgment transcribed as RECORDED_JUDGMENT and of the wording of limitations and conditions; not the primary authority for measurement values or effects`。
   test で provenance の `caption_source` 行の `authority_scope` がこの文字列と一致することを検査する (既存 `test_provenance_binds_caption_source` を更新)。
2. **固定文 2 (A-2、稿 §1.4 規則 3・§4 項 3):** 次の逐語に置換する:
   `The rule fixed before the results were seen classifies a workload as regression when effect < -floor (strict), floor being the D1639 between-run noise floor: the coefficient of variation of the per-session medians of the stock genome across 8 earlier sessions of 5 repetitions under the same settings, recorded as a lower bound; identity of binary, toolchain and node between that floor measurement and this attempt is not established.`
3. **固定文 6 (A-2、稿 §4 項 12):** 次の逐語に置換する:
   `Correctness comes from separate trace-enabled verify runs under the recorded check configuration, not the performance configuration: all 6 cells are recorded as certified with serializable verdicts (1 legacy and 5 performance records each); certified means serializability of the observed traces under that check configuration and nothing beyond, the correctness workload argv was not independently recorded, and this is not a performance certification.`
   test の固定 literal 集合 (`test_caption_contains_fixed_literals`) をこの 2 文へ更新する。他の固定文 7 つは変えない。
4. **`DF` の使用 (A 削除候補):** caption の `(df 4)` を `(df {DF})` の書式化にする (値は変わらない)。
5. **着地 test の標本束縛 (B-1):** `test_landed_fig10_repo_closure_and_caption_when_present` に、provenance `cells[]` の `samples_tps` と `median_tps` が稿 §2.2 (`_document_values()` の samples / medians) と cell_id ごとに一致する検査を足す (durable root を読まない)。
   `_reject_missing_landed_bundle` の期待 (全欠落・部分欠落は「bundle is incomplete」で失敗) が保たれることを確認する。
6. **境界 test (B-3):** 実寸 fixture を使い、hash を再封印して次の 2 本を足す:
   - `test_effect_equal_to_negative_floor_is_no_regression`: ある workload (判定が no-regression の rr5 か rr50) の床値 JSON の `between_run.cv` を、その workload の effect と `effect == -cv` になる値へ変え (effect は正なので、fixture 側で effect を負にする必要がある。fixture の標本を調整して rr50 の effect を負の小さい値にし、cv をその絶対値ちょうどにする等)、`RECORDED_JUDGMENT` どおり no-regression として**受理される**ことを検査する。厳密比較 `<` が `<=` に変わると拒否される形にすること (変異 m13 の負例)。fixture の作り方は実装に任せるが、median / effect の照合を壊さないこと。
   - `test_correctness_trace_disabled_record_is_rejected`: raw の correctness 記録 1 件の `trace_enabled` を `False` にして (manifest の hash を再封印)、`raw correctness mismatch` で拒否されることを検査する (変異 m14 の負例)。
7. 上の変更で `test_pins_floors_effects_and_judgments_match_results_document` や CLI test が壊れないこと。

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_b7_fixed5_regression.py` (自走 harness)。着地 test は**親が図を再生成するまで赤** (caption / provenance が変わるため)。それ以外が全部 passed であること。
2. 実データの実走: `python3 tools/plotting/plot_b7_fixed5_regression.py --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a probe-t2610/fig10_b7_fixed5_three_workload_regression` が rc=0 で 3 成果物を出し、provenance の `caption` に上の固定文 2・6 が逐語で含まれ、`tracked_inputs` の caption_source 行の `authority_scope` が新しい値であることを `python3` で確認する。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py`。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない)

## 実装した物
所見 id ごとに、変えた関数・定数・test 名。
## 実走した検査
nodeid と passed / failed / skipped 件数。着地 test の赤は「親の再生成待ち」と明記。実データ実走の rc と確認結果。
## 受理・拒否の含意
今回の変更で受理集合がどう変わるか (変わらないなら「変わらない」と根拠)。境界 test 2 本が通る正例と拒否する負例を各 1 文。
## 変異 m13 / m14 への対応
どの test (nodeid) が殺すか。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
