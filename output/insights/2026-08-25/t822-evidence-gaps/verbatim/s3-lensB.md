## 所見 1 — must-fix: 空の母集合でも受入が完了する

- 主張: 段 2 プランは `artifact_refs` の期待母数を検査せず、対象 0 件でも acceptance receipt を発行できるため、恒真化を防げていない。
- 原典: `s2-plan.md:83-86`、`orchestrator/campaign/autonomous_trial_completeness.py:3465-3466,3495-3497,3593-3607,3761-3798`、`orchestrator/campaign/trial_registry.py:5737-5740,5806-5820,5907-5959`
- なぜ real か / なぜ refuted か: `do_build=False` は空 bindings の `no-build` receipt を即 return する。全 cell が campaignless failure なら `build-failure` receipt を即 return する。campaign root はあるが Layer 3 report がない failure はさらに危険で、cell を `continue` した後、`mode="build"`、`unbound_fields=[]`、`artifact_refs=[]` の receipt になり得る。プランは「完全な Layer 3 が存在する cell」だけ helper を通すため、これらを hard failure にしない。正式 build report は既存条件から cell がちょうど 1 件なので、各 trial の期待母数は artifact row 1 件、六 trial 合計 6 件と明示的に検査すべきである。
- 成果物影響: 現状は `no-build` または `layer3-chain-absent` を付けた receipt が発行され、`trials[*].status` と cross-binding digest が台帳参照として残る。現在の certified 選択には直結しないが、世代証拠 0 件の run が「受入完了」として残る。

## 所見 2 — must-fix: 迂回経路が少なくとも 3 本ある

- 主張: 新設 gate を通らずに受入が完了する経路は、no-build、campaignless failure、materialized campaign の Layer 3 failure の 3 系統に加え、producer 例外の failure cell 化にも存在する。
- 原典: `orchestrator/campaign/p3_autonomous_workload_trial.py:2858-2949,3268-3321`、`orchestrator/campaign/autonomous_trial_completeness.py:3401-3450,3465-3497,3593-3607`、`orchestrator/tests/test_trial_registry.py:1799-1820`
- なぜ real か / なぜ refuted か: producer は予期した Layer 3 finalizer 例外を握り潰すのではなく、`admission_status="failed"` の診断 cell に変換する。その cell を cross-binding が空 projection に変換し、trial registry は reason code を付けて receipt 発行まで進む。既存 `test_s8c_acceptance_failure_cell_pins_layer3_chain_absent_reason` がこの受入成功を固定している。一方、新 helper が実際に呼ばれた後の例外は current acceptance の catch で握り潰される形ではなく、その点は refuted である。
- 成果物影響: failure/partial trial も receipt の六 trial 行に含まれる。台帳行自体は変更されないが、その lifecycle prefix と partial status を参照する正式 receipt が残る。

## 所見 3 — must-fix: standalone receipt verifier では保証が再発火しない

- 主張: `trial_registry.py` だけの検査では、追跡済み receipt を読む正式 verifier が世代証拠を再検証せず、保証が発行時限りになる。
- 原典: `s2-plan.md:124-126`、`orchestrator/campaign/s8c_acceptance_receipt.py:962-1001`、`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:172-186,422-430`、`orchestrator/campaign/layer3_report.py:604-624`
- なぜ real か / なぜ refuted か: verifier は report/journal の hash と、六個の cross-binding leaf digest の集約だけを検査する。leaf の元 projection、Layer 3 report、`loop_state.json` は再読しない。既存 v3 test は任意文字列から作った六 leaf digestを設定しても `verify_acceptance_receipt` が成功することを実証している。また新 helper 後に checkpoint が変更されても standalone verifier は検出できない。
- 成果物影響: 任意 leaf を持つ tracked receipt から `VerifiedAcceptanceReceipt` が得られる。現在は receipt が構造的に `certifying=False` で、`build_accepted_report` も拒否するため certified report はまだ生成されないが、将来 reason を外す際に certified 選択へ直結する。receipt schema を変えず、v3 verifier が report、manifest、Layer 3 artifact ref、checkpoint を消費側で再読する形にすべきである。

## 所見 4 — must-fix: 受理集合は新規には広がらないが、禁止された skip 分岐を残す

