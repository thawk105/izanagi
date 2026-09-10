[実測] HEAD は `97ee3cd3a49ebc62914909012687bccd907ac4ae`、worktree は clean だった。以下の `[実測]` は pytest や実 run ではなく、この HEAD に対する静的検査を意味する。

[推測] 結論は、二層 identity の方向自体は使えるが、段2 plan のままでは 33 物理 run は formal consumer まで届かない、である。

## 所見表

| severity | 所見 | file:line | 根拠 | 直す場所 |
|---|---|---|---|---|
| blocker | F1. ledger producer が計画から欠落している | `p3_autonomous_workload_trial.py:429-438,1481-1488,1632-1680`; `reflux_origin_client.py:134-170` | [実測] `OriginProducerInputs` は実行前に完成済みの `run_plan` と `result_record_bytes` を caller に要求する。`_complete_origin_runtime()` は既に sealed 済みの batch と渡された record を読むだけで、`BatchReserved`、`BatchCommitted`、`BatchResultsPrepared`、`BatchSealed` を一度も発行しない。[推測] 33 回 `drive` して record を書いても ledger member が作られず、`_pair_records()` で formal consumer に接続しない。 | plan §2.3、§2.5、§2.6 を、capability 発行、envelope 書込み、reserve、commit、33 run、prepare、seal、consumer の全状態機械として作り直す。 |
| blocker | F2. run plan の事前束縛が未解決で、現設計には hash cycle がある | `reflux_origin_binding.py:175-193`; `reflux_origin_topology.py:259-300`; `reflux_formal_consumer.py:570-575`; `trial_registry.py:201-213`; `design-doc-verbatim.md:556-564` | [実測] capability と lifecycle に run-plan digest は無い。一方 envelope は capability digest を含むため、plan 全体の digest を capability に追加すると循環する。現状は plan が capability を一方向に参照するだけで、capability 発行時に plan は固定されない。[推測] plan §2.3 の「run plan が正本」だけでは設計文書 §8 の「digest を capability と lifecycle へ束縛」を満たさない。 | §2.3 を裁定後に全面差替え。plan core と envelope の digest 分離、または §8 の契約変更が必要。 |
| blocker | F3. 提案 executor は現行 `drive` をそのまま呼べない | `p3_s4_loop_trigger_gating.py:984-1002,1118-1153`; `p3_autonomous_workload_trial.py:2105-2144,3804-3810` | [実測] `drive_iteration` は `(cfg, perf, planner, coder, auditor, prior_reverse, sub, do_build, ...)` を要求し、`TopologyMember` を取らない。さらに valid な rejected/aborted run の後も `require_admitted_campaign(...CERTIFIED_ACCEPTANCE)` を呼ぶため、P6 で必要な rejection を通常戻り値として返せない。`_run_workload` は分岐候補より前に論理 campaign の単一 layout を作り fresh check する。[推測] plan の `(cfg_q, perf, member, layout_q)` adapter だけでは、wire の注入、rejection の返却、論理 layout の誤検査を解けない。 | §2.6 を、`prepared` の直後かつ `layout` 作成前で完全分岐させる。trigger module に origin 専用の sealed physical entry point を名指しする。 |
| blocker | F4. report、completeness、Layer 3、registry acceptance がすべて単一 campaign 前提 | `p3_autonomous_workload_trial.py:2827-2859,3570-3716`; `autonomous_trial_completeness.py:2531-2584,2690-2707,4217-4272,4815-4955`; `trial_registry.py:1642-1694,5533-5599` | [実測] build finalizer は単一 `campaign_root` だけを render する。completeness は `generations == budget == 2` の role/harness 履歴を要求する。cross-binding と Layer 3 chain は単一 root を読む。acceptance issuer も `cells[0].campaign_root` を必須にする。[推測] `campaign_runs` を足し単数 root を消すだけでは、最初の completeness または registry acceptance で拒否される。 | §2.6、§2.7、§2.8、§4 を差替え。`_scan_report_attempts`、generation accounting、cell admission、Layer 3、`trial_registry.py` まで origin 専用射影を設計する。 |
| blocker | F5. qualifying rejection から evidence を作る材料変換が存在しない | `pipeline.py:1518-1549`; `reflux_formal_consumer.py:812-842`; `reflux_result_evidence.py:291-303,431-442` | [実測] production abort は `payload.verify` を持つが、consumer が要求する `candidate_attributable`、`truncated`、`witness_class_sha256s` は書かない。repo には witness normalizer が無い。create-only record writer は存在するが、production record builder/issuer は無い。[推測] source 行は qualifying single-class rejection でなければ 32 validation へ進めないため、この欠落は 33 non-tombstone の到達を直接阻止する。 | §2.5 に native abort から single witness class を導く exact algorithm、所有 file、失敗時 tombstone 判定を追加。予定 file 12 件も再計数する。 |
| must-fix | F6. t524 の slot 意味は整合するが、「`trial_registry.py` 変更0」は誤り | `p3_autonomous_workload_trial.py:1356-1427,4602-4697,4936-4961`; `t524-ruling-stage4.md:40-56`; `trial_registry.py:5533-5599` | [実測] 外側の attempt slot は論理 `binding.campaign_id`、`replicate_index == 0` の1件でよく、内部の `run_campaign` は lifecycle を開始しない。この意味では33 runとの矛盾はない。[実測] しかし t524 v5 は全 slot の final terminal を要求し、現 acceptance は単一 `campaign_root` を読む。新 report を通すには `trial_registry.py` の変更が必要で、t524 と semantic overlap がある。 | §2.8 と file list。t524 着地後に rebase し、attempt-registry部分は不変、report/measurement-target部分だけを origin-aware にする。 |
| must-fix | F7. reservation と `max_wall_s` が 33 run の実行時間を保護しない | `p3_autonomous_workload_trial.py:152,2809-2824,3850-3867,4624-4627`; `loop.py:198-207`; `reservation.py:74-117` | [実測] outer preflight は reservation に `max_wall_s` 全量を要求するが、その `ReservationCheck` を捨てる。各 `run_campaign` は残時間を1秒しか要求しない。既定 `max_wall_s` は3600秒で、D1561 の1行374から908秒を33本直列にすると約3.4から8.3時間になる。[推測] member開始前の残時間検査が無いと、scheduler kill が record/tombstone/lifecycle terminal より先に起きうる。 | §2.6、§7相当、受入要件。preflight receiptを保持し、各 q 前に次 member の保守的上限を `ensure_remaining()` で検査し、不足なら suffix tombstoneへ進む契約が必要。 |
| must-fix | F8. process crash を tombstone 化できるという表現が過大 | `reflux_origin_topology.py:500-514`; `trial_registry.py:4784-4819`; `p3_autonomous_workload_trial.py:4208-4231`; `design-doc-verbatim.md:498-512,531-539` | [実測] tombstone suffix validatorとmapping helperはあるが `run_trial` からの呼出しが無い。lifecycle terminal は同一 process の token を要求する。report無し例外は attempt registry 上 `not-consumed` となり、t524 v5 の最終消費から除外される。[推測] catch可能な member failure は tombstone化できるが、実 process crash は設計文書 §7.5どおり非終端のままである。 | §2.5、§2.6 の「crash」を「同一processで捕捉した failure」と「process crash」に分ける。 |
| must-fix | F9. 論理 cfg を registry 照合へ渡す境界を受入要件に固定すべき | `p3_autonomous_workload_trial.py:1329-1342,1518-1535`; `reflux_origin_binding.py:559-567`; `trial_registry.py:4926-4938` | [実測] 現行は suffix 作成前の `PreparedCampaignIdentity.campaign_id` を `assert_campaign_binding` と capability issuerへ渡すため、論理 binding は守られる。ただし `assert_campaign_binding` 自体は単なる文字列を受け、論理/物理を型で区別しない。[推測] executor実装時の呼出し順変更で `cfg_q` を渡すと拒否されるか、比較位置を誤って弱める危険がある。 | §2.1、§2.3、受入要件へ「registry/capability rederivation は suffix helper 呼出し前の exact `PreparedCampaignIdentity` のみ」を追加。 |
| must-fix | F10. completeness の「新 key を拒否する exact key gate」の名指しが誤っている | `autonomous_trial_completeness.py:117-133,2531-2584`; `reflux_result_evidence.py:124-132` | [実測] `campaign_runs` を拒否する既存の cell exact-key 定数は無く、`_check_cell_metadata` は required key の不足だけを見る。拒否原因は単一 `campaign_root` と論理 trial 再導出である。更新が必要な exact定数は execution provenance 側の `_EXECUTION_PROVENANCE_KEYS`。launch admission の `_LAUNCH_ADMISSION_KEYS` と `_LAUNCH_ADMISSION_REGISTERED_KEYS` は既に origin optional である。 | §2.7 と受入要件9。存在しない exact gate を更新すると書かず、origin cell用 `_CAMPAIGN_RUN_KEYS` の新設と既存 semantic branchを個別に列挙する。 |
| must-fix | F11. A6 の「identity が違えば protocol digest も違う」は現物で反証できる | `ident.py:196-235`; `campaign_claim.py:348-371` | [実測] `spec_slug` は `CampaignId` の文字列には入るが canonical preimageには入らない。従って slugだけ違う2 cfgは identityが異なり、full protocol digestは同一になる。claim scanは別 pathでも同 digestのLIVE ownerを拒否する。[実測] P1の33 cfgは同じ slug/search tagなので、33 short identityの相異を確認すればfull digest相異も従う。planの「双方を独立検査」は安全だが冗長である。 | 親 A6 と plan §1 A6、§2.1、§2.2を訂正。一般則とP1固有則を分ける。 |

