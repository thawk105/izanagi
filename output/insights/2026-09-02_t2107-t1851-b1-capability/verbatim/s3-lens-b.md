## 検査制約

単独段 dispatch の射影制約により、指定4資料だけを読み、repository の code 本体や test collection は再読していない。そのため以下はすべて `[推測]` とし、file:line は射影資料が示す code anchor である。pytest も実行していない。

## B-1 — pre-probe failure と必須 marker が両立しない

主張: `begin_classified_failure_observation()` に consumption marker を必須化すると、ticket を consume しない pre-probe 競合を terminalize できない。

[推測] B1 は failure API にも marker を必須とする一方、土台の unit C は pre-probe 競合時に admission ticket を consume せず、reserve -> classify -> failure terminal と進める。`s2-plan.md:131-147`, `s2-plan-v2.md:93-103`

具体的な壊れ方: pre-probe では marker が存在しないため、正当な `competing_process` が必須引数不足または capability 検査で停止する。pre-probe 専用 capabilityまたは別 transition APIが必要である。

深刻度: `blocker`

## B-2 — 通常 launcher が即座に壊れる

主張: adapter の public API を必須 keyword 付きへ変えながら launcher を変更しない計画は、既存 production caller を確実に取り残す。

[推測] plan 自身が launcher は one-argument API を呼ぶと認め、B1 では launcher と fallback の双方を変更しないとしている。`s2-plan.md:130-153,254-260`, code anchor `orchestrator/campaign/s8b_floor_attempt_launcher.py:533-545,628-645`

具体的な壊れ方: launcher が `begin_attempt_observation()` または failure 版を呼ぶと、registry transition 前に missing keyword の `TypeError` になる。unlanded であっても B1 checkpoint は production-callable でも suite-clean でもない。最小 launcher bridge を B1 に移すか、adapter signature の変更を C まで遅らせる必要がある。

深刻度: `blocker`

## B-3 — legacy v1 の受理形を明示的に削っている

主張: capability-only 化は brief の「legacy v1 validator を残し、受理形を減らさない」という不変条件に反する。

[推測] brief は legacy 受理形の維持を要求するが、plan は「legacy marker のみ、claim・主台帳なし」を受理から拒否へ変更し、raw fallback も拒否する。`brief.md:29-38`, `s2-plan.md:159-167,225-227,247`

具体的な壊れ方: 現在有効な legacy cut-6 evidence が admission capability を発行できず拒否される。legacy raw validator を admission-owned API として残すのか、受理縮小を新裁定に上げるのかを先に決める必要がある。

深刻度: `blocker`

## B-4 — T-2107 の「機械導出」はまだ証明されていない

主張: code を読んで policy document を手で組み立てる案は、既存純関数からの機械導出ではなく手動の意味複製である。

[推測] plan は reason、probe、例外、regex、precedence、`reps`、閾値を policy document に列挙するとするが、実装ラダーがその document を実行する設計も、同一の宣言データから両者を生成する設計も示していない。既存 scheduler authority も選択した module 定数を文書化する先例であって、parser や実行規則との同値性を保証する先例ではない。`s2-plan.md:32-54`, code anchors `s8b_scheduler_accounting.py:65-102`, `s8b_floor_campaign.py:6077-6163`

具体的な壊れ方: 将来 precedence、捕捉例外、regex、rep integrity 条件だけを変更しても authority digest が旧値のまま残り、「旧 policy を名乗って新規則で分類する」状態を作れる。分類を宣言テーブル駆動にし、その同じ object から canonical bytes を作るまでは D1380 の分岐を閉じられない。`rulings-verbatim.md:140-148`

深刻度: `blocker`

## B-5 — crash recovery で capability を再取得する caller がない

主張: process-local で非直列化の capability を observed resume で必須にする一方、その再発行を担う caller が scope にない。

[推測] plan は crash 後に admission token から capability を再発行するとするが、`resume_attempt()` へそれを渡す launcher/recovery wiring は C として除外されている。`s2-plan.md:64-68,86-88,149-153,260`

具体的な壊れ方: process restart 後、durable `observation-start` がある正当な試行でも capability が存在せず、resume が fail-closed する。inspector reconstruction -> marker validation -> `resume_attempt()` の具体的な production caller を scope と署名に加える必要がある。

深刻度: `blocker`

## B-6 — adapter assertion の引数 provenance が未定義である

主張: 9個の identity 引数を adapter のどの state field から取るかが定義されておらず、`claim_digest` の意味も曖昧である。

[推測] assertion は root、claim digest、attempt、campaign、manifest、run、cell、holdout、configuration を要求するが、`ClassifiedAttempt`、`ClassifiedFailure`、内部 state からの対応表がない。current の measurement-generation claim digest、legacy の cell-effect digest、registry classification claim digest は別 domain である。`s2-plan.md:87-108,128-150`

