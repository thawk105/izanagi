## 1. 分母の同定 — (b) とは何か

**判定: 別物 — real。**

- §11 の (b) は、1 回の campaign run に source 1 行と validation 32 行を渡して順に評価する方式である。`docs/phase3-8c-wiring-design.md:624`
- 「1 回の `drive()` の戻り値から 33 行を合成」は、1 個の物理結果を33 recordsへ使い回す禁止案であり、(b) そのものではない。`docs/phase3-8c-wiring-design.md:367-380`

**「実行費用が33倍」の文面上の分母: (b) — real。**

§5.3 の「これは実行費用を33倍にする」は、直前の「33行をそれぞれ独立した campaign run とする」を受け、§11 でも (a) の33 runsと (b) の1 runを同じ択一行で比較している。したがって文書上の33倍は、**campaign run 本数 33 対1**の比である。禁止された「1 outcome → 33 records」を分母に置いた記述ではない。`docs/phase3-8c-wiring-design.md:374-380,624`

**親の「同じ行の中で分母が入れ替わった」という指摘: refuted。**

`parent-measurements.md:144-158` は33倍の分母を禁止案へ読み替えているが、文面はその読みを支持しない。ただし、campaign run 本数比をそのままノード時間比と呼んだ設計文書側の「33倍」は粗すぎる。この点を実費モデルで訂正する方向自体は real である。

**(b) の物理評価数: 正常に最後までループした場合は32回 — real。**

- source は先に評価される。
- source と同じ mask `m_s` の validation、すなわち **`query_ordinal = 1 + m_s`** が重複として skip される。「2行目」とは限らず、`m_s=0` の場合だけ2行目である。親の `parent-measurements.md:85-86` はここが不正確。
- `variant_id` は genome と `src_token` のみから決まり、ordinalやnonceを含まない。`orchestrator/campaign/pipeline.py:121-127`
- `done` はrun開始時に一度作られ、最初の出現を `done.add(v)` し、二度目を `v in done` でskipする。実装は設計のduplicate記述と一致する。`orchestrator/campaign/loop.py:462-466,522-529`

ただし、loop自体はskip後も後続genomeを評価するので物理評価は計32回になる一方、8cではmissing record以降をtombstone suffixにする。成功topologyの33 non-tombstone rowsは作れず、originはabortedになる。`docs/phase3-8c-wiring-design.md:355-360,268-282`

## 2. 費用の種類の分離

**親が4種類を分離していないという所見: real。**

| 費用 | V-8へ返せる倍率 | 判定 |
|---|---|---|
| 計算ノード占有時間 | 親のcampaign-engine surrogateは、6-passで `(a)/(b*)=1.032`、`(a)/(current b)=1.064`、correctness-only合成で1.136/1.171。ただし正式なend-to-end倍率ではない | **未確定** |
| 待ち行列込み実時間 | 1 jobなら `(queue + T_a)/(queue + T_b)`。33 jobsなら33個のqueue待ちが加わる | **数値なし** |
| job本数・queue回数 | 実行可能な1-job controllerがあれば1対1、runごとに投入するなら33対1 | **現行8cでは実行形未成立** |
| 人手の投入・監視・回収 | 1-jobなら投入手番はほぼ1対1だが、33 campaign成果の監視・回収は残る。33-jobなら最大33対1 | **未測定** |

親の1.03–1.17倍には次の問題がある。

- `F+S <= 33` はjob開始から最初のWALまでの、prologue/importを含む上限であり、分離したper-run実測値ではない。それを各runの点推定値として使っている。`parent-measurements.md:27-34,110-113`
- current (b) の式で定義した `D` を数値計算では0として落としている。`parent-measurements.md:98-113`
- correctness-only合成では一般式にある `g` を説明なく落としている。`parent-measurements.md:117-127`
- job/process共通費 `J` と、§3で述べる8c topology費を落としている。
- `8217 / 3999` は分母が算術上 `128 + 32×121 = 4000`。さらに親自身が「到達不能な組合せ」と認めているため、裁定用の実測上限とは呼べない。`parent-measurements.md:129-142`

したがって、これらは **B-10由来のcampaign-engine-only試算** と明記すべきで、V-8全体のノード時間倍率ではない。

### 33 campaign runsを1 jobで連続実行できるか

**genericなreservationだけなら条件付きで可能、現行8c topologyとしては成立していない — real。**

