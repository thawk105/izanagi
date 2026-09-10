## 裁定 1 の比較表と推奨

結論は **代案 b** である。これは handle 案を永久に却下する裁定ではなく、実 caller と起動層の配線が入る単位 C で必要なら採る、という変更単位の裁定である。pytest は未実行で、以下は tip `57154c1dd` の静的検査結果である。

| 選択肢 | (a) 及ぶ file / 関数 | (b) 受理集合 | (c) D1113 / D1530 | (d) 単位 C | (e) changed LOC 見積り |
|---|---|---|---|---|---|
| evidence-bound handle | launcher の [`_capture()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:429)、[`_launch_floor_attempt()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:548)、terminal 型群。registry の [`_AttemptState`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:164)、terminal API 群 [`record_attempt_terminal()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2313)、[`resume_attempt()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2475)。profile の terminal schema・理由集合・validator [`s8b_attempt_profile.py:445`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:445)。core の validator 契約 [`attempt_registry_core.py:199`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:199) と terminal producer [`attempt_registry_core.py:1890`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1890)。3 test file 全て | 現在の「v2 terminal 全拒否」から、issuer が発行し durable evidence と一致する terminal だけへ広がる。raw kwargs 案よりは狭い | issuer seal、attempt identity、classification receipt、evidence digest を検証できれば D1113 に最も近い。しかし今先行実装すると、production caller 0 の未接続面へ防壁を建てるため D1530 と不整合 | **先食いする。** handle を作るには launcher が raw facts を所有・正規化・永続化する必要がある | **1,100〜1,700 LOC**。digest だけでなく durable bytes、crash cut、resume、負例を含む。A2α の上限見積りが実績より約 72%低かったことを織込み |
| 代案 a: raw keyword-only 引数 | profile の projection/policy、registry の sealed API、launcher の terminal call、core replay validator、3 test file。主アンカーは上記と同じ | v2 terminal を開く点では handle と同じだが、任意 caller が整合する raw 値と sealed record を同時に作れるため handle より広い | D1113 の「理由を引数で受け取らない」に正面から弱い。raw 値の相互整合検査だけでは所有者を拘束できない。今実装すれば D1530 にも反する | **先食いする。** 現在の launcher には v2 marker、五軸 slot、rep sink、pre-probe の carrier がない | **800〜1,250 LOC**。durable replay を省けば短くなるが、その省略形は正しさゲートを満たさない |
| **代案 b: E1/E2 を C へ送る** | 単位 A では production/test とも変更 0。C で launcher、registry、profile、必要なら core と consumer test を同時変更 | 現時点では不変。v2 terminal は二層全拒否、E2 は空集合のまま。実 caller 接続時にだけ必要な範囲を広げる | D1113 の raw 値所有を実 caller で閉じられ、D1530 の「接続と権威束縛を同一単位」に一致 | **先食いしない** | 単位 A は **0 LOC**。C の既存 scope に対する増分は **900〜1,500 LOC**程度。caller 配線と同時に試験できるため、先行 handle より重複 test を減らせる |

handle 案を採るなら、現物に当てた最小の流れは次になる。

1. launcher が post-probe と launch failure を取得する [`589-599`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:589)。token open 後に measurement、throughputs、rep evidence を取得する [`614-628`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:614)。
2. launcher がこれらと verified mode / perf-preflight、classification receipt identity、sealed session bytes digest を canonical snapshot にし、handle を発行する。terminal builder が返す status / reason / primary value は handle の権威入力にしてはならない。
3. registry が sealed API で issuer seal、slot、attempt、classification receipt、session digestを検証し、raw factsから projection を再導出して自己申告値と比較する。
4. resume は現在読み直している classification claim/receipt [`2591-2647`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2591) と marker [`2648-2665`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2648) に加え、canonical raw-evidence bytes、sealed session bytesまたはその権威 path、両者の digest を読み直す必要がある。現在の `resume_attempt()` はこれを一切持たず、observation resume 時に `deferred_output_reader()` を読むだけである [`2885-2889`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2885)。

