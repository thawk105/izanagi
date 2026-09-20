# 段 1 brief — [T-2793] fig8 に第 2 cohort の再現欄を足した後継図 fig8b (2026-09-20 07:20 JST)

## 研究前進 (1 行)

論文図 fig8 (B-10 静的 backoff 右 tail、cohort 1 の記述図) の後継図 fig8b を作り、事前登録 2026-09-19 追記 項 2 /
D2157 が求める「fig8 の再現欄 (主結果 cohort 1 と独立再現 cohort 2 の区別された併記)」を図として実在させる。
完了判定: `docs/paper-story/figures/fig8b_b10_static_tail_cohort2.{png,pdf,provenance.json}` が着地し、caption が同 README に
収録され、着地 test が緑、両 cohort の値が各 results 稿 (cohort 1: `2026-09-16` 稿 §2.3、cohort 2: `2026-09-19-…-cohort2` 稿 §2.3) と
一致し、pin 表が両稿 §4.1 と一致する。新規測定はゼロ。

## scope (純増だけ)

1. `tools/plotting/plot_b10_static_tail_formal.py` の拡張 (Codex author、D95): cohort 引数。cohort 2 の pin 表・group id・path を
   repo 所有定数として追加。2 cohort の figure (P1)、provenance v2 (P3)、caption (P4)、closure 検査の v1/v2 両対応。
2. `orchestrator/tests/test_plot_b10_static_tail_formal.py` の拡張 (Codex author): 実寸 fixture (2 cohort × 3 workload × 8 点 × 5 反復)、
   負例、cohort 2 の pin 表と cohort2 稿 §4.1 の一致、fig8b の着地 test、fig8 (v1) の着地 test は不変。
3. fig8b の 3 成果物 (親が login node で生成、計測機の外)。
4. `docs/paper-story/figures/README.md`: 一覧 1 行 + fig8b 節 + fig8 節末尾に後継図の案内 1 段落 (README は「腐らない入口」で凍結物ではない)。
   `tools/plotting/README.md`: command 例。worklog fragment、insight。
5. scope 外 (依頼どおり): gate・検査・台帳・一般化の追加、版 (`2026-09-19.md`) と results 稿・事前登録 (凍結) の変更、fig8 の bytes、
   decisions の新規 D (裁定は D2157 と追記から導出で足りる。段 7 で再判定)、2 本目の論文 (D1637)。

## 確定済み裁定 (逐語は verbatim/ に射影)

- D2157 / 事前登録 2026-09-19 追記 項 1〜7: 第 2 cohort は独立再現、cohort 1 が主結果、**fig8 の再現欄に両 cohort の group id・集団 verdict・
  束縛情報・一次成果物参照を区別して併記**、合成しない (統合 verdict・プール推定・またぐ有意水準なし)、「再現された」を「飽和しない」へ
  読み替えない、`performance_certified: false`。
