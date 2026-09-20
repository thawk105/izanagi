# [T-2793] fig8 の再現欄付き後継図 fig8b を作った — 生成器の cohort 表と `--reproduction-cohort 2`、test、3 成果物、README

`authority: none` / `default_effect: no-state-change`

**種別:** 実装 (既存図種の生成器と test の拡張、Codex author) と記録 (図の凍結物 + README)。**新規測定はゼロ**。図の入力は完走済みの
2 cohort の集団報告 6 file (repo 外、SHA-256 pin) だけである。

- 日付: 2026-09-20 (JST)
- wave: `dev-wave-t2793-fig8b-cohort2`、branch `worktree-dev-wave-t2793-fig8b-cohort2`
- 起点 local main: `b7f970dfa507558f7fb669a5ab38958d6c76b57c`
- 依頼: `verbatim/T-2793-origin.md` (ユーザー、dev-wave 引数の逐語)。要点: fig8 に第 2 cohort の再現欄を足した後継図を別 filename で作る、
  凍結 fig8 の bytes は上書きしない、Codex author (D95) が生成器の cohort 引数拡張で生成、provenance JSON と figures/README.md の節を足す、
  材料は cohort2 稿 §2.6 / §4.1、主結果 cohort 1 と区別して併記し合成・プール・統合 verdict は作らない、言い方は事前登録 §4.5 の固定表現に限る、
  規律 2 を緩めない、本題の作図だけ。

## 0. この wave が主張すること・しないこと

**主張する。**

1. **fig8b の 3 成果物 (`docs/paper-story/figures/fig8b_b10_static_tail_cohort2.{png,pdf,provenance.json}`) が着地し、caption が同 README に
   収録され、着地 test (fig8 / fig8b とも) が緑である。** §1・§2。
2. **上 block (cohort 1) の値は fig8 と同じ集団報告・同じ pin・同じ計算で、下 block (cohort 2) の値は cohort2 稿 §2.2 / §2.3 の表と一致する。**
   判定 (verdict・区間分類・qhat・L・U) は各 cohort の集団報告からコピーし、生成器は再計算しない。§3。
3. **役割 (1 = primary、2 = reproduction) と順序は生成器の定数で固定され、CLI からも provenance の改変からも入れ替えられない。provenance (schema v2)
   の top-level に cohort をまたぐ統計 field は無く、`claim_boundary.cohorts_pooled` は `false`。** §2。
4. **凍結 fig8 の 3 file は生成前後で SHA-256 不変。v1 経路の受理集合・射影は byte 同一。** §2・§6。
5. **変異 matrix (等価対照 1 + 負例 11) と受入全走の結果は §5・§6。**

**主張しない。**

- **「飽和しない」「飽和点が存在しない」「再現されたので飽和しない」とは言わない。** caption は事前登録 §4.5 の固定表現の英訳を各 cohort へ
  独立に適用し、"The second cohort returning the same aggregate verdict is reported as such and is not read as anything beyond the fixed wording above."
  を置く (追記 項 7)。
- **2 つの cohort を合成しない。** プール推定・統合 verdict・cohort をまたぐ有意水準を作らず、数値の近さを再現精度・一致度として評価しない
  (追記 項 3、cohort2 稿 §2.6)。
- **性能を認証していない** (`performance_certified: false` を両 cohort に付ける。絶対規律 2)。**機序を言わない** (D1678 / D1724)。
- **「1 ページに入る」を主張しない。** 描画寸法 7.2 × 10.6 in は実測だが、掲載寸法での可読性は投稿テンプレートでしか確かめられない (consult A4)。
- **fig2c の続きではない。** 探索走 `t2418-explore` / `t2266-tail` 系列の標本は入っていない。
- **B-10 を閉じない。第 3 cohort の実施・地位を定めない。** 版 `2026-09-19.md`・results 稿・事前登録は凍結物で変えていない。
  版への取り込みは次の版の契約が決める。

## 1. 置いたもの

