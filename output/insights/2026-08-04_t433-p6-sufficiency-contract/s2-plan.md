# [T-433] 段 2 プラン案 — P6「実装済み」認定の意味的充足契約

結論は、11 条項からなる人間 gate 契約を起草し、V1 は択 (a) を推奨する案である。P6 の 4 値実行結果と、D150 の `NOT_IMPLEMENTED` / `NOT_CLAIMED` は別の型として維持する。一次資料 5 件はすべて読了した。

## 1. README の節構成

| 節 | 題 | 要点 |
|---|---|---|
| 0 | 文書の地位 | D138・D150 の追補案。実装、機械 gate、status field、cap-lift は作らない |
| 1 | 認定対象と型境界 | P6 の 4 値結果と、非適用理由 2 語、人間の認定判断を分離 |
| 2 | 入力 field の実在確認 | 現存 field、現存するが P6 証拠にならないデータ、将来作るデータを区別 |
| 3 | 意味的充足の必須条項 | 11 条項と検査可能度を定義 |
| 4 | 正負 calibration | 具体的な入力・期待 verdict・データの現存性を列挙 |
| 5 | 偽物の棄却条件 | 最低 5 種の偽物がどの case で落ちるかを固定 |
| 6 | 限界効果変異表 | 全必須条項と、判定を反転させる変異を 1 対 1 以上で対応 |
| 7 | 独立検査者 | 読むもの、再計算するもの、自分で走らせるもの、証拠に数えないもの |
| 8 | V1 裁定案 | 択 (a)/(b)/(c) を比較し、択 (a) を推奨 |
| 9 | 択一 | V1 以外に判断が割れうる 2 点を提示 |
| 10 | 書かないもの・決めないもの | 実装 wave、T-434、T-435、および既存未定義事項との境界 |

根拠となる空白は [D150:7436–7452](/work/1/SFC/tanab/izanagi/docs/decisions.md:7436)、ユーザー裁定は [brief.md:10–22](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:10) と [worklog.md:1552–1564](/work/1/SFC/tanab/izanagi/docs/worklog.md:1552) にある。

## 2. 文書の地位と型境界

README 冒頭には次を規範文として置く。

- 本契約は D150 決定 (6)(a) の空白だけを埋め、D138・D150 を supersede しない。
- 認定対象は「申請された revision の P6 実装が D138 の意味を実際に実現するか」である。ファイルや test の存在確認ではない。
- P6 handler の結果は `P6Derived | P6NotDerived(code) | P6NotApplicable(code) | P6ContractError(code)` の 4 値を維持する。[P6 README:116–136](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:116)
- `NOT_IMPLEMENTED` / `NOT_CLAIMED` は非適用理由の分類であり、4 値結果ではない。[D150:7396–7409](/work/1/SFC/tanab/izanagi/docs/decisions.md:7396)
- 意味的充足を認定しても、それだけで `NOT_CLAIMED`、P6 充足、cap-lift 承認のいずれも成立しない。
- 証拠不足時は状態を `NOT_IMPLEMENTED` に捏造せず、承認を保留する。[D150:7413–7425](/work/1/SFC/tanab/izanagi/docs/decisions.md:7413)
- `MAX_APPROVED_GENERATIONS = 1`、verifier 必須条項、exact cut の独立性は不変。[P6 README:299–324](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:299)

## 3. DW-O13 — 入力 field の実在台帳

裸の `anomalies` は禁止する。

