## 前提の確認

- 実装・ファイル変更・pytest 実行はしていない。指定資料と repository 内の source・成果物だけを静的に確認した。
- 生産側は [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:128) l.128-158 が `--binary` を必須受領し、certify 経路では l.745-750 が実 binary の SHA-256 を検査する。[`_assemble_v2`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:644) l.644-663 は `noise_floor.kind` を書くが genome を書かない。
- trace-disabled の実体検査は [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:187) l.187-212 の `nm -C` であり、この関数と呼出し位置 l.745、l.1064-1067は変更しない。
- genome の既存正準化 API は [model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/model.py:39) l.39-63 の `Genome.canonical()` と `Genome.cmake_defines()`。既存 build API は [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/buildcache.py:3017) l.3017-3068 が `Genome` から configure argv と binary を作り、l.3101-3103、l.3165-3167 で trace-disabled を検査する。`BuildResult` は l.653-678 に genome、binary、SHA-256、argv を保持する。
- 対照の [between_run_floor.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/between_run_floor.py:371) l.371-389 は genome から build し、l.238-251 が `baseline.canonical()` を成果物へ記録している。
- 消費側は [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:353) l.353-358 の直下 glob が原因。genome 有無による確認済み protocol と歴史的仮定の分離は l.391-405 に実在し、変更しない。
- 既存 registered 2 件の SHA-256 はファイル名と一致した。いずれも `calibration/v2`、threads=48、rratio=50、records=1,000,000、genome 欠落である。bytes は変更しない。
- D19 に従い、within-run は一測定の品質、between-run は run 間採否の下限という用途を維持する。`records` の選択、既定 sweep、CV 算出には触れない。

## 生産側の裁定案

**候補 (a): producer が genome から build する**

- producer が `Genome` を build API へ渡すため、genome は producer が実際に使用した build 入力という事実になる。ELF bytes から macro を逆算するわけではないが、producer 管理下の build 入力、出力 binary、出力 SHA-256を一つの経路で結べる。
- 実在する先例は `between_run_floor.py` l.371-389、正準化は `model.py` l.56-63、build は `buildcache.py` l.3017-3219。
- ただし certified calibration は [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/tools/pegasus/certify_calibration.sh:516) l.516-547 で pinned-clean worktree、専用依存物、fresh `/scr` build、condition gate、別建ての `nm` 検査を済ませてから calibrator を呼ぶ。これを `buildcache.build()` に置換すると既存の性能用 build 経路と検証経路、予約時間、熱状態の順序まで変更する。
- T-2136 の「記録と接続だけ」を超えるため不採用。

**候補 (b): 手渡し binary と申告 genome を照合する**

- `--genome` を追加するだけなら申告にすぎず、D1374 が退けた「知らない出所を文字列で補う」を再生産する。
- 事実にするには、同一 source、toolchain、dependency、configure argv で再 build し、手渡し binary と byte equality または SHA-256 equality を確認する必要がある。既存 `buildcache.build()` と certified fresh build は build root・依存物経路が異なるため、現行 APIにその照合経路はない。
- 単なる `CMakeCache.txt` 照合や binary basename 照合も binary bytes との対応を証明しない。不採用。

**候補 (c): acquisition receipt から導出する。これを採用する**

- [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/tools/pegasus/certify_calibration.sh:527) l.527-538 は実行した configure/build argv を配列で保持する。l.539-542 がその出力 binary の SHA-256 を取得し、l.585-647 が同じ argv と SHA-256 を acquisition receipt に格納する。
- calibrator は [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:745) l.745-750 で手渡し binary と CLI SHAを照合し、l.599-640、特に l.617-618 で receipt 内 SHAとも照合する。
- したがって genome は ELF bytes そのものから逆解析する事実ではないが、「実行済み build argvから導出し、その build output と同じ SHAを持つ測定 binary」という process provenance に基づく事実である。caller の自由申告ではない。
- 過去 record の consumer 側で build argv を解釈して genome を後付け認定することはしない。新規 producer が新規成果物へ明示 field を書く場合だけ用いるため、D1374を侵さない。

**実装内容**

