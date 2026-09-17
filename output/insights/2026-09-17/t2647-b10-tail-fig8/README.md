# [T-2647] B-10 静的 backoff 右 tail 09-15 正式 cohort の論文図 fig8 を作った — 生成器・test・3 成果物・README

`authority: none` / `default_effect: no-state-change`

**種別:** 実装 (新図種の生成器 + test) と記録 (図の凍結物 + README)。**新規測定はゼロ**。図の入力は 09-15 に完走した
集団報告 3 file (repo 外) だけである。

- 日付: 2026-09-17 (JST)
- wave: `dev-wave-t2647-b10-tail-fig8`、branch `worktree-dev-wave-t2647-b10-tail-fig8`
- 起点 local main: `abc7085ae6e1a69dc294c4f827ed7949e6df5305`
- 依頼: 「B-10 右 tail 09-15 cohort の論文図 fig8 を作る。正本 = 2026-09-17 版 §4 の予定仕様 (本体系列
  `figures/fig8_b10_static_tail_not_observed.{png,pdf,provenance.json}`、新図種の生成器 `plot_b10_static_tail_formal.py`、
  group id 明示) と results 稿 §4.1 (repo 外 3 file、SHA-256)。入力 3 file は `external_inputs` に SHA-256 束縛 (fig6 同型)、
  8 点 × 3 workload の abort 率と throughput (5 反復平均) を区間分類と併せた記述図、言い方は事前登録 §4.5 の固定表現に限り
  caption に `performance_certified: false` を残す、2 本目の論文と共用しない (D1637)。FIGURE_CONVENTIONS §10 と
  figures/README.md の caption・proof chain・provenance pin test を満たす。作図は計測機の外。Codex author + 変異事前登録。
  本題の図 1 枚・生成器・test だけ。規律 2 を緩めない」

## 0. この wave が主張すること・しないこと

**主張する。**

1. **fig8 の 3 成果物が `docs/paper-story/figures/` に着地し、caption が同 README に収録され、着地 test が緑である。** §1・§2。
2. **図の値は集団報告の reps から再計算し、独立再計算 (レビュー B、24 cell) と results 稿 §2.3 の表に全件一致する。**
   判定 (verdict・区間分類・qhat・L・U) は集団報告からコピーし、生成器は再計算しない。§2。
3. **入力 3 file は生成器の pin 表 (SHA-256) と `-complete.json` の `artifacts` で束縛し、pin は CLI から渡せない。**
   pin 表の値は results 稿 §4.1 の表と test で一致を検査する。§2。
4. **変異 matrix (等価対照 1 + 負例 12) と受入全走の結果は §5・§6。**

**主張しない。**

