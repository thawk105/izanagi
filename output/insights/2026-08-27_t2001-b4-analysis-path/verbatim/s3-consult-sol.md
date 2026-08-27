## 前提の確認

次の射影資料を全文読めた。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s1-brief.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s2-plan.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-prereg-b4.md`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-decisions.md`

repo は read-only で静的確認した。Web、pytest、build、書込みは行っていない。浮動小数点境界の確認に標準ライブラリだけの短い算術 probe を実行したが、テスト緑とは扱わない。

## 所見

### F1. 凍結文面と「11理由」は両立しない

- **重大度:** blocker
- **対象:** `ref-prereg-b4.md:274-291`、`s1-brief.md:60-64`、`s2-plan.md:191`
- **根拠:** 凍結文面の識別子は、`block_count_mismatch` から `field_missing_or_ill_typed` まで数えると12個ある。`duplicate_block_id` と `unknown_block_id` は別名・別意味なので1種には数えられない。brief と plan は「11種」と固定している。さらに凍結文面は `ref-prereg-b4.md:200` で入力を4つ列挙した後、同:267で「入力は上の3つだけ」と書いている。
- **成果物影響:** 11種で実装すると、重複 ID、未知 ID、または受け皿のいずれかが統合され、レポートの invalid reason と protocol violation の参照が凍結文面から変わる。
- **反証されうる形:** `duplicate_block_id` と `unknown_block_id` が同一 enum member の別表記である、または凍結文面を12種へ訂正する裁定が既に存在するなら誤り。ただし射影資料にはない。

### F2. manifest・registry hash の内部照合は4入力の純関数では不可能

- **重大度:** blocker
- **対象:** `ref-prereg-b4.md:200-210`、`s2-plan.md:612-623`
- **根拠:** `contract_binding` が持つのは凍結側の期待 hash だけで、観測側 manifest/registry bytes または hash は他の3入力にも存在しない。それでも凍結文面は「観測側と exact 一致」「一致検査を関数の外へ出さない」と要求する。plan は統合 path の手順3で外部照合してから `evaluate_analysis()` を呼ぶため、逐語的に逆である。
- **成果物影響:** 外部照合を省けば差し替え manifest/registry が certified 選択へ流れ、外部照合を残せばレポートが「凍結純関数の機械適用」とは言えない。
- **反証されうる形:** `contract_binding` が独立した期待値と観測値の両方を持つ、または純関数へ観測 artifact bytes/hash を追加することが凍結済みなら誤り。現文面はどちらも定めていない。

### F3. tie 境界は `as_integer_ratio()` では守れない

- **重大度:** blocker
- **対象:** `s2-plan.md:153-159`
- **根拠:** plan は保存済み浮動小数点を `as_integer_ratio()` で Fraction 化する。しかしこれは丸め前の十進値ではなく、丸め後の IEEE-754 値を exact にするだけである。`on_tps=1.1`、`off_tps=1.0`、`reference_tps=1.0`、`floor=0.1` は十進契約では境界 tie だが、変換後は利得差が floor より `3 / 36028797018963968` 大きくなり、on 勝ちになる。
- **成果物影響:** 境界 block の `X` が `1/2` から `1` に変わり、`A_hat`、tie 数、`m`、p 値、最終 verdict が変わる。
- **反証されうる形:** raw artifact が十進 lexical bytes を float 化せず Fraction へ変換する、または契約上の数値を IEEE-754 の格納値そのものと定義するなら誤り。plan はどちらも固定していない。

### F4. 80回の外向き二分法は Clopper-Pearson 区間そのものではない

- **重大度:** must-fix
- **対象:** `s2-plan.md:179-187`
- **根拠:** plan は幅 `2^-80` の有理数 bracket を作り、外側の端を報告値にする。例えば `m=2, W=0` の上端は `1 - sqrt(1/40)` であり有理数ではない。外向き有理数端点はこの根より大きく、Clopper-Pearson の端点そのものではなく保守的包囲である。`m=0` の `[0,1]` と `W=0` の下端、`W=m` の上端は正しい。
- **成果物影響:** verdict は変わらないが、レポートの `theta` 区間端点が凍結文面の値と異なる。
- **反証されうる形:** `ThetaInterval` が端点ではなく根の隔離区間を保持し、レポートも「CP 根の包囲」と明記するか、凍結契約が数値包囲を許すなら誤り。

