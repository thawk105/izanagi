# 段 4 裁定 — [T-2853] (5'') fig1 生成器

段 2・3 は軽量版で省いた (DW-C00: 設計の択一が割れず、正しさ防壁・受理集合に触れない。読み出しは fig2b 生成器と同じ HISTORICAL_RAW の既存経路)。
段 4 直前に裁定 inbox (`dev-wave-jobs/rulings-inbox/` の 2026-09-26 full35・full36) を再走査し、fig1・T-2853 の新しい裁定が無いことを確認した。

## 採否
- (P1)〜(P6) を採用。(P3) の照合は描く値に限り、入力の実在と到達可能性は生死確認 (`probe_replay2.log`) で 3 workload とも実測済み (DW-O13)。
- scope 外: `orchestrator/` の変更、論文ストーリー本文・fig3、R2・再生のやり直し、一般化・新台帳。

## plan v2 (Codex author 1 本、所有 = 下の 2 file だけ)

### `tools/plotting/plot_p2_5_search_cost.py` (新規、上限 450 行)
- CLI: `python3 tools/plotting/plot_p2_5_search_cost.py <out_prefix> [--summary PATH] [--output-root DIR]`。既定 summary = `output/campaigns/p2-5-summary.json`、既定 output root = repo の `output`。出力は `<prefix>.png` / `.pdf` / `.provenance.json`。
- 入力:
  - summary の `rows[]` から workload ごとに `guided_costs`・`guided_failures`・`guided_n`・`informative`・`tied_set`・`k`・`n`・`random_E`・`oracle_E`・`greedy`・`greedy_p_lt`・`guided`。
  - P2-2 campaign: `replay.discover_p2_2_dir(tag, output_root, purpose=CampaignReadPurpose.HISTORICAL_RAW)`。WAL の全 frame を `wal.iter_lines` で検査 (`plot_backoff.load_campaign` と同じ)。
  - landscape は純関数 `landscape_from_records(records)` で組む (`replay.load_landscape` と同じ規則: build_start の genome、bench_done の `median_tps`/`tps`/`leading_indicators`、verify_done の記録上の `certified`、commit 済みだけ)。8 genome が `SILO_SPACE.enumerate()` と一致し、記録上の certified がすべて true でなければ `FigureDataError`。
- 計算 (既存関数をそのまま使い、`orchestrator/` は変えない): `replay.winner_tied_set`、`search_baselines.random_reach_distribution` / `expectation` / `oracle_ceiling` / `greedy_reach(land, tied, 500, 0)` / `_summ` / `prob_superiority` / `prob_superiority_two_sample` / `exact_perm_pvalue_A(..., "less")`。
  A は `informative` が true の workload だけ、厳密 p は summary の `correction_2026_07_03.value.write_heavy_guided_vs_greedy_exact_p` がある write-heavy だけ。
- 照合 (P3、不一致なら出力を 1 つも書かず `FigureDataError`、rc≠0): `k`・`n`・`tied_set`・`random_E`・`oracle_E`・`greedy` の `n`/`mean`/`median`/`min`/`max`/`iqr_lo`/`iqr_hi`・`greedy_p_lt`・`guided` (= `_summ(guided_costs)`)・`guided_n == len(guided_costs)`、
  A は `recalibration_2026_07_02.results.<balanced|write_heavy>.guided_vs_greedy_A` と小数 4 桁で一致、p は correction 値と `math.isclose(rel_tol=1e-12)`。
- 作図 (旧図の視覚符号を継承): 1 行 × 3 panel (read-heavy / balanced / write-heavy、y 共有、目盛り 1〜8)。LLM-guided (x=0): 試行コストの点 `#cd414c` 白縁 (決定論的な横ずらし)、中央値の横棒 `#c1121f`。greedy (x=1): 平均の四角と 25/75 分位 (`_summ` の `iqr_lo`/`iqr_hi`) のひげ `#4a4e69`。random 期待値の点線 `#9aa0a6`、oracle の破線 `#2a9d8f`、直接ラベル `random`・`oracle` は軸の内側。
  注記: informative な panel に `A=0.58` 形 (2 桁)、p がある panel に `p=2.5×10⁻⁴` 形 (有効 2 桁) と A を赤、`guided_failures>0` の panel に `8/12 mis-converged`。題・y 軸名・x 目盛り名は旧図と同じ英文。
