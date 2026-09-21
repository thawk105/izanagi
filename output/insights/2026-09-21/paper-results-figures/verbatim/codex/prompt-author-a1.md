単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (設計の正本。所見の採否・plan v2 の差分・変異事前登録の表): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s4-ruling.md
- 段 2 plan (§1 生成器・§2 test が本単位の詳細。段 4 裁定と食い違う箇所は段 4 裁定が優先): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/plan.md
- 親 brief (不変条件・描かないもの・過去の型 F872 / F623 / F812 / F653): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-brief.md
- pin 閉包 (fig9 の着地 test が何を照合するか): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-pin-closure.md
- 拡張対象の生成器 (全文): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/tools/plotting/plot_a1_sized_paired.py
- 拡張対象の test (全文): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/orchestrator/tests/test_plot_a1_sized_paired.py
- 作図規約: /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/tools/plotting/FIGURE_CONVENTIONS.md
- caption_source (attempt-0002 稿、凍結物。§0 の書かないもの、§2.1 の統計表、§2.6 / §2.7、§3 の限定、§5.1 の SHA-256 表): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md
- attempt-0002 の公開 leaf (tracked、pin。result.json は 270 KB なので `json.load` して key を見る。全文を読まない): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/
- 着地済み fig9 の provenance (構造と caption だけ): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1.provenance.json
- figures README の fig9 節 (着地 test が照合する形): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/figures-README-fig9.md
- test の skip helper: /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/orchestrator/tests/skiputil.py
- self-run harness の要件を課す meta-test: /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/orchestrator/tests/test_plain_runner_coverage.py
- perf 名の条件式を禁じる走査 test (`_python_has_perf_predicate` の規則だけ読む): /work/1/SFC/tanab/izanagi/.codex/worktrees/figs-unit-a1/orchestrator/tests/test_official_perf_closure.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

対象は研究用 repo の**論文図の生成器 (matplotlib) の拡張と、その単体 test**である。セキュリティでも攻撃でもなく、入力は repo 内 tracked の JSON (SHA-256 で束縛) と Markdown だけである。
「既存の A-1 sized 記述図の生成器 (attempt-0001 = 凍結図 fig9 を作ったもの) に、attempt ごとの repo 所有 exact pin 表で attempt-0002 を足し、attempt-0002 の単独記述図 fig14 を
fig9 と同形で描けるようにする。fig9 の再現・着地閉包は 1 文字も変えない」依頼だと理解して読むこと。

# 依頼 — `plot_a1_sized_paired.py` を attempt-0002 に対応させ、test を足す

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_a1_sized_paired.py`
2. `orchestrator/tests/test_plot_a1_sized_paired.py`
3. `probe-fig14/` (新規 dir、untracked のまま。実データで生成した scratch 図の置き場。親が job dir へ退避し repo には入れない)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` / `git merge` / `git rm` を一度も実行しない。commit は親 (と起動器) が行う。
- docs を編集しない: `docs/` 配下の全 file (`docs/paper-story/figures/README.md`、`docs/paper-story/README.md`、`docs/paper-story/results/*`、`docs/handoff/` への file 作成を含む)、`tools/plotting/README.md`、`tools/plotting/FIGURE_CONVENTIONS.md`。
- `docs/paper-story/figures/` へ file を作らない・既存 file を上書きしない (fig9 の png / pdf / provenance は凍結物。最終の fig14 は親が生成する)。`output/` 配下へ書かない。
- 他の生成器・他の test file・`orchestrator/tests/conftest.py`・`orchestrator/tests/acceptance_duration_ledger.json` (台帳は登録しない = 段 4 裁定 P9)・`orchestrator/campaign/*` を編集しない。他の生成器を import しない。
- 公開 leaf・policy・results 稿を編集しない。
- `tools/run_tests.py` と `python -m pytest` は sandbox では使わない (test は下の self-run で走らせる)。
- **既存 test の本文と期待値を変えない** (削除・条件緩和・skip 化・期待値の書換えをしない)。fixture helper に keyword 引数を足すのはよいが、既定の出力 (bytes・hash) は現行と同一にする。
  fixture へ現行 hash を差し込む等でテストを甘くしない (F27)。機構の正例・負例は実体の関数を通し、依存先 (`load_leaf`・`make_figure`・`check_figure_layout`・`_publish_outputs`) を stub しない (F649)。
