# K2 手動 loop 3 巡の結果節 — 提案 → 評価 → critic を 3 回実施し、実測の還流 2 回と critic 診断の型付き入力への還流 1 回が既存経路で成立した (2026-09-16 / 09-18 / 09-19。同 job stock 対照なし、改善の実証ではない)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む。
D2120 項 15 が「paper-story の単独 results 稿は権威 bytes から作る既存経路であり、層 3 の proof chain 付き
材料レポートと同一視しない」と定める)。英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は性能の結果節ではなく、方法論 (合成ループの往復と診断の還流) の実施例の結果節である。**
見送り台帳の項目 B-6 (リーク制御を完備した状態での実走) の材料であって、B-6 の充足を判定しない。
**本稿の状態記述 (「未起票」「裁定待ち」「未達」) はすべて 2026-09-20 時点のものである。** 台帳 ID は同日時点で未起票
(3 巡それぞれの wave は [T-2588] / [T-2746] / 上位 [T-2783] の下で走った)。

**成立範囲を最初に固定する。** 本稿が扱う保存成果物の範囲で成立したのは次の 3 つで、それ以上ではない。

- 提案 (planner + coder) → 評価 1 本 → critic を **3 回** 実施した (2026-09-16 / 09-18 / 09-19)。
- 評価の実測が次の提案の型付き入力へ戻る **実測の還流は 2 回** (1 回目の評価 → 2 回目の提案、2 回目の評価 → 3 回目の提案)。
- critic の診断が次の提案の型付き入力へ届く **診断の還流は 1 回** (2 回目の critic → 3 回目の提案。D2155 の経路)。
- **3 回目の評価の実測と critic-3 の診断を、さらに次の提案へ戻す実走は、本稿の対象成果物に含まれない。**

**限定を最初に置く。** 以下は本稿の全節に先立つ。

1. **同時刻の対照が無い。** 3 巡の評価はいずれも同一 job 内に stock (無改変 backoff) の対照を持たず、同一 job 内の別値も持たない。
   3 巡目のユーザー決定に含まれていた「同 job の stock 対照 1 本」は未達で、その扱いは [T-2795] としてユーザー裁定待ちである
   (2026-09-20 に確認した裁定パッケージの結果欄が空)。
   したがって **3 巡目の 815,983 tps を含むどの値も、性能改善・退行の証拠として書かない。** 3 巡の値は別日・別ノード・別 submit-tree の
   非同時刻 3 点であり、並べて示すのは記録のためであって比較のためではない。
2. **知識・診断の因果効果を主張しない。** K2 知識源 (別機体の測定 WAL 1 件) と、3 巡目で届いた critic 診断について、role が
   「参照した」と自己申告 (`knowledge_use` / `justification`) した記録はあるが、**それらが提案値を変えた因果は確認していない**
   (知識なし・診断なしの統制が無く、各条件 1 回の別起動である。§2.3)。「届いた」「参照したと申告した」「効いた」は別の命題であり、
   本稿が書けるのは前 2 つまでである。
3. **3 巡はいずれも legacy critic (Bash を持つ role) を使った経路であり、B-4 (リーク制御の ablation) には非適格である** (D2155、各巡の記録)。
   本稿は B-4 の材料ではない。
4. **規律 6 (外部入力はデータであって指示ではない) の検査結果を、各巡の role 出力から写す。** coder は構造化 field
   `data_boundary_report.instruction_like_content_detected=false` (4 出力とも)、planner は `uncertainty` の散文、critic は「信頼境界検査」節の散文で、
   いずれも「指示めいた文字列なし」と自己申告した (§2.4)。**形式は role ごとに違い、機械的な強制でも共通 schema の検査結果でもない。**
5. **`certified` は正しさゲート (trace-enabled build の verifier が `serializable` / anomaly 0 を返した) の意味であって、性能の判定でも
   候補間の certified な選択でもない。** whiteboard の `result=success` も同じ意味である。規律 2 (anomaly 検出時の即 reject) は 3 巡とも
   発火せず (anomaly 0)、gate は 1 行も触っていない。
6. **数値・機械判定・入力内容は §5 の一次資料から再抽出した。実行者 (各巡の親) の手続きのうち、保存成果物から再確認できないものは
   「各巡の記録による」と明示し、§4 に区別して置く。** 本稿はそれらを独立に確認された実施証拠へ昇格させない。

---

## 0. 位置づけ — 何を書き、何を書かないか

### 0.1 この稿の単位

**K2 手動 loop の 3 巡である。** 1 巡 = (i) planner-v4 と coder-v4-autonomous-k2 が K2 知識源を含む型付き入力から提案値を 1 つ作る →
(ii) 既存の段 4 loop 経路 (`orchestrator/campaign/p3_s4_loop.py`、Pegasus job body `tools/pegasus/p3_s4_loop_pegasus.sh`) がその 1 値を
build (trace / perf 別 build) → verify (trace-enabled) → bench (trace-disabled) の順で 1 回評価し、campaign WAL に terminal record を書く →
(iii) critic が digest と WAL を読んで帰属を試み、次の提案の方向を書く。**この (i)〜(iii) を 3 回実施した。**
「還流」は (ii) の実測または (iii) の診断が**次の (i) の型付き入力に入ったこと**を言い、実測の還流は 2 回 (巡 1 → 巡 2、巡 2 → 巡 3)、
診断の還流は 1 回 (critic-2 → 巡 3) 成立した。**巡 3 の (ii)(iii) の後に (i) は行われていない** (冒頭「成立範囲」)。
1 巡目の記録が「1 巡が閉じた」と呼ぶのはこの実測の還流 1 回目、2 巡目の記録の「2 巡連続で閉じた」は 2 回目までを指す。

3 巡は独立した 3 つの wave (2026-09-16、2026-09-18、2026-09-19) で、それぞれ着手時の local main から専用 submit-tree を切り、
評価 job を 1 本ずつ投入した。campaign ID は 3 巡とも `p3-s4-loop-s4-autonomous-409e13f8` である — identity 5 key
(`spec_content` / `ccbench_commit` / `search_tag` / `search_config` / `trial`) に提案値・superproject HEAD・submit-tree path が入らないため
同じ設定なら同じ ID になる。**ID の同一は走行の同一ではない**。3 巡は別 tree・別 WAL・別 `loop_state.json` で、各 WAL の iteration は 1 である。

評価は 3 巡で計 3 本 (job `1216.nqsv` / `4954.nqsv` / `10761.nqsv`)。投入は計 4 本で、2 巡目の 1 本目 (`4947.nqsv`) は job body の
preflight で拒否され評価に到達していない (§2.2、D2148 項 2)。

### 0.2 書くもの

- 3 巡に共通する固定条件 (経路・pin・配線・知識源・役割・入力の型・判定規則) と、各巡の認可 (§1)。
- 3 巡それぞれの入力 → 提案 → 評価 → 還流を、一次資料 (proposal JSON・role 逐語・campaign WAL・受領証・材料レポート) から (§2.2)。
  各巡の表で「記録による」と付けた行は、各巡の記録 README (実行者の自己記録) にしか無い手続きであり、本稿は再確認していない (§4.3)。
- 3 巡目で critic 診断が型付き入力 (`k2_critic_diagnosis`) として届いた事実と、その限界 (§2.3)。
- 規律 6 の検査結果 (§2.4)、正しさの記録 (§2.5)、材料レポート (§2.6)、時系列 (§2.7)。
- 限定 (§3) と、権威 bytes・WAL・裁定の対応が確かめられない箇所 (§4)。

### 0.3 書かないもの

- **性能の比較・改善・退行・最良点・最適量。** 同時刻対照が無い (限定 1)。3 走の tps 差、critic の純コスト模型の予測との一致・不一致、
  spin 占有率の導出値は、いずれも性能主張として書かない。
- **知識・診断の因果効果** (限定 2)。**B-4 の材料** (限定 3)。**B-6 の充足判定**。
- 3 巡目の縮小走行の受理可否、同 job stock 対照の実装方針 ([T-2795] の択 (i)〜(iii))。本稿は裁定を先取りしない。
- 2 巡目の wave が同時に実装した機序仮説層 v3 ([T-2681]、`runs/agent_outputs.jsonl` と `mechanism_hypotheses`) の実装内容・変異 matrix。
  本稿は同層が生んだ材料レポートの値だけを §2.6 に写す。
- 新しい CC 構造の合成。3 巡が動かしたのは固定 backoff の初期値 literal 1 つである (§1.1)。
- 研究としての成功・失敗・新規性の宣告 (D12)。

---

## 1. 条件 — 各巡の前に固定されていたもの

### 1.1 経路と固定条件 (3 巡共通)