| データ | 実 field / 定義 | 今日の状態 |
|---|---|---|
| WAL 外形 | `variant`, `stage`, `env_tag`, `ts`, `payload`。[model.py:90–102](/work/1/SFC/tanab/izanagi/orchestrator/campaign/model.py:90) | 存在する |
| verify 件数 | `stage="verify_done"` の `payload.anomalies`。値は `len(vr.anomalies)` の整数。[pipeline.py:778–796](/work/1/SFC/tanab/izanagi/orchestrator/campaign/pipeline.py:778) | 存在する。witness list ではない |
| cycle witness | terminal `stage="abort"` の `payload.verify.anomalies[]`。[pipeline.py:797–807](/work/1/SFC/tanab/izanagi/orchestrator/campaign/pipeline.py:797)、[report.py:42–75](/work/1/SFC/tanab/izanagi/orchestrator/verifier/report.py:42) | schema は存在する |
| cycle 内部 | `phenomenon`, `length`, `cycle`, `edges[].from/to/types/reasons[]`, `reasons[].type/key/u_ver/v_ver`。[report.py:15–39](/work/1/SFC/tanab/izanagi/orchestrator/verifier/report.py:15) | 存在する |
| attempt 束縛 | `build_start.payload.build_attempt_id` と `abort.payload.build_attempt_id`。[pipeline.py:552–563](/work/1/SFC/tanab/izanagi/orchestrator/campaign/pipeline.py:552)、[pipeline.py:620–639](/work/1/SFC/tanab/izanagi/orchestrator/campaign/pipeline.py:620) | 存在する。ただし `verify_done` には無い |
| integrity counters | `payload.verify.integrity.lock_coverage_violations`, `write_intent_violations`, `permutation_violations`。[report.py:58–70](/work/1/SFC/tanab/izanagi/orchestrator/verifier/report.py:58) | schema は存在する |
| canonical 5-bit 候補 | `TriggerGateIR.mask`、`SCHEMA_ID="izanagi-trigger-gate-ir/v1"`、5 文字 wire。[reflux_ir.py:19–23](/work/1/SFC/tanab/izanagi/orchestrator/campaign/reflux_ir.py:19)、[reflux_ir.py:78–114](/work/1/SFC/tanab/izanagi/orchestrator/campaign/reflux_ir.py:78) | コードは存在するが P6 artifact へ未束縛 |
| P6 固有入力 | `PrecommittedHypothesis`, validation plan、origin、axis、enforcement。[P6 README:116–127](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:116) | 将来実装が作る |
| P6 出力 | `forbidden_candidate_keys`, `marginal_keys`, `witness_class_set` 等。[P6 README:254–270](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:254) | 将来実装が作る |
| 構造化 IntegrityWitness | lock/write-intent/permutation 各 witness | 存在しない。[P6 README:158–180](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:158) |

今日ある cycle の具体例は [wal.jsonl:6–7](/work/1/SFC/tanab/izanagi/output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/runs/wal.jsonl:6) だが、trace を差し替えた fixture で variant 帰属は偽である。[p3_s4_red.py:13–23](/work/1/SFC/tanab/izanagi/orchestrator/campaign/p3_s4_red.py:13) したがって field 形状の見本には使えても、P6 正例の実証には数えない。

integrity の実測 counter は存在する。

- lock: `lock_coverage_violations=1016002`。[s3_lock_coverage.json:17–26](/work/1/SFC/tanab/izanagi/output/env/linux-baremetal/calibration/s3_lock_coverage.json:17)
- write-intent: `write_intent_violations=153968`。[t152_write_intent_coverage.json:130–154](/work/1/SFC/tanab/izanagi/output/env/pegasus/characterization/t152_write_intent_coverage.json:130)
- permutation: `permutation_violations=249252`。[s5_permutation_coverage.json:16–25](/work/1/SFC/tanab/izanagi/output/env/linux-baremetal/calibration/s5_permutation_coverage.json:16)

ただし、いずれも P6 が比較・外挿できる構造化 witness ではない。

## 4. 意味的充足の必須条項と検査可能度