| file | 内容 |
|---|---|
| `tools/plotting/plot_b10_static_tail_formal.py` (Codex author + fix、commit `22b9deb58`) | `COHORTS` 表 (group id・完走日・report dir・pin 3 件・results 稿 path)、`load_measurements(cohort=)`、`_figure_number(letter_suffix=)`、`_caption_v2`、`_artist_series_v2`、`_draw_block` / `make_figure_v2` (4 行 × 3 列、block 見出し gid `block-title`)、`check_figure_layout(expected_axes=)` + 見出しの panel 侵入検査、`build_provenance_v2` / `_validate_repo_closure_v2` (schema v2)、`_publish_outputs` の caption / builder 切替、CLI `--reproduction-cohort` (choices = (2,))。純増 163 行 |
| `orchestrator/tests/test_plot_b10_static_tail_formal.py` (同上) | `_fixture` / `_seal` の cohort 対応 (既定は従来と同じ)、`_fixture_pair` (同一 root の別 report dir、cohort 2 は反復間変動・区間値・job id・事前登録 commit を区別可能)、新 test 12 本 (§2)。既存 25 test の名前・本文・期待値は不変。純増 242 行 |
| `docs/paper-story/figures/fig8b_b10_static_tail_cohort2.{png,pdf,provenance.json}` (親が login node で生成、commit `864d7135e`) | 凍結物。png `ddab2873…`、pdf `c5454544…`、provenance `429b4028…`。generator SHA-256 `96f8f5de…` = commit `22b9deb58` の生成器 bytes |
| `docs/paper-story/figures/README.md` (同上) | 一覧に fig8b 行 (fig8 行に後継図の注記)、fig8 節末尾に「追補 — 再現欄付きの後継図 fig8b」、fig8b 節 (何を示す図か・再現欄の表・既存図との関係・入力・再現・作図規約への適合・キャプション正文・proof chain・言わないこと) |
| `tools/plotting/README.md` (同上) | `--reproduction-cohort 2` の契約 1 段落 |
| `docs/spool/worklog/2026-09-20-dev-wave-t2793-fig8b-cohort2-1.md`、`docs/spool/decisions/2026-09-20-dev-wave-t2793-fig8b-cohort2-2.md` | worklog fragment (T-2793 を `完了`)、decisions fragment (縦 2 block・役割固定・非プール構造・v1 不変) |
| 本 insight | 記録と逐語 (`verbatim/`) |

触っていない: 凍結 fig8 の 3 file (SHA-256 不変を `verbatim/fig8-sha256-before-generation.txt` と `verbatim/fig8b-sha256-after-generation.txt` で記録)、
既存 8 図の bytes・provenance・節、他の生成器・test、`FIGURE_CONVENTIONS.md`、`docs/paper-story/README.md`、版、results 稿、事前登録、
`docs/paper-story-backoff/**`、phase doc。

## 2. 図と生成器の契約 (段 4 裁定 §2、段 6 で確定)

- **入力**: root `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/` の `group-report-20260915/` (cohort 1、fig8 と同じ pin) と
  `group-report-20260919-cohort2/` (cohort 2: JSON `932f6ccc…` / DAT `15b99944…` / complete `93421187…`) の各 3 file。cohort 2 の pin は
  cohort2 稿 §4.1 の表と test で一致検査。**pin は CLI から渡せない** (`expected_hashes` は Python API の注入 seam で、CLI parser に hash 引数は無い。
  レビュー A が「API からも迂回不能ではない」と正確に限定した)。
- **拒否条件は両 cohort に同じ**: verdict ≠ `not-observed-in-any-workload`、`performance_certified` が `False` 以外、正しさ記録 120 件のいずれかが
  `certified is True` でない、`anomalies != 0`、SHA-256 不一致、`.dat` 120 行でない、区間集合に境界参照 1000 が入る、group id が campaign path に無い。
