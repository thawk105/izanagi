単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (設計の正本。plan v2 §1 生成器 / §2 test と変異事前登録の表を含む): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/s4-adjudication.md
- 親 brief (背景・一次資料の SHA-256・DW-O13 の field 実測・不変条件・(P1) 図の形): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid/artifacts/s1-brief.md
- 作図規約の正本: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/tools/plotting/FIGURE_CONVENTIONS.md
- 雛形 1 (生成器の型: pin 表・`_authority_data`・`check_figure_layout`・`build_provenance`・`validate_repo_closure`・`validate_external_sources`・`_publish_outputs`・`main`): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/tools/plotting/plot_b7_fixed5_regression.py
- 雛形 2 (test の型: fixture・`_reject`・実データ test・稿照合・着地 test・`_run` harness): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/orchestrator/tests/test_plot_b7_fixed5_regression.py
- forest 図の描き方の先例 (`make_contrasts_figure`: 等価域の帯・0 線・errorbar・行 label): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/tools/plotting/plot_dynamic_backoff.py
- 一次資料 1 (report provenance JSON、tracked、pin。600 KB なので `json.load` して key を見る。全文を読まない): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json
- 一次資料 2 (report .md、tracked、pin): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_report_978195.nqsv-23409962b76b.md
- caption_source の稿 (凍結。§0.2 判定しないこと、§2.2 3 族 Holm、§2.4 36 cell の効果と区間、§3 限定 1〜19、§4.1 SHA-256 表、§4.2 受領証 SHA-256): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md
- report 受領証 (repo 外、読むだけ): /work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/23409962b76be959bb523a0cd5a31bc1/submit-receipt.json
- report job 結果 (repo 外、読むだけ): /work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/23409962b76be959bb523a0cd5a31bc1/job-attempts/978195.nqsv/job-result.json
- test の skip helper: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/orchestrator/tests/skiputil.py
- self-run harness の要件を課す meta-test: /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/orchestrator/tests/test_plain_runner_coverage.py
- perf 名の条件式を禁じる走査 test (`_python_has_perf_predicate` の規則だけ読む): /work/1/SFC/tanab/izanagi/.codex/worktrees/fig13-b10-unit-impl/orchestrator/tests/test_official_perf_closure.py

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

対象は研究用 repo の**論文図の生成器 (matplotlib) と、その単体 test の新設**である。セキュリティでも攻撃でもなく、外部入力は repo 内の tracked JSON / Markdown と、SHA-256 で束縛された repo 外の投入受領証 JSON 2 本だけである。
「B-10 待ち方 grid の report (`978195.nqsv`) が出した 3 族 Holm 判定と 36 cell の効果量・95% paired-block 区間・等価域 ±3.0% を、report provenance JSON から読み、records から同じ式で再計算して一致を要求し (判定を作らない)、
1 行 × 3 panel の forest 図として描く自己完結の新 file を作る」依頼だと理解して読むこと。fig11 (`plot_a2_certification.py` の A-6 一般化) と同形の wave だが、本 wave は既存生成器を触らず新 file である。

# 依頼 — fig13 (B-10 待ち方 grid 正式走の forest 図) の生成器と test を新設する

## 所有 path (これ以外は編集禁止)

1. `tools/plotting/plot_b10_waiting_grid_forest.py` (新規)
2. `orchestrator/tests/test_plot_b10_waiting_grid_forest.py` (新規)
3. `probe-fig13/` (新規 dir、untracked のまま。実データで生成した scratch 図の置き場。親が job dir へ退避し repo には入れない)

## 禁止 (各項を個別に守ること)