### F5. scheduled registry の全件性検査が自己申告入力との循環になっている

- **重大度:** blocker
- **対象:** `s2-plan.md:486-490,538-556,697`
- **根拠:** `assert_scheduled_registry_complete()` は呼出側の `scheduled_inputs` と registry を比較するだけである。都合の悪い予定 attempt を両方から落とせば整合したまま通る。plan 自身も権威ある scheduled attempt 全列の producer が不在と認める。manifest の再生成は、欠落済み registry の内側しか検査できない。
- **成果物影響:** 不利な campaign を台帳・manifest・レポートの母集合から同時に消せるため、certified 選択の受理集合が事後に狭められる。
- **反証されうる形:** `scheduled_inputs` が、実走前に独立して固定された launcher の完全 schedule receipt からのみ導出され、その receipt の全件性も別 gate で証明されるなら誤り。該当 producer は scope 外かつ不在である。

### F6. HMAC schedule は凍結された無作為化要求をそのまま証明しない

- **重大度:** blocker
- **対象:** `s2-plan.md:558-569,759`
- **根拠:** 凍結文面は block ごとに独立、各順序を確率ちょうど `1/2` で実走前に抽出することを要求する。単一 seed と HMAC の1 bitは、PRF 仮定下の擬似無作為化であり、数学的な独立 Bernoulli 抽出の証明ではない。さらに seed の一様性、初回抽出、事前性を証明する producer/receipt verifier がなく、plan も明記している。
- **成果物影響:** seed や schedule を選び直せると二項帰無分布の根拠が失われ、レポートの `p_on`、`p_off` と certified 判定が無効になる。
- **反証されうる形:** 201個の独立 fair bit を一度だけ事前抽出する権威ある producer と、その固定 receipt を検証する gate が追加されるなら誤り。

### F7. raw adapter の失敗が全域 verdict へ写らない

- **重大度:** must-fix
- **対象:** `s2-plan.md:250-259,289-299,602-621`
- **根拠:** `parse_raw_analysis_records()` の戻り型には `AnalysisInvalid` がなく、「adapter error」は例外扱いのままである。`evaluate_b4_artifacts()` も `AnalysisResult` だけを返し、parser/loader例外を `field_missing_or_ill_typed` または protocol violation へ写す手順がない。拒否自体は fail-closed でも、全件報告の全域関数ではない。
- **成果物影響:** malformed・欠落 raw record が protocol violation 行として台帳とレポートへ残らず、分析処理の失敗として消える。
- **反証されうる形:** 全 loader/parser error を理由 enum へ変換し、必ず結果 artifact を生成する上位 path が実装されるなら誤り。

### F8. 一致 consumer は enum の意味まで固定していない

- **重大度:** must-fix
- **対象:** `s2-plan.md:370-405,411-423`
- **根拠:** consumer が抽出するのは主に enum 名、定数、文中 literal である。AST 検査も定数が source literal かを見るだけで、その定数を検証・判定が実際に使うことを保証しない。plan 自身も hidden constant/別演算経路を防げないと認める。12個の invalid reason と5個の registry reasonについて、各意味に対応する独立な発火 fixture は列挙されていない。
- **成果物影響:** 名前だけ正しい実装が違う入力を invalid/violation と数え、台帳件数、レポート理由、受理集合を変えても一致 consumer が通る。
- **反証されうる形:** 全理由について単独発火する fixture と、対応する判定箇所の mutation kill が追加されるなら誤り。

### F9. 段6の変異帰属が成立しない gate が複数ある

- **重大度:** must-fix
- **対象:** `s2-plan.md:524-535,556,569,581-590,631-645`
- **根拠:** 次は同じ変異を複数層が同時に拒否する。
  - manifest の追加・削除・並べ替えは row tuple 比較と canonical bytes 比較の両方で赤になる。片方を無効化しても帰属できない。実効 gate はどちらか一方で足りる。
  - schedule 書換えは frozen bytes 比較と seed からの再生成比較の両方で赤になる。
  - assignment 違反は `assignment_schedule_violated` の registry count と block の `assignment_followed=False` の両方で同じ protocol branchを発火する。
- **成果物影響:** 変異結果が「当該 gate を閉じた」証拠にならず、片方が将来外れて受理集合が広がっても検査緑を維持できる。
- **反証されうる形:** 各 gate について他の拒否理由を無効にした単独 fixtureと、固有の拒否 signatureを検査するなら誤り。

