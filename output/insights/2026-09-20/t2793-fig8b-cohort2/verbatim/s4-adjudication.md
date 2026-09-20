# 段 4 裁定 — [T-2793] fig8b (2026-09-20 07:30 JST)

consult (`codex/s3-consult.md`、sol、2 レンズ 1 本) の所見を real / refuted、採否、scope で裁定し、plan v2 と変異の事前登録を確定する。
裁定 inbox (`dev-wave-jobs/rulings-inbox/`) を 07:22 JST に再走査: T-2793 / fig8b に関する更新なし。

## 1. 所見の裁定

| # | 種別 | 判定 | 採否 | 裁定 |
|---|---|---|---|---|
| A1 | must-fix | real | 採用 | v2 caption は「Within each block, the upper row … / the lower row …」で行を説明する。"share nothing but the grid" は削除し、「各 cohort は別標本・別推定で、y 軸は cohort-local」を書く。固定表現の直前に「各 cohort に独立に適用する」旨を置く |
| A2 | must-fix | real | 採用 | `_figure_number` は v1 経路 (`_caption`) では従来どおり数字だけを受理し、英字 suffix は v2 経路 (`_caption_v2`) だけが受理する (`letter_suffix` 引数)。I1 の確認は着地 test に加え、親が着手前後の fig8 3 file の SHA-256 を比較して記録する (着手前: png `24eab2e8…` / pdf `11071b72…` / provenance `3ccdb0aa…`) |
| A3 | should | real | 採用 | P1 (縦 2 block) を確定。脚注に「block (cohort) 間でも形・傾きを比較しない」を残す |
| A4 | should | real | 採用 (記述) | 「1 ページに入る」は主張しない。親が PDF を目視し、README には描画寸法だけを書く。figsize は 7.2 × 10.6 in を上限に author が決める |
| A5 | should | real | 採用 (親 docs) | README の fig8b 節に cohort 別の再現欄の表 (役割・group id・verdict・事前登録 commit + blob・spec SHA-256・集団報告 3 file の root 相対 path + SHA-256・results 稿・job id) を置く。caption に全 hash は詰めない |
| A6 | nit | real | 採用 | caption 末尾の役割説明 (plan §1.4 の文 13) は文 1 と重複するので落とす。正しさは cohort 別 120 記録で総数を書かない |
| A7 | nit | real | 採用 | 未実測 (2 cohort layout、block 見出し、v2 publish / closure / caption、README 収録、掲載寸法の可読性) を insight に列挙する。consult の「実行履歴を独立に検証していない」も記録 |
| B1 | must-fix | real | 採用 | `_publish_outputs` の caption 設定 (v1 `_caption` 固定) と builder 呼び出しを v1 / v2 に対応させる。v2 の CLI test は `main` → `_publish_outputs` の実経路を通す |
| B2 | must-fix | real | 採用 | `gid="block-title"` の text は plot axes の bbox と交差してはならない (v2 の負例: 見出しを panel 内へ移動 → `FigureLayoutError`、publish ゼロ)。axes 数は mode ごとに期待値を渡す (`expected_axes`、v1 = 6、v2 = 12) |
| B3 | must-fix | real | 採用 | 変異ごとに独立した観測と失敗理由を固定する (§3)。verdict 負例は変異 (f) の値 `saturated-in-all-workloads` そのものを投入する。描画期待値は生成器の `_artist_series_v2` から取らず fixture の生値から計算する |
| B4 | should | real | 採用 | cohort 2 fixture は反復間変動 (CI 幅)・区間値 (`qhat` / `L` 等)・job id・事前登録 commit を cohort 1 と区別可能にし、JSON の reps / `tps` / statistics と DAT を整合させる。「同じ root の別 report dir」に表現を統一 |
| B5 | should | real | 採用 | v1 の展開 argv は不変 (`[python3, G, --measurement-root, root, prefix]`)。v2 は prefix の後ろに option を付ける。役割は test の固定 literal で検査 (`COHORTS[1]["role"] == "primary"`、`COHORTS[2]["role"] == "reproduction"`)。closure の限界 (自己再投影であって reps からの再計算ではない) は fig8 節と同じ文を README に書き、値の独立再計算は実 root test が担う |
| B6 | should | real | 採用 (限定) | top-level key 集合の固定は「この図の v2 出力形状を守る局所 assertion」として closure v2 に置く。汎用 validator・gate・台帳へ広げない。非プールの実証は cohort ごとの生値・統計・artist の対応で行う。test 本数は目標にしない |
| B7 | nit | real | 採用 | plan の行番号は誤り。author には consult の現物アンカー表 (`s3-consult.md` の B7) を渡し、現物を読ませる |
| B8 | nit | real | 採用 (変更) | CLI は `--reproduction-cohort 2` (choices = (2,)、省略時 = 現行の単 cohort 経路)。「主結果 cohort 1 + 独立再現 cohort 2 の併記」であることを help と plotting README に書く。fig8 節の追補文は「既存本文と凍結 3 成果物を保持し、後継図への案内を追記する」とする |
| B9 | nit | real | 採用 | 統合時に fig8 / fig8b / fig10 の一覧・節・command 例を確認する (land 直前の main 再読) |

