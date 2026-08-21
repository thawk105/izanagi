# T-1472 — formal H1/H2 workload campaign zero-diff readiness audit

**性質**: read-only 監査。approval bytes の生成・裁定の代行・正式実験の起動・結果の推測は行っていない。
コード・テスト変更ゼロ (zero-diff)。Rule 2・登録済み preregistration 条件は一切変更していない。
実験本体・人間 lockstep の実行は本 wave の範囲外であり、別 wave/別セッションでユーザーが行う。

**観測時点**: 2026-08-21、worktree HEAD (`b1c5422065650c2d3da44b11a9bb381a26059771`、main と同一)。
下記の充足/未充足判定は全てこの時点の repo 状態に基づく。判定器が導出する「発効」状態は
commit ごとに変わりうるため、後続セッションはこの HEAD からの差分を再確認すること。

**方法**: 段1 brief (親) → 段2 codex plan (`--reasoning max --sandbox read-only`) →
段3 codex 敵対2レンズ (`--lane sol`=正確性、`--lane luna`=実効性論理、同じく read-only) →
段4 親裁定 (全17所見 real・採用、詳細は `s4-adjudication.md`)。一次資料は各行に file:line で示す。

---

## 0. 総合結論

**H1/H2 の certified formal launch (正式受理・certified 選択に数える実行) は現時点で成立しない。**
決定的な直接根拠は、実行 driver 自身が明示的に拒否することである。

> `orchestrator/campaign/p3_autonomous_workload_trial.py:883-896` — `_preflight_workload_profile()`
> は `workload_profile="formal-holdout-legacy-v1"` を検査し、8c 事前登録が発効していない場合
> `effective preregistration unavailable` で例外を送出する。

§5 の実走前必須記入欄 9 項目中 8 項目が未記入であること、§6 の 12 前提条件のうち機械的に
「充足」を返す評価器経路が 1 本もないこと、§7 本文が「現時点の production では実行可能ではない」と
明記していることは、**この拒否と同じ「未発効」状態の異なる現れであり、4 つの独立根拠ではない**
(段3 lensB 指摘2)。

**ただし次の2点は brief 段階からの重要な訂正である。**

1. **「起動不可能」と「非公式実行が一切できない」は別である。** コードには
   `--allow-formal-noncertifying` / `registered-formal-non-certifying` という non-certifying
   経路の足場がある (`p3_autonomous_workload_trial.py:1123-1163,4715-4718,4767-4781`)。
   certified formal launch は不可だが、non-certifying な実行自体を本書は禁止と断定しない —
   ただし non-certifying な実行結果は「ワークロード特化合成」の証拠には数えない (8b §1 の
   selector 実験と同じ限界)。
2. **「H1/H2 の実装が存在しない」わけではない。** holdout 定義・descriptor schema・arm digest・
   generation 予算上限などの**足場は広範に実装済み**である。欠けているのは「足場の存在」ではなく
   「正式受理を証明する充足経路」である。この区別を欠くと、既に実装済みの機構を無駄に再実装する
   誤った次の一手を招く (段3 lensB 指摘1)。

---

## 1. Codex roster・worktree・lease・handoff の所有者確認

command が開始直後の確認を求めた項目。**fork による `ListAgents` 直接実測** (worklog carry より
強い証拠) の結果を記す。実測できなかった項目は「未確認」と明記する。

