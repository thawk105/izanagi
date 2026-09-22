# K2 手動 loop 4 巡の結果節 — 4 巡目で初めて同じ job の stock 対照を伴って評価し (候補・stock とも certified)、critic-4 の診断と材料レポートまで閉じた (2026-09-16 / 09-18 / 09-19 / 09-22〜23。同 job の比は記述値、改善の実証ではない)

**これは投稿本文ではない。** 論文の結果節・表へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む。D2120 項 15)。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の「results 系列」節が正本である。
**3 巡の稿 `results/2026-09-20-k2-manual-loop-three-rounds.md` を改めるものではない。** 同稿は 3 巡の単位の稿として有効なまま残る。
本稿は 4 巡目 (生成・評価・還流) を主対象とし、巡 1〜3 は terminal record の表 (§2.1) だけを一次資料から再抽出した。巡 1〜3 の入力・提案・critic の詳細は 3 巡稿 §2.2 と同じ一次資料にある。

**本稿は性能の結果節ではなく、方法論 (合成ループの往復・診断の還流・同 job 対照) の実施例の結果節である。**
見送り台帳の項目 B-6 (リーク制御を完備した状態での実走) の材料であって、**B-6 の充足を判定しない。** K2 は論文の必須経路の外にある (D2211 項 1)。
**本稿の状態記述はすべて 2026-09-23 時点のものである。**

**成立範囲を最初に固定する。** 本稿が扱う保存成果物の範囲で成立したのは次のとおりで、それ以上ではない。

- 提案 (planner + coder) → 評価 → critic を **4 回** 実施した (2026-09-16 / 09-18 / 09-19 / 09-22〜23)。
- 評価の実測が次の提案の型付き入力へ戻る **実測の還流は 3 回** (巡 1 → 2、巡 2 → 3、巡 3 → 4)。巡 3 → 4 は、巡 3 の campaign 原本が消失した後に repo 内の派生物から組んだ入力である (D2194 項 2 の択 A)。
- critic の診断が次の提案の型付き入力 (`k2_critic_diagnosis`) へ届く **診断の還流は 2 回** (critic-2 → 巡 3、critic-3 → 巡 4)。
- **同じ job の stock 対照を伴う評価は巡 4 の 1 回だけ**である (巡 1〜3 には無い)。巡とは別に、同じ週に同 job pair の再投入 1 job (候補 10 の再評価 + stock) がある (§2.3)。
- 巡 4 の critic-4 と、planner-5 / coder-5 / critic-4 の出力の材料レポートへの取込みまでを行った。**critic-4 の診断を次の提案へ戻す実走 (巡 5) は無い。**

**限定を最初に置く。** 以下は本稿の全節に先立つ。

1. **同時刻の対照は巡 4 の中の候補 5 と stock の 1 対だけである。** その比 (2.493) は、この配線 (4 threads / 100,000 records / rr50 / skew 0.9 / rmw=false / extime 1 秒 / reps 2) の 1 点の記述値である。
   他の配線へ一般化しない。stock は `BACK_OFF=1` の適応 backoff (CCBench 既定) であって `BACK_OFF=0` (backoff 無し) ではない (記録ごとの「stock」の違いに注意)。
   **巡どうしの値 (20 / 25 / 10 / 5 の tps) は別日・別 node・別 submit-tree の非同時刻の点で、比較しない。** 候補 5 と候補 10 (pair 再投入) も別 job で、優劣を言わない。
2. **知識・診断の因果効果を主張しない。** coder-5 の値 5 は critic-3 の候補値と同じだが、それは助言として参照したという自己申告である。診断なし統制は無い。
3. **critic は 4 巡とも Bash を持つ legacy role で、B-4 (リーク制御の ablation) には非適格である。** 本稿は B-4 の材料ではない。
4. **規律 6 の検査結果は各 role の自己申告であり、機械的な強制でも共通 schema の検査結果でもない** (§2.4)。
5. **`certified` は正しさゲート (trace-enabled build の verifier が `serializable` / anomaly 0 を返した) の意味であって、性能の判定でも候補間の certified な選択でもない。** 規律 2 は 4 巡とも発火していない。
6. **巡 1・巡 3 の campaign 原本 bytes は 2026-09-20 に消失した (F1034)。** 巡 1 の値は job 出力の表示値、巡 3 の値は材料レポートが保持する WAL 内容から取った (§2.1、§4)。
   巡 4 の AO と材料レポートは、原本 campaign dir ではなく原本と byte 一致を確かめた写しの上で作った (§2.6)。
