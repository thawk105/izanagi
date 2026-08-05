結論は **DW-G04 不成立、docs-only** である。段 1 前提実測 6 件を静的に再照合したが、反証は見つからなかった。read-only のため変更・テスト実走は行っていない。

## 1. 権威境界の骨子

新 D は次の条文とする。

1. **宣言と判定を分離する。** producer が宣言できるのは、利用意図を示す閉集合 `declared_use_class ∈ {official, exploration, qualification, dry}` と、raw な実行事実・証拠 pointer だけである。`qualification` は「適格性審査へ提出する」という意味であり、合格宣言ではない。

2. **producer に適格性宣言を許さない。** 新しい qualification raw receipt は closed schema とし、`eligibility_status`、`pairing_valid`、`rf_acceptance_status`、`recovery_measurement_eligibility`、`research_goal_eligible`、`pipeline_eligible` および validator identity/result の混入を未知 field として拒否する。D127 が自己申告 enum は検出器ではないとした境界にも従う (`docs/decisions.md:6252-6256`)。

3. **適格性権威は独立 validator だけが持つ。** validator は producer から合否値や加工済み object を受け取らず、永続化済み raw receipt の path を起点に bytes・hash・closure を自ら読み直し、schedule、全 attempt、allocation/accounting、測定 checkout、correctness、raw throughput を再計算する。

4. **consumer は validator decision だけを読む。** decision は少なくとも `eligible / ineligible / not_certifiable / invalid_receipt` の閉集合とし、consumer が通せるのは `eligible` のみとする。raw receipt や `declared_use_class` から直接分岐してはならない。`AdmittedCampaign` exact type だけを発行する既存境界が先例である (`orchestrator/campaign/artifact_admission.py:123-140,707-722`)。

5. **validator の独立性を成果物へ束縛する。** decision は validator の identity、source SHA-256、policy/schema version、全 input の path/size/SHA-256 を持つ。検査前後で bytes が変化した場合も拒否する。既存 admission decision の束縛形式は `orchestrator/campaign/artifact_admission.py:81-120,514-529,680-696` にある。

6. **凍結 ledger の三 field は entry-local な歴史的負判定として固定する。** `patches/ledger.json:12-17` の三つの `false` は、唯一の `ability_probe` entry についてだけ引き続き exact contract である。新 artifact の適格性権威には昇格させず、別 sidecar で上書きもしない。exact-one と exact 値は `orchestrator/campaign/silo_ladder_rung1_contract.py:506-521,538-564` のままとする。

7. **既存 T-126 を遡及昇格しない。** T-126 は `evidence-only/no-promotion` であり (`orchestrator/qualification/t126_control_v1.json:2-6`)、package 自体に promotion API がない (`orchestrator/qualification/__init__.py:2-5`)。既存 receipt を qualification-positive artifact と読み替えない。

8. **RF 統計を層 3 calibration へ混載しない。** RF record は `(trial_id, candidate_id, workload_id, contrast)` の exact composite key を持つ別区画に置く。既存 floor 閉表を広げないという Q11 をそのまま条文化する (`docs/archive/worklog-phase3-0803-138-139.md:369-372`)。

## 2. 識別子の名前

採用名は **`declared_use_class`** とする。裁定文の `artifact_role=qualification` は T-318 の概念軸を指すものと解し、永続 field の literal 名にはしない。

理由は、既存 `artifact_role` がすでに別軸だからである。

- `orchestrator/campaign/s8b_oracle_artifacts.py:26-29` では値が `manifest / observations / verdict`、すなわち exploration envelope 内の文書種別である。
- `orchestrator/campaign/s8b_oracle_artifacts.py:169-186` がその閉集合を検証する。
- producer も同じ値を filename と envelope に使う (`orchestrator/campaign/s8b_oracle_exploration.py:25-50`)。
- T-318 の軸は `official / exploration / qualification / dry` である (`docs/archive/worklog-phase3-0802-113-116.md:937-957`)。

T-318 を全 producer へ展開すると、oracle manifest には「文書種別=`manifest`」と「利用クラス=`exploration`」の両方が必要になる。同じ field では同居できない。D75 の教訓は、gate の各意味を実在する一意の input field へ対応させることであり (`docs/decisions.md:3031-3037`)、schema 文脈頼みの二義化は避けるべきである。

`artifact_class` も `derived-report` の別用途で既出なので採らない (`docs/ruleops.md:126-133`)。

影響範囲は次のとおり。

- 本 wave: 新 D と設計メモだけ。
- 将来の RF raw receipt: `declared_use_class="qualification"` を新設。
- 既存 `s8b_oracle_artifacts.py` の `artifact_role` は変更しない。
- T-318 全 producer 展開は brief の scope 外であり、別 wave とする。

## 3. DW-G04 判定

**今日この機構を通る positive-control producer と実 artifact path／計測 ID は示せない。したがって docs-only を推奨する。**

