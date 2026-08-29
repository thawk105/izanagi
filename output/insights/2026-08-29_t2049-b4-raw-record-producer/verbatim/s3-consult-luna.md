## 重大な所見

### 1. campaign root が registry の block／precursor に束縛されない

- **所見:** registry から `initial_proposal_sha256` を転記するだけで、指定された campaign root がその attempt から生じたことは証明されず、P1-b は閉じない。
- **場所:** `s2-plan.md:71-78, 408-412`、`orchestrator/campaign/p3_b4_analysis_ledgers.py:123-143`、`orchestrator/campaign/p3_b4_launcher.py:392-399`
- **なぜ欠陥か:** `B4ArmArtifactRequest` は caller 宣言の `block_id` と `campaign_root` を受けるが、lock、launch sidecar、critic receipt のいずれも `attempt_id`、`block_id`、`initial_proposal_sha256` を持たない。したがって block X の有効な on/off campaign を block Y として append し、producer が Y の registry 値を `precursor_hash` として転記できる。adapter は両 arm の転記値が一致することしか見ないため通る。
- **成果物への影響:** outcome を異なる `reference_tps` の block へ差し替えられ、block score、`A_hat`、最終 verdict が変わる。
- **real / 要確認:** real

### 2. 既存 pre-run publication の result-path 束縛を無視し、別の一回性台帳を新設している

- **所見:** 任意の `record_root` に `arms/<ordinal>-slot-<n>.json` を排他作成する設計は、既存 result-path commitment の再利用ではなく、新しい append-only／at-most-once 台帳である。
- **場所:** `s2-plan.md:110-124, 364-385, 513`、`orchestrator/campaign/p3_b4_prerun_issuer.py:1-16, 335-403, 444-464`
- **なぜ欠陥か:** 既存 issuer は `attempt_id -> result_artifact_path` の完全な写像を事前 receipt に固定する。一方 producer API は issuer receipt も `planned_result_artifacts` も受けず、caller が事後に選んだ別 root へ slot 群を作れる。slot の空きが一回性状態となり、`SLOT_CONFLICT` が消費済み判定を担う。既存 WAL、advisory campaign lock、prerun receipt のどれもこの新状態機械を支配しない。
- **成果物への影響:** 同じ registry から複数の raw 集合を別 root に作って都合のよい集合だけを選べるため、受理集合と報告対象に file-drawer が残る。
- **real / 要確認:** real

### 3. publish 順は実行 slot の観測にならない

- **所見:** arm artifact の publish 順を execution slot とするため、並行実行、完了順の逆転、収集遅延で assignment 観測が偽になる。
- **場所:** `s2-plan.md:325-330, 379-380, 416-420`
- **なぜ欠陥か:** schedule が on-first でも、on の実行開始後に off が先に完了して append されれば raw は off-first になる。逆に、実行は off-firstでも caller が結果を on、off の順に回収すれば schedule 遵守として記録される。T-2051 が順序を保証するという前提も本 wave では接続されない。
- **成果物への影響:** 正しい実走が protocol violation になり、また違反実走が遵守扱いになって、verdict 分岐と報告が逆転する。
- **real / 要確認:** real

### 4. stable snapshot と terminality を取り違え、実行途中を不可逆な missing として封印できる

- **所見:** WAL/checkpoint の前後一致は「読み取り中に変わらなかった」ことしか示さず、campaign 終了を示さない。
- **場所:** `s2-plan.md:334-344, 379-385`、`orchestrator/campaign/lock.py:67-89`
- **なぜ欠陥か:** producer が `build_done` と `verify_done` の間に走れば、二回読みは一致しても terminal suffix は無い。plan はこれを `terminal-record-absent` として immutable publish できる。その直後に COMMIT しても同 arm の再追記は `SLOT_CONFLICT` になる。また newline 完結済み frame の直後に process が crash した場合も、plan の規則では `crash` でなく `terminal-record-absent` になる。既存 advisory campaign lock の取得も計画に無い。
- **成果物への影響:** certified/rejected outcome が missing に固定され、block score、treatment 件数、全件報告の停止分類が変わる。
- **real / 要確認:** real