したがって「durable evidence digest を足す」だけでは不足する。digest の対象 bytes、create-only path、terminal rowとの結合、crash cutごとの再取得規則が必要である。現在の core validator は `Callable[[row], None]` で [`1326-1327`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1326)、外部 evidence を読めない。terminal rowへ digest fieldを足すか、adapter replayで決定的な side artifactを検証するかも未決である。

さらに、現在の launcher は v2 を起動できない。reservation の `slot_id` は四軸型で [`s8b_floor_attempt_launcher.py:53-70`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:53)、v2 は五軸である [`s8b_attempt_profile.py:155-164`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:155)。reservation は marker を持たず `_reserve()` も渡していない [`444-469`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:444) 一方、registry は v2 marker を必須にする [`1703-1708`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1703)。これは handle 先行案を単位 A に置けない直接根拠である。

`record_sealed_classified_failure_terminal()` は、単位 C が新しい非 observation 終了経路を導入しない限り **落とす**のがよい。現 launcher は `ClassifiedFailure` も observation handleへ進め [`533-545`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:533)、共通の `record_attempt_terminal()` だけを呼ぶ [`633-644`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:633)。別 API の production caller を名指しできない。

## 裁定 1 で代案 b を選んだ場合の帰結

単位 A に残る **実装作業は 0** になる。現物では次が明確な引継ぎ点になる。

- profile 層の v2 replay 拒否 [`s8b_attempt_profile.py:556-563`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:556)。
- adapter 入口の v2 legacy terminal 拒否 [`s8b_attempt_registry.py:2305-2325`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2305)。
- E2 の空集合 [`s8b_attempt_profile.py:525-534`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:525)。空集合は retryable terminal を null matrix で全拒否する [`attempt_registry_core.py:959-970`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:959)。
- 空集合と二層拒否を pin する tests [`test_attempt_registry_core_s8b_profile.py:2185-2206`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2185)、[`test_s8b_attempt_registry.py:3096-3105`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3096)。

B2 / D1 の非 terminal 部分は予定順で着手でき、全面的な並べ替えは不要である。ただし、次は C の契約確定前に完了扱いできない。

- exact v2 terminal rowを読む consumer。
- durable terminal evidenceとの結合を検証する consumer。
- E2 の4理由を正例として要求する test。
- retryable terminalから後続の measurement authorityまでを閉じる E2E。

現在の v2 terminal key集合には evidence digestがなく [`s8b_attempt_profile.py:445-462`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:445)、replay validatorもrowしか受けない。このままB2/D1が exact readerを固定すると、Cで row fieldを追加する案では必ず手戻りになる。したがって順序は「B2/D1を全面停止」ではなく、**C-facing terminal evidence contractを先に短く固定し、terminal依存部分だけC後へ送る**のがよい。A2β の「次は無条件に B2 / D1」という記述にはこの条件が不足している。

## 裁定 2 の推奨

| 論点 | 裁定時期 | 推奨 |
|---|---|---|
| `expected_use_perf` | **意味規則は今決める。実装はC** | v2を単一modeへ限定せず、validated modeとnormalized perf-preflight receiptから機械導出する。booleanをcaller引数の権威にしない |
| `probe_outcome` | **coverageとschemaは今決める。実装はC** | `probe_before` と nullable `probe_after` の exact pairにする。計測前probe sessionもv2台帳対象に含める |
| `repetition_evidence` sink | **単位Cへ送る** | launcherがprivate listを作ってcaptureへ渡し、token open後にsnapshotする。callerからの `rep_observations` 指定は引き続き拒否する |

`expected_use_perf` は既存コードで mode と perf-preflight receiptから導出される [`s8b_floor_campaign.py:433-453`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:433)。rep evidenceの `complete` / `not_required` もこの値で変わる [`s8b_floor_campaign.py:1891-1968`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:1891)。一方 `s8b_approved.py` には単独の `use_perf` pinがない [`41-58`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_approved.py:41)。したがって単一mode化は既存の権威鎖を捨てる余計な受理縮小であり、verified evidenceへの束縛が適切である。

