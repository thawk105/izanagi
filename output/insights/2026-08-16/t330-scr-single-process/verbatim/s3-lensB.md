判定: Y は現状 land 不可。ただし親の X 根拠には、caller 在庫・D108・C12 の訂正が必要です。pytest、build、計測は実行していません。

### [refuted] 親の「`run_campaign` caller は 8 本だけ」という在庫主張

- 根拠: `brief.md:23-28` に対し、`brief-addendum.md:7-24` と `orchestrator/tests/test_campaign.py:4720-4740` は 12 ファイル、15 箇所を列挙している。追加は `p3_kickoff.py:111,118`、`p3_s4_loop.py:951`、`p3_s4_red.py:165,175`、`s8a_trigger_sweep.py:464`。
- 成果物影響: DW-G04 の探索対象は増えるが、既存の certified 選択、レポート、proof chain、台帳の値は変わらない。親の「caller 不在」という根拠は「sanctioned caller と成功 ID の不在」へ修正すべき。
- 反証条件: 追加 4 ファイルが production caller ではなく、tests・vendor・out-of-scope と確認される観測。

### [real] 直接 caller の存在は DW-G04 の発火 artifact または計測 IDではない

- 根拠: `docs/dev-wave/core.md:60-63` は発火条件を満たす既存 artifact path または計測 IDを要求する。`s2-plan.md:18-24` は tracked PBS script が `campaign.loop.run_campaign` を起動しないと認め、`brief-addendum.md:59-60` の `911096` / `911104` は probe、`911106` は admission failureに留まる。
- 成果物影響: claim、reservation、`run_campaign`、`build_v2` を通った成功 IDがないため、Y は設計メモ止まり。新しい certified 選択、レポート、proof chain、受理集合は生じない。
- 反証条件: tracked PBS wrapperから `campaign.loop.run_campaign` まで到達し、claim・reservation・build・WALを含む完走 artifactまたは成功計測 IDが得られること。

### [real] 床値経路の既存 wrapper は loop sink の発火 caller ではない

- 根拠: 床値 wrapper は `floor_campaign.sh:962-965` から `s8b_floor_campaign.py` の別実装 `run_campaign` (`s8b_floor_campaign.py:4044-4058`) を起動する。claim は `s8b_floor_campaign.py:4240-4263`、一方 `campaign.loop.run_campaign` の引数は `loop.py:92-136` に claim/reservation を持たない。
- 成果物影響: 床値の既存 claim/reservation を再利用しただけでは Y の caller 実在にならない。床値の既存受理集合と proof chain は現状不変だが、共通化で床値 sink を置換すると回帰する。
- 反証条件: floor custom sink と混同せず、loop sinkを直接起動する wrapperとその end-to-end artifactが存在すること。

### [real] p3/8c を計算ノードで起動する wrapper は D125(6) と T-276 の境界を開く

- 根拠: `docs/decisions.md:6136-6139` は 8c の計算ノード運転を禁止する。実際に `p3_autonomous_workload_trial.py:2629-2645` から `p3_s4_loop_trigger_gating.py:595-604` へ到達し、`p3_autonomous_workload_trial.py:2775-2785` は compute transport を明示 opt-in に限定する。D108 の campaign task 凍結も `docs/decisions.md:4986-4993` に残る。
- 成果物影響: 新 wrapperはPegasus exploratory WAL・provenance・受理経路を増やす一方、D125の所有境界を越える。D125(7)上も得られるのは floor certified 選択ではなく exploratory 値 (`docs/decisions.md:6141-6145`)。
- 反証条件: wrapperが8cやLLM roleを起動せず、許可済みの機械的 build/verify/benchだけを運転すること、またはD125(6)/T-236を人間が明示変更すること。

### [refuted] D108 決定 (1) の `claude -p` 禁止を現行の禁止根拠として使うこと

- 根拠: `docs/decisions.md:4983-4987` は D108(1) の禁止を D122 が supersede したと明記し、`docs/decisions.md:5880-5898` は T-276 の明示 opt-in解禁を定める。
- 成果物影響: D108(1)を生きた禁止として記録するのは裁定パッケージの誤り。現在の certified 選択、レポート、proof chainは変わらない。生きている制約はD125(6)とT-236のcampaign task凍結。
- 反証条件: D122を明示的に失効させ、D108(1)を再発効する新しい人間裁定。

### [refuted] sink-local claim acquisition だけで D125(4) の「二つの真実」になるわけではない