- [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:32) l.32-49 に既存 `Genome` API の import を追加する。
- l.354-369 直後に、`acquisition_receipt.ccbench.build_argv` から canonical genome を導出する局所 helper を置く。新しい汎用 parser module は作らない。
- helper は次を全て満たさなければ `CertificationError("receipt-genome-invalid", ...)` で停止する。

  - configure と build の区切り `&&` が一つだけある。
  - build 側に `--target ycsb_<protocol>.exe` が一つだけある。
  - 測定 binary の basename がその target と一致する。
  - configure 側の `-DCCBENCH_<FLAG>=<整数>` を全て回収する。
  - flag 重複、値なし、非整数、build 側への CCBENCH 定義混入を拒否する。
  - `CCBENCH_TRACE` はちょうど一つで値が `0` でなければならない。`TRACE` は `Genome.flags` へ入れない。
  - TRACE 以外の flag が一つ以上必要。
  - `Genome(protocol, flags).canonical()` で正準文字列を作る。

- [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:745) l.745-750 の binary SHA確認後に一度だけ導出し、benchmark 前に不正 receipt を落とす。
- [`_assemble_v2`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/cli.py:644) l.644-663 に必須の `genome` 引数を追加し、top-level `"genome": genome` を書く。schema preflight、accepted、rejected の全 v2 組立呼出し l.774-781、l.907-908、l.1014-1017へ同じ導出値を渡す。
- 非 certify 経路 l.1064-1092 には acquisition receipt がなく、bytesとの対応を事実として検査できないため genome を自己申告で追加しない。従来どおり legacy record とし、層 3 の `genome-absent-legacy-record` 扱いに残す。公式 certified 経路をT-2136の生産側閉包とする。

## 消費側の裁定案

**候補 (a): registered の glob 追加と field 絞り込み**

- 新規 record の `genome` なら protocol 絞り込みができるが、凍結された既存2件には追加 field がない。
- 両方が同じ legacy silo 仮定、threads、records、workload に一致するため、registered glob の追加だけでは [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:432) l.432-433 の複数一致を発火させる。
- 既存 bytes を変えずに両者を区別できる artifact 内 field はない。不採用。

**候補 (b): env contract の content-addressed pin**

経路は実在する。ただし `AdmittedCampaign` や WAL が直接 `calibration_ref` を持つのではなく、検証済み `campaign.lock` を通る。

- `AdmittedCampaign` は [artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/artifact_admission.py:295) l.295-327 の layout、WAL records、decision、verifier epoch だけで、`calibration_ref` はない。
- 層 3 は [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:571) l.571-572 で `DecodedCampaignLock` を既に保持する。
- [campaign_lock.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/campaign_lock.py:84) l.84-114 の v2 authority に `environment_contract_sha256` がある。codec は l.215-250 で exact 検証する。
- [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:881) l.881-913 の `resolve_by_contract_sha256(..., expected_env_tag=...)` が全世代から一意かつ ever-active な `GenerationEntry` を返す。
- `GenerationEntry.contract.calibration_ref` は [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:80) l.80-96、l.99-119 の path と SHA-256。
- WAL は [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/wal.py:1387) l.1387-1421 で lock の contract hash を解決し、l.1447-1459 で commit と env_tag を照合するが、calibration path 自体は持たない。

したがって (b) は実装可能である。

**候補 (c): pin 優先と legacy fallback の併用。これを採用する**

- authority を持つ v2 campaign の within-run は contract が pin した1件だけを候補にする。`registered/` 全体は走査しない。
- authority のない v1 campaign は現在の直下走査をそのまま使う。D1374 の歴史的 silo fallback と表示を維持する。
- between-run は env contract の calibration pinとは用途が異なるため、現行の directory 直下走査を維持する。D19 に沿う。
- これにより既存 registered 2件が同時候補になることはない。現行 activation は `00000001.json` が pegasus generation 1を指し、registry の g1/g2 pin は [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/env_contract.py:253) l.253-282 にある。g2を新たに activate したとは扱わない。

**実装内容**

- [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:53) l.53-59 の import に既存 `env_contract` を追加する。
- l.307-352 付近に `DecodedCampaignLock` と一意な WAL env_tag から contract calibration ref を得る局所 helper を追加する。

  - v1で `authority is None` なら `None` を返す。
  - v2なら `resolve_by_contract_sha256(authority.environment_contract_sha256, expected_env_tag=env_tag)` を呼ぶ。
  - 解決失敗、never-active、env不一致は `Layer3ReportError` へ変換して fail closed にする。

