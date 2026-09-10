## 所見

### 公開 fixture 正例は現プランのままでは `P6Unavailable` へ到達不能

- 重大度: blocker
- 根拠: `/home/SFC/tanab/.claude/jobs/68d5cbca/tmp/t2437/s2-plan.md:293-300,331-338,505-510`; `orchestrator/campaign/p3_autonomous_workload_trial.py:461-470,4807-4812`; `orchestrator/campaign/reflux_formal_consumer.py:912-982,1055-1061`; `orchestrator/tests/test_reflux_formal_consumer.py:249-316`
- 影響: formal consumer は FC03 または FC06、record 自体が足りなければ FC01 で拒否し、formal receipt、terminal projection、台帳 terminal は得られない。
- 反証可能な主張: public CLI の fresh `run_root` から標準 drive を1回実行しても、active query 以外の32 physical campaign root、各 `campaign.lock`、source、projection、provenanceは作られない。consumer は exact 33件を要求するため `P6Unavailable` には到達しない。

既存 consumer test は helper が33 root全部を明示生成して初めて成立する。プランは `result_record_bytes` の32 companion recordを残すが、その参照先を fresh rootへ物理配置する入力または処理を追加していない。

さらに fixture ledger の evidence digest は実行前に確定済みだが、新 record は `secrets.token_hex(16)` の attempt ID、`os.urandom(32)` の trigger nonce、`time.time()` の WAL timestampを含む (`pipeline.py:1694`; `trigger_gate_binding.py:167-169`; `wal.py:1585-1592`)。consumer は ledger digestに一致するrecordをexact 1件要求する (`reflux_formal_consumer.py:664-670`)。通常のpublic CLIには未来のbytesを固定する注入面がなく、プラン記載の「future digestへ合わせた固定fixture」はtest seamなしでは成立しない。

### identity-error と既存 terminal skip は issuer を迂回する

- 重大度: must-fix
- 根拠: `orchestrator/campaign/loop.py:489-543,544-550,655-667`; `/home/SFC/tanab/.claude/jobs/68d5cbca/tmp/t2437/s2-plan.md:240-263`
- 影響: terminal abortまたは既存terminalを持つのにrecord無しのまま、`run_campaign()` が通常の `CampaignSummary` を返す。
- 反証可能な主張: origin context付きone-genome runで `source_digest.resolve_evidence()` に `RuntimeError` を発生させると、`build_start` と `identity-error` abortを書いた後 `continue` するため、プランのline 655相当のissue callへ到達しない。

同じく、issue直前のcrash後に再度同じlayoutを開くとterminal variantは `done` に入り、line 545-549でskipされる。プランの「per-result terminal直後」という挿入点はこの2経路を覆っていない。

### issue失敗は下位campaignでは閉じるが、公開wrapperの例外処理が壊れる

- 重大度: must-fix
- 根拠: `orchestrator/campaign/p3_autonomous_workload_trial.py:3611-3650,3788-3789,5226-5256,5282-5337`; `/home/SFC/tanab/.claude/jobs/68d5cbca/tmp/t2437/s2-plan.md:25,243-263,331-338`
- 影響: false successやcertified選択は生じないが、`run_origin_trial()` が契約どおり `OriginPartialTrialReport` を返さず `AttributeError` を送出し、reportと台帳処理が中途半端になる。
- 反証可能な主張: issueで `FileExistsError` 等を起こすと、`_finish_trial()` はdrive例外をsupervisor errorへ変換した後 `_complete_origin_runtime()` を呼び、zero issued pathで再度例外になる。外側の `except BaseException` はlifecycle tokenがある場合その例外を再送出せず関数を `None` で終了し、続く `report.get(...)` が失敗する。

A3のconsumer判定自体はfail-closedである。record無しのnon-tombstone memberはFC04/FC07/FC09より前、`_pair_records()` のFC01で拒否される (`reflux_formal_consumer.py:664-670`)。自動でledger tombstoneへ移す経路は本プランにない。

### `site=OTHER` では execution receipt 条件が恒偽

