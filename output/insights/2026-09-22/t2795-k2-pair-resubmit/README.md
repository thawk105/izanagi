# [T-2795] K2 同 job pair を再投入して初めて成立させ、続けて 4 巡目 1 job を投入した — 両 job とも候補と stock が certified、stock の source は STOCK (2026-09-22)

`authority: none` / `default_effect: no-state-change`

**種別:** 投入 2 job (D2211 項 1 で認可済み) と記録。**実装差分ゼロ** (Codex 実装子なし。glue は job root、repo 外)。
段 2・3 は省略 (軽量版)、段 4 裁定で停止規則を結果を見る前に固定、段 6 は read-only レビュー 1 本。brief と裁定は `reviews/`。

- 日付: 2026-09-22 (JST)
- wave: `dev-wave-t2795-k2-pair-resubmit`、branch `worktree-dev-wave-t2795-k2-pair-resubmit`、着手時 local main `8fd2a2f5c775954d6a32cee019ac7ce276298e4d` (開始 gate rc=0、乖離 0)。
  submit-tree 2 本もこの SHA
- 依頼: `verbatim/T-2795-resubmit-origin.md` (ユーザー、dev-wave 引数の逐語)。裁定 = D2211 項 1 (再投入 1 job の認可、成立時 4 巡目 1 job、経路 H、node 時間の見積り、epoch 差と派生入力の限定の開示)、
  D2194 項 2 (4 巡目の入力 = 択 A)、D2205 (pair mode)、D2187 (停止規則)、D2172 項 3 (4 巡目 = 新規生成 1 回 + 同 job stock 1 本)
