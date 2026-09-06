[実測] HEAD `04f06d0326eaf9fad51a3c698b2b3a5e5b062e77` を静的検査した。pytest は実行していない。結論は、**plan はこのまま author へ渡せない**。blocker 6 件、must-fix 9 件、nit 1 件である。

## blocker

### 所見 1 — `SealedTerminalEvidence` が attempt / observation に束縛されていない

- (a) [実測] plan の 19 field と carrier の 3 private fieldには、freeze・protocol・schedule・slot・attempt identity が無い。API は `(observation, evidence)` を別々に受けるだけなので、attempt A で封印した evidence と attempt B の `CapturedObservation` を組み合わせても比較点が無い。plan `s2-plan.md:13-32,219-226,284-294`、現 state `s8b_attempt_registry.py:164-185,229-255`。
- (b) [実測] terminal row 自体は slot/binding を持つが、evidence bytes はそれを名指さない。`s8b_attempt_profile.py:445-462,490-503`。
- (c) [推測] 放置時は別 attempt の status・reason・primary・journal record が対象 slot に束縛され、v5 coverage と certified 選択の参照先が入れ替わりうる。
- (d) [推測] evidence に exact な `attempt_binding` を追加する。最低限 `{freeze_sha256, protocol_sha256, schedule_sha256, slot全軸, schedule_row_sha256, attempt_id, campaign_run_id, manifest_sha256, run_relpath, cell_id}` を持たせ、adapter で `_AttemptState`、classification claim、terminal row の三者と照合する。`evidence-A + observation-B` の直接負例も要る。
- (e) [実測] (P3)、`terminal_evidence_sha256`、D1113。

### 所見 2 — `mode`・perf receipt・classification authority が依然 caller 選択である

- (a) [実測] protocol は canonical hash を registry binding と比較できるが、plan の `mode` と `perf_preflight_receipt` は生の reservation fieldにすぎない。durable admission claim は `mode` を持つ一方、adapter の現照合は freeze/protocol/cell だけで mode を見ない。plan `s2-plan.md:40-41,58-59,234-246`、`s8b_attempt_registry.py:1575-1605`。
- (a) [実測] perf receipt は内部整合を検査できても、manifest や admission authority への束縛が計画されていない。`perf_preflight.py:179-224,261-270`。
- (a) [実測] public launcher は今も caller 提供の `ClassificationAuthority` を受け、その ID と policy digest をそのまま classification へ渡す。`s8b_floor_attempt_launcher.py:557-578,601-609,648-669`。これは設計 wave の launcher-owned authority 要求が plan から落ちた consumer である。
- (c) [推測] 放置時は同じ計測 bytesでも perf 完備性、E2 reason、receipt 上の authority 表示を caller が選べ、台帳の受理集合が変わる。
- (d) [推測] protocol は adapter bindingへ、mode は durable admission claimへ、normalized perf receipt bytesまたは digest は manifest/perf-preflight authorityへ束縛する。production classification authority は launcher 定数と policy bytesから導出し、public API から引数を除く。
- (e) [実測] (P3)、`expected_use_perf`、`mode`、`perf_preflight_receipt`、D1113。

### 所見 3 — `reserve → pre-probe` と consumption marker の既存権限順が両立しない

- (a) [実測] v2 reserve は `FloorAttemptConsumptionMarker` 必須である。`s8b_attempt_registry.py:1932-1963`。その marker は ticket 消費後にだけ検証・発行できる。`s8b_holdout_admission.py:4349-4392,5082-5103`。
- (a) [実測] 現 campaign は pre-probe 後、実測直前の measure wrapper 内で ticket を消費する。`s8b_floor_campaign.py:5941-5995,6241-6263`。pre-probe 競合では wrapper 自体を呼ばない。
- (a) [実測] `consume_attempt_ticket()` が返すのは capture 用 `HoldoutObservationAdmission` であり、plan の reservation は marker しか運ばない。`s2-plan.md:234-246`。
- (c) [推測] 放置時は、pre-probe 除外を台帳化できないか、逆に計測しない attempt の ticket を先に消費して admission budget・resume 判定を変える。
- (d) [推測] 次のどちらかを明示裁定する必要がある。(1) ticket を pre-probe 前に消費し、marker と capture 用 observation capability の組を launcher へ渡す、または (2) pre-probe 除外専用の非 consumption reservation authorityを admission/adapter に作る。後者は既存の「v2 reservation/observation は marker-bound」の変更になる。
- (e) [実測] (P1)、(P2)、`probe_before`、`consumption_marker`。