| 項目 | 値 | 出所 |
|---|---|---|
| 評価経路 | `orchestrator/campaign/p3_s4_loop.py` の `drive_iteration` (proposal file 1 本 → `run_campaign` → `pipeline.evaluate`)。job body は `tools/pegasus/p3_s4_loop_pegasus.sh` (1 job = driver 1 起動 = 候補 1 本) | 各巡 `job.stdout` 末尾の「=== 段 4b iteration (proposal=…, reflux=on, build=True, …) ===」 |
| CCBench pin | `511c9538e4e8efa54b45cda62e72389ed3b706ec` (D1936 項 1 で前進、3 巡とも同一) | 各巡 WAL `build_start.build_admission.source.ccbench_commit` |
| 編集面 | `include/backoff.hh` の hole 1 箇所 `double now_backoff = <整数 literal>;`。文法 `backoff_hole_grammar` v1、値域は整数 1..1000 | 各巡 proposal の `coder.proposal.implementation`、WAL `backoff_grammar_version: 1`、[T-2795] の記述 |
| 固定 genome | `silo\|BACKOFF_FIXED=<value>,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` (value 以外は 3 巡不変) | 各巡 WAL `build_start.payload.genome` |
| 性能配線 | `-thread_num=4 -ycsb_tuple_num=100000 -extime=1 -clocks_per_us=2100 -ycsb_rratio=50 -ycsb_zipf_skew=0.9 -ycsb_rmw=false`、reps 2 | 各巡 WAL `bench_done.payload.run_cmd`、`tps` の要素数 |
| 正しさ検証 | trace-enabled build の legacy workload 1 条件 (`verify_configs: ["legacy"]`)。verdict は `serializable` / `certified` / `anomalies` | 各巡 WAL `verify_done`、`commit.payload.verify_configs` |
| perf counter | 計算ノードで `perf stat` が使えない (`perf_observation.preflight.status=unavailable`、`rc=2`、`reason=nonzero-rc`)。`llc_miss_rate` / `ipc` は 3 巡とも null | 各巡 WAL `bench_done.payload.perf_observation` |
| 機体 | Pegasus (`env_tag: pegasus`)。ノードは巡ごとに異なる (§2.1) | 各巡 WAL `env_tag`、`reservation.json` の `IZANAGI_RESERVATION_HOST` |
| 知識水準 | K2。manifest は wal-only 1 件 (resolver digest `396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e`)。呼び手宣言 `classification=known_result_conditioned_derivative` / `de_novo_claim=false` / `pilot_comparison_eligible=false` | 各巡 WAL `build_start.payload.knowledge_provenance`、`knowledge_manifest_receipt.json` (3 巡とも同一 bytes、§5.1) |
| whiteboard | 5 field (`iteration` / `direction` / `magnitude` / `result` / `delta_pct`)。`delta_pct` は harness の設計 (`_DELTA_PCT_LIVE = False`) で常に null | 各巡 `loop_state.json`、2 巡目・3 巡目の記録 |
| 停止判定 | harness の `check_stop` (anomaly ≥ 1 で即 reject、`continue` 以外で停止、walltime 予算 3600 秒)。3 巡とも `continue` | 各巡 `job.stdout` の「停止判定: continue」、3 巡目 `run-summary.json` の `stop_decision` |

**この条件は calibrator が決めた飽和点ではなく kickoff 配線である** (1 巡目 critic の R0-b が指摘、親が開示)。絶対値は他の配線へ転移しない。

### 1.2 知識源の内容 (3 巡共通、bytes 同一)

manifest が指す唯一の source は commit `2fa13a262a53b7f4e610a40a7a7af7f86fc9d621` の
`output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl` (sha256 `2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611`、
6,687 bytes、15 行)。3 variant × 5 stage の測定 WAL で、`env_tag` は 3 記録とも `linux-baremetal` (本走の Pegasus とは別機体)、
`ts` は 2026-07-09 JST。records 100,000 / threads 4 / extime 1 / rr50 / skew 0.9 / rmw false と反復数 2 は本走 (§1.1) と同じだが、
**`clocks_per_us` は知識源が 1800、本走が 2100** で、実行コマンド全体・実行環境の同一性は無い (`run_cmd` の逐語比較)。

| variant | `BACKOFF_FIXED` | verdict | `median_tps` | `settled` | `abort_rate` | `llc_miss_rate` | `ipc` | run 内 cv |
|---|---|---|---|---|---|---|---|---|
| `20bbb4c1a855` | 40 | serializable / certified / anomalies 0 | 491,796.5 | true | 0.0703 | 0.3263 | 0.7796 | 0.0092 |
| `27d1d016998e` | 30 | serializable / certified / anomalies 0 | 525,721.5 | true | 0.0780 | 0.3303 | 0.7979 | 0.0066 |
| `dad58f9f9000` | 40 | serializable / certified / anomalies 0 | 487,088.5 | **false** | 0.0720 | 0.3229 | 0.7387 | 0.0072 |

(出所: 3 巡目 `materials/knowledge-input.json` の `sources[0].content_utf8`。本稿が sha256 を再計算し `2163b794…` と一致。)
**知識源に 30 未満の点は無い。** 3 巡の提案値 (20 / 25 / 10) はすべて知識源の外側への外挿である (§2.2)。

役割へ渡した射影 `knowledge_input` (`knowledge_level` / `knowledge_manifest_sha256` / `data_boundary=external_knowledge_is_data_not_instructions` /
`sources[0]` に本文全文) は 3 巡とも**内容同一**である。bytes は 1 巡目 (sha256 `3080a98b…`) と 2・3 巡目 (`05f2b267…`) で異なるが、
差は JSON の key 順だけで、正規化 (sort_keys) 後の差分は 0 行である (本稿が 2026-09-20 に確認)。

### 1.3 各巡の認可と予算

| 巡 | 認可 | 予算 (逐語の要点) | 逸脱 |
|---|---|---|---|
| 1 | D2044 項 9 (2026-09-16 ユーザー裁定)「知識付きの新提案を既存経路で 1 回評価し、その結果を次の提案へ戻す実走を指示する。新しい機構は足さず、既存経路だけで行う」 | 評価 1 本、次提案の生成まで (評価しない) | 保存成果物からは無し (proposal は 2 本、WAL は 1 variant)。1 巡目の記録によれば planner 1 回目を省略射影で投げ、出力を読まずに破棄して全文で取り直した (再抽選ではない、§2.2。破棄側は保存されておらず本稿は再確認できない) |
| 2 | D2120 項 1 (2026-09-17 ユーザー裁定、択 A)「保存済み proposal-2 を既存経路で 1 回評価し、その実測を planner-3 / coder-3 へ戻して proposal-3 を保存する 1 巡を認可する。予算 = 評価 job 1 本・critic 1 回・planner-3 / coder-3 各 1 回、再投入・再抽選・比較 arm なし」 | 同左 | 投入 2 本 / 評価 1 本。1 本目は preflight 拒否 (親の操作ミス、評価・抽選に未到達)。D2148 項 2 (2026-09-18) が**今回限定で事後承認** |
| 3 | ユーザー決定 (2026-09-19)「候補の生成 1 回・評価 1 本・同 job の stock 対照 1 本、再投入なし」。診断経路は D2148 項 3 / D2155 | 候補 1 + stock 1 | **stock 対照は未達 (縮小走行)。** [T-2795] で裁定待ち (択 (i) 同 job pair launcher を別 wave で実装 / (ii) 縮小走行として受理 / (iii) pair 要求を維持し scope を別途確定)。既知値 20 が出た場合は投入しない裁定だった |

3 巡とも**実装面の差分ゼロ**で走った (2 巡目の wave は同時に機序仮説層 v3 を実装したが、loop の評価経路・whiteboard・判定は触っていない。§0.3)。

### 1.4 役割と入力の型

| 役割 | 定義 | 入力の key (保存 JSON から) | 3 巡目で増えたもの |
|---|---|---|---|
| planner-v4 | tool なし・構造化出力。方向 (`increase` / `decrease` / `explore_both`) と magnitude を出し、値も機序も出さない | `current_perf` / `leading_indicators` / `whiteboard` / `knowledge_input` | `k2_critic_diagnosis` |
| coder-v4-autonomous-k2 | tool なし・構造化出力。`planner_direction` と K2 知識から値と hole 実装を合成し、`knowledge_use` / `classification` / `data_boundary_report` を自己申告 | `baseline` / `planner_direction` / `whiteboard` / `knowledge_input` / `leakproof_context` | `k2_critic_diagnosis` |
| critic | Bash を持つ role (legacy)。digest と WAL を読み `attribution` / `recommend` / `avoid` / `uncertainty` を書く | `role` / `campaign_id` / `campaign_dir` / `iteration` / `digest_path` / `digest_sha256` / `evaluated_variant` / `genome` / `output_format_request` / `parent_disclosures` (10 key、2 巡目・3 巡目の保存入力。1 巡目の critic 入力 JSON は保存されていない) | — |

`k2_critic_diagnosis` (D2155) は、親が指定した critic 逐語の bytes から既存抽出器で 4 節を取り、`data_boundary` と `source_sha256` を
加えた exact 6 field で、planner と coder の**両方に同一の診断**を渡す。whiteboard の 5 field・`delta_pct=None`・AO 非読取・評価・停止判定は不変で、
実 consumer は登録 Claude role への親の inline 送付である (D2155 逐語)。**1 巡目・2 巡目の入力にこの key は無い** (§2.2 の各表)。

規律 6 の自己申告の形式は role ごとに違う: coder は構造化 field `data_boundary_report.instruction_like_content_detected` (bool) と `details`、
planner は `uncertainty` の散文、critic は出力冒頭の「信頼境界検査」節の散文である (§2.4)。

役割の起動は、各巡の記録によれば親が保存済み入力 JSON の全文を prompt に入れて inline で行った (自動 launcher は無い)。
**保存された入力・prompt の範囲には欠落がある** — 1 巡目は prompt 全文と coder-2 の実入力 JSON が保存されておらず、2 巡目以降は
`*-input-*.json` と `*-prompt-*.md` が保存されている (§4.1)。起動・完了時刻は保存成果物に無い。

### 1.5 判定規則 (結果を見る前に固定されていたもの)