| 対象 | 所有者/状態 | 証拠 | 確度 |
|---|---|---|---|
| T-425 | 稼働中セッションあり (`t-425 between_run_floor validation prep [d3eff9]`, 5h前開始) | `ListAgents` 実測 | 実測 |
| T-972 | 稼働中セッションあり (`preflight receipt perf staging [627462]`, 15h前開始、worktree名 `dev-wave-t972-perf-preflight-receipt` と符合) | `ListAgents` 実測 + worktree名対応 | 実測+推測 |
| T-1371 | 名指しセッションなし。worktree (`T-1371-official-run-root`, locked) は存在、worklog 次の一手で未クローズ | `git worktree list` + `docs/worklog.md` | worktree実在のみ実測、生存プロセスは未確認 |
| T-1438 | 稼働中セッションあり (`t-1438 real-repo serial chain perf [eb3697]`, 5h前開始) | `ListAgents` 実測 | 実測 |
| T-1458 | **稼働中セッション2件同時** (`t-1458 registry-orchestrator connection [4ef591]` idle、`t-1458 admission registry orchestration [2ef6ae]` shell、いずれも5h前開始) | `ListAgents` 実測 | 実測 |
| T-139 (scope-B Q3ガードの優先タスク) | **未確認**。pilot/本走の現在状態を確認できなかった | fork 側の環境障害により未達成 | 未確認 — 要再監査 |
| scope-B 裁定 fragment の land 状況 | **未確認**。`2026-08-10-rulings-20260806-a-38.md` (commit `051551dd`) が worklog へ land 済みか未達成 | 同上 | 未確認 — 要再監査 |
| docs/handoff/ 残存5ファイル | いずれも H1/H2/floor/oracle/holdout/campaign へ直接言及なし。T-1334 handoff (2026-08-20) に「T-1283 の worktree は既に消滅、生死を再確認せよ」という別件の申し送りあり (T-1472 とは無関係) | 全5ファイル読了 | 実測 |
| worklog 次の一手 | T425/T972/T1371/T1438/T1458 は entry 794→795→796 と一貫して bare carry `(795)` (詳細裁定文なし = 未決着) | `docs/worklog.md` | 実測 |

**評価 (段3 lensA/lensB 共通指摘への回答)**: worklog の carry だけでは「稼働中」を証明できないという
指摘は正当。しかし `ListAgents` の直接実測はこれを補う独立証拠であり、T-425/T-972/T-1438/T-1458 に
ついては「現在も進行中」の確度は高い。**各タスクが実際に H1/H2 の同じファイル・同じ scope を編集して
いるかの diff レベル一致は未検証** (worktree 名とタスク説明文の対応による推測に留まる)。

**command が求めた「重複する場合は実験を起動しない」への回答**: 本 wave は read-only 監査であり
そもそも実験起動権限を持たないため、この条件は無条件に充足している。加えて上記のとおり、
これら5タスクは高い確度で H1/H2 前提整備の並行作業であり、**この audit の結論以前に、これらの wave が
land するまで H1/H2 関連コードは動いている最中**であることを次のセクション以降の判断材料に含める。

---

## 2. H1/H2 の on/off/swapped 条件

**定義は確定・承認済み** (`docs/phase3-8b-descriptor-design.md:3-12,113-127,156-173`、
2026-07-16 ユーザー承認、8b §3-4)。

- H1 = `rratio=80`、H2 = `rratio=20`。共通: `skew=0.9`、`rmw=0`、`records=1,000,000`、`threads=48`。
- `on` = 当該 holdout の正しい descriptor。`off` = descriptor を渡さず静的既定選択
  (`stock_common` 固定)。`swapped` = 同じ holdout 集合の別条件の descriptor (derangement、
  自己対応なしの置換、対応表は実走者・エージェントへ非公開)。
- コード側の実体: `HOLDOUTS`/`DERANGEMENT` (`orchestrator/campaign/s8b_holdout_freeze.py:80-112`)、
  `ARMS=("on","off","swapped")` (`orchestrator/campaign/s8c_arm_inputs.py:33`)。

**実装状況 (C01/C02、段3 lensB の4段階評価)**:

| 段階 | 状態 | 根拠 |
|---|---|---|
| 足場 | あり。`FORMAL_WORKLOADS`、1m/48 threads の scale 検査が存在 | `p3_autonomous_workload_trial.py:218-242,710-793` |
| 到達可能性 | 限定的。arm binding (二層 digest) の足場はあるが、`s8c_arm_inputs.py` の ARMS 定義は
  「autonomous runner にも completeness consumer にも import されない意図的な leaf module」であり
  **未配線** | `s8c_arm_inputs.py:2-6`、`docs/phase3-8c-preregistration.md:204-212,388-402` |