- 重大度: must-fix
- 根拠: `orchestrator/campaign/loop.py:180-193`; `orchestrator/campaign/env_contract.py:291-311`; `orchestrator/campaign/p3_autonomous_workload_trial.py:2955-2976`; `/home/SFC/tanab/.claude/jobs/68d5cbca/tmp/t2437/s2-plan.md:197-207,425-434`
- 影響: acceptedでもrejectedでもrecordは発行拒否となり、public fixture modeはPegasus computeまたはtest注入に事実上限定される。
- 反証可能な主張: `site_policy.OTHER` は有効なbuild siteで、`linux-baremetal` contractの `attestation_mode` は `none` だが、`_authorize_measurement()` はmodeが `required` の場合しかreceiptを作らない。したがって計画された「actual execution receipt必須」は常に満たせない。

OTHERを意図的な負例にするなら、公開CLIと成果物の名乗りに「Pegasus compute限定」を明記する必要がある。

### A1: sourceはlive WALではなくimmutable prefix snapshotを選ぶべき

- 重大度: nit
- 根拠: `orchestrator/campaign/wal.py:1184-1188,1266-1276,1326-1344,1486-1559`; `orchestrator/campaign/loop.py:484-692`; `orchestrator/campaign/reflux_result_evidence.py:978-1001,1107-1129`
- 影響: live `runs/wal.jsonl` を参照すると後続appendだけでsource refのwhole-file SHA-256が壊れ、FC05B相当の参照解決失敗になる。prefix copyなら受理集合は動かない。
- 反証可能な主張: terminal後に別genomeを同じcampaignへ1件追加すると、WALは `O_APPEND` で伸び、元の区間bytesは不変でもfile全体digestは変わる。

したがって二択ではプランのprefix copyが正しい。ただし「source WAL」ではなく「terminal時点のimmutable source-WAL prefix snapshot」と名乗るべきである。consumerはsource pathがliteral `runs/wal.jsonl` であることを要求せず、physical root内配置と区間bytes一致だけを要求する。

## 親 brief の誤り

1. 「production authorityが空だからproductionで発火しない」は理由が不足している。現HEADのauthorityは実際に71 bytes、`origins: []` だが、`issue_origin_binding_capability()` は `store_scope=="production"` を無条件拒否する (`reflux_origin_binding.py:600-603`)。またproduction runtime初期化も拒否される (`reflux_origin_ledger.py:2914-2918`)。repo内に正規のproduction発火pathはなく、authorityへentryを足すだけでも発火しない。

2. 成果物を「production issuer」と呼ぶのは設計§9の名乗り上限と衝突する。正直な名称は「production-code issuer wiring、fixture-origin authorityでのみ到達実証」である。brief本文の限定 (`brief-t2437.md:45-46`) は正しいが、表題と研究前進の表現は強すぎる。

3. `brief-t2437.md:85-86` のzero-pin測定は列挙した4 fileについては正しかったが、wave全体へ一般化できない。実際の必須編集面 `p3_s4_loop_trigger_gating.py` のSHA-256は `1c6a55d...be7fd1` で、次のtracked artifact 3件にexact出現する。

   - `output/insights/2026-08-27_t1769-b4-wiring-probe/t2341-eligibility/base.json:1`
   - 同 `sort.json:1`
   - 同 `trigger.json:1`

4. record pathをphysical `<campaign_root>` 配下とした `brief-t2437.md:92,101-102` は誤り。recordはouter evidence rootに残り、physical Layer3 reportへ入るのは3 content artifactだけである (`reflux_result_evidence.py:818-827`; `test_reflux_formal_consumer.py:249-316`)。

5. `brief-t2437.md:21` のcampaign末尾をissuer最終化点とする記述は複数genomeでは遅すぎ、`brief-t2437.md:54-55` と両立しない。per-attempt位置はplanのline 655相当で正しいが、前述のidentity/skip分岐を追加で閉じる必要がある。

6. 15-file集合は実在するが、「issuer pathのsource closure」と一般化してはならない。これはhard-coded AST scan集合であり (`test_reflux_formal_consumer.py:2285-2309`)、`pipeline.py`、`loop.py`、`p3_s4_loop_trigger_gating.py` は含まれない。

