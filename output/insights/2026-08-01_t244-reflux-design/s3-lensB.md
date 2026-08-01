静的検査のみを行った。pytest、build、`check_docs.py` は実行しておらず、試験結果についての主張はしない。

## 1. hidden constraint が auditor と SHA 経由で露出する

- **重大度:** BLOCKER
- **根拠:** `s2-plan.md:15` は untrusted auditor に実効 diff と raw/effective IR の SHA を渡す。`:151-153` でも control WAL に両 SHA を残す。一方、`:58` 自身が小さい値域の SHA は辞書攻撃可能と認め、`:186` は同一 UID の caller から trusted state を秘匿できないと認める。候補空間は `axis_trigger_gating.py:45-51` の 5 atom、わずか 32 mask である。
- 実効 diff は SHA を破るまでもなく `E_t` を直接示す。raw/effective SHA も32通りを総当たりすれば復元でき、`E_t \ P_t` から constraint の一部または全部を測れる。
- `s2-plan.md:62` は role 間共有 state を検出したら fail-closed とするが、その検出機構は無い。現行も session ID 重複拒否は provider instance 内だけであり、role 横断再利用を拒否しない（`docs/decisions.md:4803-4805`）。
- **放置時の成果物影響:** constraint を知った後続 provider/caller が候補を適応させ、WAL の raw/effective 参照、certified mask、材料レポートの採用候補集合が変わる。

## 2. Qmax=2 は gate 探索を消さず、origin 分割で 5 atom を回収できる

- **重大度:** BLOCKER
- **根拠:** `s2-plan.md:68-76` は予算を「workload × treatment cell ごとの origin」に置き、A/B/C を別 origin として許す。`:95-100` では generator が選んだ singleton relaxation `r` の red を、そのまま `must-backoff(r)` に変換する。`:235-242` も、外部 caller が2 atomを照会でき、人間が新 origin を発行すれば予算が再生すると認めている。
- これは「generator が constraint を誘発して gate の形を測る」経路そのものである。caller は照会した `r` を知り、二値結果からその atom の label を得る。
- `Qmax=2` なら到達可能な constraint 集合は大きくても `|C|≤2`、状態数は `1+5+10=16`、4 bit である。設計自身の公開上限は `4.585 bit/window`（`:48-56`）なので、この会計は reachable constraint state を隠せる根拠にならない。
- A/B/C の3 originだけで6 query、正式 H1/H2 × on/off/swapped ならさらに増える。Kmax=1 の seal 後開示も別 origin の次手に利用できる。

この設計が弱めるのは、動的自然文 constraint、planner/coder への直接 result/metrics、同一 origin 内の3件目以降の照会である。弱めないのは、caller 選択の singleton oracle、新 origin、cell 横断集約、timing/停止位置、auditor の実効 diff、provider 注入・共有 state である。

- **放置時の成果物影響:** cell/origin を跨いだ照会で gate atom が復元され、proposal 分布、制約台帳の公開 class、最終 certified 候補が gate 既知の探索へ変わる。

## 3. 一回の verifier red から atom 全域の safety constraint は導けない

- **重大度:** BLOCKER
- **根拠:** `s2-plan.md:95-100` は一つの singleton relaxation の red から、その atom を全後続候補で必須化する。しかし `:183` 自身が「実行時挙動の数学的単調性までは証明しない」と認める。`axis_trigger_gating.py:45-51` は列挙空間を定義するだけで、他 atom との相互作用や因果単調性を証明しない。
- verifier red が証明するのは「その mask のその実走を certify できない」ことだけである。他 atom の組合せでも `r=false` が常に不正、または `r` が anomaly の原因だったとは証明しない。
- `C_t⊆C_{t+1}` と `A(C_{t+1})⊆A(C_t)`（`s2-plan.md:203-219`）は構文 mask 集合の単調性であり、正しさ集合の単調性ではない。
- 具体的な相互作用反例は未実測なので、その存在自体は**推測**である。ただし、普遍化を支える証拠が設計に無いことは事実である。
- 最終 verifier を毎候補で回す点は規律2を弱めない。問題は誤った一般化による過剰拒否と、generator が制約集合を誘導できる点である。
- **放置時の成果物影響:** 実際には certify 可能な mask が探索前に排除され、certified best、tie 判定、材料レポートの候補母集団が不当に縮む。

## 4. D114 が保証外とした層が formal consumer まで素通りする

- **重大度:** BLOCKER
- **根拠:** 設計は「origin proof のない raw driver 出力を正式 report/proof chain に入れない」とする（`s2-plan.md:133,188`）が、その consumer gate が scope に無い。