- **既知値の再提案:** run-card (`output/insights/2026-09-10_cc-next-precheck/run-card.md`) の投入契約 1「新提案が 20/30/40 を再提案した場合は
  『既知値の再提案』と記録し、未評価値生成の成功へ数えない。新しい値が出るまで再抽選する操作はしない」。本稿はこの集合をそのまま使う。
- **正しさ:** verify が anomaly ≥ 1 を返せば harness が即 reject (規律 2)。3 巡とも発火していない。
- **`success`:** whiteboard の `result=success` は certified の意味 (harness)。性能改善ではない。
- **`prior_critic_reverse`:** proposal の bool。機械 consumer は `_fold_critic_reverse` と停止判定だけで planner / coder の方向生成器には渡らない。
  1 巡目 proposal-1 は null、以後は親の解釈で false (critic が逆方向 = increase を推奨していない)。
- **知識の分類:** 呼び手宣言は `known_result_conditioned_derivative`。driver は proposal 側の `classification` を読み捨てるので、role の自己申告との一致は
  機構が保証したものではない (3 巡とも一致した、§2.2)。

---

## 2. 結果

### 2.1 3 巡通し — 評価 3 本の terminal record (campaign WAL から)

| 巡 | 日付 (JST) | job / host | submit-tree HEAD (= 着手時 local main) | variant | value | verdict (legacy) | commits / aborts / anomalies | `median_tps` | 2 反復 `tps` | run 内 cv | `abort_rate` (perf build) | `latency_ns` | 停止判定 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-09-16 | `1216.nqsv` / bnode058 | `d97c423bd` | `8a84a7b00103` | 20 | serializable / certified | 469,618 / 83,034 / **0** | 719,324.5 | 727,985 / 710,664 | 0.01703 | 0.0775 | 5,494.6187 | continue |
| 2 | 2026-09-18 | `4954.nqsv` / bnode110 | `d2ebef7a4` | `3dec27291054` | 25 | serializable / certified | 445,394 / 71,877 / **0** | 687,508.5 | 692,403 / 682,614 | 0.01007 | 0.0740 | 5,818.4048 | continue |
| 3 | 2026-09-19 | `10761.nqsv` / bnode020 | `a99425b66` | `002642c7ac96` | 10 | serializable / certified | 523,120 / 122,211 / **0** | 815,983.0 | 815,067 / 816,899 | 0.00159 | 0.0907 | 4,902.0691 | continue |

- `commits` / `aborts` / `anomalies` は trace-enabled build の verify 走の値、`median_tps` 以下は trace-disabled build の bench 走の値 (別 build・別 run、規律 1)。
  verify 走の abort 率 (aborts ÷ (commits + aborts)) は 15.02 % / 13.90 % / 18.94 % で、perf 走の `abort_rate` と並べて読まない (1 巡目 critic の R5、3 巡目 critic の avoid)。
- **`abort_rate` の集約規則は 1 巡目と 2・3 巡目で違う。** 1 巡目は 2 反復のうち速い側 (727,985 tps) の代表 rep の値 (`runner.py` の `throughputs[len//2]`、1 巡目 critic が指摘し親が検算)。
  2 巡目以降は [T-2702] の是正で偶数 reps では中央 2 件の中央値。`median_tps` は 3 巡とも 2 点の真の中央値である。
- `llc_miss_rate` / `ipc` は 3 巡とも null (perf 不在、§1.1)。0 でも「差なし」でもない。
- `settled` は 3 巡とも true、`high_variance` / `unstable` は false。`bench_wall_s` は 2.09 / 2.10 / 2.09 秒。
- **この表の 3 行を比較しない** (限定 1)。3 巡目 critic が critic-2 の判別規則と照合した「abort_rate 9.07 % は 7–8 % 帯より上・10 % 未満、tps は非同時刻ながら 2 巡目比 +18.7 %」
  は critic の読みの記録であって、本稿の判定ではない。

### 2.2 巡ごとの入力 → 提案 → 評価 → 還流

#### 巡 1 (2026-09-16、wave `dev-wave-t2588-k2-loop-roundtrip`、記録 entry 1548)

| 段 | 事実 | 出所 |
|---|---|---|
| 入力 (planner-1) | `current_perf` = 知識源の最後の `bench_done` (variant `dad58f9f9000`、`throughput_ops_sec` 487,088.5 / `abort_rate_pct` 7.2 / `last_delta_pct` null)、`leading_indicators` = 同 (`cache_miss_rate_pct` 32.29 / `IPC_overall` 0.7387 / `contention_level` 未判定)、`whiteboard` = `[]`、`knowledge_input` (§1.2)。**この基準点は `settled=false` かつ `linux-baremetal`** (JSON 自体から読める)。親が prompt の散文でこれを開示したことは**記録による** (1 巡目の prompt は保存されていない) | `materials/planner-input-1.json`; 開示は 1 巡目記録 |
| 射影の事故 (**記録による**) | planner の 1 回目を知識源本文を省略記号で切った射影で投げ、**出力を見る前に停止して全文で取り直した**。破棄した側は読んでいないので候補の選り好みには当たらない、と記録は書く。破棄した prompt / 出力は保存されておらず、本稿は再確認できない | 1 巡目記録 §「射影の事故と是正」 |
| planner-1 | `axis=silo-backoff-magnitude` / `direction=decrease` / `magnitude=medium`。値も機序も出していない。uncertainty (1)〜(6) で機体差・`settled=false`・reps=2・contention 未判定・規律 6 の検査 (指示めいた文字列なし) を自分から挙げた | `materials/proposal-1.json` の `planner` |
| coder-1 | `value=20`、`implementation="double now_backoff = 20;"`、`confidence=medium`、`classification=known_result_conditioned_derivative`、`knowledge_use` は source 0 のみ、`instruction_like_content_detected=false`。coder の入力にある値は 40 と 30 だけで、「CV を大きく超えて分離できた既知の刻み幅 10 を踏襲して 30 → 20」と外挿した | 同 `coder` |
| 判定 | **20 は run-card が名指しする既知値 → 「既知値の再提案」。** 未評価値生成の成功に数えない。「再抽選していない」は**記録による** (保存された proposal は 1 巡目に 2 本 = proposal-1 / proposal-2 だけで、別候補の出力は保存範囲に無い)。[T-2581] が現行 pin で評価済みの値でもある | run-card 投入契約 1、1 巡目記録 |
| 投入前検査 (login、**記録による**) | `assert_closed_proposal_schema(..., coder_contract=CODER_CONTRACT_K2)` OK / `validate_backoff_preflight("double now_backoff = 20;")` accepted / `load_proposal_file(..., coder_role="coder-v4-autonomous-k2")` OK。負例 `"double now_backoff = 25 + 1;"` は `backoff-grammar.initializer-literal.v1` で拒否。検査の log は保存されていない | 1 巡目記録 |
| 評価 | §2.1 の 1 行目。job `1216.nqsv`、Created 15:57:02 → Started 15:57:09 → Ended 15:58:26 JST、Elapse 82 秒。`driver_rc=0`、`1 committed / 0 aborted / 0 skipped`、`outcome=certified`、`iteration=1` | WAL、`job.stderr` の NQSV 要約、`compute-result.json` |
| 受領証 | `knowledge_manifest_receipt.json` は計算ノードの job 内で生成。source の `verification.method=git-blob-at-commit-path` / `status=verified` / `observed_sha256=2163b794…`。`declaration_status` は「data_boundary と claim_boundary は記録上の宣言であり強制機構ではない」 | 受領証 (§5.1) |
| critic-1 | attribution: **どの設計選択についても「効いた / 効かない」は言えない** (campaign 内 1 点、stock 対照なし、別機体との比較は分離不能)。digest に指示混入なし。親の開示に無い所見 2 件 — (a) `latency_ns` は throughput の恒等変換で独立指標でない、(b) 偶数 reps では `abort_rate` / `latency` が速い側 rep から取られる — を出し、親が現物コードで両方確認した (同 file 末尾の「親による検算 (2026-09-16)」節にコード断片と算術が保存されている)。recommend は R0 (同一 campaign・同機体・同配線で stock を 1 点、配線凍結、reps を奇数に)、R1 (BACK_OFF 0 vs 1 を 1 組) を先に置き、`BACKOFF_FIXED` を振るのは R1 の後 (R2) | `verbatim/critic-1.md` (本文と末尾の親の検算節) |
| 還流 (planner-2 / coder-2) | 入力を本走の実測に差し替えた: `current_perf` 719,324.5 / 7.75 / null、`leading_indicators` null / null / 未判定、`whiteboard` 1 件 (`decrease` / `medium` / `success` / null)。(b) の集約のずれを prompt の散文で開示したことは**記録による** (prompt 未保存)。planner-2 は `decrease` / `small` (「現行 abort 率 7.75 % は帯の上端にほぼ一致」「刻みを縮めて転回の有無を 1 点で判別」)。coder-2 は `value=25`、`instruction_like_content_detected=false` (「最良点 30 から刻み 5 で 1 段下げた」)。**25 は既知値ではない未評価値**。proposal-2 は 1 巡目では**評価されていない** (1 巡目の WAL は variant `8a84a7b00103` の 5 record だけ)。proposal-2 が投入前検査 3 本を通したことは**記録による** | `materials/planner-input-2.json`、`materials/proposal-2.json`、1 巡目 WAL |
| 閉じていないもの | critic の診断は次の生成の型付き入力に届かない。`planner_context_payload` が射影するのは whiteboard・`knowledge_input`・任意 `policy_hint` だけで、`prior_critic_reverse` は方向生成器へ渡らない。**1 巡目が閉じたのは「実測の還流」であって「診断の還流」ではない** | 1 巡目記録 §「閉じていないもの」 |