| ID | 必須条項 | 分類 |
|---|---|---|
| SC-01 | stage 修飾 field だけを読み、ordered WAL 上で `variant`・`env_tag`・workload・attempt を束縛する。曖昧なら `P6NotDerived(ambiguous-wal-binding)` | 機械検査できる |
| SC-02 | evidence を CycleWitness と 3 種の IntegrityWitness の閉じた和とし、4 adapter 全部に正の到達例を要求する。未知 kind は `P6ContractError(unknown-witness-kind)` | 定義後ならできる |
| SC-03 | cycle の長さ、辺の隣接、reason、rotation 正規化、key/version 同値関係、複数 anomaly の class-set、切詰めを検査する。[P6 README:182–207](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:182) | 定義後ならできる |
| SC-04 | `hypothesis` は source failure 前に hash 固定され、`extrapolation_set` は非空。反証 test・evidence plan を持つ。[P6 README:209–226](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:209) | 定義後ならできる |
| SC-05 | `P6Derived` は `B \ C_exact != ∅` の場合だけ。`marginal_keys` はその差集合と完全一致し、空なら `P6NotDerived(no-marginal-effect)`。[P6 README:228–235](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:228) | 機械検査できる |
| SC-06 | 事前登録した反証 test が失敗したら `P6NotDerived(hypothesis-falsified)` とし、origin を seal する。仮説差替えは禁止 | 定義後ならできる |
| SC-07 | handler は全入力で 4 値のいずれかを返し、固定 corpus と検査者生成の新鮮な metamorphic case の双方で exact verdict を返す。case ID は handler 入力に渡さない | 定義後ならできる |
| SC-08 | qualifying red の exact cut は P6 より先に独立 append し、P6 の失敗で外さない。禁止外候補も通常 verifier を必ず通す | 定義後ならできる |
| SC-09 | 4 値結果と D150 の状態語を混同しない。意味的認定済みで明示的非主張の run だけが `NOT_CLAIMED` 候補になる。欠落・曖昧を既定の `NOT_CLAIMED` にしない | 人間 gate |
| SC-10 | 独立検査者が申請者と別 context で再計算・再実走する。申請者の宣言、path 名、test node 名は証拠 0 | 人間 gate |
| SC-11 | 全必須条項に最低 1 個の判定反転変異を対応させる。生存変異があれば認定不可。反転変異を書けない条項は恒真として削除 | 定義後ならできる |

## 5. 正負 calibration の具体ケース

候補キーは将来 fixture 上で、`k0=("izanagi-trigger-gate-ir/v1","00000")`、`k1=("izanagi-trigger-gate-ir/v1","10000")` とする。

