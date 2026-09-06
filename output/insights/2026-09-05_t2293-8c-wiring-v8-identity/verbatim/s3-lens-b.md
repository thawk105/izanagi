[実測] worktree HEAD は指定どおり `97ee3cd3a` です。pytest、編集、commit は行っていません。

## 所見表

| severity | 所見 | file:line | 偽装シナリオまたは新規受理入力 | 設計への要求 |
|---|---|---|---|---|
| blocker | [実測] 新 FC03 は `execution_provenance.campaign_run_identity` と run plan の自己申告値を比較するだけです。execution receipt は環境情報しか持たず、formal consumer は `CampaignSummary` や `campaign.lock` を読みません。[推測] 論理 `campaign_id` も物理 identity も同じ evidence writerが書けるため、3項等式は §10 が却下した issuer 文字列と同型の恒真化です。 | `s2-plan.md:141-156,184-192,293-304`; `reflux_formal_consumer.py:682-719`; `execution_guard.py:204-222`; `design-doc-verbatim.md:221-256` | (b), (f)。別 trial の33 WALを使い、provenanceだけ対象 trial / plan の値にすれば、FC05a〜cを満たしたまま通せます。 | formal consumer 自身が各 `campaign.lock` を exact decodeし、lockの物理cfgから物理identityを再計算し、さらに論理cfgを再構成して `capability.campaign_id` と比較すること。WAL参照のinodeと区間もそのlayout配下へ束縛すること。 |
| blocker | [実測] envelopeは capability digestを含みますが、capability、launch admission、lifecycleのどれも envelope digestを含みません。consumerは渡されたin-memory `RecoveryEnvelope` を検査し、そのdigestを受理後のreceiptへ書くだけです。create-only fileそのものを再読していません。 | `reflux_origin_topology.py:258-301,420-497`; `reflux_formal_consumer.py:539-576,923-925,942-999`; `s2-plan.md:118-122,261-266` | (d), (e)。同一pathの上書きは拒否されますが、別objectまたは別pathのenvelopeをformal consumerへ渡す差し替えは拒否されません。 | capability発行後に、`capability_sha256 + attempt-capability digest + envelope_sha256 + canonical path` を束縛する第二段の issued plan sealを作り、launch/lifecycle/formal consumerの全てが同じsealを要求すること。 |
| blocker | [実測] 物理identityの入力は論理cfgとqだけで、slot、`replicate_index`、`attempt_index`、prereg commitを含みません。一方、既存の `AttemptSlotCapability` はこれらを全てdigestへ束縛しています。 | `s2-plan.md:55-79,268-274`; `trial_registry.py:2975-3008,3059-3078`; `p3_autonomous_workload_trial.py:1387-1427` | (c)。同じ論理campaignの過去slotの33 runは同じplanned identityになります。unique attempt/WALをそのまま再利用でき、新attemptの正規実行は古いclaim/layoutに衝突します。 | `AttemptSlotCapability.capability_digest_sha256` または同等の測定世代を物理identity導出とrun plan、provenance、lock検査へ入れること。同一slotの再入は同identity、別slot/attemptは別identityにすること。 |
| blocker | [実測] planは複数の新規受理を導入しますが「拒否分岐を緩和しない」とだけ記し、受理集合変更の裁定を返していません。 | `s1-brief.md:20-29`; `s2-plan.md:102-106,126-154,170-180,253-266,311-316` | 新規受理は下表の claim/resume迂回、native WAL shape、8-key provenance、複数campaign root reportです。 | 各変更を「既存predicateは維持するが上位写像の受理集合は拡大する」と明記し、D1616/D1555がどこまで承認したかを裁定へ返すこと。 |
| blocker | [実測] `trial` suffixの非衝突証明は現在の8c workload集合内にしか成立しません。`CampaignConfig.trial` とcampaign-lock decoderは任意の文字列を許し、物理identityはglobalなclaim/layout名前空間を使います。 | `s2-plan.md:55-87`; `model.py:66-84`; `campaign_lock.py:191-203`; `layout.py:589-597` | [推測] 同じ他fieldを持つ `trial="foo"` のq00と、別callerの素の `trial="foo-q00"` はcanonical preimageまで一致します。33件内相異検査では検出できません。 | 文字列suffixではなく、structuredかつdomain-separatedな物理run成分をidentity preimageへ追加すること。少なくとも論理trialとして受理可能な値と物理名前空間を構文上分離すること。 |
| blocker | [実測] durable envelopeの現行writeは `begin_attempt_observation()` より後です。planも「executorと最初のledger `BatchReserved` より前」にしか移動条件を置いていません。 | `p3_autonomous_workload_trial.py:4671-4678,3790-3816`; `s2-plan.md:120-122`; `design-doc-verbatim.md:478-494,560-564` | (e)。observation開始後、create-only envelope作成前のcrashでは、事前登録済みのdurable bytesが存在しません。 | slot予約後、observation開始前にidentity導出、envelope create-only、plan seal発行を完了する順序へ変更すること。 |
| must-fix | [実測] completenessで33 `campaign.lock` を再読する案は、formal origin terminalの防壁にはなりません。`_complete_origin_runtime()` がformal resultをledgerへcommitした後にcompletenessが走ります。 | `s2-plan.md:239-255,304`; `p3_autonomous_workload_trial.py:1632-1680,3570-3572,3684-3709` | (b), (f)。後段completenessが赤になっても、origin formal resultは先にcommit済みです。 | lock/WAL/layoutの物理束縛をformal consumerへ移すこと。completenessは同じ検査の再確認に限定すること。 |
| must-fix | [実測] planはnative WALとfixture shapeの閉じたdecoderを併存させますが、1 projection内でのschema family統一とmixed-shape拒否を要求していません。 | `s2-plan.md:170-180,328`; `reflux_formal_consumer.py:722-742,812-842` | 新規受理: native `stage/payload` triggerをfixture terminalと組み合わせるmixed projection。 | projectionごとにschema discriminatorを1つ固定し、全recordが同じfamilyでなければFC05c/FC07で拒否する負例を追加すること。 |
| nit | [実測] plan作成時の記録ではHEADとlocal mainが共に `97ee3cd3a` ですが、現在のlocal mainは `b152eec77` です。worktree HEADは `97ee3cd3a` のままです。 | `s2-plan.md:3` | なし。 | 最終記録では「検査対象HEAD」と「現在のlocal main」を分けて書くこと。 |