### 所見 4 — C1a 単独状態は v2 を「閉じたまま」にしない

- (a) [実測] C1a は marker を `_reserve()` に渡す計画である。`s2-plan.md:203-208,234-246`。すると v2 は genesis、start、classification、observation-start まで進み、最後に旧 terminal API の拒否へ当たる。現 launcher は genesis を reserve より前に作る。`s8b_floor_attempt_launcher.py:582-589,600-644`、拒否は `s8b_attempt_registry.py:2536-2557`。
- (b) [実測] v2 observation も同じ markerで実際に開く。`s8b_attempt_registry.py:2434-2468`。
- (c) [推測] certified 出力は production caller 0 のため直ちには変わらないが、C1a checkpoint に非 terminal v2 台帳が残り、C1b/C2 resume の参照状態を変える。
- (d) [推測] C1a では marker fieldを運ぶだけにし、v2 profile/markerを副作用前に専用署名で拒否する。C1b で sealed API と同時にその gate を外す。
- (e) [実測] (P1)、(P5)、C1a の「production 整合・境界固定」。

### 所見 5 — `campaign_record` を crash 後の権威にする検証が不足する

- (a) [実測] plan は `serialize_session_line(campaign_record) == raw_output_bytes` と self-report 3 値の比較だけを明記する。`s2-plan.md:126-130,348-356`。しかし現 session record は attempt identity、throughputs、exec failures、rep evidence、probe 組など多数の field を持つ。`s8b_floor_campaign.py:6361-6380`。
- (a) [実測] byte equality は「campaign が申告した object と bytes が同じ」ことしか証明せず、launcher の reservation/opened facts と一致することを証明しない。
- (c) [推測] terminal-first crash 回復で、異なる attempt ID、throughput、probe、exec failureを持つ session bytesが journalへ復元され、report値・eligible session集合・台帳参照が変わる。
- (d) [推測] journal session の exact key/type表を固定し、全 identity fieldを reservationから、計測 fieldを opened measurement/private sinkから、probe fieldを launcher probeから再照合する。`campaign_record` はこの全照合後だけ durable authorityにする。
- (e) [実測] (P3)、(P6)、`campaign_record`、`raw_output_sha256`、`self_report`。

### 所見 6 — 非有限 throughput の E2 分岐は canonical evidence に到達しない

- (a) [実測] 親契約は evidence の `throughputs` を有限 float 列としながら、非有限値を `measurement_sample_incomplete` の導出条件に含める。brief `s1-brief.md:34-41`。
- (a) [実測] plan は `_num()` が非有限をすべて `None` にするとするが誤りである。`_num()` は `"nan"`, `"inf"`, `"-inf"` だけを明示除去し、実測では `"Infinity"`, `"+inf"`, `"-Infinity"` がそれぞれ `inf`, `inf`, `-inf` になった。`benchparse.py:39-50`。値は `ScalePoint.throughputs` と sink に入る。`runner.py:1003-1023`。
- (a) [実測] canonical JSON は `allow_nan=False` なのでその evidence を封印できない。`attempt_registry_core.py:219-228`。
- (c) [推測] 放置時は本来 `measurement_sample_incomplete` で terminalize すべき attempt が evidence seal errorで停止し、台帳 terminal・report session・certified coverageが欠落する。
- (d) [推測] `_num()` を `math.isfinite()` で閉じるか、evidence/sink の非有限値を `null + nonfinite indicator` に正規化する。後者なら「snapshot」の意味を normalized snapshot と明記する。
- (e) [実測] `throughputs`、`repetition_evidence`、(P4)。

## must-fix

### 所見 7 — field 間の到達可能性 matrix が固定されていない