可能側の根拠:

- reservation bindingはjob ID・host・boot ID・deadlineを保持し、消費済み状態を持たない。同じjob内で再検査できる。`orchestrator/campaign/reservation.py:26-55,223-275`
- ただし `run_campaign()` は各呼出しで残時間を1秒しか要求せず、33 runs分のwalltime保証は外側にない。`orchestrator/campaign/loop.py:198-207`

成立しない側の根拠:

- 各 `run_campaign()` は開始前にclaimを取得する。`orchestrator/campaign/loop.py:194-229`
- claimはone-shotでreleaseがなく、同じcampaign identityの二度目は永続するclaim fileの `O_EXCL` で拒否される。`orchestrator/campaign/campaign_claim.py:74-79,383-434`
- identityが違っても、同じprotocol digestをlive ownerが持てば拒否される。`orchestrator/campaign/campaign_claim.py:348-371,409-416`
- campaign identity/protocol digestは `CampaignConfig` のcanonical preimageから作られ、`genomes` は含まれない。同じcfgをsingleton genomeごとに33回呼んでも同じidentityになる。`orchestrator/campaign/ident.py:196-235`
- 反対にcfgを変えて33 identities/digestsにすると、8cのissued capabilityが持つ単一 `campaign_id` と、全recordsのcampaign一致条件に衝突する。`docs/phase3-8c-wiring-design.md:264-273,407-435`
- そもそも33-row producerは未実装である。`docs/phase3-8c-wiring-design.md:379-380`

従って `s2-plan.md:95-105` と `parent-measurements.md:188-192` の「1 jobで連続実行できる」は、genericな異なるprotocol群についてのみ成立する条件文であり、V-8へそのまま移せない。33 jobsに分けても同一identityの永続claimは解消しない。

## 3. 8c topology固有のper-run費用

**親のB-10式が8c固有費を落としている — real。**

| 操作 | 成功時の回数 | 単位 |
|---|---:|---|
| fresh origin | 1 | origin/topology |
| origin capability・create-only run plan | 原則1 | origin/batch |
| `BatchReserved` | 1 | batch |
| `BatchCommitted` | 1。payload内に33 candidate commitments | batch |
| `BatchResultsPrepared` | 1 | batch |
| `BatchSealed` | 1 | batch |
| `OriginSealed` | 1 | origin |
| campaign authorization・reservation check・claim・layout/WAL replay | (a)では33、(b)では1 | campaign run |
| 物理attempt | (a)は33、current (b)は32 | row |
| terminal WAL/provenance | 物理attemptごと | row |
| `result-evidence/v1` | 成功topologyは33 | non-tombstone member |
| formal consumer | 1回だが33 records/WAL区間を検査 | sealed batch/origin |
| formal-consumer receipt | 1 | consumer実行 |
| ledger event receipt照合 | eventごとに1。receipt喪失時のみexact replay | ledger event |

根拠は、成功topologyが「fresh origin・exact 1 batch・33 member」であること、reserve/commitがbatch単位であることにある。`docs/phase3-8c-wiring-design.md:329-360`。result-evidenceはnon-tombstone memberごとにexact 1 record、formal consumerは集合全体を一度に検査する。`docs/phase3-8c-wiring-design.md:264-305`。receipt喪失時の再送もqueryごとではなく、各ledger eventのexact replayである。`docs/phase3-8c-wiring-design.md:496-512`

したがって、**「1 query ordinal = 1 campaign run」にしてもledger reserve/commit/sealは33回にならず、各1回のまま**である。33倍になるのはcampaign側のauthorization/claim/layout等と物理attempt/result-evidence側であり、ledger batch lifecycleではない。

current (b) では、duplicate位置 `q=1+m_s` から末尾がtombstoneになるため、result-evidenceは最大でもその前の `1+m_s` recordsだけで、残りには発行できない。一方、現行loopは後続の相異variantを評価し続けるので、tombstoneに捨てられる物理実行費も生じる。

generic campaign loopに「終端seal」が無いという親の指摘自体は正しいが、8cには別階層の `BatchSealed` と `OriginSealed` がある。`parent-measurements.md:165-169` を理由にseal費全体を式から除くのは誤りである。

## 4. 裁定への渡し方

**親がV-8の択一を明示的に選んでいるという心配: refuted。**

