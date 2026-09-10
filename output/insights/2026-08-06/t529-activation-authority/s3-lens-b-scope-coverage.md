# 敵対検証結果

**結論: 現プランのままでは land 不可。** activation authority の中核は設計されているが、入口、履歴 artifact、publish evidence、durable identity の層に迂回が残る。

これは静的検査のみである。pytest は実行しておらず、緑を確認したとは主張しない。ファイル変更はなく、worktree は clean だった。

## 全層被覆

| 層 | 現状とプランの被覆 | 判定 |
|---|---|---|
| 世代候補 | `GENERATIONS` と successor 検査は `orchestrator/campaign/env_contract.py:163-228,278-347` | 被覆 |
| current 導出 | plan は `_ACTIVATION_STATE → REGISTRY` へ置換する `s2-plan.md:130-153` | 被覆 |
| current API | production の直接 `REGISTRY` read と `resolve_by_contract_sha256()` call は静的 `rg` で0件。公開経路は実質 `lookup()` `orchestrator/campaign/env_contract.py:349-390` | 現時点では被覆。ただし historical resolver が production 未配線 |
| publish evidence | path/hash/schema/accepted のみ `s2-plan.md:89-108` | 不足 |
| 最初の書込み前 gate | floor driver、oracle driver、P3 autonomous、T126、selector producer、silo ability probe を計画 `s2-plan.md:233-331` | 不足。oracle report、旧P3 writer、T419、true silo promotion が外 |
| durable proof / campaign identity | in-memory receipt を選択し、durable 証拠なし `s2-plan.md:362-373` | 未被覆 |
| historical replay | artifact 内の旧 contract hash を current `lookup()` と比較 `orchestrator/campaign/s8b_ratified_freeze.py:2876-2886` | 未被覆 |
| pin / trust-root 閉包 | T126 identity、silo runtime、T419 dirty scope は計画 `s2-plan.md:428-446` | 不足。committed protocol、silo evidence、S8c evidence contract 等を漏らす |

## must-fix

### 1. activation evidence は「契約と内容が異なる accepted calibration」を活性化できる

- **判定:** real（静的実測）
- **根拠:** plan の検査は generation/hash/path/schema/accepted に限る `s2-plan.md:89-99`。`schema_v2` は receipt 内部の整合だけを検査する `orchestrator/calibrator/schema_v2.py:504-544`。一方、既存の正規 loader は calibration と contract の `env_tag`、`clocks_per_us`、effective-clock policy を明示比較する `orchestrator/campaign/env_attestation.py:1091-1111`。
- **失敗シナリオ:** 別環境向けの schema-valid・accepted artifact を Pegasus の正規 filename に配置し、その bytes を指す g2 を登録する。path/hash/schema/quality は全て通るが、calibration の `env_tag` や clock が Pegasus contract と異なるまま current になる。
- **成果物影響:** floor/oracle/T126 の certified 受理集合が「Pegasus 契約に一致しない較正」まで拡大し、report と台帳の contract hash が実際の較正意味を表さなくなる。

### 2. P3 の「publish 証拠による非偽造性」は認証ではなく自己整合 JSON に留まる

- **判定:** real（機械的保証について）。脅威モデル上の扱いは親裁定が必要
- **根拠:** 親 brief は acquisition receipt により非偽造性を担保するとする `brief.md:75-78`。しかし receipt は exact-key と自己整合条件だけである `orchestrator/calibrator/schema_v2.py:521-544,555-567,611-627`。publisher の no-replace publish `s2-plan.md:66-76` を経たことを証明する署名、scheduler 発行証拠、外部 ledger tip は record loader から確認されない。
- **失敗シナリオ:** qsub ID、allocation、known-values、quality を内部整合するよう手書きし、正規 path・digest 名で commit する。issuer は「publisher が生成したもの」と手書き artifact を区別できない。
- **成果物影響:** fabricated calibration が current contract と certified 選択の参照値になり得る。
- **必要裁定:** detached/signed publish evidence を trust root にするか、maintainer commit review だけを trust root と明記して「非偽造性」という主張を弱める必要がある。

