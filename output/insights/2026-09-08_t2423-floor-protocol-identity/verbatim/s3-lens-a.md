## 1. 規律 2 と受理集合

- 判定: **real 候補**
- file:line: `orchestrator/campaign/s8b_binary_admission.py:41-46,67-69,356-369,397-423`、`orchestrator/campaign/model.py:40-59`、`orchestrator/campaign/s8b_materialization.py:114-123`、`orchestrator/campaign/genome.py:223-251`、`orchestrator/campaign/p3_b4_floor_artifact_issuer.py:755-781`
- 親 brief の N2 は偽である。receipt に独立した `protocol` key はないが、portable record の artifact ごとの `binding.genome_canonical` は `Genome.canonical()` が生成する `protocol|flags` である。production writer はこれを `prepared.genome` から作り、validator は source の `genome_sha256`、materialization binding、receipt subject、artifact の binary SHA へ束縛する。さらに protocol を抽出する既存共有関数 `protocol_from_floor_genome()` がある。
- 現行 issuer が探す場所が top-level receipt なので発行不能なだけであり、「receipt から導出不能」ではない。P4 はこの実在する binary provenance を捨て、任意に宣言できる `spec.protocol` だけで発行を可能にする。v3/v4 の raw byte 集合は包含関係にないが、論理的な発行受理集合は「binary と束縛された protocol」から「人手宣言された canonical ID」へ広がる。
- 支配関係は、spec schema/validator 拡張には D1696 (`docs/decisions.md:51700-51718`) が直接効き、むしろ P2 に不利である。D1373 (`docs/decisions.md:43774-43805`) の exact source scan を新設する必要はないが、その source 事実へ寄せる理由は receipt binding を選ぶ方向を支持する。D1374 (`docs/decisions.md:43806-43825`) は、未検査の spec 宣言値を binary 確認済みの protocol と同じ顔で表示することに不利である。
- 成果物影響: P4 のままでは silo binary の floor を `protocol=mocc` と宣言した権威成果物と名前を発行でき、材料レポートと受理済み floor の意味が binary の事実から外れる。
- 推奨: **must-fix** — 段 4 の択を (a)/(b) から広げ、(c)「strict 検証済み record の `binding.genome_canonical` から既存 helper で protocol を導出し、最後に `_identifier` を課す」を第一候補にする。receipt schema、allowlist、source scan、validator は変更しない。

## 2. fail-closed の恒真化

- 判定: **real 候補**
- file:line: `orchestrator/campaign/floor_pair_driver.py:700-733,759-776,1136-1147,1194-1215`、`orchestrator/campaign/p3_b4_floor_artifact_issuer.py:411-433,736-804,847-860,890-895`
- P4 を採った場合、public issuer 経路では `threads`、`workload_identifier`、`campaign_identifier`、`protocol` の全 missing 分岐が到達不能になる。cells と artifacts は非空、全 cell の threads/workload は同じ calibration と一致し、campaigns も非空である。新 protocol は loader が exact key と `_identifier` で先に保証する。親 brief:23 の「threads 不一致・campaign 空は今も起こりうる」は反証される。
- ただし推奨する receipt 経路なら `protocol` 欠落だけは到達可能である。`_validate_binding()` は `genome_canonical` を非空文字列としては検査するが canonical Genome 文法までは検査しない。また artifact ごとに silo/mocc が混在する場合も protocol 集合が 1 値にならない。
- 成果物影響: P4 後に全 missing 機構を形だけ残すと `B4FloorIdentityError` は public 入力では発火しない防壁となり、issuer 単体の拒否集合が実質消える。
- 推奨: **must-fix** — threads/workload/campaign の死んだ missing 分岐は削除し、receipt-derived protocol の malformed/mixed 分岐と `B4FloorIdentityError` は残す。P4を維持する場合は全 missing 分岐を削除し、`_authority_value` の内部破損 guard だけを別 test で守るのが整合的だが、こちらは非推奨。

## 3. (P1) の (a)/(b) 択一

