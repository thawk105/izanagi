静的検査のみ実施した。`pegasus02` のため pytest・ビルド・計測は走らせていない。

## 独立再列挙

`grep -rn "tolerance_pct" --include=*.py` の結果を分類すると、production の直接面は以下だった。

- producer／入力面: `orchestrator/calibrator/cli.py:131,485-488,551`、`orchestrator/campaign/env_attestation.py:433-440`、`tools/pegasus/submit_certify.sh:7-42,177`、`tools/pegasus/certify_calibration.sh:154-164,730`
- schema／loader／直列化: `orchestrator/calibrator/schema_v2.py:218-239,499,530-554`、`orchestrator/campaign/env_attestation.py:490-502,521-525,643-692`
- 判定 consumer: `orchestrator/campaign/env_attestation.py:576-592`、`orchestrator/campaign/execution_guard.py:182-199`
- 設計案が参照者一覧から落とした production consumer: `orchestrator/campaign/silo_ladder_rung1.py:1962-1965,3401-3415`
- field 除去の間接 consumer: `tools/pegasus/run_probe.py:64-70`、`orchestrator/qualification/t126_driver.py:439-455`
- fixture／golden: `test_calibrator_certify.py:531-636`、`test_s8b_floor_campaign.py:3238-3243,3454-3477`、`test_silo_ladder_rung1_evidence.py:938-963`、`test_env_attestation.py:249-260`、`test_schema_v2.py:65-77,185-202`、`test_execution_guard.py:360-470`

実 artifact は、registered 1件と attempts 2件が `tolerance_pct=2.0`、calibration job-staging の observed artifact 15件が `pegasus-probe-output/v1` かつ `tolerance_pct=100.0` だった。

### [所見 B-1] 重大 — calibration pin 更新は凍結 floor protocol まで到達するのに、設計案は間接 pin を閉包から落としている

`FROZEN_MANIFEST` に `output/env/` が無いという記述自体は正しいが、そこから「frozen closure へ影響しない」とは結論できない。

具体的な失敗シナリオ: U-2 で calibration path/SHA を更新すると `contract_sha256` が変わる。現行の凍結 `floor_protocol.json` は旧 contract SHA を埋め込んでいるため、current registry と照合する validator が開始前に拒否し、floor campaign と ratified freeze replay が通らなくなる。旧 protocol bytes を書き換えれば、今度は `FROZEN_MANIFEST`、protocol SHA、selector journal、独立 golden が破れる。

根拠: `orchestrator/campaign/env_contract.py:145-160,186-192`、`output/s8b-freeze/floor_protocol.json:1`、`orchestrator/campaign/s8b_floor_contract.py:138-151`、`orchestrator/campaign/s8b_ratified_freeze.py:2870-2886,3025-3031`、`orchestrator/tests/test_frozen_artifacts.py:38-46,125-150`、`output/s8b-freeze/selector-runs/journal.jsonl:1`、`orchestrator/tests/test_s8b_protocol_builder.py:108-118,401-416`、`orchestrator/tests/test_s8b_floor_campaign.py:3238-3243`。

直し方の提案: U-2 より前に contract generation/version の移行設計を追加する。旧 frozen protocol は旧 contract を厳密に解決できるまま保持し、新 calibration は新 contract version・新 protocol・新 evidence に束縛する。旧 frozen bytes の貼り替えを pin closure に含めてはならない。

**成果物影響**: 直さない場合、既存 certified floor 選択と材料レポートの contract 参照が current registry から検証不能になり、受理集合は実質空、台帳には旧 protocol SHA と新 contract SHA が混在する。

### [所見 B-2] 高 — T-453 の median consumer を残したまま「全 consumer が policy を共有」として authority を先に land する順序は成立しない

設計案の参照者4者という列挙は不完全であり、T-453 が所有する2箇所は loader、issuer、canonical consumer のどの防壁も通らない独立経路である。

具体的な失敗シナリオ: authority 実装後も silo ladder は calibration JSON を直接読み、artifact 内 tolerance で中央値同士だけを比較する。全要素 canonical predicate なら落ちる帯外標本があっても median が近ければ `effective_clock_match=true` になりうる。後からT-453を実装すると同じ2箇所を再度変更する二重実装になる。

根拠: `orchestrator/campaign/silo_ladder_rung1.py:1931-1965,3393-3419`、`orchestrator/tests/test_silo_ladder_rung1_evidence.py:938-963`、`docs/decisions.md:7700-7704,7733-7735`、`docs/worklog.md:951-953`。設計案自身は参照者を4者だけとしている `s2-plan.md:19-24`。

