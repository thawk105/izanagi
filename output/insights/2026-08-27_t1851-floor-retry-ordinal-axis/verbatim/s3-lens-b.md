## consumer 閉包の所見

1. **plan の slot identity 代案 (a) の production consumer 列挙はほぼ閉じているが、完全な在庫表ではない。**

   production の `SlotCodec` 実装は `S8BSlotCodec` (`orchestrator/campaign/s8b_attempt_profile.py:53-148`) と `_S8CSlotCodec` (`orchestrator/campaign/trial_registry.py:1983-2002`) の 2 本だった。4-tuple を実際に生成・比較する経路も、plan が挙げた以下で尽きる。

   - `slot_id` 生成: `s8b_attempt_profile.py:121-129`
   - `series_key`: `s8b_attempt_profile.py:131-143`
   - `budget_key`: `s8b_attempt_profile.py:405-408`
   - core の lookup/prefix/budget: `attempt_registry_core.py:483-509,539-584,1062-1129,1513-1523`
   - holdout の別名 tuple 生成: `s8b_holdout_admission.py:4200-4205,4241-4289,4304-4310,4470-4477`
   - scheduler の tuple 比較: `s8b_scheduler_accounting.py:319-350`
   - launcher の membership: `s8b_floor_attempt_launcher.py:472-500`
   - 8c 側: `trial_registry.py:1930-2002`

   ただしテスト内の部分 codec `orchestrator/tests/test_s8b_floor_attempt_launcher.py:43-69` は plan の file:line 一覧にない。具体状態は、案 (a) で production codec だけを 5-tuple 化した場合、この fake は旧 4-tuple のまま緑になり、launcher の identity closure を検査しなくなる。

2. **選択案 (b) では `FloorRetryAuthorization` が issuer-bound でなく、「reason を caller から自由入力させない」という説明が機械的に成立していない。**

   現在の authorization は公開 dataclass (`s8b_holdout_admission.py:217-230`) で、runner は `isinstance` しか検査しない (`s8b_floor_campaign.py:5871-5887`)。plan は `reason` と `evidence_sha256` を追加するだけで seal や再導出を予定していない (`s2-plan.md:115-120`)。

   具体状態は、注入された `retry_trigger_query_fn` が、実際の trigger session は `launch_failure` なのに `reason="performance_anomaly"` の `FloorRetryAuthorization` を構築する場合である。型検査は通り、durable writer が journal から再導出しなければ誤った理由が start row に固定される。新しい保証は authorization object の issuer identity、または launcher 内での evidence 再導出が必要である。

3. **plan の新しい glob inventory は sink 閉包が足りない。**

   plan は adapter import、`reserve_attempt_slot`、`capture_measure_point` を列挙する (`s2-plan.md:231-237`) が、公開 `launch_floor_attempt()` の全 production caller と `FloorAttemptTerminal` builder の在庫を固定していない。現在は production caller 0 件である (`s8b_floor_attempt_launcher.py:648-670`)。

   具体状態は、新規 production module が public launcher を直接呼び、output-derived の任意の閉集合 reason を terminal builder から返す場合である。adapter/capture の caller 数は変わらないため、plan の列挙だけではこの生成器追加を捕捉できない。

4. **D444 の 16 field については、plan 内に実質的な値変更は見つからない。**

   `retry_slots_per_cell` は既に ticket 数 (`s8b_holdout_admission.py:1194-1202,1319-1350`) と runner 上限 (`s8b_floor_campaign.py:5794-5797`) を支配している。これを同じ値の registry 上限として読むこと自体は値・既存受理集合の変更ではない。`allowed_excluded_reasons` の固定順照合 (`s8b_floor_contract.py:523-528`) も plan は変更していない。

## 記録の同一性の所見

1. **選択案 (b) の新軸は slot identity ではなく start row の metadata であり、台帳の各行から単独では復元できない。**

   plan は 4 field を start event だけへ追加する (`s2-plan.md:64-71,89-97`)。terminal/classification は引き続き 4-tuple slot だけで識別される (`s8b_attempt_profile.py:291-365`)。具体状態は、terminal row 1 行だけを渡された場合で、`remeasurement_ordinal` はその行に存在せず、対応 start rowとの join が必要になる。

   同じ `(cell, round, attempt_ordinal)` に異なる新軸を持つ start を 2 行置くと、core は旧 4-tuple の `slot_id` で衝突させて二つ目を拒否する (`attempt_registry_core.py:1005-1010,1062-1076`)。したがって valid registry 内では曖昧な複数行は作れないが、これは「独立軸だから識別できる」のではなく「同じ旧 slot に 1 行しか置けない」ためである。