probe pairは「あるべき設計」だけではなく現物に対応する。計測前競合は `probe_after=None` のsessionを実際に生成する [`s8b_floor_campaign.py:6077-6090`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:6077)。計測後probeは別経路で実行される [`6103-6163`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:6103)。journal schemaにも両fieldがある [`s8b_ratified_freeze.py:262-269`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_ratified_freeze.py:262)。単一 `probe_outcome` では両者を区別できず、計測前session除外は「全attemptを台帳化する」coverageに穴を作る。

`repetition_evidence` は現在到達不能である。launcherのallowlistに `rep_observations` はなく [`s8b_floor_attempt_launcher.py:32-46`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:32)、`_capture()`もprivate sinkを作らない。testは明示指定を拒否する [`test_s8b_floor_attempt_launcher.py:600-645`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:600)。一方、下層captureはlistが与えられた場合だけopened resultへrep evidenceを載せる [`runner.py:938-1049`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/calibrator/runner.py:938)。よってCでlauncher-owned listを作る明確な到達化経路があるが、それが入るまでvalidatorをactiveにしてはならない。これはDW-O13の直接適用である。

後で壊れうるschema/validatorは、個別booleanやprobe fieldそのものより、**terminal rowとdurable raw evidenceをどう結ぶか**である。現在のrow-only validator契約では外部 evidenceを再検証できない。B2/D1が exact schemaを固定する前に、少なくとも次をC briefで固定すべきである。

- versioned terminal-evidence documentのexact field集合。
- mode / perf-preflight、probe pair、throughputs、execution failures、rep evidence、sealed record digestのcanonical化。
- terminal rowにdigestを追加するか、slot identityから決まるside artifactをadapter replayで検査するか。
- crash後にどのbytesを権威として読み直すか。

## 裁定 3 の推奨

**今は囲まない**を推奨する。A2α の「束縛側と非束縛側をexact pinし、非束縛集合を明記する」を維持する。

現物の差は明確である。

- 素の [`_atomic_update()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1508) はprelock snapshot後にroot lockを取り、registryを更新するがmarkerを再検証しない。
- [`_atomic_update_with_consumption_marker()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1532) は同じlock内で `marker.use()` を呼び、generation claim、attempt/campaign/manifest/run/cell、slot各軸を再検証してから更新する [`1553-1579`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1553)。
- v2予約はmarker経路 [`1770-1797`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1770)、observation-startもmarker経路 [`2203-2237`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2203)。
- classification claim/rowは素の経路 [`2075-2082`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2075)、recovery rowも素の経路 [`2466-2472`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2466)。

囲むと、validなissued handleがあっても、予約後にmarker、measurement-generation claim、main ledger identityが変化・消失した形をclassification/recovery時に追加拒否する。したがってv2受理集合は狭まる。

囲まなくてもv1より広くはならない。v2の `ReservedAttempt` はmarker必須の予約を通らないと発行されず、後続APIはexact type、process-local seal、state fingerprintを検証する [`s8b_attempt_registry.py:258-316`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:258)。v1はmarkerなしの予約と素の更新を受理する [`1733-1737`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1733)。つまりv2はmutation瞬間の再検証が弱いだけで、公開経路全体の入口はv1より狭い。