### 3. oracle report は独立 writer なのに Unit B から完全に漏れている

- **判定:** real（静的実測）
- **根拠:** brief は report を oracle 入口に含める `brief.md:85-87`。report は current contract を読む `orchestrator/campaign/s8b_oracle_report.py:1193-1204` 一方、CLI は独立して observations を create-only write する `orchestrator/campaign/s8b_oracle_report.py:1689-1692,1706-1725`。plan の oracle 節は driver の claim しか扱わず `s2-plan.md:258-267`、Unit B に report がない `s2-plan.md:505-523`。
- **失敗シナリオ:** oracle driver と別プロセスで report を再生成する。driver の activation receipt を持たず、report 起動時の別 activation state の下で observations が書かれる。
- **成果物影響:** certified oracle observations/report が driver と同じ activation serial だったことを保証できず、proof chain が混在する。

### 4. in-memory receipt では「6入口が同一 activation state」を事後証明できない

- **判定:** real（brief の文言に対して）。「同一 process 内だけ」の要件へ弱めるなら設計裁定
- **根拠:** brief は6入口が同一状態を検査する receipt を要求する `brief.md:50-53`。plan は import 時の `_ACTIVATION_STATE` を canonical state とする `s2-plan.md:132-143,182` が、成果物 bytes・campaign IDを一切変えず、durable 証拠は明示的にゼロ `s2-plan.md:362-373`。
- **失敗シナリオ:** floor を serial 1、oracle を serial 2、T126 を serial 3 で実行する。各process内の検査は通るが、既存成果物には serial/state hash が残らないため aggregator は混在を検出できない。また import 後に record tip が変わっても、同processでは cached state との比較しか行わない。
- **成果物影響:** certified 選択、report、台帳から activation serial を再構成できず、「同一状態」の証明参照が存在しない。
- **必要裁定:** versioned sidecar/schema を採るか、要件を「各 writer の process-local control-flow gate」に明示的に弱める必要がある。

### 5. Pegasus g2 を活性化すると既存 frozen proof chain が current lookup との比較で壊れる

- **判定:** real（静的実測）
- **根拠:** committed floor protocol は g1 contract hash を固定する `output/s8b-freeze/floor_protocol.json:1`。protocol validator は supplied current hash と一致を要求する `orchestrator/campaign/s8b_floor_contract.py:104-151`。ratified freeze はそこへ current `lookup()` を渡す `orchestrator/campaign/s8b_ratified_freeze.py:2876-2886`。selector seal も current contract から protocol を再導出し、committed bytes と完全一致させる `orchestrator/campaign/s8b_prediction_runner.py:1457-1473,1564-1571`。
- **失敗シナリオ:** 正規 Pegasus g2 を record で current にする。既存 g1 floor protocol は historical artifact として正しいのに、current g2 hash と不一致になり、ratified freeze load と selector seal が失敗する。
- **成果物影響:** 既存 certified floor、freeze、selector、oracle の参照鎖が読めなくなる。新規 g2 campaign も protocol bytes を更新しない限り開始できない。
- **不変条件判定:** 初期 g1 record 追加時は既存 bytes を変えずに済む。しかし実際に g2 を使う段階では、historical resolver/versioned protocol を配線しない限り「既存 bytes 不変」と「g2 稼働」は両立しない `brief.md:55-60`。

### 6. 「silo 昇格入口」は実在せず、ability probe を保護しても要件を満たさない

- **判定:** real（入口同定誤り）
- **根拠:** `silo_ladder_rung1` は成果物を `ability_probe`、`research_goal_eligible=False`、`recovery_measurement_eligibility=False` と固定する `orchestrator/campaign/silo_ladder_rung1.py:4688-4703`。plan 自身も true promotion consumer が未同定だと認める `s2-plan.md:309-331`。
- **失敗シナリオ:** correctness/gap-job/collect の3 writer 全てに gate を挿し、「6入口完了」と報告する。しかしそれらは ability evidence の生成経路であり、promotion acceptance を実行する consumer は検査されていない。
- **成果物影響:** silo promotion の受理集合・台帳参照は未保護のままか、そもそも実装対象が存在しない。
- **必要裁定:** scope を「silo ability probe writers」に改名するか、真の promotion consumer を同定・追加するまで完了扱いを禁止すべきである。