| 充足証明 | ない。C02 (非干渉性: off arm の payload が真の holdout を跨いで byte 同一) は
  「本書の発効時点でこの性質は成立していない」と明記 | `docs/phase3-8c-preregistration.md:96-109` |
| 正式受理 | 不可。`_preflight_workload_profile()` が拒否 | `p3_autonomous_workload_trial.py:883-896` |

---

## 3. holdout (rr80/rr20) の定義と凍結状況

- 未既知性確認手続き (三軸正規表現による全件検索) は定義済み (`phase3-8b-descriptor-design.md:106-129`)。
  8c 側では実走直前の再実行が必須、証跡は自己参照しない専用パスへ置く (`8c-preregistration.md:170-176`)。
- v1 freeze は**存在する**: `output/s8b-freeze/holdout_freeze.json` (H1/H2・derangement・
  `confirmed_by`/`confirmed_at` あり、`confirmed_at=2026-07-16`)。ただし `floor=null`、
  `budget=null`。
- **v2 candidate producer は実在する** (段3 lensA が段2 plan の誤断定を訂正): CLI
  `generate-v2-candidate` とその実装が存在する
  (`s8b_holdout_freeze.py:1681-1761,1849-1861,1874-1915`)。しかし official floor が前提であり
  (`s8b_holdout_freeze.py:1409-1410`)、**ratified な active freeze としての発効・承認は未成立**。
  `output/s8b-freeze-candidates/` (v2 格納想定パス) は不在。
- v2 candidate の格納パスに**実装間の食い違い**がある: 実装定数は `output/s8b-freeze-candidates/...`
  を指す一方、restart runbook は `output/s8b-freeze/holdout_freeze.v2.g{N}.json` と書く
  (`s8b_holdout_freeze.py:47-61`、`phase3-8b-restart-runbook.md:258-268`)。

---

## 4. rr80/rr20 calibration

**未充足。** T-425 の 2026-08-20 再監査が、登録済み calibration は rr50 向けであり rr80/rr20 向けの
calibration が未登録であると記録している
(`output/insights/2026-08-20_t425-dependency-reaudit/README.md:22-26,34-61`)。
oracle v2 実走前には verified calibration・contract 一致・attestation receipt が必須
(`orchestrator/campaign/s8b_oracle_driver.py:910-978`)。g1→g2 の環境契約活性化は human lockstep 待ち
(`docs/decisions.md:18175-18186,22358-22366`)。

---

## 5. floor / oracle prerequisite (8b §6 の12条件、C01〜C12 個別4段階評価)

**8b floor 判定方式そのものが 2026-08-18 に再凍結された** (D496系、`phase3-8b-descriptor-design.md
§10`)。「対象別 floor 超過」から「同一 campaign 内 paired 差分統計」へ変更。**この改訂は仕様のみ
発効し、判定器・attempt registry・judge の実装は別 wave 待ちという epoch 境界が明記されている**
(§10.6: 「追随実装の発効前に走った run は legacy・exploratory であり、後から formal へ昇格・
再解釈・混合しない」)。

8c-preregistration.md §6 の 12 前提条件 (現物、`condition-freeze.v1.g10.json` まで存在するが
**発効の有無は record 単体からは確定できない**、段3 lensA 指摘)。段3 lensB の指摘に従い、
「足場」「到達可能性」「充足証明」「正式受理」の4段階で個別評価する:

| 条件 | 内容 | 足場 | 到達可能性 | 充足証明 | 正式受理 | 根拠 |
|---|---|---|---|---|---|---|
| C01 | H1/H2 workload定義・scale | あり | あり | — | 未成立 (formal profile拒否) | `p3_autonomous_workload_trial.py:218-242,710-793,883-896` |
| C02 | off/swapped arm・非干渉性 | あり (二層digest) | 部分的 | **ない** (非干渉性未成立) | 未成立 | `phase3-8c-preregistration.md:96-109,204-212,388-402` |
| C03 | 6cell manifest・append-only registry | genericな機構はあり | 6cellのP/C束縛は未証明 | ない | 未成立 (`schedule.v1.json`不在) | `p3_autonomous_workload_trial.py:1123-1199`、`8c-preregistration.md:213-217` |
| C04 | crash時 attempt registry整合 | p3側stateはあり | 8bのfreeze-wide registryと不一致 | ない | 未成立 | `8c-preregistration.md:82-87,218-225` |
| C05 | schedule・master seed・arm順序の固定 | — | — | 確認できず | 未登録 | `8c-preregistration.md:226-227` |
| C06 | 累積ベンチ実時間予算consumer | registered-effective branchにconsumer実在 | formal admissionから到達不能 | ない | 未成立 | `p3_autonomous_workload_trial.py:1740-1803` |
| C07 | paired反復判定パラメータ+judge+3表 | 評価器はdispatch対象 | 到達可能 | **充足経路0** (judge条件・パラメータ未確定) | 未成立 | `8c-preregistration.md:231-239,303-317,328-337` |
| C08 | 内容commit・発効commit・HEAD三者束縛 | reportにP/C欄あり | 欄はある | 意味的束縛の証明なし | 未成立 (機械検査対象外) | `p3_autonomous_workload_trial.py:3270-3297`、`8c-preregistration.md:388-394` |
| C09 | 層3材料レポート必須配線 | layer3 renderer実装済み | 任意CLIのみ | ない | 未成立 (acceptance未配線) | `8c-preregistration.md:246-247,442-460` |
| C10 | proof chain / cross-binding authority | supervisorがpath/hash保持 | path/hash保有のみ | cross-binding未成立 | 未成立 | `8c-preregistration.md:248-250,456-465` |
| C11 | generation予算 (exact G=2) | 上限機構+3入口validatorあり | 到達可能 | **下限G=2は強制しない** | 未成立 (CLI既定値は1) | `p3_autonomous_workload_trial.py:138-139,464-472,4694-4708` |
| C12 | 計測環境allocation binding | reservation consumer実在 | 8c起動経路から到達しない | ない | 未成立 | `8c-preregistration.md:257-265,419-423` |

**SATISFIABLE_CONDITION_IDS は現時点で空集合であり、いずれかの評価器が誤って充足を返しても
実行時に不充足へ倒す関門が働く** (`8c-preregistration.md:328-337`)。12条件のうち機械的に
「充足」を返す経路は現時点で0。

**D581 (2026-08-20) の影響**: 公式 `s8b_floor_campaign.py` の事前登録儀式 (official mode) を
「粗い provenance で足りる」へ緩和した (`docs/decisions.md:23453-23482`)。ただし
**T-425 の `between_run_floor.py` (2026-08-18再凍結の paired 差分測定を担う別スクリプト) への
機械的適用は未検証** — 混同しないこと
(`output/insights/2026-08-20_t425-dependency-reaudit/README.md:55-61`)。

**T-425 (2026-08-20再監査) の結論、当日時点で不変と明記**: 公式 H1/H2 実験の起票は
(a) T-424/T-272 の要求全体閉包、または (b) D145 決定5の明示的再訪裁定、かつ
(c) rr80/rr20 calibration 登録 (human lockstep) が揃うまで不可。T-424/T-272 は「実装ゼロ」ではなく
**部分実装で未閉包** (段3 lensA が段2 plan の粗い表現を訂正、`job_script_sha256` の紐付け欠落等)。
(`docs/archive/worklog-phase3-0820-731.md:121-134`、
`output/insights/2026-08-20_t425-dependency-reaudit/README.md:63-91,156-176`)。

---

## 6. 必要な human lockstep (実行主体を明示分離、段3 lensB 指摘4の反映)