- `check_figure_layout(fig, axes)`: 保存前に全 text artist の bbox の相互重なりと figure 外へのはみ出しを検査し、違反で `FigureLayoutError` (出力を書かない)。雛形は `plot_mocc_witlight_four_arm.check_figure_layout`。
- provenance: 生成器 path・sha256、summary と各 campaign の `runs/wal.jsonl`・`campaign.lock` の path・sha256、`campaign_verifier_epoch` (epoch・state・reason_code・`verifier_assessment_basis`、`plot_backoff` と同じ field)、測定条件 (WAL の `run_cmd` の flag と lock の `ccbench_commit`)、workload ごとの計算値 (greedy の度数分布を含む) と照合した key の一覧、
  描いた artist から読み戻した値 (`artist_series`: 点・中央値棒・四角・ひげ・参照線・注記文字)、caption (日本語、下記)、出力 png/pdf の sha256、argv、`generated_utc`、python/matplotlib/numpy の版。
- `validate_repo_closure(provenance, repo_root)`: 入力と出力の sha256 を現物と比べ、違えば `FigureDataError`。
- caption は生成器が 1 つの関数で作る。内容: 旧 linux-baremetal、P2-2 の silo 8 構成、guided は中立 critic の 30 試行 (6/12/12) で原 WAL は削除済みのため summary の凍結値、未到達は予算上限 8 を算入 (事前登録)、greedy は P2-2 WAL の決定論的再生 500 seed、random は解析期待値、oracle は初手ランダム制約下の天井、A = P(誘導<貪欲)+0.5·P(=)、p は厳密 permutation (片側)、verifier epoch E0 の記録をそのまま使い現行 verifier で再検証していないこと、read-heavy は k=4 で到達判定が情報を持たない (注記なし)。

### `orchestrator/tests/test_plot_p2_5_search_cost.py` (新規、上限 300 行)
- T1 実データ: 追跡下の summary と P2-2 campaign から読み、write-heavy の greedy 度数 `{1:62,2:66,3:67,4:35,5:31,6:182,7:57}`、A (0.5813 / 0.2304 を 4 桁)、厳密 p `0.0002521080185096` (rel 1e-12) を固定。
- T2 照合: tmp に写した summary の値を 1 つずつ変えると `FigureDataError` で出力 0 件 — 少なくとも greedy `mean`、`guided_vs_greedy_A`、厳密 p、`random_E` の 4 例 (parametrize)。
- T3 landscape: 合成 record で (a) 記録上の certified が 1 つ false、(b) 7 genome だけ、の各々で `FigureDataError`、(c) 正例 8 genome・全 certified は通る。
- T4 end-to-end: 実データで `main` を tmp prefix へ → 3 出力、`artist_series` の値が計算値と一致 (中央値棒 = 中央値、四角 = 平均、ひげ = 分位、参照線 = random_E / oracle_E、注記文字)。
- T5 レイアウト: 実データの本物の Figure が `check_figure_layout` を通る。同じ Figure に既存注記と重なる text を足すと `FigureLayoutError`。
- T6 closure: tmp の bundle の png を 1 byte 変えると `validate_repo_closure` が `FigureDataError`。着地 bundle があれば (`docs/paper-story/figures/fig1b_phase2_negative.*`) `validate_repo_closure` が通り caption が figures README に含まれる (無ければ skip。親が同 wave で着地させる)。
- 自走で緑を確かめたうえで、例外文の完全一致比較は使わない (先頭行または `match=` の部分一致)。

## 変異の事前登録 (DW-M01、anchor は実装後に一意性を確認)
| ID | 変異 | 期待 kill |
|---|---|---|
| M1 | greedy 統計の照合を外す | T2 (greedy mean) |
| M2 | A の照合を外す | T2 (A) |
| M3 | 厳密 p の照合を外す | T2 (p) |
| M4 | landscape の記録上 certified の検査を外す | T3 (a) |
| M5 | landscape の空間被覆の検査を外す | T3 (b) |
| M6 | `greedy_reach` の seed0 を 0→1 | T1・T4 等 (値の変化) |
| M7 | HISTORICAL_RAW → CERTIFIED_ACCEPTANCE | 実データを読む T1・T4・T5 |
| M8 | 中央値棒に平均を描く | T4 |
| M9 | closure の png sha256 比較を外す | T6 (改変 png) |
| M10 | レイアウト検査を早期 return | T5 (負例) |
| C0 | docstring 1 行だけ変更 (対照) | SURVIVED |
単一理由性は実装後に確認し、満たさない変異は登録から外すか実効 gate へ再照準する (F28)。

## 以後の段
段 5 Codex author 1 本 → 親の自走・焦点走 → 段 6 read-only 敵対レビュー 2 本並列 (DW-S06-A: A = 正しさ・値・caption の忠実性、B = 過剰・削除 (DW-S03 のレンズ)。段 1 brief の「1 本」は DW-S06-A の「実装 wave は必ず 2 本」に合わせて改めた) → fix → 変異 (dispatch) → 親が login で描画・照合・docs → 段 7 記録 → 受入 → 段 9 land。