- **役割・順序**: `COHORTS[1]["role"] == "primary"`、`COHORTS[2]["role"] == "reproduction"` を定数で固定。CLI は `--reproduction-cohort 2` だけを受理し
  (cohort 2 単独の図は作らない)、closure v2 は provenance の位置ごとの `(cohort, role)` 対を `[(1, "primary"), (2, "reproduction")]` と照合する。
- **provenance schema v2**: top-level key 集合 = {schema, generated_utc, generator, outputs, external_source_locator, cohorts, claim_boundary,
  artist_series, caption, reproduction} に固定 (局所 assertion、汎用 validator にしない)。`cohorts[]` の各要素だけが `workloads` / `report` /
  `correctness` / `external_inputs` / `preregistration` / `campaigns` を持つ。`claim_boundary` = v1 の 6 key + `cohorts_pooled: false` +
  `cohort_roles_fixed_in_generator: true` + 両 group id。closure は境界辞書の一致とは別に `cohorts_pooled is False` を独立に検査する。
- **caption v2** (4215 字、`verbatim/` は無く provenance と README が正本): 両 cohort の group id・verdict・事前登録 commit (先頭 9 桁)・
  「same spec SHA-256」・"performance_certified: false for both cohorts"、block 構成と cohort 別 job id、「Within each block」の行説明、
  cohort 別の区間分類 (18/18、L の範囲)・throughput 比・正しさ 120 記録、固定表現を各 cohort へ独立に適用する前置き + 固定表現 1 回、
  NO_REREAD_WORDING、NOT_POOLED_WORDING、条件、比較禁止 (panel 間・block 間)、fig2c / 探索走の除外。禁止語なし。
- **v1 経路は不変**: `_caption` / `_artist_series` / `build_provenance` / closure v1 の本文、v1 の展開 argv (5 要素)、`_figure_number` の既定
  (数字だけ) は base と一致 (レビュー A / B が source 比較で確認)。英字 suffix (`fig8b_`) の受理は v2 経路だけ。
- **layout**: `check_figure_layout(fig, axes, expected_axes=12)`、`gid="block-title"` の text は plot axes の bbox と交差不可。保存前検査に落ちたら
  3 成果物を 1 つも出さない (v2 も `_publish_outputs` の実経路)。fix1 後の余白: 下 block 見出しと上 block の x ラベルの間 ≈ 32 pt、
  見出しと下 block 上段の panel title の間 ≈ 21 pt (fix1 報告の実測)。

## 3. 数値の検算

- 生死確認 (brief 前、job dir の使い捨て script、repo 外): 現行 loader に定数を差し替えて cohort 2 を読ませ、verdict / 24 cell / job / 比 / 18/18 /
  L の範囲 / 境界参照 1000 の write-heavy 平均 992,686.2 が cohort2 稿 §2.2 / §2.3 と一致。
- 着地 provenance の caption: cohort 1 = fig8 と同じ値 (比 0.444 / 0.481 / 0.400、L 0.2738〜0.3704)、cohort 2 = 比 0.445 / 0.484 / 0.398、
  L 0.2782〜0.3732。test `test_real_root_loads_cohort2_and_matches_results_document_when_present` が実 root で稿 §2.3 の文字列と照合。
- 描画値: `test_two_cohort_artists_match_raw_repetitions_and_intervals` が fixture の生 reps から平均・CI を test 側で計算し、両 block の tail /
  境界参照 / CI bar / cap / 区間線 / 直接ラベルと比較する (生成器の artist 関数を oracle にしない、レビュー B が確認)。

## 4. 相談・レビューの所見と裁定

- 段 3 consult (`verbatim/s3-consult.md`、sol、2 レンズ 1 本): must-fix 5 / should 6 / nit 4、refuted 0、全件採用 (`verbatim/s4-adjudication.md` §1)。
  主なもの: A1 v2 caption の行説明、A2 v1 受理集合の不変 (図番号の suffix は v2 だけ)、B1 publish 経路の caption 切替、B2 block 見出しの侵入検査、
  B3 変異ごとの独立した根拠、B8 CLI 名 (`--reproduction-cohort`)。