refuted: 0 件。scope 外 real 所見: 0 件 (裁定パッケージ不要)。

## 2. plan v2 (差分だけ。`s2-plan.md` の他の項は維持、行番号は consult B7 の表で読み替える)

1. **定数**: `COHORTS` 表 (1: primary / 2: reproduction、group id・`completed_jst`・`report_dir`・pin 3 件・`results_document`)。既存名は cohort 1 の別名として残す。
   `SCHEMA_V2`、`CLAIM_BOUNDARY_V2` (= v1 の 6 key + `cohorts_pooled: False` + `cohort_roles_fixed_in_generator: True` + 両 group id)、`NOT_POOLED_WORDING`、
   `NO_REREAD_WORDING`。`FIXED_WORDING` / `COMPARISON_WARNING` / `CLAIM_BOUNDARY` / `SCHEMA` は不変。
2. **loader**: `load_measurements(root, *, expected_hashes=None, cohort=1)`。返り値に `cohort` / `role` / `completed_jst` / `results_document` を足す。
3. **図番号**: `_figure_number(prefix, *, letter_suffix=False)`。v1 `_caption` は既定 (数字のみ)、v2 は `letter_suffix=True`。
4. **caption v2** (`_caption_v2(prov_like, prefix)`): 文 1 (Figure 8b … primary result cohort 1 … and independent reproduction cohort 2 …; performance_certified: false for both)、
   block 構成と cohort 別 job id、「Within each block」の行説明、x 軸 (fig8 と同じ)、cohort 別の区間分類 2 文、「the fixed wording applies to each cohort separately」+
   `FIXED_WORDING` + "9999 us is not a physical limit." + `NO_REREAD_WORDING`、cohort 別 throughput 比 2 文、`NOT_POOLED_WORDING`、descriptive accounting 文、Conditions 文、
   Correctness 文 (cohort 別 120 記録・anomaly 0、限定の語は fig8 と同じ)、`COMPARISON_WARNING` + "The two cohort blocks also use cohort-local y scales and are not to be
   compared for shape or slope."、fig2c / 探索走の除外 2 文。役割説明の重複文は置かない。
5. **図 v2** (`make_figure_v2`): 4 行 × 3 列、block ごとに `_draw_block`、block 見出しは `fig.text(gid="block-title")` ("Primary result — cohort 1 (2026-09-15, group …)" /
   "Independent reproduction — cohort 2 (2026-09-19, group …)")、凡例 1 つ、脚注は `COMPARISON_WARNING` + block 間比較禁止。figsize は 7.2 × ≤10.6。
6. **layout**: `check_figure_layout(fig, axes, *, expected_axes=6)`。`block-title` の text は plot axes bbox と交差不可 (`_intersection > 1` で `FigureLayoutError`)。
7. **publish**: `_publish_outputs(fig, axes, prefix, data, argv, *, caption=_caption, build=build_provenance)` の形で v2 (caption=`_caption_v2`、build=`build_provenance_v2`) に対応。
8. **provenance v2 / closure v2**: `cohorts[]` (順序 primary, reproduction)。closure v2 は generator path、`[(c["cohort"], c["role"])] == [(1, "primary"), (2, "reproduction")]`、
   各 cohort の group id / external_inputs (path・kind・sha256) が `COHORTS[n]` と一致、verdict == `EXPECTED_VERDICT`、`performance_certified is False`、outputs 2 件の sha256、
   artist / caption の再投影一致、`claim_boundary == CLAIM_BOUNDARY_V2` かつ `claim_boundary["cohorts_pooled"] is False` を独立に、top-level key 集合の固定。
