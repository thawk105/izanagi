## brief 訂正

対象は HEAD `5efd69367`。以下の観測値は親の [probe-2.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2812-old-series-realignment/evidence/probe-2.json) と CLI 記録による。本段ではコード・成果物を書き換えず、テストも実行していない。コード参照の `campaign/` は `orchestrator/campaign/` を指す。

1. **P1「K2 は追加整合不要」は pin 整合に限定する。** H で候補が走った事実はあるが、pair は one-shot claim で不成立。stock は未 build。現行 main で旧 pair lock を読む場合は、policy が一致しても exact-63→85 の codec 変更で拒否される。
2. **P2 は attempt-0003 の認可を欠く。** `paper_story_a1_paired.py:228` の `V3_SIZED_RERUN_AUTHORIZATIONS` は attempt-0002 だけを列挙する。H の境界通過は attempt-0003 の受理を意味しない。
3. **P3 の S' は SHA の到達可能性まで確認済み。live 型の発行は未実装。** probe が使った `HistoricalBuildAdmissionPolicy` を渡すだけでは `s8b_binary_admission.py:369` が拒否する。
4. **「g1 を塞ぐのは policy だけ」は段階4に限る。** 候補文書の scan hit、W-4 の未承認 spec、実行環境・store・予算等は残る。親の gate-check は `allowed:false`、拒否2件、held checks 3件。
5. **N は reseal・再測定・批准だけでは実行可能にならない。** `s8b_ratified_freeze.py:3273` は generation 1 以外を `certificate-generation-scope` で拒否する。g2 を使う N には別途、世代・証明書の設計裁定が要る。
6. **reseal 直後に resolver が成功するわけではない。** 新 file を commit する前は `_scan_floor_protocol_index_at_commit` の HEAD blob 検査で拒否される（`s8b_floor_campaign.py:984`）。commit 後に初めて新 pin の一意候補になる。
7. **READMIT-STOCK は再 admission 成功の実測ではない。** g1/B-4 について実行したのは、非 stock class の registry membership 確認。`G1-BIN-HIST` も `expected_policy=None` による歴史検証であり、S' の live 成功実測ではない。

## K2

**現状の拒否。**

| 証拠 | 観測／静的根拠 |
|---|---|
| `K2-PIN-NEW` | `HEAD (e9e477ca…) が pin (511c9538…) と不一致`。`p3_s4_loop.py:3390` → `patchharness.py:174,194` |
| `K2-PIN-H` | submodule を 511c にすると同検査を通る |
| `K2-LOCK-PAIR` | 現行 codec は `authority.contract_loader_blob_sha256s の exact key 集合が不正`。`campaign_lock.py:491`。歴史 codec は読め、記録 policy は現行 `db6bc9ea…` と一致 |
| T-2795 実走 | H、HEAD `6a3e15809` で候補 certified。stock は claim 取得で停止、admission 未到達 |
| 静的 | 旧 epoch lock は `ident.py:121,350`、通常 replay は `wal.py:2800` でも現行 policy 一致を要求 |

**stock arm の class。** `--stock-control` は coder authority のない context を作る（`p3_s4_loop.py:3369`）が、`_stock_capability_resolver:2005` が STOCK source に generator receipt を供給し、`:2089` で渡す。`build_admission.py:674` の stock-baseline 分岐は `CURRENT_PIN` に依存する一方、旧 full OID の source はその分岐を通らず、generator receipt があれば **machine-generated** になる。

したがって「新 epoch なので旧 stock は admission 不能」は誤り。ただし `src_token == STOCK` の成立は実 compiler で未観測であり、非 STOCK なら resolver は receipt を返さず、authority もないため拒否される。pair 修復でこの capability resolver を落としてはならない。full/short の exact 比較問題を本件に便乗して変更しない。

| 経路 | 判定 |
|---|---|
| O | 固定 checkout の旧条件継続に適合。ただし既存 one-shot claim の再取得や pair 不成立は解消しない |
| H | **新 campaign の候補経路は成立実績あり**。pair は D2187 修復・再投入裁定が先 |
| O' | 旧 epoch の新実験を作ることは可能だが、pair 修復も移植が必要。新 main の保守から外れる費用に見合わない |
| S' | 不要。旧 lock 復活には codec・claim も関係し、consumer policy 改訂だけでは解決しない |
| N | 新 pin の別系列として可能。旧巡の単純継続にはしない |