- `git add` / `git commit` / `git stash` / `git checkout` / `git switch` / `git reset` / `git merge` を一度も実行しない。commit は親が行う。
- docs を編集しない: `docs/` 配下の全 file (`docs/paper-story/figures/README.md`、`docs/paper-story/README.md`、`docs/paper-story/results/*`、`docs/handoff/` への file 作成を含む)、`tools/plotting/README.md`、`tools/plotting/FIGURE_CONVENTIONS.md`。
- `docs/paper-story/figures/` へ file を作らない (最終図は親が生成する)。`output/` 配下へ書かない。
- 他の生成器 (`plot_b7_fixed5_regression.py`、`plot_a2_certification.py`、`plot_dynamic_backoff.py` など)、他の test file、`orchestrator/tests/conftest.py`、`orchestrator/tests/README.md`、`orchestrator/campaign/*` を編集しない。既存生成器を import しない (自己完結、matplotlib + numpy + 標準 library のみ)。
- 一次資料 (provenance JSON / report .md / 受領証 / job 結果) と稿を編集しない。
- `tools/run_tests.py` と `python -m pytest` は sandbox では走らない。使わない。
- **既存 test の期待値を変えない** (所有外なので触れない)。fixture へ現行 hash を差し込む等でテストを甘くしない (F27)。機構の正例・負例は実体の関数を通し、依存先を stub しない (F649)。
- 生成器へ判定・効果の新規計算経路 (稿に無い閾値・補正・有意差・等価性検定・raw p の再列挙) を足さない。records からの再計算は**一致検査のためだけ**で、描く値・provenance の値は再計算値と一致した report の値である。
- caption と図中の文言で、区間が ±3% の内側にあることを「等価」「equivalent」「no difference」と書かない。cell ごとの有意差を書かない。静的右 tail の稿・図 (fig8 / fig8b) と合成・比較しない。機序 (脱同期など) を書かない。
- `if` / `while` / 三項の条件式に `perf` を含む名前 (`perf_*`、`*_perf`、`_perf_`、`perf`) を置かない (`test_official_perf_closure.py` の走査に掛かる)。records の `perf_preflight_receipt` / `performance_binary_sha256` は読まない。

## 作る物 1 — `tools/plotting/plot_b10_waiting_grid_forest.py`

段 4 裁定の「plan v2 §1」を正本とし、そこに書かれた定数・`_authority_data` の 7 項目の検査・`make_figure` (brief の (P1) の形)・`check_figure_layout`・`_caption` (固定文 8 文を逐語、禁句なし)・`build_provenance`・`validate_repo_closure`・`validate_external_sources`・`_publish_outputs`・`main` を全部実装する。
雛形は `plot_b7_fixed5_regression.py` の構造 (定数 → `_require` 系 → `_load_tracked` → `_authority_data` → `load_evidence` → `_caption` → `_artist_series` → `make_figure` → layout check → provenance → closure → publish → main)。

図の形 (brief (P1)、必ず守る):
- 1 行 × 3 panel (左から write-heavy / balanced / read-heavy)。各 panel の y は μ 6 行 (2, 5, 10, 25, 50, 100 µs、上から下、`invert_yaxis`)、x は `symmetric-modulo` 対 `constant` の対相対効果 (%)。x 範囲は 3 panel 共通 (36 cell の区間と ±3% 帯を含む対称範囲)。
- 各行: constant 参照 cell = x 0 に空丸 (効果 0・区間 [0, 0]、構成上の参照)、symmetric-modulo cell = 塗り印 + 95% paired-block 区間の横線 (cap 付き)、3 block の対相対効果 = 小さい灰色の縦 tick (区間より後ろの zorder)。
  `overlaps-equivalence-boundary` の cell は印の形を変える (例: 塗り四角)。凡例に 4 種 (cell effect + 95% interval / overlaps boundary / constant reference / block-level paired effects) と帯を載せる。
- 等価域 ±3.0% は `axvspan` の帯、0 は縦線。
- panel 題 = `<workload>: symmetric-modulo vs constant — <outcome>` と 2 行目 `Holm p = <holm_p:.4g> (raw p = <n>/2^18 = <raw_p:.3g>), 18 pairs, sum of paired effects <sum:+.4f>` (書式は layout check が通る範囲で調整可、値は data から)。
- suptitle に `B-10 waiting-shape grid, report 978195.nqsv: preregistered contrast constant vs symmetric-modulo (3 families x 18 pairs, 36 cell effects)` 相当、脚注に条件 (Pegasus compute nodes, 48 threads, silo, YCSB write-heavy / balanced / read-heavy, 5 reps x 3 blocks, CCBench pin, `official_certification: false`) と
  `Intervals inside the band are not equivalence; no per-cell significance is decided.` 相当の 1 行。図中の文字は最小にし、展開は caption で行う (FIGURE_CONVENTIONS §5)。