## A1からA17の監査

| anchor | 判定 |
|---|---|
| A1 | [実測] 正しい。`ident.py:196-235` の列挙と一致する。 |
| A2 | [実測] fieldと用途説明は正しい。[must-fix/F4,F10] seamが存在するだけでは report/completeness が通る根拠にならない。 |
| A3 | [実測] 正しい。`p3_autonomous_workload_trial.py:749-801`。 |
| A4 | [実測] 正しい。ただし論理 cfg である保証は呼出し順に依存するためF9が必要。 |
| A5 | [実測] 正しい。`loop.py:194-229`。関数名は `_authorize_measurement`。 |
| A6 | [実測] 誤り。F11のslug反例がある。planもSHA衝突だけを論点にしており反証を取り切れていない。 |
| A7 | [実測] 正しい。`loop.py:427-463,527-533`。 |
| A8 | [実測] [nit] 8cの通常 `drive_iteration` では正しいが一般化が過大。`run_campaign` 直呼びはこのgateを通らず、第1 runが対象artifactを残さなければ同 gateでは止まらない。 |
| A9 | [実測] [nit] 意味は正しいが `Genome` は現行 `p3_s4_loop_trigger_gating.py:768`。また現時点に33行executorは無いので「将来33行で変えるべき値」と書く方が正確。 |
| A10 | [実測] 正しい。`reflux_origin_binding.py:175-193,559-564,609-630`。 |
| A11 | [実測] 正しい。論理3項等式、attempt相異、trigger一致はいずれも実在する。 |
| A12 | [実測] [nit] 「production issuer不在」は正しいが「書き手不在」は過大。create-only writer自体は `reflux_result_evidence.py:431-442` にある。無いのはproduction record builderとcallerである。 |
| A13 | [実測] [nit] `planned_campaign_run_identity` をproduction consumerが読まない点は正しい。topology builder自身は `reflux_origin_topology.py:397-413` でfieldをコピーする。planの「親はrun plan全体が未参照と言った」という反論は親の文言より広い。 |
| A14 | [実測] 正しい。`campaign_lock.py:275-304`。ただし先例であって今回の実装部品ではない。 |
| A15 | [実測] [nit] anchor不足。消費identityは `s8b_attempt_registry.py:114-148`、決定的世代導出は `s8b_holdout_admission.py:782-802`。planの訂正は正しい。 |
| A16 | [実測] 正しい。`trial_registry.py:4222-4276`。 |
| A17 | [実測] 正しい。ただし専用分岐は `p3_autonomous_workload_trial.py:3804` の単一layout作成より前でなければならない。 |

