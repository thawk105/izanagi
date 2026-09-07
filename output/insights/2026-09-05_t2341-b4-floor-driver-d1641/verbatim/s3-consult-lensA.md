現状の brief / plan のまま本 wave を進めるのは不可です。D1641 への適合は欠測規則だけでは閉じず、P1 は DW-S04 に従って再裁定待ちへ戻す必要があります。

## blocker

### 所見 1 — P1 は DW-S04 に反する

- (a) [実測] D1641 は「sanctioned CLI が存在しないので別 wave で新設する」と決定していますが、実際には裁定前の 2026-09-02 に driver が存在していました。これは理由だけでなく、決定された実行行為「新設する」の前提も変える未見事実です。親の P1 はこれを自分で「差分適合」に読み替えています。
- (b) [実測] `s1-brief.md:8-15,67-68`、`refs/D1641.md:29-31`、`refs/D1453.md:3-8`。ユーザー提示の DW-S04 は、承認済み裁定に未見事実が出た場合、親が不採用や再解釈をせず、新事実を添えて再裁定待ちへ戻すよう要求しています。
- (c) [実測] 放置すると、成果物は「新設する」という裁定を「既存物を改修する」へ無裁定で置換した実行機構を参照し、床値以前に採用根拠の権威系列が変わります。
- (d) [実測] commit 1、配線 probe、S-C 実装の前に、新事実と後述の残存差を裁定 fragment 候補へ載せ、「既存 driver の差分適合で D1641 第4項を履行したものと扱うか」をユーザーへ戻してください。
- (e) [実測] 親 brief の **P1 = 却下**。

### 所見 2 — 「同一セッション」の意味が未決で、plan の B も実装仕様になっていない

- (a) [実測] 現物は candidate 1、candidate 2、reference をそれぞれ別 `PlannedSession`、別 `measure_point` 呼出しとして実行します。D1641 の「参照点は対ごとに同一セッション内で測る」と逐語では一致しません。
- (b) [実測] D1641 は `refs/D1641.md:16-17`。現物は `floor_pair_driver.py:4-6,239-249,1218-1253,1640-1774`。plan 自身も `s2-plan.md:271-275` で不一致を認めています。
- (c) [実測] 一つの共通 reference を使う現行式 `|c1/ref - c2/ref|` と、candidate ごとに別 reference を使う式 `|c1/ref1 - c2/ref2|` は一般に別の D になり、床値を直接変えます。
- (d) [実測] 「同一セッション」を、(A) 3 role を連続実行する一つの sample block の意味に訂正するか、(B) 二つの paired session と reference の個数・式を新たに定義するかを再裁定してください。plan の「一つの低水準 session 呼出しへ再設計」だけでは、候補2側の独立性と共通 reference の個数が決まりません。
- (e) [実測] **P4 と D1641 第3項第6行に対応。P4 採用前の blocker**。

### 所見 3 — n=59、5% 欠測許容、95/95 上限は同時には成立しない

- (a) [実測] D1641 は n=59 の標本最大値を 95パーセンタイルの信頼度95%上限としつつ、5%以下の欠測を許しています。残存標本数を補充しない plan では、その被覆信頼度は95%未満になります。
- (b) [実測] `refs/D1641.md:20-27,35-37`、`s2-plan.md:175-199`。標本最大値の被覆確率は m 個の独立標本なら `1 - 0.95^m` です。m=59 で約0.9515ですが、59件中2件欠測を許すと m=57、約0.9463です。
- (c) [実測] 許容による受理集合の拡大は「旧 policy が拒否した欠測率0%超5%以下の campaign も、残存標本最大値で床値生成へ進める」ことであり、その床値は全予定標本が得られた反実仮想の最大値より小さくなり得て、§5 の `difference <= floor` の tie 集合を縮めます。
- (d) [実測] `NOT_PROVEN` の追記だけでは「95/95上限とする」という裁定と両立しません。少なくとも、欠測後も各 stratum に59件残るよう予定数を増やす、n=59なら欠測0件とする、または被覆主張を下げる、のどれかを再裁定してください。
- (d) [実測] `dropped * 20 > planned` は分母を campaign 全体と決めた後の算術としては正しく、exact 5%を受理します。文言上の「campaign」は window 全 pair 合算を支持しますが、統計上限は `(window,pair)` ごとなので、欠測を一 pair に集中させられます。pair ごとの5%制限はより厳しい別規則であり、AI が無裁定で足してはいけません。
- (d) [実測] 旧 policy と新 policy の両受理も不可です。安全側の過剰棄却でも campaign の受理集合を変更するため、D1641 が固定した手続きを spec 起草者が選び直すことになります。D1638 の AI 委任はこの裁定済み policy に選択余地を戻しません。
- (e) [実測] **P3 = 採用**、ただし欠測と被覆の矛盾が解消されるまで **P4 = 却下**。