7. critic-4 の attribution (「固定 5 µs は適応 backoff より速い」「適応は待ちすぎ」) と、その中の「noise floor 3.0% を大きく超える」は **LLM の帰属記録であって本稿の判定ではない。**
   材料レポートの noise floor は本走の条件に合う記録が無い (`no-matching-env-record`)。

---

## 1. 条件 — 巡 4 の前に固定されていたもの (3 巡との差分)

評価経路の本体 (`p3_s4_loop.py` の段 4 loop、1 値の build → trace-enabled verify → trace-disabled bench)、編集面 (`include/backoff.hh` の
`double now_backoff = <整数 literal>;`、文法 v1、値域 1..1000)、固定 genome の value 以外の 4 flag、性能配線、正しさ検証 (legacy 1 条件)、
知識源 (manifest wal-only 1 件、resolver digest `396cd559…`、受領証 `c42dc712…` は 4 巡同一 bytes)、呼び手宣言 (`known_result_conditioned_derivative` /
`de_novo_claim=false`) は 3 巡と同じである (3 巡稿 §1.1〜§1.2 と同じ一次資料、巡 4 は WAL `build_start` / `bench_done` の `run_cmd` と受領証で確認)。

| 項目 | 巡 1〜3 | 巡 4 | 出所 |
|---|---|---|---|
| job の形 | 1 job = driver 1 起動 = 候補 1 本 | 1 job = driver 1 起動 (pair mode、D2205)。候補の後に同じ campaign・同じ WAL で stock を 1 本 (`IZANAGI_S4_STOCK_CONTROL=1`) | 巡 4 WAL の 10 record (2 variant × 5 stage)、`job.stdout` の `p3 S4 pair: candidate_rc=0 stock_rc=0` |
| campaign ID | `p3-s4-loop-s4-autonomous-409e13f8` (3 巡とも。別 tree・別 WAL) | `p3-s4-loop-s4-autonomous-b24749ae` (admission policy epoch `db6bc9ea…` の違い) | 各巡 WAL、T-2795 insight §4 (`materials/epoch-diff-r4.json`) |
| submit-tree HEAD | `d97c423bd` / `d2ebef7a4` / `a99425b66` | `8fd2a2f5c` (CCBench は `p3_s4_loop.PIN` `511c9538…` へ checkout、経路 H = D1777) | 各巡 insight、T-2795 insight §1 |
| stock | 無し | variant `602b4ce9c788` = `silo\|BACKOFF_FIXED=-1,BACK_OFF=1,…`。BUILD_START の `src_token` は `stock` | 巡 4 WAL `build_start` |
| 認可 | 3 巡稿 §1.3 | D2211 項 1 (pair 成立時だけ 4 巡目 1 job、新規生成 1 回 + 同 job stock、再投入なし、入力は D2194 項 2 の択 A)。D2172 項 3 | decisions |
| 停止規則 (結果の前に固定) | — | 候補 certified ∧ terminal commit、stock certified ∧ terminal commit ∧ `src_token == stock` ∧ variant = stock genome の id | T-2795 `reviews/s4-ruling.md` |
| critic 入力 | 巡 3 まで同型 (`build_critic_input_3.py`) | 同型 + `same_job_stock_variant` / `stock_genome` の 2 key。開示 14 項 | 巡 4 `materials/critic-input-4.json` |

---

## 2. 結果

### 2.1 4 巡通し — 評価の terminal record