- **attempt-0001 の不変条件 (fig9 の着地 test が現行生成器で作り直した値と着地 provenance の完全一致を要求する):** 既存定数 (`LEAF_DIR`、`RESULT_JSON`、`RECEIPT_JSON`、`COMPLETE_JSON`、`POLICY_PATH`、
  `PINNED_SHA256` の名前・値・dict の挿入順、`CAPTION_SOURCE`、`FIXED_LANE`、`FIXED_SCOPE`、`COMPARISON_WARNING`、`SCHEMA`) を変えない。attempt-0001 の `load_leaf` 返り値は現行と同じ 9 key・同じ値
  (key を足さない)。attempt-0001 の `_caption` 出力文字列・`_artist_series`・`make_figure` の描画 (figsize・余白・題・凡例)・CLI の既定 (`--attempt` 省略 = attempt-0001) と記録 argv の形を変えない。
- **描かない・書かないもの (fig14):** attempt-0001 の値、2 attempt のプール・差・比・区間の重なり・再現判定、`variance_plan_breach` の原因帰属、sd / planned sigma の比。`improvement` / `regression` / 有意性の語。
- `if` / `while` / 三項の条件式に `perf` を含む名前を置かない (`test_official_perf_closure.py` の走査に掛かる)。

## 作る物 1 — 生成器の拡張

段 4 裁定「plan v2 / fig14」と plan §1 を正本とする。要点:
- attempt 表: 2 entry だけ (`attempt-0001` = 既存定数を参照、`attempt-0002` = `ATTEMPT2_LEAF_DIR` = `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002`、pin 4 件 = result `b7e0518e197500f2daf875e841acabf63f5eddb82bc14e072dd28e3431fe5f74` /
  receipt `98c35cca4fe0e9f12559b8f9dc3acb4c6c5c4c597e5f5cc01a6449533918ecbf` / .complete `7ad34232eaf920babd783140c47018b5c9d2f7665635872d4c2ee3be6f464fb3` / policy `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`、
  caption_source = `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md`)。pin は CLI から渡せない (D1752)。未知 attempt は拒否し既定へ落とさない。
- `load_leaf(repo_root, *, attempt="attempt-0001", expected_hashes=None)`。`expected_hashes` の key 集合は選んだ attempt の pin 表と exact 一致。
- `variance_plan_breach`: 述語 `is (sd > sigma)` の一致は両 attempt。`is False` の拒否は attempt-0001 だけ (既存の例外文のまま)。
- attempt-0002 の返り値だけ `"attempt": "attempt-0002"` を足す。
- caption: attempt-0001 は現行のまま。attempt-0002 は `_caption_attempt2` (plan §1 の固定文 2 つ `Attempt-0001 is neither pooled nor compared with this attempt; no between-attempt difference, ratio, or reproducibility judgment is made.` と
  `No cause is attributed to variance_plan_breach.`、既存 `FIXED_LANE` / `FIXED_SCOPE` / `COMPARISON_WARNING`、workload ごとの breach (true / false)・sample sd・planned sigma (比は作らない)、job / host / source commit / 条件は data から)。
  文頭は `Figure {N}. A-1 balanced five-rep paired comparison, sized run attempt-0002 (...)` の形。図番号は prefix から (既存 `_figure_number`)。
- 描画 (attempt-0002 だけ): panel 題を 3 行 (現行題 / `variance_plan_breach=true` または `false` / `sd <値> tps; planned sigma <値> tps`)、図の上端に図レベル text 1 行
  (`sized run attempt-0002` と、attempt-0001 とプールも比較もしない旨。値は描かない。凡例と重ねない)。figsize・余白は attempt-0002 分岐内だけで調整し、layout 検査を緩めない。
  provenance の `artist_series` は描画関数が実際に使った系列 (表示文字列を含む) から作る (F623)。
- `validate_repo_closure`: provenance に `attempt` が無ければ attempt-0001、あれば表で exact 選択 (未知は拒否)。以降の照合は現行どおり全 key。
- CLI: `--attempt {attempt-0001,attempt-0002}` (既定 attempt-0001)。attempt-0001 のときの記録 argv は現行の形 (`--attempt` を含めない)、attempt-0002 は plan §1 の形。

## 作る物 2 — test の追加

