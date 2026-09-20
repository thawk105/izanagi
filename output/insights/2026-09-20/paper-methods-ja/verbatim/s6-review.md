## 所見

照合基準は worktree HEAD `fec4a818741e5464fffcd11e4b094c125dfe5280`。対象は [methods.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/paper-methods-ja/methods.md) と [implementation.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-2026-09-20/output/insights/2026-09-20/paper-methods-ja/implementation.md)。**must-fix 4 件、should-fix 3 件。現状は NO-GO。**

1. **real / must-fix — K2 の対照を「無 backoff」と誤記している。**

   該当: methods §2「候補と同じ campaign で無 backoff の stock を対照として評価する」。

   一次資料: D2183、`output/insights/2026-09-20/t2795-pair-launcher/README.md` §0・§2、`orchestrator/campaign/p3_s4_loop.py` `_run_stock_control_resolved`。実装は `BACK_OFF=1, BACKOFF_FIXED=-1` の**適応 backoff**である。`src_token == STOCK` は無 backoff を意味しない。

   対案:
   > 候補と同じ campaign で、CCBench 内蔵の適応 backoff（`BACK_OFF=1, BACKOFF_FIXED=-1`）を stock 対照として評価する独立の口が、2026-09-20 に段 4 ドライバへ加わった（D2183）。

   放置時の影響: 比較対象が適応 backoff から無 backoff に置き換わり、K2 の比較が答える問いを誤る。

2. **real / must-fix — 保存される admission record と、保存されない元 record を取り違えている。**

   該当: methods §4「admission record は成果物に digest までを残し、record の本体は残らない」、implementation「09-10 以後の機構」の A-2 / A-6 行。

   一次資料: story §8 exact claim 限定 (iv)、`paper_story_a2_certification.py` `_CONDITION_ADMISSION_KEYS`・`_write_condition_gate_admissions_x`・`_parse_condition_gate_admissions`。現物の
   `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/condition-gate-rr5.admissions.jsonl`
   には、`admitted`、`use_class`、`unestablished_meaning_macros`、`record_ids` 等を持つ admission record が保存されている。本文が残らないのは参照先の supply-effectuation / runtime-meaning record である。

   対案:
   > 成果物には admission record（`admitted=true`、`use_class="paper"`、`unestablished_meaning_macros` 等）と、供給・意味検査の元 record を指す `record_ids`（digest）が残る。ただし、元 record の本体は残らない。

   放置時の影響: 成果物から確認できる証拠を過小に記述し、story の限定 (iv) と実際の保存形式が食い違う。

3. **real / must-fix — 前稿の B-4 の実装限界を、解消根拠なく落としている。**

   該当: implementation「実走・契約・未了の境界」、methods §6 の B-4 記述。

   一次資料: D1936 項 9、D2016、現行の `p3_b4_raw_record_producer.py`、`p3_b4_material_report.py`、`p3_b4_launcher.py`。writer の排他作成、report の `section_7_1_four_classifications_operationalized=False`、launcher の単一 `--arm` は存続している。床値 pair の w1 完走や K2 stock 口の追加は、この限界の解消ではない。

   対案（implementation の B-4 段落へ復記）:
   > B-4 の writer は create-only、材料 report の §7.1 の 4 分類は未実効、launcher は単一 arm までである（D1936 項 9）。記述統計への限定は機械の受理集合を変更せず（D2016）、正式な certified 選択への接続も未完である。

   放置時の影響: B-4 の未了が赤 precursor 不足だけであるように読め、部分実装の完成度を過大に示す。

4. **real / must-fix — pin 前進の「未実施」を「未解禁」にしている。**

   該当: implementation「MoCC 温度述語 template と機械実証」行の「探索・pin 前進・軸採用は未解禁」。

   一次資料: D2150 項 1、D2159 項 8・9。`e9e477ca` への pin 前進は D2150 で条件付き承認済み。wave 2 の緑が追加認可を与えないことと、既存の承認がないことは別である。HEAD の gitlink は実際に `511c9538…` のまま。

   対案:
   > 探索・正式な軸採用は未解禁。pin 前進は D2150 項 1 で承認済みだが、公開確認等の手順は未実施で、基準 HEAD の pin は `511c9538` のままである。wave 2 の緑自体は pin 前進を認可しない。

   放置時の影響: 承認済み未実施の作業を未承認へ戻し、基準時点の状態分類を誤る。