- axes はちょうど 3 (凡例は fig 全体に置いてよいが text の重なりは layout check に掛かる)。

caption (英文、決定的、`Figure {N}.` 始まり) は裁定 §1 の固定文 8 文を逐語で含み、禁句 (`equivalent`, `superior`, `desynchroniz`, `performance certified`, `significantly`, `no difference`, `mechanism explains`, `reproduc`) を含まない。
値 (3 族の outcome / raw p 分数と小数 / Holm p / 対 18 / 和の符号、36 cell の集計、点推定が負の cell 数、区間下限が正の cell 数、条件、request、prereg / source commit の短縮 9 桁、pin) は data から書式化する。
`overlaps` の 4 cell は workload と μ を列挙する (`write-heavy mu 2 and 25, balanced mu 2 and 25` の形は data から組む)。

provenance の key は裁定 §1 / brief「成果物の形」のとおり。`tracked_inputs` は 3 行 (`report_provenance` / `report_markdown` = pin、`caption_source` = 稿の path と現 SHA-256 と `authority_scope`)、`external_inputs` は 2 行 (`kind` `report_receipt` / `report_job_result`、root 相対 path、SHA-256)。
`validate_repo_closure(provenance, repo_root, *, expected_hashes=None)` は repo 外を読まずに `_authority_data` を再実行し、provenance の全 key (`generated_utc` / `generator.sha256` / `outputs` を除く) が再構成と一致、outputs の SHA-256 が現物と一致、`artist_series` / `caption` が再構成と一致することを要求する。
`validate_external_sources(provenance, evidence_root)` は 2 file の SHA-256 を照合する。

## 作る物 2 — `orchestrator/tests/test_plot_b10_waiting_grid_forest.py`

段 4 裁定の「plan v2 §2」を正本とし、列挙された test を**全部**その名前で書く。fixture は実寸 (135 record、36 cell、3 族、Holm 3 行 + Cell effects 36 行の report .md、受領証 + job 結果、稿 placeholder) で、fixture 自身が同じ式で judgement を組み立てる (境界を跨ぐ・点推定が負・区間下限が正の cell を各 1 以上含める)。
本物の `load_evidence` / `make_figure` / `check_figure_layout` / `build_provenance` / `validate_repo_closure` / `validate_external_sources` / `main` を通す。
実データ test 3 本 (`test_pins_match_results_document` / `test_document_values_match_report_json` / `test_real_evidence_loads_when_root_present`) は実 repo の稿・JSON・evidence root を読む (evidence root 不在だけ skip、稿 / JSON は tracked なので skip しない)。
稿の parse: §2.2 の表 (`| write-heavy / symmetric-modulo | \`testable\` | **\`different\`** | 18 | <raw p> (= <n> / 2^18) | <Holm p> |` の形)、§2.4 の生値表 (`| write-heavy | 2 | <effect> | <ci95_low> | <ci95_high> | \`<relation>\` | \`estimable\` |` の形)、§4.1 の SHA-256 表 (`| report 成果物 (provenance JSON、…) | \`<path>\` | \`<sha>\` |`)。列の位置は現物を読んで決め、値は `float` の等値 (稿は小数をそのまま写しているので `==` でよい。合わなければ rel 1e-12) で比較する。
着地 test `test_landed_fig13_repo_closure_and_caption_when_present` は雛形 2 の fig10 版と同型: bundle 3 file 実在 → `validate_repo_closure(prov, REPO)` → caption が `docs/paper-story/figures/README.md` に逐語で含まれる → README の fig13 節「## 着地 bytes の SHA-256」の 3 行 (`- \`<basename>\` SHA-256: \`<64 hex>\``) と現物一致 → provenance の `tracked_inputs` の caption_source 行の SHA-256 が稿の現物と一致。bundle 未着地は skip でなく失敗 (全欠落 / 部分欠落は別 test)。
**親が着地させるまでこの test は赤になる。それは期待赤であり、報告に「未着地のため赤」と書けばよい (xfail 化・skip 化しない)。**
`LANDED = "docs/paper-story/figures/fig13_b10_waiting_grid_forest"`。末尾に `_run()` harness と `if __name__ == "__main__": sys.exit(_run())` (雛形 2 と同型、`skiputil.Skip` / `skip` を使う)。