- 事前登録 §4.5 の固定表現 ("Under the predicates of this preregistration, saturation was not observed up to 9999 us, the representable
  limit of the current encoding.") に限る。「飽和しない」「飽和点が存在しない」禁止。機序を言わない (D1678 / D1724)。
- figures/README.md 冒頭: 凍結図は上書きしない。後継図は別 filename で、再現可能な生成器を伴うときだけ。
- FIGURE_CONVENTIONS §1 (生値から再計算)・§2 (CI)・§4 (重ね描きは機序目的のときだけ)・§6 (provenance)・§7 (login node)・§9 (layout fail-closed)・
  §10 (実寸 fixture、実データ全モード実走)。
- 依頼: 「主結果 cohort 1 と区別して併記し、合成・プール・統合 verdict は作らない」「本題の作図だけ」「規律 2 を緩めない」。

## 不変条件

- I1: fig8 の 3 file の bytes 不変 (着手時 SHA-256: png `24eab2e8…`, pdf `11071b72…`, provenance `3ccdb0aa…`)。生成器の変更後も
  `test_landed_fig8_repo_closure_and_caption_when_present` は fig8 の provenance v1 をそのまま受理する (artist / caption の射影が byte 同一)。
- I2: pin (SHA-256) は CLI から渡せない。cohort 2 の 3 file の pin は repo 所有定数で、cohort2 稿 §4.1 と test で一致検査。
- I3: 図・provenance・caption のどこにも 2 cohort をまたぐ統計 (プール平均・統合 verdict・差・比・一致度) を置かない。
- I4: cohort 1 = primary、cohort 2 = reproduction の役割は生成器の定数で固定し、CLI で入れ替えられない。
- I5: caption に固定表現・`performance_certified: false`・両 cohort の group id / verdict / 事前登録 commit・「not pooled」の旨を含む。
  禁止語 (test の forbidden list) を含まない。
- I6: 作図は login node、新規測定なし。受入前に `git submodule update --init --recursive` 相当を確認。
- I7: 出力 prefix の図番号は `fig8b_` を受理し、`figX_` は拒否のまま。

## 親の実測 (2026-09-20 07:13〜07:14 JST、worktree = local main b7f970dfa)

- repo 外 root `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/` の 6 file の SHA-256 は両稿 §4.1 と全件一致 (cohort 2: JSON `932f6ccc…`、
  DAT `15b99944…`、complete `93421187…`)。
- 現行 loader に定数 (group id・path・pin) だけ差し替えて cohort 2 を読ませると受理: verdict `not-observed-in-any-workload`、24 cell、
  事前登録 commit `8737cacb4bd286eb3e0784d16dba6eb85e5d6eab` / blob `8511d479…`、job `0:10752.nqsv` / `0:10753.nqsv` / `0:10754.nqsv`
  (`host` は completion に無い — cohort 1 も同じ)、admission `admitted` ×3、18/18 `declining`、L の範囲 0.2782〜0.3732、
  1250→9999 の throughput 比 0.445 / 0.484 / 0.398、境界参照 1000 の write-heavy 平均 992,686.2 — いずれも cohort2 稿 §2.2 / §2.3 と一致。
  単 cohort の layout check も通る。
- 現行 test の自走 harness: 25 passed (login、07:14 JST)。
- (一般化の限界) 上の受理は「定数差し替えで loader が通る」ことだけを示す。2 cohort 図の layout・provenance v2 の closure は未実測。

## provisional 裁定 (攻撃対象)

- (P1) **レイアウト = 縦 2 block (4 行 × 3 列)。** 上 block = cohort 1 (主結果) を fig8 と同じ 2 行 (throughput / abort 率) で描き、
  下 block = cohort 2 (独立再現) を同じ形で描く。y 軸は workload-local かつ cohort-local (block 間で共有しない)。block 見出しに役割
  (primary result / independent reproduction)・group id・完走日を書く。**同一 panel への重ね描きは採らない** (FIGURE_CONVENTIONS §4、
  「近さを一致度として評価しない」の視覚化を避ける)。代案 (攻撃可): 2 行 × 3 列に 2 cohort を marker 違いで重ねる (コンパクトだが比較を誘う)。
- (P2) **CLI = `--cohort {1,2}` (既定 1)。** `1` = 現行どおり単 cohort (fig8 の形、値・caption の射影は不変)。`2` = fig8b の形 (主結果 cohort 1 +
  再現欄 cohort 2 の 2 block)。cohort 2 単独の図は作らない (再現欄は主結果と併記する形でしか意味を持たない、追記 項 2)。
- (P3) **provenance = schema v2** (`izanagi-b10-static-tail-formal-figure-provenance/v2`)。`cohorts: [{role, cohort, group_id, external_inputs,
  report, preregistration, campaigns, measurement_conditions, workloads, correctness}]` (順序 = primary, reproduction)。top-level に
  `claim_boundary` (v1 の 6 key + `cohorts_pooled: false` + `primary_cohort_group_id`)、`artist_series` (cohort 別)、`caption`、`outputs`、
  `reproduction`。`validate_repo_closure` は v1 (fig8) と v2 (fig8b) を schema で分岐し、v1 の受理集合は変えない。
- (P4) **caption** は "Figure 8b." で始め、両 cohort の group id・verdict・job id・事前登録 commit (blob は provenance)・spec 同一を書き、
  固定表現を 1 回、"performance_certified: false" を 1 回、「The two cohorts are not pooled: no combined estimate, no combined verdict,
  no cross-cohort significance level, and the closeness of the two cohorts' values is not evaluated as reproduction accuracy or agreement.」
  の旨、cohort 別の 18/18・L 範囲・throughput 比、条件、正しさ 120 記録 ×2、比較禁止の警告、fig2c / 探索走の除外を書く。
- (P5) **README** は fig8 節の末尾に「後継図 fig8b (再現欄付き) がある。本節と fig8 の bytes は変えない」の 1 段落を足す (fig5 追補と同型)。
  fig8b 節は fig8 節と同じ構成 (何を示す図か / 既存図との関係 / 入力 / 再現 / 作図規約への適合 / キャプション正文 / proof chain)。
- (P6) `_figure_number` の正規表現を `fig([0-9]+[a-z]?)_` に広げる (fig2b / 図2b の先例)。
- (P7) 軽量版 + 敵対検証: 段 2 plan は親起草 (file:line)、段 3 consult 1 本 2 レンズ、段 5 author 1 本、段 6 review 2 本 + fix + 変異 matrix
  (段 4 で事前登録、8 件前後) + 受入。

## 変更面 (実アンカー)

| file | 位置 | 変更 |
|---|---|---|
| `tools/plotting/plot_b10_static_tail_formal.py` | :25-36 定数 (GROUP_ID / REPORT_* / PINNED_SHA256) | cohort 表 (1, 2) へ再編。既存名は cohort 1 の別名として残すか planner が決める |
| 同 | :47 `CLAIM_BOUNDARY`、:49-50 `COMPARISON_WARNING` / `FIXED_WORDING` | v2 用 key 追加、固定表現は不変 |
| 同 | :155-233 `_load_measurements` | cohort 表を引数に取る (group id・path・pin) |
| 同 | :236-239 `_figure_number` | `[a-z]?` |
| 同 | :242-267 `_caption` | cohort 1 用は不変 (v1 射影)、v2 用 `_caption_cohorts` を追加 |
| 同 | :278-292 `_artist_series`、:295-345 `make_figure` | block 化 (2 行 × 3 列を 1 block とし、block 数 = cohort 数)。`_b10_tail_caption` の prefix 固定値 "fig8_…" (:342) は v2 では prefix を引数で受ける |
| 同 | :356-388 `check_figure_layout` | axes 数 = 6 × cohort 数 |
| 同 | :395-411 `build_provenance`、:423-441 `validate_repo_closure` | v2 と v1 の分岐 |
| 同 | :478-500 `main` | `--cohort` |
| `orchestrator/tests/test_plot_b10_static_tail_formal.py` | `_fixture` :46-107 | cohort 引数 (group id・path・sha) で 2 root を作る |
| 同 | 新 test | 2 cohort 図の 12 axes + layout、役割固定、プール不在、caption 要素、cohort2 pin と稿 §4.1、fig8b 着地、`--cohort 3` 拒否、fig8b prefix 受理 |
| `docs/paper-story/figures/README.md` | :12-27 一覧、:723-819 fig8 節、fig8b 節を fig8 節の直後 (fig9 見出し :821 の前) に挿入 | 親が書く |
| `tools/plotting/README.md` | :137-146 | command 例に `--cohort 2` を足す |

## 並列分割・環境

- 実装子 1 本 (author、unit worktree `t2793-unit-impl`、所有 = 生成器 + test の 2 file)。fix は同木で branch を切る。
- 親: fig8b 生成 (login)、README・plotting README・fragment・insight。焦点走・変異は計算ノードへ dispatch (`tools/run_tests.py <test> --force-dispatch`)、
  受入は `tools/dev_wave_wait.py acceptance --lease-optional`。
- 並行 wave: `dev-wave-t2610-fig10` (07:04 起動、段 1 前) は `figures/README.md` と `tools/plotting/README.md` へ末尾追記する見込み。
  本 wave は fig8b 節を fig8 節直後 (中間) に置き、末尾追記と衝突しにくくする。land 直前に main を再読して merge する。