### F10. 実成果物から certified 選択へ届く production path はこの plan にない

- **重大度:** blocker
- **対象:** `s1-brief.md:52-56,128-138`、`s2-plan.md:691-707,711-717`
- **根拠:** plan は production caller、sanctioned CLI、結果 artifact writer、§7.1 report generator、certified 選択 gateの更新を一つも置かず、直接 consumer は新規テストだけである。加えて raw field、reference resolver、schedule producer、seed receipt、正式 manifest bytes がすべて不在で、plan 自身が「正式実走 pathにはならない」と結論している。したがって brief の「4経路を実在させる」「文面だけの実走経路を閉じる」は成立しない。
- **成果物影響:** このwaveをlandしても、実際のcertified選択、レポート、台帳の値・受理集合・参照は1 bitも変わらない。
- **反証されうる形:** 既存 launcher/report/certification consumer が新 `evaluate_b4_artifacts()` を必須呼出しする実在経路が示されれば誤り。静的走査では存在しない。

なお、plan の `Fraction + math.comb` による `A_hat` と二項裾、`m=0` の p 値、片側 `1/40` 比較、`A_min` 非閾値化、順位3段、verdict順序は凍結文面と一致している。符号検定について浮動小数点反転例を追加する必要はない。

## 親 brief への所見

### PB1. 実測1・2の「0件」は文字どおりには偽

- **重大度:** nit
- **対象:** `s1-brief.md:20-28`
- **根拠:** `design_not_feasible` は `orchestrator/preregistration/stress_check_simulation.py` と関連 test/JSON に多数存在する。`analysis_invalid` は別設計文書にもあり、`treatment_fired` 等も凍結 doc と tracked insights に存在する。「B-4 production producer が0件」なら概ね正しいが、「repo/Python/JSON全体で0件」ではない。別名束縛や文字列合成もこのgrepでは否定できない。
- **成果物影響:** 直接の受理集合変更はないため nit。ただし既存語義や汎用核を無視した重複実装判断の根拠には使えない。
- **反証されうる形:** 測定母集合を「B-4 production moduleのみ」と明示していたなら誤り。briefにはその限定がない。

### PB2. `observe_relative()` の不流用結論は正しいが「片側」は不正確

- **重大度:** nit
- **対象:** `s1-brief.md:23-28,110-113`、`orchestrator/qualification/contract.py:332-353`
- **根拠:** 実装は上側・下側の乗法境界を持ち、`direction` は3分類するため単なる片側関数ではない。ただし `bit=0` が tie と reference優位を畳み、`floor=0` も拒否し、共通 reference に対する2利得差ではない。直接流用不能というP4の結論は維持できる。
- **成果物影響:** 誤って流用すると tie/off上位とfloor=0の受理が変わる。今回のplanは流用していないため現時点の影響はない。
- **反証されうる形:** B-4専用の追加情報と変換で凍結関数と全域同値になる合成が示されれば誤り。

### PB3. 実測4は正しい。§5を埋めた後の危険も実在する

- **重大度:** must-fix
- **対象:** `s1-brief.md:34-37`、`orchestrator/campaign/p3_b4_admission_record.py:536-624`
- **根拠:** checker は固定表形、10ラベル、非空、予約 sentinel、model/prompt/projectionの3値を検査するが、primary outcomeセルのpath、hash、型、意味、実在は見ない。このwave後にprimary outcomeセルへ任意の非sentinel文字列を書けば、そのセル自体は通る。全セルが同様に埋まれば、§6.9が実在しなくてもadmission gateは開きうる。
- **成果物影響:** 実在しない分析path/hashを参照した版で実走が受理され、certified選択とレポートが未検査集計に戻る。
- **反証されうる形:** §6.9を意味検査する別の必須gateがlauncher直前に存在すれば誤り。現repoとplanにはない。

### PB4. 実測3・5・6は確認できた

- **重大度:** nit
- **対象:** `s1-brief.md:29-45`
- **根拠:** whiteboardの3値域と`delta_pct=None`、prereg docのliving登録、B-4 whole-file pin不在、既存CP片側float実装、attempt registry汎用核はコードどおりである。
- **成果物影響:** 反証所見なしのため nit。既存CPはB-4の両側95%へそのまま流用できず、汎用registry coreもevent意味が違う。
- **反証されうる形:** 別のwhole-file pinまたはB-4専用profileが間接生成される経路が示されれば再確認を要する。