## 検査 (sandbox で走るものだけ。実走した nodeid と件数を報告する)

1. `PYTHONPATH=. python3 orchestrator/tests/test_plot_b10_waiting_grid_forest.py` (self-run harness)。pytest が起動できなければ、最低限 test module を import して対象 test 関数を直接呼び出し (`tmp_path` は `tempfile.mkdtemp()` で代用)、fixture が成立するかを確かめ、さらに対象の検査を一時的に除去して期待どおり赤化するかまで確かめ、`DIRECT_CALL_PASS` / `DID NOT RAISE` の形で報告する。着地 test 以外が全部 passed であること (evidence root は読めるはずなので skip 0 を目標)。
2. 実データの全モード実走 (FIGURE_CONVENTIONS §10): `python3 tools/plotting/plot_b10_waiting_grid_forest.py probe-fig13/fig13_b10_waiting_grid_forest` が rc=0 で png / pdf / provenance.json の 3 成果物を出すこと (既定の `--repo-root` は生成器の位置から、既定の `--evidence-root` は定数)。
   provenance の `families[]` (outcome / raw_p / raw_p_numerator_2pow18 = 6702 / 70 / 2 / holm_p)、`summary` (inside 32 / overlaps 4 / outside 0 / indeterminate 0 / estimable 36)、`cells[]` の write-heavy μ 5 (effect −0.009738229292106326)、`tracked_inputs` の caption_source 行、`external_inputs` 2 行、`caption` を稿 §2.2 / §2.4 / §4.1 / §4.2 と照合し、結果を報告に写す。
   生成した provenance を `validate_repo_closure(prov, REPO)` と `validate_external_sources(prov, EVIDENCE_ROOT)` に通し、例外が出ないことを報告する。
3. `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py` と、test file の列挙・命名・bytecode に制約を課す他の meta-test (`orchestrator/tests/` を `grep -l "test_plot_\|tests/test_" ` で自分で洗い出す) を走らせる (F42。親の名指しを網羅と見なさない)。新 test file が subprocess を起こすなら env に `PYTHONDONTWRITEBYTECODE` を継承させる (bytecode guard checker がある)。
4. `python3 -m py_compile` 相当の構文確認。`python3 orchestrator/tests/test_official_perf_closure.py` 相当の走査が sandbox で走るなら走らせ、走らなければ `_python_has_perf_predicate` を新生成器の source に直接当てて False を確かめる。guard で拒否された command はその旨を書き、1 の自走結果を正とする。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない)

## 実装した物
file ごとの要点 (定数・検査 7 項目・図の形・caption の構成・provenance の key)。
## 実走した検査
nodeid と passed / failed / skipped 件数。実データ実走の rc と 3 成果物の path、provenance と稿の照合結果 (3 族の p、summary、write-heavy μ 5 の effect、caption_source SHA-256、external_inputs 2 行の SHA-256)。closure 2 関数の結果。meta-test の結果。perf 走査の結果。
## 未実走・期待赤
走らせられなかったもの、着地前に赤の test 名。
## 受理・拒否の含意
受理する入力の形 (この report の bytes、または同じ schema・同じ格子・同じ族構成で再計算が一致する fixture) と拒否する入力 (各 1 文)、通る正例 1 つ。
## 所有外への波及
所有外の caller・共有 fixture・consumer test・列挙型 meta-test への影響の静的列挙 (無ければ「無し」と根拠)。
## 変異事前登録への対応
裁定の表の各 id (m0〜m14) について、どの test (nodeid) が殺すか。前後に同じ入力を拒否する層があって単一理由にならない変異があれば指摘 (分割案を添える)。
## 総括
実装済み / 未実走 / 期待赤 / 親への依頼 を 5 行以内。