具体的な壊れ方: 実装者が registry claim digest を admission claim digest として渡すと全 current capability が拒否される。逆に比較項目を省けば cross-generation capability が通る。署名ごとの「引数 -> 権威 field」表が必要である。

深刻度: `real`

## B-7 — consumer と赤テストの列挙が少なくとも launcher 分だけ不足する

主張: 「直接14、transitive 7」は registry test file 内の集計であり、production caller と launcher test を含む repo-wide 集計ではない。

[推測] 前 wave は launcher test caller を public 1件、private 5件としているが、B1 plan の赤一覧と編集面には `test_s8b_floor_attempt_launcher.py` がない。`s2-plan-v2.md:25`, `s2-plan.md:173-209,252-260`

具体的な壊れ方: registry tests を21件更新しても、launcher 経由の最大6 call siteが旧一引数呼出しのまま赤になる。`s8b_floor_campaign.py` から launcher を経由する integration family も同様に波及しうる。

深刻度: `real`

## B-8 — dataclass の全数調査としては検索軸が不足する

主張: 型名、constructor、`asdict`、`astuple` の検索だけでは equality、hash、pickle、opaque container 利用を除外できない。

[推測] brief と plan は constructor 2箇所、位置引数0件、token digestなしとするが、`hash(token)`、`token in set`、dict key、opaque list comparison、`pickle.dumps(value)`、`repr` snapshot、`dataclasses.fields()` は型名を参照しない。`brief.md:64-68`, `s2-plan.md:66-70`

具体的な壊れ方: field 追加で hash/equality/repr/pickle state が変わり、見落とした cache key、fixture snapshot、旧 pickle の復元が壊れる。少なくとも `replace(`、`pickle`、`hash(`、set/dict membership、equality、repr、reflection の参照調査が必要である。

深刻度: `real`

## B-9 — current-generation 正例は既存 fixture だけでは書けない

主張: 現行 fixture は historical v1/v2 専用なので、そのままでは plan の current marker 正例を構築できない。

[推測] plan 自身がこの制約を認め、production reservation/finalize/consume を使う別 helper の追加を提案している。`s2-plan.md:195-209,215-232,258`

具体的な壊れ方: author が既存 `build_floor_admission_evidence()` を流用すると legacy marker しか得られず、「current capability 正例」が実際には path dispatch を通らない。別 helper の追加は B1 scope に明記されているため、追加する限り blocker ではない。

深刻度: `real`

## B-10 — test node 数は parametrize 展開を数えていない

主張: test 計画の18行は18 nodeではなく、既存21 nodeの更新に多数の parameter nodeが加わる。

[推測] marker shape は5方向、marker identity は約10方向、main row は3方向、capability 移植は3方向、resume 負例は3方向を要求している。`s2-plan.md:213-232`

具体的な壊れ方: review と mutation 実行量を18新規 node程度と見積もると、parameterごとの fixture生成、失敗帰属、実行時間を大きく過小評価する。既存更新を含む executable node は概ね45-65になる。

深刻度: `real`

## B-11 — M4、M6、M7、M9 は単一理由性が成立していない

主張: 変異候補4件は前後の gate と重複するか、複数変異を一つにまとめている。

[推測] `s2-plan.md:241-249` に対して次の問題がある。

- M4: claim と主台帳の generation ID を同期改竄すると claim digest、marker path、token-state digest も変わり、generation ID 再導出より前に拒否されうる。
- M6: exact keys と全 identity を既に個別検査するなら、最後の dict equality を削っても拒否理由が残り、変異が生存しうる。
- M7: exact-type 削除と seal 削除は別変異であり、一方を残せば同じ forged input を拒否できる。
- M9: root と generation digest の削除も別変異で、cross-root fixture が他 identity まで変えると帰属できない。

具体的な壊れ方: kill test が別 gate で赤になるか、対象 gate を消しても緑のままになる。M4 は identity helper の component test、M6 は他検査を全て通る単一 field 差、M7/M9 は一変異一入力へ分割すべきである。M1、M2、M3、M5、M8、M10-M13 には射影資料内で明確な反証材料なし。

深刻度: `real`

## B-12 — B1 は前 wave の単位B見積もり内に収まらない

主張: adapter と fixture 移管後の B1 は約550-850 changed LOC、45-65 executable nodeと見積もるのが妥当である。

[推測] 前 wave の単位B 450-700 LOC、25-45 nodeは prefix replay と coverage を含む一方、adapter は単位Aに置いていた。今回のB1は2 production module、fixture、2 test module、21既存node更新と多数の新規parameterをまとめている。`s2-plan-v2.md:310-316`, `s2-plan.md:173-259`