② H では現行 policy を持つ新 ID・新 lock を生成する。旧 lock を張り替えない。③ `p3_s4_loop.py:116` の full PIN は 511c 据置。⑤ floor protocol はこの経路には不要。

round 3 以前の `949ddcc2…` と pair／今後の巡の `db6bc9ea…` は、source PIN を揃えても campaign ID、receipt、cache identity、enforcement closure が異なる。T-2795 の候補再評価は既にこの境界を越えている。時刻・tree・環境差も含め、epoch 間の数値差を改善・退行・同等性の証拠にしない。D2194 項2の派生入力による巡の継続とは区別する。

**受理集合。**

- H：既存述語のまま「PIN不一致 checkout は拒否 → PIN一致の新 campaign は受理可能」。正例は旧 source＋現行 policy の候補、負例は旧 lock の live resume。規律2/7の緩和なし。
- pair 修復：「2回の claim 取得で後段拒否 → 1回の認可所有範囲で両 arm」。正例は同一認可下の候補・stock、負例は別 process の再取得。D2187 の別 wave で扱う。
- N：「511c source の登録 → e9e source の新登録」。旧 source を新登録で通さない。旧記録不変。

**推奨：裁定後の H。** 現在の「旧系列は固定 checkout」を本段で変更せず、H を採る旨と pair 再投入1 job＋4巡目1 job の予算を裁定へ返す。

## A-1 sized v3

`A1-BOUNDARY-NEW` は canonical HEAD mismatch（`paper_story_a1_paired.py:2419`）、`A1-SOURCE-NEW` は pinned-clean 不一致（`paper_story_a1_source.py:68,95`）。H の両 probe は通る。`A1-IDENTITY` は旧3 workload の **admission preimage 部分**と現行の差が `repo_stock_pin` だけであることを示す。campaign 全体の差分がこの一項だけとは証明していない。

**attempt-0003 は現行コードでは受理されない。**

- `paper_story_a1_paired.py:228`：認可列挙は attempt-0002 のみ。
- `:3478`：`authorize-rerun` は study・attempt・decision の列挙一致を要求。
- `:2715`：認可 record の study、attempt root、`source_commit` が今回の値と exact 一致。
- `:2795`：認可が解除する過去 attempt は `authorization[2]` の一つだけ。
- `:2970`：解除対象外の同 study が bench barrier に達していれば拒否。
- `:8406`：materialize も同じ認可 record を検証し、認可された attempt は既存 insight の**兄弟 dir**へ出力する。

従って列挙に0003を足すだけでも十分とは限らない。0001と0002の両 barrier 証拠が durable base に残る場合、0002だけを解除しても0001で止まる。実装 wave は残存証拠を読み、**どの過去 attempt に対して今回の再走を許すか**を裁定どおり明示する。証拠削除・全 prior の無条件除外は不可。

同 study の attempt 間で campaign ID を一致させる述語は、上記 rerun 判定にはない。ただし**今回の** cfg、lock、WAL、materialization は一致が必要（`ident.py:412–438`、`paper_story_a1_paired.py:5923`）。古い認可 record や旧 WAL を新 HEAD に流用できる意味ではない。

| 経路 | 判定 |
|---|---|
| O | 旧条件保持に適する。ただし0003の新認可が必要。文字どおり無変更の O では0003は通らない |
| H | source・境界は成立。0003の認可改訂後、同 study の新 attempt として構成可能 |
| O' | 認可変更を旧 base に移植する案。測定 source は保てるが保守費用増 |
| S' | 推奨しない。新 build の context、identity、WALまで旧 epochへ合わせる必要があり、g1 consumer限定案の範囲を越える |
| N | 新 study／登録・source契約が必要。sized v3 の0003とは別実験 |

② H は studyを保持して新 campaign ID・lock・認可recordを作る。③ canonical full OID は `paper_story_a1_paired.py:211,1085,2390` と source 契約とも511c据置。⑤不要。Nなら canonical pin、source契約、登録SHAをまとめて新設し、旧登録を上書きしない。

**受理集合。**

- H自体：「canonical 511c の clean submodule → 同条件」。正例H、負例e9e checkout。述語変更なし。
- 0003認可：「列挙された0002のみ → 裁定された0003・解除対象も受理」。正例は決定・root・HEAD一致record、負例は別HEAD／未裁定priorのbarrier。再走制限の受理集合変更なのでユーザー裁定必須。旧結果を保持する限り規律7に適合。
- N：「旧study条件 → 新study条件」。旧canonicalの入力は新studyで拒否。