- **飽和が存在しないとは言わない。** caption の言い方は事前登録 §4.5 の固定表現の英訳
  ("Under the predicates of this preregistration, saturation was not observed up to 9999 us, the representable limit of
  the current encoding.") に限る。
- **性能を認証していない。** `performance_certified: false` を caption・provenance・claim boundary に残す。この図を variant
  採用の根拠にしない (絶対規律 2)。
- **機序を言わない** (D1678 / D1724)。図が支えるのは記述的な費用併記と域内非飽和であって主張ではない。
- **fig2c の続きではない。** 別格子・別 cohort・別 report schema。探索走 `t2418-explore` / `t2266-tail` 系列の標本は入っていない。
- **[T-2647] も B-10 も閉じない。D2104 項 7 (再現 cohort の延期) を解除しない。** 版 `2026-09-17.md` と results 稿の
  「図は無い」は当時は真であり、書き換えない。`docs/paper-story/README.md` への fig8 成立の案内は別 wave (§7)。

## 1. 置いたもの

| file | 内容 |
|---|---|
| `tools/plotting/plot_b10_static_tail_formal.py` (新規、Codex author) | 新図種の生成器。自己完結 (標準 lib + numpy + matplotlib)。pin 表・group id・load (fail-closed)・再計算・作図・layout check・provenance・closure 検査・CLI |
| `orchestrator/tests/test_plot_b10_static_tail_formal.py` (新規、Codex author) | 25 test (自走 harness 付き)。実寸 fixture (3 × 8 × 5、`.dat` 120 行、区間 6 × 3)、本物の Figure の layout check、負例 10 種 + 11 変異、pin 表と results 稿 §4.1 の一致、CLI 3 成果物と closure、実データ読込、着地 bundle |
| `docs/paper-story/figures/fig8_b10_static_tail_not_observed.{png,pdf,provenance.json}` (新規、親が login node で生成) | 凍結物。値は results 稿 §2.3 と一致 |
| `docs/paper-story/figures/README.md` | 一覧 1 行 + fig8 節 (何を示す図か・既存図との関係・入力・再現・作図規約への適合・キャプション正文・proof chain) |
| `tools/plotting/README.md` | command 例と契約の要点 |
| `docs/spool/worklog/2026-09-17-dev-wave-t2647-b10-tail-fig8-1.md` | worklog fragment ([T-2647] を `更新`) |
| 本 insight | 記録と逐語 |

触っていない: 既存 7 図の bytes・provenance・節、`plot_a2_certification.py` / `plot_b10_extended_backoff.py` / `plot_backoff.py`、
`FIGURE_CONVENTIONS.md`、`docs/paper-story/README.md`、版、`docs/paper-story-backoff/**`、事前登録、results 稿、phase doc、decisions。

## 2. 図と生成器の契約 (段 4 裁定 §2、段 6 で確定)

- **入力**: root `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/` の `group-report-20260915/t2500-backoff-static-tail-formal.json`
  (5f426ecb…) / `.dat` (758b3121…) / `-complete.json` (7192d1da…)。root 相対 path + SHA-256 を `external_inputs` に記録。
  group id `b10-backoff-grid-20260915T061814Z-545445` は JSON top-level に無く `campaigns[].admission.campaign_path` に含まれる —
  生成器はその包含を検査する。
- **受理集合**: schema / run_kind / verdict (`not-observed-in-any-workload`) の一致、`performance_certified is False`、`failures == []`、
  3 campaign が `admitted*`・`measurement_env == "pegasus"`・threads 48・records 1e6・extime 3・rratio 5/50/95・zipf 0.9・rmw 0・
  max ope 10・grid 8 点・reps 5・stock pin 511c953・`complete`、各 point の reps 5 件 (整数カウンタ正、throughput 正の有限数、
  `abort_rate_recomputed` 一致、`tps[]` 一致)、正しさ記録 5 件すべて `certified` かつ anomaly 0、`.dat` 120 行と JSON の 1:1
  (カウンタ・throughput・abort_rate 列の一致)、区間 6 件が tail の隣接対 (1000 を含めば拒否)、`L = 1 − 2^qU`・`U = 1 − 2^qL`、
  `statistics` (平均 2 種・CV 2 種・abort SD) との相互検算。いずれか不一致で rc=2、成果物ゼロ。
- **コピーと再計算**: verdict・state・区間 state・qhat・qL・qU・L・U・U_flat はコピー。平均・t 分布 95% CI (`t_{0.975,4} = 2.7764`)・
  abort 率 (整数カウンタから全精度)・変動係数・端点比 (9999 / 1250) は reps から再計算。
- **図**: 2 段 × 3 列、x = backoff µs (log、8 tick)、上段 throughput (M tps) 平均 ± CI、下段 abort 率 平均 ± CI。tail 7 点は塗り marker、
  境界参照 1000 は中抜きで線で結ばない。下段の隣接線分は区間 state で描き分け、panel 内注記 "6/6 intervals declining / min L = x.xxx"。
  y は workload-local、比較禁止文を図と caption に持つ。保存前に renderer-backed layout check (6 axis)、赤なら成果物ゼロ。
- **caption**: 図番号は prefix `fig<N>_` から。固定表現の英訳、`performance_certified: false`、group id、job id 3 件、18/18 declining と
  L の範囲 (0.2738〜0.3704)、端点比 (0.444 / 0.481 / 0.400)、条件 (Pegasus compute nodes, 48 threads, …)、certified の射程 (観測した
  YCSB point read/write trace 上の直列化可能性まで)、fig2c との非連続、探索走・t2266 系列の非混合。禁止句 ("does not saturate" 等) は
  test 側で負例検査 (生成器に恒真 gate は置かない)。
- **closure**: `validate_external_sources` (root 相対 path + SHA-256)、`validate_repo_closure` (schema・generator path・着地 PNG / PDF
  の SHA-256・pin 表・artist / caption の再投影・claim boundary)。着地 test は `validate_repo_closure` + caption ⊂ README。

## 3. 数値の検算

親: 生成後の provenance の 24 cell の平均・abort 率が results 稿 §2.3 の表と一致 (`inspect_prov.py`、job dir)。
レビュー B (`verbatim/s6-b.md`): 生成器を import せず標準 lib で `.dat` 120 行と JSON reps から 24 cell の平均・CI・abort 率・CV を再計算し、
provenance と最大相対差 3.79e-15 で全件一致。端点比 0.44357 / 0.48139 / 0.40039、L の範囲 0.27379〜0.37044、18 区間の `L = 1 − 2^qU`・
`U = 1 − 2^qL`、artist_series 15 行、入力 3 件と着地 PNG / PDF の SHA-256、caption の README 収録を確認。results 稿 §2.2 の 108 値・§2.3 の表とも
不一致なし。

## 4. レビューの所見と裁定 (段 6、`verbatim/s6-adjudication.md`)

段 2 / 3 は省き (設計は正本と brief で file 粒度まで確定、1563 wave と同型)、段 6 に敵対レビュー 2 本 (Codex gpt-6-astra、medium、read-only)。

| # | 出所 | 所見 | 裁定 | 対応 |
|---|---|---|---|---|
| R1 | A must-fix | panel 内注記 `L >= 0.299` は四捨五入で偽 (balanced の min L = 0.29889、read-heavy 0.27379) | real (段 4 裁定 §2.3 自身の指定誤り) | `min L = 0.299` (不等式を使わない) |
| R2 | A must-fix | README の group id 参照先 `campaigns[].campaign_path` は実 JSON に無い (正: `campaigns[].admission.campaign_path`)。brief と裁定の誤記が伝播、生成器は正しい | real | README 訂正 |
| R3 | A nit | caption に測定環境名が無い (§6) | real | `measurement_env == "pegasus"` を検査し "Pegasus compute nodes" を条件列へ |
| R4 | A nit | 探索走・t2266 系列の非混合が caption に無い | real | 末尾に 1 文 |
| R5 | A nit | README の相互検算の記述が実装より広い (CI・端点比は照合しない、U も検査) | real | README 2 本を実装に合わせた |
| R6 | A nit | certified の射程 (版 §7) が caption に無い | real | correctness の文に射程を足した |
| R7 | B must-fix | M11 に対し `test_pinned_hashes_are_used_when_no_override` は completion 検査 (G:178) に mask され診断文言差だけの赤 (DW-M03) | real | fixture の completion record を production pin にし、byte 比較だけが拒否する単一理由 fixture へ |
| R8 | B must-fix | 変異の期待 node は完全集合 (M9 は `test_layout_failure_publishes_nothing` も、M1/M4/M5/M6 は着地 test も赤) | real | 最終 commit の container で probe → 完全集合で final (§5) |
| R9 | B nit | `validate_repo_closure` は保存済み cells の再投影であって reps の再計算ではない | real | README proof chain に射程を 1 文 |

refuted: 「declining / keeps decreasing が過大主張」「性能認証との混同」「caption 数値の転記誤り」「README 節欠落」「並べ替え・位置 zip の
誤対応」「parse が SHA 不一致を隠す」「fixture 寸法不足」「禁止句 test・axes gate の恒真」「skip / harness」。brief の「statistics に
median がある」は現物どおり。負例 11 件 (`test_malformed_fields_…`) は単一理由でない箇所があるが登録変異の証拠に使っていない。

fix は Codex fix 子 1 巡 (`verbatim/s6-fix.md`、R1・R3・R4・R6・R7 closed、期待赤 = 着地 test 1 件のみ、回帰なし)。docs は親。
図・provenance を再生成し README の caption を同期した (fix commit `ce39429d5`)。

## 5. 変異 matrix (事前登録 → probe → 本走)

事前登録は段 4 裁定 §4 (`verbatim/s4-adjudication.md`)。逐語 anchor は最終 commit の生成器から `make_mutation_spec.py` (job dir) が生成し、
一意性 (13 件とも 1 回) を検査した。runner = `tools/run_tests.py orchestrator/tests/test_plot_b10_static_tail_formal.py -q -rf --force-dispatch`、
container worktree `ce39429d5`、`--runner-mode dispatch --detached`。

probe 走 (全件 SURVIVED 期待、`verbatim/mutation-spec-probe.json` sha256 `63e37d39…` / `mutation-probe-out.json`、2026-09-17 08:04〜08:24 JST):
baseline PASSED (37 秒)、M0 SURVIVED、負例 12 件はすべて赤 node を出し、その集合はレビュー B の静的予測 (`verbatim/s6-b.md` の表) と
完全一致した。観測集合を本走 spec (`verbatim/mutation-spec-final.json`、sha256 `3dccc90d…`) に写した。

本走 (`verbatim/mutation-final-out.json`、08:25〜08:47 JST): **baseline PASSED (34 秒)、12/12 KILLED (期待 node 完全一致)、M0 SURVIVED、
MISMATCH 0、matching 13/13**。`N::` = `orchestrator/tests/test_plot_b10_static_tail_formal.py::`。

| id | 変異 (最終 commit の位置) | 分類 | 結果 | 赤 node (完全集合) |
|---|---|---|---|---|
| M0 | module docstring に 1 行足す | 等価対照 | **SURVIVED** (期待どおり) | — |
| M1 | pin 表の `.dat` SHA-256 の末尾 1 文字 | pin | **KILLED** | `N::test_pinned_input_hashes_match_results_document`、`N::test_real_root_loads_and_matches_results_document_when_present`、`N::test_landed_fig8_repo_closure_and_caption_when_present` (3) |
| M2 | `performance_certified is False` → `in (False, True)` | 規律 2 | **KILLED** | `N::test_performance_certified_true_is_rejected`、`N::test_malformed_fields_and_counterpart_mismatches_are_rejected` (2。後者は `performance_certified=0` が受理される) |
| M3 | `.dat` の `abort_rate` 列と整数カウンタの一致検査を除去 | 数値忠実性 | **KILLED** | `N::test_dat_abort_rate_disagreeing_with_counters_is_rejected` (1) |
| M4 | 境界参照 1000 を tail 系列に含める (`TAIL_GRID_US` → `GRID_US`) | 図の意味 | **KILLED** | `N::test_artist_series_have_exact_x_and_boundary_reference_is_separate`、`N::test_landed_fig8_repo_closure_and_caption_when_present` (2) |
| M5 | caption から `performance_certified: false` を落とす | 規律 2 | **KILLED** | `N::test_caption_contains_fixed_expression_and_certification_literal`、`N::test_landed_fig8_repo_closure_and_caption_when_present` (2) |
| M6 | `FIXED_WORDING` を "the abort rate does not saturate" に | 事前登録 §4.5 | **KILLED** | `N::test_caption_avoids_forbidden_saturation_claims`、`N::test_caption_contains_fixed_expression_and_certification_literal`、`N::test_landed_fig8_repo_closure_and_caption_when_present` (3) |
| M7 | 区間 `state` を `L > 0.05` から再計算して上書き | コピー契約 | **KILLED** | `N::test_interval_states_are_copied_not_recomputed` (1) |
| M8 | `T95_DF4` を 1.96 に | 統計 | **KILLED** | `N::test_fixture_has_production_shape_and_recomputes_statistics` (1) |
| M9 | `check_figure_layout` の先頭で `return` | §9 fail-closed | **KILLED** | `N::test_bbox_overlap_is_a_failure`、`N::test_layout_failure_publishes_nothing` (2) |
| M10 | `.dat` 行数 `== 120` → `<= 120` | 入力の完全性 | **KILLED** | `N::test_dat_with_missing_row_is_rejected` (1) |
| M11 | SHA-256 の比較を長さ検査に | pin | **KILLED** | `N::test_pinned_hashes_are_used_when_no_override`、`N::test_external_input_hash_drift_is_rejected` (2。R7 の単一理由化後は両方とも受理の消失による kill) |
| M12 | `certified is True` → `in (True, False)` | 規律 2 | **KILLED** | `N::test_uncertified_correctness_record_is_rejected` (1) |

- 12 件はいずれも受理集合または fail-closed 挙動の変化による kill で、診断文言差だけの赤は無い (R7 で M11 の mask を除いた)。
- 等価と判断して登録しなかった候補: 未使用代入の増減、`_display_path` の書式。
- 所要は probe 20 分・本走 22 分 (計算ノード dispatch、1 変異 1.5 分前後)。

## 6. 受入全走

焦点走 (post-s5、tip 4636181a9 相当の作業木、計算ノード request 2756.nqsv、07:22〜07:27 JST): 新 test 25 件 + `test_plain_runner_coverage` 3 件
= 27 passed / 1 skipped (skip は着地前の着地 test)。fix 後は自走 harness 25/25 緑 (login node)。
`python3 tools/check_docs.py` 違反なし、`git diff --check` rc=0、三軸語走査 (`s8b_holdout_freeze search`) holdout hit 0 (rc=0。
fig8 provenance は正例対照 rr50 の一般 hit に fig5〜7 と同じく含まれる)。全史 provenance 監査 (`check_ai_provenance.py`) 新規違反なし。

**final**: 本記録 commit の tip で clean tree から `tools/dev_wave_wait.py acceptance --lease-optional` (post-claim merge で local main を取り込む)
を 1 回投入する。結果は本 README には書かず (受入は記録の後)、受領証 (`acceptance-receipt-final-1.json`、job dir) と worklog が持つ。
child-green でなければ land しない。

## 7. 言ってよいこと・言ってはいけないこと・次の一手

- 言ってよい: fig8 は 09-15 正式 cohort の記述図として `figures/` に存在し、値は集団報告から再計算され、判定はコピーである。
  言い方は事前登録 §4.5 の固定表現に限り、性能は未認証である。
- 言ってはいけない: 「飽和しない」「飽和点が存在しない」、機序、転移、性能認証、B-10 の完了、[T-2647] の閉鎖、
  D2104 項 7 (再現 cohort) の解除、fig2c の続き。
- 次の一手 (別 wave、裁定パッケージ候補): `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」へ fig8 の成立を
  案内する (版 `2026-09-17.md` §4 と results 稿 §3 限定 11 の「図は無い」は当時は真。分類は「当時は真、後続で古くなった記述」)。

## 8. 一次資料

- 逐語: `verbatim/` (brief、段 4 裁定、author prompt / 出力、レビュー A / B prompt / 出力、段 6 裁定、fix prompt / 出力、実装 diff 2 本、
  変異 spec / 結果)。生 log・受領証は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/`。
  `.md` / `.txt` は `git diff --check` のため行末空白を可逆に正規化した (可視文字不変。`s6-a.md` 6 行、`s6-fix.diff.txt` 8 行 +
  EOF の空行 1 行)。原文 (UTF-8 text・sha256・byte 数) は `verbatim/originals.json` (sha256 `176f68d4…`) にあり、
  復元は同 JSON の `text` を UTF-8 で書き出す。
- 図の正本: `docs/paper-story/figures/README.md` の fig8 節。生成器の契約: `tools/plotting/README.md`。
- 事前登録 `docs/b10-backoff-static-tail-preregistration.md` (§4.1・§4.4・§4.5)、results 稿
  `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`、版 `docs/paper-story/2026-09-17.md` §4。
