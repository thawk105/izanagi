# fig13 — B-10 待ち方 grid 正式走 (report `978195.nqsv`) の 3 族 Holm 判定と 36 cell の効果量・95% 区間・等価域 ±3.0% の forest 図 (dev-wave、2026-09-20)

台帳 ID 未起票 (ユーザー依頼文がそう明記)。fig11 wave (entry 1738) と同形の軽量版 (段 2・3 省略、段 6 review 2 本は残した)。
branch `worktree-dev-wave-fig13-b10-waiting-grid`、起点 local main `482f19b88` (2026-09-20 19:00 JST)、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig13-b10-waiting-grid`
(brief `artifacts/s1-brief.md`、段 4 裁定 `s4-adjudication.md`、段 6 裁定 `s6-adjudication.md`、codex の prompt / 報告 `codex/`、変異 spec / 結果、受入 receipt)。

## 1. 依頼 (逐語は `verbatim/origin.md`)

凍結稿 `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md` (編集しない) の 3 族 Holm 判定と 36 cell の効果量・95% 区間・等価域 ±3.0% を 1 枚の forest 図にする。
生成器は `tools/plotting/` に新設 (Codex author = D95、FIGURE_CONVENTIONS に従う、計測機の外で描く)、成果物は `docs/paper-story/figures/fig13_b10_waiting_grid_*.{png,pdf,provenance.json}`
と `figures/README.md` の節・日本語キャプション正文。データは稿が束縛する一次資料 (report phase `978195.nqsv` の report・受領証) から読み、provenance は稿を `caption_source` として
SHA-256 束縛する (F36)。書いてよいことは事前登録発効版 §3 の範囲: 区間が ±3% に収まることを「等価性の成立」と呼ばず、36 cell の個別有意差にも読み替えず、右 tail 2 稿と合成しない (D2157)。
README の results 表は触らない。仮想リスク向けの gate・検査・台帳の追加は scope 外。

## 2. 着手時の実測 (段 1)

- fig 番号: figures/README.md の最新は fig12 → fig13 は空き。
- 開始 gate `check_wave_startup.py --mode fresh --external-handoff` rc=0 (乖離 0)。20 分後の midflight gate では main が 12 commit 進行 (paper-methods-ja / T-2700 / T-2304 の land)、本 wave の編集面 (tools/plotting、figures、一次資料、稿) に重なりなし。
- 編集面重複検査 (`overlap_scan.py`): branch tip の hit は既着地 wave の `[T-2638]` 残差記録 commit のみで fig13 / 新生成器 path に hit 0、47 worktree の未 commit 差分 0 (unreadable 0)。
- pin 閉包: `fig13` / 生成器名 hit 0。変更する README 2 file の byte pin なし (着地 test は節内の caption と SHA 行だけを見る)。
- 一次資料 4 件の SHA-256 が稿 §4.1 / §4.2 と全一致: report provenance JSON `a4390603…`、report .md `e237d17d…`、report 受領証 `93a1cd74…` (= JSON の `submission.receipt_sha256`)、job 結果 `d5d4a0ee…`。
- DW-O13 (gate 入力の実在と値域): `judgement.families[]` 3 件 (pairs 18、`differences` 18 値、`raw_p` = 6702 / 70 / 2 ÷ 2^18、`holm_p` ≤ 0.05、`outcome` `different`)、`judgement.cell_effects[]` 36 件
  (`inside` 32 / `overlaps` 4)、`records[]` 135 件。135 record の `median_tps` から差分 54・効果 / 区間 18 cell を同じ式で再計算して cell_effects と差 0 (bit 一致)、`differences` の順序は block-major / μ-minor で一致。
  brief の「3 workload × 3 block × 15 点 × 5 rep = 135 record」は誤記で、正しくは 135 record × 5 sample = 675 sample (review A の指摘。fixture には伝播していない)。

## 3. 設計 (段 4 裁定、軽量版)

(P1) 図の形: 1 行 × 3 panel (workload)、y = μ 6 行、x = `symmetric-modulo` 対 `constant` の対相対効果 (%、3 panel 共通範囲)、帯 = 等価域 ±3.0%、0 の縦線、
constant 参照 cell = 空丸 (効果 0、区間 [0, 0])、symmetric-modulo = 塗り印 + 95% paired-block 区間、3 block の対相対効果 = 灰色 tick、境界跨ぎ = 四角。panel 題に族の判定 (outcome、Holm p、raw p の 2^18 分母の分数、対 18、和の符号)。
不採用: 対差 54 の別 panel、全 135 cell の throughput、参照点 3 種の描画、results 表の更新 (ユーザー指示)、既存生成器の一般化。
生成器は判定を作らず、report の値と再計算の一致を要求する (raw p の全 2^18 列挙は再計算せず分母の整数性と Holm の再計算だけ)。

## 4. 段 5 (Codex author、gpt-6-astra / medium)

unit worktree `.codex/worktrees/fig13-b10-unit-impl` (@482f19b88)。所有 = `tools/plotting/plot_b10_waiting_grid_forest.py` (544 行) + `orchestrator/tests/test_plot_b10_waiting_grid_forest.py` (635 行、49 test)。
19:25 起動 → 19:43 完了 (18 分)。報告: 自走 48 passed / 期待赤 1 (未着地 test)、実データ CLI rc=0 で 3 成果物、稿 §2.2 / §2.4 と一致 (3 族の p、summary inside 32 / overlaps 4 / outside 0、write-heavy μ 5 の effect −0.009738229292106326)、
`validate_repo_closure` / `validate_external_sources` 成功、perf 走査 (`_python_has_perf_predicate`) False、`test_plain_runner_coverage` 3 passed。所有外の編集なし。
親: patch (+1179) を wave worktree へ展開、login (pegasus02) で実データから fig13 生成 rc=0 (PNG は author の probe と bit 一致)、README 2 file を編集、login 自走 49 passed / 0 failed / 0 skipped、
commit `76488debb` (実装、Codex author) / `680d6136d` (docs + 図)。焦点走 1 (計算ノード、request 13484.nqsv、11 file): 491 passed (107 秒)。

## 5. 段 6 (review 2 本 → 裁定 → fix1 → 焦点再レビュー)

- review A (過剰・削除、gpt-6-astra / medium): must-fix 0 / GO。should 5 (A-1 README の「report .md との照合」が実装 (Holm 3 行の値 + cell 36 行の行数) より広い、A-2 `outside-equivalence-range` の受理、A-4 panel 題の情報量、A-5 README の重複、A-6 変異 m4 / m13 の単一理由性)、nit 1 (A-3 epoch 定数)。
  実測: 入力 5 file と画像 2 file の SHA、36 cell の効果・区間を照合し差 0。
- review B (正しさ境界・限定): **must-fix 1 (B-1: FIGURE_CONVENTIONS §6 が必須とするレコード数 1,000,000 と Zipf skew 0.9 が図・caption・provenance に無い)** / NO-GO。should 2 (B-2 等価域の端点 ±0.03 を fixture が踏まず `>=` / `<=` の向きが未検査、B-3 = A-1)。
  値の写し: raw p 3 組 (6702 / 70 / 2 ÷ 2^18)、Holm p、和 (+0.11202543669460518 / +0.13167898485090257 / +0.087727340019642996)、集計 (inside 32 / overlaps 4 / outside 0 / indeterminate 0 / estimable 36)、境界 4 cell (write-heavy μ 2・25、balanced μ 2・25)、
  負の点推定 1 (write-heavy μ 5)、区間下限が正 8、identity、caption・SHA の README 収録、全項目一致。言い方の逸脱 (a)〜(h) なし。
- 裁定 (`s6-adjudication.md`): B-1 採用 (fix 子)、B-2 採用 (fix 子)、A-1 / B-3 採用 (親 docs)、A-5 採用 (親 docs)、**A-2 refuted** (`outside-equivalence-range` は producer `2a338449b` の `b10_backoff_shape_sweep.py` L1895〜1900 の語彙そのもので、規則も等号の向きも同一。拒否へ変えると producer と食い違う)、
  A-3 / A-4 不採用 (epoch 定数は repo 外を読まない閉包に要る。panel 題は読取可能で、短縮は bytes を変えるだけ)、A-6 採用 (m4 は係数だけ `1.96` に変える形で登録済み、m13 は削除形 / 境界形に分割)。
- fix1 (Codex、20:01 → 20:06、5 分): `calibration` (records / threads / env_tag) と `spec.workloads` (skew / rratio / rmw / max_ope) / `spec.execution` (extime_s / performance_reps) を定数と照合して `measurement_conditions` に加え、caption の `Conditions:` と図の脚注に出す。
  負例 2 + 端点 test 2 を追加 (49 → 53)。自走 52 passed + 期待赤 1。親: 図を再生成 (rc=0、PNG は fix 子の probe と bit 一致)、README 更新、login 自走 53 passed、commit `225d0b311` (実装) / `46e3c0a4d` (docs + 図)。
- 焦点再レビュー (Codex focus、20:10〜20:13): 所見 9 件の対応表 = closed 6 (A-1 / A-5 / B-1 / B-2 / B-3、B-1 の実値 7 項目を report JSON と照合して一致) / not-adopted 3 (A-2 / A-3 / A-4、親裁定どおり) / partial 1 (A-6 = 変異 final 待ち)。回帰 0 (固定文 8 文・禁句・図の形・閉包契約・pin・既存 key 不変)。GO。変異への所見: 条件検査 4 種の変異追加 (→ m15〜m18)、m4 は係数のみ、m13a / m13b 分割。
- 焦点走 2 (fix1 後、同 11 file、計算ノード request 13502.nqsv): **495 passed** (106 秒。queue 待ちを含む wall 24 分)。

## 6. 変異 matrix

登録 worktree `.codex/worktrees/mut-fig13-b10-v2` (anchor = wave tip `46e3c0a4d`、`tools/mutation_harness.py` を直接、runner = `tools/run_tests.py --force-dispatch <新 test file> -q -rf`、`--runner-mode dispatch --detached`)。
spec = `mutation-spec-v3-final.json` (SHA-256 `55d50544e10b09d2bae9c08d1b922318a331a2ac77a682bc9bb97e320d33865c`、20 件 = 等価対照 1 + 負例 19。段 4 登録の m0〜m14 に、段 6 裁定で m13 を m13a 削除形 / m13b 境界形へ分割し、焦点再レビューの推奨で fix1 の条件検査 4 種 m15 records / m16 skew / m17 rratio / m18 threads を追加)。
期待 node は本走前に login の self-run harness で観測した完全集合 (`login_probe.py`: 変異を注入 → `python3 orchestrator/tests/test_plot_b10_waiting_grid_forest.py` → 復元 (bytes 一致を assert)。observed JSON の SHA-256 は summary に記録)。
本走 2026-09-20T11:24:23Z 〜 2026-09-20T12:19:00Z: **baseline PASSED (request 13512.nqsv)、m0 SURVIVED、負例 19 / 19 KILLED、期待 node 完全一致 20 / 20、MISMATCH 0 / PARSE_ERROR 0 / TIMEOUT 0** (`summary` = {"KILLED": 19, "MISMATCH": 0, "PARSE_ERROR": 0, "SURVIVED": 1, "TIMEOUT": 0, "completed": 20, "matching": 20, "recorded": 20, "registered": 20})。
結果台帳 `mutation-final-results.json` (581 KB、job dir、SHA-256 `3190cc897b97eaccad556e432447c16805f00de808a63bcbff027e736a6d3de2`) は insight へ複製せず、要約 `mutation-final-summary.json` (各変異の status / rc / 期待 node / 観測 node / request / 所要 / 注入 diff の SHA) を置く。
旧 anchor (`680d6136d`、fix1 前) の probe は baseline dispatch の qsub 段で orphan hold を latch したため中断 (§8)。走行結果は 1 件も無い。

| id | 種別 | 結果 | 期待 node 数 | 期待 = 観測 node | request | 所要 |
|---|---|---|---:|---|---|---:|
| m15-drop-calibration-records-check | negative | KILLED | 1 | `test_calibration_records_or_threads_mismatch_is_rejected` | 13513.nqsv | 32 s |
| m17-drop-workload-rratio-check | negative | KILLED | 1 | `test_workload_skew_or_rratio_mismatch_is_rejected` | 13514.nqsv | 32 s |
| m18-drop-threads-check | negative | KILLED | 1 | `test_calibration_records_or_threads_mismatch_is_rejected` | 13515.nqsv | 1047 s |
| m16-drop-workload-skew-check | negative | KILLED | 1 | `test_workload_skew_or_rratio_mismatch_is_rejected` | 13534.nqsv | 37 s |
| m0-equivalent-docstring | positive | SURVIVED | 0 |  | 13535.nqsv | 39 s |
| m1-provenance-pin-drift | negative | KILLED | 4 | `test_landed_fig13_repo_closure_and_caption_when_present`, `test_pinned_hashes_are_used_when_no_override`, `test_pins_match_results_document`, `test_real_evidence_loads_when_root_present` | 13536.nqsv | 33 s |
| m2-drop-receipt-sha-binding | negative | KILLED | 1 | `test_receipt_sha_not_matching_submission_is_rejected` | 13538.nqsv | 710 s |
| m3-differences-order-free | negative | KILLED | 1 | `test_differences_order_mismatch_is_rejected` | 13557.nqsv | 34 s |
| m4-ci-formula-normal-quantile | negative | KILLED | 25 | 25 node (fixture 全般が赤 = 過剰決定、単独変異の証拠から外す。先頭: `test_artist_series_equal_provenance_cells_and_rendered_artists` …) | 13558.nqsv | 33 s |
| m5-trust-recorded-relation | negative | KILLED | 1 | `test_equivalence_relation_mismatch_is_rejected` | 13559.nqsv | 32 s |
| m6-drop-holm-recalculation | negative | KILLED | 1 | `test_holm_p_mismatch_is_rejected` | 13561.nqsv | 33 s |
| m7-drop-caption-literal-2 | negative | KILLED | 2 | `test_caption_contains_fixed_literals`, `test_landed_fig13_repo_closure_and_caption_when_present` | 13562.nqsv | 32 s |
| m8-layout-overlap-ignored | negative | KILLED | 2 | `test_bbox_overlap_is_a_failure`, `test_layout_failure_publishes_nothing` | 13563.nqsv | 32 s |
| m9-drop-constant-zero-check | negative | KILLED | 1 | `test_constant_cell_nonzero_is_rejected` | 13564.nqsv | 32 s |
| m10-accept-official-certification-true | negative | KILLED | 1 | `test_official_certification_true_is_rejected` | 13565.nqsv | 32 s |
| m11-family-count-at-least | negative | KILLED | 1 | `test_family_count_mismatch_is_rejected` | 13566.nqsv | 33 s |
| m12-drop-raw-p-denominator | negative | KILLED | 1 | `test_raw_p_not_dyadic_is_rejected` | 13569.nqsv | 35 s |
| m13a-drop-exposure-check | negative | KILLED | 1 | `test_underexposed_registered_cell_is_rejected` | 13570.nqsv | 694 s |
| m13b-exposure-strict-boundary | negative | KILLED | 33 | 33 node (fixture 全般が赤 = 過剰決定、単独変異の証拠から外す。先頭: `test_artist_series_equal_provenance_cells_and_rendered_artists` …) | 13579.nqsv | 32 s |
| m14-figure-number-regex-loosened | negative | KILLED | 1 | `test_cli_rejects_prefix_without_fig_number` | 13580.nqsv | 32 s |

単一理由性: 15 件は単一 node (専用負例) で殺した。m1 (pin drift) は実データ系 4 node、m7 (固定文の削除) は逐語検査 + 着地 closure の 2 node、m8 (重なり検査の無効化) は重なり負例 + 無出力検査の 2 node で、いずれも同一の述語が複数 test に現れたもの。
**m4 (CI の係数 1.96、25 node) と m13b (曝露 `>=`→`>`、33 node) は fixture 全般が先に赤になる過剰決定**で、DW-M03 に従い単独変異の証拠から外す (CI 式の検出は `test_cell_interval_mismatch_is_rejected` が m4 の 25 node に含まれることで、曝露の検出は m13a の単一 node で担う)。

## 7. 検査・受入・land

- login self-run (新 test file の `__main__` harness): 着地前 49 passed / 0 failed / 0 skipped (`selfrun-1.log`)、fix1 後 53 passed / 0 failed / 0 skipped (`selfrun-2.log`)。
- 焦点走 (計算ノード dispatch、11 file = 新 test + `test_plain_runner_coverage` + `test_check_subprocess_bytecode_guard` + `test_pytest_collection_config` + `test_official_perf_closure` + figures README を読む既存 4 test + provenance 2 test): 焦点走 1 (request 13484.nqsv) **491 passed**、焦点走 2 (fix1 後、request 13502.nqsv) **495 passed**。
- `check_docs` 違反なし (各 commit 前)、`git diff --check` 緑。provenance: message-file 検査 rc=0 (4 commit)、range 監査 `482f19b88..46e3c0a4d` **4 件、違反なし** (login)。full 監査は記録 commit と main 取り込みの後に dispatch で 1 回走らせる (結果は job dir `provenance/` と land の記録が持つ。prov-1 は §8 の事故で rc=2)。
- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、rc=1): hit は既知の凍結 holdout 系 file (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/*`、`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`、`docs/paper-story/figures/fig8b_b10_static_tail_cohort2.provenance.json`、`docs/paper-story/results/2026-09-16-b7-three-run-materials.md`) だけで、本 wave が足した file への hit は 0 (log は job dir `three-axis-scan.log`)。
- 受入: 記録 commit の tip で main を固定 SHA で取り込んだ後、待ち手経由の全走 (`dev_wave_wait.py acceptance`、3 shard) を門番 loop から投入する。**結果は本 README には書かず、受領証 (`acceptance-receipt-final-<n>.json`、job dir) と land の記録が持つ。child-green でなければ land しない。**