D356 (`docs/decisions.md:15565-15587`, 2026-08-13): **oracle spec の人間承認は現状機械強制されて
いない。機械が確認できるのは「人間が staged diff を review した」までであり、それ以上を
「機械確認した」と書いてはならない。** `confirmed_by`/`confirmed_at` も非空文字列として記録される
だけで人間の身元・承認そのものを機械証明しない (`s8b_holdout_freeze.py:817-820`)。

| # | 内容 | 実行主体 | 根拠 |
|---|---|---|---|
| 1 | rr80/rr20 calibration の登録 | **人間** | `output/insights/2026-08-20_t425-dependency-reaudit/README.md:22-26` |
| 2 | g1→g2 環境契約 activation | **人間** | `docs/decisions.md:18175-18186,22358-22366` |
| 3 | T-424/T-272 の要求全体閉包、または D145 決定5 の明示的再訪裁定 | **人間 (ユーザー裁定)** | `docs/archive/worklog-phase3-0820-731.md:127-134` |
| 4 | paired judge の `n`/`delta_min`/`sd_max` を結果閲覧前に確定し、judge実装後に8b再凍結+承認 | **人間 (承認) + 実装 (Codex author、別wave)** | `phase3-8b-descriptor-design.md:466-484` |
| 5 | 6-cell manifest・schedule・registry・二段commit bindingの確定 | **人間 (承認) + 実装** | `8c-preregistration.md:213-265,497-519` |
| 6 | oracle spec の staged diff review | **人間**。機械が代替できるのは receipt の存在確認までであり、承認そのものではない | `docs/decisions.md:15567-15587` |
| 7 | scope-B Q3 運用ガード (ノード単独性、T-139 非稼働確認、裁定優先順位) | **人間 + 実行前チェック (Codexが確認、判断は人間)** | `docs/phase3-8b-restart-runbook.md:19-28` |

**AI (Codex/Claude) が行ってよい範囲**: receipt・artifact の存在確認、file:line 根拠の提示、
到達可能性の静的検査、欠落の列挙。**充足の断定・承認 bytes の生成はしない** (本 wave 自身がこの
原則の下で書かれている)。

---

## 7. 期待 artifact (存在確認、pilot/formal を混同しない)

**存在するもの (探索/pilot 系および凍結済み世代 record)**:

- `output/s8b-freeze/holdout_freeze.json` (v1、2026-07-16 confirmed、floor/budget は null)
- `output/s8b-freeze/floor_protocol.json`
- `output/s8b-freeze/selector_predictions.json` (freeze hash を参照)
- `output/s8c-preregistration/arm-inputs/freeze.v1.json`
- `output/s8c-preregistration/arm-inputs/off-neutral-descriptor.v1.json` (read_ratio=50%、off arm用)
- `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json` 〜 `g10.json`
  (世代 record。**g10 が現に active/effective かは本 audit では確定していない**)

**不足・不在のもの (正式受理に必要だが repo 上に確認できないもの)**:

- `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` (実装定数側の想定パス)
- `output/s8b-freeze/holdout_freeze.v2.g1.json` (restart runbook 側の想定パス — 両者が食い違う)
- `output/s8b-freeze-budget-approvals/g1.json`
- `output/s8c-preregistration/schedule.v1.json`

**pilot 専用 (formal proof chain とは別物、混同しないこと)**:

- `output/exploration/autonomous-trials/<trial-id>/` — p3 CLI の既定出力先。8c-preregistration.md
  前提条件10は「現状 `output/autonomous-trials/` は正式proof chainではない」と明記
  (`8c-preregistration.md:248-250`)。

---

## 8. exact submission command

**正式 H1/H2 の単一の exact submission command は存在しない。** 既存 CLI は次の3系統の部品であり、
統合された投入コマンドはない。p3 pilot CLI の formal profile は事前検証 (`_preflight_workload_profile`)
で拒否されるため、これを formal submission command と呼ばない。