| 層 | 実在する迂回 | 必要な扱い |
|---|---|---|
| `run_trial(drive=/providers=/preview=)` | 注入引数は `p3_autonomous_workload_trial.py:1002-1004`、任意 `drive` は `:932-949` で実行される | production API から分離するか、注入 run を originless/non-formal として下流で拒否する。保証対象外の注記だけでは不足 |
| `drive_iteration()` 直接反復 | `p3_s4_loop_trigger_gating.py:468-518` は既存 state を復元して反復する | human loop は残し、8c formal wrapper だけ token 必須にする。`s2-plan.md:82` の「direct driver に token」と `:188` の「raw driver は残る」を明確に分離する |
| freshness TOCTOU | D114 `docs/decisions.md:5370-5373` | formal D116 では単一 in-flight/CAS を閉じる必要がある。単なる保証対象外では `C_t` と frontier の順序が成立しない |
| fixture+build carve-out | D114 `:5374-5375`、CLI 拒否だけは `p3_autonomous_workload_trial.py:1111-1114` | programmatic formal 経路で拒否するか、origin proof と材料 report から除外する |
| 材料 report | `layer3_report.py:384-404,416-427` は任意 campaign WAL の `commit` と `loop_state` を読み、origin seal を要求しない | `layer3_report.py` と certified consumer も scope に含める必要がある |

実在する直接反復成果物は `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/loop_state.json:2-18`、それを通常の Layer3 材料へ射影したものは同 campaign の `reports/layer3_report.json` である。これは consumer 層の発火 artifact path として使える。

- **放置時の成果物影響:** origin reservation を一度も通らない WAL `COMMIT` が正式材料レポートへ入り、query 上限外の variant が certified 選択候補と proof-chain 参照に混入する。

## 5. origin ledger は原子的な「状態遷移」になっていない

- **重大度:** BLOCKER
- **根拠:** `s2-plan.md:80-87` は count-check-reserve の新 primitiveを要求するが、`wal.append()` の flock は一 record の追記だけを覆う（`wal.py:283-378`）。計画された event 群は `s2-plan.md:147-159` に分離され、campaign WAL と origin control WAL を跨ぐ。
- 二つの process が slot 1/2 を順に予約した後で並行実行すれば、双方が同じ `C_t` と frontier を読む。query 数は正しくても reflux の世代順序は壊れる。
- crash window が未定義である。

  - `slot-reserved` 後、provider 前
  - campaign WAL の verifier red 後、`constraint-added` 前
  - `constraint-added` 後、`query-result` 前
  - query 完了後、`origin-sealed` 前

- 現行 driver は run 後に provenance、`loop_state.json`、digestを順に書く（`p3_s4_loop_trigger_gating.py:500-517`）。supervisor が結果を受けてから外側で constraint を追加すると、その前に checkpoint は前進済みになる。
- `origin_layout` は `s2-plan.md:142` のローカル名にしか存在せず、layout constructor、lock identity、保存 root が定義されていない。`reflux-control` stage も現行 `WAL_STAGES` には無い（`model.py:20-32`）。
- 必要なのは単なる予約数の原子化でなく、「pending は最大1」「state commitment の CAS」「未完 event の idempotent replay」を含む状態機械である。
- **放置時の成果物影響:** query consumed 値と実行数、constraint state、campaign WAL、source refs が食い違い、同じ失敗の二重反映または反映漏れが台帳と材料レポートに残る。

## 6. docs-only 判断は半分正しいが、「設計確定」への状態遷移は不正

- **重大度:** BLOCKER
- **根拠:** `DW-G04` は発火 artifact/計測 ID が無ければ設計メモに留める（`docs/dev-wave/core.md:57-60`）。clean verifier red の singleton relaxation 等が見つからないという `s2-plan.md:289-296` から、failure→constraint machinery を今実装しない判断は正しい。
- しかし同プランは `:251-274` で D116 を「設計 v1 確定」として未解決記述を閉じる一方、`:330-332` では次を未決と認める。

  - `I/Q=2・K=1` を正式採用するか
  - origin authority を tracked registry と service/ACL のどちらにするか

  これは bit 会計と信頼境界の中核であり、未決のまま「設計確定」とは書けない。