**推奨：0003を行うなら H。** source条件を保持しつつ現行の検査を使う。ただし「同一 campaign identity の反復」ではなく、policy epochを開示した同studyの再走とする。再走理由・予算・prior解除範囲を裁定するまで投入しない。

## g1 launch と W-5

**観測と後段を分ける。**

- `G1-LOAD`：g1、SHA `7e1114…`、G `32ba8cae4` をロード。
- `G1-LAUNCH`：段階4、`manifest-invalid`／`binary-admission`。呼出しは `s8b_ratified_freeze.py:3394` → `:1905` → `s8b_binary_admission.py:371`。
- `G1-BIN-CURRENT`：12/12が同じpolicy不一致。
- `G1-BIN-HIST`：同じsource・contract・cell・binding期待値で12/12通過。ただし歴史検証。
- `POLICY-SERIES-PIN`：現行registry＋protocolの511cから得るSHAは
  `949ddcc2951935405f661ce70cb7df1031fedfd162788655e78faaadac671a44`。**12 receipt のSHA集合と exact一致**。S'の要求値は到達可能。
- `READMIT-STOCK`：12件すべてhuman-reviewed、review=`s8b-floor`は現行registryに存在。stock-baseline分類の問題ではない。
- 親gate-check：policy拒否のほか未知性layer2のhit。候補削除はD2194項5の別commit。
- **静的後段**：`s8b_oracle_spec.py:23,185` の承認SHAはNone。W-4は `no-approved-spec`。W-5のstore実体・hash、環境、reservation、budget、one-shot制限も未通過。

| 経路 | 判定 |
|---|---|
| O | `fec4a8187`はpolicyが合うがT-2810修復を持たず、journal／lineageで止まる。無修正Oは解決策にならない |
| H | submoduleだけ戻しても `_new_policy()` は新mainの `CURRENT_PIN` を使う。段階4の拒否不変 |
| O' | T-2810移植＋候補削除で解決候補になる。非main HEADは禁止されていない。ただし未実測 |
| S' | **推奨する設計候補**。旧floor receiptのlive消費に限定して期待policyを組み直す |
| N | 新protocol・build・official測定・新世代批准に加え、g2 launch契約の裁定と実装が必要 |

**S'の具体設計。**

1. `build_admission.py:499,510` の既存policy構築を、通常呼出しでは従来どおり `CURRENT_PIN`、批准系列のconsumerでは検証済みfull OIDの先頭7桁を使う形へ改訂する。schema、coder authority、generator/review registryは必ず現在のコードから得る。receipt・歴史preimageをpolicyの入力にしない。返すのは既存のexact `BuildAdmissionPolicy`。
2. `s8b_ratified_freeze.py:3394` は、`:3330`のraw hash照合と`:3369`のprotocol検証を通った `protocol["ccbench_pin"]` で構築する。sourceの外部期待値も引き続き同protocolから渡す（`:1907`）。
3. `s8b_oracle_driver.py:1003` も同じ規則にする。pinは `validated.floor_artifact.document["ccbench_pin"]` を使用できる。このdocumentは`:3413`以降のfloor検証・bindingを通り、`:3609`で凍結されたresultであり、receiptから独立する。approved manifestの `run_contract["ccbench_pin"]` との一致も保つ。
4. `s8b_binary_admission.py:368–372` のexact型・SHA一致、`:434`のsource pin、contract・subject・binary照合を維持する。
5. oracleの**新規build**は `s8b_oracle_driver.py:1441,1759` の現行contextを維持する。`S8B_ORACLE` reviewによる新receipt発行と、旧floor receiptの消費を混ぜない。旧receiptを再発行しない。

**失効性。** `_new_policy:505–506` は現在の列挙からregistryを生成する。generatorまたはreviewを除けばpolicy SHAが変わるため、旧receiptは`:371`で拒否される。`s8b-floor`を除けばclass/review検査（`:364–366`）も正常受理できない。S'は「記録当時のregistryを永久承認する」方式ではない。registry変更後にreceiptを張り替えて一致させる案はD2184の却下案そのもの。

**O'の閉包。**