| case | 入力と期待 verdict | データの所在 |
|---|---|---|
| C-01 Derived-cycle | `verify_done.payload.anomalies=1`、`abort.payload.verify.verdict="non-serializable"`、`integrity.clean=true`、`anomaly_count=total_cycles=1`、有効な G2 witness。`C_exact={k0}`, `B={k0,k1}`。期待は `P6Derived`、`forbidden_candidate_keys={k0,k1}`、`marginal_keys={k1}` | field schema は今日存在。candidate-bound の正例、hypothesis、matrix は将来実装が作る |
| C-02 rotation | C-01 の `cycle` と `edges` を同じ向きのまま rotation。期待は C-01 と同じ `witness_class_set` と禁止集合 | 将来検査者が C-01 から生成 |
| C-03 no-marginal | C-01 と同じ witness だが `C_exact={k0,k1}`, `B={k0,k1}`。期待は `P6NotDerived(no-marginal-effect)` | 将来実装が作る |
| C-04 late-precommit | C-01 の `hypothesis` 固定時点を source failure 後へ移す。期待は `P6ContractError(precommit-order-invalid)`、generalized cut なし | 将来実装が作る |
| C-05 falsified | C-01 の事前登録 paired test に反証例を 1 件置く。期待は `P6NotDerived(hypothesis-falsified)` と origin seal | 将来実装が作る |
| C-06 truncated | `abort.payload.verify.total_cycles=2`、`anomaly_count=1`、`len(anomalies)=1`。期待は `P6NotDerived(witness-truncated)` | field は今日存在。case は将来生成 |
| C-07 invalid-witness | `length=3` だが `len(cycle)=2`、または `edges[].from/to` が隣接不一致。期待は `P6NotDerived(witness-invalid)` | field は今日存在。case は将来生成 |
| C-08 unknown-kind | 閉じた和に無い witness constructor を adapter seam へ渡す。期待は `P6ContractError(unknown-witness-kind)`、origin seal、source の exact cut は維持 | discriminator と fixture は将来実装が作る。現時点で実 field 名を捏造しない |
| C-09 environment | `abort.payload.reason="trace-timeout"` で `payload.verify` なし。期待は `P6NotApplicable(non-candidate-failure)` | 今日の実例が [wal.jsonl:3](/work/1/SFC/tanab/izanagi/output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/runs/wal.jsonl:3) に存在 |
| C-10L lock adapter | candidate-bound の構造化 lock witness、`lock_coverage_violations>0`、C-01 と同じ非空 marginal setup。期待は `P6Derived` | raw counter は今日存在。構造化 witness と正例は将来実装が作る |
| C-10W write adapter | candidate-bound の構造化 write-intent witness と非空 marginal setup。期待は `P6Derived` | raw counter は今日存在。構造化 witness と正例は将来実装が作る |
| C-10P permutation adapter | candidate-bound の構造化 permutation witness と非空 marginal setup。期待は `P6Derived` | raw counter は今日存在。構造化 witness と正例は将来実装が作る |
| C-11 claim pair | 同じ revision・origin・運転構成で、明示的非主張 run は `NOT_CLAIMED` 候補。claim を有効にして C-01 を与えた run は `NOT_CLAIMED` ではなく `P6Derived` | per-run の束縛 artifact は T-434 が将来定義 |
| C-12 verifier | P6 禁止集合に無い候補を通常 verifier が `non-serializable` と判定。期待は candidate reject と exact cut append | 将来の統合 calibration |

C-10L/W/P は「counter を見たら一律エラー」の adapter を実装済みと認めないための正例である。構造化 witness が存在しない現在は、この 3 case を満たせず、P6 認定も通らない。

### 偽物の最低棄却集合

| 偽物 | 落ちる case |
|---|---|
| 空 handler | C-01 で 4 値結果を返せない |
| 常に同じ verdict | C-01 / C-03 / C-08 / C-09 の期待型・code が異なるため最低 1 件で落ちる |
| 全入力を `P6ContractError` にする blanket handler | C-01、C-03、C-09、C-10L/W/P で落ちる |
| 未知 kind を無視する実装 | C-08 で exact `P6ContractError(unknown-witness-kind)` にならず落ちる |
| 常時 `NOT_CLAIMED` | C-11 の claim 側と C-01 で落ちる |
| 全 integrity kind を安全側エラーにする adapter | C-10L/W/P の正例で落ちる |
| case ID のみを暗記する実装 | C-02 と独立検査者が生成する未公開 rotation/key-renaming case で落ちる |

## 6. 非空の限界効果を示す変異表

表の正式列は `条項ID / 変異対象 / 破壊変異 / 対応case / 無変異期待 / 変異後観測 / KILLED判定 / 検査者` とする。