- [`_calibration_floors`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:353) l.353-472 に任意の contract pinを渡す引数を追加する。

  - 直下 `*.json` は従来どおり列挙する。
  - pin がある場合だけ、その repository-relative path 1件を追加して読む。
  - pin path が repo外、対象 env の calibration directory 外、通常ファイルでない場合は拒否する。
  - bytes の SHA-256が `calibration_ref.sha256` と一致しなければ拒否する。
  - within-run 候補は pin された path だけに限定し、直下の別 within-run record は `skipped_unpinned_within_run` として検索詳細へ残す。
  - between-run 候補は従来どおり直下だけを使う。
  - pin が直下 file 自身を指す linux-baremetal の場合は path を重複排除する。
  - l.391-405 の canonical genome と `genome-absent-legacy-record` 分岐は変更しない。

- [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/layer3_report.py:620) l.620-642 で、env_tag確定後に decoded lockから pinを解決し `_calibration_floors` へ渡す。
- `layer3_schema.json` は変更しない。成功時の既存 `source.path` と `source.sha256` で registered pathとcontent addressを表せる。protocol の根拠は既存 `protocol_match_basis` で区別する。
- env contract、activation record、登録済み calibration bytes は編集しない。D1377に従い、新 floor の権威化や activation は行わない。

## schema の影響

- 現在の [schema_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/schema_v2.py:563) l.563-567 の `_TOP_KEYS` に `genome` はなく、l.740-758 の `_exact` により、新 field を足しただけでは必ず拒否される。
- `schema_version` は `calibration/v2` のままとする。変更は provenance の加法 field であり、次の二つの exact shapeだけを明示的に受理する。

  - 凍結 legacy shape: 現在の `_TOP_KEYS`。typed result の `genome` は `None`。
  - 新規 producer shape: `_TOP_KEYS | {"genome"}`。`genome` は canonical な非空文字列。

- [CalibrationV2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/calibrator/schema_v2.py:486) l.486-503 に `genome: Union[str, None]` を追加する。
- l.703-739 付近に stdlib-only の canonical genome 検査を追加する。`protocol|A=1,B=0` 形、非空 protocol/body、整数値、重複なし、flag名順、再構成値との完全一致を検査する。`schema_v2.py` の stdlib-only leafを崩す importは追加しない。
- `validate_calibration_v2` l.740-773 は上記2 shape以外の欠落・未知 field を従来どおり拒否する。任意 field 一般化にはしない。
- schemaをv3へ上げると、[calibration_verify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/calibration_verify.py:41) l.41-63 と l.116-142、env contract activation、fixture群へ二重 validatorを追加する必要がある。これはT-2136の記録追加に対して過大で、新しい互換層にもなるため採らない。
- 既存2件の再検証は [test_env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_env_attestation.py:1297) l.1297-1319 の実 bytes + 固定 SHA parametrizationをそのまま維持する。legacy shapeを受理するため赤にならない設計である。今回、実測はしていない。

## 編集する file と行

**Production file**

- `orchestrator/calibrator/cli.py`

  - l.32-49: `Genome` import。
  - l.354-369 後: receipt build argvからの canonical genome導出 helper。
  - l.644-663: `_assemble_v2` の必須 genome引数と top-level field。
  - l.745-750 後: binary SHA照合後、benchmark前の導出。
  - l.774-781、l.907-908、l.1014-1017: 全組立呼出しへの同一 genome伝播。
  - l.187-212、l.1064-1075 の trace検査・非 certify測定条件は変更しない。

- `orchestrator/calibrator/schema_v2.py`

  - l.486-503: typed `genome`。
  - l.563-567: legacy/newの二つの exact top-level key集合。
  - l.703-739 付近: canonical genome validator。
  - l.740-773: 二つの shapeを分岐して検証。

- `orchestrator/campaign/layer3_report.py`

  - l.53-68: `env_contract` import。
  - l.307-352 付近: decoded lockからcalibration refを解決する helper。
  - l.353-472: pin 1件と直下走査を用途別に併用。
  - l.620-642: build_reportからpinを解決・伝播。

**Test file**