#### 巡 2 (2026-09-18、wave `dev-wave-t2746-k2-loop-round2`、記録 entry 1652)

| 段 | 事実 | 出所 |
|---|---|---|
| 入力 | 1 巡目が保存した proposal-2 (`value=25`) をそのまま評価対象にした (2 巡目 `materials/proposal-2.json` は 1 巡目のものと bytes 同一、sha256 `3dbe30d7…`。job.stdout の起動行も `proposal=…/proposal-2.json` を指す)。`knowledge-input.json` は 1 巡目と内容同一 (§1.2) | `materials/proposal-2.json` (両巡)、`evidence/attempt-0002/job.stdout` |
| 投入前検査 (login、**記録による**) | 1 巡目と同じ 3 本 (`double now_backoff = 25;` accepted、負例 `25 + 1` 拒否)、manifest の resolver digest `396cd559…` を再実測。検査の log は保存されていない (digest 自体は WAL `build_start` と受領証に同じ値がある) | 2 巡目記録 |
| 投入 1 本目 | `4947.nqsv`: Created 06:33:25 → Started 06:33:59 → Ended 06:34:02 JST、Elapse 7 秒。job body preflight が `p3 S4 loop job refused: allocation qstat evidence is not fresh` で拒否 (`driver_rc=2`、campaign 未接触)。原因は親 — 投入直後に `qstat -f` の写しを evidence dir へ置き、job body が自分で書く file と衝突した | `evidence/attempt-0001/job.stderr`、`compute-result.json` |
| 投入 2 本目 | `4954.nqsv`: Created 06:36:06 → Started 06:36:14 → Ended 06:43:21 JST、Elapse 432 秒。§2.1 の 2 行目。`1 committed / 0 aborted / 0 skipped`、`outcome=certified` | WAL、`evidence/attempt-0002/job.stderr` |
| 所要の内訳 | WAL ts: build_start 06:36:48 → build_done 06:37:03 → verify_done 06:37:14 → bench_done 06:43:21。**verify_done → bench_done は約 367.3 秒で、記録された `bench_wall_s` は約 2.10 秒。差の約 365.2 秒の内訳はこの WAL からは特定できず、原因は追跡されていない** (1 巡目・3 巡目の同区間は約 2 秒で、build_start → commit の全体でも 32 秒 / 30 秒) | WAL ts、`bench_done.payload.bench_wall_s` |
| 逸脱 | 「再投入なし」に対し投入 2 本。評価・抽選には 1 本目が到達していないので再測定・再抽選ではない。D2148 項 2 が今回限定で事後承認し、preflight 失敗を一律に予算外とする一般規則は作らないと定めた | D2148 項 2 |
| critic-2 | digest (sha256 `a0a4c204…`) と WAL 5 行を全文読み、**指示めいた文字列は無い** (機械 grep は digest 0 件、WAL は perf event 名 `instructions` の 1 件のみ)。attribution: **どの設計選択にも帰属できない** (campaign 内 1 点、stock 対照なし、1 巡目との −4.4 % は非同時刻)。機序の候補として「abort 1 回につき backoff 1 回、value 25 で thread 時間の約 34 % が backoff spin (計測値でなく導出)」。**recommend R1 = `decrease` / `large`、候補値 10** (次いで grammar 下限 1 を floor probe に)、R0 = 同一 job 内の stock 対照。avoid: 20 / 25 / 30 を刻み 5 で往復すること | `verbatim/critic-2.md` (sha256 `d2b2ab77…`) |
| 還流 (planner-3 / coder-3) | 入力: `current_perf` (`throughput_tps` 687,508.5 / `abort_rate_pct` 7.4)、`leading_indicators` null / null / 未判定、`whiteboard` 1 件 (`decrease` / `small` / `success` / null)、`knowledge_input`。**`k2_critic_diagnosis` は無い** (経路が未実装)。planner-3 は `decrease` / `medium`。coder-3 は **`value=20`**、`classification=known_result_conditioned_derivative`、`instruction_like_content_detected=false` (「K2 記録の 40→30 の向きを 30 の下側へ外挿」) | `materials/planner-input-3.json`、`coder-input-3.json`、`proposal-3.json` |
| 判定 | **20 は既知値の再提案** (run-card)。coder-3 の保存入力には 20 が評価済みであること (1 巡目は別 tree の WAL) も、critic-2 の候補 10 も載っていない (key 集合に `k2_critic_diagnosis` が無い)。**この巡では「診断が型付き入力に無い」ことと「critic の候補 10 に対し coder が 20 を出した」ことが併存した記録である。両者の因果は未検証** (§2.3)。proposal-3 は評価されていない (3 巡目へ進まない裁定。2 巡目 WAL は variant `3dec27291054` の 5 record だけ)。投入前検査 3 本を通したことは**記録による** | `materials/coder-input-3.json`、`proposal-3.json`、2 巡目 WAL、2 巡目記録 |
| 材料レポート | 同 wave が実装した機序仮説層 v3 の取込み口で AO 4 event (planner-2 / critic-2 / planner-3 / coder-3) を記録 (AO 4 行は権威 bytes で確認)。**coder-2 の event は無い。** 理由 (1 巡目で coder-2 へ渡した実入力 JSON が保存されておらず `input_sha256` を真に計算できない、裁定 A4) は**記録による**。§2.6 | `layer3_report.json`、AO (§5.1)、2 巡目記録 |

#### 巡 3 (2026-09-19、wave `dev-wave-k2-loop-round3`、記録 entry 1691)

| 段 | 事実 | 出所 |
|---|---|---|
| 診断入力の組立て | 2 巡目の critic-2 逐語 (sha256 `d2b2ab77…`) から `k2_critic_diagnosis_from_bytes` で exact 6 field (`attribution` 2,035 字 / `recommend` 1,469 字 / `avoid` 639 字 / `uncertainty` 1,802 字 / `data_boundary` 41 字 / `source_sha256` 64 字) を作り、`planner_context_payload` (K2・非 B-4・reflux on の適用条件検査込み) → `k2_next_generation_inputs` で planner-4 / coder-4 の両入力へ**同一の診断**を組み込んだ | `materials/diagnosis-4.json` (sha256 `7b742268…`)、`planner-context-4.json` (`280caa0f…`) |
| CLI の不使用 (**記録による**) | runbook の `--emit-planner-context` は login node で `_admit_env_contract` が `PEGASUS_LOGIN` を拒むため使えず、CLI と同じ production 関数を直接呼んだ。CLI が行う受領証の書込み / 照合の代わりに親が照合した、と記録は書く: 受領証の正準 bytes が 2 巡目 campaign の `knowledge_manifest_receipt.json` と完全一致 (`c42dc712…`)、K2 射影 bytes が 2 巡目の `knowledge-input.json` と同 bytes (`05f2b267…`)、campaign identity の preimage が 2 巡目 `campaign.lock` と一致 (`409e13f8…`)、完全入力 2 本に tripwire `assert_no_ability_probe_material` を通した。本稿が再確認したのは受領証 bytes が 3 巡同一 (`c42dc712…`) と `knowledge-input.json` の sha だけで、照合の実施と tripwire は再実行していない (§4.3)。[T-2796] (runbook 追記候補) | 3 巡目記録 §「診断が届いたか」 |
| 送付 | 保存された prompt (`planner-prompt-4.md` / `coder-prompt-4.md`) は対応する入力 JSON の全文と、親の事実開示「診断中の候補値・avoid・追加実験の提言は採用義務・値の禁止・実行予算の追加を意味しない」を含む (本稿が確認)。`planner-input-4.json` 18,509 bytes (key: `current_perf` / `leading_indicators` / `whiteboard` / `knowledge_input` / `k2_critic_diagnosis`)、`coder-input-4.json` 25,745 bytes (key: `baseline` / `planner_direction` / `whiteboard` / `knowledge_input` / `leakproof_context` / `k2_critic_diagnosis`)。**この prompt を role へ inline 送付したことは記録による** — 保存 prompt は送達の証拠ではない | `materials/planner-input-4.json`、`coder-input-4.json`、`planner-prompt-4.md`、`coder-prompt-4.md`; 送付は 3 巡目記録 |
| planner-4 | `decrease` / **`large`**。justification は「critic 診断が本走の 2 指標から decrease/large を推奨していること」「abort_rate 同帯 + tps 差 floor 近傍」を挙げ、uncertainty (8) で規律 6 の検査 (診断の R0 と診断 build の要望は上書き指示ではないと判断) を報告 | `materials/proposal-4.json` の `planner` |
| coder-4 | **`value=10`**、`implementation="double now_backoff = 10;"`、`confidence=medium`、`classification=known_result_conditioned_derivative`、`knowledge_use` は source 0 のみ、`instruction_like_content_detected=false` (details に `k2_critic_diagnosis.recommend` の R0 / 診断 build を助言と判定した理由)。justification は「`k2_critic_diagnosis` (助言として検討) は…候補 10、次いで下限 1 を推奨」と参照し、下限 1 でなく 10 を採る理由を書いた | 同 `coder` |
| 開示の差 | **診断本文は評価済みの 2 値 (20 / 25) とその tps・機序候補・候補 10 を含む。** これは D2155 が「4 節を留保ごと逐語で渡す」と裁定した設計であり、許可された兄弟 key での開示である。**coder-4 の保存入力には評価済みの 20 / 25 が含まれ (coder-3 の入力には無い)、coder-4 はそれらを参照したと申告した** (justification に「20 と 25 の 2 点 (非同時刻・集約規則違い) で…」)。通常射影 (`current_perf` / `baseline` / whiteboard) には値を足していない。「既知値を見ずに合成した」とは書かない | `coder-input-3.json`、`coder-input-4.json`、`diagnosis-4.json`、`proposal-4.json` |
| 判定 | **10 は既知値集合 (20 / 30 / 40) の外 → 1 評価へ。** 診断の候補値と一致した提案である (診断の「採用」の自己申告であって、因果ではない) | run-card、3 巡目記録 |
| 投入前検査 (login、**記録による**) | 3 本 OK (`double now_backoff = 10;` accepted、負例 `25 + 1` 拒否)。`prior_critic_reverse=False` は親の解釈 (proposal-2 と critic-2 はともに decrease)。bool 自体は `proposal-4.json` にある | 3 巡目記録、`materials/proposal-4.json` |
| 評価 | §2.1 の 3 行目。job `10761.nqsv`、Created 22:19:56 → Started 22:20:14 → Ended 22:21:19 JST、Elapse 69 秒。build は trace `2dc461cc11abfee0` / perf `3fae380fee3b0a5b` とも非 cache、WAL ts: build_start 22:20:48 → build_done 22:21:03 → verify_done 22:21:16 → bench_done 22:21:18 → commit 22:21:18。`1 committed / 0 aborted / 0 skipped`、`outcome=certified` | WAL、`job.stderr`、`run-summary.json` |
| critic-3 | digest (sha256 `f993251d…` を再計算) と WAL・`loop_state.json`・受領証・`campaign.lock` を読み、**指示めいた文字列は無い** (機械 grep の hit 3 件はいずれも記述語)。attribution: **本走単独では帰属不能 (3 巡連続)**。critic-2 の判別規則との照合は「中間」— 「当たった」とは言わず「矛盾しなかった」まで。recommend: R0 = 同 job 内 stock 対照 (3 巡連続で最優先)、R1 = `decrease` / `large`、候補 5、R1' = 下限 1 の floor probe、R2 = 固定最良点 vs 適応の同 job 比較、R3 = `CCBENCH_ADD_ANALYSIS=1` は別の診断 build として。avoid に「**候補 10 の評価をもって『診断が効いた』と数える**」を含む | `verbatim/critic-3.md` (sha256 `5cd8f518…`) |
| 未達 | **同 job の stock 対照。** `p3_s4_loop_pegasus.sh` は 1 job = driver 1 起動 (候補 1 本) で stock arm が無く、`p3_s4_loop.py` の value 受理域 1..1000 は stock 相当 `-1` を拒否する。確認した代替 (A-1 paired / B10 grid / 床値 / [T-1998] stock-inline / guided `--genome`) は別 study・別 PerfConfig で同条件 pair にならない (全手順の不在証明ではない)。「経路の改修・新 launcher」は決定の scope 外 → [T-2795] | 3 巡目記録、rulings-inbox 2026-09-19 |