- baseはA/Xを含む `fec4a8187`。
- T-2810の `dc5b0f39b`、docstring補足 `0d943f9cb`、fix2 `083a45ee9` を移植対象とする。
- D2194項5に従い候補fileだけを削除する別commit。削除commit自体は本HEADでは未実施なので、存在しないSHAを指定しない。
- 最小移植では、新mainの `cfab7a2f2`（意味witness 21→22、`condition_meaning_gate.py:325,335,940`）と `65e94a3a7`（exact-85 enforcement closure、`campaign_lock.py`／`contract_loader_binding.py`／`artifact_admission.py`）を取り残す。現行W-5と同じ検査を主張するO'なら、これらも移植して閉包を検査する。pin前進・新epoch goldenを丸ごと戻す／混ぜる作業ではない。
- validatorはbranch名mainを要求しない。O'自身のrootでloadし、その `activation_head` とlaunch時HEADを一致させる（`:3268`）。G/A/Xの祖先関係、G/H/worktreeのbytes、導入区間は維持。別rootで得たvalidated objectの流用は `t080_freeze_migration.py:2234` が拒否する。

**Nの費用。** T-2698記録では12 cell buildが7分18秒、96 sessionが71分24秒、job Elapseが4769秒＝約79.5分。これは同規模再実行の参考値で、queue待ち・再試行・再凍結・G/A/X批准・g2対応・W-4/W-5を含まない。既存枠はplanned 96＋retry 24、reservation 10時間。新pinでの所要保証には使わない。

**受理集合。**

- S'：「現行repo pin由来policyだけ → 検証済み系列pin＋現行registry由来policy」。正例はg1の12旧receipt、負例は失効registry・異なるsource pin・receipt由来pin・改変binary。live受理集合は広がるため裁定必須。規律2の照合を維持し、規律7のbytesは不変。
- O'：「旧validatorが拒否する現物journal／導入区間 → T-2810の厳密な修復条件」。正例は `C≤i≤G` の一意非merge導入、負例は複数導入・Cより前。既裁定修復の移植であり、過去結果の変更なし。
- N：「g1専用launch → 新世代も扱う契約」は未設計の受理集合変更。単にgeneration制限を削除する案は推奨しない。

**推奨：S'をconsumer限定で裁定する。** D2184が「必要なら別裁定」としたrepo pin依存の変更に当たると明記する。policy照合除去・live `None`・receipt張替えとは区別するが、無裁定で既存方針の範囲内とは扱わない。

## B-4 床値

**観測。**

- `B4-PROTOCOL`：`current_count=2 head_exact_count=0`。`s8b_floor_campaign.py:1032–1075`。
- `B4-RECORD-HIST`は通り、`B4-RECORD-CURRENT`はpolicy不一致。
- 親 `place`：`binary store preflight admission 不一致`。`b4_binary_record.py:170` → `s8b_floor_campaign.py:5825,5830`。
- 親 `validate-only`：新checkoutのbinary store不在で `lstat` 失敗。`floor_pair_driver.py:498,1136`。これはpolicy拒否とは別の観測。
- `B4-W1-HEAD`：3 JSONLとも `loaded_head=2ba40008…`。新HEADとは不一致。

| 経路 | 判定 |
|---|---|
| O | **f1 w2/finalizeの正規継続**。既存storeを使い、同submit-treeのHEADを維持 |
| H | policyもresolverのHEAD gitlinkも変わらず、新mainへの移転を解決しない |
| O' | HEADが変わるためf1の継続不可。新campaignなら別問題 |
| S' | placeのpolicyだけを改訂してもw1のHEAD一致を満たさない。g1案をB-4へ拡張しない |
| N | 新pinの新campaignとして成立させる。f1は移行しない |

`floor_pair_driver.py:1091` は既存の歴史receipt検証を用い、binary SHAを凍結specに束縛する。ここへ新しい `expected_policy=None` を導入する設計ではない。一方placeは現行policyを要求する。両者を同一のgateと説明しない。

② Nでは新campaign/spec、artifact・receipt SHA、測定窓・出力identityを新登録。旧w1を流用しない。③ floor-pairにK2型のPIN更新だけで済む入口はなく、specのartifact/provenance束縛を更新する。⑤ 新pinのbinaryを生成するにはsuccessor protocolをcommitし、再build・新record・A-5の新spec凍結とsubmitterのSHA束縛を揃える（`b4_binary_record.py:185`、`submit_floor_pair.sh:101–108`）。