親成果物は (a)/(b)/(b*) の数字と制約を示し、(a) または (b) を採るとは結論していない。`parent-measurements.md:96-142`。(b) がcertifiable成果物を作れないとの記述は既存設計の正しさ条件であり、新しい推奨ではない。`parent-measurements.md:91-94`

**数字だけでは裁定できない残余がある — real。**

少なくとも次が未確定である。

- 比較対象をcurrent (b) のaborted成果とするか、33物理行を実行できる反実仮想 (b*) とするか。
- formal P6の `do_bench`、extime、reps。親自身も未測定と認める。`parent-measurements.md:176-186`
- 同一campaign/capabilityを維持したまま33 campaign runsを成立させるidentity・claim構成。
- 十分な1-job walltimeが予約可能か、jobを分けるか。
- queue待ちと人手運用費。
- fresh origin、ledger、evidence、formal consumerを含めた8c end-to-end費。
- current (b) のduplicate位置 `m_s`。tombstone/evidence費がこれで変わる。

**下流へ必要な形で渡っているか: refuted。**

D1561は数字を持って裁定するとし、D1555はV-8をV-7・runtime provisioning・production origin・P6の依存鎖の根に置く。`docs/decisions.md:48169-48183`、`docs/decisions.md:47986-48000`

現在の1.03–1.17倍だけでは、下流は必要なjob形状、walltime、campaign identity、capability数を決められない。返却物には最低限、

- campaign-engine-onlyノード時間帯
- topology共通費・per-row費
- queue/job/人手の条件分岐
- 現行identity/claimでは33-run形が成立していない事実
- formal P6 protocol未確定

を別欄で渡す必要がある。

## 5. 規律の検査

- **絶対規律2を緩める記述が混入しているという心配: refuted。** 親は費用を理由に物理実行保証を緩めず、current (b) を非certifiableと明記している。`s1-brief.md:20-25`、`parent-measurements.md:91-94`
- **過去の33倍をbytes単位で書き換える提案であるという心配: refuted。** briefと測定artifactを残したまま、訂正内容を別節へ追記している。`s1-brief.md:24-25`、`parent-measurements.md:160-174`
- **新しいgate・台帳・道具・一般化を本waveへ混入したという心配: refuted。** exact Fにはinstrumentationが必要と述べるだけで、実施せず上限扱いにしている。反実仮想 (b*) も提案ではなく比較モデルである。`parent-measurements.md:182-184`
- **実走していない検査を緑と報告したという心配: refuted。** 新規投入なしと明記され、pytest等の成功主張もない。`parent-measurements.md:1-4`

## 総括

real と裁定する所見:

- 設計文書の「33倍」はcampaign run本数比であり、ノード時間倍率ではない。放置すると (a) の資源費を最大33倍と誤認して裁定する。
- current (b) は `query_ordinal=1+m_s` をskipし、物理評価は32回、成果物はabortedになる。放置すると不等価な成果物同士を同一成果物単価として比較する。
- 33 runsを1 jobで回せるとの親の結論はactual 8cには移せない。one-shot claimと単一campaign capabilityが衝突する。放置するとjob/queue費を1回と仮定したまま、実行不能な案へ裁定する。
- B-10式はorigin/ledger/evidence/formal-consumer費を含まず、`D`・`g`・`J`にも未解決がある。放置するとcampaign-engine surrogateを8c end-to-end倍率として扱う。
- formal P6 protocol、queue、walltime、人手費は未確定。放置するとD1555の下流が必要とするprovisioning形を決められない。

refuted と裁定する親の心配:

- 「33倍は禁止された1 outcome→33 recordsを分母とし、V-8表の中で分母が入れ替わった」— refuted。文面上の分母は一貫して§11 (b) の1 campaign runである。
- 費用測定が物理実行保証を緩める、過去文書をbytes単位で書き換える、新しい機構をwaveへ混入する、という懸念はいずれもrefuted。

親が裁定へ返す前に必ず直すべき1件:

- **「33 campaign runsを1 jobで連続実行でき、`J` は1回」とする前提を撤回し、actual 8cではidentity・one-shot claim・単一campaign capabilityの整合が未成立であると明記すること。** ここを直さない限り、job数、queue回数、人手費、さらに1.03–1.17倍という式の前提まで確定しない。

以上は静的検査と射影成果物の読取りのみで、テスト・ベンチは実走していない。