### 5. post-link の durability 不明状態から再開できず、後続 assembly の受理も非決定的である

- **所見:** target を残したまま `durability_unknown` を返し、同 arm の再追記を拒否する規則は再開不能である。
- **場所:** `s2-plan.md:379, 381-385, 495-497`
- **なぜ欠陥か:** file fsync と link の後、最初の directory fsync が失敗すると target は見えるが成功は返らない。再試行は同 arm conflict になる一方、assembly は visible target の canonical bytes だけを見て採用しうる。実 crash 後に directory entry が消えた場合だけ結果が変わる。既存 consumption writer は不完了時に target を削除する (`p3_s4_loop.py:1358-1363`) ため、plan が「再利用」と呼ぶ機構とも失敗意味論が異なる。
- **成果物への影響:** 同じ実走でも storage の残存状態次第で 402 件が完成したり永久に詰まったりし、raw の受理集合が変わる。
- **real / 要確認:** real

### 6. `treatment_fired=true` の根拠が「その decision で次を合成した」を証明しない

- **所見:** receipt の生成・検証・消費だけで `treatment_fired` を真にするため、既知の proposal hash 書き写し経路を treatment 発火として数える。
- **場所:** `s2-plan.md:389-404`、`verbatim-prereg-7.md:33-35`、`orchestrator/campaign/p3_s4_loop.py:1530-1538`
- **なぜ欠陥か:** valid receipt hash を legacy critic 由来 proposal に書き写しても authorization と consumption は成立する。逐語資料自身が、閉じているのは closed critic の併存までであり、その decision で synthesis したことではないと明記している。plan の列挙条件はこの開口を追加で閉じない。
- **成果物への影響:** treatment 未発火 block を発火済みとして n に算入し、本来の判定不能から成立／不成立へ進める。
- **real / 要確認:** real

### 7. `contaminated` の証拠源と verdict 分岐が誤っている

- **所見:** admitted WAL 不一致を contamination とし、valid receipt pair なら実際の off 汚染を偽とする設計は、事前登録の contamination と一致しない。
- **場所:** `s2-plan.md:332, 467-473`、`docs/phase3-b4-reflux-ablation-preregistration.md:114-120, 478-485`、`verbatim-d824.md:16-21`
- **なぜ欠陥か:** 事前登録の off 汚染は off 側が別経路で赤へ到達した場合である。`B4ArmPairComparison` の admitted-view／loop-state／iteration equality はその不在を証明しない。逆に admitted WAL 不一致は同一 precursor の pair でない protocol 条件の破壊であり、plan はこれを `contaminated=true` として protocol violation より弱い判定不能へ落とす。producer は registry の precursor を両 arm へ同じ値で転記するため、contract の precursor mismatch も発火しない。
- **成果物への影響:** protocol violation が判定不能へ弱まり、検出不能な off 汚染は clean block として verdict に入る。
- **real / 要確認:** real

### 8. arm ごとに別の receipt pair を選べる

- **所見:** 各 append が別々に valid pair を検証できる一方、最終 assembly は二つの source artifact が同じ pair を使ったことを要求していない。
- **場所:** `s2-plan.md:71-78, 243-253, 325-332, 395-403`
- **なぜ欠陥か:** on artifact を pair A、off artifact を pair B で作れば、各 append 内の `assert_b4_arm_pair` は通る。source schema には `pair_id` がなく、assembly 規則にも on の selected hash と off の peer hash、その逆の exact 交差一致が無い。各 source の protocol check が pass なら raw block は clean になる。
- **成果物への影響:** 複数 pair から都合のよい arm を組み合わせる receipt shopping が可能となり、block score と verdict が変わる。
- **real / 要確認:** real

### 9. producer の意味は凍結 pin に入らず、production verdict への接続も scope 外である