- 判定: **real 候補**
- file:line: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2423-floor-protocol-identity/verbatim-d1641.md:24-25`、`orchestrator/campaign/between_run_floor.py:59-72,196-212`、`orchestrator/campaign/p3_b4_floor_artifact_issuer.py:920-927,930-961,983-1000`
- (a) が壊すもの: protocol を artifact ごとの binary provenance から spec 全体の自己申告へ移し、異 protocol artifact の混在検知を失う。加えて不要な spec schema、spec SHA、HMAC 順序の変更を生む。
- (b) が壊すもの: D1641 の逐語 5 要素を4要素へ減らす。現在の `between_run_floor` は silo と mocc を既に扱い、mocc に protocol suffix を付けて出力を分離している。issuer から protocol segment を落とすと、他の4要素が同じ2 summaryは同一 targetになる。`_publish_create_only()` は上書きせず2件目を `artifact_exists` で拒否する。
- 「3 driver は今すべて silo」は、現時点で衝突 instance がないことだけを示す。`p3_b4_protocol.py:15-21` は確かに3軸とも silo だが、既存の mocc 経路と D1641 の将来を消す根拠にはならない。
- 成果物影響: (a) は誤った protocol 名の権威成果物を許し、(b) は別 protocol の正しい2件目を発行不能にする。
- 推奨: **must-fix、1と同根** — false dichotomy を解消し、(c) receipt binding 由来の5要素を段4へ提示する。

## 4. (P2) の置き場と一意性

- 判定: **real 候補**
- file:line: `orchestrator/campaign/floor_pair_driver.py:181-217,700-733,1021-1050`、`orchestrator/campaign/p3_b4_floor_artifact_issuer.py:755-781`
- top-level 1値では、reference=silo、candidate=mocc のような対照対を正確に表現できず、拒否もできない。`ArtifactConfig` に protocol はなく、`_validate_cross_references()` は artifact ID の存在しか検査しないため、spec はどちらか一方を全体の protocol として暗黙に主張して通る。
- 一方、既存 receipt は artifact ごとに `binding.genome_canonical` を持つ。issuer が全 artifact から抽出して集合が1値であることを要求すれば、artifact-level 宣言 keyや新 validatorを追加せずに混在を拒否できる。これは現行 `_derive_identity()` の `len(protocols) != 1` という既存意図とも一致する。
- D1696 は spec 側の機械検査を増やさない判断であり、top-level 宣言を binary の事実とみなす判断ではない。
- 成果物影響: P2 のままでは異 protocol 対の floor が一方の protocol 名で発行され、権威成果物と材料レポートが対の実体を隠す。
- 推奨: **must-fix、1と同根** — top-level keyを追加せず、receipt-derived protocol が全 artifact で1値でなければ発行拒否する。異 protocol 対そのものを権威 floor として許可したい場合だけ、identityを単一値以外へ変える別の**裁定パッケージ候補**とする。

## 5. (P3) の schema id bump

- 判定: **refuted 候補** — (a) を採る条件下で「instance ゼロだから v3 のままでよい」という反論は成立しない。
- file:line: `orchestrator/campaign/floor_pair_driver.py:56,1194-1204`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2423-floor-protocol-identity/verbatim-d1759.md:3-15`
- exact top-level key集合を変更するなら v4 が正しい。同一 v3 名で受理 wire contract を変える方が版識別を壊す。D1759 の直接対象は issuer が受理する summary producer 版だが、同一 ID で意味を変えない原則は整合する。
- 成果物影響: (a) で v3を据え置くと、同じ `floor-pair-spec/v3` が時点により異なる raw JSONを受理し、再現時の受理集合を識別できない。
- 推奨: **nit** — (a) を選ぶなら v4 は維持する。

- 判定: **real 候補** — N5 の「`spec.schema` が window/planへ書かれる」は字義どおり偽であり、N2修正後は P3自体が不要である。
- file:line: `orchestrator/campaign/floor_pair_driver.py:1298-1329,1405-1419,2190-2198,2643-2651,3004-3010,3047-3055`、`orchestrator/campaign/p3_b4_floor_artifact_issuer.py:38-40,665-674`
- `spec.schema` は HMAC rank の入力で、planへ直に書かれるのは `PLAN_SCHEMA` と `spec_sha256`、windowは `WINDOW_SCHEMA`、summaryは `SUMMARY_SCHEMA` である。liveな `floor-pair-spec/v3` literalは driver定数と `test_floor_pair_driver.py:484` の2箇所だけで、window validatorやissuer summary pinに v3 spec literalはない。
- 成果物影響: v4化と protocol keyは spec SHAとHMAC順序を変え、その sessions、plan hash、window、summary bytesへ伝播するが、PLAN/WINDOW/SUMMARY schema ID自体は変えない。
- 推奨: **must-fix、1と同根** — receipt経路を採れば spec contractは変わらないため `SPEC_SCHEMA` はv3のまま、driverとHMAC goldenも変更しない。なお(a)を採るならS2が挙げたHMAC golden更新は必須。

## 6. テストの負例

- 判定: **real 候補**
- file:line: `orchestrator/tests/test_floor_pair_driver.py:52-73`、`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:40-84,217-250,473-497`、`orchestrator/campaign/s8b_binary_admission.py:131-147`
- 現行 fixture は `genome_canonical` に `{"fixture":"candidate"}` という JSON文字列を入れており、実 production の `protocol|flags` 形式ではない。この fixture が receipt内の利用可能な protocol 事実を隠し、N2の誤判定を誘発している。
- P4後には「loaderを通ったがidentityを組めない」public入力は存在しない。S2は `_authority_value()` へ破損状態を直接渡す内部負例を残しているので、issuer単体負例が完全にゼロという批判は技術的には refuted だが、public経路の負例ではない。
- 残すべき本物の負例は、candidate receiptを `mocc|FIXTURE=1`、reference receiptを `silo|FIXTURE=1` とし、全 hashとreceipt bindingを正しく再計算するもの。`load_frozen_spec()` は通るが、issuerは protocol集合が2値なので `missing_identity_elements == ("protocol",)`、発行は `B4FloorIdentityError` で拒否すべきである。
- 正例は全 artifactを `mocc|FIXTURE=1` とし、名前と `artifact_identity.protocol` がともに `mocc` であることを検査する。これで `"silo"` 固定 fallbackも殺せる。malformed canonical genomeの負例も追加可能だが、混在負例の方が成果物意味へ直結する。
- 成果物影響: loader拒否だけの負例では、issuerが異 protocol binariesを1 protocolとして発行する変異や `silo` 固定 fallbackを検知できない。
- 推奨: **must-fix** — fixtureを実 canonical Genome形式へ直し、receipt-derived正例と異 protocol混在のissuer負例を独立nodeidで置く。内部 `_authority_value` 破損 testは補助として残す。