- (a) [実測] 実環境の値域は次である。

  - `measurement`: production は `ScalePoint | None` で、`throughputs`, `notes`, `rep_observations` を属性で読む。`model.py:54-76`。現 launcher fake は dict を返しており同形でない。`test_s8b_floor_attempt_launcher.py:168-189`。
  - `launch_failures`: exact tuple、各要素は `{exception_type:str, errno:int|null, message:str}` へ射影され、production では概ね 0..reps 件。`runner.py:54-90,847-908`、`launcher.py:321-359`。
  - private sink: capture 時には空で、`token.open()` 内の `open_measurement_point()` 冒頭で reps 件へ初期化され、その後更新される。`runner.py:933-1005`。
  - `use_perf_from_receipt`: `None→True`、available→True、unavailable→False、probe_error→例外。`perf_preflight.py:202-224,261-270`。official は non-null available receiptを拒否する。`s8b_floor_campaign.py:448-455`。
  - `assess_session`: reps は exact intかつ2以上、CV閾値は `(0,1]` の decimal文字列。空列・本数不足・非有限・非正値は例外でなく partial reason、bool/非数値は例外。`s8b_floor_stats.py:127-165`。

- (a) [実測] `probe_after is None` のとき plan が拒否するのは throughputs 非空だけで、実際に必要な一式が無い。`s2-plan.md:398-404`。
- (c) [推測] unreachable combination が durable evidence として受理されると、同じ raw factsから異なるE2 reasonを作れる。
- (d) [推測] 少なくとも次を exact にする。

  - `probe_after=None` ⇔ `probe_before.competing=True`、かつ failures/throughputs/repetition evidence は空、open failure は null、rep integrity は null。
  - opened measurementあり ⇒ open failure null、sink長=reps、rep integrityはexact int。
  - open failureあり ⇒ measurementなし。`exec_failures=reps_expected` とするなら、それが「実測失敗数」でなく unavailable projectionであることを明記する。
  - `expected_use_perf` は receiptから再導出し、capture kwargs の省略時 defaultも正規化して比較する。
  - `reps_expected` と `session_cv_max` は protocolからのみ導出する。

- (e) [実測] DW-O13、全 evidence field、(P2)、(P4)。

### 所見 8 — 規模計数は一部正しいが、既存赤は 16 でなく 14 node

- (a) [実測] 現物行数は direct C1 production 4 fileで `701 + 3122 + 2131 + 684 = 6,638` 行。support は stats 1,278、runner 1,276、campaign 8,645 行である。
- (a) [実測] ASTで parametrize を展開した値は planどおり、launcher `7関数/12 node`、adapter `75/111`、core/profile `68/108`、spawn inventory `43/44`。plan `s2-plan.md:159-168` は正しい。
- (a) [実測] required reservation fieldを planどおり足す場合、更新必須は launcher 全12 nodeに、E2 pin `test_v2_profile_is_additive_empty_retryable_and_budgeted_by_cell`、historical v2 terminal `test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive` を加えた **14 unique node** である。
- (a) [実測] `test_profile_extension_fields_are_keyword_only_and_preserve_legacy_defaults` は現状 equality flagを pinせず、validator non-nullだけを見るため自然には赤くならない。`test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed` も旧API拒否を維持する限り緑のまま。両者は強化対象だが赤ではない。`test_attempt_registry_core_s8b_profile.py:2219-2248`、`test_s8b_attempt_registry.py:3000-3105`。
- (c) [推測] 件数差自体は成果物を変えないが、16赤前提では「実際には通った旧 pin」を supersede しやすく、受理集合回帰を隠す。
- (d) [推測] 「既存赤14」と「緑のまま強化する2」を分離する。launcher 12 nodeは7定義すべて、うち動作差が出るのは ordering 3 param + open error 1が中心である。
- (e) [実測] (P5)、plan 依頼2、fixture transitive赤。

### 所見 9 — `record_attempt_terminal` の全 consumer と fake の実契約

