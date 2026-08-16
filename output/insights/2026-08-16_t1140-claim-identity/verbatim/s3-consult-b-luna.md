## 総括

NO-GO。段 2 プランの S2 は host だけを land し、既裁定の host / script SHA / nonce 3点を縮小している。  
script SHA と nonce の値および receipt path は `tools/pegasus` と実成果物に存在する。ただし receipt は submitter-owned で scheduler-owned authority ではない。  
S1 の identity hashだけでは、別 `out_root` と generic `acquire_claim` の回避を塞げず、P5も現状の leaf だけでは成立しない。  
`loop.py` は明示的な scope 外だが、未解決の proof 影響を裁定パッケージへ返す必要がある。pytest は未実走。

## 所見

### 1. S2をhost-onlyへ縮小しており、既裁定と衝突する

severity: high

根拠: `brief.md:7`、`brief.md:20`、`artifacts/s2-plan.md:5`、`artifacts/s2-plan.md:112`、`orchestrator/campaign/reservation.py:218`、`orchestrator/campaign/s8b_oracle_driver.py:915`。

現在の `check_reservation` は PBS job ID、boot ID、時刻、残容量しか検査せず、host・script SHA・nonceを検査しない。プラン自身も script SHA と nonce を保留している。

成果物影響: host-onlyで land すると、reservation leaf と oracle 経路の script/nonce不一致の受理集合が残り、材料レポートと proof chain は未検証の reservation binding を参照し続ける。

提案する修正: host-onlyの部分実装は land しない。3項目を同じ waveで実装するか、既裁定を変更する明示的な再裁定を先に取る。

scope: S2内。ただし nonce の authority 所有者は裁定パッケージ候補。

### 2. 「authorityがない」と「artifactがない」を混同している

severity: high

根拠: `tools/pegasus/submit_floor.sh:411` は nonce を qsub に渡し、`submit_floor.sh:466` は submit receipt を create-only で生成する。`tools/pegasus/floor_campaign.sh:346`、`floor_campaign.sh:446`、`floor_campaign.sh:508`、`floor_campaign.sh:733` は nonce、job ID、実行 script SHA、commit blobを照合する。T126にも同型の照合が `tools/pegasus/t126_qualification.sh:674` と `t126_qualification.sh:708` にある。

実際に次の receipt が存在する。

`output/env/pegasus/floor/attempts/submissions/f29f559a81afd2d3ba5dde05000a3471/submit-receipt.json:2` は `dry_run=false`、`:3` は job ID、`:5` は script SHA、`:6` は nonce を持つ。`e587...` の receiptも同様である。

ただし receipt は login-side の submitter が作るもので、scheduler-ownedではない。nonceも PBS固有値ではなく `qsub -v` で渡される。scheduler由来の独立値は PBS job ID と qstat 応答であり、nonce自体の独立 authority は未確認である。

成果物影響: nonce検査を設計メモへ送ると、既存 receiptの不一致を検出する gateも、receiptを参照する proof chainも追加されず、reservationの受理集合が現状のまま残る。

提案する修正: nonce receiptの実在を前提に、`source_commit`、PBS job ID、nonce、script SHAの束縛を明記する。submitter-owned receiptをauthorityと認めるなら明示裁定し、認めないなら scheduler-owned receiptを実装条件として停止する。

scope: 発火経路とartifactはscope内。authorityの採否は裁定パッケージ候補。

### 3. P5は現在のgeneric leafでは成立しない

severity: high

根拠: `orchestrator/campaign/campaign_claim.py:167` の `acquire_claim` は `ClaimRecord` の identity文字列しか受け取らず、`:184` でその文字列を filenameに使うだけである。プランの `acquire_protocol_claim` 案は `artifacts/s2-plan.md:38` で protocol/freezeを追加受領するため、floor専用経路ではP5を成立させられる。しかし `s8b_oracle_driver.py:1015` は依然として generic `acquire_claim` を呼ぶ。

成果物影響: merge後にcallerがrun identityをgeneric leafへ渡す経路が残れば、二重投入の claim が再び作成され、certified floor proofの単独性主張が崩れる。

提案する修正: required経路の全production callerを context-bearing helperへ移す。generic leafを内部APIへ閉じるか、protocol identityの検証済み型を必須にする。run identityを直接渡す回帰テストも追加する。

scope: floor S1はscope内。Oracleを含むAPI閉包は裁定パッケージ候補。

