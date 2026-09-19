# K2 手動 loop 第 3 巡 — critic-2 診断を型付き入力へ渡して候補 10 を 1 評価した (縮小走行: 同 job stock 対照は未達) (2026-09-19)

wave: `dev-wave-k2-loop-round3` / branch `worktree-dev-wave-k2-loop-round3` / 着手時 local main
`a99425b66258911973785b11fd7d194884aeec64` (記録前に `657e1e5a7` を取り込み)。job root (repo 外)
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round3/`。上位 task = T-2783 (D2148 項 3 / D2155) の「3 巡目の実走予算は別依頼で確定」。
実装差分ゼロ (Codex 実装子なし)。段 2 plan 1 本、段 3 相談 2 本、段 4 裁定、段 6 read-only レビュー 1 本の逐語は `reviews/`。

## 一行で

**critic-2 の診断 4 節が D2155 の経路で初めて planner-v4 / coder-v4-autonomous-k2 の型付き入力 (`k2_critic_diagnosis`) に届き、
planner-4 は decrease / large、coder-4 は value 10 (診断の候補値と同じ) を提案し、その 1 評価は serializable / certified / anomalies 0、
median 815,983 tps、停止判定 continue、critic-3 まで 1 巡が閉じた。** ユーザー決定 (2026-09-19) の「同 job の stock 対照 1 本」は
既存の評価口に stock 結線が無く**未達**であり、本走は候補のみの**縮小走行**である (裁定パッケージ候補 1)。
**改善の実証ではない** — 同時刻対照が無く、3 走 (20 / 25 / 10) はすべて非同時刻・別 tree。**診断が「届いた」「参照された」ことと
「効いた」ことは別**であり、coder-4 が候補 10 を出した因果は本走からは言えない。

## ユーザー決定と実行の対応

| ユーザー決定 (2026-09-19、逐語は `reviews/s1-brief.md`) | 実行 |
|---|---|
| 候補の生成 1 回 | planner-4 1 回 + coder-4 1 回 (再抽選なし) |
| 評価 1 本 | job `10761.nqsv` 1 本 (attempt-0001、投入 1 回、再投入なし) |
| 同 job の stock 対照 1 本 | **未達。** `tools/pegasus/p3_s4_loop_pegasus.sh` は 1 job = driver 1 起動 (候補 1 本) で stock arm が無く、`p3_s4_loop.py` の value 受理域は 1..1000 (stock 相当 `-1` は拒否)。確認した代替 (A-1 paired / B10 grid / floor / T-1998 stock-inline / guided `--genome`) は別 study・別 PerfConfig で同条件 pair にならない (段 2 plan 項 6、相談 A#7)。全手順の不在証明ではない。「経路の改修・新 launcher」は scope 外の指定 |
| 既知値 20 の再評価はしない | coder-4 は 10 を提案 (20 なら投入しない裁定だった) |
| 候補 10 を正解扱いしない | 記録は「診断の候補値と一致した提案」まで。正解・改善とは書かない |
| `delta_pct` は null のまま | whiteboard の `delta_pct=null` (harness の `_DELTA_PCT_LIVE=False`) |
| anomaly は即 reject | anomalies 0 で発火せず。手順は既存 `run_campaign` → `pipeline.evaluate` (trace / perf 別 build) を触っていない |

## 診断が届いたか (D2148 項 3 / D2155 の初回実走)

- **入力組立て:** round 2 の critic-2 逐語 (`output/insights/2026-09-18/t2746-k2-loop-round2/verbatim/critic-2.md`、sha256 `d2b2ab77…`) から `k2_critic_diagnosis_from_bytes` で exact 6 field
  (`data_boundary` / `source_sha256` / attribution 2035 / recommend 1469 / avoid 639 / uncertainty 1802 chars) を作り、`planner_context_payload`
  (K2・非 B-4・reflux on の適用条件検査込み) → `k2_next_generation_inputs` で planner-4 / coder-4 の両入力へ同一診断を組み込んだ
  (`materials/diagnosis-4.json` sha `7b742268…`、`planner-context-4.json` sha `280caa0f…`)。
- **CLI `--emit-planner-context` は使っていない。** login node は `PEGASUS_LOGIN` 分類 (hostname + NQSV 証拠) で `_admit_env_contract` が
  emit 分岐より前に拒否する (round 1 の記録 §射影と同じ制約)。CLI の中身と同じ production 関数を直接呼び、CLI が行う受領証の
  書込み/照合は親が代替検査した: 受領証の正準 bytes (`knowledge_manifest.receipt_bytes`) が round 2 campaign の `knowledge_manifest_receipt.json`
  と完全一致 (sha `c42dc712…`)、K2 射影 bytes が round 2 の `knowledge-input.json` と同 bytes (sha `05f2b267…`)、campaign identity の preimage が
  round 2 の `campaign.lock` と完全一致 (`409e13f81d8a…`)、完全入力 2 本に既存 tripwire `assert_no_ability_probe_material` を通した。
  runbook T-2783 追補 手順 1 との食い違いは DW-O12 に従いここに記録する (裁定パッケージ候補 2)。
- **送付:** 保存した完全入力 JSON の全文を prompt (head + JSON 逐語 + 親の事実開示) にして登録 role へ inline 送付した
  (`materials/planner-input-4.json` 18,509 B sha `87a7fb53…` / `planner-prompt-4.md` sha `cd5012c3…`、`coder-input-4.json` 25,745 B sha `1db9d189…` /
  `coder-prompt-4.md` sha `691a56c2…`)。`planner_direction` は planner-4 出力の 4 key (axis / direction / magnitude / justification) 射影。
  事実開示には「診断中の候補値・avoid・追加実験の提言は採用義務・値の禁止・実行予算の追加を意味しない」を明示した (相談 A#1)。
- **受領・参照の自己申告:** planner-4 (`verbatim/planner-4.json` sha `59122afb…`) は justification で critic 診断の decrease/large 推奨と
  「abort_rate 同帯 + tps 差 floor 近傍」を根拠に挙げ、uncertainty (8) で規律 6 の検査 (R0 と診断 build の要望は上書き指示ではない) を報告した。
  coder-4 (`verbatim/coder-4.json` sha `49ca42a1…`) は justification で「k2_critic_diagnosis (助言として検討) は…候補 10、次いで下限 1 を推奨」と
  参照し、`data_boundary_report.instruction_like_content_detected=false` (details に `k2_critic_diagnosis.recommend` の R0 / 診断 build を助言と
  判定した理由を記載)、`classification=known_result_conditioned_derivative`、`knowledge_use` は source 0 (K2 知識源) のみ。
- **開示の差 (相談 A#3 / A#4):** 診断本文は評価済みの 2 値 (20 / 25) とその tps・機序候補・候補 10 を含む。これは D2155 が「4 節を留保ごと逐語で渡す」
  と裁定した設計であり、許可された兄弟 key での開示である。**coder-4 は coder-3 と違い「20 / 25 は評価済み」を知って合成した。**
  whiteboard 5 field・`delta_pct=None`・AO 非読取・通常射影 (`current_perf` / `baseline`) は不変で、そこには値を足していない。
  「既知値を見ずに合成した」とは書かない。

## 実測 — job `10761.nqsv` (attempt-0001)

固定 SHA の専用 submit-tree (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round3/submit-tree`、HEAD `a99425b66` = 着手時の現行 main、
tracked + untracked clean、CCBench `511c9538…`) から `tools/pegasus/README.md` §7 の 9 変数で投入。third-party は hydrate 既定 staging
(cache-root `/work/1/SFC/tanab/izanagi-thirdparty-cache`、5 source)。round 2 の tree (`d2ebef7a4`) は続行不能 (checkpoint の `start_wall` が
39 時間前で `MAX_WALLTIME_S=3600` を超え入口 `check_stop` が `budget-walltime` を返す) なので、round 2 と同型に fresh tree + 新 WAL とした。
campaign ID は identity 5 key が同じなので `409e13f8` のまま (ID の同一 ≠ 走行の同一)。