- 根拠: D125(4)の単一 sink制約は attestationの順序と一回性 (`docs/decisions.md:6123-6128`) であり、`loop.py:61-89` と `loop.py:130-136` に既存 sinkがある。段 2 プランも caller supplied claimを受けず sink-local acquisition としている (`s2-plan.md:55-57`)。
- 成果物影響: claimをsink内で取得し、attestationをloopだけに残す設計なら、この指摘単独では certified 選択やproof chainを変えない。
- 反証条件: wrapperまたはdriverも `attest_and_build_receipt` を呼ぶ、または別 receiptを正本として記録する観測。その場合は重複実装として real。

### [real] `reservation.check_reservation` は binding の host を現在 host と照合しない

- 根拠: `orchestrator/campaign/reservation.py:218-270` は PBS_JOBID、boot ID、時刻、容量だけを検査し、`binding.host`を現在 hostnameと比較しない。wrapperは hostを設定する (`tools/pegasus/floor_campaign.sh:716-740`) が、floor側も同じ検査を呼ぶ (`s8b_floor_campaign.py:4205-4221`)。
- 成果物影響: 新しい Pegasus artifactの実行 host provenanceが確定せず、measurement IDを受理集合やproof chainへ加えられない。既存 floor経路を共通化して変更すると、誤 bindingを拒否する方向の受理集合変化も起きる。
- 反証条件: 検査時に現在 hostnameを取得し、binding.hostとの完全一致を要求する実装と、正しい hostを供給する wrapperの組が確認できること。

### [real] `single_process` を loop 全 callerへ無条件に共通化すると OTHER 経路を壊す

- 根拠: Pegasus契約は `single_process=True` (`env_contract.py:245-258`) だが、linux-baremetal契約は `single_process=False` (`env_contract.py:284-300`)。`pipeline.py:613-616` は未指定 callerを従来経路に残す契約で、loopの全callerは `loop.py:92-136` に集約される。
- 成果物影響: 無条件強制なら PBS環境を持たない OTHER callerのWAL、レポート、受理集合を変え、D125の「OTHERを1 bitも変えない」境界を破る。
- 反証条件: authorized contractの `isolation_policy.single_process is True` の場合だけ発火し、OTHERのbuild namespace・campaign identity・cache keyを変更しないこと。

### [refuted] `AcquiredClaim` が public dataclass であることだけでは sink-local Y 全体を偽造可能とはいえない

- 根拠: `campaign_claim.py:62-68` は構造上 constructibleだが、実際の原子的取得は `campaign_claim.py:167-228` にあり、床値は戻り値を権限として受け取らず `s8b_floor_campaign.py:4253-4263` で取得している。段 2 プランもこの形を指定している (`s2-plan.md:55-57`)。
- 成果物影響: callerからclaim objectを受け取らないなら、R2だけを理由にY全体を否定するのは過剰。claim objectを権限として受け取る実装なら、measurement artifactの受理を止める必要がある。
- 反証条件: `run_campaign` が caller supplied `AcquiredClaim` を受け入れる、または取得副作用を検査せず objectの存在だけを権限にすること。

### [real] `env_contract.py` の registry・`contract_sha256`・凍結 bytes は共通化の編集面にしてはならない

- 根拠: registryは宣言と強制を分離した read-only構造 (`env_contract.py:7-19`) で、`contract_sha256` は全 fieldのcanonical JSONから導出される (`env_contract.py:159-169`)。Pegasusのgolden hashは `env_contract.py:240-281`、registry/activation indexは `env_contract.py:367-371` で固定される。
- 成果物影響: ここを触ると契約 hash、activation、calibration参照、build/campaign identityの受理集合が変わり、既存のPegasus proof chainや凍結参照が無効化され得る。Yは既存契約を読むだけで足りる。
- 反証条件: 新しい環境契約が必要だという人間裁定、対応 calibration bytes、activation successor、golden hashが同時に存在すること。

### [real] F319 の汚染対象は third-party source cache であり、S4 の build-variants `cache_root` ではない

- 根拠: F319は ignored生成物71件と `config.h` を第三者source treeの問題として記録する (`docs/failures.md:7707-7727`)。原因は `ThirdParty.cmake:66-77` の source tree内build。床値のbuild-variants rootは `s8b_floor_campaign.py:1941-1954`、third-party rootは別に `s8b_floor_campaign.py:1582-1603,2019-2021` で解決される。
- 成果物影響: `cache_root`を`/scr/<job>`へ移しても、F319のconfig.h/archive汚染、床値・Silo ladderのoracle/proof chainは救われない。汚染を含む値をcertified選択へ入れる受理集合は閉じたままにすべき。
- 反証条件: F319の71件がbuild-variants root内に存在し、S4がthird-party source rootもjob-local化し、ignored bytesとoracle/build rootの一致まで検査すること。