- 段 6 レビュー A (`verbatim/s6-a.md`、正しさ境界・言い方): **must-fix 0 / should 0 / nit 1、GO**。変異 M0〜M11 の期待 node を静的予測。
- 段 6 レビュー B (`verbatim/s6-b.md`、過剰・削除): **must-fix 0 / should 1 (親の README 作業) / nit 1、GO**。diff = base→現物と完全一致、
  既存 25 test 不変、fixture の区別可能性 (B4) 充足を確認。
- fix1 (`verbatim/s6-fix1.md`): A-N1 / B-N1 / 親 nit の 3 件 closed (対応表あり)。**焦点再レビュー子は起動しなかった**: 所見が nit だけで
  real 所見の fix ではなく (DW-O16 の対象外)、変更は 3 行の値・1 行の削除・1 行の assert 追加で、親の自走 harness 再走・実データ再生成・PNG 目視・
  変異 matrix で閉じた (DW-S06-C「1 本でよい」)。
- レビューが実行していないこと: pytest・作図・実行履歴の独立検証。それらは親の焦点走 (§6) と本 README が担う。

## 5. 変異 matrix (事前登録 → probe → 本走)

事前登録は段 4 裁定 §3 (`verbatim/s4-adjudication.md`)。逐語 anchor は成果物 commit `864d7135e` の生成器から job dir の `make_mutation_spec.py`
が生成し、一意性 (12 件とも 1 回) を fix1 統合後にも検査した。runner = `python3 tools/run_tests.py --force-dispatch
orchestrator/tests/test_plot_b10_static_tail_formal.py -q -rf`、独立 clone (`mutation-source`、main = `864d7135e`、D1009)、`--runner-mode dispatch --detached`。
spec は `timeout_seconds` 5400 / `hang_timeout_seconds` 3000 / `estimated_run_seconds` 240。

初回 probe (`verbatim/mutation-spec-probe.json`、timeout 2700) は harness の preflight で中止 (dispatch の待機契約 queue 3600 + grace 600 より短い、
走行ゼロ)。probe2 (`verbatim/mutation-spec-probe2.json` sha256 `92653867…` / `verbatim/mutation-probe2-out.json`、08:17〜08:54 JST、全件 SURVIVED 登録):
baseline PASSED (38 秒)、M0 SURVIVED、負例 11 件はすべて赤 node を出し、その集合はレビュー A の静的予測 (`verbatim/s6-a.md` の表、着地後に
fig8b 着地 test が加わる予測を含む) と一致した。観測集合を final spec (`verbatim/mutation-spec-final.json` sha256 `50079895…`) に写した。

本走 (`verbatim/mutation-final-out.json`、08:57〜09:15 JST): **baseline PASSED (33 秒)、11/11 KILLED (期待 node 完全一致)、M0 SURVIVED、MISMATCH 0、
matching 12/12**。`N::` = `orchestrator/tests/test_plot_b10_static_tail_formal.py::`。