## 受理集合の向き

| 拒否条件 | 変更後に新しく受理される入力 | 判定 |
|---|---|---|
| `campaign_claim.acquire_claim` | [推測] 同じ論理campaignのq1以降。旧写像ではq0と同じclaim path/digestで拒否、新写像では別cfg/path/digestとして受理されます。関数内predicate自体は不変です。 | blocker候補 |
| `_assert_resume_allowed` | [推測] q0 artifactが存在する状態でのq1。旧写像では同layoutで拒否、新写像ではfresh `layout_q1` として受理されます。 | blocker候補 |
| `assert_campaign_binding` | [実測] なし。論理 `PreparedCampaignIdentity.campaign_id == binding.campaign_id` は維持され、物理cfgを渡せば拒否されます。 | 不変 |
| FC03 | [実測] 旧7-key v1が拒否され、新8-key v1が受理されます。その新schema内ではplanned identity比較が追加されるため集合は狭まりますが、物理事実への束縛はありません。 | blocker候補 |
| FC04 | [実測] なし。ordinal/replicate/wire/outcome/constraint写像は変更されません。 | 不変 |
| FC05a | [実測] なし。`build_attempt_id` 相異を維持します。 | 不変 |
| FC05b | [実測] なし。inode単位のWAL区間非重複を維持します。 | 不変 |
| FC05c | [推測] productionのnative `stage/payload` WALが新たに受理されます。現状はfixture root-shapeしか通りません。 | blocker候補 |
| `_validate_members` | [実測] directにはなし。既存の33件、固定順、identity/path相異は維持され、preflight再導出でさらに狭まります。 | 狭まる |
| launch admission origin一致 | [実測] なし。`origin_record.campaign_id == binding.campaign_id` は維持されます。 | 不変 |
| completeness exact key | [推測] `campaign_runs` を持ち単数 `campaign_root` を欠くorigin cellが新たに受理されます。originless shapeは維持されます。 | blocker候補 |