| 系統 | CLI | 用途 | 根拠 |
|---|---|---|---|
| holdout | `search` / `generate` / `verify` / `generate-v2-candidate` | freeze 生成・検証 | `s8b_holdout_freeze.py:1864-1919` |
| oracle | `gate-check` / `run-block` | oracle 実走 (manifest必須) | `s8b_oracle_driver.py:1829-1894` |
| p3 pilot | `p3_autonomous_workload_trial` (`--trial-id` `--provider` `--workload-profile {exploratory-ycsb-abc(既定)\|formal-holdout-legacy-v1}` 等) | 8c trial 駆動。formal profile は拒否される | `p3_autonomous_workload_trial.py:4690-4828,883-896` |

8c-preregistration.md §7 本文自身が明記: **「本節の起動形は、現時点の production では実行可能では
ない」「本系列の投入は、本節の依存をすべて閉じる別タスクとして起票する」**
(`8c-preregistration.md:520-527`)。

---

## 9. 停止条件

**正式系列の規範 (8b/8c 設計文書が定める規則)**:

- 各 cell は厳密に `G=2`、性能による早期停止は置かない (`8c-preregistration.md:91-95,497-519`)。
- crash 後の再走は freeze-wide 事前割当 attempt registry の範囲内だけ (`phase3-8b-descriptor-design.md:518-543`)。
- oracle は全 schedule 行が terminal にならなければ `protocol_violation`
  (`s8b_oracle_driver.py:1783-1803`)。exit code: `completed=0`、`refused/budget=2`、
  `protocol_violation=3`、internal error=1 (`s8b_oracle_driver.py:1852-1871`)。
- role 応答の schema 違反は再試行しない (cell を停止)。screen-reject・timeout も除外せず
  `screen_outcome`/`excluded_reason` を付けて全件報告する (`phase3-8b-descriptor-design.md:143-151`)。
- 累積ベンチ実時間予算不足時は、未実施 arm を**対称的に**判定不能へ倒す (`8c-preregistration.md:228-230`)。

**現行 p3 実装との食い違い (正式停止条件とは一致しない)**:

- `MAX_APPROVED_GENERATIONS=2` は**上限**であり、`G=2` の**下限強制ではない**
  (`p3_autonomous_workload_trial.py:134-139,464-472`)。
- CLI 既定値は `G=1` (`p3_autonomous_workload_trial.py:4694-4708`)。
- supervisor wall budget により次 generation を開始せず途中停止できる (`:3491-3508`)。
  wall budget は bench 実時間予算の代替ではない (`phase3-s8c-autonomous-trial-runbook.md:221-225`)。
- `stop_reason != continue` でも途中停止する (`:3817-3819`)。

なお `docs/phase3.md:490-498` (D114 由来記述) は「承認上限 `MAX_APPROVED_GENERATIONS=1`」と書くが、
現行コード実値は `2` (`docs/decisions.md:17149-17190` の D410 系が上限2への変更を記録)。
**phase3.md 本文は古い可能性があり、この epoch 不一致自体を別途 docs 更新候補として扱うべきである**
(本 wave の scope 外、記録のみ)。

---

## 10. blocker 要約表