- 機械的な cap 紐付けも必要である。D114 は現状、解除を「定数1個と境界テストの同時変更」に限定するだけである（`docs/decisions.md:5310-5313`）。設計実装・origin proof・consumer gateの存在とは結び付いていない。
- bareな `MAX_APPROVED_GENERATIONS=2` を捕捉できる既存計測はある。**計測 ID `V7`**、artifact は `output/insights/2026-08-01_t244-generation-gate/mutation-ledger.json:191-218`。したがって、cap 引上げ時に D116 前提の機械検査を要求する guard は `DW-G04` の根拠を持つ。
- 最小の二択は次である。

  1. `V7` を cap-lift prerequisite mutation に拡張し、実装・formal consumer・origin ledger の前提不足で落とす。
  2. コードを触らないなら D116 を採番せず設計 draft として置き、phase/runbook の「未解決」を閉じない。

- **放置時の成果物影響:** 将来 author が定数と境界テストだけを同時更新して現行の狭い還流経路を開き、generation budget、role attempt 数、WAL `COMMIT`、terminal report が設計未実装のまま多世代化する。

## 7. 親 brief §3 の「実測」7項目には誤りがある

- **重大度:** MAJOR

| # | 判定・根拠 | 放置時の成果物影響 |
|---|---|---|
| 1 recipient matrix | 行番号と payload 内容は概ね正しい（`p3_autonomous_workload_trial.py:816-825,843-860,897-905,957-967`）。ただし item 2 の「2本だけ」と両立しない | bit 会計が `current_metrics` を落とし、proposal の適応量を過小評価する |
| 2 cross-generation は2本だけ | **誤り。** `current_metrics` は `:795-802` で保持され、`:953` で前結果から更新され、次世代の planner/coderへ `:818-824,858` で渡る。数値の有無だけでも certified/non-certified を区別しうる | 次世代 proposal と受理 variant が性能・合否に適応する |
| 3 whiteboard の型は閉じている | key 集合だけ閉じている。`state_from_dict()` は direction/magnitude/result の enum、exact type、iteration 整合を検査せず、整数/floatへ coercionする（`p3_s4_loop.py:390-404`） | checkpoint 入力で planner/coder payload と停止判定を変えられる |
| 4 failure はすべて正しさ・構造由来 | `_preview` は構造由来だが、`outcome=aborted` は build、trace timeout、probe、環境等も含む（`pipeline.py:545-555,648-707`、trigger driver `:422-430`） | infrastructure failure を safety constraint に誤変換し、候補集合を縮める |
| 5 既存 constraint 強制点 | **過大表現。** `check_syntax_contract(str)->List[str]` は禁止変数名の regex（`p3_s4_loop_trigger_gating.py:105-115`）。5 abort atom の mask 強制ではない | 実装済み拡張と誤認し、constraint が未執行のまま report だけ付く |
| 6 search_config で campaign binding | 個別 campaign ID への束縛は正しい（`ident.py:76-103`）。ただし trial等を変えた別 campaign 全体の global budgetにはならない | run/cell 分割で counter と constraint state が初期化される |
| 7 WAL | `wal.log(layout,variant,stage,env_tag,payload,ts)` は正しい（`wal.py:499-506`）。ただし `records_by_stage` は last-wins（`:586-601`）で、append flock は transaction ledgerではない | verify/source event の取り落としや budget 二重予約を見逃す |

理由経路の精密な結論は次のとおりである。

- 通常の非注入経路では、proposal/report/journal/digest を次世代 planner/coder payloadへ直接読み戻す consumer は無い。
- proposal file は planner/coder/auditor全文と prior bool を持つが、critic 自然文は持たない（`p3_autonomous_workload_trial.py:923-931`）。
- digest は critic だけが読む（`:955-967`）。
- critic の全5 fieldは parseされ、journal/reportへ保存される（`:300-312,590-597,978-979,722-748`）。次手制御に使うのが boolだけ、という限定なら正しい。
- ただし `reverse_recommended` は full digestから criticが作った**理由条件付き1 bit**で、driver停止へ効く（`p3_s4_loop.py:673-683`）。よって「理由は1 bitも渡っていない」は planner/coderの直接 payloadに限定しなければ偽である。
- injected provider は世代間 state を保持できるため、この限定も D114 の保証外では崩れる。

- **放置時の成果物影響:** 情報量を過小評価した D116 が land し、proposal、stop reason、report の役割記録、WAL受理集合が想定以上に前世代結果へ条件付く。

## 8. 実シグネチャと実装地図が不足している

- **重大度:** MAJOR