- (a) [実測] S8B production 鎖は launcher `:637` → adapter `:2544` → core `:2580`。legacy classified-failure APIも coreを `:2636` で呼ぶが production callerは0、test callerは `test_s8b_attempt_registry.py:713` の1件。
- (a) [実測] adapter APIの既存 test consumerは planどおり13 node、coreのS8B helper consumerは12 nodeである。plan `s2-plan.md:180-184`。
- (a) [実測] coreの他 domain production consumerは `trial_registry.py:3294-3434`、その上の formal producerは `p3_autonomous_workload_trial.py:4208-4291` から5経路で呼ぶ。test側はS8C 8、equivalence 1、trial 7 node。optional defaultなら赤くしない判断は妥当である。
- (a) [実測] 見落としは launcher fake の意味契約である。`_RecorderRegistry.record_attempt_terminal` は `**kwargs` を記録するだけで実 adapterのseal検査を通らず、`_Token.open()` は `ScalePoint` でなく dictを返し、capture kwargsもprivate sink追加を許容しない。`test_s8b_floor_attempt_launcher.py:86-189,279-315`。
- (c) [推測] fakeと実体が別契約のまま緑になると、launcherが発行する evidenceを実 adapterが一度も受理できず、production terminalが0件になる。
- (d) [推測] fakeにも production の `_require_sealed_terminal_evidence()` を呼ばせ、sinkをopen時に更新するScalePoint形 tokenへ変える。実 adapterを通す launcher統合正例を別に維持する。
- (e) [実測] (P3)、(P5)、D1522。

### 所見 10 — C1b の2本並列境界は型として未確定

- (a) [実測] plan は `_require_sealed_terminal_evidence()` の戻り型を定めず、`TerminalProjection` の exact field/typeも定義していない。adapterはcanonical bytes、digest、projection、attempt bindingを必要とするため、3 private fieldだけではunit2の実装が一意に決まらない。`s2-plan.md:214-230,428-453`。
- (a) [実測] 新 moduleはunit1所有だがunit2がimportして検証するため、unit2はunit1なしではimport/testできない。片側先行時の独立greenは対称には成立しない。
- (c) [推測] 放置時は両側が別々のunseal戻り値やfield名を仮定し、統合時にAPI修正とfixture全面修正が発生する。
- (d) [推測] C1bの前に小さい contract leafを固定する。`ValidatedTerminalEvidence` の exact dataclass、`seal_terminal_evidence(reservation, opened, terminal)`、`require_sealed_terminal_evidence(value) -> ValidatedTerminalEvidence`、attempt binding、canonical bytes/digestを先に置き、その後 launcher と adapterを並列化する。
- (e) [実測] (P3)、(P5)、所有分割。

### 所見 11 — C2 は launcher signatureを変えずには呼べるが、現 campaign seamのままでは動かない

- (a) [実測] protocol/mode/receipt/reps/CV は `_Runner` の `self.protocol`, `self.mode`, `self.perf_preflight`, `self.reps`, `self.session_cv_max` から供給可能である。`s8b_floor_campaign.py:6033-6081`。
- (a) [実測] 一方、markerとcapture用 observation capabilityは現在 measure wrapper内でだけ取得され、launcher呼出し前には存在しない。`s8b_floor_campaign.py:5959-5993`。
- (a) [実測] `_finish_session()` は recordを作るだけでなく即 journalへfsyncする。terminal builderからそのまま呼ぶと registry terminalより先にjournalが書かれる。`s8b_floor_campaign.py:6346-6383`。
- (a) [実測] 328 test関数/476 nodeが依存する既存 `measure_fn` / `probe_fn` seamを、certified public launcherは受けない。`s8b_floor_attempt_launcher.py:648-670`。
- (c) [推測] 放置時は二相順序が journal-firstへ逆転するか、非default campaign test/pilot seamが全拒否される。
- (d) [推測] C2境界に、pure `_build_session_record()`、production launcher callable、明示的 noncertifying launcher seam、consume結果の capability pairを固定する。`launch_floor_attempt` 自体へ mode/reps/CVの追加引数は不要だが、reservation authorityの補正は必要である。
- (e) [実測] (P1)、(P2)、`campaign_record`、`finished_at`。

### 所見 12 — mutation 16件中、M4/M6/M7/M11/M16 は現記述では帰属不成立