### 所見 4 — candidate throughput 0 を落とす現行経路は値依存除外である

- (a) [実測] plan は「有限正の検査は validity 判定なので値を小さくする除外ではない」としていますが、candidate throughput 0 は有限であり、正の reference に対する `gain=-1` を計算できます。これを欠測へ落とすと、大きな D を最大値から除けます。
- (b) [実測] `_measurement_complete` は全 role の throughput を `<= 0` で不完全にします (`floor_pair_driver.py:1562-1566`)。finalizer も同じ判定です (`:2005-2013`)。`compute_gain_difference` も candidate と reference を区別せず正数必須です (`:1283-1306`)。plan の判断は `s2-plan.md:32-36`。
- (c) [実測] candidate 0 を含む高い D の標本を落とせば標本最大値と床値が下がり、campaign と§5の方向付き判定の受理集合が変わります。
- (d) [実測] role-aware に、candidate の各 rep と median は有限非負、reference は有限正としてください。負値は欠測でなく artifact/protocol 不正として扱い、ゼロ candidate を保持する正負テストを追加してください。
- (e) [実測] **P4 と規律2に対応。P4 = 却下**。

### 所見 5 — finalizer は status を再導出せず、値を見た後の drop を受理できる

- (a) [実測] plan は `status != complete` だけで drop を確定すれば値非依存になるとしますが、window artifact の status は finalizer から見れば自己申告です。現行 validator は status が閉集合内かしか検査せず、probe・measurement・error との因果整合を再導出しません。
- (b) [実測] `_validate_window_artifact` の検査は metadata と status membership までです (`floor_pair_driver.py:1945-1983`)。既存 `test_mutation_07` は、完全測定後に `records[1]["status"]` だけを `measure_incomplete` へ書き換え、finalizer がそれを受理することを示します (`test_floor_pair_driver.py:1693-1712`)。plan はこの test を欠測受理の正例へ置換しようとしています (`s2-plan.md:113-126`)。
- (c) [実測] 観測済み D の大きい標本だけ status を書き換えて terminal count も合わせれば、その標本を最大値から外して低い床値を生成できます。
- (d) [実測] drop は status 文字列からではなく、exact schema の probe結果、測定完備性、attempt lifecycle から再導出してください。non-complete record の因果整合、同一 sample 内の not-run 順序、terminal count をすべて検査し、window artifact の発行時 hash を finalize 入力へ束縛してください。書換え test を正例へ転用してはいけません。
- (e) [実測] **P4 = 却下**。

### 所見 6 — P2 の site 述語は base / sort では成立せず、複数合格規則も全域でない