## `CampaignConfig.trial` 全参照の判定

[実測] `rg -n '\.trial\b' orchestrator/campaign` のうち、`CampaignConfig.trial` を実際に読む箇所は次で尽きる。

| 用途 | 全参照 | P1の影響 |
|---|---|---|
| identity | `ident.py:217` | [実測] 接尾辞をcampaign identityとlock preimageへ入れる本体。期待どおり別挙動。 |
| A-1分岐 | `ident.py:72` | [実測] `search_config` のA-1 marker群と `cfg.trial == study_id` の合接。8c cfgにはmarkerが無いため不発火。 |
| B4 driver分類 | `p3_b4_closed_critic.py:725`; `p3_s4_loop.py:1442,1573,1994`; `p3_s4_loop_sort.py:377,532`; `p3_s4_loop_trigger_gating.py:757,882,1051` | [実測] suffix付き値はB4固定identityには一致しない。ただし各呼出しは `b4_protocol` markerでguardされ、8c `_campaign_for()` はmarkerを持たないためorigin経路では不発火。 |
| CampaignConfig以外 | `guided.py:181,185,191,194,200,214,216,219,266`; `s6_sort_sweep.py:753`; `s8a_trigger_sweep.py:882`; `b10_backoff_shape_sweep.py:3642,4015` | [実測] CLI引数、guided trial名、submission/report labelであり、P1のcfg_qを読まない。 |
| lock codecの文字列 | `campaign_lock.py:202` | [実測] attribute readではなく、decoded `identity.trial` の型エラー文。実gateは `campaign_lock.py:19-21,191-203,334-354`。 |