| id | 変異 (成果物 commit の位置) | 分類 | 結果 | 赤 node (完全集合) |
|---|---|---|---|---|
| M0 | module docstring に 1 行足す | 等価対照 | **SURVIVED** (期待どおり) | — |
| M1 | `COHORTS[2]` の DAT pin 末尾 1 文字 | pin | **KILLED** | `N::test_cohort2_pinned_hashes_match_cohort2_results_document`、`N::test_real_root_loads_cohort2_and_matches_results_document_when_present`、`N::test_landed_fig8b_repo_closure_and_both_captions_when_present` (3) |
| M2 | `COHORTS[2]["role"]` → `"primary"` | 役割固定 | **KILLED** | `N::test_cohort_roles_are_fixed_literals`、`N::test_cli_cohort2_writes_three_outputs_and_v2_closure` (2) |
| M3 | loader の verdict 検査 → `in (EXPECTED_VERDICT, "saturated-in-all-workloads")` | 規律 2 / 受理集合 | **KILLED** | `N::test_cohort2_rejects_alternate_verdict_and_certification_failures` (1。既存の `"fixture-invalid"` 負例では殺せない変異) |
| M4 | `_caption_v2` から `NOT_POOLED_WORDING` を落とす | 非プールの言い方 | **KILLED** | `N::test_v2_caption_contains_independent_fixed_wording`、`N::test_landed_fig8b_repo_closure_and_both_captions_when_present` (2) |
| M5 | `FIXED_WORDING` を "the abort rate does not saturate" に | 事前登録 §4.5 | **KILLED** | `N::test_caption_contains_fixed_expression_and_certification_literal`、`N::test_v2_caption_contains_independent_fixed_wording`、`N::test_caption_avoids_forbidden_saturation_claims`、`N::test_landed_fig8_repo_closure_and_caption_when_present`、`N::test_landed_fig8b_repo_closure_and_both_captions_when_present` (5) |
| M6 | `check_figure_layout` の先頭で `return` | §9 fail-closed | **KILLED** | `N::test_bbox_overlap_is_a_failure`、`N::test_layout_failure_publishes_nothing`、`N::test_v2_block_title_intrusion_publishes_nothing`、`N::test_v2_text_overlap_publishes_nothing` (4) |
| M7 | block-title の panel 侵入検査を無効化 | §9 (v2 固有) | **KILLED** | `N::test_v2_block_title_intrusion_publishes_nothing` (1) |
| M8 | v2 の `_figure_number` を数字のみへ戻す | 図番号 | **KILLED** | `N::test_figure_number_suffix_is_v2_only` + v2 経路の巻き添え 6 本 (`test_cli_cohort2_writes_three_outputs_and_v2_closure`、`test_v2_caption_contains_independent_fixed_wording`、`test_landed_fig8b_repo_closure_and_both_captions_when_present`、`test_two_cohort_artists_match_raw_repetitions_and_intervals`、`test_v2_text_overlap_publishes_nothing`、`test_v2_block_title_intrusion_publishes_nothing`) (7) |
| M9 | 下 block に cohort 1 の cell を描く (取り違え) | 図の意味 | **KILLED** | `N::test_two_cohort_artists_match_raw_repetitions_and_intervals` (1。fixture の生値から計算した期待値との不一致) |
| M10 | `CLAIM_BOUNDARY_V2["cohorts_pooled"]` → `True` | 非プール構造 | **KILLED** | `N::test_cohort_roles_are_fixed_literals`、`N::test_landed_fig8b_repo_closure_and_both_captions_when_present`、`N::test_cli_cohort2_writes_three_outputs_and_v2_closure` (3) |
| M11 | closure v2 の位置 (cohort, role) 対検査を除去 | 役割固定 | **KILLED** | `N::test_cli_cohort2_writes_three_outputs_and_v2_closure` (1。入替 provenance を再射影した負例だけが殺す) |

- 11 件はいずれも受理集合または fail-closed 挙動の変化による kill で、診断文言差だけの赤は無い。M3 / M7 / M9 / M11 は単一 node で、
  それぞれ「指定 verdict の投入」「見出しの侵入」「fixture 生値からの描画期待値」「入替 provenance」という独立した根拠に帰属する。
- 等価と判断して登録しなかった候補: 未使用代入の増減、`_display_path` の書式、cohort 1 経路の既存変異 (先行 wave [T-2647] の matrix で kill 済み)。
- 所要は probe2 37 分・本走 18 分 (計算ノード dispatch、1 変異 32〜49 秒、M0 と M9 は queue 待ちで 356 / 370 秒)。

## 6. 受入全走・検査