- (a) [実測] M4 の `_read_regular_bytes` call数だけを見るspyは registry本体やclassification receiptのreadでも満たされる。evidence exact pathを観測しないと mutation がmaskされる。`s8b_attempt_registry.py:582-632,903-978,2116-2135`。
- (a) [推測] M6 は通常のrep evidenceを使うと、bool反転がcounter status/missing events gateにも掛かる。pre-probe skipのneutral documentか、receipt導出helperの直接testへ分離すべきである。
- (a) [実測] M7 は `_seal_terminal_evidence(document)` に registry binding引数が無く、どの関数のprotocol digest比較を変異するのか未確定である。所見1のbinding補正後に再登録が必要。
- (a) [実測] M11 は plan自身が要求する `raw_output_bytes == serialize_session_line(campaign_record)` の独立gateに遮られる。digest導出だけを変えても同じ不一致が先に拒否される。`s2-plan.md:128-130,469`。
- (a) [実測] M16 は到達不能である。`_derive_rep_integrity()` で failureが出たrepはqualified throughputへ入らないため、qualified列をevidence `throughputs` と照合するplanでは本数不足が先にpartialになる。CV dispersionとの同居入力は作れない。`s8b_floor_stats.py:471-589`、plan `s2-plan.md:45,474`。
- (c) [推測] 放置時は SURVIVED を実装欠陥と誤認するか、別gateによる赤を対象gateのKILLEDとして記録する。
- (d) [推測] M4はevidence path exact spy、M6はreceipt helper直接、M7はadapter binding比較、M11はbyte equalityとの多層同時変異または登録除外、M16は到達可能な「post-probe競合 + open failure」のprecedenceへ再照準する。加えて `evidence-A + observation-B` mutationを登録する。
- (e) [実測] 依頼4、D1522、(P3)、(P4)、(P6)。

### 所見 13 — 親の1回目focusで赤を集約する実行集合が未固定

- (a) [実測] plan は新nodeの配置だけを列挙し、親が最初に走らせるexact file/node集合を定めない。A1'では非所有 consumerが118赤、B2/D1では新fixtureのcampaign identity衝突が親実走まで遅れた。`a2alpha-README.md:113-130`、`b2d1-README.md:49-54`。
- (a) [実測] 今回も fake token形、real marker capability、同一claim identityの再利用という同型リスクがある。
- (c) [推測] 放置時は所有4 fileのgreen後に、trial facadeまたはreal adapter integrationの赤がfix巡へ遅延する。
- (d) [推測] 最初の親focusを少なくとも launcher、adapter、core/profile、spawn inventory、core equivalence、trial registry、対象S8C facade、holdout/campaignのv1 recovery対照まで1回で走らせる。子はpytest不能時に新fixtureの対象関数direct-callとgate除去反実仮想を必須にし、各paramで固有repo/campaign identityを使う。
- (e) [実測] (P5)、codex子のpytest不能前提。

### 所見 14 — (P5) は不採用で正しいが、C1bもA2α級である

- (a) [実測] planの基礎見積りは production 573〜793追加、test込み1,600〜2,300 changed LOC。`s2-plan.md:146-157`。A2αは5 file、+1,671/−97、fix 5巡だった。`a2alpha-README.md:5-9`。B2/D1は+1,749/−11、fix 2巡だった。`b2d1-README.md:5-7,49-54`。
- (a) [推測] 所見1〜7のbinding、authority、reachability matrix、campaign record全照合を足すと、C1全体は約2,100〜3,100 changed LOC、うちC1bだけで約1,650〜2,400 LOCが妥当である。
- (c) [推測] 一波扱いするとfake/adapter/artifactの統合不良がfix段へ集中し、未検査の受理面を残す確率が上がる。
- (d) [推測] C1aは所見4の早期gate込みで1 checkpoint、C1bはcontract leaf後に1 checkpointとする。fix見積りはC1a 2巡、C1b 4〜6巡、統合1巡、全体6〜8巡を基準にする。
- (e) [実測] (P1)、(P5)。

### 所見 15 — durable artifact経路は概ね正しいが、全readerと観測点をexact化すべき