補足経路:

- [実測] site別cfgは `p3_s4_loop_trigger_gating.py:458-472` で `trial` を変更せず、Pegasusの `measurement_env` とbound contractだけを足す。
- [実測] campaign lockはtrial込みpreimageをexact照合するため、cfg_qとlayout_qが一致すれば正常、別qのlayoutを渡せば拒否する。
- [実測] report/lifecycleは `CampaignConfig.trial` 自体を記録しない。reportは `campaign_id/campaign_root`、lifecycleは論理`trial_id`、slot、launch admissionを記録する。
- [実測] registry再導出は現在 `p3_autonomous_workload_trial.py:1329-1342`、origin capability発行は同`:1518-1535`から論理prepared cfgを使用する。これが「物理cfgでなく論理cfgに対して呼ばれる」現時点の保証である。
- [推測] 実装waveではこの順序を受入要件と負例で固定しなければ、P1の安全性は関数型だけでは保証されない。

## D1555と物理 evidence

[実測] D1555のshape不一致は現存する。consumerの `_wal_trigger()` は `reflux_formal_consumer.py:722-728` でroot `kind == "TriggerGateBinding"` を要求するが、production writerは `wal.py:1595-1611` で `stage="trigger_binding"`、`payload.build_attempt_id`、`payload.trigger_binding` を書く。

[実測] plan §2.5のnative decoder追加は必須で、方向も正しい。ただし受入要件は次まで合接しないと足りない。

- [推測] native trigger recordをexact 1件に限定し、`trigger_gate_binding.validate_record()`、attempt一致、build-start commitment一致を検査する。
- [推測] terminalもroot `kind`ではなくnative `stage == commit|abort` を読む。
- [推測] synthetic fixture shapeの正例だけでなく、`wal.log_trigger_binding()` とpipelineが実際に作るframe列を正例にする。
- [推測] native abortからcandidate-attributable single witness classを導けない場合はrejected recordを発行せず、tombstoneにする。

[実測] `drive` outcomeから取得可能なのは、物理campaign identity、layout、variant、last-wins WAL records、binding commitmentである (`p3_s4_loop_trigger_gating.py:633-640,839-860`)。build attemptはWALから取れる (`:714-731`)。execution receiptはinner scopeの`CampaignSummary`にある (`:811-829`) がpublic outcomeには出ない。raw WAL byte区間とwitness classはoutcomeだけからは得られない。

## t524とt1851

- [実測] t524の実験単位は外側slotであり、33個のcampaign claimではない。1 slot、`replicate_index == 0`、lifecycle start/terminal各1件の内側で33 physical runを行う設計は意味上は両立する。
- [実測] t524 v5は`observed`または`terminal-failure`をfinal terminalとして全unit消費を検査し、`not-consumed`を正例から外す (`t524-ruling-stage4.md:48-57`)。
- [推測] catch可能なorigin失敗をtombstone suffixへ畳んでreportを終端できればt524を通せる。process crashでtokenを失った場合はunitが非終端になり、v5 receiptは成立しない。これは既存§7.5のliveness限界と一致する。
- [実測] `trial_registry.py` のreport/campaign-root検査は変更が必要なので、planの「t524とのsemantic overlap 0」は誤り。t524着地後のrebaseが必要である。
- [実測] s8bの`campaign_run_id`とmeasurement generationは `s8b_attempt_registry.py`、`s8b_holdout_admission.py` に閉じ、8cの`PreparedCampaignIdentity`、origin topology、formal consumerから参照されない。
- [推測] 命名を`campaign_run_identity`に保ち、s8bのgeneration/claimへ接続しない限り、t1851のfileを変更する必要はない。