- **所見:** 新 producer は source artifact の意味を決める権威になるが、既存分析 path はその bytes を opaque hash としてしか検査せず、producer 自体も exact source closure に入らない。
- **場所:** `s2-plan.md:24-29, 503, 507-516`、`orchestrator/campaign/p3_b4_analysis_path.py:67-73, 174-196`、`orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:98-104, 751-754`
- **なぜ欠陥か:** 新 file 名や `_RAW_TERMINAL_STAGE` は既存の exact tuple／AST 内容走査には直接引っかからないことを確認した。しかし evaluator は source bytes を parse せず、raw が宣言した hash 列との一致だけを見る。この wave の test が producer bytes を evaluator に渡しても、production caller、certified selection、closure receipt との結線にはならない。

  raw から報告までの層は次のとおりである。

  | 層 | 現状 | 本 wave |
  |---|---|---|
  | registry／manifest／seed と planned result path | `p3_b4_prerun_issuer.py` に実在 | scope 外かつ producer が未消費 |
  | formal launcher、critic receipt、WAL、campaign lock | 実在 | 読取依存のみ |
  | arm source と raw durable writer | 未実装 | scope 内 |
  | adapter、ledger completeness、analysis path、pure contract | 実在 | 変更なし |
  | prereg consumer／analysis source closure receipt | 実在、5 file pin | producer は scope 外 |
  | producer を呼ぶ sanctioned command | 未接続 | T-2051 として scope 外 |
  | raw bytes を certified verdict 呼出しへ渡す接続 | 未接続 | scope 外 |
  | report generator／論文 cell | 未接続 | scope 外、T-2052 を含む |

  `s2-plan.md:451,503` の evaluator 到達は test 内だけであり、scope 外層を production 実装したことにはならない。
- **成果物への影響:** wave 完了後も producer 出力が certified verdict、report、論文 cell へ到達する経路は無く、改変 producer の出力を verdict から排除する根拠も無い。
- **real / 要確認:** real

### 10. test 設計に変異の一意帰属がなく、明示された唯一の全件正例は実機構を通らない

- **所見:** test 節は性質の列挙であり、実装の一行と単独 nodeid の対応表になっていない。
- **場所:** `s2-plan.md:440-503`
- **なぜ欠陥か:** 明示された 402 件の正例は全 arm が「campaign root 未到達」で、WAL、formal marker、launch sidecar、critic pair、consumption、commit receipt を通らない。したがって executed arm を一律拒否する分岐があっても、この全件正例は緑のままである。一方 `_RAW_TERMINAL_STAGE` の COMMIT 写像を壊せば classifier と実 campaign regression の複数 test、source byte 順を壊せば 402 assembly と既存 hash-order test の複数 test が落ちうる。さらに source schema を解釈する独立 consumer はなく、producer とその raw projection が同じ誤った意味で揃えば `evaluate_b4_artifacts` は opaque hash 一致だけで通る。
- **成果物への影響:** 変異 matrix の緑を producer の意味論保証と誤読でき、実 formal campaign を全拒否する実装や source／raw の共通誤写像が verdict 経路へ残る。
- **real / 要確認:** real

### 11. binary-float 負例の値が変異を発火させない

- **所見:** `491796.5` は binary float で正確に表せるため、float 経由変異を検出する負例にならない。
- **場所:** `s2-plan.md:479-481`、`output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:5`
- **なぜ欠陥か:** `.5` は二進有限小数であり、Python float 化と通常の JSON 再出力を経ても `491796.5` の token が維持される。この値だけで「binary float を経由した実装」を赤にすることはできない。
- **成果物への影響:** 十進境界を変える float 経由実装が test 緑のまま残り、source hash、floor 境界、throughput 比較を変えうる。
- **real / 要確認:** real

### 12. 時点を狙う負例に発火位置の識別がない