| 巡 | 日付 (JST) | job / host | variant | value | verdict | commits / aborts / anomalies (trace build) | `median_tps` | 2 反復 `tps` | run 内 cv | `abort_rate` (perf build) | 停止判定 | 値の出所 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-09-16 | `1216.nqsv` / bnode058 | `8a84a7b00103` | 20 | serializable / certified | 469,618 / 83,034 / **0** | 719,324 (表示値) | — | 1.70% (表示値) | — | continue | `job.stdout` (WAL 原本は消失) |
| 2 | 2026-09-18 | `4954.nqsv` / bnode110 | `3dec27291054` | 25 | serializable / certified | 445,394 / 71,877 / **0** | 687,508.5 | 692,403 / 682,614 | 1.007% | 0.0740 | continue | `layer3_report.json` の events (WAL 内容) |
| 3 | 2026-09-19 | `10761.nqsv` / bnode020 | `002642c7ac96` | 10 | serializable / certified | 523,120 / 122,211 / **0** | 815,983.0 | 815,067 / 816,899 | 0.159% | 0.09065 | continue | 同上 |
| 4 候補 | 2026-09-22 | `16312.nqsv` / bnode052 | `fceb937ae6c5` | 5 | serializable / certified | 566,368 / 161,015 / **0** | 884,922.5 | 892,103 / 877,742 | 1.148% | 0.10105 | continue | 巡 4 WAL (原本と byte 一致の写し) |
| 4 stock | 同上 (同 job) | 同上 | `602b4ce9c788` | stock (-1) | serializable / certified | 281,132 / 8,715 / **0** | 354,948.0 | 358,000 / 351,896 | 1.216% | 0.01835 | — (`certified-stock`) | 同上 |

- `commits` / `aborts` / `anomalies` は trace-enabled build の verify 走、`median_tps` 以下は trace-disabled build の bench 走の値 (別 build・別 run、規律 1)。
  trace build と perf build の abort 率を並べて読まない。
- `abort_rate` の集約規則は巡 1 と巡 2 以降で違う (3 巡稿 §2.1)。巡 1 の `abort_rate` と 2 反復の値は、WAL 原本が消失し job 出力に無いので本稿は再抽出していない (3 巡稿 §5.1 が消失前に WAL の sha256 を記録している)。
- `llc_miss_rate` / `ipc` は 4 巡とも null (計算ノードの perf 前検査 `status=unavailable`、`reason=nonzero-rc`)。0 でも「差なし」でもない。
- `settled` は巡 2〜4 (巡 4 は候補・stock とも) true。
- **この表の巡どうしの行を比較しない** (限定 1)。同時刻の対照は巡 4 の 2 行だけである。

### 2.2 巡 4 の入力 → 提案 → 評価 → 還流

| 段 | 事実 | 出所 |
|---|---|---|
| 入力の組立て (択 A) | 巡 3 の repo 内派生物だけから production 関数で組んだ: 診断 = `critic-3.md` (sha256 `5cd8f518…`) → `k2_critic_diagnosis` exact 6 field、whiteboard = 巡 3 `run-summary.json` の `loop_state` (`iteration 1 / decrease / large / success / delta null`)、`current_perf` = 同 bench (815,983 tps / abort 9.065%)、knowledge-input は巡 3 と bytes 一致、leakproof_context は巡 3 `coder-input-4.json` の同 field。**pair 再投入の結果は入れていない。** 巡 3 の `loop_state.json` と AO の再構成物は sha 一致を確かめたが harness には渡していない | T-2795 `materials/planner-input-5.json` (`1693a12d…`)・`coder-input-5.json` (`5d88e798…`)・`diagnosis-5.json`、T-2795 insight §2.1 |
| planner-5 | `axis=silo-backoff-magnitude` / `direction=decrease` / `magnitude=large`。値も機序も出していない。uncertainty で「3 巡目までの評価点は別日・別 job の単発、同 job stock 対照が入るまでは帰属しない」「cache / IPC は欠測」を挙げた | T-2795 `verbatim/planner-5.json` (`cd4a2ea4…`) |
| coder-5 | **`value=5`**、`implementation="double now_backoff = 5;"`、`confidence=medium`、`classification=known_result_conditioned_derivative`、`knowledge_use` は source 0 のみ (別機体の傾向を方向の傍証としてだけ使ったと申告)、`instruction_like_content_detected=false`。justification は「10 の半減である 5」「k2_critic_diagnosis は助言としてのみ使」ったと書く。応答は JSON の前に 118 字の要約を付けていた (契約は JSON だけ、JSON は機械的に取り出した) | T-2795 `verbatim/coder-5.json` (`1f86dc6b…`)、`verbatim/coder-5-response.md` |
| 開示の差 | coder-5 の入力の診断本文は評価済みの 20 / 25 / 10 とその tps・候補 5 を含む (D2155 の設計どおり)。「既知値を見ずに合成した」とは書かない | T-2795 `materials/coder-input-5.json` |
| 判定と検査 | 5 は既知値 (10 / 20 / 25 / 30 / 40) の外。login の production 検査 3 本 (`assert_closed_proposal_schema` / `validate_backoff_preflight` / `load_proposal_file`) を通したことは**記録による**。`prior_critic_reverse=false` (proposal-5 の bool、親の解釈) | T-2795 insight §2.2、`materials/proposal-5.json` (`146d2f85…`) |
| 評価 | §2.1 の巡 4 の 2 行。job `16312.nqsv`: Created 11:16:18 → Started 11:16:25 → Ended 11:18:07 JST、Elapse 107 秒。WAL ts: 候補 build_start 11:17:02 → commit 11:17:35、stock build_start 11:17:41 → commit 11:18:07。停止規則の 4 条件は成立 | 巡 4 WAL、T-2795 `evidence/attempt-r4-0001/job.stderr` の NQSV 要約 |
| critic-4 | 1 回。§2.5 | 本稿 §2.5 |
| 材料レポート | AO 3 件 (planner-5 / coder-5 / critic-4) と材料レポート。§2.6 | 本稿 §2.6 |
| 閉じていないもの | critic-4 の診断を次の提案へ戻す実走は無い。critic-4 の推奨 (同じ job で複数候補、次の値 2〜3 µs、待機 0 の対照、perf の修復) は採用も起票もしていない | T-2860 insight §5 |