段 4 裁定と plan §2 の一覧を**全部**その名前で書く (段 4 裁定で `test_landed_fig14_rejects_missing_or_partial_bundle` は全欠落 + 単独欠落 3 例に縮めた)。加えて段 4 裁定の禁止句 test
(caption と `fig.findobj(Text)` の可視 text の両方を走査、肯定形の禁止句を列挙し否定の固定文は許す、正常 Figure の panel 題へ違反句を 1 つ足した負例で赤になること) を足す。
- fixture は FIGURE_CONVENTIONS §10 の実寸 (3 workload × 30 対 × 2 arm)。attempt-0002 の fixture は write-heavy / read-heavy で標本 sd が planned sigma を超え、balanced は超えない値にして、生値・pairs・統計・hash を整合させる。
- 実データ test: `test_attempt2_pinned_input_hashes_match_results_document` (稿 §5.1 の表)、`test_attempt2_real_leaf_loads_and_matches_results_document` (稿 §2.1 の表、breach 列 `true / false / true` を含む)。
- 着地 test `test_landed_fig14_repo_closure_and_caption_when_present` (fig9 版と同型、`LANDED` 相当 = `docs/paper-story/figures/fig14_a1_balanced5_sized_attempt2`、bundle 未着地は skip でなく失敗)。
  **親が着地させるまで fig14 の着地 test は赤になる。それは期待赤であり、報告に「未着地のため赤」と書けばよい (xfail 化・skip 化しない)。**
- matplotlib の実描画は attempt-0002 について 4 回以内 (layout 正例・artist / breach 照合・CLI・禁止句負例)。数値 test では Figure を作らない。
- 末尾の `_run()` harness はそのまま使う (新 test も `test_` 名で自動収集される)。

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

matplotlib の cache dir が書けない場合は `MPLCONFIGDIR=probe-fig14/.mplconfig` を付けて走らせる。

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_a1_sized_paired.py` (self-run harness)。既存 28 本を含め、fig14 の着地 test 以外が全部 passed (skip 0) であること。所要 (wall 秒) も報告する。
2. 実データ実走 (FIGURE_CONVENTIONS §10):
   - `python3 tools/plotting/plot_a1_sized_paired.py --attempt attempt-0002 probe-fig14/fig14_a1_balanced5_sized_attempt2` が rc=0 で png / pdf / provenance.json を出すこと。provenance の 3 workload の mean / h / B / sd / planned sigma / classification / breach を稿 §2.1 と照合し、caption 全文を報告に写す。
   - **fig9 の不変性の実測:** `python3 tools/plotting/plot_a1_sized_paired.py probe-fig14/fig9_a1_balanced5_sized_attempt1` (既定 = attempt-0001) を実走し、生成した provenance と着地 fig9 の provenance
     (`docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1.provenance.json`) を、`generated_utc` / `generator.sha256` / `outputs` / `reproduction` を除く全 key で比較して一致を報告する (差があれば全列挙)。
   - 生成した fig14 の provenance を `validate_repo_closure(prov, <worktree root>)` に通し例外が出ないこと。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py` と、test file の列挙・命名に制約を課す他の meta-test (`orchestrator/tests/` を自分で `grep -l` して洗い出す) を走らせる (F42)。
4. 構文確認 (`python3 -m py_compile`)。`_python_has_perf_predicate` を生成器の source に当てて False を確かめる (走査 test が sandbox で走ればそれでよい)。guard で拒否された command はその旨を書く。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個)

## 実装した物
file ごとの要点 (attempt 表・分岐点・caption の構成・描画の差・CLI・closure)。
## 実走した検査
nodeid と passed / failed / skipped 件数、所要。実データ実走の rc と 3 成果物の path、稿との照合結果、caption 全文、fig9 provenance との比較結果、closure の結果、meta-test・perf 走査の結果。
## 未実走・期待赤
走らせられなかったもの、着地前に赤の test 名。
## 受理・拒否の含意
変更前の受理・拒否 (attempt-0001 の leaf のみ、breach true は拒否) と変更後 (attempt-0002 の leaf を pin 表で受理、breach は attempt-0001 だけ拒否)、それぞれ 1 文と通る正例 1 つ。
## 所有外への波及
所有外の caller・共有 fixture・consumer test・列挙型 meta-test への影響の静的列挙 (無ければ「無し」と根拠)。
## 変異事前登録への対応
段 4 裁定の表の M0〜M5 (本単位の分) について、どの test (nodeid) が殺すか。前後に同じ入力を拒否する層があって単一理由にならない変異があれば指摘 (分割案を添える)。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