5. **real / should-fix — B-10 report の実行日と記録・裁定日が混ざっている。**

   該当: implementation「B-10 待ち方 grid」行の「report phase `978195.nqsv`（2026-09-07）」。

   一次資料: `output/insights/2026-09-05/t1905-b10-report/README.md` §0、`docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md` §1・限定 17。report 実行は **2026-09-05**、記録と D1678 は **2026-09-07**。

   対案:
   > report phase `978195.nqsv`（実行 2026-09-05、記録・D1678 の裁定 2026-09-07）。単独 results 稿は entry 1737。

   放置時の影響: 使用実績の時系列と、判定後の記録・裁定との前後関係を誤る。

6. **real / should-fix — 「使用欄に無い機能は走っていない」という全称は強すぎる。**

   該当: implementation「09-10 以後の機構」冒頭。

   一次資料: `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md`。表にない nodes=5 probe `t2489-20260918a` は実走しており、fan-out の使用実績を持つ。ただし `collect` を行わず、A-2 の取得済み判定を更新していない。

   対案:
   > 「使用」欄は本稿で参照する走行を示す。未掲載だけを未使用の根拠とせず、未投入・未使用は各行で明記する。

   必要なら A-2 行へ:
   > 別途 nodes=5 probe の実走があるが、outer status は作成せず、A-2 の認証結果を更新する attempt には数えない。

   放置時の影響: 表の非掲載から実走不在を推論し、実装済み／使用済みの分類を誤る。

7. **real / should-fix — certification の workload 束縛に関する限定 (ii) が明示されていない。**

   該当: methods §5、implementation「記録・経路の読み分け」の cell certified 行。

   一次資料: story §8 exact claim 限定 (ii)、D1257、対象 `certification.json` の各 cell にある
   `workload_argv_observation="not-independently-recorded-by-existing-pipeline"`。

   対案:
   > correctness 側の実 argv は既存 pipeline では独立に記録されておらず、workload の束縛は campaign lock と pipeline constructor による。

   放置時の影響: 「当該 workload で検証した」という主張を支える証拠の種類が不明確になり、実 argv の独立記録まであると読まれる余地が残る。

8. **refuted / must-fix 相当の懸念 — g1 を「未発効」へ戻す必要はない。**

   該当: methods §4、implementation「story 未反映の着地」。

   一次資料: D2180、`output/insights/2026-09-20/t2724-ax-delegated/README.md`、entry 1742。A/X 作成と批准 loader 成功は記録されている。

   対案: 現文を維持する。「発効済み、oracle 実走とは別、科学的に十分な床とは主張しない」という分離は適切。

   懸念を採用した場合の影響: story の古い状態語へ後退し、基準 HEAD までの発効を消してしまう。

9. **refuted / must-fix 相当の懸念 — 検証相を packed verifier の使用実績へ数えてはいない。**

   該当: methods §3、implementation「検証相」「verifier の容量」行。

   一次資料: D2160・D2181、両 wave の README。表は entry 1702 が変更前 verifier で走ったと明記している。

   対案: 現文を維持する。必要な追記はなく、旧検証相の判定や校正値も変更しない。

   懸念を採用した場合の影響: 保全 trace の後日の比較検査を、検証相の再実施・再校正へ取り違える。

## 実装アンカー照合表

「一致」は静的な存在・記述との対応であり、本レビューでの実行成功を意味しない。継承部分の一部は所在確認までで、全経路の再監査ではない。

