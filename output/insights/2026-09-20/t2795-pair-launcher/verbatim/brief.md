# 段 1 brief — [T-2795] (i) + [T-2797]/[T-1872] (α): 同 job pair launcher と B-5 §10 共有部品の段階実装

起点 local main `371674ea6` (2026-09-20 12:32 JST)、worktree `.claude/worktrees/dev-wave-t2795-pair-launcher`。

## 研究前進
土台。止めている実測 = (a) K2 手動 loop の「同 job stock 対照」(D2172 項 3: critic R0 が 3 巡連続で要望、launcher 不在で未履行)、
(b) B-5 生成器対照の試走 (β) (D2172 項 4: §10 の「実装が要る」部品のうち K2 共有 3 部品が無いと 1 session も流せない)。
最小差分 = 3 file (job body / driver / pipeline) と test。完了判定 = 候補 1 + stock 1 を 1 job で評価する CLI 経路が test で成立し、既存 fixture / proposal 経路の既定挙動が bytes 不変で残ること。

## scope (裁定 D2172 項 3 (i)・項 4 (α) の逐語範囲。順に区切る)
1. **同 job pair**: job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) に stock step、driver (`orchestrator/campaign/p3_s4_loop.py`) に stock genome の評価口、pipeline (`orchestrator/campaign/pipeline.py`) 自身が発行する stock WAL、identity への影響の整合 (設計メモ `output/insights/2026-09-19/k2-loop-round3/reviews/s2-plan.md` 項 6)。
2. **較正動作点 CLI**: `default_perf()` の無条件使用を、承認済み PerfConfig (較正済み 1M / 48 / 3 s / 5 reps = `p2_2.py` 定数、workload 3 種 = B-5 §5.2) の指定に差し替える口。
3. **exact correctness 経路**: `pipeline.evaluate` の correctness 引数の指定・記録と `performance_correctness_workload()` の接続 (§5.5)。
scope 外: pair 投入 (候補 10 + stock)・4 巡目・B-5 試走 (β) は land 後の別 wave。B-5 本走は未認可。仮想リスク向けの gate・検査・台帳・一般化・互換層は足さない。random 生成器・sweep B 点・解析 consumer・session 契約の flag 束縛・B/A 台帳は本 wave の対象外 (§10 の残り部品)。

## 確定済みユーザー裁定
- D2172 項 3 (i): 同 job pair launcher を Codex author の別 wave で実装 (= 本 wave)。候補 10 の再評価・4 巡目 (iv) は認可済みだが別 wave。
- D2172 項 4 (α): §10 部品を K2 共有部品 (同 job stock、較正動作点 CLI、exact correctness 経路) から段階実装。本走は未認可、発効 commit は本走認可時。
- D95: 実装面は Codex author。親は実装面を直接編集しない。

## 不変条件 (受理集合を変えない / 規律 2)
- I1. 既存 fixture 経路 (`--value`、受理域 1..1000、`validate_backoff_value`) と proposal 経路 (`--run-iteration`) の既定挙動・既定 argv・既定 identity (search_config) は不変。stock は**別の口**で、`--value -1` の受理拡大にしない。
- I2. correctness 拒否・anomaly 即 reject・certified の条件 (全 verify pass 通過後だけ COMMIT) を保存する。exact correctness は既存の `search_config["verify"]` 機構 (`loop._closed_verify_workloads` → `performance_correctness_workload(perf)`) を通し、legacy 既定 pass を外さない。
- I3. stock WAL は `pipeline.evaluate` (run_campaign 経由) だけが書く。親・job body・driver が WAL record を手書き・移植しない。
- I4. stock 評価は LoopState (checkpoint / iteration / whiteboard) を進めない。planner / coder / 検疫 (quarantine) を通らない (対照であって提案ではない)。
- I5. identity: PerfConfig を差し替える経路では `search_config` の `records` / `threads` (+ workload 識別) を perf と一致させ、identity が実際の動作点を表す。既定経路の identity は不変。
- I6. job body の逐語 pin test (`orchestrator/tests/test_p3_s4_loop_job_contract.py`) は author が同時更新し、既存 pin 行は削らない。`--reasoning`/権限等の dev-wave 契約は別。
- I7. 凍結物の bytes を変えない (DW-O09: 3 file の live pin なし、hit は歴史 receipt のみ)。