- `orchestrator/tests/test_calibrator_certify.py`

  - l.303-336: `_receipt` の `build_argv` を実契約と同形の configure、`&&`、build targetへ更新。
  - l.369-418: fixture binary名を target と一致させる。
  - l.482-560 付近: malformed/duplicate/TRACE/target不一致をbenchmark前に拒否する負例。
  - l.1117-1165 付近: published artifactの exact canonical genomeを検査。

- `orchestrator/tests/test_schema_v2.py`

  - l.34-114: legacy `_valid_document` は genome欠落のまま保持。
  - l.136-168 付近: genome付きshapeの正例、legacy shapeの正例、malformed canonical値と未知 fieldの負例。
  - registered 2件の bytesはfixtureへコピーせず、既存 `test_env_attestation.py` l.1297-1319を回帰閉包として使う。

- `orchestrator/tests/test_layer3_report.py`

  - l.80-112、l.204-240: fixture helperへ authorization、env_tag、records、threadsの任意指定を最小追加。
  - l.2772-3112: registered pin、2件衝突回避、hash不一致、mocc canonical genome、v1 legacy fallbackの試験を追加。
  - l.2948-2997 のD1374回帰は削除・期待変更しない。
  - l.3060-3073 のv1複数一致 fail-closedも維持する。

`tools/pegasus/certify_calibration.sh`、`env_contract.py`、activation JSON、`layer3_schema.json`、既存登録 artifact、between-run producerは編集しない。

## consumer test の一覧

production module名またはproduction path名を `orchestrator/tests/` で `rg` した静的参照閉包である。

- `orchestrator.calibrator.cli`

  - `test_calibrator_certify.py:21`
  - `test_effective_clock_policy.py:16`

- `orchestrator.calibrator.schema_v2` または `schema_v2.py`

  - `test_calibrator_certify.py:27`
  - `test_env_attestation.py:25`
  - `test_env_contract.py:95`
  - `test_env_contract_activation.py:39`
  - `test_execution_guard.py:28`
  - `test_pegasus_floor_tools.py:217`
  - `test_pegasus_tools.py:659`
  - `test_s8b_freeze_io.py:28`
  - `test_s8b_ratified_freeze.py:34`
  - `test_schema_v2.py:17`
  - `test_silo_ladder_rung1_driver.py:979`
  - `test_t126_pegasus_tools.py:1484`
  - `test_t126_qualification_driver.py:25`
  - `test_t419_probe_causality.py:29`

- `orchestrator.campaign.layer3_report` または `layer3_report.py`

  - `test_autonomous_trial_completeness.py:26`
  - `test_ccbench_spawn_sites.py:110`
  - `test_layer3_admission_diagnosis.py:21`
  - `test_layer3_report.py:31`
  - `test_official_perf_closure.py:53`
  - `test_p3_autonomous_workload_trial.py:3497`
  - `test_s8b_oracle_driver.py:5034`
  - `test_s8c_acceptance_receipt_v2.py:342`
  - `test_t126_pegasus_tools.py:451`
  - `test_t126_qualification_artifacts.py:18`
  - `test_trial_registry.py:24`

焦点実測は親が少なくとも編集対象3 test fileを走らせ、その後この参照閉包を `tools/run_tests.py` 経由で確認する。ここでは緑と報告しない。

## 変異事前登録の候補

1. **producer が genome fieldを書かない変異**

   - `test_calibrator_certify.py:1117` 付近へ、published/attempt両 artifactの `validated.genome` が独立 literal `silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` と一致する試験を追加する。
   - `_assemble_v2` の代入を削ると、schemaはlegacy shapeを意図的に受理するが、このproducer試験が `None != expected` で落ちる。

2. **build targetを無視して protocolをliteral siloにする変異**

   - `test_calibrator_certify.py:482` 付近へ mocc targetとmocc flagのhelper単体正例を追加する。
   - protocolを固定すると期待する `mocc|...` と不一致で落ちる。siloだけの試験では恒真化しうるため、moccを使う。

3. **`CCBENCH_TRACE=1` を無視する変異**

   - `test_calibrator_certify.py:530` 付近のbenchmark前拒否試験で receiptだけをTRACE=1にし、`calibrate_calls == []`、非0、registered不存在、reason=`receipt-genome-invalid` を要求する。
   - helperがTRACEを単に捨てる変異ではbenchmarkが呼ばれ、試験が落ちる。実 binary側の既存 `nm` 検査とは独立した面を撃つ。