### 7. create-only hash chain は tip の削除・過去 commit への rollback を検出できない

- **判定:** real（設計上）
- **根拠:** record は predecessor hash を持つ内部 chain で、issuer は現 chain と次 serial を検査する `s2-plan.md:13-20,66-74`。信頼された最新 serial/tip を chain 外に保持する設計はない。M03 も gap/predecessor/filename の破壊しか扱わない `s2-plan.md:532-535`。
- **失敗シナリオ:** serial 4 を削除し、serial 3 までの有効 prefix を clean commit にする。全 predecessor/hash/canonical 検査は通り、current contract は過去状態へ戻る。
- **成果物影響:** certified selection が参照する calibration と activation state hash が静かに後退し、台帳上の単調性が失われる。
- **必要修正:** 外部 monotonic anchorを導入するか、保証名を「同一 snapshot 内の chain integrity」に限定し、rollback resistance を主張しないこと。

### 8. pin 閉包は key 側・artifact 側の参照を複数漏らしている

- **判定:** real（静的実測）
- **根拠:**
  - protocol golden が contract hash と exact bytes を保持する `orchestrator/tests/test_s8b_protocol_builder.py:47-63,91-105`。
  - floor replay test が protocol/calibration/contract hash を literal pin する `orchestrator/tests/test_s8b_floor_campaign.py:3240-3252`。
  - committed silo evidence test は historical binding を current `lookup()` と比較する `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1252-1262`。
  - S8c evidence contract は role keyと reachabilityを `run_trial.env_contract`、`lookup`、`execution_guard` に固定するが、新 activation APIを知らない `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:431-468`。evaluator も `lookup` と `attest_and_build_receipt` だけを見る `orchestrator/campaign/s8c_preregistration_evidence.py:575-607`。
  - legacy trust root は path ではなく SHA 定数で pin される `orchestrator/campaign/env_attestation.py:28-30,1119-1133`。
  - T126 protocol は `env_tag/clocks/numactl` を別定義する `orchestrator/qualification/contract.py:140-149`。
  - plan の閉包列挙はこれらを含まない `s2-plan.md:428-446`。
- **失敗シナリオ:** g2 activation 後、silo/floor の historical test が current mismatch で赤くなる。一方、P3 から新 activation gate を除去しても、S8c evidence evaluator は旧 `lookup` と execution receipt が残るため満足し続ける。
- **成果物影響:** historical evidence が無効化される一方、preregistration は activation authority が欠けた実装を環境契約 consumer として誤受理する。

## should-fix

### 9. 第7入口以降として旧P3 writers、T419、floor protocol authoring が残る

- **判定:** writer/bypass の実在は real。certified scope に含めるかは疑い
- **根拠:**
  - 共通 P3 loop は `env_contract=None` を無条件受理する `orchestrator/campaign/loop.py:62-70` 後、layout を作る `orchestrator/campaign/loop.py:139-145`。
  - `p3_s4_loop` は契約値を定数複製し `orchestrator/campaign/p3_s4_loop.py:83-88`、lookup/receipt なしに write と run を行う `orchestrator/campaign/p3_s4_loop.py:878-905`。
  - 同様の経路が `p3_s4_loop_sort.py:90-94,230-252`、`p3_kickoff.py:42-45,99-111` にある。
  - T419 は Python 側で current lookup する `tools/pegasus/probes/t419_probe_causality.py:3388-3425` が、PBS wrapper はそれ以前に output root と marker を書く `tools/pegasus/probes/t419_probe_causality.pbs:44-70,141-166`。
  - floor protocol authoring は lookup で contract hash を埋め `orchestrator/campaign/s8b_floor_campaign.py:410-438`、directoryを生成する `orchestrator/campaign/s8b_floor_campaign.py:467-480` が、plan は scope 外とする `s2-plan.md:256`。
