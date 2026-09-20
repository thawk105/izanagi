単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (今回の fix の正本。B-1 / B-2 の処置と、変えないもの): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/s6-adjudication.md
- review B の所見 (B-1 must-fix の逐語、B-2): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/codex/review-B.md
- 段 4 裁定 (plan v2。今回変えない部分の正本): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/s4-adjudication.md
- author (前巡) の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/codex/author.md
- 作図規約 (§6 の測定条件の必須項目): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/tools/plotting/FIGURE_CONVENTIONS.md
- 編集対象 1 (生成器): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/tools/plotting/plot_b10_waiting_grid_forest.py
- 編集対象 2 (test): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/orchestrator/tests/test_plot_b10_waiting_grid_forest.py
- 一次資料 (report provenance JSON、tracked、pin。`calibration` と `preregistration.spec.workloads` / `spec.execution` を見る。600 KB なので `json.load` して key を見る): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json
- producer の等価域分類規則の逐語 (B-2 の向きの正本。L1858〜1900): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/verbatim/producer-2a338449b-relation.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

前巡 (author) が作った fig13 の生成器と test に対し、敵対 review が出した must-fix 1 件 (B-1: 作図規約 §6 が必須とする測定条件のうちレコード数と Zipf skew が図・caption・provenance に無い) と should 1 件 (B-2: 等価域の端点 ±3.0% ちょうどを fixture が踏まず `>=` / `<=` の向きが未検査) を直す局所 fix である。
セキュリティでも攻撃でもない。unit worktree の branch `dev-wave-fig13-b10-unit-fix1` (author の終端 commit の上) で作業する。前巡の生成器・test は所有 path にそのまま入っている。

# 依頼 — fix1: 測定条件 (records / skew / rratio 等) を provenance・caption・図に加え、等価域の端点 test を足す

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_b10_waiting_grid_forest.py`
2. `orchestrator/tests/test_plot_b10_waiting_grid_forest.py`
3. `probe-fig13/` (scratch 図の置き場。再生成して上書きしてよい。repo には入れない)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` / `git merge` を一度も実行しない。commit は親が行う。
- docs (`docs/**`、`tools/plotting/README.md`、`FIGURE_CONVENTIONS.md`) と `docs/paper-story/figures/` の file、`output/` 配下、他の生成器・他の test・`orchestrator/campaign/*` を編集しない。
- **既存 test (他 file) の期待値を変えない。** 本 wave の test file (所有 path 2) は B-1 / B-2 に必要な範囲でだけ更新する: fixture に条件 field を足す、caption / provenance の期待に条件を足す、端点 test を足す。反転・緩和・skip・削除・fixture へ現行 hash 差し込みで緑にすることを禁じる (F27)。赤なら実装側が誤り。期待値が誤りなら実装を変えず報告して止める。
- plan v2 §1 の他の検査・図の形 (P1)・固定文 8 文・禁句・provenance の既存 key・閉包 2 関数の契約を変えない。新しい判定経路・gate を足さない。
- `if` / `while` / 三項の条件式に `perf` を含む名前を置かない。`tools/run_tests.py` と `python -m pytest` は sandbox では走らない。

## 作る物 (B-1)

1. `_authority_data` で次を読み、検査し、`measurement_conditions` に加える:
   - `source['calibration']['records']` == 1000000 (定数 `RECORDS_PER_DB = 1_000_000` を module 定数に置き、一致を `_require`)、`calibration['threads']` == `spec['execution']['threads']` == 48 (定数 `THREADS = 48`)、`calibration['env_tag']` == "pegasus"。
   - `spec['workloads']`: name の列が `WORKLOADS` と同順、各 `ycsb_zipf_skew` == "0.9" (定数 `ZIPF_SKEW = "0.9"`)、`ycsb_rmw` == "0"、`ycsb_max_ope` == "10"、`ycsb_rratio` が write-heavy "5" / balanced "50" / read-heavy "95" (定数 `RRATIOS`)。
   - `spec['execution']['extime_s']` == 3 (定数 `EXTIME_S = 3`)、`performance_reps` == REPS。
   - `measurement_conditions` に `records`, `zipf_skew`, `rratios` (workload → 値の dict または順序付き list), `rmw`, `max_ope`, `extime_s` を追加 (既存 key は保持)。
2. caption の `Conditions:` 文に `1,000,000 records, Zipf skew 0.9, read ratio 5 / 50 / 95 (write-heavy / balanced / read-heavy), read-modify-write disabled, max operations 10, 3 s per repetition` 相当を、data から書式化して加える。固定文 8 文と禁句は不変。
3. 図の脚注 (条件行) に `1,000,000 records; Zipf 0.9; rratio 5/50/95` 相当を加える (layout check を通す。必要なら脚注を 2 行に分けるか fontsize を下げる。axes 数 3 は不変)。
4. fixture (`_fixture`) に `calibration` と `spec.workloads` / `spec.execution` の該当 field を実物と同じ形で足し、次の負例を追加: `test_calibration_records_or_threads_mismatch_is_rejected` (records 999999 / calibration.threads 47 でそれぞれ拒否)、`test_workload_skew_or_rratio_mismatch_is_rejected` (skew "0.8" / rratio 入れ替えで拒否)。`test_caption_contains_fixed_literals` に条件文の逐語 (`1,000,000 records` と `Zipf skew 0.9`) を足す。

## 作る物 (B-2)

5. `test_relation_boundaries_match_producer_rule`: `_relation` を端点で直接呼び、(−0.03, +0.03) → inside、(−0.03, +0.02) → inside、(−0.031, +0.02) → overlaps、(+0.03, +0.04) → overlaps (low == +m は outside でない)、(+0.031, +0.04) → outside、(−0.05, −0.031) → outside、(−0.05, −0.03) → overlaps を確かめる。producer の逐語 (射影 file) と同じ向きであることを test の docstring に 1 行で書く。
   加えて、fixture 経由で cell 1 つの区間を端点ちょうどに置き (`ci95_high == +0.03`、report 側の relation は `inside`)、生成器が受理することを `test_cell_interval_on_margin_edge_is_inside` で確かめる (fixture の block 値から端点を作れなければ、`_relation` の直接 test だけにし、その旨を報告に書く)。

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_b10_waiting_grid_forest.py` (self-run harness)。着地 test `test_landed_fig13_repo_closure_and_caption_when_present` は本 fix で caption が変わるため**親が図を再生成して README を直すまで赤**になる (期待赤。skip / xfail 化しない)。それ以外は全部 passed であること。
2. 実データ実走: `python3 tools/plotting/plot_b10_waiting_grid_forest.py probe-fig13/fig13_b10_waiting_grid_forest` が rc=0。provenance の `measurement_conditions` と `caption` の `Conditions:` 文を報告に写す。`validate_repo_closure(prov, REPO)` / `validate_external_sources(prov, EVIDENCE_ROOT)` に通す。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py`、`_python_has_perf_predicate` の直接適用 (False)。
4. pytest が走らない場合の代替 (module import + 直接呼び出し + 検査除去で赤化) は前巡と同じ。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない)

## 所見別の対応表
B-1 / B-2 それぞれ closed / partial / regressed と、変更箇所 (関数名・test 名)。
## 実走した検査
nodeid と passed / failed / skipped 件数、実データ実走の rc と `measurement_conditions` / `Conditions:` 文、閉包 2 関数の結果。
## 未実走・期待赤
着地前に赤の test 名、走らせられなかったもの。
## 受理・拒否の含意
fix 前後で受理集合がどう変わるか (records / threads / skew / rratio の不一致を新たに拒否する) を 2 文と、通る正例 1 つ。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