部分的な producer は存在する。T-126 は `tools/pegasus/t126_qualification.sh:735-744` から `t126_driver.py run` を呼び、`output/env/pegasus/qualification/t126/attempts/<attempt-id>/series-result.json` を生成する (`orchestrator/qualification/t126_driver.py:1009-1030,1212-1233`)。しかしこれは対象機構ではない。

- protocol は `subject/reference` の二者だけである (`orchestrator/qualification/t126_control_v1.json:28-39`)。
- `statistical_claim="none"`、authority は evidence-only である (`orchestrator/qualification/t126_series_result_schema.json:89-107`)。
- schema は closed で、結果 verifier も exact key set を要求する (`orchestrator/qualification/t126_driver.py:1265-1273`)。
- worktree の tracked inventory に `output/env/pegasus/qualification/**` の実 receipt は 0 件だった。repo 外 persistent receipt の不存在までは証明できないため、既存 T-126 schema の変更はなおさら安全といえない。

実測 ID `877859` も発火条件にはならない。

- 実 path は `output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/`。
- W2 と全 workload の verdict は 0 (`.../verdict.tsv:1-3`)。
- D126 も W2 逆転による不成立と確定している (`docs/decisions.md:6196-6208`)。
- さらに一 allocation、`J=1` で、cluster 間分散を推定できない (`output/insights/2026-08-03_t338-rf-statistical-design/package.md:144-153`)。
- D120 は負例が RF consumer の DW-G04 を満たさないと明示している (`docs/decisions.md:5756-5762`)。

したがって本 wave では機械 gate を作らず、将来は **新 version・新 namespace** に置く。これなら frozen artifact と既存 T-126 receipt の検証契約を一切変えない。

## 4. Q11 の consumer 経路

### 現在実在する入力

| 成果物 | 実在 field | 判定 |
|---|---|---|
| `.../0_877859.nqsv/throughput.tsv:1-31` | `workload / arm / rep / throughput_tps` | raw 値はあるが負例かつ `J=1` |
| `.../0_877859.nqsv/order.tsv:1-31` | `ordinal / workload / rep / position / arm` | 実現順だけ。schedule algorithm、seed、washout、cluster がない |
| frozen rung evidence | `classification.recovery_measurement_eligibility=false` 等 (`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:134-137`) | entry-local な負判定 |
| T-126 | schema 上は二者の `median_tps`、binary hash、evidence pointer がある (`orchestrator/qualification/t126_series_result_schema.json:14-39,41-71`) | tracked 実 receipt はなく、三 arm RF でもない |

`trial_id`、`candidate_id`、`contrast`、独立 `cluster_id`、measurement-start receipt、三 arm の source identity、RF preregistration、attempt と schedule の双射を表す field は、現在の実成果物には**実在しない**。

### 将来の設計

経路は次の一方向に限定する。

`raw receipts → read-only validator → hash-bound decision → sealed admission type → selector/material report`

提案する raw input は以下である。すべて新 schema の field であり、現時点では未実在である。

- `measurement_start`: `trial_id`、`candidate_id`、`prereg_commit`、`measurement_head`、`parent_family_id`、allocation receipt の path/hash。
- `schedule`: `cluster_id`、`slot`、`workload_id`、`arm_role`、`position`、washout/balance 規則、schedule hash。
- `attempts[]`: `attempt_id`、schedule slot、raw-run pointer/hash、scheduler/accounting status、correctness evidence、trace-disabled の `throughput_tps`。
- raw envelope: `declared_use_class="qualification"`。適格性 field は持たせない。

再計算規則は次の順序にする。

1. exact schema、closure、hash、measurement-start と preregistration ancestry を再検証する。全 schedule slot と全 attempt の双射を要求する。
2. arm label を信用せず、事前登録した source/binary identity へ再束縛する。既存 `trial_registry` は宣言しか証明しないため、そのまま権威には使えない (`orchestrator/campaign/trial_registry.py:2-6,124-129`)。
3. correctness anomaly は即 `ineligible`。削除・置換・再試行で消せない。infra replacement は結果観測前に外部証拠で確定し、事前登録された予備だけを許す (`docs/archive/worklog-phase3-0803-138-139.md:361-363`)。
4. 事前登録した arm 代表値から各 cluster の `D=m_stock−m_degraded`、`N=m_candidate−m_degraded`、`G=m_stock−m_candidate` を raw TPS から計算する。
5. RF は `E[N]/E[D]`、primary endpoint は trace-disabled `throughput_tps` とする (`docs/archive/worklog-phase3-0803-138-139.md:5-14`)。
6. `D>δ_D`、`N>0`、`G>0` の多重性調整済み同時信頼領域だけを eligibility に使う。Fieller を primary とし、弱い分母は `weak_denominator_not_certifiable`、`RF>1` は stock 超過であって回復合格にしない (`docs/archive/worklog-phase3-0803-138-139.md:364-366`)。
7. 約 11 cluster を含む J は実走前に固定し、結果後の追加を認めない (`docs/archive/worklog-phase3-0803-142-143.md:3-11`)。

validator 出力は次を持つ。