- **所見:** lock 差替えと二回の directory fsync fault は発火時点が重要だが、test 設計に呼出番号や同期点が固定されていない。
- **場所:** `s2-plan.md:459-461, 495-497`
- **なぜ欠陥か:** lock mutation が最初の読取前なら単なる不正 lock、producer 終了後なら無関係であり、「分類後かつ receipt 検証前」とは別の負例になる。directory fsync も link 後の第1回と temp unlink 後の第2回で可視 target と durability の意味が違う。単に `fsync` を失敗させる spy では、狙った時点でなくても「拒否された」という目的だけを満たせる。
- **成果物への影響:** D1240 の同一 snapshot や post-link crash semantics が壊れても、別時点の例外で test が緑になる。
- **real / 要確認:** real

## nit

### strict loader の引用範囲が途中で切れている

- **所見:** `p3_b4_closed_critic.py:1436-1588` は strict loader 全体のアンカーではない。
- **場所:** `s2-plan.md:148`
- **なぜ欠陥か:** 同関数は 1589 行以降も argv、実行 binary、role file、prompt、projection、envelope、decision の照合を続け、次の top-level function は 1798 行からである。
- **成果物への影響:** 直接の verdict 変更はないが、引用範囲だけでは plan が依存する receipt 検査全体を再確認できない。
- **real / 要確認:** real

### WAL writer の引用が表の全 field を支えない

- **所見:** `wal.py:640-669` は COMMIT receipt 埋込み箇所であり、ABORT reason や `fitness_tps` の生成 writer 全体ではない。
- **場所:** `s2-plan.md:151`
- **なぜ欠陥か:** この範囲は caller から渡された terminal payload を receipt と共に再構成するだけで、diff-quarantine の writer は `p3_s4_loop.py:389-394` にある。
- **成果物への影響:** 直接なし。ただし artifact field の出所監査を誤誘導する。
- **real / 要確認:** real

## 親 brief 自身の欠陥

### 実 campaign の WAL／checkpoint の前後関係を逆に読んでいる

- **所見:** 観測例は loop state が WAL より一世代先だが、brief はこれを「進んだ WAL と一世代古い loop state」の実物と記述している。
- **場所:** `s1-brief.md:76-82`
- **なぜ欠陥か:** 実 WAL は COMMIT 3 件、`loop_state.json` は iteration 4、whiteboard 4 件である。逐語 §7 の非保証は逆向きの「進んだ WAL と一世代古い loop state」を指す。この一例は二者の不一致可能性は示すが、逐語に書かれた向きの実例ではない。
- **成果物への影響:** producer の alignment 分岐を逆向きの実測根拠で正当化し、正しい実 artifact を missing／protocol failure に誤分類しうる。
- **real / 要確認:** real

### 「実アンカー表」の大半は実測値でなく静的仕様である

- **所見:** 1 本の legacy on campaign から観測できない field まで「実データ上の出所・実測済み」としている。
- **場所:** `s1-brief.md:53-72`
- **なぜ欠陥か:** この campaign から実測できるのは `reflux:"on"`、小文字 WAL stage、COMMIT の `fitness_tps`、whiteboard `success`、WAL 3 terminal 対 whiteboard 4 件、formal marker／sidecar／receipt が無いことまでである。次は実測していない。

  - registry／manifest の block、reference、assignment
  - off arm
  - ABORT と diff-quarantine の実例
  - critic receipt、`treatment_fired`
  - pair comparison、contamination、protocol flag
  - launch sidecar
  - source artifact とその hash
  - lock absence digest
  - missing／duplicate／dry-pass／crash の各 disposition
  - 3 driver や 201 block にわたる値域

  とりわけ `s1-brief.md:71-72` の「`b4_launch_context.json` の実在も実測」は、同じ campaign root にその file が無いという plan 自身の確認 (`s2-plan.md:11`) と矛盾する。
- **成果物への影響:** 未観測形式を production 値域として固定し、正式 B-4 artifact を誤拒否または誤受理する。
- **real / 要確認:** real

### 「欠けているのは producer だけ」は test から導けない