### 2.3 同じ job の stock 対照 — 巡 4 と pair 再投入

| job | 位置づけ | 候補 | 候補 `median_tps` | stock `median_tps` | 候補 / stock | perf abort 率 (候補 / stock) | trace abort 率 (候補 / stock) | 出所 |
|---|---|---|---|---|---|---|---|---|
| `16269.nqsv` (bnode001、2026-09-22 09:24:41〜09:26:16、Elapse 100 秒) | 巡ではない。D2211 項 1 の pair 再投入 (候補 = 巡 3 の proposal-4 の再評価) | 10 (`002642c7ac96`) | 825,490 | 348,883 | 2.366 | 9.01% / 1.815% | 18.88% / 3.11% | pair の WAL (byte 複製 `originals-copy-20260922/pair/`、`materials/run-summary-pair.json`) |
| `16312.nqsv` (bnode052) | 巡 4 | 5 (`fceb937ae6c5`) | 884,922.5 | 354,948 | 2.493 | 10.105% / 1.835% | 22.14% / 3.01% | 巡 4 WAL (`materials/run-summary-r4.json`) |

- 両 job とも候補・stock とも `serializable` / certified / anomaly 0、stock の `src_token` は `stock`、stock の variant は stock genome の id と一致した。
- 比 (候補 / stock) は同じ job の中の 2 点の記述値である。2 job の stock どうしにも +1.74% の差がある (別 job・別 node で同じ stock を 2 回測った 1 対)。
  **候補 5 と候補 10 の差 (+7.20%) と比の差 (2.366 → 2.493) は job・node の差と分離できず、設定の効果に帰属しない。** 候補間比較の不確かさの大きさは推定していない。
- 両 job とも、stock の abort 率は候補より低く、throughput も低い (perf build)。これは測定の記述であり、適応 backoff の機序の帰属ではない。

### 2.4 規律 6 の検査結果 — 巡 4 の role 出力から

| role | 形式 | 結果 | 出所 |
|---|---|---|---|
| planner-5 | `uncertainty` の散文 | uncertainty (6)「規律6の検査」で、診断と knowledge_input に権限・検証順序・正しさゲートを上書きする指示は見当たらないと申告し、診断中の R0 / R3 を運用側への要望と判断した | `verbatim/planner-5.json` |
| coder-5 | 構造化 field `data_boundary_report.instruction_like_content_detected` | `false`。走査範囲 (knowledge_input の WAL 15 行、診断 4 節) を details に書いた | `verbatim/coder-5.json` |
| critic-4 | 追加節 `## 異常の報告 (規律 6)` の散文 | digest と WAL に指示めいた文字列なし (grep の hit は perf event 名 `instructions` の 1 語)。digest の「フラグ軸の限界効果」節の表示上の限界を注入ではないと明記 | `verbatim/critic-4.md` |