- 焦点走 (post-s5、tip 22b9deb58 相当の作業木、計算ノード request 11883.nqsv、07:47〜07:48 JST): `test_plot_b10_static_tail_formal.py` +
  `test_plain_runner_coverage.py` = **39 passed / 1 skipped** (skip は着地前の fig8b 着地 test)。fix1 統合後の login 自走 harness 36/36 → fig8b 着地後 37/37
  (`verbatim/selfharness-post-landing.log`、着地 test 2 本とも PASS)。
- `python3 tools/check_docs.py` 違反なし (2 回)、`git diff --check` rc=0、三軸語走査 (`s8b_holdout_freeze search`) holdout hit 0 (rc=0。fig8b provenance は
  正例対照 rr50 の一般 hit に fig5〜8 と同じく含まれる)、wave 区間の provenance 監査 (`check_ai_provenance.py --range b7f970dfa..HEAD`) 違反なし。
- **final**: 記録 commit の tip で clean tree から `tools/dev_wave_wait.py acceptance --lease-optional` を 1 回投入する。結果は本 README には書かず
  (受入は記録の後)、受領証 (`acceptance-receipt-final-1.json`、job dir) と worklog が持つ。child-green でなければ land しない。

## 7. 言ってよいこと・言ってはいけないこと・次の一手

- 言ってよい: fig8b は fig8 の再現欄付き後継図として `figures/` に存在し、上 block は cohort 1、下 block は cohort 2 で、値は各集団報告から再計算され、
  判定はコピーである。役割・順序は定数で固定され、cohort をまたぐ統計は provenance に無い。言い方は事前登録 §4.5 の固定表現に限り、性能は未認証である。
- 言ってはいけない: 「飽和しない」「飽和点が存在しない」「再現されたので飽和しない」、一致度・再現精度、機序、転移、性能認証、B-10 の完了、
  第 3 cohort の地位、fig2c の続き、「1 ページに入る」。
- 次の一手 (別 wave、いずれも本 wave の scope 外): `docs/paper-story/README.md` の stale 注記へ fig8b の成立を案内する (版 `2026-09-19.md` §4 と
  cohort2 稿 §3 限定 11 の「図は無い」は当時は真)。掲載寸法での PDF 可読性の確認は投稿テンプレートが決まった時点で行う。

## 8. 一次資料

- 依頼: `verbatim/T-2793-origin.md`。brief: `verbatim/s1-brief.md`。plan: `verbatim/s2-plan.md`。裁定: `verbatim/s4-adjudication.md`。
- consult: `verbatim/s3-consult-prompt.md` / `verbatim/s3-consult.md`。author: `verbatim/s5-author-prompt.md` / `verbatim/s5-author.md`。
  レビュー: `verbatim/s6-a-prompt.md` / `verbatim/s6-a.md` / `verbatim/s6-b-prompt.md` / `verbatim/s6-b.md`。fix1: `verbatim/s6-fix1-prompt.md` / `verbatim/s6-fix1.md`。
- 実装差分は commit `22b9deb58` (patch file は insight へ写さない)。生死確認 script は job dir (`probe_cohort2_load.py`、.py は insight へ写さない。
  内容は「定数 5 件を cohort 2 の値へ差し替えて `load_measurements` と `make_figure` / `check_figure_layout` を呼ぶ」だけ)。
- 焦点走: `verbatim/focus-post-s5.log` (dispatch trace 行を除いた写し)、`verbatim/selfharness-post-landing.log`。
- SHA-256: `verbatim/fig8-sha256-before-generation.txt`、`verbatim/fig8b-sha256-after-generation.txt`。
- 変異: `verbatim/mutation-spec-probe.json` (初回、preflight で中止)、`verbatim/mutation-spec-probe2.json`、`verbatim/mutation-spec-final.json`、
  `verbatim/mutation-probe2-out.json`、`verbatim/mutation-final-out.json`。
- 事前登録: `docs/b10-backoff-static-tail-preregistration.md` (§4.5、2026-09-19 追記)。裁定: D2157。稿: `docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md`
  (§2.6 / §4.1)、`docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`。図の正本: `docs/paper-story/figures/README.md` の fig8b 節。