**受理集合。**

- O継続：「w1と同HEAD・同spec・同binary → 同条件」。正例は保持されたsubmit-tree、負例は新HEAD。`submit_floor_pair.sh:173` を維持。
- N：「旧specのartifactだけ → 新specのartifactだけ」。正例は新record/hash一致、負例は旧binaryを新pinの結果として投入。旧凍結を保持する限り規律2/7に適合。
- f1移転のためloaded_head検査を外す案は規律2/7に抵触し、却下。

**推奨：Oでf1を完了。** w2は09-29T00:00Z以降かつ `now+24h≤10-07T00:00Z`、finalizeも同checkout。参考実測は1窓job約69〜77分。Nは別系列の必要が生じた時点で費用と登録を裁定する。

## 横断 (policy consumer 全数表・reseal の帰結・閉包)

以下は指定production群とS8b横断検索で確認した直接consumer、およびW-4/W-5の間接経路。**g1 S'の必須変更は旧floor receiptの2入口**であり、floor producer/resume全体を一括変更しない。

| consumer／入口 | 現行束縛 | S'での扱い |
|---|---|---|
| `build_admission.py:499,510` | repo pin＋現行registry | 既存構築を限定改訂。通常context不変 |
| `s8b_binary_admission.py:324,368` | exact live型・policy SHA | 検証を維持 |
| `s8b_ratified_freeze.py:3394,1905` | launchのfloor manifest | **系列protocol pinへ変更** |
| `s8b_oracle_driver.py:1003,1026` | W-5 store消費 | **検証済みfloorのpinへ変更** |
| 同 `:659,1340` | gate-check／run-blockからlaunch | 上記変更を共有。別の迂回口を作らない |
| 同 `:1441,1759` | oracle新build context | 現行policyのまま |
| `s8b_floor_campaign.py:4836` | portable record検証 | producer/resume用。S'では変更しない |
| 同 `:5825` | storeへの配置 | 変更しない。W-5用旧store配置をこのAPIで行うなら別途設計が必要 |
| 同 `:5884` | resume store | 変更しない |
| 同 `:6495` | floor runner live admission | 変更しない |
| 同 `:8149` | resume binary | 変更しない |
| `s8b_holdout_freeze.py:1387,1522` | 新freezeを作るfloor result検証 | W-3 producer。既存g1 launchからは呼ばれず、変更不要 |
| `ident.py:84,121,350,412` | cfg／旧lock policy一致 | K2/A-1新campaignは現行policy。緩和しない |
| `wal.py:2130,2145,2800` | live receipt／歴史receipt／通常replay | 型分離と現行一致を維持 |
| `s8b_oracle_manifest.py:1062,1167` | approved spec、manifest identity | admission resolverなし。W-4 specのpinをg1と整合 |
| `t080_freeze_migration.py:2222` | validated objectのroot/HEAD/scan | admission resolverなし。S'後もそのまま |
| `b4_binary_record.py:140,170`／`floor_pair_driver.py:1099` | 歴史検証と現行配置が別 | g1裁定の対象外 |

W-5のstoreは、`:1043`以降が実体SHAを全scheduleについて照合する。S'採択時には、既存の正しいbytesを所定storeへ揃える作業も必要。`b4_binary_record.place_record` はpinをreceiptから取得する（`:168`）ため、ここをそのまま「系列pin権威」としてS'へ流用してはならない。

**resealの実行帰結。**

- `s8b_floor_campaign.py:1110` はlegacy anchorを複製し、現行contractとHEAD gitlinkの**2 fieldだけ**を変更する。
- 追加先は `output/s8b-freeze/floor-protocols/<e576e9cd…>--<e9e477ca…>.json`。旧2文書は不変。
- create-only。発行後・commit前はHEAD blob不在でresolverが拒否する。commit後は同contract候補3、head exact 1となり新文書を返す。
- Hはsubmoduleを変えるだけなので、この選択基準を変えない。
- 新protocolは床値の実測結果ではない。official resultやg1批准を自動で更新しない。

**閉包。**