- **失敗シナリオ:** activation state が変わった後でも、これらのコマンドは receipt なしで WAL、probe result、protocol artifact を生成する。
- **成果物影響:** certified 対象外なら直接影響はないが、後段 admission がこれらを参照した時点で activation state 非束縛の成果物が混入する。明示的な非eligible宣言か gate が必要。

### 10. selector は「実行入口」ではなく proof-chain producer である

- **判定:** real
- **根拠:** 親が挙げた3ファイルは producer 入口ではなく、実writerは `s8b_prediction_runner.seal()` `s2-plan.md:290-307`。seal は current contract を間接的に再導出し `orchestrator/campaign/s8b_prediction_runner.py:1457-1473`、最初の副作用は provider artifact root 作成 `orchestrator/campaign/s8b_prediction_runner.py:1092-1101`。
- **失敗シナリオ:** selector を「環境実行入口」の6番目として数え、receipt を入れる。prediction provenance は守られるが、workload environment attestation の入口は1つも増えない。
- **成果物影響:** selector prediction と protocol の state は守られるが、測定の受理集合には効果がなく、入口被覆率を過大報告する。
- **必要裁定:** 入口数を5へ訂正するか、「proof-chain producer を含む6種」と scope を定義すること。

### 11. 段5のファイル集合は字面上素集合だが、並列実装単位として独立していない

- **判定:** real
- **根拠:** Unit A は先行指定 `s2-plan.md:475-499`、Unit B はAの未実装 receipt APIへ依存する `s2-plan.md:501-503`。一方、Aの責務である transitive pin closure が `silo_ladder_rung1.py` を必要とするのに、このファイルはB所有 `s2-plan.md:492-526`。さらに M08 が変更を前提とする `env_attestation.py` `s2-plan.md:539` はどちらの所有一覧にもない。同ファイルは `env_contract` をimportするため `orchestrator/campaign/env_attestation.py:22-25`、legacy predicate の共用方法次第で循環依存も生じる。
- **失敗シナリオ:** A/Bを同時投入すると、Bが未確定APIを仮実装・stub化するか、test collection時に import失敗する。pin closure修正をA/B双方が `silo_ladder_rung1.py` へ入れれば所有衝突になる。
- **成果物影響:** gate と code-identity pin の片方だけが land し、receipt APIがあるのに runtime identityへ含まれない中間状態を作る。
- **修正:** A完了後Bを開始する直列分割にするか、API/schemaだけの先行単位を設ける。`env_attestation.py` の所有者も明記すること。

### 12. 変異候補は複合変異と既存gate由来の赤が混ざり、帰属が成立しない

- **判定:** real
- **根拠:**
  - M07の「receiptless v2」は既存 exact top schemaだけで既に拒否される `orchestrator/calibrator/schema_v2.py:561-567,748-771`。新 gate を壊した帰属にならない。
  - M08は既存 grandfather loaderと新 legacy gateを同時に壊す `s2-plan.md:538-539`。既存 loader `orchestrator/campaign/env_attestation.py:1119-1133` が赤にする。
  - M09/M10/M11は複数入口・複数位置を1 mutantにまとめる `s2-plan.md:540-542`。
  - M12の plain dict は seal checkを外しても、後続の属性アクセス・exact type比較が別理由で落とし得る `s2-plan.md:543`。
  - M03の “rollback” は tail削除を試さない `s2-plan.md:534`。
- **失敗シナリオ:** 新 activation quality check を削除しても receiptless fixture は旧schemaで赤のままになり、mutationをkillしたと誤認する。複合入口 mutantでは一方のgateだけが赤を出し、他方の漏れが隠れる。
- **成果物影響:** mutation scoreが防壁強度を過大評価し、実際にはaccepted/rejected集合を広げる欠落がland可能になる。
- **修正:** 1 mutant＝1 predicate/1入口に分解し、既存schemaを通る positive fixtureを使うこと。

### 13. `generation` は3義目ではないが、genericな activation 命名は既存概念と混在する