形式は role ごとに違い、機械的な強制ではない (限定 4)。

### 2.5 critic-4 (1 回、登録 role `critic`、Bash を持つ legacy role)

- 入力 `critic-input-4.json` (6,436 B、sha256 `a271116e…`)、prompt 全文 `critic-prompt-4.md` (7,083 B、`2a766305…`)。出力 `critic-4.md` (11,115 B、`bb9e3277…`) は子の手渡しの本文を transcript から bytes のまま取り出した。
- **読んだもの:** 写しの digest (sha256 を再計算し入力と一致)・WAL 全 10 行・`loop_state.json`、repo の既存 insight 2 本 (pair 再投入の記録と `2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md`)。
  **受領証と `campaign.lock` は名前を列挙しただけで本文を読んでいない** (critic-3 は 5 種すべてを読んだと記録されている)。書込みは無い (Bash 8 本とも読取り)。
- **attribution:** 動いた設計選択は `BACKOFF_FIXED` の 1 軸 (-1 → 5)。同 job の対で throughput 2.493 倍、perf build の abort_rate は 1.835% → 10.105% と逆向き。
  仮説「適応 backoff は待ちすぎ、この配線では abort して再試行する方が安い」— 待ち時間は測っておらず推定。llc / ipc 欠測で帰属不能。5 と 10 の優劣と診断の効果は言えない。
- **recommend:** R1 = 同じ job で「5 / 次の候補 / stock」を並べる構成、R2 = decrease / small (2〜3 µs)、R3 = `BACKOFF_FIXED=0` の対照、R4 = perf カウンタの修復。
- **avoid:** この配線で適応 backoff を候補として再訪する、abort_rate の低さを目標にする、別 job の差を候補の優劣として渡す、「診断が改善をもたらした」という因果主張。
- **uncertainty:** 機序の独立指標の欠測、標本 2 反復、配線は kickoff、noise floor の適用範囲、build 間の abort 比の違い、verify は legacy 1 構成。
- 本稿の注記: critic-4 の「noise floor 3.0%」は critic が持ち込んだ値で、材料レポートの noise floor は `no-matching-env-record` (限定 7)。「適応は待ちすぎ」「wrapper の失敗原因」は推測である。

### 2.6 材料レポート (機序仮説層 v3、巡 2・3・4)

| 巡 | AO | `mechanism_hypotheses` | `source_refs` | noise floor | 出所 |
|---|---|---|---|---|---|
| 2 | 4 event (planner-2 / critic-2 / planner-3 / coder-3、coder-2 は無い) | 3 巡稿 §2.6 | 3 巡稿 §2.6 | 3 巡稿 §2.6 | 巡 2 `layer3_report.json` |
| 3 | 3 event (planner-4 / coder-4 / critic-3) | 1 件 (variant `002642c7ac96`) | 9 = wal 5 + wb 1 + ao 3 | between / within とも `no-matching-env-record` | 巡 3 `layer3_report.json` (sha256 `c37fda1f…`) |
| 4 | 3 event (planner-5 `ao:09e6ec18…` / coder-5 `ao:71496b75…` / critic-4 `ao:c19fbc7a…`) | 1 件 (variant `fceb937ae6c5`、attribution = critic-4 の `## attribution` 節、refs 10、digest `8d564034…`) | 14 = wal 10 + wb 1 + ao 3 (双射検査を通過) | between / within とも `no-matching-env-record` (契約 pin `validated`) | 巡 4 `layer3_report.json` (sha256 `fdbaa579…`、65,158 B) |

- 巡 4 のレポートは `schema_version` v3、admission `admitted` / `admitted-new-schema`、`certifying_input=false`、`knowledge_level=K2`、variants 2 (候補と stock)、rejects 0。**材料であって certifying 入力ではない。**
- **巡 4 の取込み先は原本ではない。** 取込み口は campaign dir に `runs/agent_outputs.jsonl` を新設するので、依頼 (原本は動かさない) に従い、lock 済み原本と byte 一致 (6 file の sha256) を確かめた job root の写しへ取り込んだ。
  AO 3 行 (32,549 B、sha256 `0dbd185a…`) は写しにあり、原本の `runs/` は `wal.jsonl` だけである。巡 3 は原本 campaign dir へ直接取り込んでいた。