- `b10_backoff_grid.sh:585` はs1/s8b freeze配下のpathとbytesを全数hashするため、追加fileだけでも `:22` の `EXPECTED_FREEZE_TREES_SHA256` と不一致。`:596,648` の前後検査を維持し、更新の承認範囲を明示する。
- 対応literalは `test_backoff_extended_sweep.py:1670,2025`。旧B-10 submit-treeの定数は据置。
- `s8b_approved.py:63`、`s8b_ratified_freeze.V1_FREEZE_SHA256`、既存G/A/X・floor_sourceのSHAはresealだけでは変えない。
- floor resolver／reseal tests、protocol builder golden、binary admission tests、新specのSHA、submitterのspec pinを確認する。過去epoch goldenを新値で上書きしない。
- Nで新登録・manifest・result・generationを作る場合だけ、それぞれの新SHA閉包を追加する。S'にはresealもB-10 pin更新も不要。

## 裁定を要する点 (番号付き、択と推奨)

1. **g1：S'／O'／N。推奨S'。** 現行registryを保ち、批准protocolのpinで旧floor receiptをlive受理する変更を明示承認する。D2184の「別裁定」に該当。再測定費用を避け、現行mainの検査を維持できる。
2. **K2：固定checkout継続／Hによる新campaign／N。推奨H。** source PIN据置、epoch差開示、D2187修復後のpair1 job＋4巡目1 jobを裁定。旧claim・旧lockは変更しない。
3. **A-1：再走しない／O系／H／N。再走するならH。** attempt-0003の理由・予算・解除するprior集合を裁定。現行コードでは0003は未認可。
4. **B-4：f1をOで完了／新mainへ移転。推奨O。** f1移転は選ばず、新pinの必要が生じたときだけNの別spec・再測定を裁定する。
5. **g1の残手番。** 候補削除はD2194項5で裁定済み。S'採択はreviewed spec承認、held checks解除、W-5測定予算の代替ではない。
6. **Nを選ぶ場合の追加費用・契約。** g2 launch対応、再build約7分・official測定約71分を参考とする計算枠、再凍結・批准、B-10 aggregate pin更新を一括して提示する。resealだけを完了条件にしない。

## 実装 wave への申し送り (file:line・負例・閉包)

| 作業 | 起点 | 必須の正例／負例と閉包 |
|---|---|---|
| S' policy構築 | `build_admission.py:499,510` | 511c＋現registry→949d、通常→db6b。registry削除で旧receipt拒否。歴史decoderをlive authorityに使わない |
| g1 launch | `s8b_ratified_freeze.py:3330,3369,3394,1905` | 実12 receiptを無変更で通す。protocol hash改変、source pin違い、mixed policy、cell/binding改変を拒否 |
| W-5 floor消費 | `s8b_oracle_driver.py:1003,1026` | validated floor pinを使用。manifest pin違い、store欠落／hash違いを拒否。新build contextは現行のまま |
| 候補削除 | D2194項5指定file | 単独削除commit。load/reverify/gate-check再観測。再生成でhit復活。scan exemption不変 |
| A-1 0003 | `paper_story_a1_paired.py:228,2681,2795,3470,8406` | 正しいdecision/root/HEADのみ。0001・0002がともに残るケース、他prior、record既存、兄弟dir既存を検査 |
| K2 pair | `p3_s4_loop.py:2005,2019,2089,3369` | 実Pegasus認可を通す候補→stock。STOCK＋generator admission、非STOCK拒否、claim二重取得拒否を保持 |
| B-4新系列のみ | `s8b_floor_campaign.py:1110`、`b4_binary_record.py:185`、submitter `:101` | successor commit後の解決、新record/spec/hash。旧w1の新HEAD投入は拒否 |
| O'を選ぶ場合 | T-2810の3commit＋上記前提修正 | O'自身のroot/HEADで全段を検証。移植済みをmainの試験結果で代用しない |

親の実測では、S'のlive発行型を使う12 cell検証、候補削除後のlaunch、approved manifestからのW-5 preflight、A-1のprior集合を含む0003経路が未確認。これらを裁定後waveの受入対象とする。旧receipt・lock・凍結bytesの張替え、曖昧fallback、liveへの`None`追加は実装しない。

## 総括

推奨は **K2＝裁定後H、A-1＝0003認可を整えたH、g1＝consumer限定S'、B-4 f1＝O継続**。

特に追加裁定が必要なのは、g1のlive受理集合、A-1の0003とprior解除範囲、K2の再投入予算。Nにはg2 launch契約まで必要であり、再 admissionやresealだけでは完結しない。