- (a) [実測] `site_projected_cfg` は trigger にだけ作られ、base と sort では常に `None` です。親の `status != not_measured` は null を安全に検査できず、plan の `status == measured` 修正も base / sort を必ず不合格にします。また「複数合格なら base」は、base 不合格で sort と trigger が合格した場合に不合格候補を選びます。
- (b) [実測] 親 P2 は `s1-brief.md:69-71`、plan 修正は `s2-plan.md:240-252`。現物は `p3_b4_wiring_probe.py:1727-1766`、base / sort が null であることを固定する test は `test_p3_b4_wiring_probe.py:1293-1303` です。
- (b) [実測] 一方、§5.1(ii) の本体である切替点、on の赤詳細、off の §8 項目1・2、identity 分離は `_CHECKS` と publish 前検査に含まれます (`p3_b4_wiring_probe.py:1640-1674,1699-1718,1769-1774,1973-1998`)。
- (c) [実測] 放置すると、base / sort を誤って除外するか、逆に null を「not_measuredではない」と読んで site 未証明の候補を受理し、§5 の対象 driver・軸が変わります。
- (d) [実測] probe evidence に全3 driver共通の resolver由来 `execution_site` と attestationを追加するか、compute dispatch receiptを別の束縛済み証拠として採ってください。全3件の判定後、合格集合から固定優先順 `base, sort, trigger` の最初を選び、0件なら値セルを変更しない規則にしてください。
- (e) [実測] **P2 = 条件付き**。

### 所見 7 — P4 は binary / 時間窓の不一致を通常欠測へ格下げし、環境不一致は逆に記録しない

- (a) [実測] plan は `binary_binding_failed` と `outside_window` を5%枠の dropped sampleとして続行します。これは現在の fail-closed を緩めます。一方、D1641 が明記する環境不一致は window開始前に例外となり、drop件数も成果物も残りません。
- (b) [実測] 現行は live環境を出力確保前に拒否します (`floor_pair_driver.py:1437-1453,1800-1809`)。binary と時間窓 status は `:1659-1696`、最初の非 complete 後に全 window を閉じる現行分岐は `:1834-1862`。plan の変更は `s2-plan.md:27-30,152-168`、D1641 の列挙は `refs/D1641.md:26-28` です。
- (c) [実測] 一時的な binary差替えや予定窓外の1標本を5%以下として受理できると、凍結 binary・時間窓に属さない campaignから床値を生成できます。環境不一致側では逆に要求された欠測参照が消えます。
- (d) [実測] probe競合・probe不確定・測定失敗・role-awareな非有限だけを通常の dropped sample としてください。source、plan、binary、window境界の不一致は campaign-level protocol/binding failureのまま維持してください。環境不一致は、全予定標本を不採用とするcreate-only refusal receiptを残すか、D1641の「標本として落とす」意味を再裁定してください。
- (e) [実測] **P4 = 却下**。

## must-fix

### 所見 8 — 「唯一の実差は欠測規則」は12行検算で成立しない

- (a) [実測] 親の主張 `s1-brief.md:16-22` は誤りです。plan は複数差を見つけていますが、行8を「一致」とし、JSONLを「JSON」と同視するなど、なお過大評価があります。
- (b) [実測] 12行の現物対応は次のとおりです。