- composite key: `trial_id / candidate_id / workload_id / contrast`
- `eligibility_status`
- input receipt の path/size/SHA-256
- validator identity/source SHA-256/policy version
- 再計算した D/N/G、RF confidence set、family/alpha ledger binding
- `reasons[]`: `{code, input_ref, field_or_column, expected, observed}`

理由 code は少なくとも schema 不正、producer eligibility claim 混入、attempt/schedule 非双射、arm identity 不一致、correctness anomaly、不正な置換、性能欠測、弱い分母、同時領域不成立を区別する。

## 5. 変更計画

### 本 waveで行う変更

1. `[new] docs/spool/decisions/2026-08-05-dev-wave-t337-qualification-authority-1.md`

   `docs/spool/README.md:24-49` と `docs/spool/decisions/README.md:1-34` に従い、`{{D:t337-qualification-authority}}` として第1節の条文を記録する。`docs/decisions.md` は直接編集しない。

2. `[new] output/insights/2026-08-05_t337-qualification-authority/mechanization-design.md`

   第4節の proposed schema、validator decision、consumer 型、DW-G04 未達、将来の発火条件を「未実装設計」として保存する。

3. production code、schema、test、frozen artifact は変更しない。

### live positive artifact が得られた後の実装候補

以下は T-339 相当の後続であり、本 wave では作らない。

- `[new] orchestrator/qualification/rf_measurement_receipt_schema.json`: eligibility field を含まない raw receipt の closed schema。
- `[new] orchestrator/qualification/rf_eligibility_decision_schema.json`: validator-only decision と structured reasons。
- `[new] orchestrator/qualification/rf_contract.py`: composite key、D/N/G、Fieller・同時領域、閉じた status/reason 型。
- `[new] orchestrator/qualification/rf_trial_registry.py`: append-only attempt/RF registry。`trial_registry.py:725-879` の fsync・prefix-extension 型だけを参照し、既存 8c registry へ混載しない。
- `[new] orchestrator/qualification/rf_validator.py`: raw path を自力で読み、decision を再計算する read-only authority。
- `[new] orchestrator/campaign/rf_qualification_admission.py`: validator だけが生成できる immutable `QualifiedArtifact` を発行する consumer 境界。
- `[new] orchestrator/qualification/rf_trial_driver.py` と新 Pegasus submit/run script: live producer が確定してから raw facts のみを出力。
- `[new] orchestrator/tests/test_rf_qualification_*.py`: schema、双射、arm binding、correctness terminal reject、sealed consumer を検査。

現在 RF consumer 自体が存在しない (`output/insights/2026-08-03_t338-rf-statistical-design/package.md:291-310`) ため、selector/material-report の既存 hook を file:line で指定することはできない。存在しない hook を仮定して配線計画を書くことは DW-O13/D75 違反になる。

### 触ってはならない file

- `patches/ledger.json`
- `patches/silo_ladder_rung1.patch`
- `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json`
- `orchestrator/campaign/silo_ladder_rung1_contract.py`
- `orchestrator/campaign/silo_ladder_rung1.py`
- 既存 `orchestrator/qualification/t126_*` と T-126 schema
- `orchestrator/campaign/s8b_oracle_artifacts.py`
- `orchestrator/campaign/trial_registry.py`
- 層 3 calibration/floor の既存 schema・閉表
- `docs/decisions.md` の直接編集面

## 6. 変異事前登録候補

**対象外。** 本 wave は docs-only で機械 gate を新設しないため、無効化できる gate も赤になる test node もない。後続実装時は live positive artifact と実 consumer が揃った段階で、実際の production 呼出し線を確認してから別途事前登録する。

## 7. 正しさへの影響

この設計は受理集合を緩めない。

- frozen entry の三つの `false` と exact-one contract を維持し、sidecar override を作らない。
- `declared_use_class="qualification"` は審査への routing にすぎず、合格条件にならない。
- consumer は raw producer object を受けず、validator が発行した exact sealed type だけを受理する。
- missing field、未知 field、hash drift、attempt 欠落、弱い分母、判定不能はいずれも非受理になる。
- correctness anomaly は終端 reject とし、解析集合から除外して成功 attempt に置換できない。
- 全 attempt の双射と候補系列の alpha ledger により、成功した試行だけの選別を防ぐ。

producer 自己申告を権威にすると、具体的には request `877859` の W2 失敗を省略して `rf_acceptance_status=eligible` と書く、mode1/mode2/stock の arm label を入れ替える、correctness 不合格 attempt を欠測扱いで捨てる、schedule が崩れていても `pairing_valid=true` とする、測定 checkout を別 binary のものへ付け替える、といった偽装が可能になる。これは規律 2 への直接攻撃である。

## 総括

- **DW-G04:** live positive producer・実 receipt・consumer がなく、判定は **docs-only**。
- **最大の設計リスク:** producer の利用クラス宣言が validator decision へ無再計算で昇格し、恒真 gate になること。
- **段 4 の択一:** T-318 の語を概念軸と解して `declared_use_class` を採るか、既存文書種別と衝突する literal `artifact_role` を再利用するか。前者を推奨する。