- 主張: 差分前後の集合比較では受理集合を新たに広げないものの、「再導出不能なら既存 reason へ残す」という明示的 skip は指定された規律上不採用である。
- 原典: `s2-plan.md:83-86,99-107,123-126`、`orchestrator/campaign/trial_registry.py:5907-5912,5948-5959`
- なぜ real か / なぜ refuted か: sealed iteration が存在する不一致 run は新たに拒否されるので、その部分は縮小方向である。しかし no-build、campaignless、Layer 3 不在は世代数を再導出できないまま receipt 発行を維持する。これは依頼で禁止された「再導出できないときは検査をスキップする」分岐そのものである。
- 成果物影響: skip を残すと証拠欠落 run の receipt と参照が残る。hard failure にすれば receipt は発行されず、受理集合は純粋に狭まる。診断 receipt が必要なら formal acceptance と別 API・別成果物に分離すべきである。

## 所見 5 — refuted: 入力 field は producer から到達可能だが fixture は未整合

- 主張: 四キー形の `loop_state.json.iteration` は実 producer から到達可能であり P1 は成立するが、現行 fixture 単独ではその証明にならない。
- 原典: `orchestrator/campaign/p3_autonomous_workload_trial.py:481-491,3733-3750,4032-4058`、`orchestrator/campaign/p3_s4_loop_trigger_gating.py:823-854`、`orchestrator/campaign/p3_s4_loop.py:653-665,731-742`、`orchestrator/campaign/layer3_report.py:193-198,472-523,589-601`、`orchestrator/tests/test_trial_registry.py:1017-1049,1078-1162`
- なぜ real か / なぜ refuted か: producer は fresh campaign を要求し、standard driver が実行ごとに iteration を増やして四キー checkpoint を保存する。supervisor は driver 完了後に generation を report へ追加し、最後に Layer 3 producer が campaign 全ファイルを `artifact_refs` に列挙するため、成功した二世代 run では値 2 に到達できる。一方、正式受入 fixture は現在 `{"whiteboard":[]}` を手書きし、二世代 report に対して WAL build/bench は一組だけで producer と一致しない。
- 成果物影響: 正しい producer 成果物の receipt bytes は helper が read-only なら不変である。fixture は手書き JSON ではなく `LoopState` と `save_loop_state` を使って生成しないと、producer と test が再び乖離する。

## 所見 6 — must-fix: 空実装検出は部分的に成立するが、空母集合と verifier の負例がない

- 主張: 下振れ・上振れの二負例は helper を常時成功へ置換すると赤くなるが、正例追加は赤くならず、対象 0 件を skip する変異も検出できない。
- 原典: `s2-plan.md:109-119`、`orchestrator/tests/test_trial_registry.py:1644-1681,1799-1820,1925-1972`、`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:422-471`
- なぜ real か / なぜ refuted か: proposed below/above tests は既存 gate では拒否されず、新 helper の四者比較だけを発火させるため、完全な空実装には検出力がある。赤くならない計画項目は、既存正例への「六 cell の iteration が 2」追加である。また missing `loop_state`、空 `artifact_refs`、no-build、campaignless、Layer 3 不在、standalone v3 verifier の任意 leaf を負例にしていない。既存 `test_t1185_m3_m4...` は report と manifest の宣言差、`test_v3_aggregate_is_recomputed...` は aggregate と leaf の差だけで、新検査とは重複しない。AST 静的走査では既存 top-level 関数名の重複はなく、予定名も未使用だった。
- 成果物影響: 現テスト案でも完全 no-op は防げるが、`if not artifact_refs: return` 型の恒真化が着地し、証拠 0 件の receipt を残せる。0 件、各迂回経路、standalone verifier の負例を追加する必要がある。

## 所見 7 — refuted: 禁止された編集面は要求していない

- 主張: プランは `autonomous_trial_completeness.py` を 0 byte 変更と明記しており、編集面制約には適合する。
- 原典: `s1-brief.md:31-36`、`s2-plan.md:48-55`
- なぜ real か / なぜ refuted か: 必要な projection は既に返されるため、発行時 gate は `trial_registry.py` で完結できる。durable な再検証を追加する場合も、`s8c_acceptance_receipt.py` が既存 report、manifest、Layer 3、checkpoint を再読すればよく、競合中の completeness file を変更する必要はない。
- 成果物影響: この制約自体による certified 選択、report、台帳、参照の変化はないため nit ではなく refuted finding である。

## 総括

- must-fix: formal acceptance では各 trial 1 artifact row、合計 6 row、各 row 1 `loop_state.json` を下限込みで必須化する。
- must-fix: no-build、campaignless、Layer 3 不在を generation gate の skip にせず hard failure、または診断 receipt を formal acceptance から分離する。
- must-fix: v3 standalone verifierでも同じ世代再導出を再発火させ、receipt 発行後の変更を検出する。
- must-fix: 0 件・全迂回経路・任意 leaf の負例を追加し、fixture は producer serializer で作る。
- nit: なし。P1 の入力到達性と禁止編集面 0 byte は refuted。