| 名称 | 実体と食い違い |
|---|---|
| `check_syntax_contract` | 実体は `implementation: str -> List[str]`。constraint mask、failure、WAL refを受けない |
| `SYNTAX_CONTRACT_FORBIDDEN` | `thid_`, `result_`, `read_set_`, `write_set_`, `node_map_`（`axis_trigger_gating.py:58-64`）。5 gate atomは別の `GATEABLE_REASONS`（`:45-51`） |
| `gating_spec` | 現行は自由 C++ 一行を説明する `GATING_SPEC` と payload key（`p3_autonomous_workload_trial.py:158-163,850`）。`gating_spec_v2`、mask parser、canonical emitterは存在しない |
| `whiteboard` | 保存5 fieldは実在するが、値域は未閉包。設計では保存を残し generator projectionだけ外すため、report consumerとの二重契約が要る |
| `loop_state.json` | top-levelは iteration/start_wall/reverse/whiteboardの4 fieldだけ（`p3_s4_loop.py:356-368`）。origin、constraint、frontier、reservationは無い |
| `search_config` | campaign identityには入るが、authority-issued originやglobal ledgerを発行・照合するAPIは無い |
| `wal.log` | 呼出形は一致する。ただし `origin_layout`、`STAGE_REFLUX_CONTROL`、record ordinal、count-check-reserve primitiveは存在しない |
| `preview()` | その名前の関数は無い。実体は `_preview(coder, *, sub)`（`p3_autonomous_workload_trial.py:479-497`）と `_preview_diff(path,sub,root)`（trigger driver `:523-535`） |
| 新 field 群 | `candidate_ir_schema_sha256`、`reflux_origin_id`、`reflux_policy_sha256`、raw/effective IR、hidden mask、last certified frontier、`report.reflux.*` はすべて新設対象 |

さらに将来変更表 `s2-plan.md:300-316` は、formal consumer の `layer3_report.py`、origin layoutの `layout.py`、role非干渉の `claude_projected_provider.py`、verifier policy/binary bindingの `pipeline.py`、registry/authority実装を含まない。

- **放置時の成果物影響:** 実装者が既存 syntax gate や campaign WAL を流用しただけで完成と誤認し、constraint proof、origin counter、正式 report 参照が互いに結び付かない。

## 9. 1世代運転・runbook 3手順・ablation を維持する契約が無い

- **重大度:** MAJOR
- **根拠:**

  - 現行 fixture coder は C++ `implementation` を返す（`p3_autonomous_workload_trial.py:345-360`）。固定5-bit maskへ変えると、`ROLE_CONTRACTS`、`FixtureRoleProvider`、parser、preview、driver、runbook 3.1/3.2/3.3を同時更新しなければ全入口が壊れる。将来変更表は fixture providerを名指ししていない。
  - no-build は correctness queryではなく、driverも `dry-pass` を返して whiteboardを進めない（`p3_s4_loop_trigger_gating.py:406-412`）。これを Qmaxに数えると、runbookの配線確認だけで formal originを使い切る。診断 runはoriginless/non-formalとして分離すべきである。
  - 現行 `reflux=off` は critic digestから赤節だけを落とす（`p3_s4_loop.py:236-253`、trigger driver `:511-514`）。設計は criticをreport-onlyにするが、hidden constraintをoff armで無効にするかを定義していない。常時適用なら off が汚染され、無効化しなければ on/off が同一になる。
  - 一世代の既存 report/provenance SHAを維持するのか、v2 origin経路へ移行するのかも未定義である。

- **放置時の成果物影響:** runbookの正当な1世代 pilotが失敗または別schemaになり、reflux on/offのarmラベルと材料レポートの比較対象が偽になる。

## 総括

**(a) 判定: NO-GO。**

**(b) BLOCKER は6件。**

1. auditorの実効diffと小空間SHAがhidden constraintを露出する。  
2. cell別Qmaxと新originでgenerator/caller選択のgate probeが残る。  
3. 単一redからatom全域を禁止する正しさ上の単調性が証明されていない。  
4. 注入・direct driver・fixture carve-outをformal consumerが拒否しない。  
5. origin ledgerに単一in-flight、CAS、crash replayが無い。  
6. 未決の予算/authorityを残したままD116を「設計確定」にし、cap liftを実装前提へ機械束縛していない。  

**(c) 設計を救う最小の変更:** この wave では D116 を確定 decision にせず、設計 draftとして残し、D114上限1と計測ID `V7` のcap防壁を維持する。その上で、軸(iii)の事前 batch freezeを必須化し、series-global予算、untrusted auditorへの実効mask非開示、単一in-flightの復旧可能origin ledger、formal report consumerのorigin-proof gate、on/off・診断runの明確な分離をすべて定義してから再裁定する。これらは一つでも欠けると同じ迂回が残る。