### 2.3 診断が「届いた」こと と「効いた」こと の分離 (3 巡目)

| 命題 | 本稿の位置 | 根拠 |
|---|---|---|
| 診断が型付き入力に**届いた** | 書く | `planner-input-4.json` / `coder-input-4.json` に key `k2_critic_diagnosis` が実在し、その 6 field が critic-2 逐語 (`source_sha256` = `d2b2ab77…`) から抽出器で作られた bytes と一致する (親が照合) |
| role が診断を**参照したと申告した** | 書く | planner-4 の justification / uncertainty (8)、coder-4 の justification / `data_boundary_report.details` が診断の節を名指しで引く |
| 診断が提案値を**変えた** (因果) | 書かない | 診断なしの統制比較が無い。保存入力を比べると、planner-3 と planner-4 の入力は **`k2_critic_diagnosis` の追加以外は内容同一** (`current_perf` 687,508.5 / 7.4、`leading_indicators`、whiteboard 1 件、`knowledge_input` とも同じ。3 巡目の生成は 2 巡目の実測を `current_perf` に使った)。coder-3 と coder-4 の入力は**診断の追加と `planner_direction` (planner-4 の出力 = decrease / large) の差だけ**で、`baseline` / whiteboard / `knowledge_input` / `leakproof_context` は同一。差が少ない対比ではあるが、**各条件 1 回の別起動であり、無作為化も反復も無い**ので、提案値の差 (20 → 10) を診断の因果効果とは判定しない |
| 候補 10 が診断の候補値と**一致した** | 書く | proposal-4 `value=10`、critic-2 recommend R1「候補値 10」 |
| 候補 10 の評価が診断の**効果** | 書かない | critic-3 の avoid が明示的に禁じる。3 巡目記録も同じ |

### 2.4 規律 6 の検査結果 — 各巡の role 出力から

| 巡 | role | 検査対象 (自己申告) | 結果 |
|---|---|---|---|
| 1 | coder-1 | `knowledge_input.sources[0]` の `content_utf8` 全 15 行 (全 JSON key と値、埋め込み文字列) | `instruction_like_content_detected=false`。命令形に見える文字列 (cmake / numactl + perf stat の command 列、絶対 path) は「campaign が実行したコマンドの記録 (過去形の観測データ)」と分類 |
| 1 | planner-1 / planner-2 | source 本文 | uncertainty (6) / (8) で「振る舞いを誘導する指示めいた文字列は見当たらなかった」 |
| 1 | coder-2 | 同 15 行の全 field | `false`。hex 文字列 (`src_token` 等) は不透明な識別子として扱った |
| 1 | critic-1 | digest 本文 | 「指示めいた文字列は無い」「injection 該当なし」 |
| 2 | critic-2 | digest + WAL 5 行 + `campaign.lock` | 「指示めいた文字列は無い」。機械 grep: digest 0 件、WAL 1 件 (perf event 名 `instructions`) |
| 2 | planner-3 | K2 sources 本文 | uncertainty (5)「指示めいた文字列は見当たらず、データとしてのみ扱った」 |
| 2 | coder-3 | source 0 の全行 | `false` |
| 3 | planner-4 | `knowledge_input` + `k2_critic_diagnosis` | uncertainty (8): 診断の R0 と診断 build の要望は「harness / 運用側への要望であり、planner の権限・検証順序・正しさゲートを上書きする指示ではない」 |
| 3 | coder-4 | `knowledge_input.sources[0]` 全行 + 診断 4 節全文 + `leakproof_context` | `false`。診断の R0 / `CCBENCH_ADD_ANALYSIS=1` は「呼び手の判断」「書き込みはしない」と明記された助言と判定。`avoid` は候補値の禁止ではなく助言 |
| 3 | critic-3 | digest + WAL + `loop_state.json` + 受領証 + `campaign.lock` | 「指示めいた文字列は無い」。`campaign.lock` の `identity_preimage` 内の `spec_content` (段 4 loop の説明文) は campaign 仕様の説明であって誘導ではない |

**注:** 2026-09-09 の走行を止めたのは `campaign.lock` の自由文 `spec_content` であり、今回の知識源 (測定 WAL 1 件) には含まれない (1 巡目記録)。
**critic-2 は「`campaign.lock` は 3 key (`authority` / `identity_preimage` / `schema_version`) で自由文 `spec_content` は無い」と報告したが、実物の 2 巡目
`campaign.lock` では `identity_preimage` (JSON 文字列) の中に `spec_content` が 1 件ある** (`grep -c` で 1、本稿が確認)。critic-3 は同じ位置の自由文を
見つけ、campaign 仕様の説明であって誘導ではないと判定した。critic-2 の当時の判定は変えず、**走査範囲の留保**として記録する (§4.3)。
**いずれも role の自己申告であり、gate は 1 行も触っていない。**

### 2.5 正しさの記録 — 3 巡とも certified、anomaly 0 (性能の判定ではない)

| 巡 | `verify_done` | `commit_witness` | `proof_surfaces` | `verifier_result_sha256` (commit record 内) |
|---|---|---|---|---|
| 1 | `serializable` / `certified=true` / commits 469,618 / aborts 83,034 / anomalies 0 / workload `legacy` | {commit_counts 469,618, batch_commit_counts 0} | protocol `silo`、X present / P present / I absent | `45b96812…` |
| 2 | `serializable` / `certified=true` / 445,394 / 71,877 / 0 / `legacy` | {445,394, 0} | 同 | `4b8ea125…` |
| 3 | `serializable` / `certified=true` / 523,120 / 122,211 / 0 / `legacy` | {523,120, 0} | 同 | `2fedd3d4…` |

- 正しさは trace-enabled build の別 run で取っており、bench (trace-disabled) とは別 build・別 run である (規律 1)。
- `certified` は「この 1 条件の trace で G2 を含む cycle が検出されなかった」の意味で、**候補間の certified な選択ではなく、性能の判定でもない**。
- commit record の `commit_verification_receipt` は `sink_kind=campaign-wal`、`lock_identity_sha256` が各巡の `campaign.lock` の sha256 と一致する
  (1 巡目 `48520c2b…`、2 巡目 `fc7acaca…`、3 巡目 `f1ab4966…`。§5.1)。