## 8. 事故・気づき

- provenance 全史監査 (prov-1、request 13493.nqsv) を投入した後、queue 待ちの間に fix1 の commit を作ったため「HEAD が監査中に変化した」で rc=2 (実行不能。違反ではない)。監査は全 commit が固まった後に再走した (§7)。
  DW-O26 (同一 worktree の dispatch は全種直列) の「直列」には、dispatch 中の HEAD 変更も含めて読む。
- brief の record / sample の単位誤記 (§2)。
- `verbatim/` の codex 出力 5 file (author / fix1 / focus / review-A / review-B) は Markdown の行末 2 空白が `git diff --check` に抵触するため、行末空白の除去だけの可逆最小正規化を掛けた (可視文字不変。原文 SHA-256・byte 数・変更行・復元法は `verbatim/whitespace-normalization.json`、原 bytes は job dir `codex/` に残る)。

## 9. 言わないこと (成果物の限定)

区間が ±3.0% の内側にあることは等価性の成立ではない (等価性検定はしていない)。36 cell の個別有意差は判定しない (検定は 3 族の族水準だけ)。静的右 tail の 2 cohort (fig8 / fig8b) と合成・比較しない (D2157)。
機序を述べない (D1097、D1678)。`official_certification` は `false` で採用根拠にしない (絶対規律 2)。正しさは trace 有効ビルドの別走行で性能の認証ではない。稿の bytes と `docs/paper-story/README.md` の results 表は触っていない
(同表の「図は無い」は起草時点の記述として残る。ユーザー指示)。判定は D1678 で閉じており、本図はそれを改めない。B-10 という項目の閉鎖ではない。

## 10. 裁定パッケージ候補 (実装せず記録)

- `docs/paper-story/README.md` の results 表の当該行「図は無い」を fig13 の着地に合わせて追補するか (fig11 wave は A-6 行を更新した先例。本 wave はユーザー指示で触っていない)。
- panel 題の情報量 (review A-4): 論文本文幅へ縮小するときに raw p の分数 + 小数の二重表示と和の数値を caption へ移すか。図の bytes が変わるので後継図 (別 filename) の扱いになる。

## 11. 工数

codex 5 本 (author 1、review 2、fix 1、focus 1、全て gpt-6-astra / medium)、計算ノード job = 焦点走 2 + provenance 監査 2 + 変異 (probe 2 + final 1) + 受入。作図は login (計測機の外)。