[推測] claim/resumeの拡大はD1616を実現するため意図的ですが、「同じpredicateを編集していない」だけではシステム全体の受理集合不変にはなりません。規律2との関係をユーザー裁定として明示する必要があります。

## 偽装シナリオ

| scenario | 判定 | 拒否する検査、または穴 |
|---|---|---|
| (a) 1 runのWAL/receipt/attemptを33回再利用 | [実測] 拒否されます。 | FC05aが重複attemptを拒否します (`reflux_formal_consumer.py:731-736`)。同じWAL区間ならFC05bも拒否します (`reflux_result_evidence.py:707-724`)。 |
| (b) 別trialの33 runを流用 | [推測] 素通り可能です。 | honestな別trial provenanceを保持すればFC03で拒否されます。しかし対象trialの論理/物理identityへprovenanceを書き換えると、consumerはlockやsummaryを再読しないため拒否条件がありません。blockerです。 |
| (c) 同じtrialの過去attemptを流用 | [推測] 素通りします。 | planned identityがslot/generationを含まず同一です。FC05a/bは過去33 run内で相異なら通ります。launch digestはresult record側だけを書き換えられます。blockerです。 |
| (d) envelopeへ任意33 identity、実行は1 layout | [推測] 正規live経路ではpreflight再導出とproducerのsummary比較が拒否します (`s2-plan.md:118-120,184-192`)。ただしalternate envelopeと手書きprovenanceをformal consumerへ渡す経路では拒否がありません。 | 全体としてblockerです。 |
| (e) run planを後から書換え | [実測] 同じcanonical pathの上書きは `O_EXCL` とread-backが拒否します (`reflux_origin_artifacts.py:196-251`)。[推測] しかしalternate object/pathへの差し替えをconsumerは検出しません。 | second-stage plan sealが必要です。 |
| (f) producer不在でprovenanceを手書き | [実測] content digestとexact schemaは通せます。設計自身も同一UIDの先書きを排除できないと明記しています (`design-doc-verbatim.md:221-256`)。 | V-10の運用前提で脅威圏外にするか、writer権限分離が必要です。現planの「択一0件」は誤りです。 |

## identityの決定性、一意性、衝突

[実測] 導出は時刻、乱数、PIDを含まず、同じ論理cfgとqから同じ値になるため決定的です (`s2-plan.md:55-77`)。

[実測] 32-bit短縮hashで33個の少なくとも1組が衝突する確率は、

`1 - product(k=0..32, 1 - k / 2^32) = 1.2293457e-7`

で、約813万4408組に1回です。full SHA-256 digestの同条件での近似値は約 `4.56e-75` です。

[推測] planどおり33 identityとfull digestをreservation前に相異検査すれば、内部衝突はfail-closedです (`s2-plan.md:81-87`)。検査が欠けても同じclaim pathは `O_EXCL` で拒否されます (`campaign_claim.py:400-434`)。既存layout artifactがあればresume/fresh検査も拒否します。

[実測] ただし検査対象は33個相互だけで、論理campaignや他producerのidentityとのglobal衝突は対象外です。特にsuffixはgeneric `CampaignConfig.trial` 名前空間と構文分離されていません。この部分の一意性証明は成立していません。

## FC03と§4.2の双射

[実測] FC05aとFC05bが保証するのは「33個の相異なるbuild attemptと非重複WAL区間」です。どのcampaign layoutで実行されたかは保証しません。