### PB5. 実測7はfile名の非重複だけなら正しいが、interfaceは重なる

- **重大度:** must-fix
- **対象:** `s1-brief.md:46-50,87,98-105`
- **根拠:** t1769のproduction/test pathとplanの新規pathは重ならない。t1840も現在このbaseより先のcommitは0件である。一方、t1840のlauncher/run pathは、planがproducer不在とした`execution_disposition`、slot順、raw receiptの自然なownerであり、P2のschemaと意味上重なる。file素集合だけではschema ownershipを分離できない。
- **成果物影響:** launcherが別schemaを生成するとadapterの実受理集合が空になり、台帳・レポートが生成されない。
- **反証されうる形:** t1840との間でraw schema、producer責任、receipt hashを固定した共有契約が既にあるなら誤り。

### PB6. P1とP4は維持、P2は「部品」に限定、P3は部分成立

- **重大度:** blocker
- **対象:** `s1-brief.md:92-113`
- **根拠:**
  - P1: 維持。F10のとおり実走可能pathがまだ無いため、primary outcomeセルを埋める条件を満たさない。
  - P2: fail-closedなschema部品の宣言までは可能だが、到達不能producerを残したまま「adapter経路が実在」「§6.9充足」とは扱えない。
  - P3: docから実装を生成しない方向は正しい。ただしF8のとおり定数・名前の独立性だけで意味一致にならない。
  - P4: 維持。ただし代替実装もF3のfloat境界を直す必要がある。
- **成果物影響:** P2をそのままclosure認定すると、実成果物を1件も受理できないのに§5参照だけが埋まり、certified選択とレポートの関門が空洞化する。
- **反証されうる形:** producer、統合caller、report writer、certification gateまで同じ発効単位で実在するならP2への反証は消える。

## 裁定パッケージ候補

1. **凍結文面の自己矛盾修正**
   - `analysis_invalid` は12名か11名か。
   - 「入力は上の3つ」を「4つ」へ直すか。
   - 観測manifest/registry hashを純関数の第5入力にするか、block列へ束縛するか、外部照合を正式に許すか。
   - 推奨: 実装前に同一裁定で3点を修正し、現文面のまま作者へ解釈させない。

2. **schedule・registry権威のowner**
   - t1840 launcherが全scheduled attempt、seed初回抽出、slot順、raw execution dispositionをdurable receiptとして生成するか、専用waveへ分けるか。
   - 推奨: launcher側を権威producerとし、本waveのgeneratorはそのreceiptを検証するconsumerに限定する。

3. **数値表現とCP報告形式**
   - TPS/floorを十進文字列から有理数へ読むか、IEEE-754値を契約値とするか。
   - CP端点を数値近似、外向き包囲、代数根の隔離区間のどれで報告するか。
   - 推奨: canonical decimal文字列からFractionへ変換し、CPは根の隔離区間として型に残して表示精度と外向き丸めを明記する。

4. **成果物へ効かせる後続層**
   - 権威あるreference resolver。
   - `treatment_fired`、`contaminated`、`protocol_ok`、実行slot順のproducer。
   - sanctioned analysis entrypoint、immutable result artifact、§7.1全件report writer。
   - report/registry completeness consumerとcertified選択の必須gate。
   - §5セルへpath/hashを書き、admission checkerがその実在とhashを検証する更新。
   - 推奨: これらを別waveとして明示し、本wave単体は「部品実装済み・正式path未実走・§6.9未充足」と記録する。

## 総括

- 独立所見の blocker は6件。最重はF2の「凍結文面が要求するhash内部照合を、凍結された4入力では実装できない」である。
- enumは「11種」ではなく文面上12名あり、実装前の裁定が必要である。
- tie境界はfloatを後からFraction化しても守れず、具体的に`1.1 - 1.0`対`0.1`で反転する。
- registry全件性と割当無作為化には権威producerがなく、file-drawerと二項帰無分布を閉じていない。
- plan自身が正式実走pathへ到達不能と認めており、certified選択・レポート・台帳へのproduction効果は現状0である。
- pytest/buildは実行しておらず、緑とは報告しない。