### 4. 別 `out_root` ではprotocol identityでも排他できない

severity: high

根拠: `campaign_claim.py:170` は claim root の共有時だけ排他が成立し、`:172` は cloneごとに別 `out_root` を使う実行を排他できないと明記する。Oracle側にも同じ制限が `s8b_oracle_driver.py:1021` にある。`tools/pegasus/README.md:187` も複数 clone間では同一 `out_root` を共有する前提である。

成果物影響: 同一 protocolでも別 `out_root` なら別 claim fileを作成でき、二重計測を検出できないため、throughput値とproof chainの単独性保証は共有root時に限定される。

提案する修正: canonicalな共有 claim rootをcontractまたは投入wrapperで固定し、未承認rootをfail-closedで拒否する。外部の共有lock authorityがない限り「protocol単位のglobal排他」とは表現しない。

scope: 現行のhash変更だけでは塞げず、裁定パッケージ候補。

### 5. 効く層のscope境界を成果物説明から分離できていない

severity: medium

根拠: `orchestrator/campaign/loop.py:61` の `_authorize_measurement` はattestationしか行わず、`:75` 以降にもclaim、reservation、resume拒否はない。`env_contract.py:7` もcontractは強制をしないと明記する。これは裁定材料の `materials/t330-s4-adjudication.md:62` と一致する。

一方、floorのclaimは `s8b_floor_campaign.py:4720`、OracleのG12 claimは `s8b_oracle_driver.py:1019` で別経路にある。G12 identity自体はprotocol由来だが、loop sinkは未保護である。

成果物影響: T-1097のtransport欠陥が直ると、loop経由の exploratory WAL、report、binary、throughputがsingle_process未検査のまま受理され、材料レポートのproof参照が未発火gateを含む。

提案する修正: `loop.py` を本 waveへ密輸入しない。その欠陥と影響をT-330の選択肢として親へ返し、tracked callerと同一waveで再裁定する。

scope: 本 waveのscope外。裁定パッケージ候補。

### 6. Unit A / Unit B の素集合は、完全なS2では維持できない

severity: medium

根拠: プランは `artifacts/s2-plan.md:214` で素集合とするが、script SHAやnonceを本当に照合するには、floorのreservation caller `s8b_floor_campaign.py:4693` とOracle caller `s8b_oracle_driver.py:920` へ現実側sourceを渡す必要がある。floor fileはclaim側のUnit Aが `s8b_floor_campaign.py:4716` から所有する。

成果物影響: 現在の分割のまま並列実装すると、host fixtureだけが緑になり、production callerがscript/nonce evidenceを渡さない部分実装が完成扱いされる。

提案する修正: API、floor caller、Oracle caller、PBS wrapperの所有境界を先に確定し、同一fileの変更は直列化する。Unit Bを `s8b_floor_campaign.py:4693` まで含む予約照合担当にする必要がある。

scope: 既裁定のS2内。ただしwrapperと編集面の拡張は裁定パッケージ候補。

### 7. `single_process=True / allow_resume=True` は現行registryにはないが、設計上は可能

severity: medium

根拠: `env_contract.py:64` と `env_contract.py:67` は二つのboolを独立に検査するだけで、組合せを禁止しない。registryは `env_contract.py:245` の `(True, False)` と `env_contract.py:284` の `(False, True)` だけである。一方、テストは `test_s8b_floor_campaign.py:3674` で `(True, True)` を構築できる。floorのresume拒否は `s8b_floor_campaign.py:4658` で `allow_resume=False` のときだけ発火する。

現行registered contractでは受理集合は変わらない。Pegasusはresumeを先に拒否し、linux-baremetalはclaimを取得しない。ただし将来 `(True, True)` を登録すると、one-shot claimが残る正当なresumeを拒否し、`allow_resume=True` が実質無効になる。

成果物影響: 将来の再開経路では正当なresumeの受理集合が狭まり、未完了runの材料レポートとproof chainが完成しなくなる可能性がある。

提案する修正: `(True, True)` を禁止するか、resume時のclaim handoffを設計する。少なくともsynthetic contractで受理集合を固定する。

scope: 現行の直接影響はない。contract設計の裁定パッケージ候補。

### 8. D75はfloorのlocal nameだけでは閉じない

severity: low