- `mechanism_hypotheses` は LLM (critic) の帰属記録であって機序の実証ではない。AO の `input_sha256` / `ts` は記録であって、role が入力を実際に受け取った証明ではない。

### 2.7 時系列 (巡 4、JST)

| 時刻 | 事象 | 出所 |
|---|---|---|
| 2026-09-22 09:18:06〜09:26:16 | pair 再投入 `16269.nqsv` (巡ではない) | T-2795 `evidence/attempt-pair-0001/job.stderr` |
| 同日 (時刻は記録による) | planner-5 / coder-5 を各 1 回 (各約 37 秒、T-2795 の記録) | T-2795 insight |
| 11:16:18 → 11:16:25 → 11:18:07 | 巡 4 `16312.nqsv` の Created → Started → Ended (Elapse 107 秒) | T-2795 `evidence/attempt-r4-0001/job.stderr` |
| 11:17:02 → 11:17:35 / 11:17:41 → 11:18:07 | 候補 build_start → commit / stock build_start → commit | 巡 4 WAL ts |
| 2026-09-23 07:47:56 | 取込み用の写しを作成し原本と照合 | T-2860 `logs/setup-ao-root.log` |
| 07:5x (起動時刻は保存されていない) | critic-4 を 1 回 (約 206 秒) | T-2860 insight §2 |
| 07:57:32〜07:57:35 | AO 3 件の取込み (各 rc=0) | T-2860 `logs/ingest-real.log` |
| 07:58:20 | 材料レポート (2 回目、rc=0) | T-2860 `logs/layer3-r4.log` |

---

## 3. 限定 — この結果が言わないこと

1. **性能の改善・最良点・一般化。** 巡 4 の比 2.493 はこの配線 1 点の記述値で、固定 backoff が適応 backoff より良いという一般命題ではない。巡どうし・job どうしの差は比較しない。
2. **候補 5 が候補 10 より良い** (別 job)。**critic 診断が効いた** (統制なし)。**知識が効いた** (統制なし)。
3. **B-6 の充足・リーク制御の完備。** critic は legacy role で B-4 に非適格。遮断の完備は主張しない。K2 を論文の必須経路へ戻さない (D2211 項 1)。
4. **critic-4 の機序仮説の実証。** 待ち時間・llc・ipc は測っていない。
5. **巡 4 の critic が依頼どおりの 5 種を読んだこと。** 受領証と lock の本文は未読である (§2.5)。
6. **起動・送付の独立確認。** 保存 prompt は送達の証拠ではない (送った bytes と file の一致は機械照合していない)。

## 4. 欠落 — 権威 bytes・WAL・裁定の対応が確かめられない箇所

- **巡 1・巡 3 の WAL 原本は消失** (F1034)。巡 1 は job 出力の表示値 (丸め・CV) だけを本稿は再抽出した。巡 3 は材料レポートの events (canonical ref 5/5 一致、bytes は不一致) による。巡 2 は材料レポートの events による。
- **巡 4 の取込みは写しの上で行った。** 写しと原本の同一性は取込み前 (6 file) と取込み前後 (保護 5 file) の sha256 一致であり、`reports/p3_s4_loop_provenance.json` は取込み前にだけ照合した。
- **巡 4 の planner-5 / coder-5 の起動時刻と、送った prompt の bytes** は保存成果物に無い (記録による)。critic-4 の起動時刻も保存されていない。
- 巡 4 の入力組立ての正しさ (完全入力の組立て、critic-3 が読んだ対象全体の再監査、実送付) は sha 一致では証明されない (D2194 項 2 の限定)。

## 5. 一次資料

### 5.1 権威 bytes (repo 外) と SHA-256