[推測] 物理identity検査が追加で拒否すべき具体例は、q10とq11について相異なる正規attempt/WALを使いつつ、campaign root/configだけを交換した入力です。FC05a〜cは通りますが、lockから再導出した物理identityとplanned identityの比較なら拒否できます。

[推測] 現planの文字列比較だけなら、provenanceも交換後のplanned値へ書き換えられるため、この追加拒否を物理実行へ帰属できません。現状のmutation案 `33値を循環shift` は文字列gateをkillするだけです (`s2-plan.md:325-329`)。実装waveでは「lock/rootを交換し、provenanceを整合的に再生成した負例」が赤になる必要があります。そうでなければF28型の冗長gateです。

## D1190とcrash

[実測] D1190は「同じrunのresumeは同じ世代、別runは別世代」を要求しています (`decisions-verbatim.md:50-64`)。本案は「同じ論理trialとqなら、別attemptでも同じidentity」なので後半を満たしません。

[推測] 正しい同型は次です。

`logical campaign座標 + sealed attempt-slot generation + q -> physical campaign run identity`

これなら同一slotへの再入は同identity、別attempt/replicate/prereg generationは別identityです。

[実測] Pegasusでは `allow_resume=False` なので、同一slot/qへの再入は同じlayout/claimへ当たり拒否されます。これは「物理行を再実行せずtombstoneにする」という§7.2とは整合します。ただしprocess crashでsealを失った場合はtombstoneを発行できず、設計上も非終端のままです (`design-doc-verbatim.md:541-550`)。

[推測] したがって決定的導出はresumeを成功させるためではなく、同一slotの二重実行をfail-closedにするためです。planの「乱数はresumeを壊す」という説明だけでは意味が逆転しており、修正が必要です。

## 判定

[推測] planは作り直すべきです。局所修正では足りません。identity seed、slot取得、envelope作成、plan seal、observation開始、物理実行、formal consumptionの順序を組み直す必要があります。

推奨順序は次です。

1. [推測] 論理capabilityを発行し、attempt slotを予約する。
2. [推測] slot capability digestとqからdomain-separatedな物理identityを導出する。
3. [推測] envelopeをcreate-onlyで永続化する。
4. [推測] envelope digestを束縛した第二段plan sealを発行し、observationを開始する。
5. [推測] 各runのcampaign.lock、WAL、receiptをtrusted harnessがfinalizeする。
6. [推測] formal consumerがdisk上のenvelope、lock、WALを自力で再導出してからorigin terminalを許可する。

## 裁定パッケージ候補

1. [推測] 物理identityの世代範囲

   - 推奨: `AttemptSlotCapability` digestとqを入力にする。別attemptは別identity。
   - 非推奨: 論理campaignとqだけに固定し、同trialのretry/反復を永久に禁止する。

2. [推測] envelopeの権威化

   - 推奨: capability発行後に、attempt capabilityとenvelope digestを束縛する第二段plan sealを発行する。
   - 代案: capability schema自体へplan digestを入れる。現構造では相互digestになるため、発行順の再設計が必要です。

3. [実測] V-10 writer trust

   - 選択肢(a): 同一UIDの手書きを脅威圏外とし、「物理実行保証」はsole-writer運用前提付きと明記する。
   - 選択肢(b): 別UIDまたは別namespaceでwriterを分離する。
   - [推測] 提供された決定資料にはV-10の最終裁定がなく、planの「残る択一0件」は成立しません。

4. [推測] 規律2上の受理集合拡大

   - D1616がq別claim/layoutの新規受理まで承認したか。
   - D1555のWAL修理指示がnative WAL shapeの新規受理まで承認したか。
   - provenance/reportのschema変更をin-placeで行うか、新versionで分離するか。

## 総括

- blocker: 6件。
- must-fix: 2件。
- [推測] (a) はFC05a/bで拒否されます。
- [推測] (b)、(c)、(f) は現planを素通りできます。
- [推測] (d)、(e) は正規live経路だけ拒否し、差し替え経路が残ります。
- [推測] planは局所修正ではなく、identity世代とplan sealを含めて作り直すべきです。