- **所見:** adapter/path の 49 test は fixture raw の消費可能性を示すだけで、実走 blocker が producer だけとは証明しない。
- **場所:** `s1-brief.md:83-84, 109-119`
- **なぜ欠陥か:** brief 自身が sanctioned command、schedule/seed issuer、certified-selection connection、report generator、paper cell を scope 外として列挙している。さらに事前登録本文は先行 freeze と人間指名が済むまで発効しないとする (`docs/phase3-b4-reflux-ablation-preregistration.md:725-739`)。formal B-4 が 0 本であることから、その原因を producer 不在だけへ帰属できない。
- **成果物への影響:** T-2049 完了を B-4 実走可能／verdict 到達可能と誤報し、実際には空欄の報告セルを埋められない。
- **real / 要確認:** real

### 親の P1-b 対策は campaign との結合点を欠く

- **所見:** registry が唯一の `precursor_hash` 権威だという主張は、registry row と実 campaign の対応が証明されない限り転記権威に留まる。
- **場所:** `s1-brief.md:93-100`
- **なぜ欠陥か:** plan はまさに registry 値を転記するが、root の lock、sidecar、receipt に block／attempt／initial proposal の結合 field がない。外部 evidence hash を source に並べても、その evidence がどの registry row のものかは決まらない。
- **成果物への影響:** precursor/reference の reward hack が残り、pair の差替えで verdict を操作できる。
- **real / 要確認:** real

## 裁定パッケージ候補 (scope 外だが判断が要る事項)

### 1. pre-run receipt と raw authority の境界

- **問い:** T-2049 の authority は、既存 `B4PrerunPublication` の planned result path に束縛される必要があるか、それとも任意 `record_root` の別台帳を許すか。
- **選択肢:** 束縛を T-2049 の受入条件にする／T-2051 の責務へ送り、T-2049 は「未束縛 writer」と明記する。
- **推奨:** 後者へ送るなら、本 wave を authoritative／file-drawer closed／verdict-ready と呼ばない。
- **判断しない場合の影響:** 同一 registry から複数 raw root を作る受理集合が未確定のまま残る。

### 2. `treatment_fired` と `contaminated` の意味

- **問い:** 既知の未閉鎖経路がある状態で、receipt の生成・消費を treatment 発火とみなし、検出証拠のない contamination を偽としてよいか。
- **選択肢:** receipt-level の狭い意味へ正式に定義変更する／事前登録どおり next synthesis と off 汚染を要求し、証明不能な標本は verdict-ready にしない。
- **推奨:** 現在の事前登録文言を維持するなら後者。
- **判断しない場合の影響:** treatment shortage と contamination 分岐の受理集合が producer 実装者の裁量になる。

### 3. exact analysis closure 外の producer を誰が認証するか

- **問い:** 5-file pin を動かさないまま、source artifact の意味を決める新 producer の版と実行結果をどの層が certified verdict に束縛するか。
- **選択肢:** 後続 certified-selection 層の明示責務とする／T-2049 成果物を非 certified projection に限定する。
- **推奨:** 接続層が実在するまで後者として扱う。
- **判断しない場合の影響:** source bytes の hash は一致しても、どの producer 意味論で生成されたかを verdict が識別できない。

## 総括

plan は 402 個の file を並べることはできても、402 campaign root の実行順、終了、block／precursor 帰属、再開を権威的に記録できない。特に publish 順 slot、任意 `record_root`、post-link 不明状態、未証明の `treatment_fired`／`contaminated` により、verdict と受理集合が実運用順序や caller 選択で変わる。

凍結 pin への直接の file 名・定数名衝突は見つからなかったが、その結果、新しい権威 producer は pin と独立 consumer の外に残る。新しい署名や protocol nonce は計画されていない一方、slot occupancy を一回性状態とする新台帳は実質的に導入されている。

親 brief の一 campaign から一般化できるのは legacy on の具体的 lexical shape と観測された不一致までであり、formal B-4、off、receipt、sidecar、abort、missing、並行性、201 block の値域へは一般化できない。現状の plan を完了しても、B-4 は production verdict へ到達しない。