| 条項 | 代表変異 | 対応 case と判定反転 |
|---|---|---|
| SC-01 | `verify_done.payload.anomalies` の整数を witness list として読む、または ordered WAL を last-wins に置換 | C-01 が Derived から error/無出力へ変わり、calibration PASS→FAIL |
| SC-02 | cycle / lock / write / permutation adapter のいずれかを空にする | C-01 または C-10L/W/P が Derived→error となり PASS→FAIL |
| SC-03 | rotation 正規化を除去 | C-02 の class/output が C-01 と不一致になり PASS→FAIL |
| SC-04 | precommit 順序検査を削除 | C-04 が ContractError から Derived へ変わり PASS→FAIL |
| SC-05 | `B \ C_exact` の空検査を恒真化 | C-03 が NotDerived から Derived へ変わり PASS→FAIL |
| SC-06 | 反証結果を無視する | C-05 が NotDerived+seal から Derived へ変わり PASS→FAIL |
| SC-07 | handler を常時 `P6Derived` に置換 | C-03/C-08/C-09 が不一致になり PASS→FAIL |
| SC-08 | P6 error 時に exact cut append を省略、または禁止外候補の verifier を skip | C-08/C-12 の side effect が反転し PASS→FAIL |
| SC-09 | claim 値を読まず常時 `NOT_CLAIMED` | C-11 の claim 側が Derived から NOT_CLAIMED へ変わり PASS→FAIL |
| SC-10 | 申請者の期待 manifest・path 名・test node 名を独立再計算の代わりに受理 | 空 handler 申請が棄却→認定へ反転するため、検査手続自体を FAIL とする |
| SC-11 | 必須条項の matrix 行を 1 行削除、または反転不能な条項を追加 | 契約完全性判定が PASS→FAIL |

排除規則は次の逐語案とする。

> 必須条項は、当該条項だけを破壊した変異によって最低 1 件の calibration 判定が PASS から FAIL へ反転しなければならない。対応変異を書けない条項、または変異が生存する条項は意味的効果を示せないため、認定根拠として使用せず契約から削除する。条項を残すために期待値を変異実装へ合わせてはならない。

## 7. 独立検査者の手続

独立性は「別名の reviewer」ではなく、申請者の期待値・会話履歴・mutable workspace を引き継がない fresh context とする。

1. 読むもの

   - D138、D150、本契約、P6 README §3.2〜§3.12。
   - handler、4 adapter、normalizer、hypothesis/validation reader、exact-cut append、enforcer、verifier 呼出しの実体。
   - ordered WAL、source failure、precommit、validation matrix の生 artifact。
   - calibration corpus と変異対応表。

2. 自分で再計算するもの

   - `verify_done.payload.anomalies` と `abort.payload.verify.anomalies` の投影。
   - variant・environment・workload・attempt・origin の束縛。
   - witness 内部整合、正規化、class-set。
   - `B`、`C_exact`、`B \ C_exact`、`marginal_keys`。
   - precommit の順序と hash、paired test の結果、seal の要否。
   - 固定表からの期待 verdict。申請者作成の expected-output file は使わない。

3. 自分で走らせるもの

   - C-01〜C-12 の exact-result calibration。
   - case ID を渡さない新鮮な rotation・key-renaming・version-shift case。
   - SC-01〜SC-11 の変異を 1 個ずつ適用した kill 確認。
   - P6 禁止外候補にも通常 verifier が走る統合 case。
   - すべて対象 revision の fresh checkout/context で行う。

4. 証拠に数えないもの

   - 申請者の「実装済み」宣言。
   - `derive_p6_cut.py` 等の path 名。
   - `test_p6_*` 等の node 名や件数。
   - 申請者が実行したというログだけ。
   - coverage 数値だけ、mutation 名だけ、receipt path だけ。
   - `P6NotApplicable` を返した事実だけ。

全 calibration の exact result、全変異の KILLED、独立再計算の一致が揃って初めて人間 gate が意味的充足を認定できる。欠落時は承認保留であり、自動的な状態再分類ではない。

## 8. V1 の比較と推奨

| 択 | U2 の保存 | ゼロ効果 loophole | 評価 |
|---|---|---|---|
| (a) per-run gate | `NOT_CLAIMED` を失敗とは数えない。ただし standing な global 許可にはしない | revision・origin・運転構成が変わるたび再判定し、非主張 run は多世代 allowance を消費しない | **推奨** |
| (b) `NOT_CLAIMED` 構成では cap を開けない | 状態上は免責を残せる | 明確に閉じるが、「構成」の範囲次第で global approval 全体を人質化しうる | 保守的だが過広 |
| (c) global 免責 | 最も字義的 | 実装だけ置いて常時非主張にすれば、限界効果ゼロのまま cap を開ける | 却下 |