## 7. 親 brief の N1〜N7

- 判定: **refuted 候補、N1への反証は不成立**
- file:line: `orchestrator/campaign/floor_pair_driver.py:56`、`orchestrator/tests/test_floor_pair_driver.py:484`、`output/insights/2026-09-07_b4-paired-session-driver/verbatim/s2-plan.md:25`、同 `mutation-ledger-probe-round2.json:35`
- `git grep` は live literal 2件と insights 3件だけだった。`output/` の全 JSON走査でも `"schema": "floor-pair-spec/v3"` は0件で、worktreeもcleanだった。
- 成果物影響: 既存の実 specや権威成果物を移行する必要はない。
- 推奨: **nit** — N1は維持し、insightsの文字列はinstanceでない旨を残す。

- 判定: **real 候補、N2は反証**
- file:line: `orchestrator/campaign/s8b_binary_admission.py:41-46,67-69`、`orchestrator/campaign/model.py:56-59`、`orchestrator/campaign/genome.py:223-251`
- `PORTABLE_SORT_BEST_BUILT_KEYS` に直接 protocol keyはないが、基底集合から `binding` を継承し、その `genome_canonical` の先頭が protocolである。
- 成果物影響: N2を前提にしたP1〜P4の変更面は不要となり、誤った受理集合変更を避けられる。
- 推奨: **must-fix、1と同根**。

- 判定: **refuted 候補、N3への反証は不成立**
- file:line: `orchestrator/campaign/between_run_floor.py:59-72,201-207`、`orchestrator/campaign/p3_b4_protocol.py:15-21`
- protocolの意味が CC protocol名であること、現行3 driverがsiloであることは支持される。
- 成果物影響: 現行B4の正しい receipt-derived identity は `silo` になる。
- 推奨: **nit** — N3は維持する。

- 判定: **real 候補、N4の推論は一部反証**
- file:line: `docs/decisions.md:43774-43825,51700-51718`
- D1373が新しいsource scanを要求しない点は正しい。しかしD1696は spec schema/validator拡張を見送った裁定であり、P2を積極的に支える根拠ではない。既存 receipt bindingを読むことは新 gateではない。
- 成果物影響: N4をP2の根拠にすると、machine-bound事実を人手宣言へ弱める。
- 推奨: **must-fix、1と同根**。

- 判定: **real 候補、N5は字義反証**
- file:line: `orchestrator/campaign/floor_pair_driver.py:1302,1316,1328,1405-1419,2190-2198,3004-3010`
- `spec.schema` は成果物へ直接書かれない。downstream bytesが変わるという結論だけはspec SHAとHMAC順序の伝播により正しい。
- 成果物影響: 変更時にはplan/window/summary bytesとHMAC goldenが変わるが、下流schema pin変更は不要。
- 推奨: **nit** — briefの表現をS2の訂正へ合わせる。

- 判定: **real 候補、N6の状態は陳腐化**
- file:line: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:1200-1292`、同 `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:109,510-515`
- consult時点のt2412は未commit差分ではなく、cleanな `4f8601fb7` までcommit済みである。ただし現在のmain `6172ea26b` の祖先ではなく、cwdは依然 `34af5a571` なので未着地という部分だけは真である。
- 成果物影響: 古いfixtureとHEAD束縛を基に実装すると、t2412着地時にspec load可否とissuer testの意味が再度変わる。
- 推奨: **must-fix** — 最終受入前にt2412のcommitted差分を取り込み、特にloaderとissuer fixtureを再読する。

- 判定: **refuted 候補、N7への反証は不成立**
- file:line: `orchestrator/campaign/p3_b4_floor_artifact_issuer.py:38-40,669-674`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2423-floor-protocol-identity/verbatim-d1759.md:3-15`
- D1759の直接pinは `floor-pair-summary/v3` であり、spec版ではない。
- 成果物影響: receipt経路への修正はsummaryの受理版集合を変えない。
- 推奨: **nit** — D1759はspec v4の類推根拠に限り、直接命令とは書かない。

## 総括

must-fix候補は重複をまとめて4件: receipt canonicalへの導出訂正、missing分岐整理、実 receipt形式の正負テスト、t2412取り込み。
最大の懸念は、実在するbinary-bound protocolを見落とし、自己申告値で権威成果物を発行する受理集合へ変えること。
親 briefへの反証あり: N2とN5、N6の状態、N4の解釈。
裁定パッケージ候補あり: (c) receipt-derived identityの追加、および異 protocol対を将来許すか。
read-only制約に従いpytestは実行していない。