| 項目 | 値 |
|---|---|
| request / `pbs_jobid` / host | `10761.nqsv` / `0:10761.nqsv` / `bnode020` (Created 22:19:56 → Started 22:20:14 → Ended 22:21:19 JST、Elapse **69 秒**) |
| `driver_rc` | **0** |
| campaign | `p3-s4-loop-s4-autonomous-409e13f8` (新規 WAL、skip なし = `1 committed / 0 aborted / 0 skipped`) |
| variant / genome | `002642c7ac96` / `silo\|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| build | trace `2dc461cc11abfee0` / perf `3fae380fee3b0a5b`、いずれも非 cache (`trace_cached=false` / `perf_cached=false`)、build 区間 15 秒 |
| verdict | **`serializable` / `certified=true`**、anomalies **0** (commits 523,120 / aborts 122,211、trace build の abort 率 18.94%)、`commit_witness` {523120, 0}、`proof_surfaces` X/P present、I absent |
| bench | median **815,983 tps**、2 反復 `[815067, 816899]`、run 内 CV 0.1588%、`settled=true`、`bench_wall_s` 2.09 |
| abort 率 (perf build) | 9.065% (T-2702 以降の集約: 偶数 reps では中央 2 件の中央値。round 2 と同じ規則) |
| `llc_miss_rate` / `ipc` | **null (欠測)** — `perf_observation.preflight` `status=unavailable` / `rc=2`。0 でも差なしでもない |
| 終端 / 停止判定 | `outcome=certified`、`iteration=1`、whiteboard 1 件 (decrease / large / success / delta null; **success は certified の意味で、性能改善ではない**)、**`continue`** |
| WAL / 防護 file | WAL 5 record sha256 `eb8927b7…`、`campaign.lock` `f1ab4966…`、`loop_state.json` `917ba3d3…`、`s4_loop_digest.txt` `f993251d…`、受領証 `c42dc712…` (critic-3 前後・AO 取込み前後で不変) |

投入前に login で通した production 検査 3 本 (`assert_closed_proposal_schema(..., coder_contract=CODER_CONTRACT_K2)` OK /
`validate_backoff_preflight("double now_backoff = 10;")` accepted (負例 `25 + 1` は拒否) / `load_proposal_file(..., coder_role="coder-v4-autonomous-k2")` OK、
planner=decrease/large、value=10、`prior_critic_reverse=False` は親の解釈: 前評価 proposal-2 と critic-2 はともに decrease で逆方向でない)。
proposal は `materials/proposal-4.json` (sha `bd3e5fd2…`)。K2 env は manifest = t2182 の wal-only (resolver digest `396cd559…`)、
`CODER_ROLE=coder-v4-autonomous-k2`、`KNOWLEDGE_CLASSIFICATION` は coder-4 の自己申告と同じ `known_result_conditioned_derivative`、`DE_NOVO_CLAIM=false`。

**Elapse 69 秒 (round 2 は 432 秒)。** bench 本体 (`bench_wall_s`) は両巡とも約 2.1 秒、build 区間も両巡 15 秒で、差は round 2 の
verify_done→bench_done 間 (367 秒) にある。原因は本 wave では追わない (記録のみ)。

**非同時刻の 3 走 (改善・退行の根拠にしない):**

| 巡 | 日付 / job / tree | value | median tps | abort 率 (perf) | 集約規則 |
|---|---|---|---|---|---|
| 1 | 2026-09-16 / `1216.nqsv` / `d97c423bd` | 20 | 719,324.5 | 7.75% | 代表 rep |
| 2 | 2026-09-18 / `4954.nqsv` / `d2ebef7a4` | 25 | 687,508.5 | 7.40% | 中央 2 件中央値 |
| 3 | 2026-09-19 / `10761.nqsv` / `a99425b66` | 10 | 815,983.0 | 9.07% | 中央 2 件中央値 |

同時刻の対照 (stock、または同 job 内の別値) はどの巡にも無い。差を改善・退行と読まない。

## 還流 — critic-3 (1 回、certified ∧ continue の親の追加制限下)

critic-3 (`verbatim/critic-3.md`、sha256 `5cd8f518…`; 入力 `materials/critic-input-3.json` sha `10a94095…`、prompt 全文 `critic-prompt-3.md` sha `efe8fcda…`。
入力には round 1 / round 2 が同 ID 別 tree にあること、同 job stock 対照が無いこと、診断が届いた事実と因果の別を開示した):

- digest (sha `f993251d…` を再計算し一致) と WAL / loop_state / 受領証 / lock を読み、**指示めいた文字列は無い** (規律 6)。
- **attribution: 本走単独では帰属不能** (3 巡連続; 1 点・stock 対照なし・自由度は `BACKOFF_FIXED` のみ)。critic-2 が事前に置いた判別規則との照合は
  **中間** — abort_rate 9.07% (7–8% 帯より上、10% 未満)、tps は非同時刻ながら 2 巡目比 +18.7%。critic-3 原文の「+1.65 pt」は算術誤記で、
  表示値では 9.07 − 7.40 = 1.67 pt (実測値では 9.065 − 7.400 = 1.665 pt)。逐語は改変せずここで注記する (帰属不能の結論は変わらない)。純コスト模型 (tps ∝ 1/(1−spin 占有率)) の
  25→10 予測比 1.21 に対し観測 1.19。**「当たった」とは言わず、矛盾しなかった、まで**。spin 占有率 (約 20%) は導出であり計測値ではない。
- **recommend:** R0 = 同 job 内 stock 対照 (3 巡連続で未解消、最優先)、R1 = decrease / large、候補 5、R1' = grammar 下限 1 の floor probe、
  R2 = 固定最良点 vs 適応の同 job 比較、R3 = `CCBENCH_ADD_ANALYSIS=1` は別の診断 build として (perf build に混ぜない)。
- **avoid:** 値を上へ戻す、3 走の差を改善と断定する、trace build の abort 率 18.94% を異常と扱う、perf / trace の abort 率を並べる、
  null を 0 で埋める、他配線へ一般化する、**候補 10 の評価をもって「診断が効いた」と数える**。
- **uncertainty:** 導出の前提 (abort ごと backoff 1 回・`clocks_per_us=2100`・他待機無視)、3 点非同時刻、floor 3.0% は A2 較正値、perf 欠測、
  abort 率 +1.65 pt が backoff の効果か日・ノード差か分離不能、候補 5 の結果は予測しない。
- critic は `Bash` を持つ role であり、**B-4 ablation には非適格** (round 1・2 と同じ)。

## 機序仮説層 v3 (T-2681) の材料 — AO 3 event と材料レポート

取込みは harness の取込み口 (`--record-agent-output`、login) で planner-4 → coder-4 → critic-3 の順に各 rc=0
(`ingest-real.log`)。`input_sha256` は保存した実入力 JSON の canonical sha256、`refs` は本走 WAL 5 record の canonical ref (`materials/wal-refs.json`)、
3 event とも `--agent-prompt` 付き (相談 B#11)。取込み前後で防護 5 file の sha256 は不変。

| 順 | stage | 出力 | 入力 | variant | `ao:` ref |
|---|---|---|---|---|---|
| 1 | planner_proposed | `verbatim/planner-4.json` | `materials/planner-input-4.json` | `002642c7ac96` | `36ed8464…` |
| 2 | coder_proposed | `verbatim/coder-4.json` | `materials/coder-input-4.json` | `002642c7ac96` | `9fc336fc…` |
| 3 | critic_attributed | `verbatim/critic-3.md` | `materials/critic-input-3.json` (digest sha `f993251d…` を含む) | `002642c7ac96` | `00b6a51c…` |

AO は `submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/runs/agent_outputs.jsonl` (3 行、sha256 `66d3e737…`、repo へは複製しない)。

**材料レポート `layer3_report.json`** (sha256 `c37fda1f…`、`--output-root <submit-tree>/output`、`--generated-from-head a99425b66`):
`schema_version` v3、`agent_outputs` 3 件、`mechanism_hypotheses` 1 件 (variant `002642c7ac96`、attribution = critic-3 の逐語、refs 5、digest `f993251d…`)、
`mechanism_hypotheses_provenance = agent_outputs`、`source_refs` **9 = wal 5 + wb 1 + ao 3** (双射通過)、`admission_status = admitted` /
`classification = admitted-new-schema`、`certifying_input = false`、`knowledge_level = K2`、`noise_floor` は within/between とも
`no-matching-env-record` — 較正記録は走査されたが本走の条件 (silo / 4 threads / 100,000 records) に適合する採用可能な記録が無い
(between-run の候補 3 file はいずれも 48 threads / 1,000,000 records で不一致、within-run は登録済み較正 pin の `within_run_exclusion =
self-inconsistent-calibration` で除外)。**材料であって certifying 入力ではない。**

## 閉じていないもの

- **同 job の stock 対照 (ユーザー決定の 1 項目、critic の R0 が 3 巡連続)。** 既存 S4 口に結線が無く、本 wave の scope 外 (経路の改修・新 launcher)。
  最小 launcher に要る要素の設計メモ (job body の stock step、driver の stock genome 評価口、pipeline 自身が発行する stock WAL、
  identity への影響) は `reviews/s2-plan.md` 項 6。実装はしていない。
- critic の診断は届くようになったが、**診断なし統制が無いので「効いた」は言えない**。診断が既知値 (20 / 25) を開示する点は設計どおりで、
  次巡以降の記録では coder が何を知って合成したかを明記し続ける。
- perf 欠測、legacy critic のため B-4 非適格、`classification` の自己申告と呼び手宣言の非照合は変わらない。
- runbook T-2783 追補 手順 1 の CLI は login では走らない (round 1 と同じ)。docs 追記は本 wave の変更面に入れず候補として返す。

## 主張しないこと

- **3 巡が閉じたことは、合成による改善や探索の有効性の実証ではない。** 815,983 tps は非同時刻の 1 点で、同時刻対照が無い。
- 候補 10 が診断の候補値と一致したことは、**診断の「採用」を自己申告した記録であって、診断が提案値を変えた因果ではない**。
- 固定 backoff の初期値であって新しい CC 構造ではない。候補間の certified な選択ではない。K2 の利用因果、B-4 適格を主張しない。
- `mechanism_hypotheses` は LLM の帰属記録であって機序の実証ではない。critic-3 の spin 占有率・模型比は導出であって計測値ではない。
- AO の `input_sha256` / `mode` / `ts`、診断の `source_sha256` は申告・記録・識別であって、role が実際にその入力を受け取ったことの証明ではない。
- 本 wave は認可された 3 巡目の**完全達成ではない** (stock 未達の縮小走行)。

## 裁定パッケージ候補 (本 wave は判定しない)

1. **同 job の stock 対照 (未達)。** 択 (i) 同 job pair launcher を別 wave で実装してから候補 + stock の pair を投入 (候補 10 の再評価を含む
   認可が要る)、択 (ii) 本 wave の候補のみ評価を縮小走行として受理し stock は別途、択 (iii) 元の pair 要求を維持し手順と scope を別途確定。
   新 launcher が必須とは断定しない (全手順の不在証明ではない)。
2. **runbook T-2783 追補 手順 1 (CLI emit) の login 制約。** 追補に「login では production 関数の直呼び (round 1 / 3 の形) で組み立てる」の
   1 文を足すか (docs 追記のみ)。
3. (round 2 から持ち越し) 層 3 v1 reader / fresh 比較 consumer (T-2784) — 本 wave では触れない。

## 証拠の所在

repo 内 (本 dir):

- `evidence/attempt-0001/` — `job.stdout` / `job.stderr` / `compute-result.json` / `reservation.json` / `masstree-prebuild-receipt.json`
- `materials/` — 診断 / planner context / 役割の入力 JSON 3 本 / prompt 全文 3 本 / knowledge-input / proposal-4 / run-summary / wal-refs
- `verbatim/` — planner-4 / coder-4 / critic-3 の逐語
- `reviews/` — 段 1 brief、段 2 plan、段 3 相談 2 本、段 4 裁定、段 6 レビュー
- `layer3_report.json` — 本巡 campaign の材料レポート (v3、`mechanism_hypotheses` 非空)

**可逆最小正規化 (DW-S07):** `evidence/attempt-0001/job.stdout` は行末空白 2 行 (`-- Found Threads: TRUE  `) が `git diff --check` に抵触するため
行末の空白 / tab を除去した (可視文字不変)。原文 sha256 `2b7c25f7957614d2d38d635a0314a509e3dddbf61657442db2babdb09c48087a` (12,365 bytes)、
正規化後 `f223cecc05429fc0613a47af4966962fed31807cb7eadaca3f41546fc50d4677` (12,361 bytes)。`diff -w -B` で原文と一致する (実測 rc=0)。
他の file は無変更の複製で、原文 sha256 は `job.stderr`=`27ce767a…`、`compute-result.json`=`0f637c06…`、`reservation.json`=`c8fecde6…`、
`masstree-prebuild-receipt.json`=`626c0d14…`。

**campaign WAL・`campaign.lock`・`s4_loop_digest.txt`・`loop_state.json`・受領証・`runs/agent_outputs.jsonl` は repo へ複製していない**
(`guard_bash` / `guard_write` の防護対象)。原本は repo 外 job root `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round3/` の下:

- WAL / AO: `submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/runs/{wal.jsonl,agent_outputs.jsonl}`
- checkpoint / digest / 受領証 / lock: 同 `loop_state.json` / `s4_loop_digest.txt` / `knowledge_manifest_receipt.json` / `campaign.lock`
- 投入・取込みの記録: `qsub-0001.stdout`、`qstat-after-submit-0001.txt`、`setup-submit-tree.log`、`hydrate.json`、`ingest-real.log`
- 親の glue (repo 外、実装面ではない): `build_round3_inputs.py`、`build_coder_input_4.py`、`build_proposal_4.py`、`project_round3_results.py`、
  `build_critic_input_3.py`、`run-ingest.sh`、`run-layer3.sh`、`qsub-submit.sh`、`setup-submit-tree.sh`