| 稿の記述 | module / 関数・定数 | 照合 |
|---|---|---|
| planner/coder の分担、反復駆動 | `p3_s4_loop.py` `PlannerProposal`、`CoderProposal`、`planner_context_payload`、`drive_iteration` | 一致 |
| hole、検疫、値の帰属 | 同 `render_hole`、`quarantine`、`assert_value_literal_consistent`、`_check_attribution_before_quarantine`、`diff_quarantine.py`、`backoff_hole_grammar.py` | 一致（主要アンカーの所在） |
| patch 適用・評価・復元 | 同 `_run_one_iteration_resolved`、`patchharness.applied`、`pipeline._prepare_evaluation_core` | 一致（所在） |
| 拒否・重複・状態保存 | 同 `record_diff_reject`、`_resolve_duplicate`、`save_loop_state`、`load_loop_state`、`project_whiteboard`、`check_stop` | 一致 |
| 拒否診断の所在訂正 | `critic/digest.py` `load_rejections`、`load_liveness_rejections`、`render_rejections` | 一致 |
| reflux off は診断提示だけを切る | `p3_s4_loop.make_critic_digest` | 一致 |
| trace/perf の別 build | `pipeline.py` `_build_one(trace=True/False)`、検証・bench 関数 | 一致 |
| 構成・反復、測定・不安定性 | `CorrectnessWorkload`、`performance_correctness_workload`、`calibrator/runner.py`、`stability.py` | 一致（所在・主要分岐） |
| bench-first の閾値・例外 | `ScreeningConfig`、`active_screening` 分岐 | 一致。`k≥1.5`、unstable・abort 率・古い基準点の扱いを確認 |
| 保存証拠の用途別受理 | `artifact_admission.py` の二つの `require_*`、`CampaignReadPurpose` | 一致（所在） |
| selector・oracle の部品 | `s8b_selector_input.py`、`s8b_selector_output.py`、`s8b_oracle_report.py` の列挙関数 | 一致（所在）。catalog は現行も固定 6 候補 |
| 機序仮説の二次 view | `layer3_report._mechanism_view`、通常出力の `certifying_input=False` | 一致 |
| certification の三受領証 | `paper_story_a2_certification.py` `record_submission_receipt`、`record_completion_receipt`、`record_acquisition_receipt` | 一致。前段との束縛・排他作成を確認 |
| cell source 束縛 | 同 `_cell_source_binding_status`、`_require_cell_src_token_role`、source receipt parser | 一致。単独で TU 全体の意味一致を保証しない |
| outer status の順序 | 同 `collect_results` | 一致。anomaly → source reject → correctness 未確定 → performance 未確定／効果不足 → 全効果正 → その他 reject |
| fan-out の台数 | 同 `_validate_verify_fanout_hosts`、`verify_fanout_worker.py` | 一致。別 host 数は `scheduler.nodes−1` |
| admission 証拠の保存範囲 | 同 `_write_condition_gate_admissions_x`、`_parse_condition_gate_admissions` | **不一致：所見 2** |
| A-1 の 3 分類 | `paper_story_a1_paired.py` `CLASSIFICATION_RULES`、`_classify_difference` | 一致。`abs(mean)-h>B`、`abs(mean)+h<=B`、その他 |
| A-1 非認証 lane | `paper_story_a1_paired.v3-sized.json` | 一致。`formal=false`、`promotion_prohibited=true`、指定の `result_authority` |
| A-1 認可 record | `V3_SIZED_RERUN_AUTHORIZATIONS`、`_exact_v3_rerun_authorization`、`_assert_no_prior_v3_bench_start`、`run_authorize_rerun` | 一致。定数 1 件、source commit 一致、解除対象は attempt-0001 |
| A-1 公開先 | `_exact_materialization_destination` | 一致。一致認可時の兄弟 dir、既存先の再使用拒否 |
| K2 exact 6 field | `_validate_k2_critic_diagnosis`、`planner_context_payload`、`k2_next_generation_inputs` | 一致。4 節＋boundary＋SHA、K2・非 B-4・reflux on、両 role へ同一診断 |
| K2 stock 対照 | `_run_stock_control_resolved`、`--stock-control`、job body | **不一致：無 backoff の説明のみ。所見 1** |
| verifier 証明面 | `verifier/core.py` `verify_trace_dir` | 一致。source context と proof surface assessment を扱う |
| packed 内部表現 | `verifier/dsg.py` `_PackedVersions`、`_PackedProducer`、`DSG._build_compact_packed`、worker 経路 | 一致。対象範囲外では旧表現への経路も残る |
| B-10 静的 tail | `b10_backoff_static_tail_formal.py` `analyze_interval`、`analyze_cohort` | 一致。区間 3 状態と workload／集団判定を分離 |
| B-10 待ち方 grid | `b10_backoff_shape_sweep.py` `SHAPES`、`holm_adjust`、`judge`、`cell_effects`、報告関数 | 一致。3 workload の族から得た p 値をまとめて Holm 調整 |
| ソース identity | `source_digest.py` の `-dD` と空入力 prefix 除去 | 一致。include 相対位置・push/pop の限界も対応 |
| 条件関門 | `evaluate_define_supply_effectuation`、`evaluate_define_runtime_meaning`、witness 宣言 | 一致。供給と意味を別に評価 |
| MoCC 計装・template | 列挙 patch、`axis_mocc_temperature.py`、`s3_mocc_template_proof.py`、関連 driver | 一致（アンカー）。承認状態の記述は所見 4 |
| MoCC 軽量 witness | CCBench hook commit `5b02546f`、一次資料の patch 記録 | 一致。Izanagi module ではなく、現行 pin にも含まれない |
| 床値 pair | `floor_pair_driver.py` docstring、`SPEC_SCHEMA`、`compute_gain_difference`、`run_window`、`finalize_floor` | 一致。`D` は相対利得差の**絶対値**、閉じた stratum の最大、create-only |
| B-4 の残る限界 | `p3_b4_raw_record_producer.py`、`p3_b4_material_report.py`、`p3_b4_launcher.py` | **新稿で欠落：所見 3** |