- 3 巡とも verify は legacy 条件 1 回ずつであり、採用候補の検証相 (`2026-09-20-verify-phase-adopted-backoff.md`) のような多反復ではない。

### 2.6 材料レポート (機序仮説層 v3、2 巡目・3 巡目)

| 巡 | `layer3_report.json` sha256 | `schema_version` | `agent_outputs` | `mechanism_hypotheses` | `source_refs` | `certifying_input` | `admission_decision` | `noise_floor` |
|---|---|---|---|---|---|---|---|---|
| 2 | `f6dca3b9…` | `layer3-material-report/v3` | 4 件 (planner-2 / critic-2 / planner-3 / coder-3) | 1 件 (variant `3dec27291054`、attribution = critic-2 逐語、digest `a0a4c204…`、refs 5) | 10 = wal 5 + wb 1 + ao 4 | **false** | admitted / admitted-new-schema | between / within とも `no-matching-env-record` |
| 3 | `c37fda1f…` | 同 | 3 件 (planner-4 / coder-4 / critic-3) | 1 件 (variant `002642c7ac96`、attribution = critic-3 逐語、digest `f993251d…`、refs 5) | 9 = wal 5 + wb 1 + ao 3 | **false** | 同 | 同 |

- 1 巡目には材料レポートが無い (v3 は 2 巡目の wave で実装。1 巡目 campaign は当時の renderer が描画できなかった、2 巡目記録の N1)。
- `mechanism_hypotheses` は **LLM (critic) の帰属記録であって機序の実証ではない**。両巡とも critic の結論は「帰属不能」である。
- `noise_floor` が `no-matching-env-record` なのは、較正記録は走査された (`scanned_files` 2 巡目 7 / 3 巡目 8) が本走の条件 (silo / 4 threads /
  100,000 records) に適合する採用可能な記録が無いため — between-run は候補 3 file (`between_run_noise_t48_skew0p9_rr50/rr5/rr95_rmw0.json`) が
  いずれも 48 threads / 1,000,000 records で不一致、within-run は候補 0 で、登録済み較正 pin (`calibration-753f535a8d024727.json`) が
  `within_run_exclusion = self-inconsistent-calibration` で除外されている。**2 巡目の記録が「submit-tree に較正記録が無い」と書くのは、
  この材料レポートの記録 (走査 7 file・候補 3 file の条件不一致) より粗い説明である** (§4.3)。
- AO の `input_sha256` / `mode` / `ts` は申告した保存 JSON の canonical sha256・記録方式・記録時刻であって、role が実際にその入力を受け取ったことの証明ではない。

### 2.7 時系列 (JST。job の Created / Started / Ended / Elapse は各 job の `job.stderr` 末尾の NQSV 要約、WAL は `ts` (epoch) の変換)

| 巡 | 出来事 | 時刻 |
|---|---|---|
| 1 | job `1216.nqsv` Created / Started | 2026-09-16 15:57:02 / 15:57:09 |
| 1 | WAL `build_start` → `build_done` → `verify_done` → `bench_done` → `commit` | 15:57:54 → 15:58:12 → 15:58:24 → 15:58:26 → 15:58:26 |
| 1 | job Ended (Elapse 82 秒) | 15:58:26 |
| 1 | critic-1 → planner-2 / coder-2 → proposal-2 保存 (未評価) | 保存成果物に時刻は無い。同日 (2026-09-16) であることと順序は 1 巡目の記録による |
| 2 | job `4947.nqsv` Created / Started / Ended (preflight 拒否、Elapse 7 秒) | 2026-09-18 06:33:25 / 06:33:59 / 06:34:02 |
| 2 | job `4954.nqsv` Created / Started | 06:36:06 / 06:36:14 |
| 2 | WAL `build_start` → `build_done` → `verify_done` → `bench_done` → `commit` | 06:36:48 → 06:37:03 → 06:37:14 → 06:43:21 → 06:43:21 |
| 2 | job Ended (Elapse 432 秒) | 06:43:21 |
| 2 | critic-2 → planner-3 / coder-3 → proposal-3 保存 (未評価) → AO 取込み・材料レポート | 保存成果物に時刻は無い。同日 (2026-09-18) であることと順序は 2 巡目の記録による (AO の `ts` は記録時刻であって起動時刻ではない) |
| 3 | 診断入力の組立て → planner-4 → coder-4 → proposal-4 | 保存成果物に時刻は無い。job の実行 log (`job.stdout` の起動行) が示すのは、実行中の driver が `proposal-4.json` を評価対象として使用したこと (= 遅くとも build_start 22:20:48 の時点で file が存在した) までである。生成日 2026-09-19 と「job 投入 (22:19:56) より前に生成した」という順序は 3 巡目の記録による |
| 3 | job `10761.nqsv` Created / Started | 22:19:56 / 22:20:14 |
| 3 | WAL `build_start` → `build_done` → `verify_done` → `bench_done` → `commit` | 22:20:48 → 22:21:03 → 22:21:16 → 22:21:18 → 22:21:18 |
| 3 | job Ended (Elapse 69 秒) | 22:21:19 |
| 3 | critic-3 → AO 取込み 3 event → 材料レポート | 保存成果物に時刻は無い。同日 (2026-09-19) であることは 3 巡目の記録による (`ingest-real.log` は job root) |

各巡の順序のうち、**保存成果物から言えるのは「driver が起動時に proposal file を評価対象として使用した」(各巡 `job.stdout` の起動行) と、
2 巡目・3 巡目について「critic の保存入力がその評価の digest sha を含む」(`critic-input-2/3.json`) だけ**である。critic-1 の入力 JSON は
保存されておらず、critic-1 が同走の digest を入力にしたことは逐語冒頭の自己記述による。**役割の起動日時と細かな実施順序は各巡の記録による** (§4.1、§4.3)。

---

## 3. 限定 — この結果が言わないこと

1. **性能の改善・退行。** 同時刻対照 (stock、または同 job 内の別値) がどの巡にも無い。3 走は別日 (09-16 / 09-18 / 09-19)・別ノード (bnode058 / 110 / 020)・
   別 submit-tree・別 WAL である。3 巡目の 815,983 tps は非同時刻の 1 点であり、2 巡目比 +18.7 % / 1 巡目比 +13.4 % といった比は書いても性能主張にならない。
   1 巡目と 2 巡目の −4.4 % も同じ。critic-3 の純コスト模型 (25 → 10 で予測比 1.21、観測 1.19) は「矛盾しなかった」までで、模型の前提 (abort ごと backoff 1 回、
   `clocks_per_us=2100`、他の待機無視) は未検証である。
2. **同 job stock 対照の未達は裁定待ちである** ([T-2795])。本稿は 3 巡目を「認可の完全達成」とは書かず、縮小走行の受理可否も判定しない。
3. **知識 (K2) の因果効果。** `knowledge_use` / `classification` は role の自己申告であり、知識なし統制が無い。受領証の `claim_boundary` も宣言であって強制機構ではない。
4. **診断の因果効果** (§2.3)。3 巡目で診断は届いたが、診断なし統制が無いので「効いた」は言えない。coder-3 と coder-4 の対比は非統制である。
5. **B-4 の適格性。** 3 巡とも Bash を持つ legacy critic を使い、planner → coder の漏れの遮断 (route-local) も完備ではない。B-6 の材料であって B-4 の材料ではない。
6. **既知値の再提案 2 回 (1 巡目 20、2 巡目 20) は「未評価値生成」の成功に数えない** (run-card)。25 と 10 は未評価値だが、いずれも固定 backoff の初期値であって
   新しい CC 構造の合成ではない。
7. **perf counter の欠測。** `llc_miss_rate` / `ipc` は 3 巡とも null。機序の裏取りには使えず、role も使っていないと申告した。
8. **`abort_rate` の集約規則が 1 巡目 (速い側 rep) と 2・3 巡目 (中央 2 件の中央値) で違う** (§2.1)。1 巡目の 7.75 % と 2・3 巡目の 7.40 % / 9.07 % を同じ規則の値として並べない。
9. **知識源は別機体 (`linux-baremetal`、2026-07-09、`clocks_per_us` 1800) で、1 点は `settled=false`。** coder は「絶対 tps は本走へ直接転移しない」と
   申告する一方、**方向に加えて既知の backoff 値 (40 / 30)・相対差 (約 +7 %)・abort 率の変化幅 (1 pt 弱)・刻み幅 (10、5) を提案根拠に用いた**と
   申告している (`knowledge_use` / `justification`)。K2 が生成へ開示した定量情報はこの範囲に及び、本稿はその妥当性も因果効果も確認しない。
10. **campaign ID `409e13f8` の同一は走行の同一ではない** (§0.1)。同 ID の 3 tree の WAL を 1 つの campaign として集計しない。
11. **role の自己申告 (`classification`、`instruction_like_content_detected`、`knowledge_use`) と呼び手宣言は機構で照合されていない。** 3 巡とも一致したが、一致は機構の保証ではない。
12. **AO の `input_sha256` / `mode` / `ts`、診断の `source_sha256` は申告・記録・識別であって、role が実際にその入力を受け取ったことの証明ではない。**
13. **`certified` / `success` は正しさゲート通過の意味** (限定 5)。verify は legacy 条件 1 回ずつで、多反復の検証相ではない。
14. **2 巡目の投入 2 本 / 評価 1 本は事後承認済み (D2148 項 2)** であり、preflight 失敗を予算外とする一般規則ではない。
15. **1 巡目の planner 1 回目の破棄** (1 巡目の記録による) は、記録によれば出力未読で行った再投入であり候補の選り好みではないが、破棄側の prompt / 出力は
    保存されておらず本稿は再確認できない。「役割起動 1 回」の勘定からは外れる。