## 親の provisional 裁定 (攻撃対象)
- (P1) stock は候補と**同じ campaign** (同 identity / 同 WAL) に入れる。variant は `src_token == STOCK` で区別され、`make_critic_identity_projection` (`p3_s4_loop.py:1064–1136`) は既に stock label を持つ。別 campaign 案は「同 job・同 pin・同 identity の対照」を identity で分断する。
- (P2) stock genome = `Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": -1})` を **applied TEMPLATE_PATCH 下**で評価 (stock-inert: b10 の `_inert_reference_genomes` 先例 `b10_backoff_shape_sweep.py:957–1036`、`source_digest` が STOCK token を返す)。無改変 PIN 木で `BACKOFF_FIXED` flag を渡す案は build の受理を別途確認する必要があり採らない。pipeline が STOCK token を実際に返すことは test / 実走で確認する (約束しない)。
- (P3) 較正動作点 CLI は `--perf-workload {write-heavy,balanced,read-heavy}` + 較正 opt-in の 2 口で `PerfConfig(records=p2_2.RECORDS, threads=p2_2.THREADS, workload=..., extime=p2_2.EXTIME, reps=p2_2.REPS)` を組む。`ycsb_max_ope` は `performance_correctness_workload` の 4 key 必須のため明示する (出所は plan が示す: `S2_FLAGS` の "10" / A-2 qualification の "10" / CCBench 既定)。省略時は `default_perf()` (既定不変)。
- (P4) exact correctness は `search_config["verify"] = VERIFY_LEGACY_PLUS_PERFORMANCE` を CLI opt-in で焼く (identity が変わる = 意図どおり別 campaign)。「記録」は WAL verify record の `workload == {"tag": tag}` exact 照合 (`pipeline.py:961`) を壊さない場所に置く (候補: campaign layout 配下の create-only receipt、または campaign.lock preimage に既に含まれる search_config で足りるなら追加なし)。
- (P5) job body の stock step は `IZANAGI_S4_STOCK_CONTROL` 系の env opt-in で、proposal 経路の**後**に同 allocation・同 prebuild receipt で driver を再度呼ぶ (候補 → stock の順、失敗時は stock を省かず結果を残す)。既定 (env 不在) は現行の排他的 1 起動と bytes 同一の挙動。
- (P6) 段構成: 設計択一 (P1〜P5) が割れうる・pipeline (正しさ経路) に触るため軽量版でなく、段 2 plan 1 + 段 3 consult 2 レンズ + 段 6 review 2 本を回す。

## 変更面 (実アンカー)
| file | 現行アンカー | 変更 |
|---|---|---|
| `tools/pegasus/p3_s4_loop_pegasus.sh` | `:17–24` required_env、`:53–96` K2 env → argv、`:580–593` 排他的 1 起動 | stock env の受理 + stock step の追加 (proposal 経路の後) |
| `orchestrator/campaign/p3_s4_loop.py` | `default_cfg :1552–1583` (search_config records/threads)、`default_perf :1631–1636`、genome 組立て `:1930`、`run_campaign` 呼出 `:2019–2052`、`main :2785–3220` (argparse `:2797–2854`、`perf = default_perf()` `:3040`) | stock 評価口 (I4)、PerfConfig 指定口 (P3、I5)、verify mode opt-in (P4) |
| `orchestrator/campaign/pipeline.py` | `performance_correctness_workload :193–226`、`evaluate :2585`、verify pass 組立て `:1719–1722`、verify record `:1925 / :961` | correctness 引数の記録 (P4 の置き場次第で無変更もありうる) |
| `orchestrator/campaign/loop.py` | `_closed_verify_workloads :152–161` | 変更なし想定 (接続先として引く) |
| `orchestrator/tests/test_p3_s4_loop_job_contract.py`、`test_p3_s4_loop.py`、`test_pipeline_verify_result_retention.py` | 逐語 pin / driver test | 新 test (正例・負例) と pin 更新 |

## 成果物の形
- 実装 commit (author の差分を親が統合)、記録 commit (insight `output/insights/2026-09-20/t2795-pair-launcher/README.md`、worklog / decisions fragment)。
- 変異 matrix (等価対照 + 負例: stock が whiteboard を進める・`--value -1` 受理・legacy pass 欠落・identity 不整合・job body の stock step が既定で発火 等)。
- 受入 = `tools/dev_wave_wait.py acceptance` (計算ノード)。焦点走 = 変更 test file + `test_plain_runner_coverage`。

## 並列分割
author 1 本 (3 file + test は結合が強い。(1)→(2)→(3) の順で作業し報告を節で分ける)。段 6 review 2 本 (A: 正しさ境界・identity・WAL、B: 既定挙動不変・過剰実装・削除)。

## 成果物影響 (DW-G05)
放置時: K2 の同 job stock 対照が取得できず critic R0 が未達のまま、B-5 試走 (β) が開始できない。certified 選択・台帳の既存値は変わらない (影響は「取得できない対照」)。

## 生死確認 (DW-G01)
stock genome の pipeline 評価は b10 / A-1 paired / `loop.run_campaign` で実走済み (先例)。新規探索軸ではなく結線なので、専用の使い捨て driver は作らない。E2E の実走 (1 job) は land 後の pair 投入 wave が担う。