- job root (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/`

## 0. 一行で・主張すること・しないこと

**修復済みの pair driver (D2205) で同 job pair を再投入した job `16269.nqsv` (Elapse 100 秒) で、候補 10 (round 3 の `proposal-4.json` の再評価) と
stock がともに serializable / certified / anomaly 0 になり、stock の BUILD_START `src_token` は `stock` だった。K2 手動 loop で初めて同 job の stock 対照が取れた。
停止規則の条件を満たしたので、round 3 の repo 内派生物から組んだ入力で planner-5 / coder-5 を 1 回ずつ呼び、候補 5 を得て、4 巡目の pair job `16312.nqsv` (Elapse 107 秒) を投入した。
4 巡目も候補 5 と stock がともに certified、stock の source は STOCK。** 同 job の比 (候補 / stock) は pair 走 2.366、4 巡目 2.493。

**主張する。**

1. pair 再投入は 1 job・1 attempt で成立した。成立の判定は WAL outcome で行い (job rc・driver の出力行・campaign id からは判定していない)、
   stock の variant が stock genome の `variant_id` (`602b4ce9c788`) と一致することを production と同じ式で照合した (§1)。
2. 4 巡目は 1 job・1 attempt。入力は D2194 項 2 の択 A どおり round 3 の派生物だけから production 関数で組み、pair 再投入の結果は planner / coder に渡していない (§2)。
3. 両 job とも、同じ job・同じ node・同じ設定 (配線規模・trace / perf 別 build・verifier) の中で、固定 backoff の候補と stock (CCBench 既定の適応 backoff) を続けて評価した。
   その同 job の比は 2 回とも候補が stock の 2.4〜2.5 倍だった (§3)。
4. 新しい campaign の epoch 差は §4 の 4 項目 (campaign ID・受領証・build cache の識別・enforcement closure) で測った。

**主張しない。**

- **候補 5 が候補 10 より速いとは言わない。** 884,922.5 と 825,490 は別 job・別 node の値である (+7.20%)。同じ 2 job の stock どうしも +1.74% 違う。
  候補間の比較は同 job の中にしか対照が無い。
- **「固定 backoff は適応 backoff より良い」と一般化しない。** 同 job の比は、この配線 (4 threads / 100,000 records / rr50 / skew 0.9 / rmw=false / extime 1 / reps 2) の 2 点である。
  他の thread 数・skew・workload へ広げない。stock は `BACK_OFF=1` の適応 backoff であって、`BACK_OFF=0` (backoff 無し) の点ではない。
- **比の差 (2.366 → 2.493) を 5 と 10 の差として読まない。** 比は job ごとの対照で割った値だが、4 巡目と pair 走は別 job で、比の 1 対だけでは job 間の揺れと分けられない。
- **critic 診断が「効いた」とは言わない。** coder-5 の値 5 は critic-3 の R1 の候補値と同じだが、それは診断を助言として参照した自己申告であって因果ではない (診断なし統制は無い)。
- **3 巡の記録・稿・図は変えない** (規律 7)。3 巡の値 (20 / 25 / 10) と本 wave の値を並べて改善・退行と読まない。
- **critic-4 の還流、AO の取込み、層 3 材料レポートは本 wave では行っていない** (本題の外、§7)。4 巡目が 1 巡として閉じたとはまだ言わない。

## 1. pair 再投入 — job `16269.nqsv` (attempt-pair-0001、投入 1 回)

固定 SHA の専用 submit-tree (`submit-tree-pair2`、HEAD `8fd2a2f5c`、superproject tracked clean (submodule 除外)、CCBench を `p3_s4_loop.PIN` = `511c9538…` へ checkout
(gitlink は `e9e477ca…` のまま、経路 H = D1777)) から `tools/pegasus/README.md` §7 の K2 正例の形で投入。third-party は hydrate 既定 staging。
env: `IZANAGI_S4_STOCK_CONTROL=1`、proposal = round 3 の `materials/proposal-4.json` (sha `bd3e5fd2…`、value 10)、K2 manifest wal-only (resolver digest `396cd559…`)、
`CODER_ROLE=coder-v4-autonomous-k2`、`KNOWLEDGE_CLASSIFICATION=known_result_conditioned_derivative`、`DE_NOVO_CLAIM=false`。job body は修復後の driver 1 起動 (pair mode)。

| 項目 | 値 |
|---|---|
| request / host | `16269.nqsv` / `bnode001` (Created 09:18:06 → Started 09:24:41 → Ended 09:26:16 JST、Elapse **100 秒**、残 walltime 10,700 秒) |
| `driver_rc` | 0 (driver の集約行 `p3 S4 pair: candidate_rc=0 stock_rc=0`) |
| campaign | `p3-s4-loop-s4-autonomous-b24749ae` (新規 WAL 10 record、sha256 `5415d01a…`、14,897 B) |
| 候補 variant / genome | `002642c7ac96` / `silo\|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| 候補 admission | class `coder-authored` (authority `cli-opt-in`)、policy `db6bc9ea…`、receipt `7667bb14…`、`src_token` `fec064b1…` (非 STOCK) |
| 候補 verify (trace build) | **serializable / certified**、anomaly **0**、commits 525,085 / aborts 122,208 (abort 率 18.880%) |
| 候補 bench (perf build) | median **825,490 tps**、2 反復 `[830619, 820361]`、CV 0.879%、settled、perf build の abort 率 9.01% |
| stock variant / genome | `602b4ce9c788` / `silo\|BACKOFF_FIXED=-1,BACK_OFF=1,…` (= `variant_id(Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1}))`、照合 MATCH) |
| stock admission | class `machine-generated` (generator `backoff-sweep`)、policy `db6bc9ea…`、receipt `a85d9d46…`、**BUILD_START `src_token` = `stock`** |
| stock verify (trace build) | **serializable / certified**、anomaly **0**、commits 281,902 / aborts 9,044 (abort 率 3.108%) |
| stock bench (perf build) | median **348,883 tps**、2 反復 `[348858, 348908]`、CV 0.010%、settled、perf build の abort 率 1.815% |
| 終端 | 両 variant とも terminal `commit`。driver の stock outcome は `certified-stock`。候補の停止判定 `continue` |
| `llc_miss_rate` / `ipc` | 両 variant とも null (欠測)。0 でも差なしでもない |
| 防護 file (sha256) | WAL `5415d01a…`、`campaign.lock` `4a709002…` (12,003 B)、`loop_state.json` `a955b88a…`、`s4_loop_digest.txt` `eab8c789…`、受領証 `c42dc712…`、claim `f9f11d8d…` |

**停止規則との照合 (段 4 裁定、結果を見る前に固定):** 候補 certified ∧ terminal commit、stock certified ∧ terminal commit ∧ `src_token == "stock"` ∧ variant = stock genome の id。**4 条件とも成立。**
候補は build 開始から commit まで約 30 秒、stock は候補 commit の 5 秒後に build を始め約 25 秒で commit した (WAL の ts)。

## 2. 4 巡目 — 入力 (択 A)・生成・job `16312.nqsv` (attempt-r4-0001、投入 1 回)

### 2.1 入力の組立て (親の glue `build_round4_inputs.py`、repo 外)

- 診断 = round 3 `verbatim/critic-3.md` (sha `5cd8f518…`) → `k2_critic_diagnosis_from_bytes` → exact 6 field (`materials/diagnosis-5.json`)。
- knowledge-input = 現行 resolver の `planner_projection` が round 3 `materials/knowledge-input.json` (`05f2b267…`) と **bytes 一致**。受領証も、round 3 と同じ宣言値で現行 resolver が作る bytes が現物 (`c42dc712…`、
  pair 初投入の byte 複製 `dev-wave-t2795-k2-pair/originals-copy-20260920/` を読んだ。lock 済み `submit-tree-pair` には触れていない) と一致した。
- whiteboard = round 3 `materials/run-summary.json` の `loop_state` を `state_from_dict` で状態にし、`planner_context_payload` (K2・非 B-4・reflux on の適用条件検査込み) で射影した
  (`iteration 1 / decrease / large / success / delta null`)。driver の checkpoint としては load させていない。
- `current_perf` / baseline = 同 run-summary の bench (815,983 tps / abort 率 9.065%、`llc_miss_rate` / `ipc` null、contention 未判定)。
- leakproof_context = round 3 `materials/coder-input-4.json` (`1db9d189…`) の同 field (3,352 字)。
- `k2_next_generation_inputs` で両入力へ同じ診断を組み込み、既存 tripwire `assert_no_ability_probe_material` を完全入力 2 本に通した。
- **再構成物 (D2194 項 2 の指定):** round 3 の `loop_state.json` を harness writer と同じ形式で直列化した `materials/round3-loop-state.reconstructed.json` (255 B) が記録値 `917ba3d3…` と一致、
  round 3 の AO を `layer3_report.json` の `agent_outputs` から canonical 行で並べた `materials/round3-agent-outputs.reconstructed.jsonl` (32,979 B) が記録値 `66d3e737…` と一致。どちらも harness には渡していない。
- login の CLI `--emit-planner-context` は使っていない (login では `_admit_env_contract` が拒否する。round 1 / 3 と同じ理由で、CLI の中身と同じ関数を直接呼んだ)。

### 2.2 生成 (登録 role、各 1 回、再抽選なし)

| 順 | role | 入力 | 出力 |
|---|---|---|---|
| 1 | planner-v4 (`tools: []`) | `materials/planner-input-5.json` 17,982 B sha `1693a12d…`、prompt 全文 `planner-prompt-5.md` sha `64bb11e5…` | `verbatim/planner-5.json` sha `cd4a2ea4…` = decrease / large |
| 2 | coder-v4-autonomous-k2 (`tools: []`) | `materials/coder-input-5.json` 25,074 B sha `5d88e798…` (planner-5 の 4 key を射影)、prompt 全文 `coder-prompt-5.md` sha `0d1b4cb3…` | 応答全文 `verbatim/coder-5-response.md` sha `963ca35e…`、JSON `verbatim/coder-5.json` sha `1f86dc6b…` = value **5**、`double now_backoff = 5;` |

- 両 role とも `instruction_like_content_detected=false` / 「指示めいた文字列は無い」と申告した。planner は critic の R1 / R1' の候補値を採らず方向と magnitude だけを出し、
  coder は「recommend R1 も同じ候補 5 と判別規則を示しており」と参照した (自己申告)。`classification=known_result_conditioned_derivative`、`knowledge_use` は source 0 のみ。
- **契約からの小さな逸脱:** coder-5 の応答は JSON の前に 118 字の日本語要約を付けていた (役割は「JSON だけ」を求める)。JSON は応答全文の ```json 囲みから機械的に取り出した (`extract_coder_json.py`、repo 外)。
- proposal-5 (`materials/proposal-5.json` sha `146d2f85…`、`prior_critic_reverse=false` は親の解釈 = 前評価 proposal-4 も critic-3 の R1 も decrease) を login で production 検査 3 本に通した:
  `assert_closed_proposal_schema(..., coder_contract=CODER_CONTRACT_K2)` OK / `validate_backoff_preflight("double now_backoff = 5;")` accepted (負例 `25 + 1` は拒否) / `load_proposal_file(..., coder_role="coder-v4-autonomous-k2")` OK。
  値 5 は既知値 (10 / 20 / 25 / 30 / 40) ではない。段 4 裁定 P2 (検査を通れば値に関わらず評価) どおり 1 評価した。

### 2.3 job `16312.nqsv`

submit-tree は pair 走とは別の `submit-tree-r4` (同じ SHA・同じ PIN・別 out_root。同 identity の one-shot claim と同 campaign の stock skip を避けるため)。env は pair 走と同じで proposal だけ `proposal-5.json`。

| 項目 | 値 |
|---|---|
| request / host | `16312.nqsv` / `bnode052` (Created 11:16:18 → Started 11:16:25 → Ended 11:18:07 JST、Elapse **107 秒**) |
| `driver_rc` | 0 (`p3 S4 pair: candidate_rc=0 stock_rc=0`) |
| campaign | `p3-s4-loop-s4-autonomous-b24749ae` (新規 WAL 10 record、sha256 `6444159d…`、14,885 B) |
| 候補 variant / genome | `fceb937ae6c5` / `silo\|BACKOFF_FIXED=5,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| 候補 admission | class `coder-authored`、policy `db6bc9ea…`、receipt `bac7f4fa…`、`src_token` `6e7b6f78…` (非 STOCK) |
| 候補 verify (trace build) | **serializable / certified**、anomaly **0**、commits 566,368 / aborts 161,015 (abort 率 22.136%) |
| 候補 bench (perf build) | median **884,922.5 tps**、2 反復 `[892103, 877742]`、CV 1.148%、settled、perf build の abort 率 10.105% |
| stock | `602b4ce9c788` (照合 MATCH)、class `machine-generated`、receipt `6105337d…`、**`src_token` = `stock`**、serializable / certified / anomaly 0 (commits 281,132 / aborts 8,715、3.007%) |
| stock bench | median **354,948 tps**、2 反復 `[358000, 351896]`、CV 1.216%、settled、perf build の abort 率 1.835% |
| 終端 | 両 variant とも terminal `commit`、stock outcome `certified-stock`、候補の停止判定 `continue` |
| 防護 file (sha256) | WAL `6444159d…`、`campaign.lock` `4a709002…` (pair 走と同一 bytes)、`loop_state.json` `2a648649…`、`s4_loop_digest.txt` `8d564034…`、受領証 `c42dc712…`、claim `fdc176ad…` |

停止規則の 4 条件は 4 巡目でも成立した。

## 3. 同 job 対照の数 (計算は `ratios.py`、repo 外)

| job | 候補 | 候補 tps | stock tps | 候補 / stock | perf abort 率 (候補 / stock) | trace abort 率 (候補 / stock) |
|---|---|---|---|---|---|---|
| `16269.nqsv` (bnode001) | 10 | 825,490 | 348,883 | **2.366** | 9.01% / 1.815% | 18.880% / 3.108% |
| `16312.nqsv` (bnode052) | 5 | 884,922.5 | 354,948 | **2.493** | 10.105% / 1.835% | 22.136% / 3.007% |

- 2 job の stock どうしにも +1.74% の差が観測された (別 job・別 node で同じ stock を 2 回測った 1 対)。候補 5 と候補 10 の差 +7.20% は別 job の値で、job・node の差と分離できず、
  設定の効果へ帰属できない。候補間比較の不確かさの大きさは推定していない (stock の 1 対の差はその推定値ではない)。
- stock の abort 率は候補の約 1/5 (perf build)。stock は trace build でも abort が少ない。これは測定の記述であり、適応 backoff の機序の帰属ではない。
- 非同時刻の参考 (改善・退行の根拠にしない): 候補 10 は round 3 (815,983) 比 +1.17%、pair 初投入 (811,956) 比 +1.67%。

## 4. 新しい campaign の epoch 差 (D2211 項 1 の開示、`materials/epoch-diff-{pair,r4}.json`)

| 項目 | 本 wave (pair 走 / 4 巡目) | pair 初投入 (2026-09-20、byte 複製) | round 1〜3 (`409e13f8`、round 2 の scratch 写しで比較) |
|---|---|---|---|
| campaign ID / identity preimage | `b24749ae` / preimage sha `b24749ae65f2…` (2 job で同一) | 同一 (preimage 一致) | `409e13f8` (search_config の admission policy epoch が違う) |
| 受領証 (`knowledge_manifest_receipt.json`) | `c42dc712…` | 同一 | 同一 |
| 環境契約 sha / activation | `e576e9cd…` / serial 1 `f7807285…` | 同一 | 同一 |
| enforcement closure (lock の contract loader 束縛) | commit `8fd2a2f5c`、**96 path** (2 job で同一 bytes の lock) | commit `6a3e15809`、63 path — **37 path が違う** (追加 33、変更 4: `loop.py`・`campaign_lock.py`・`contract_loader_binding.py`・`artifact_admission.py`) | commit `d2ebef7a4`、63 path — 42 path が違う |
| 旧 lock の読取り | — | 現行の厳密 decoder は「closure の key 集合が不正」で拒否する (JSON を直接読んで比較した) | 同じく拒否 |
| admission policy | `db6bc9ea…` | 同一 | 別 (`949ddcc2…`、T-2304 の pin 前進前) |
| build cache の識別 (trace / perf) | 候補 10 `01d14a22…` / `486bcc0a…`、候補 5 `8e06e0bb…` / `344e98a8…`、stock `ed7f05fa…` / `cbbce43c…` と `f458519c…` / `f7d2e775…`、すべて非 cache | 候補 10 `6c87eb2e…` / `7a60310d…` | round 3 候補 10 `2dc461cc…` / `3fae380f…` |
| 候補 10 の source (`src_token`) | `fec064b1…` | 同一 | (round 3 の WAL 原本は消失、比較していない) |

同じ variant・同じ PIN でも build の識別は job ごとに違い、どの build も cache を使っていない。ID が同じでも走行は別であり (ID の同一 ≠ 走行の同一)、
本 wave の 2 job は初投入とは別 tree・別 out_root・別 claim である。**epoch が違うことを理由に過去の測定を無効にはしない** (規律 7)。

## 5. 派生入力の限定 (D2194 項 2 / D2211 項 1 の開示)

- **round 3 の campaign 原本 bytes は 2026-09-20 に消失している (F1034)。** 4 巡目の入力は派生物 (repo tracked) から組んだ。sha 一致が示すのは**確認した data の同一性まで**である。
  (i) critic-3 が読んだ対象全体の再監査、(ii) planner / coder へ渡す完全入力を正しく組み立てたこと、(iii) その実送付、のいずれも証明しない。
- **送付の限定:** 登録 role へは prompt 全文 (上の sha の file) を親が Agent 呼出しへ写して送った。送った bytes と file の一致は機械照合していない (round 3 と同じ限定)。
- 4 巡目の入力に pair 再投入の結果 (同 job stock 348,883 tps など) は入れていない (段 4 裁定 P1、D2194 が却下した択 C の混在を避けた)。prompt は「4 巡目の job に同 job stock が入り、その結果は生成より後に出る」ことだけを開示した。
- coder-5 は診断 (評価済みの 20 / 25 / 10 とその tps・候補 5) を知って合成した。「既知値を見ずに合成した」とは書かない。

## 6. 親の判断 (段 4 裁定 `reviews/s4-ruling.md`、結果を見る前)

- P1 (4 巡目入力は択 A 厳守、pair 結果を渡さない)、P2 (検査を通れば値に関わらず評価、拒否なら再生成せず停止)、P3 (`prior_critic_reverse=false`、classification は coder の自己申告値)、
  P4 (見積り) を採用。やらない理由の最も強い形は裁定に記録した。
- **node 時間の見積り (D2212 項 4、第 31 回 項 1) — 投入前の見積りは裁定に反していた:** 投入前は pair job を 3〜15 分と置き、受入 1 回 ≈ 0.25 node 時間 × 最大 3 回を足して
  合計 ≈ 0.35〜1.25 node 時間と見積もり、確認ライン (2 node 時間) を下回るとして**確認を取らずに**1 本目を投入した。しかしこの 3〜15 分は候補のみ job の実測 69〜432 秒を部品に置いた外挿であり、
  **D2211 項 1 は「過去の K2 1 job の Elapse 69〜432 秒は候補走の値で、pair の完走時間へ外挿しない」と明示している。** brief (`reviews/s1-brief.md` P4、当時のまま保存) は
  「外挿を含む仮定、D2211 の注意どおり実測扱いしない」と書いたが、限定を付けても外挿を使ったことは変わらず、注意に従ったとは言えない (段 6 レビュー M1)。第 31 回 項 1 もこの禁止を解いていない。
  外挿を使わずに言える投入前の上限は job の walltime (3 時間 × 1 node) × 2 job = 6 node 時間で、これは確認ラインを越える。**本来は 1 本目の前にユーザーの確認を取るべきだった。**
  - 4 巡目の前の取り直し (≈ 0.8 node 時間) は、pair 走の実測 Elapse 100 秒 (pair job そのものの実測) に基づくもので、上の外挿とは別である。
  - 実使用: 計算ノードは 2 job で 207 秒 (1 node ずつ、≈ 0.06 node 時間)。受入の実使用は job root の受領証と worklog が持つ。LLM の直列時間は role 2 回 (各約 37 秒) と段 6 レビュー 1 本。
  - 測定値・certified 判定・停止規則の判定には影響しない。失敗の記録は failures fragment (本 wave) に置いた。

## 7. 観測したこと (本 wave では直さない)

1. **`tools/dev_wave_wait.py compute` の使い方を誤り、pair job の終了 (09:26) から 11:07 まで約 1 時間 40 分待った。** この待ち手は qstat を見ず、done file か NQSV accounting file が
   書かれるのを待つだけである。親が直接 qsub した job body はどちらも書かないので戻らなかった。4 巡目は `--done-file <attempt dir>/compute-result.json` (job body が終端で書く) で正しく待てた。
   この使い方は記憶 (`measurement-wave-facts` の待ち手節) に既にあり、引かなかったことが原因である。測定値・判定には影響していない。
2. **pair 用 submit-tree の submodule 初期化 tool (`tools/dev_wave_submodule_init.py`) が 2 回とも `runtime-io-failure` (`update-no-fetch`) を返した。** 入れ子の
   `external/ccbench/third_party/shirakami/third_party/googletest` が記録 `f8d7d77c` でなく `4267679b` のままだった (4 巡目用 tree は同じ手順で成功し `f8d7d77c`)。
   worktree の展開中に Lustre の `システムコール割り込み` 警告が多数出ている。job body の検査 (HEAD・tracked clean・CCBench == PIN) は満たし、CCBench の tracked 改変は 0 行、
   候補・stock とも `--isolate-worktree` の別 checkout で build するので入れ子 submodule は build に入らない。投入は続行した。
3. **`tools/pegasus/README.md` §7 の同 job pair の記述は、修復前の 2 起動 (候補の後に stock driver を 1 回起動) のままである。** job body は D2205 で driver 1 起動 (pair mode) になっている。
4. pair 初投入 (2026-09-20) の `campaign.lock` は、現行コードの厳密 decoder では読めない (closure の key 集合が 63 → 96 path に変わったため)。§4 の比較は JSON を直接読んだ。
5. 並走中の掃除 session があったので、submit-tree 2 本を `git worktree lock` し、両 campaign の原本 (campaign dir + claim、14 file) を job root の `originals-copy-20260922/` へ byte 複製した
   (MANIFEST に sha256、原本と一致)。lock は写しの代わりではなく、写しは lock の代わりではない。

## 8. 次の一手 (本 wave の外)

- **4 巡目の還流:** critic-4 (候補 5 と同 job stock の WAL・digest を読む診断) 1 回、planner-5 / coder-5 / critic-4 の AO 取込み (`--record-agent-output`、login)、層 3 材料レポート。計算ノードは使わない。
- [T-2808] fig12b (同 job stock 対照ありの巡を描く後継図) の起動条件「K2 手動 loop の次の巡が実走したら」が成立した。
- 論文ストーリーの B-6 (d)「同 job stock 対照は未達」と results 表 K2 行の更新 (本 wave では稿・story を編集しない)。
- 上の観測 2・3 (submodule 初期化 tool の EINTR 耐性、手順書 §7 の pair 記述) は必要なら別 wave。

## 9. 一次資料

- `verbatim/` — 依頼の逐語、`planner-5.json`、`coder-5-response.md` (応答全文)、`coder-5.json` (取り出した JSON)
- `reviews/` — `s1-brief.md`、`s4-ruling.md`、段 6 の `s6-review-prompt.md` / `s6-review.md` (NO-GO、must-fix 1 = 見積りの外挿、should 1) / `s6-adjudication.md` (2 件とも real・採用)。
  `s6-review.md` は markdown 改行用の行末空白 15 行を除く可逆最小正規化を当てた: 原文 sha256 `241309447bd0b16c94942cdbcdc7abc3bac4804c6b5e5d92edc9d5526f6a9990` (5,806 B) →
  `8576ad1e0bbe4d3190880d68038c72b4417b9d667b2e04027f3e8298f8e67309` (5,776 B)、job root の原文 `review.md` と `diff -w -B` で一致 (rc=0)。
  fix (`6dc046add`) 後の焦点再レビュー 1 巡目 `s6-focus-1-prompt.md` / `s6-focus-1.md`: **GO**、M1 / S1 とも closed、派生値 (6 node 時間・207 秒 ≈ 0.06 node 時間・正規化の値) を再計算で一致。
  同じ正規化 (行末空白 4 行): 原文 sha256 `8808b7b58c68b41530d4f1f2375d89340252d18ea01da377a1f8d19d988b4fb9` (5,300 B) →
  `ec7a0dd31982bb35efbf073bec687742ba1bae22d7c520d5c005f0c3408be317` (5,292 B)、job root の原文 `focus-1.md` と `diff -w -B` で一致 (rc=0)
- `materials/` — 4 巡目の入力 (`planner-input-5.json`、`planner-context-5.json`、`coder-input-5.json`、`diagnosis-5.json`、prompt 全文 2 本)、`proposal-5.json`、
  再構成物 2 本、WAL 射影 (`wal-outcomes-pair.json`、`wal-outcomes-r4.json`、variant ごとの stage・admission・verify・bench)、epoch 比較 (`epoch-diff-pair.json`、`epoch-diff-r4.json`)
- `evidence/attempt-{pair,r4}-0001/` — `job.stdout` / `job.stderr` / `compute-result.json` / `reservation.json` / `masstree-prebuild-receipt.json`。
  **可逆最小正規化 (DW-S07):** 両 `job.stdout` は行末空白 2 行 (`-- Found Threads: TRUE  `) が `git diff --check` に抵触するため行末の空白 / tab を除去した (可視文字不変)。
  pair: 原文 sha256 `19e4641587563b65f3a1e46091d1d3a928d9eaf0013d6679c87351a579eab1fa` (13,524 B) → `9b838edf643434658e953d19036eb095c2347758d7f3870486e54e3acce0b42d` (13,520 B)。
  4 巡目: 原文 `0949e2b8806db0c8afb685fd5e1b223f8bc65551b87511dd41728ccbddf3188a` (13,505 B) → `19b90032671ff0683b0dd5dc7bb565d3a4c4355709e0e80de7222f2e51efb8cb` (13,501 B)。
  どちらも job root の原文と `diff -w -B` で一致 (rc=0 を実測)。他の file は無変更の複製 (pair: `job.stderr`=`ad2cb3fa…`、`compute-result.json`=`f0233f92…`、`reservation.json`=`bb129716…`、
  `masstree-prebuild-receipt.json`=`a872ac98…`。4 巡目: `797b15f7…`、`4b128073…`、`1e038656…`、`462fed16…`)。
- **campaign WAL・`campaign.lock`・`s4_loop_digest.txt`・`loop_state.json`・受領証・claim は repo へ複製していない** (guard の防護対象)。原本は lock 済みの
  `submit-tree-pair2` / `submit-tree-r4` の `output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` と `output/env/pegasus/claims/`、byte 複製は `originals-copy-20260922/`。
- job root の glue (repo 外、実装面ではない): `precheck.py`、`setup-submit-trees.sh`、`lock-trees.sh`、`qsub-submit-pair.sh`、`wal_outcomes.py`、`check_stock_variant.py`、
  `build_round4_inputs.py`、`build_coder_input_5.py`、`build_proposal_5.py`、`extract_coder_json.py`、`concat_prompt.py`、`epoch_diff.py`、`ratios.py`。