具体的な壊れ方: 現在の blocker を抱えたまま一 wave で実装・review・mutation verificationを行うと、red checkpointの原因切分けまで同じ wave に混入する。設計修正後でも大型一 waveであり、現状のままは収まらない。

深刻度: `real`

## B-13 — 「pin 閉包0件」は検索語から一般化できない

主張: schema定数名と directory literal の hit が少ないことは、byte pin が0件である証明にならない。

[推測] 親の検索は定数名と `measurement-generation-consumed` を軸にしている。`brief.md:69-73`

具体的な壊れ方: 次の pin はその検索から漏れる。

- schema値を文字列で直書きした fixture
- exact key tupleを独立複製した validator
- canonical bytesの SHA-256 だけを保存した manifest/golden
- generated JSON、binary fixture、圧縮 snapshot
- generic serializerやrepr snapshot
- imported alias、reflection、factory経由の参照

そのいずれかがあれば field/schema変更後に golden mismatch または historical verification failureになる。「0件」ではなく「指定語による可視 pin は0件」と限定すべきである。

深刻度: `real`

## B-14 — DW-O10 不成立には限定付きで反証材料なし

主張: marker、claim、ledger の production writer bytesを変更しないという狭い意味では、DW-O10 不成立を反証する材料はない。

[推測] plan は既存 canonical buildersとwriter bytesを変更せず、read-side validatorとprocess-local objectだけを追加するとしている。`brief.md:31-35,73`, `s2-plan.md:3-4,110-124`

具体的な壊れ方: ただし dataclass repr、error surface、public API return objectまで「出力」に含めて族全体へ一般化すると未検査である。DW-O10 の対象を durable producer bytesに限定して記録しないと、後に「一切の observable output は不変」と誤読される。

深刻度: `nit`

## B-15 — T-2107 が B1 実装を前提にする証拠はない

主張: 分類 policy の導出可能性調査そのものが B1 capability を必要とするという反証材料はない。

[推測] T-2107 が読むのは campaign の分類ラダー、stats、approved pin、scheduler authority の先例であり、B1 の marker validatorやdataclass fieldを入力にしていない。`s2-plan.md:6-54`, `brief.md:75-96`

具体的な壊れ方: 順序問題は「T-2107 が B1 を必要とする」ことではなく、B-4のとおり T-2107 の機械導出判定が未完成なのに D1380 を閉じた扱いにすることである。

深刻度: `nit`

## B-16 — constructor 2箇所という主張には射影内の反証材料なし

主張: `CellHoldoutAdmission` の直接 constructor が2箇所という plan の主張を覆す資料内証拠はない。

[推測] fresh/resume 共通 issuer と inspector reconstruction の2箇所が列挙され、いずれも keyword construction とされている。`s2-plan.md:64-69`, code anchors `s8b_holdout_admission.py:1793-1819,6227-6253`

具体的な壊れ方: この数が誤っていれば defaultなし field追加時に見落とした constructor が `TypeError` になる。ただし B-8の opaque利用と pickle/hash 調査は別途必要である。

深刻度: `nit`

## B-17 — scope 外だが成果物の実効性に必要な層が残る

主張: B1だけでは保証は発火せず、少なくとも5層を後続裁定パッケージとして明示する必要がある。

[推測] brief はA、B2、C、Dをscope外にし、planも launcher、contract、stats、freeze を変更しない。`brief.md:14-15`, `s2-plan.md:252-267`

具体的な壊れ方: 次が未実装のまま残る。

- normal launcher が current capability を取得して adapter へ渡す層
- pre-probe failure を markerなしで正当に terminalizeする権限層
- crash recovery が admission tokenと capabilityを再取得する層
- unit A の世代別 registry/claim namespace
- B2/D の全単射 coverage、prefix proof、consumer verification
- unit C の分類規則と authority documentを同一 source of truthへ束縛する層

裁定候補は、最小 launcher/recovery bridgeをB1へ移すか、adapter破壊変更をCまで延期するか、legacy raw受理を維持するか、pre-probe専用 capabilityを新設するか、authority ruleを宣言データ駆動へ変えるか、の5件である。

深刻度: `real`

## 総括

blocker は5件である。

特に、failure APIとpre-probeの不整合、launcherの必須引数取り残し、legacy受理形の無裁定な削除、T-2107の機械導出未証明、crash recovery caller欠落は、実装後に直ちに停止するか保証が発火しない問題である。

この plan はこのまま実装子へ渡せない。少なくとも5 blockerを解消し、consumer source map、legacy受理方針、pre-probe権限、authority digest追随機構、更新対象testの全数を plan に反映してから再レビューが必要である。