根拠: 現行floorは `s8b_floor_campaign.py:4716` でrun IDを `claim_identity` に入れ、同じ `_fresh_run_id` を `s8b_floor_campaign.py:4759` と `s8b_floor_campaign.py:5104` でrun identityに使う。`ClaimRecord` の field名は `campaign_identity` のまま `campaign_claim.py:34` にあり、generic leafはrun IDも受け入れられる。

成果物影響: local renameを逃すとrun identityがcampaign identityとしてclaim recordに入り、二重投入拒否のkeyが秒単位run IDへ戻る。

提案する修正: `protocol_claim_identity` と `campaign_run_id` を全callerで固定し、可能なら `campaign_identity` をprotocol専用value objectにする。

scope: S1内。generic APIの型閉包は裁定パッケージ候補。

## 親 brief の誤り

- `brief.md:70` はnonceを設計メモへ残しhost / script SHAだけを実装できるとする。しかし `brief.md:7` と `brief.md:20` の既裁定は3項目を同一waveで扱うため、この縮小は明示的な再裁定なしには不受理である。

- `brief.md:102` はUnit Bが `reservation.py` と `test_reservation.py` だけで閉じるとする。完全な3項目照合にはfloor caller、Oracle caller、PBS wrapperのsource closureが必要である。

- `brief.md:75` のP5は、identity文字列だけを受け取る現行leafが意味を判定できる前提になっている。実際には `campaign_claim.py:167` のgeneric leafでは判定できず、プランのcontext-bearing helperが必要である。

- `brief.md:66` は現行resume拒否を元runのclaim残存が主因とするが、現行Pegasus contractの直接の拒否は `s8b_floor_campaign.py:4658` の `allow_resume=False` である。

- `brief.md:46` のDW-O13充足は、fieldの形状があることまでなら正しいが、独立した現実側authorityまで充足したという意味なら過大である。script SHAはwrapper側にsourceがあり、nonce receiptは存在するがsubmitter-ownedである。

## 残る穴 (本 wave で塞がないもの)

- `loop.py` のsink-local強制。`brief.md:12` でscope外と確定しており、tracked callerの新設を伴うT-330再裁定が必要である。塞がない間、transport復旧後のexploratory成果物はsingle_process未検査で受理され得る。

- 別 `out_root` 間の排他。identity hashの変更だけでは塞がらず、共有claim rootまたは外部lock authorityが必要である。塞がない間、protocol単位の保証は共有root時だけである。

- scheduler-owned nonce receipt。workspaceにはsubmitter-ownedの実receiptがあるが、schedulerがnonceを発行・束縛したreceiptは確認できない。塞がない間、nonceの独立照合をproof chainの必須条件にできない。

- Oracle G12のidentity導出そのものは既にprotocol由来だが、generic leafとroot共有制約は残る。S1 floorだけを実装してOracle全体も強化済みとは報告できない。

- `(True, True)` resume contract。現行registryにはないため本waveの現行値は変えないが、将来登録時の受理集合は未確定である。

## 退けた自分の疑い

- 「nonce receiptは存在しない」は退ける。`output/env/pegasus/floor/attempts/submissions/f29f559a81afd2d3ba5dde05000a3471/submit-receipt.json:2` は実投入receiptで、`:3`、`:5`、`:6` にjob ID、script SHA、nonceがある。ただし現在のHEADとreceiptのsource commitは同一とは限らないため、現waveの成功計測IDと同一視はしない。

- 「script SHAの現実側sourceはない」は退ける。`tools/pegasus/floor_campaign.sh:508` の実行script hash、`:542` のcommit blob、`:519` の照合がある。T126にも `tools/pegasus/t126_qualification.sh:678` の実行script照合がある。

- 「Oracle G12 identityも時刻由来である」は退ける。`orchestrator/campaign/s8b_oracle_driver.py:1005` のpreimageはmanifest、freeze、schedule、campaign_idだけで、時刻・PID・UUIDを含まない。

- 「現行registryに `single_process=True / allow_resume=True` がある」は退ける。`env_contract.py:245` と `env_contract.py:284` の登録組合せは相互排他的である。ただし型とテストでは将来注入可能である。

- 「縮小プランの列挙済みUnit A / Unit Bが文字どおり同一fileを共有している」は退ける。`artifacts/s2-plan.md:214` から `:222` の列挙集合は素集合である。ただし既裁定のscript/nonceまで戻すと、必要consumer closureが追加され、同じ素集合を維持できない。