|D1641行|静的検算|driver変更要否|
|---|---|---|
|1 対象driver・軸|[実測] schemaにfieldがなく、`protocol`もunknownとして拒否 (`floor_pair_driver.py:220-235,1105-1111`; test `:539-556`)|[実測] 明示束縛を求めるなら必要|
|2 site=gen_S|[実測] siteは表現でき、liveとexact比較 (`:602-618,1437-1453`)|[実測] frozen specをgen_Sに固定するなら不要|
|3 env_tag機械導出|[実測] resolver導出値とspecを照合 (`:1404-1453`)|[実測] 不要|
|4 校正済みPerfConfig|[実測] records、threads、workload、env、clockだけ照合し、extime、reps、ycsb_max_opeは自由入力 (`:685-705,994-1060`)|[実測] 全項目の出所束縛には必要|
|5 3 workload × contention|[実測] 任意cellsの閉包だけ検査し、§5集合との一致は見ない (`:708-725,932-960`)|[実測] spec外部validatorまたはschema拡張が必要|
|6 共通参照点・対照対|[実測] candidate byte identityは束縛するが3 roleは別session (`:728-767,1218-1253`)|[実測] 再裁定後に必要性を決定|
|7 probe→測定→probe→journal|[実測] 前後probeはあるが、s8b型の事前authorization journalはない (`:1697-1773,1836-1852`)|[実測] durable lifecycleには必要|
|8 n=59、2 campaign、24h|[実測] 任意のwindow数、sample_count、非重複だけを受理し、24h gapも強制しない (`:779-835`)|[実測] frozen spec validatorが必要|
|9 標本最大値|[実測] `sample_max/v1`に閉じる (`:847-880,1309-1340`)|[実測] 不要|
|10 全cell×2窓の最大|[実測] planned strata exact閉包と二段max (`:951-960,2105-2122`)|[実測] 行8が正しく凍結される条件で不要|
|11 JSON・命名5要素|[実測] rawはJSONLで、pathは任意relative path。protocol fieldもない (`:56-58,779-827,905-919`)|[実測] 必要|
|12 欠測等・upper≥1|[実測] upper非丸めは実装済みだが、欠測、環境、retryは不一致 (`:1997-2004,2158-2165`)|[実測] 必要|

- (c) [実測] 放置すると、選定と無関係のdriver・軸、別PerfConfig、短い窓や少数標本、命名不適合の成果物が同じsummary schemaで床値候補になり得ます。
- (d) [実測] S-Cだけを先行する場合でも「D1641完全適合」と記録せず、行1、4、6、7、8、11、12を測定開始前の必須追随面として閉じてください。
- (e) [実測] **P1、P4、および親の「唯一の差」主張に対応**。

### 所見 9 — `not_run` と予定外retryを区別するdurable記録がない

- (a) [実測] plan の `status=not_run_after_fail_closed`、`error=sample_dropped` だけでは、誰がどの失敗を根拠に飛ばしたか、attemptを開始したか、予定外retryがあったかを再構成できません。
- (b) [実測] floor-pair側はheader後、probeと測定が終わってからsession recordを一度だけ書きます (`floor_pair_driver.py:1813-1852`)。s8b側は測定前に `session-start` をfsyncし、attempt_id、kind、retry_ordinalを記録します (`s8b_floor_campaign.py:6011-6019,6213-6225,6346-6383`)。T2166一次資料も削除・改名後の再作成を防がないと明記しています。
- (c) [実測] crash後の再実行や出力削除後の追加attemptが記録外になると、予定数を超えて得た値から都合のよいcampaignだけを採る経路が残り、床値と参照集合が変わります。
- (d) [実測] sample単位の `sample-start`、role単位のattempt start/end、`attempt_kind=planned`、`retry_ordinal=null`、skipの原因session_idをdurableに記録してください。`not_run_sample_dropped` を独立statusにし、plan外attemptが1件でもあればそのsampleまたはcampaignを不採用にしてください。
- (e) [実測] **P4に対応**。

### 所見 10 — §5.1(i) のfreezeは親briefの短い記述だけでは不足する

- (a) [実測] 親の「対象driver item直後に§5.1.2」は、その位置にH4を置くと後続の§5.1 bulletsまで§5.1.2配下に入れます。また、対象driver行のconsumerは意味、evidence hash、選択規則を検査しません。
- (b) [実測] 現在の対象itemは `preregistration.md:171-191`、次のbulletは `:192`、§5.1.1の終端と§6は `:530-542`。section consumerは5.1.1だけをhash対象にします (`p3_b4_analysis_prereg_consumer.py:301-345,394-407`)。§5表consumerは非空・sentinelなしまでです (`p3_b4_admission_record.py:602-688`)。
- (b) [実測] driver-axis対は `base=silo-backoff-magnitude`、`sort=silo-writeset-sort`、`trigger=silo-backoff-trigger-gating` です (`p3_s4_loop.py:125`、`p3_s4_loop_sort.py:109`、`axis_trigger_gating.py:23`)。
- (b) [実測] `thawk105` はD1266の不変identityを満たし、AIはその名義で操作するというD1641とも整合します。既存の役割定義も `preregistration.md:174-176` にあります。AI名義へ置き換える必要はありません。
- (c) [実測] 証拠1件だけ、または意味未検査の自由文だけで値セルを埋めると、複数合格の選択を再計算できず、§5の参照が結果後選択を許します。
- (d) [実測] plan `s2-plan.md:223-267` の配置、3本のfull dispatch command、freeze commit祖先条件、全3 JSON・sidecar hash、合格集合内固定優先順を採用してください。ただし所見6のsite証拠不足は先に直してください。
- (e) [実測] **P2 = 条件付き**。