9. **CLI**: `--reproduction-cohort` (type=int、choices=(2,)、default=None)。None → 現行 v1 経路 (展開 argv 不変)。2 → `[load(cohort=1), load(cohort=2)]` → `make_figure_v2` →
   v2 publish。展開 argv = `[python3, G, --measurement-root, root, prefix, --reproduction-cohort, 2]`。
10. **test**: fixture `_fixture(tmp_path, cohort=1, **overrides)` / `_seal(root, cohort=1)` / `_fixture_pair(tmp_path)` (同一 root、別 report dir、cohort 2 は反復間変動・区間値・job id・
    事前登録 commit を区別可能)。新 test は §3 の変異ごとに独立した根拠 (fixture 生値からの期待値、凍結稿の pin、固定 literal、不正入力の拒否) を持つ。既存 25 test の期待値は不変。

## 3. 変異の事前登録 (段 6 で probe → final。逐語 anchor と期待 node は実装後の最終 commit から取り、単一理由性を確認してから登録する)

| id | 変異 (位置は関数で指定、逐語は実装後) | 分類 | 期待 | 独立した根拠 (帰属先) |
|---|---|---|---|---|
| M0 | module docstring に 1 行足す | positive (等価対照) | SURVIVED | — |
| M1 | `COHORTS[2]` の DAT pin 末尾 1 文字 | negative | KILLED | cohort 2 pin と cohort2 稿 §4.1 の一致 test (+ 実 root cohort 2 test、着地 fig8b test) |
| M2 | `COHORTS[2]["role"]` → `"primary"` | negative | KILLED | 役割の固定 literal test |
| M3 | loader の verdict 検査 → `in (EXPECTED_VERDICT, "saturated-in-all-workloads")` | negative | KILLED | verdict `saturated-in-all-workloads` を投入する負例 (cohort 2 fixture、再 seal) |
| M4 | `_caption_v2` から `NOT_POOLED_WORDING` を落とす | negative | KILLED | v2 caption の内容 assertion (固定 literal) (+ 着地 fig8b の caption 再投影) |
| M5 | `FIXED_WORDING` → "the abort rate does not saturate" | negative | KILLED | 既存の禁止語 test + 固定表現 literal test (v1 / v2) + 着地 test |
| M6 | `check_figure_layout` 先頭 `return` | negative | KILLED | 既存負例 (v1) + v2 の重なり / 侵入負例 + publish ゼロ負例 |
| M7 | block-title の panel 侵入検査を除去 | negative | KILLED | v2 の見出し侵入負例 (単一理由) |
| M8 | v2 の `_figure_number` を数字のみへ戻す | negative | KILLED | suffix 受理 test (`fig8b_`) (+ v2 caption / CLI / 着地 fig8b の巻き添え) |
| M9 | 下 block に cohort 1 の cell を描く (取り違え) | negative | KILLED | fixture 生値から計算した cohort 2 の期待値と実 line の y の比較 test |
| M10 | `CLAIM_BOUNDARY_V2["cohorts_pooled"]` → `True` | negative | KILLED | `is False` の独立 assertion (+ 着地 fig8b の closure) |
| M11 | closure v2 の位置 (cohort, role) 対検査を除去 | negative | KILLED | (cohort 2, reproduction) と (cohort 1, primary) を入れ替えた provenance の拒否負例 |

- 全 KILLED 期待は probe (全件 SURVIVED 登録) で観測 node を集め、final に完全集合を写す (DW-M08)。
- runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_plot_b10_static_tail_formal.py -q -rf`、独立 clone (D1009)、`--runner-mode dispatch --detached`。
- 規模上限: 生成器 +250 行 / test +300 行程度。超過は差し戻す。

## 4. 段 5 の投入

- author 1 本 (Codex `role=author`、`sandbox=workspace-write`、unit worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2793-unit-impl`、base = wave tip `b7f970dfa`)。
  所有 = `tools/plotting/plot_b10_static_tail_formal.py`、`orchestrator/tests/test_plot_b10_static_tail_formal.py` の 2 file。docs・成果物は親。
- 投入直前に `tools/check_wave_startup.py --repo <unit> --mode midflight`。