### [real] D136 は durable v2 cache の依存 bytes と job identity を完全には束縛していない

- 根拠: D136はv2 preimage/manifestへのadmission束縛を定める (`docs/decisions.md:6616-6628`) 一方、未閉鎖層を明示的に残している (`docs/decisions.md:6650-6654`)。v2 identityはdependency prefixのpath列を入れるだけ (`buildcache.py:750-770,1043-1066,1312-1347`) で、hit時はmanifest・toolchain・binary hashを検証する (`buildcache.py:918-1005`) が依存source bytesのhashではない。
- 成果物影響: 同一pathの依存headers/libsを跨ジョブで差し替えてもcache hitし得るため、D136だけを理由に新しい計測値へ追加のprovenance creditを与えられない。S4だけでもF319のsource cache問題は閉じない。
- 反証条件: dependency/toolchainのimmutable manifestとfull digestをv2 preimage、completion manifest、WAL/proof chain、現在bytesの全てへ束縛すること。

### [real] `/scr` fresh cacheはcold buildを強制し、現行walltime envelopeを圧迫する

- 根拠: floorは毎回 `out_root/s8b-build-cache`をcache rootにする (`s8b_floor_campaign.py:1953`, `s8b_floor_campaign.py:5113-5116`)。v2は既存entryならhit (`buildcache.py:1363-1385`)、なければconfigure/buildを実行する (`buildcache.py:1388-1431`)。floor予約は1 cellあたりbuild cap 900秒を要求する (`s8b_floor_campaign.py:250-259,844-881`)。
- 成果物影響: `/scr`移設でcache hitがmissへ変われば、計測時間、PBS walltime、reservation受理、成功するfloor measurement ID数が悪化し得る。静的検査では実時間の増分は確定できないが、S4のcold化コストは現行予算に直結する。
- 反証条件: fresh rootでの実測台帳が、全cellのbuild時間とfinalize reserveを含む既存reservation envelope内に収まること。

### [real] dispatch非計測とC12休眠から「Yは不要」と一般化するのは飛躍

- 根拠: `dispatch_compute.py:3-6,54-79` は現行TASKSがtests/provenanceだけだと示すが、これは現在のdispatcher集合であってwrapperの不可能性ではない。C12 evaluatorは登録済みで (`s8c_preregistration_evidence.py:578-620`)、`machine_checkable=False` の条件だけが `_evaluate_undefined`へ送られる (`s8c_preregistration_evidence.py:698-710`)。
- 成果物影響: 親は「現行dispatchに計測callerなし」「現行C12は受理不能」とは言えるが、「callerが存在し得ない」「Yの必要性が消滅した」とは言えない。現在のC12受理集合は空のままで、certified選択やproof chainは変わらない。
- 反証条件: tracked wrapperの全inventory、end-to-end成功IDの不在、C12の現行結果がundefinedであることを三つとも独立に確認すること。`machine_checkable`を変えた場合は新しいnegative controlと受理手続きも必要。

## scope 外の裁定パッケージ候補

- F319の恒久対応: T-1094/T-1128のsource/build root一致、T-1129のignored fileを含む新schema、T-1095の`config.h` compile closureとoracle receipt。根拠は `docs/worklog.md:2323-2373`、`docs/archive/worklog-phase3-0815-555.md:731-737`。S4へ混ぜず、floor・Silo・S5のproof chain所有者へ返す。
- 8c compute transport / campaign task: D122の解禁条件、D125(6)、D108(2)-(5)、T-276の所有を一括して人間裁定へ返す。新PBS wrapperで暗黙に開かない。
- reservation authority hardening: hostだけでなくscript hash、nonce authority、owner-only artifactの検証範囲を再裁定する。現行 `reservation.py:218-277` の残穴をT-330のcache namespace変更で隠さない。

## 総括

YはDW-G04の成功artifact/計測IDがなく、床値wrapperもloop sink callerではないためland不可。  
8cを起動するwrapperはD125(6)/T-276/T-236に衝突し、D108(1)だけはD122で失効済み。  
S4はF319のthird-party汚染を直さず、D136にも依存bytesの残穴とcold-buildのwalltimeリスクがある。