### 所見 11 — test / mutation計画は正負対を閉じていない

- (a) [実測] plan の追加3 functionでは、規律2の中心経路とcampaign単位の集計を守れません。とくに既存のstatus書換えtestを欠測受理の正例へ変える案は逆向きです。
- (b) [実測] 提案testは `s2-plan.md:111-128,201-217`。欠けているのは、candidateゼロ、statusとprobe因果不一致、2 window間のdrop率pooling、pair集中欠測、binary/outside-window fatal性、環境不一致receipt、not_runの原因session、plan外retryです。
- (c) [推測] これらの変異が生存すると、高D標本の選択的drop、別campaignへの分母希釈、binary不一致campaignの受理が緑のまま残り、床値または受理集合を変えます。
- (d) [実測] 少なくとも次を追加してください: 同一status/drop集合でthroughputだけ変えてもdrop集合不変のmetamorphic test、完全recordのstatus改変拒否、candidate 0保持、reference 0拒否、campaign別閾値、pair別count報告、fatal status継続禁止、予定外attempt拒否。既存 `test_mutation_07` は実際のrun経路で欠測を生成してください。
- (e) [実測] **P4、規律2 / 3に対応**。

### 所見 12 — regression不緩和はP4修正後にだけ示せる

- (a) [実測] 変更予定関数の外側には既存gateが残っていますが、P4のbinary/outside-window格下げが一つ明示的な緩和です。したがって現planのまま「一つも緩めない」とは言えません。
- (b) [実測] 現行の呼出し関係は次です。

```text
load_frozen_spec
  -> spec bytes sha256 + HEAD blob exact
  -> _bind_checkout_inputs
       -> calibration HEAD/hash
       -> build receipt + binary sha256
  -> source_commit == loaded HEAD

run_window
  -> _assert_plan_exact
  -> _assert_live_environment
  -> runtime HEAD == loaded HEAD == source_commit
  -> _ExclusiveWriter(O_CREAT|O_EXCL|O_APPEND|O_NOFOLLOW)
  -> _run_planned_session
       -> binary sha256 + trace symbol
       -> fixed COMPETING_PROBE_ARGV
       -> pre probe -> measure -> post probe

finalize_floor
  -> _assert_plan_exact
  -> _validate_window_artifact
  -> _status_from_records -> _derive_strata
  -> upper >= 1なら非丸め
  -> summary _ExclusiveWriter
```

- (b) [実測] 対応箇所は `floor_pair_driver.py:538-545,994-1060,1094-1150,1456-1484,1501-1515,1652-1697,1715,1794-1836,1899-1985,2126-2195` です。
- (c) [実測] binary不一致をdrop扱いへ変える一点だけでも、現在不採用のcampaignを5%以下なら受理するため、受理集合が広がります。
- (d) [実測] 上記call順を保持し、fatal statusを5%分母へ入れず、既存のcreate-only、HEAD三者束縛、live site、binary、probe argv、upper非丸めtestを変更せず緑にしてください。summary shape変更についてproduction consumer 0件は静的検索で確認できるため、`SPEC_SCHEMA`、`WINDOW_SCHEMA`、`SUMMARY_SCHEMA` のv2 bumpは妥当です。
- (e) [実測] **P4に対応**。