2. **最大の欠陥は、certified verifier が新 registry を一切 proof chain に入れないことである。plan のままでは親 brief の影響は解消しない。**

   `verify_floor_artifact` 自身が attempt registry と schedule の突合を保証外と明記している (`s8b_floor_stats.py:412-416,682-695`)。live wrapper も holdout admission ledger を検査するだけで registry を読まない (`s8b_floor_stats.py:1036-1082`)。ratified verifier も result、journal、live admission だけを渡す (`s8b_ratified_freeze.py:3209-3242`)。plan は `s8b_ratified_freeze.py` を変更不要としている (`s2-plan.md:158-162`)。

   具体状態は、legacy `performance_anomaly` による測り直し完了後、S8B attempt registry を削除または不正化し、journal・consume marker・attempt admission ledger を残した場合である。legacy trigger は registry rows が無くても受理される (`s8b_holdout_admission.py:4222-4238,4296-4303,4609-4621`)。したがって artifact verification は新軸の欠落を検出しない。台帳へ書く production 経路は増えるが、certified 選択がその台帳を根拠にする保証は増えない。

3. **D1007 の「最初の測り直しで止まる」は回避できるが、plan はそのために二つの既存防壁を実質変更している。**

   具体入力は、planned attempt の pre-output classification が `None` で、観測後に `performance_anomaly` となる session である (`s8b_floor_campaign.py:6012-6045`)。

   - 現在は terminal reason equality が `None != performance_anomaly` を拒否する (`attempt_registry_core.py:1264-1279`)。
   - その terminal を `terminal-failure` にすると、次の primary attempt は non-retryable outcome として拒否される (`attempt_registry_core.py:1085-1119`)。

   plan は equality 例外と、secondary reservation がある場合の `terminal-failure` predecessor 例外を同時に追加する (`s2-plan.md:89-97`)。よって最初の測り直しは止まらないが、`require_previous_terminal` は満たしても、`require_terminal_reason_equals_classification` はこの入力では満たしていない。また定数 `S8B_RETRYABLE_FAILURE_REASONS` が空のままでも、「次を開ける outcome」の集合は実質的に広がる。plan の「retryable_failure_reasons を広げない」という説明だけでは D1007 の防壁維持を証明できない。

4. **schema `/v2` 化の readable 集合と live registry の扱いが欠落している。**

   現在の S8B `SchemaProfile.readable` は v1 だけである (`s8b_attempt_profile.py:367-375`)。単に定数を v2 へ変えると、v1 genesis は `_schema_version()` で拒否される (`attempt_registry_core.py:429-435`)。既存 registry は repo 内ではなく Git common dir 配下に置かれる (`s8b_attempt_registry.py:462-482`)。

   具体状態は、shared admission root に v1 registry が存在する最初の production launchである。launcher は create-only 失敗を resume とみなした後に既存 bytes を読む (`s8b_floor_attempt_launcher.py:503-520`) が、v2-only readable なら unsupported schema で capture 前に停止する。

   repo に commit 済み run artifact がないという brief の実測 (`brief.md:44-48`) は、repo artifact の migration を不要にする。しかし shared root の未追跡 v1 registry が存在しない証拠にはならない。最低限、v1 を readable-only に残すか、live state 不在を別途検査して明示的に拒否する必要がある。v1 genesis へ v2 row は append できないため、readable 追加だけでも書込 migration は解決しない (`attempt_registry_core.py:1046-1051`)。

## テスト閉包の所見

1. **`test_attempt_registry_core_equivalence.py` は新軸の正例ではない。**

   byte equality test (`test_attempt_registry_core_equivalence.py:436-470`) は secondary policy が無い 8c profileだけを通す。新軸を全く実装しなくても現在緑である。逆に generic builder が新 field を無条件追加すれば bytes mismatch、`reserve_attempt_slot` の新引数を必須化すれば `_core_reference()` (`:299-350`) が `TypeError` になる。

   またこの equivalence は 8c compatibility profileの terminal reason mismatch を意図的に許している (`:274-295,336-349`)。S8B equality 例外が 8c formal policyへ漏れない保証にはならない。必要な既存 canary は `test_trial_registry.py:7111-7158` であり、plan のテスト表にない。

2. **plan が挙げたうち、新軸が無くても緑のままになり得るものがある。**

   - `test_attempt_registry_core_equivalence.py:436-470`
   - `test_s8b_ratified_verify.py:1373-1397`
   - `test_s8b_floor_stats.py:848-874`
   - `test_s8b_protocol_builder.py`
   - `test_s8b_approved.py`

   これらは 8c bytes、既存 journal budget、4理由、既存 schema の回帰 canaryであり、新しい genesis policy/start field を検査しない。`test_s8b_scheduler_accounting.py` の「4-tuple のまま」検査も、factory が `retry_slots_per_cell` を受け取るだけで無視する実装を落とせない。生成器そのものを固定するには、serialized genesis bytes と start row 4-field unionを直接検査する必要がある。