直し方の提案: T-453 を authority completion の前提、または同一 landing closure にする。T-453 が canonical 全要素述語へ移るまで「全 consumer の policy authority 完了」を名乗らず、silo の policy不一致 negative controlもT-453側へ割り当てる。

**成果物影響**: 直さない場合、silo ladder の `all_pass` と試行台帳だけが広い median 受理集合を維持し、canonical receipt・材料レポートと同じ観測に異なる verdict を記録する。

### [所見 B-3] 高 — observed field 除去に schema version／履歴 loader の移行がなく、既存 staging artifact と hash 意味を同じ版のまま壊す

専用 observed 型は妥当だが、外部 JSON schemaと診断 hashの版を据え置いたまま shape を変える計画になっている。

具体的な失敗シナリオ: staging にある15件の `pegasus-probe-output/v1` は全て4-key clockと sentinel 100を持つ。新しい3-key observed exact loaderでは extra fieldで落ち、旧共有 loaderでは expected schemaの `<100` 化で落ちる。一方、新 probeも `pegasus-probe-output/v1` のまま3-key shapeを出すと、同じversionが二つの形を意味する。T-126の `observed_profile_sha256` も同一schema名のままpreimageが変わる。

根拠: `output/env/pegasus/calibration/job-staging/0:867876.nqsv/attestation-pre.json:1-4,1418-1425`、`orchestrator/campaign/env_attestation.py:450-505,508-518`、`tools/pegasus/run_probe.py:52-70`、`orchestrator/qualification/t126_driver.py:439-455`。registered artifact自体は `tolerance_pct=2.0` なので構造上は `<100` を通る `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1485-1493`。

直し方の提案: tolerance-free 出力を `pegasus-probe-output/v2` として発行し、v1 replay は「4 keysかつsentinelが厳密に100」の専用legacy parserで3-key内部型へ射影する。full-profile hashにも版付きprojectionを置き、同一schema名でhash意味を変えない。

**成果物影響**: 直さない場合、既存 staging evidence の再読・試行台帳の observed hash 照合が不能になり、新旧trialの参照が同じschema名なのに比較不能になる。

### [所見 B-4] 中 — fixture／golden の移行一覧が不足し、既存テスト契約を壊すかF109型の偽正例を残す

設計案は一部テストの置換を挙げるが、任意 tolerance を前提にした canonical vectors、clamped E2E probe、silo の median 再導出、独立 calibration/contract literalを閉包化していない。

具体的な失敗シナリオ: canonical predicateにpolicy一致を入れると、現行vectorsの10%、20%、微小値、0%、100%の期待値が一斉に変わる。observed型分離では`dataclasses.replace(... tolerance_pct=100.0)` fixtureが作れず、U-2ではfloor E2Eの旧 calibration/contract literalも不一致になる。安易に削除するとF109の代表性検査をさらに弱める。

根拠: `orchestrator/tests/test_execution_guard.py:360-470`、`orchestrator/tests/test_s8b_floor_campaign.py:3238-3243,3446-3477`、`orchestrator/tests/test_calibrator_certify.py:531-636`、`orchestrator/tests/test_env_attestation.py:249-260`、`orchestrator/tests/test_silo_ladder_rung1_evidence.py:938-963`、`docs/failures.md:2378-2390`。

直し方の提案: 実装前に fixture migration matrix を追加する。admission用canonical testはliteral 2.0に限定し、任意幅の数学的境界vectorはadmissionに露出しない純粋helperへ分離する。F109 fixtureはtolerance-free型へ移すが、synthetic clampである事実は保持する。

**成果物影響**: 直さない場合、受理集合を守る回帰検査が赤になるか削除され、certified選択・材料レポート・台帳へ非canonical median比較やsynthetic観測のpassが再流入しても検出できない。

## 総括

**NO-GO**。単一定数2.0、observed専用型、CLI入力面撤去という中心方針は維持できるが、現設計案の移行閉包と順序では既存の凍結成果物・silo consumer・staging evidenceを壊す。

must-fix:

- calibration更新で変わるcontract SHAから、frozen floor protocol・selector journal・goldenまでの世代付き移行を設計する。
- T-453をauthority完了の前提または同一landing closureにし、siloの2 consumerを取り残さない。
- tolerance-free observed出力をversion upし、既存`pegasus-probe-output/v1`の厳密な履歴replay経路を残す。
- fixture／golden／独立literal pinの移行matrixを追加し、F109型の偽正例を削除や恒真化で処理しない。