## nit

### 所見 13 — brief / plan の実測事実とアンカーに複数誤記がある

- (a) [実測] plan のtest数、親の一部アンカー、未記入行数、現在のHEAD/main同一性が不正確です。
- (b) [実測] source上の `def test_...` は51件で、親 `s1-brief.md:8-9` が正しく、plan `s2-plan.md:59` の42件が誤りです。
- (b) [実測] `_ExclusiveWriter` classは `floor_pair_driver.py:1456`で、`:1462`は`os.open`です。failed分岐は`:1834-1850`、`_DRIVER_MODULES`は`p3_b4_wiring_probe.py:70-74`、対象driver itemは`preregistration.md:171-191`です。plan `s2-plan.md:46-57` のアンカー訂正は正しいです。
- (b) [実測] 対象driver行を埋めた後も`未記入`を含むのは8 value cellで、n行は既に記入済みです (`preregistration.md:158-167`)。親 `s1-brief.md:31-33,43-44,61` の「他9行」は誤りですが、関門が閉じたままという結論は変わりません。
- (b) [実測] 全文sha256のpinは0件という親の限定は正しい一方、§5.1.1部分にはraw / semanticの2 pinがあります (`p3_b4_analysis_prereg_consumer.py:47-51,399-407`)。
- (b) [実測] 検査時点ではHEAD=`97ee3cd3a...`、local main=`103c32e30...`で同一ではありません。ただし両者間で本件3主要fileの差分は0件です。
- (c) [実測] 現時点で床値や§5参照は変わりませんが、実装担当が誤ったtest母数や行範囲を根拠にすると検査漏れを生みます。
- (d) [実測] brief / planの実測欄とアンカーだけを訂正してください。
- (e) [実測] **P1 / P2への直接変更なし**。

## 裁定パッケージ候補

- [実測] D1641第4項の未見事実: 既存driverを「新設済み」とみなし差分適合してよいか。
- [実測] 「参照点は同一セッション」のsession単位、reference個数、Dの式。
- [実測] n=59と5%欠測を両立させるため、95/95主張、予定標本数、欠測閾値のどれを変更するか。
- [実測] campaign全体5%を逐語採用するか、各 `(window,pair)` にも閾値を課すか。
- [実測] s8b floor campaignの「journal」を実module統合と読むか、同等のdurable authorization lifecycleで足りるか。

## S-C scope外だがrealな所見

- [実測] driver・軸と§5選定結果、PerfConfig全項目の出所をspecへ明示束縛する面がありません。
- [実測] 一つのwindow artifactが複数workload / threadsを含められる一方、D1641は成果物名へ単一のworkload / threadsを要求しています。per-cell成果物へ分割するか、命名規則を再定義する必要があります。
- [実測] raw window成果物はJSONLであり、D1641の「create-onlyのJSON」を逐語では満たしません。durable JSONL journalから最終create-only JSONを作る二層構成が一案です。
- [実測] exact 2 window、各pair n=59、24時間gap、全windowで同一cell集合を検査するfreeze validatorが必要です。

## 総括

- blocker: **7件**、must-fix: **5件**、nit: **1件**。
- (P1) **却下** — DW-S04に従いユーザー再裁定待ち。
- (P2) **条件付き** — 合格集合内固定優先順と全driver共通site証拠が必要。
- (P3) **採用** — 裁定済み欠測policyは1値だけを受理する。
- (P4) **却下** — 被覆矛盾、値依存drop、status偽造、fatal status格下げが残る。
- (P5) **採用** — gen_S generic dispatch、infra rc=16なら未完了停止で正しい。
- (P6) **採用** — slugとcreate-only path規則に整合する。
- 結論: **本 waveは再裁定まで進めず、§5記入・測定は行わない**。
- [実測] pytestは実走せず、指定どおり静的検査のみ実施。