3. **plan が個別に名指していない既存テストで、production wiring により確実に赤くなるものがある。**

   - `test_s8b_freeze_io.py:242-485` は `s8b_floor_campaign.measure_point` を patch して呼出しを観測する。launcher の captured dependencyへ移すと spy は発火しない。
   - `test_s8b_floor_campaign.py:1422-1449` は repo-wide AST inventory に `s8b_floor_campaign.py` の直接 `measure_point` 1件を固定している。直接呼出し削除で stale inventory になる。
   - `test_s8b_floor_campaign.py:7423-7460,7463-7491,7494-7555` も同じ旧 patch surface に依存する。

   `test_s8b_floor_campaign.py` 自体は計画表にあるが、上記 node の更新理由は記載されていない。`test_s8b_freeze_io.py` はファイルごと漏れている。

4. **不足する positive/negative test がある。**

   具体的に必要なのは以下である。

   - valid artifact の registry を削除したら ratified verify が落ちる。
   - terminal row 単独ではなく、full replayで start の新軸へ一意に joinできる。
   - 同じ旧 slotへ異なる `remeasurement_ordinal` の二重 startを入れると duplicate-start で落ちる。
   - factory が `retry_slots_per_cell` を無視する変異で、serialized genesis test が赤になる。
   - S8B equality 例外を `_S8C_FORMAL_ATTEMPT_PROFILE` に適用する変異で `test_trial_registry.py:7111-7158` が赤になる。
   - public launcher caller、`FloorAttemptTerminal` builder、`FloorRetryAuthorization` constructor の production glob inventory。

## 整合・実効性の所見

- plan と brief の production anchor はすべて実在した。`attempt_registry_core.py:73,494,1081-1090`、holdout `:4289,4304,4470`、scheduler `:349`、8c `trial_registry.py:1998` は正しい。
- テスト anchor は実在するが説明と現在内容がずれている。`test_s8b_floor_contract.py:327` は現状 attempt ID transplant test、`test_s8b_ratified_verify.py:1373` は session-start schedule mutation testであり、新軸 canaryではない。
- brief のアンカー表に明確な file:line 誤りは見つからなかった。
- 「1モジュール族なので実装子1本で閉じる」(`brief.md:113-119`) は成立しない。変更は generic core/8c compatibility、8b durable adapter、holdout authorization、trusted launcher、campaign state machine、ratified verifierに跨がる。
- 安全な分割は source 層別ではなく vertical slice で行うべきである。

  1. legacy statistical remeasurement の完全な production slice: v2/readability、core、adapter、holdout legacy reason、launcher、campaign、live/ratified verifier、no-capture branch、関連テストを同時に land する。planned attemptから既に production caller があるため、前半だけでも caller 0 の死んだ gateにはならない。
  2. `verified-registry-recovery` の secondary sourceを別 waveにする。現在は authority集合が空 (`s8b_holdout_admission.py:101-105`) で、collectorも理由を発行不能 (`s8b_scheduler_accounting.py:59-62,780-782`) なので、legacy sliceから外しても到達可能な機能は失わない。

  writer と verifier を別々に land する分割は不可である。writer先行なら certified proof chain がregistry欠落を許し、verifier先行なら既存 campaignを停止させる。

## scope 外だが real な所見 (裁定パッケージ候補)

1. **D1032 の文面と P1/P4 は衝突している。**

   D1032 は別軸を選んだ同じ決定文で「受理する理由の集合を広げる場合も外部 scheduler 証拠に限る」としている (`docs/decisions.md:35995-36009`)。plan は legacy sourceへ4つの非 scheduler 理由を追加する (`s2-plan.md:43-60,197-205`)。これを「既存 primary retryable 集合だけへの制約」と読む根拠は provisional であり、実装前に人間裁定へ戻すべきである。

2. **recovery source は現状 production 発行不能である。**

   S8B start schema に `scheduler_request_id` がなく registry binding は inert (`s8b_scheduler_accounting.py:319-365`)、Exit Code対応表も空 (`:59-62`) である。具体状態は任意の保存済み qstat recordで、`collect_scheduler_accounting()` は claim作成前に unclassifiable で停止する (`:764-815`)。この unreachable branchを今回の大きな vertical sliceへ同梱する理由は弱い。

## 根拠薄・未確認

- pytest、build、checker は実行していない。所見は静的検査のみ。
- `git ls-files` と repo 内 content走査では、commit 済みの実 S8B floor registry/run artifactの反例は見つからなかった。brief の「repo に1件もない」実測には反例なし。
- Git common dir 配下の shared admission root に live v1 registry があるかは、この単独段の読取対象外として未確認。
- 実装後の行数と、legacy vertical sliceだけに絞った正確な差分量は未確認。

## 総括

plan はそのままでは実装へ進めない。最大の理由は、新軸を書き込む production 経路は作るのに、`verify_floor_artifact`、ratified verifier、certified 選択がその registry の存在・完全性・journalとの対応を要求しないためである。したがって親 brief が掲げた「certified proof chainから測り直しが欠落する」問題は解消しない。

加えて、最初の測り直しを通す案は `terminal-failure` predecessor と terminal reason equality の二重例外であり、空の retryable 定数を保つだけでは D1007 の防壁維持にならない。schema v1の live state方針、8c formal equality test、旧 measurement patch surfaceの更新も planへ追加する必要がある。