## 既定経路のbytes不変

[実測] originless不変を支える既存の実アンカーはある。

- `p3_autonomous_workload_trial.py:1591-1599` はcapability無しなら従来launch recordをそのまま返す。
- 同`:3280-3293` の`origin_runtime`は既定`None`。
- 同`:3390-3392,3618-3624,4936-4939` はorigin値がある場合だけ追加経路を使う。
- `trial_registry.py:4252-4276` は`origin_binding`をcapability発行時だけ出す。
- `autonomous_trial_completeness.py:117-133` はoriginlessとorigin-boundのlaunch exact key集合を既に分離している。

[実測] 一方、`campaign_runs`用の既存exact cell key gateは無い。実際の拒否点は単一root、素のtrial、2 generations、Layer 3 chainである。plan §2.7の「origin/non-origin exact key集合を別々にpin」は、新設する定数と上記semantic gateを具体的に列挙して初めて受入要件になる。

## plan判定

[推測] **修正では足りず、planを作り直すべき**である。二層identityとFC03への物理identity追加は残せるが、実行制御、ledger状態機械、report acceptance、crash処理が中心設計から欠けている。

残してよい節:

- [推測] §2.1 二層identityの基本式。
- [推測] §2.2 claim/layout/WAL分離。ただしA6の一般化を訂正する。
- [推測] §2.4 論理FC03を残し、物理identity比較を追加する方向。
- [推測] 却下案の大半。

差替える節:

1. [推測] §1 A1からA17検証。
2. [推測] §2.3を「capability、plan core、envelope、lifecycleの発行順とdigest束縛」に差替え。
3. [推測] §2.5を「native WAL outcome classifier、witness normalizer、artifact writer、返却型」に差替え。
4. [推測] §2.6を「origin ledgerのreserveからsealまでを含むcontroller FSM」に差替え。
5. [推測] §2.7を「origin report state machine、Layer 3、completeness、registry acceptance、originless projection」に差替え。
6. [推測] §2.8をt524着地後の実surfaceとmerge順に差替え。
7. [推測] §4の受入要件と12-file listを全面再計数。少なくとも`trial_registry.py`は追加対象になる。

## 裁定パッケージ候補

1. **run plan digestの循環をどう解くか**

   - [推測] 推奨: capability digestを含まない`run-plan-core`を先にcanonical化し、そのdigestをcapabilityとlifecycleへ束縛する。envelopeはそのcore、issued capability digest、初期state commitmentを包む。
   - [推測] 代案: capabilityへのplan束縛を諦め、lifecycleだけへ束縛する。この場合は設計文書§8を明示改訂する必要がある。

2. **origin cellの「complete」を何が認証するか**

   - [推測] 推奨: 通常cellの「全campaignがadmitted」と別に、issued origin capabilityとformal-consumer receiptに限定したorigin専用completion algebraを設ける。P6はqualifying rejectionを必要とするため、全33 physical campaignの通常Layer 3 admissionを要求する案は成立しない。
   - [推測] これは既存report/completeness受理集合へ新しい形を足す決定なので、本waveだけで黙って確定しない方がよい。

3. **`execution-provenance`のschema世代**

   - [推測] 推奨: `campaign_run_identity`必須形は`execution-provenance/v2`とし、v1 readerをhistorical decoderとして残すが新origin consumerでは受理しない。
   - [推測] 代案: planどおりv1をin-place変更する。production artifact 0件を理由に最小化できるが、同じschema名が異なるexact key集合を表す。

[実測] process crash後のdurable capability再発行は既存設計§7.5で範囲外とされている。これを覆さないなら新裁定ではなく、planの「crash後tombstone」という表現を訂正すればよい。

## 総括

- [実測] blockerは5件、must-fixは6件。
- [実測] P1のidentity分離自体は成立しうるが、ledger、report、formal evidenceへの経路が閉じていない。
- [実測] t524の1 slot原則とは両立するが、`trial_registry.py`変更0・semantic overlap 0は誤り。
- [実測] t1851のs8b fileは変更不要。
- [推測] 判定は **plan作り直し**。§2.1、§2.2、§2.4の核だけを再利用する。