| 項目 | 現状 | 主要根拠 | 次の一手・実行主体 |
|---|---|---|---|
| §5 記入欄 | 9項目中8項目が未記入 (検定4点のみ記入=no_hypothesis_test) | `8c-preregistration.md:185-197` | 人間: env owner・seed・manifest・paired parameter確定。judge実装後に限る |
| §6 充足判定 (C01-C12) | 充足を返す経路0、5条件は機械検査対象外 | `8c-preregistration.md:303-317,328-337` (本書§5の表) | 人間+実装: active epoch確定 → 各条件のproduction consumer実装 |
| H1/H2 正式admission | 足場はあるが `_preflight_workload_profile()` が明示拒否 | `p3_autonomous_workload_trial.py:883-896` | 人間: 8c事前登録の発効条件を満たすまで着手しない |
| on/off/swapped 非干渉性 (C02) | arm binding足場はあるが非干渉性は「成立していない」と自己申告 | `8c-preregistration.md:96-109` | 実装 (Codex author、別wave): payload閉包の是正 |
| rr80/rr20 calibration | 未登録 (rr50向けのみ登録済み) | `output/insights/2026-08-20_t425-dependency-reaudit/README.md:22-26` | **人間**: calibration実測・登録 |
| v2 holdout freeze | producerは実在するが ratified active発効は未成立、path定数も実装間で食い違う | `s8b_holdout_freeze.py:47-61,1681-1761`; `phase3-8b-restart-runbook.md:258-268` | 人間+実装: official floor確定 → v2生成 → 承認 |
| floor 判定方式 | 2026-08-18再凍結は仕様のみ発効、判定器/registry/judge実装は別wave待ち (epoch境界) | `phase3-8b-descriptor-design.md §10.6` | 実装 (Codex author、別wave): judge・3表・validatorの実装 |
| oracle 実走 | official floor必須、v1 freezeはfloor/budget null | `s8b_oracle_driver.py:1409-1410`; `holdout_freeze.json` | 人間+実装: floor確定後にoracle実走を別wave起票 |
| exact G=2 下限 | 上限機構のみ、CLI既定は1、途中停止可 | `p3_autonomous_workload_trial.py:138-139,4694-4708` | 実装 (Codex author): 下限consumer新設は別途裁定 |
| 6-cell manifest / schedule / registry | prereg上必須だが `schedule.v1.json` 不在 | `8c-preregistration.md:213-217` | 人間+実装: manifest/schedule/registry権威の確定 |
| T-424/T-272 / D145 | 部分実装、job-result bindingなど未閉包 | `output/insights/2026-08-20_t425-dependency-reaudit/README.md:63-91` | **人間 (ユーザー裁定)**: 全閉包かD145決定5再訪の選択 |
| scope-B / Q3 ガード | 手順は正本化済み。T-139稼働状態は本waveでは未確認 | `phase3-8b-restart-runbook.md:19-28` | **要再監査**: T-139状態・scope-B land確認 (別セッション) |
| oracle spec 人間承認 | staged diff review以上は機械強制不可 | `docs/decisions.md:15565-15587` | **人間**: reviewそのもの。AIは受理bytes生成をしない |
| T425/T972/T1438/T1458 | ListAgents実測で稼働中確認、H1/H2前提整備との高確度な並行作業 | 本書§1 | 各waveのland待ち。本waveは着手しない (read-only) |
| T1371 | worktree実在・未クローズ、生存プロセス未確認 | `git worktree list`, `docs/worklog.md` | 要再確認 |

---

## 一次資料索引

- `docs/phase3-8b-descriptor-design.md` (H1/H2定義、on/off/swapped、floor判定方式)
- `docs/phase3-8c-preregistration.md` (8c事前登録、§5/§6/§7、epoch履歴)
- `docs/phase3-8b-restart-runbook.md`
- `docs/phase3-s8c-autonomous-trial-runbook.md`
- `docs/phase3.md:19-37,411-529` (現行チェックポイント、H1/H2位置づけ)
- `docs/decisions.md` D356 (15565)、D496系 (20614,21225)、D410系 (17149)、D555 (22604)、
  D581 (23453) ほか
- `docs/worklog.md` (次の一手 T425/T972/T1371/T1438/T1458)
- `docs/archive/worklog-phase3-0820-731.md` (T-425 2026-08-20再監査)
- `output/insights/2026-08-20_t425-dependency-reaudit/README.md`
- `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-10-scope-b-reopen.md` (scope-B裁定一次控え)
- `orchestrator/campaign/s8b_oracle_driver.py`、`s8b_holdout_freeze.py`、`s8c_arm_inputs.py`、
  `p3_autonomous_workload_trial.py`
- 段2/段3 codex 記録: `verbatim/s2-plan.md`、`verbatim/s3-lensA-sol.md`、`verbatim/s3-lensB-luna.md`
- 親裁定: `s4-adjudication.md`