## 前稿から消えた・変わった記述の判定

| 前稿の記述 | 新稿の扱い | 判定 |
|---|---|---|
| certified は指定構成・判定器意味論での受理 | point trace、build bytes、非性能判定を具体化 | **(a)** 一次資料に沿う明確化。保存証拠の説明は所見 2 |
| genome に加えて実ソースの識別情報を使う | `src_token`、`-dD`、残る限界を追記 | **(a)** D2108・D2120 項 7 に対応 |
| critic の拒否還流 3 関数を `p3_s4_loop.py` に帰属 | `orchestrator/critic/digest.py` へ訂正 | **(a)** 現行所在と一致 |
| verifier の内部表現の説明なし | packed 配列と変更時点を追加 | **(a)** D2181 の実装・比較記録に対応 |
| `mechanism_hypotheses` は空の予約区画・未実装 | critic 帰属の決定論射影が実装済み | **(a)** D2143 に対応 |
| 固定「6」候補 | 固定候補一覧と表現 | **(b)** 記述の簡約。有限の凍結一覧という射程は維持、現物は 6 候補 |
| `competing_bench_pids` 等の所在を省略 | calibrator の module を明記 | **(a)** 参照の明確化 |
| B-4 の記述統計裁定だけでは consumer 変更済みでない | 赤 precursor 不足・実走不可を中心に記述 | **(c)** 実装限界の復記が必要 |
| writer は create-only、report 4 分類は未実効、launcher は単一 arm | 三点とも削除 | **(c)** 所見 3。解消した証拠なし |
| 正式選択への接続は未完 | 系全体の留保はあるが B-4 固有の留保を削除 | **(c)** 所見 3 にまとめて復記 |
| 過去の人間監督反復、8c の限定的駆動 | 節番号の細部を省き、無人化しない説明を維持 | **(b)** 意味を保つ整理 |
| raw screening／COMMIT／正式適格の読み分け | 既存区別を維持し、各新機構の行を追加 | **(b)** 構成の拡張 |
| 前稿の 6 節構成 | 同じ 6 節を保持 | **(b)** P1 と一致 |

前稿の「単一数値リテラル」「有限の字句検疫」「reflux off ≠ verify off」「測定付き COMMIT ≠ 最終勝者」「探索 certified ≠ 正式適格」「性能ビルドと検証ビルドの分離」は残っている。

## 照合して一致を確認した範囲