4. **重複flagまたはtarget欠落を最後勝ちで受理する変異**

   - 同じ位置に `BACK_OFF=0` と `BACK_OFF=1` の重複、`--target` 欠落をparametrizeする。
   - parserがdict上書きやbasename fallbackをするとbenchmarkが呼ばれ、`calibrate_calls == []` で落ちる。

5. **schemaが非canonical genomeを単なる文字列として受理する変異**

   - `test_schema_v2.py:136` 付近で `silo|Z=1,A=0`、`silo|A=1,A=2`、`silo|A=x`、`silo|` を拒否させる。
   - canonical検査を `_text` だけへ弱めると `CalibrationSchemaError` が出ずに落ちる。

6. **consumerがcontract pinを無視してregistered全件をglobする変異**

   - `test_layer3_report.py:2772` 付近で凍結2件をtmp outputのregisteredへbyte copyし、pegasus g1 authorityを持つv2 campaignを構築する。
   - reportが `calibration-753f535a8d024727.json` のみをsourceに選び、legacy basisを表示することを要求する。
   - registered globへ戻すと2件一致エラー、またはg2選択でsource path不一致となる。

7. **content-addressのSHA照合を削る変異**

   - pin対象JSONへ意味を変えない空白を加えてvalid JSONのままSHAだけ変える試験を追加する。
   - 正常系は `Layer3ReportError` の calibration SHA不一致で落ちる。SHA検査を削ると値はそのまま一致してreportが生成され、試験が落ちる。

8. **D1374のlegacy表示を削る変異**

   - 既存 `test_layer3_report.py:2948-2970` が `protocol_match_basis == "genome-absent-legacy-record"` を要求する。
   - field削除、canonical確認済み扱い、moccへのfallback拡張はいずれも既存試験で落ちる。

**候補から外す点**

- 「registered 2件のファイル名またはSHAが異なる」だけの試験は、consumerが両方をglobしても緑なので恒真になりうる。
- test側で作った genome を同じ production helperで再parseするだけのround-tripは、producerとtestの共通誤りを検出できない。期待値は独立 literalにする。
- source textに `"genome"` があることだけをgrepする試験は、実成果物への伝播が切れても緑なので採らない。
- fixtureへ直接 `"genome"` を挿入して存在だけをassertする試験はproducerを通らないため採らない。

## scope 外の所見

- [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/tools/pegasus/certify_calibration.sh:527) l.527-540 は `CCBENCH_*` flagと `ycsb_silo.exe` をhardcodeしている。T-2136でproducerがmoccを正しく記録できるようになっても、このwrapper自体はmoccを生産できない。launcher一般化は別課題とし、本プランへ混ぜない。
- 現在のregistered 2件はいずれもgenome欠落なので、contract pinで衝突は避けられてもprotocolを確認済みにはできない。silo campaignへ入る場合も必ず `genome-absent-legacy-record` のままである。
- pegasus g2はregistryにはあるが、[test_env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/tests/test_env_contract.py:618) l.618-621 が示すとおりnever-activeとしてresolverに拒否される。本waveでactivationを変更しない。
- 現在のenv contractはenvごとにcalibration refを一つだけ持ち、protocol/workload別registryではない。将来、別protocolや別workloadの権威あるfloorをactivateする設計はD1377の手続きと別課題である。
- `Genome.canonical()` 自体は空flagsを `protocol|` として生成できる一方、floor consumerは [genome.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2136-within-run-floor-protocol/orchestrator/campaign/genome.py:121) l.121-148 で空bodyを拒否する。この一般的なAPI差はT-2136では触らず、receipt導出helper側で非TRACE flagを一つ以上要求する。

## 総括

採用案は、生産側が certified acquisition receipt の実行済み build argvから canonical genomeを導出し、binary SHAとの既存照合を根拠に新規 `calibration/v2` 成果物へ記録する方式である。自己申告や過去bytesの書換えは行わない。

消費側はregistered全走査をせず、v2 `campaign.lock` が束縛した ever-active env contract の `calibration_ref` 1件だけをwithin-run候補にする。v1の直下走査、D1374のlegacy表示、between-runの用途、trace検査、飽和判定は維持する。これで既存2件の衝突を避けつつ、将来のgenome付き非silo certified calibrationを確認済みprotocolとして層3へ接続できる。