16. **各巡の `success` は certified の意味であり、whiteboard の `delta_pct` は常に null。** planner が受け取る「前巡は success」に改善幅の情報は無い。
17. **有意差判定・区間推定・認証の昇格はいずれも無い。** 材料レポートは `certifying_input=false`。3 巡の結果は A-2 / A-6 / [T-1998] の certified 記録の地位を変えない (規律 7)。
18. **run-card の既知値集合 (20 / 30 / 40) は run-card の規定である。** 本稿はそれを再定義せず、T-2581 の評価 (20) を含めて「既知」の理由を追加していない。
19. **critic-3 の純コスト模型の比 1.21 は、観測済みの throughput と abort 率から導いた spin 占有率を用いる事後的な計算であり、独立な事前予測の的中ではない。**
    観測比 1.19 と並べても「矛盾しなかった」以上を言わない (critic-3 自身の留保と同じ)。
20. **3 評価とも anomaly 0 で、正しさ側の赤 (anomaly 検出 → 即 reject → その構造化理由を次生成へ戻す) の還流は 1 度も発火していない。**
    本稿が示す還流は緑の実測と critic 診断の還流だけで、規律 3 が求める「なぜ壊れたか」の還流は実証していない。
21. **役割の起動は親が手で組んだ inline 送付であり、自動 launcher・送達 receipt は無い (D2155 逐語)。** 使用した LLM の厳密な版は保存入力・逐語からは
    特定できない。記録にあるのは role 定義名 (planner-v4 / coder-v4-autonomous-k2 / critic) と、critic-1 逐語冒頭の `opus/high` (model 族と reasoning の
    表示値) までで、他の role 出力に model の記載は無い。

---

## 4. 欠落 — 権威 bytes・WAL・裁定の対応が確かめられない箇所

### 4.1 回収成果物に情報が無い

不在の主張は、repo 内の 3 巡の insight dir (`materials/` / `verbatim/` / `evidence/` / `reviews/` の全 file 名) と、repo 外の 3 job root
直下の file 名一覧を 2026-09-20 に走査した範囲で言う。job root の file mtime は起動・完了時刻の証拠として扱わない。

- **役割起動の時刻。** planner / coder / critic の起動・完了時刻は proposal・逐語 JSON に無い。本稿は転記しない。
- **1 巡目の prompt 全文と coder-2 の実入力 JSON。** 1 巡目の `materials/` は `knowledge-input` / `leakproof-context-k2` / `planner-input-1` /
  `planner-input-2` / `proposal-1` / `proposal-2` の 6 file で、`coder-input-*.json` と `*-prompt-*.md` は無い。2 巡目の AO 取込みで coder-2 だけが
  `input_sha256` を計算できず未取込みになった理由 (裁定 A4: `input_sha256: null` も再構成入力も採らない) は 2 巡目記録による。coder-2 の出力
  (`value=25`) 自体は `proposal-2.json` にある。1 巡目の critic-1 の入力 JSON も保存されていない (critic-1 の逐語だけがある)。
- **2 巡目 verify_done → bench_done の約 367 秒の内訳。** WAL は 2 record の `ts` と `bench_wall_s` しか持たず、原因は追跡されていない。
- **1 巡目の材料レポート。** v3 実装前で、`layer3_report.json` は無い (当時の renderer が本 loop 型 campaign を描画できなかったことは 2 巡目記録による)。
- **投入前検査 3 本の log。** 3 巡とも保存されていない (§2.2 で「記録による」)。
- **3 巡目 critic-3 の「+1.65 pt」。** 表示値では 9.07 − 7.40 = 1.67 pt、実測値では 9.065 − 7.400 = 1.665 pt で、逐語は改変せず記録が注記している。帰属不能の結論は変わらない。

### 4.2 束縛の範囲が限られる

- **受領証の `data_boundary` / `claim_boundary` は宣言。** 受領証自身が「強制機構ではない」と書く。
- **campaign identity に提案値が入らない。** 5 key の同一で「同じ campaign」と読める範囲は設定の同一までで、走行の同一・提案値の同一は submit-tree / request / WAL で識別する。
- **driver は proposal の `classification` を読み捨てる。** role 自己申告と呼び手宣言の一致は照合されない。
- **`planner_context_payload` の適用条件 (K2・非 B-4・reflux on)** は 3 巡目の入力組立てで検査されたが、CLI を経ていないので CLI 側の書込み / 照合は親の代替照合である。

### 4.3 本稿で対応を再確認していない (実行者の記録に依存する手続き)

次は各巡の記録 README (実行者の自己記録) にしか無く、保存成果物から再確認できない。本稿はこれらを「記録による」と付けて書き、
独立に確認された実施証拠としては扱わない。

- 1 巡目の射影の事故 (planner 1 回目を出力未読で破棄) と、各巡の投入前検査 3 本の実施、「再抽選なし」「予算どおり」の遵守。
- 1 巡目の prompt の散文による開示 (機体差・`settled=false`・集約のずれ)。
- 3 巡目の CLI 拒否と親の代替照合 (受領証正準 bytes・identity preimage・K2 射影 bytes の一致、tripwire)。受領証の bytes が 3 巡とも同一
  (`c42dc712…`、1,317 bytes) であることと `knowledge-input.json` の sha は本稿が再計算した。
- coder-2 未取込みの理由、旧 renderer が 1 巡目 campaign を描画できなかったこと。
- 段 2 plan・段 3 相談・段 6 レビューの逐語 (各巡 `reviews/`) は、各巡の記録 README を通じて所見を引き、全文は読んでいない。
- `runs/agent_outputs.jsonl` (2 巡目 4 行、3 巡目 3 行) は sha256 と行数を再計算したが、各 event の `refs` が WAL の canonical ref と一致することは
  各巡の記録 (双射検査通過) に依存し、本稿は再計算していない。

**記録との差 (原本を採り、記録側は直さない):**

- **2 巡目記録の「Created 06:35:44」。** `4954.nqsv` の Created Request Time は job 内 qstat と NQSV 終了要約の両方で 06:36:06 である。
  本稿は 06:36:06 を採る。差は 22 秒で、順序 (Created → Started → Ended) と Elapse に影響しない。06:35:44 の出所は特定していない。
- **2 巡目記録の noise floor の説明「submit-tree に較正記録が無い」。** 材料レポートは較正 file 7 本を走査し、between-run の候補 3 file が条件不一致、
  within-run が登録済み pin の `self-inconsistent-calibration` で除外、と記録している (§2.6)。材料レポートの provenance は変えず、説明の粗さを差として書く。
- **critic-2 の「`campaign.lock` に自由文 `spec_content` は無い」。** 実物の `identity_preimage` (JSON 文字列) の中に 1 件ある (§2.4)。critic-2 の当時の
  判定は変えず、走査範囲の留保として書く。critic-3 は同じ自由文を見つけて判定している。
- 1 巡目 WAL の `build_start` が記録する `knowledge_provenance` と、1 巡目 proposal-1 の生成に使った `knowledge_input` の内容が同じ source を指すことは
  sha256 (`2163b794…`) で確認したが、role が受け取った prompt bytes は保存されていない (1 巡目は prompt 全文を保存していない。2 巡目以降は `*-prompt-*.md` がある)。

---

## 5. 一次資料

### 5.1 権威 bytes (repo 外) と SHA-256 — 本稿が 2026-09-20 に再計算した値

各巡の job root `/work/1/SFC/tanab/dev-wave-jobs/<wave>/submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/`。
これらは `guard_bash` / `guard_write` の防護対象で repo へ複製されていない。

| 巡 (wave) | file | sha256 | bytes |
|---|---|---|---|
| 1 (`dev-wave-t2588-k2-loop-roundtrip`) | `runs/wal.jsonl` (5 record) | `ac12b80fbc65a9b22f8dc9c1488efc0d5274d6e823f8fb313e4ca175a7584d9b` | 7,053 |
| 1 | `knowledge_manifest_receipt.json` | `c42dc712bbd11fc7e7a29921f7e760fa5a4e8c315a5ea62266c32f5ea97d4d2a` | 1,317 |
| 1 | `campaign.lock` | `48520c2b99c85182f422a1f8f278cbacb4a0365eac32b84f87278f89c81176fa` | 8,307 |
| 1 | `loop_state.json` | `e6b819f3c047d41300274c4021bdeacdb30e98396285c5a9383200b8e8fd4c33` | 256 |
| 1 | `s4_loop_digest.txt` | `1d834279bf63112fb56d41dde337953503a95830157d11a939c82553d89d64ed` | 1,893 |
| 2 (`dev-wave-t2746-k2-loop-round2`) | `runs/wal.jsonl` (5 record) | `03ac8508ba9a3d28b89f9a7b39046c76a49375e381a6c3b135949171c4f16d26` | 7,057 |
| 2 | `runs/agent_outputs.jsonl` (4 行) | `804c62c713e6785a1560725cb35690ffa044208ae94249d21deffdb41fa0a17b` | 34,017 |
| 2 | `knowledge_manifest_receipt.json` | `c42dc712…` (1 巡目と同一 bytes) | 1,317 |
| 2 | `campaign.lock` | `fc7acacabd871a180c2f1f4b86d0b2bb90ce5f682476b3a230862c495ed401de` | 8,307 |
| 2 | `loop_state.json` | `03ebaf94339c89849e969cb7547f31f6c241a81698f5195c090bc8351db716a7` | 255 |
| 2 | `s4_loop_digest.txt` | `a0a4c204f9d214bb52f87d1cdc0dcf9d19a307e36d6db0d9d3c5f13b517e6c9c` | 1,938 |
| 3 (`dev-wave-k2-loop-round3`) | `runs/wal.jsonl` (5 record) | `eb8927b78129a8700ceec9c30a13df1fa7287b1c5520f6cf19ae48b191aa4daa` | 7,057 |
| 3 | `runs/agent_outputs.jsonl` (3 行) | `66d3e737c1e4bb2e651805d97d40e047093f85273642464d24b23b797813efce` | 32,979 |
| 3 | `knowledge_manifest_receipt.json` | `c42dc712…` (同一 bytes) | 1,317 |
| 3 | `campaign.lock` | `f1ab4966ec7fb702c477ae022b0652f4478868191623e884c75cf989987f9ce4` | 8,307 |
| 3 | `loop_state.json` | `917ba3d3b34df45eff85aa536999dd30b895256fdefaef68214431ae88a1f950` | 255 |
| 3 | `s4_loop_digest.txt` | `f993251dc33cd9d25246778c8b6b8820f431d4d121030377af65f9046ebe3598` | 1,939 |