- (a) [実測] `prepare()` がregistry staging前にあるため、evidence-first公開の基礎は正しい。`s8b_attempt_registry.py:1666-1736`。
- (a) [実測] terminalを含む世代を受理しうるload面は prefix `:974`、他世代budget `:1647`、atomic old/candidate `:1687,1698`、public read `:1883`、reserve/observe snapshot `:1942,2439`、resume `:2791`。planは主要面を挙げるが、mutation/testとの1対1対応がない。
- (a) [実測] prefix readerは現状、shared lock内でpayloadを読んだ後、lock外でcore replayする。`s8b_attempt_registry.py:903-978`。planがlock区間をartifact readまで延長する判断は妥当である。
- (c) [推測] readerが1面でもartifact検査を迂回すると、欠落evidence付きterminalからprefix proofが作られ、v5 resultの参照集合が広がる。
- (d) [推測] 各load面を表にし、terminalあり正例/欠落負例を直接当てる。M4 spyは `_terminal_evidence_path()` のexact pathをassertする。candidateはpublish後・staging前に再検査する。
- (e) [実測] (P6)、`terminal_evidence_sha256`、D1522。

## nit

### 所見 16 — 親 brief の実アンカーと一般化に誤りがある

- (a) [実測] production行数は正しいが、launcher行アンカーは複数ずれる。実際は `FloorAttemptTerminal:125`、`_owned_post_probe:238`、`_external_evidence_sha256:362`、`_pre_observation_failure_reason:378`、`_launch_floor_attempt:548`、terminal call `:637`。brief `s1-brief.md:96` の `:123/:232/:350/:366/:527/:628` は誤り。
- (a) [実測] `S8B_V2_RETRYABLE_FAILURE_REASONS` は `s8b_attempt_profile.py:533`、`_finish_session` は `s8b_floor_campaign.py:6346`、`RESULT_SCHEMA` literal/aliasは `s8b_floor_contract.py:35-36`。
- (a) [実測] briefの `7/75/68 node` はtest関数数で、node数は `12/111/108`。campaignも `328関数/476 node` で、briefの「328 node」は誤り。brief `s1-brief.md:66-67,103`。
- (a) [実測] DW-O09のtracked v2 registry 0件とv4 pinは正しい。ただし現event_keys testは全eventの `measurement_ordinal` しか見ず、terminal evidence keyをpinしていない。`test_attempt_registry_core_s8b_profile.py:2211-2212`。
- (a) [実測] DW-O13の「fake tokenで値域を組める」は誤り。fake measurementはdict、pre-probeとprivate sinkは未実装、v2 terminalは全拒否である。brief `s1-brief.md:112-115`。
- (c) [推測] 行ずれ自体は成果物を変えないが、node誤計数とDW-O13の一般化はreview量と受理可能入力の判断を誤らせる。
- (d) [推測] briefのアンカー、node表、DW-O09/O13を上記実測へ訂正する。なお `_receipt_path()` はflatなclassification receipt pathなので、P6のnested `terminal-evidence/` には専用 `_terminal_evidence_path()` を新設する。`s8b_attempt_registry.py:1430-1437`。
- (e) [実測] (P5)、(P6)、DW-O09、DW-O13。

## 裁定パッケージ候補

1. [実測] **pre-probe除外時にadmission ticketを消費するか。** 所見3の二案は受理集合と予算意味を変える。現scope外の admission authority変更を伴うため、人間裁定候補である。
2. [実測] **非有限値をrunnerで除去するか、evidenceで表現するか。** `benchparse._num()` の修正はC1所有外かつ既存計測値域を変える。C1内のnormalized evidenceで閉じない場合は裁定候補である。

## 総括

- blocker 6件、must-fix 9件、nit 1件。
- [実測] 既存行数はdirect C1 production 6,638行、主要test 10,464行。
- [実測] parametrize展開後は12 / 111 / 108 / 44 node。親の7 / 75 / 68は関数数。
- [実測] planどおりrequired reservation fieldを足す場合、赤になる既存nodeは16でなく14。
- [推測] 規模はC1全体2,100〜3,100 changed LOC、fix 6〜8巡が妥当。
- [推測] (P1) C1/C2分割とC1a/C1b分割は条件付き採用。C1aにv2早期gateが必要。
- [推測] (P2) launcher所有pre-probeは採用。ただしmarker順序は未裁定。
- [推測] (P3) handle案は採用。ただしattempt-bound identityとexact unseal型が必須。
- [推測] (P4) observed/retryable対応とv2文字列等値解除は採用。
- [推測] (P5) 1 waveは不採用。C1bもA2α級として扱う。
- [推測] (P6) create-only + row digestは採用。専用pathと全reader検査が必要。