囲む実装をv2 schema分岐に限定すれば、既存v1経路は原理上壊れない。ただし現在のexact test [`test_v2_mutation_marker_binding_scope_is_exact()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:2953) は、予約/観測だけがmarker、分類/回復がplainであることを明示的に要求しており、必ず更新が要る。分岐せず全世代をmarker経路へ送れば、marker自体がcurrent-generation専用なので [`s8b_holdout_admission.py:303-309`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_holdout_admission.py:303)、v1を全拒否する。

現時点では、marker-bound reservationから得たhandleを迂回するproduction経路も、classification/recovery時の再検証不足が正式受理へ届く実経路も示されていない。production caller接続前に追加権威束縛を置くより、単位Cで独立resume/recovery経路が生じた場合に再裁定するのがD1530とD1533に整合する。

## 前 wave の推奨の根拠の裏付け状況

| 項目 | 判定 | 現物による確認 |
|---|---|---|
| 固定8 signatureではraw factsをsealed APIへ運べない | **裏付けあり** | registry handleが保持するterminal関連情報はclassification receiptとraw-output digestまで [`s8b_attempt_registry.py:164-185`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:164)。現terminal callはbuilderのstatus/valueをそのまま渡す [`s8b_floor_attempt_launcher.py:628-644`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:628) |
| handleをA2βで先行するのが最善 | **根拠不足、現物とは不整合** | durable evidence artifact、terminalとのdigest結合、resume再読込が実装にもsignatureにもない。さらにlauncherはv2 marker/五軸slot未対応で、production callerも定義外にはtest 1件しかない [`launch_floor_attempt():648`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:648)。D1530によりC同時実装が妥当 |
| raw kwargsはD1113から遠い | **裏付けあり** | 現terminal builderがstatus/primary valueを自由に返せる [`test_s8b_floor_attempt_launcher.py:296-315`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:296)。raw値も同じcallerから受ければ、相互に整合する偽入力を選べる |
| `expected_use_perf` は既存2定数だけでは決まらない | **裏付けあり** | mode/perf-preflightから実行時導出 [`s8b_floor_campaign.py:433-453`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:433)。rep integrityもその値で変化 [`1891-1968`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:1891) |
| probeを前後の組にする | **裏付けあり** | pre-probe competingとpost-probe competingは別到達経路で、session schemaも両fieldを持つ [`s8b_floor_campaign.py:6077-6163`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:6077)、[`s8b_ratified_freeze.py:262-269`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_ratified_freeze.py:262) |
| repetition evidenceは現在到達不能 | **裏付けあり** | launcher allowlistと `_capture()` にsinkがなく、testが明示指定を拒否する [`s8b_floor_attempt_launcher.py:408-441`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:408)、[`test_s8b_floor_attempt_launcher.py:600-645`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:600) |
| 分類/回復をmarkerで囲まなくてもv1より広くない | **裏付けあり** | v2予約はmarker必須で、後続はissued handle必須。exact経路はtestでもpin済み [`test_s8b_attempt_registry.py:2953-2997`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:2953) |
| `record_sealed_classified_failure_terminal()` のcaller 0を根拠に将来APIを残す | **根拠不足** | 新API自体が未実装なのでcaller 0は自明。既存analogにはtest callerがある [`test_s8b_attempt_registry.py:702-718`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:702) 一方、production launcherはfailureも共通observation/terminal経路へ送る。現物からは削除側が強い |

A2α の「生の事実が揃うのはtoken open後」は全体として正しいが、厳密にはpost-probeとlaunch failuresはopen前 [`589-599`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:589)、measurement/throughputsだけがopen後 [`614-627`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:614)である。この時系列差はdurable snapshotのcrash cut設計に影響する。

## 総括

裁定1: **代案 b**。E1/E2を実caller接続と同じ単位Cへ送り、handleを採る場合もC内で実装する。  
裁定2: `expected_use_perf` はverified mode/perf-preflight束縛、probeは前後pairを今固定し、rep sink実装はCへ送る。  
裁定3: **今は囲まない**。予約・観測だけmarker-boundというexact pinと非束縛集合の明記を維持する。  

親の裁定前に確かめるべき現物の事実:

- C briefが、terminal evidenceのdurable bytes、digest結合、resume再読込を具体的に名指ししているか。
- `record_sealed_classified_failure_terminal()` のproduction callerを示せない場合、API削除が明記されているか。
- B2/D1のterminal依存部分が、Cで確定するexact evidence schemaを先に凍結していないか。