job root にはほかに、投入・取込みの記録 (`qsub-*.stdout`、`qstat-after-submit-*.txt`、`ingest-real.log`)、役割の prompt 全文 (2 巡目以降)、
3 巡目の親の glue script (`build_round3_inputs.py` 等、実装面ではない) がある。

### 5.2 repo 内 (tracked) の一次資料

| 巡 | path | 本稿が使った file |
|---|---|---|
| 1 | `output/insights/2026-09-16/t2588-k2-loop-roundtrip/` | `materials/proposal-1.json` (sha256 `590b6f27…`)、`proposal-2.json` (`3dbe30d7…`)、`planner-input-1.json`、`planner-input-2.json`、`knowledge-input.json` (`3080a98b…`)、`verbatim/critic-1.md` (`0ee26a8c…`)、`evidence/compute-result.json` / `job.stdout` / `job.stderr` / `reservation.json` |
| 2 | `output/insights/2026-09-18/t2746-k2-loop-round2/` | `materials/proposal-3.json` (`7277e526…`)、`planner-input-3.json`、`coder-input-3.json`、`critic-input-2.json`、`knowledge-input.json` (`05f2b267…`)、`verbatim/critic-2.md` (`d2b2ab77…`)、`layer3_report.json` (`f6dca3b9…`)、`evidence/attempt-0001/` と `attempt-0002/` の `compute-result.json` / `job.stderr` / `job.stdout` / `reservation.json` |
| 3 | `output/insights/2026-09-19/k2-loop-round3/` | `materials/diagnosis-4.json` (`7b742268…`)、`planner-context-4.json` (`280caa0f…`)、`planner-input-4.json`、`coder-input-4.json`、`critic-input-3.json`、`proposal-4.json` (`bd3e5fd2…`)、`run-summary.json`、`knowledge-input.json` (`05f2b267…`)、`verbatim/critic-3.md` (`5cd8f518…`)、`layer3_report.json` (`c37fda1f…`)、`evidence/attempt-0001/` の `compute-result.json` / `job.stderr` / `job.stdout` / `reservation.json` |
| 共通 | `output/insights/2026-09-10_cc-next-precheck/run-card.md` | 投入契約 1 (既知値の再提案の規定) |

各巡の `evidence/*/job.stdout` は行末空白の可逆最小正規化 (可視文字不変、原文 sha256 は各巡の記録に記載) を受けている。本稿が引いたのは
末尾の要約行 (`[eval …] verify[legacy]: …`、`bench: median …`、`停止判定: continue`) で、正規化の影響を受けない。

### 5.3 裁定

| 裁定 | 内容 (本稿に関わる部分) |
|---|---|
| D2044 項 9 (2026-09-16) | 1 巡目の認可。「新しい機構は足さず、既存経路だけで行う」 |
| D2120 項 1 (2026-09-17) | 2 巡目の認可 (択 A)。予算と停止条件。「2 巡目が閉じても合成による改善や探索の有効性の実証とはしない」 |
| D2148 項 2 (2026-09-18) | 2 巡目 attempt-0002 の今回限定の事後承認 |
| D2148 項 3 (2026-09-18) | 3 巡目の前に critic 診断を次生成へ渡す最小経路を先に整える (択 (b))。同機体・同 job 内の stock 対照を次の実走計画に含める |
| D2155 (2026-09-19) | `k2_critic_diagnosis` の設計 (exact 6 field、両 role へ同一診断、whiteboard 不変、実 consumer は親の inline 送付)。「実受領・採用・改善効果は別の実走で確認する」 |
| ユーザー決定 (2026-09-19、逐語は 3 巡目 `reviews/s1-brief.md`) | 3 巡目の予算「候補の生成 1 回・評価 1 本・同 job の stock 対照 1 本、再投入なし」 |
| [T-2795] (rulings-inbox `2026-09-19-k2-loop-round3-same-job-stock-control.md` 項 1) | 同 job stock 対照の未達の扱い。**2026-09-20 に確認した時点で結果欄は空 (裁定待ち)** |
| [T-2796] (同 項 2) | runbook T-2783 追補の login 制約の追記候補 (同日時点で未実施。本稿は追記を既成事実にしない) |

### 5.4 値の出所 (転記した数値ごと)

| 値 | 出所 |
|---|---|
| 3 巡の variant / genome / `ccbench_commit` / `knowledge_provenance` | 各巡 WAL `build_start` |
| 3 巡の trace / perf bin id、`trace_cached` / `perf_cached` | 各巡 WAL `build_done` |
| commits / aborts / anomalies / `commit_witness` / `proof_surfaces` | 各巡 WAL `verify_done` |
| `median_tps` / `tps` / `cv` / `bench_wall_s` / `settled` / `leading_indicators` / `perf_observation` | 各巡 WAL `bench_done` |
| `verifier_result_sha256` / `lock_identity_sha256` / `verify_configs` | 各巡 WAL `commit` |
| whiteboard の 1 件、`iteration`、`start_wall` | 各巡 `loop_state.json` |
| 停止判定 `continue`、`1 committed / 0 aborted / 0 skipped`、`outcome=certified` | 各巡 `job.stdout` 末尾、3 巡目 `run-summary.json` |
| job の Created / Started / Ended / Elapse、Request ID | 各巡 `job.stderr` 末尾の NQSV 要約 (4 job) |
| host | 各巡 `reservation.json` の `IZANAGI_RESERVATION_HOST` |
| planner の方向 / magnitude、coder の値 / 実装 / 分類 / `knowledge_use` / `data_boundary_report` | `proposal-1.json` 〜 `proposal-4.json` |
| role 入力の key、`current_perf` の値 | `planner-input-1/2/3/4.json`、`coder-input-3/4.json`、`critic-input-2/3.json` |
| 診断 6 field の文字数 | `diagnosis-4.json` |
| 知識源 3 記録の値 | `knowledge-input.json` の `sources[0].content_utf8` |
| critic の結論・recommend・avoid・規律 6 の判定 | `verbatim/critic-1.md` / `critic-2.md` / `critic-3.md` |
| 材料レポートの件数・`source_refs`・`certifying_input`・`noise_floor` | 2・3 巡目 `layer3_report.json` |
| 受領証の `verification` / `claim_boundary` / `declaration_status` | `knowledge_manifest_receipt.json` (repo 外、3 巡同一 bytes) |
| verify 走の abort 率 (15.02 % / 13.90 % / 18.94 %)、3 走の比 (+18.7 % 等)、1.67 pt | 本稿が上の値から計算 (性能主張には使わない) |
| 2 巡目 attempt-0001 の拒否文言 | `evidence/attempt-0001/job.stderr` 1 行目 |

### 5.5 同じ結果についての既存の稿 (本稿の出所ではない)

- 各巡の記録 (`output/insights/2026-09-16/t2588-k2-loop-roundtrip/README.md`、`2026-09-18/t2746-k2-loop-round2/README.md`、
  `2026-09-19/k2-loop-round3/README.md`) と worklog entry 1548 / 1652 / 1691。**数値・機械判定・入力内容**は記録の散文を出所にせず、同 dir の
  materials / verbatim / evidence と repo 外の権威 bytes から作り直した。**実行者の手続き** (射影の事故、投入前検査、代替照合、未取込みの理由など) は
  記録にしか無く、本文で「記録による」と付けて引いた (§4.3)。数値・判定について記録との食い違いは §4.3 の 3 点 (2 巡目の Created 時刻、
  noise floor の説明の粗さ、critic-2 の `spec_content` 不在報告) で、他の照合した値は一致した。
- 論文ストーリー版 `docs/paper-story/2026-09-19.md` §8 の B-6 と、`docs/paper-story/README.md` の stale 注記 (3 巡目)。**版・stale 注記は本稿の出所ではない**
  ([T-2611] / [T-2674] の型)。
- B-5 生成器対照の事前登録 (D2158) は K2 loop を 3 生成器の 1 つに置くが、較正済み動作点 (1M / 48 / 3 s / 5 reps) で本稿の配線 (100k / 4 / 1 s / 2 reps) とは別であり、
  本稿の 3 巡は B-5 の評価数に入らない。