D138 は exact-only の限界効果がゼロと証明している。[D138:6726–6749](/work/1/SFC/tanab/izanagi/docs/decisions.md:6726) 一方、D150 は状態分類と承認判断を分離している。[D150:7413–7425](/work/1/SFC/tanab/izanagi/docs/decisions.md:7413) この二つを同時に保存できるのが択 (a) である。

推奨文案は次のとおり。

> `NOT_CLAIMED` は実装 revision に対する standing な global cap-lift 免責ではなく、revision・origin・運転構成に束縛された個別 run の状態とする。`NOT_CLAIMED` 自体は P6 失敗に数えないが、その run に多世代 allowance を付与する積極的証拠にはしない。別 run、別 revision、別 origin、別運転構成へ持ち越さない。具体的な receipt field と consumer 結線は T-434 が定義する。

これは親の provisional (P2) と同じ択だが、`NOT_CLAIMED` を「局所的な非利用」であって「局所的な cap 許可」ではないと明記して補強する。

## 9. その他の択一

1. adapter の意味的充足

   - (a) 現存 counter を読み安全側エラーにするだけで実装済みと認める。
   - (b) cycle・lock・write-intent・permutation の各 adapter に最低 1 個の `P6Derived` 正例を要求する。
   - **推奨: (b)。** (a) は blanket handler の kind 別分割にすぎない。

2. calibration の新鮮性

   - (a) checked-in 固定 case だけ。
   - (b) 固定 case に加え、独立検査者が case ID 非公開で rotation・renaming を生成する。
   - **推奨: (b)。** 固定入力の暗記を「実装」と認定しないためである。

したがって判断点は V1 を含めて 3 件である。

## 10. 書かないもの・決めないもの

- 将来の P6 実装 wave が所有するもの:
  handler、4 adapter、構造化 IntegrityWitness と discriminator、normalizer、hypothesis/validation artifact、calibration fixture、mutation harness、exact-cut/P6/verifier 統合。
- T-434 が所有するもの:
  cap-lift receipt の path・schema、revision・P1〜P10・裁定・witness hash の束縛、runbook/journal/report/Layer3/producer/completeness consumer への結線。現状は判定入力 field 自体が無い。[D150:7446–7448](/work/1/SFC/tanab/izanagi/docs/decisions.md:7446)
- T-435 が所有するもの:
  次の 8c 実走直前の再事前登録。T-433 は事前登録文書を編集しない。
- 本契約が決めないもの:
  crash 回復状態機械、replicate 数、schedule/seed policy、generator への 0 bit 証明、sort witness の同値関係、`Bmax` と build 計数。[P6 README:472–492](/work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md:472)
- 本 wave で行わないもの:
  コード・test・設定変更、機械 gate/status field 新設、cap-lift 結線、`MAX_APPROVED_GENERATIONS` 変更、pytest。
- 現在の P6 は引き続き `NOT_IMPLEMENTED` であり、この契約案だけで状態は変わらない。[brief.md:24–29](/work/1/SFC/tanab/dev-wave-jobs/t433-p6-contract/brief.md:24)

## 総括

- 骨子は、11 必須条項・12 系統の calibration・全条項対応の反転変異・独立検査者である。
- 空 handler、恒一 verdict、blanket error、未知 kind 無視、常時 `NOT_CLAIMED` を具体 case で棄却する。
- V1 は択 (a) の per-run gate を推奨し、`NOT_CLAIMED` を global standing 許可にしない。
- 択一は V1、adapter 正例要件、calibration 新鮮性の 3 件。
- 現存するのは raw field、fixture cycle、integrity counter までで、P6 固有 artifact は存在しない。
- 構造化 IntegrityWitness、receipt field、実装・変異・pytest 実測は確認不能ではなく将来所有であり、本段では実施していない。