- **certification の取得済み bytes:** A-2 `t2364-20260907b` は 4 cell certified・bound、outer `observed-positive`、埋込み policy は nodes=1。A-6 `a6-20260908b` は 2 cell certified・bound、outer `reject`、nodes=1。B-7 `b7f5-20260919a` は 6 cell certified・bound、nodes=5、request `10807`〜`10809.nqsv`、outer `reject`。B-7 の各 cell は legacy 1＋performance 5 回。outer reject を全 workload の退行へ読み替えていない。
- **検証相:** 一次資料 README と D2160 の判定集合は候補ごとに `24＋6＝30`。校正 6 job、本走 12 job。未完走は候補ごとに 2 件、別に read-heavy 10 s の未実走が候補ごとに 1 件ある。稿は判定集合へ限定しており、S-1 充足・B-8 取得・確率保証へ昇格していない。runner の走行版 v1 と最終集計版 v2 は repo 外。
- **A-1:** attempt-0001 の job `4939`〜`4941`、各 workload 30 対、6 arm の legacy 検証、方向を持たない 3 分類と非認証 lane が対応。attempt-0002 の旧 submit は qsub 前 rc=2。認可 record の実装 wave は投入を含まない。
- **K2:** 3 巡目の `10761.nqsv`、診断 exact 6 field、planner/coder 両方への送付、certified 1 評価が対応。stock 対照口は実装 wave で投入 0 件。「届いた」と「効いた」を分けている。
- **MoCC:** witness 4 arm×60 走、on `0/60・0/60`、off `1/60・1/60`、discriminator 未発火が対応。wave 2 の `11161.nqsv` と 30 check all_pass、wave 1 の `5096.nqsv` が対応。陰性を不在証明・観測者効果の除去へ昇格していない。
- **床値 pair:** w1 の `10711`〜`10713.nqsv`、各 62 標本、各 124 session、3 job complete が対応。w2・finalize・集約・採用は未実施。between-run floor、B-4 pair floor、8b official floor を別量としている。
- **B-10:** cohort 2 の 120 correctness 記録と legacy 条件、各 cohort の verdict を分離する扱いが対応。二つの cohort のプール、有意性の追加、飽和しないという一般化はない。
- **B-7 と g1:** D2174 項 3 の「単一 attempt・descriptive・非認証・反復間安定性未判定」を保持。D2180 の g1 発効を反映し、oracle 実走や床の科学的十分性とは区別している。
- **量化:** methods は 6 節。implementation の表は主要対応 19 行、追加機構 15 行、読み分け 13 行。brief の「7 機構」は機構群の数であり、追加表の行数ではない。
- **参照数:** D 番号は **37 種**で、親の「36 件」とは一致しない。全 37 見出しの実在を確認した。
  `D52, D496, D955, D1198, D1598, D1678, D1936, D2016, D2027, D2044, D2083, D2104, D2108, D2114, D2120, D2134, D2138, D2143, D2145, D2147, D2148, D2150, D2155, D2156, D2157, D2158, D2159, D2160, D2162, D2172, D2174, D2175, D2178, D2180, D2181, D2182, D2183`。
- **entry 参照:** **19 種**の見出しが実在する。
  `1430, 1636, 1666, 1686, 1687, 1690, 1691, 1693, 1696, 1701, 1702, 1705, 1716, 1736, 1737, 1742, 1744, 1745, 1746`。
- **path:** バッククォート内の明示 repo path として抽出した 48 件は実在。両稿に file:line／`#L番号` 形式の行番号参照はない。探索中に推測した `docs/b4*`、`tools/pegasus/*reflux*`、`…/b10-waiting-grid-results/README.md`、B-7 成果物 dir の `README.md` は不在だったが、指定射影 file の不読はなく、対応する実在資料へ進んだ。
- **凍結物・scope:** 開始時と終了時の `git status --short` は `?? output/insights/2026-09-20/paper-methods-ja/` のみ。tracked diff は空。前稿・story・results 稿・実装に本 wave の差分はない。英訳、新規実験、追加 gate／検査／台帳の提案、性能値・図の転載は確認しなかった。

件数の照合は指定 README・裁定・一部の権威 JSON に基づく。全実走の raw trace／WAL の再集計や保存先全体の独立監査は行っていない。pytest・build・測定・受入検査は実行していない。

## GO / NO-GO

**NO-GO。稿 2 本をこのまま凍結しない。**

must-fix は次の 4 件。

1. K2 stock 対照を「無 backoff」から「適応 backoff」へ訂正する。
2. 保存される admission record と、本文が残らない supply／meaning record を区別する。
3. 前稿から落とした B-4 の実装限界と正式選択への接続未完を復記する。
4. MoCC pin 前進を「未解禁」から「承認済み・未実施」へ訂正する。

訂正先は新稿 2 本に限る。凍結済み前稿・story・results・事前登録、旧 attempt の判定を変更する必要はない。

## 総括

基準 HEAD と新稿の時点設定は一致している。
certified を性能判定へ拡張する主張や、検証相・B-7・g1 の過大な昇格は見つからなかった。
主要な不一致は、K2 の比較対象と条件関門の保存証拠の説明である。
B-4 の未解消限界の削除、pin 前進の承認状態も訂正が必要。
must-fix 4 件を直した後、その変更箇所を対象とする焦点レビューで凍結可否を再判定する。
本レビューは read-only の静的照合であり、書込み・commit・push・テスト・測定は行っていない。