再測定で正しかった値:

- producer core API 3関数の非test callerはゼロ。
- `run_origin_trial()` の非test callerはゼロ。
- `ordered-wal-projection` のproduction出現は既存validator 2件だけ。
- `execution-provenance/v2` のproduction出現は既存validator 1件だけ。
- briefが列挙した4 file自身の現在のSHA-256/git blob exact pinはゼロ。

## プランの誤り

- blocker: public fixture E2E正例に必要な残り32 physical rootとfuture ledger digestを作る経路がない。
- must-fix: issue挿入点がidentity-errorとterminal skipを覆わない。
- must-fix: issuer例外を受ける既存supervisor/wrapperの広い `except` が、partial resultではなく `None` と後続 `AttributeError` を生む。
- must-fix: validな `site=OTHER` ではexecution receiptが必ず `None` になり、issuance条件が恒偽。
- nit: live WALではなくprefix copyを選ぶ判断は正しいが、artifact名称をsnapshotと明示すべき。

以下は反例なし。

- A2: acceptedで `verify_result=None` とすることは穴ではない。全pass/repetition成功は `verification_capabilities` とreceiptを全件束ねてからCOMMITされる (`pipeline.py:2368-2381`; `wal.py:1295-1320`)。任意の1件のtyped値を残す方が全pass成功を誤縮約する。
- production形のrejected abortは死んでいない。local non-serializableではterminal payloadが `{reason, build_attempt_id, build_admission_receipt_sha256, verify, workload}` となり、`verify` はWAL作成時とderive時の双方で同じ `result_to_dict()` から `trace_dir` を除く (`pipeline.py:649-665,1851-1866`; `reflux_result_evidence.py:571-608`)。cleanかつ1 witnessならcanonical bytes一致は成立しうる。
- remote fan-outからtyped `VerifyResult` を再構成する計画はない。wire payloadだけが残り、rejected issuanceはexact type検査で拒否される。
- 複数repetition/passの選択順は一意である。localはrepetition順、pass順で最初のabortを即returnし、fan-outはlocal rep 0を先に、remoteをrep昇順で処理する (`pipeline.py:2111-2120,2228-2253,2320-2367`)。
- formal consumer関数自体は編集対象でなく、数学的な受理集合は変わらない。

## 裁定パッケージ候補 (scope 外の real な所見)

### 33件topologyをこのwaveへ含めるか

- 推奨: 本waveの完了条件を「active queryのrecord発行とcore consumer parity」に狭め、public `P6Unavailable` 到達を主張しない。
- 代案: 33 physical campaign/material、ledger batch producer、future digest問題を同じwaveへ含める。
- 影響: 前者なら成果物名はfixtureでのissuer到達まで。後者は設計§12/Jの要件9-18とledger topologyへscope拡張が必要。

### terminal後のissuer失敗をtombstoneへ接続するか

- 現状: terminal WALと部分content artifactが残り、recordはなく、consumerはFC01。自動tombstone suffixはない。
- 選択肢: issuer失敗をorigin producerがtombstone suffixへ接続するか、trial全体をindeterminateのまま不可逆終了とするか。
- これはcrash recoveryとledger producer topologyに関わるため、本wave内で暗黙実装すべきではない。

### `attestation_mode=none` のreceipt契約

- `site=OTHER` を明示拒否してPegasus compute限定にするか、mode noneでも発行できる認証済みexecution receiptを定義するかの裁定が必要。
- 自己申告digestで埋める案は規律3に反する。

## 総括

最大の問題は、プランが「1件のissuer配線」と「33件すべてを要求するformal consumer到達」を同じ正例としている点である。後者はscope外としたledger/physical topologyなしには成立しない。

下位のissuer、rejected typed値、WAL prefix snapshotは正しさ境界を緩めていない。一方、identity-errorのissue迂回と公開wrapperの例外処理は実装前に修正が必要である。静的検査のみで、pytestは実行していない。