| 対象 | path | SHA-256 |
|---|---|---|
| 巡 4 WAL | 原本 `dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/submit-tree-r4/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/runs/wal.jsonl` (14,885 B、写しと byte 複製も同一) | `6444159d2710a99aada7ee7cf079e0f4289e331ffe1fe8f2bf14aa1ef25f631d` |
| 巡 4 `campaign.lock` | 同 dir (12,003 B) | `4a709002aa7e671529d729b4ad1bb9d10b2eae060168a4dab4ff67dc8a794274` |
| 巡 4 `loop_state.json` | 同 dir (255 B) | `2a648649221c4adbf89a25cee7869431947d6940d7020450ee94ee9b8b068184` |
| 巡 4 digest | 同 dir `s4_loop_digest.txt` (2,103 B) | `8d5640349425fe32abe63c2e2c9d86263891d3472c98b8ca144dec8cea9a1a07` |
| 受領証 | 同 dir `knowledge_manifest_receipt.json` (1,317 B、4 巡同一) | `c42dc712bbd11fc7e7a29921f7e760fa5a4e8c315a5ea62266c32f5ea97d4d2a` |
| 巡 4 AO | 写し `dev-wave-jobs/dev-wave-t2860-k2-round4-reflux/ao-root/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/runs/agent_outputs.jsonl` (3 行、32,549 B) | `0dbd185ae697c99b9c6f3dff23a07653456bef203a900de28a61b42e67958628` |
| pair 再投入 WAL | byte 複製 `dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/originals-copy-20260922/pair/campaign/runs/wal.jsonl` (14,897 B) | `5415d01a3c746f0cad7e81ee966d7cb552215097cbe68de9cadd7f9f5e4e4367` |
| 巡 1〜3 | 3 巡稿 §5.1 (消失前の 2026-09-20 に再計算) | — |

### 5.2 repo 内 (tracked) の一次資料

- 巡 4 の還流: `output/insights/2026-09-23/t2860-k2-round4-reflux/` (`verbatim/critic-4.md`、`materials/critic-input-4.json`・`critic-prompt-4.md`・`run-summary-r4.json`・`wal-refs-r4.json`・`run-summary-pair.json`・`wal-refs-pair.json`、`layer3_report.json`、`logs/`)
- 巡 4 の生成と評価・pair 再投入: `output/insights/2026-09-22/t2795-k2-pair-resubmit/` (`verbatim/planner-5.json`・`coder-5.json`・`coder-5-response.md`、`materials/`、`evidence/attempt-{pair,r4}-0001/`)
- 巡 1〜3: `output/insights/2026-09-16/t2588-k2-loop-roundtrip/evidence/job.stdout`、`output/insights/2026-09-18/t2746-k2-loop-round2/layer3_report.json`、`output/insights/2026-09-19/k2-loop-round3/layer3_report.json`、各巡 `reservation.json`

### 5.3 裁定

D2211 項 1、D2194 項 2、D2205、D2187、D2172 項 3、D2155、D2120 項 15。F1034 (原本消失)、F1041 (T-2795 の投入前確認の省略)。

### 5.4 値の出所

| 値 | 出所 |
|---|---|
| 巡 4 の verdict・commits / aborts / anomalies・`median_tps` / `tps` / cv / `abort_rate`・genome・`src_token`・WAL ts | 巡 4 WAL (写し、`materials/run-summary-r4.json` は `project_round4_results.py` の射影) |
| pair 再投入の同上 | pair の WAL (byte 複製、`materials/run-summary-pair.json`) |
| 巡 2・3 の同上 | 各巡 `layer3_report.json` の `variants[].events` |
| 巡 1 の verdict・commits / aborts / anomalies・`median_tps` (表示値)・CV (表示値)・停止判定 | 巡 1 `evidence/job.stdout` |
| job の Created / Started / Ended / Elapse、host | 各 `job.stderr` 末尾の NQSV 要約、各 `reservation.json` |
| planner-5 / coder-5 の方向・値・分類・規律 6 | T-2795 `verbatim/planner-5.json`・`coder-5.json` |
| critic-4 の診断 | `verbatim/critic-4.md` |
| 材料レポートの件数・refs・noise floor | 巡 4 `layer3_report.json` |
| 比 2.366 / 2.493、+7.20%、+1.74% | 本稿が上の値から計算 (性能主張には使わない) |

### 5.5 同じ結果についての既存の稿 (本稿の出所ではない)

- 3 巡稿 `results/2026-09-20-k2-manual-loop-three-rounds.md` (巡 1〜3 の詳細の稿)。
- 記録 insight (T-2795 README、T-2860 README) と worklog entry 1823。手続き (投入前検査、送付) は記録にしか無く「記録による」と付けた。
- 論文ストーリー版 `docs/paper-story/2026-09-22.md` §8 の B-6 と README の stale 注記。**版・stale 注記は本稿の出所ではない。**