- **判定:** real（意味上）。字面衝突はなし
- **根拠:** planned `generation` は既存の契約世代 `GenerationEntry.generation` と同義 `orchestrator/campaign/env_contract.py:163-179` なので3義目ではない。ただしP3 artifactでは同じ `generation` がLLM提案世代として使われる `orchestrator/campaign/p3_autonomous_workload_trial.py:938-967,1538-1556`。既存には preregistration の `ActivationReport` `orchestrator/campaign/s8c_preregistration.py:206`、`activation_report_digest_sha256` `orchestrator/campaign/trial_registry.py:72-75`、silo macroの `activation_contract` `orchestrator/campaign/silo_ladder_rung1.py:4692-4700` がある。
- **失敗シナリオ:** 将来receiptをP3 reportへ直列化すると、同一document内で「proposal generation」と「contract generation」が無修飾で混在する。
- **成果物影響:** report/台帳のfield参照がどのgenerationを指すか曖昧になり、proof-chain joinを誤る。
- **修正:** `EnvContractActivationReceipt`、`env_contract_generation`、`env_contract_activation_serial/state_sha256` のようにnamespaceを付ける。module名 `env_contract_activation.py` 自体には既存衝突を確認しなかった。

### 14. 親の fuse 実測は import/current view だけを証明し、入口受理を証明していない

- **判定:** real
- **根拠:** 親実測は fuseを外すと非実在g2が `lookup()` currentになったことまで `brief.md:45-48`。floorは実行前に calibration load/receiptを行う `orchestrator/campaign/s8b_floor_campaign.py:2739-2785`、oracle driverも同様のpreflightを持つ `s2-plan.md:258-262`。plan自身も実測の限界を認める `s2-plan.md:547-563`。
- **失敗シナリオ:** nonexistent g2をcurrentにし「全入口で危険」と一般化する。floor/oracleは既存loaderで落ちる一方、旧P3/T419等は別経路で書き始めるため、実際の破綻分布とテスト対象がずれる。
- **成果物影響:** import-only negative testを入口gateの証拠と誤認し、writer単位の迂回が残る。

## nit

### 15. activation 例外型の識別子が未指定で、D75検査を完了できない

- **判定:** realだが nit
- **根拠:** module設計は “error” の配置だけを述べ、名前を定めていない `s2-plan.md:80-87`。receipt/module/fieldの候補名は別途定めている `s2-plan.md:155-180,448-471`。
- **失敗シナリオ:** Unit Aが `ActivationError`、Unit Bのtestsが `EnvContractActivationError` を仮定し、統合時に例外捕捉がずれる。
- **成果物影響:** certified値や受理集合への直接影響はないが、fail-closed例外処理とtest APIに不要な揺れが出る。

## 総括

最も重い所見3つ:

- g2 activation後、既存frozen protocolをcurrent hashで検証するため、既存bytesを保ったままproof chainを利用できない。
- in-memory receiptでは6入口の同一activation stateを成果物から証明できず、process間・時点間の混在を検出できない。
- 実入口の被覆が欠けている。特にoracle report、true silo promotion、旧P3 writerが未保護である。

親が裁定すべき択一:

- durable sidecar/versioned schemaを導入するか、要件をprocess-local gateへ弱めるか。
- signed/detached publish evidenceを導入するか、maintainer commitを唯一のtrust rootとして「非偽造性」を弱めるか。
- selectorをproof-chain producerとして6入口に数えるか、実行入口を5種とするか。
- silo scopeをability probeへ訂正するか、true promotion consumerを同定するまで停止するか。
- external monotonic anchorを導入するか、rollback resistanceを保証対象外とするか。

scopeから漏れていて、塞がないと迂回が残る層:

- `s8b_oracle_report.py` の独立 observations writer
- `p3_s4_loop.py`、`p3_s4_loop_sort.py`、`p3_kickoff.py` と `loop.py` の `env_contract=None` 経路
- `t419_probe_causality.pbs` のPython起動前のdirectory/marker write
- floor protocol authoring utility
- 未同定のtrue silo promotion consumer
- historical artifactをrecorded contract hashで解決するproduction resolver層
- activation serial/state hashをcampaign identity・report・台帳へ残すdurable proof層
- S8c preregistration evidence contractのactivation reachability層