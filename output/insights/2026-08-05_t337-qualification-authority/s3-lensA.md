## `declared_use_class` への改名は裁定済みの閉表を破る

- 深刻度: blocker
- 根拠: `docs/archive/worklog-phase3-0802-113-116.md:937-957`、`docs/archive/worklog-phase3-0802-117-121.md:1367-1370,1407-1409`、`output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:25-43`
- 攻撃入力または再現手順: T-318/T-337 は literal に `artifact_role=qualification` を反復している。ところが新 receipt を `{"declared_use_class":"qualification", ...}` とし `artifact_role` を欠落させると、将来の T-318 共通 gate は二択になる。裁定どおり `artifact_role` 必須なら正当な RF receipt を全拒否し、RF だけ別名を例外許可すれば新 producer が共通閉表の外へ出る。既存名が別用途なのは事実だが、`orchestrator/campaign/s8b_oracle_artifacts.py:26-29,169-186` の局所 schema に閉じており、D75 は全 schema における同名禁止を定めていない。改名には再裁定が必要である。
- 成果物影響: 前者では正当な RF 証拠が certified 選択・材料レポートへ一件も入らず、後者では未分類 producer の receipt が試行台帳と選択経路へ入る。

## arm/source/binary を再束縛するための入力 field が存在しない

- 深刻度: blocker
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:77,85-100`、`docs/decisions.md:6165-6174`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:113-120`
- 攻撃入力または再現手順: 提案 input は schedule に `arm_role`、attempt に raw-run pointer と TPS を持つだけで、三 arm の source path/hash、binary hash、candidate bytes、`env_tag`、CCBench pin、trace mode を持たない。11 cluster で stock=100000、degraded=20000、手製中間版=60000 を安定して測り、手製版を `arm_role="candidate"`、`candidate_id="synth-C"` と書けば `D=80000,N=40000,G=40000` となる。合成システムの実候補 bytes との照合先がないため、`s2-plan.md:95` の「事前登録 identity へ再束縛」は実装不能である。
- 成果物影響: 合成系が作っていない中間版を合成候補として `eligible` にでき、certified 選択の受理集合、材料レポートの RF 値、試行台帳の candidate 参照が偽装される。

## producer 同士の双射で失敗試行と family 全体を消せる

- 深刻度: blocker
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:87-100,102-111,168-170`、`output/insights/2026-08-03_t338-rf-statistical-design/package.md:280-289`、`output/insights/2026-08-03_t338-rf-statistical-design/s2-plan.md:107-120`
- 攻撃入力または再現手順: 先に repo 外で C1/C2、W1/W2、12 allocation を走らせて結果を見る。その後、成功した C2/W1 の11件だけを含む prereg commit `A` と descendant `B` を作り、`measurement_start={prereg_commit:A,measurement_head:B,parent_family_id:"fresh-C2"}`、11件だけの `schedule`、それと完全一致する `attempts[]` を書く。W2、C1、失敗 allocation は schedule と attempts の両方から欠落させる。提案には prereg manifest の path/hash、期待 workload/contrast/candidate 集合、`family_members`、alpha/spending、canonical registry head がないため、ancestry・双射・family binding はすべて通る。git ancestry が raw 値の先行取得を検出しないことは同 package が既に指摘している。
- 成果物影響: 成功した候補・workload・attempt だけで `eligible` を作れ、certified 選択が拡大し、材料レポートと試行台帳は「完全な双射」を持つように見える欠落集合になる。

## `cluster_id` の自己申告だけで真の J=1 を J=11 にできる

- 深刻度: blocker
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:87-100`、`output/insights/2026-08-03_t338-rf-statistical-design/package.md:144-151`、`docs/archive/worklog-phase3-0803-138-139.md:350-353`
- 攻撃入力または再現手順: 同じ allocation・node・時間窓内で33 runを行い、三 arm ごとの11反復に `cluster_id="c01"`〜`"c11"` を付ける。全 attempt の accounting pointer は同じ allocation を指す。計画には cluster を node/時間窓から独立に導出する規則がなく、schedule の producer field を数えれば J=11 になる。Q4 は allocation ID 自体すら独立性の必要十分条件でないと裁定しているため、ID 一意性検査だけでも足りない。
- 成果物影響: 擬似反復で信頼領域が過度に狭まり、真には判定不能な artifact が certified 選択へ入り、材料レポートの J・区間と試行台帳の cluster 参照が虚偽になる。

## validator の source hash は「その validator が実行された」証拠にならない

- 深刻度: blocker
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:13-15,102-108,131-136`、`orchestrator/campaign/artifact_admission.py:99-120,707-722`、`docs/decisions.md:6650-6654`
- 攻撃入力または再現手順: producer が実 repo から予定 validator の SHA-256 を読み、`eligibility_status:"eligible"`、正しい validator identity/source hash、任意の input hash、空の `reasons` を持つ decision JSON を直接書く。hash はコード identity しか示さず、そのコードによる計算結果であることを証明しない。現行先例の実効防壁は detached decision を信用することではなく、`require_admitted_campaign()` が raw path から `_inspect_campaign()` を同一呼出し内で実行する点にある。提案は admission が trusted validator を必ず再実行することも、decision を入力として受け取らないことも定めていない。
- 成果物影響: producer 作成の `eligible` decision が sealed 型へ昇格し、certified 選択・材料レポート・試行台帳の全三層で偽の validator authority が参照される。

## 前後 hash 比較は ABA と validation 後の差替えを防がない

- 深刻度: blocker
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:15,81-83,102-109`、`docs/decisions.md:6650-6654`、`orchestrator/campaign/layer3_report.py:423-429`
- 攻撃入力または再現手順: path が指す bytes を A（不適格）と B（適格値）で切り替える。pre-hash 時は A、semantic read 時は B、post-hash 時は A に戻せば、二回の hash は一致するが decision は B から計算され A の hash に束縛される。symlink 禁止、単一 fd/snapshot、同じ byte buffer の hash と parse が計画にない。さらに正しく検証した後に path を差し替えても、consumer は decision だけを読むため再検出規則がない。現行 Layer 3 はこの窓を狭めるため admission 後に再 hash している。
- 成果物影響: decision と実 bytes が食い違ったまま certified 選択され、材料レポートの path/hash 参照と試行台帳の再現対象が別物になる。

## brief の「適格性 field を読む consumer は 0 件」は実測と矛盾する

- 深刻度: must-fix
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/brief.md:27-30,55-59`、`orchestrator/campaign/silo_ladder_rung1_contract.py:538-564`、`orchestrator/campaign/silo_ladder_rung1.py:1220-1246,1556-1560,3755-3761`
- 攻撃入力または再現手順: filesystem は変えず、ledger の in-memory copyで `pipeline_eligible=true` にして `validate_ledger()` へ渡すと exact scalar mismatch になる。同様に evidence copy の `recovery_measurement_eligibility=true` は `_validate_schema()` で拒否される。これは正例へ昇格させる consumer ではないが、明白な受理/拒否 consumer であり、brief が掲げた P2 の反証条件を満たす。
- 成果物影響: 三 field を「不活性な歴史的宣言」と誤認すると、既存 driver が拒否する ledger/evidence を後続 proof chain が参照し、材料レポートと試行台帳の受理集合説明が実装と食い違う。

## P4 は一回の事後調整禁止を新 study の永久禁止へ一般化している

- 深刻度: must-fix
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/brief.md:62-64`、`docs/decisions.md:6191-6217`、`docs/archive/worklog-phase3-0802-117-121.md:353-358`
- 攻撃入力または再現手順: 代替 X、両 workload、J、schedule、受理条件を結果取得前に新しい preregistration として commitし、その後に別 study を走らせる。これは D126 が禁じた「877859 の結果を見て同じ probe の候補・workload を差し替える」操作ではなく、worklog が明示した次の選択肢である。P4 の理由をそのまま適用すると、この正当な新 study まで拒否される。
- 成果物影響: 適格な新正例が試行台帳へ登録できず、certified 選択と材料レポートの RF 証拠受理集合が過剰に空のままになる。

## docs-only なのに未実装の六層を現在形の保証として数えている

- 深刻度: nit
- 根拠: `output/insights/2026-08-05_t337-qualification-authority/s2-plan.md:115-140,155-168`、`output/insights/2026-08-03_t338-rf-statistical-design/package.md:310-312`、`orchestrator/campaign/layer3_report.py:350-355,415-417`
- 攻撃入力または再現手順: T-339 が列挙した9層で数えると、本 wave の実装被覆は 0/9。後続候補も producer、registry、schedule validator、RF calculator、authority/admission、tests の6/9だけで、Layer 3、selector、材料レポートの3/9を残す。それにもかかわらず第7節は sealed consumer、missing reject、全 attempt/alpha ledger 防御を現在形で列挙する。docsだけを land して RF receipt を現行 Layer 3 に渡しても qualification ancestry として拒否され、selector hook は存在しない。
- 成果物影響: 現時点の certified 選択・材料レポート・試行台帳は不変だが、未発火保証が将来の材料レポートから誤って参照され得るため nit とする。

### 独立照合結果

- 実測1、2、5は確認できた。実測6も tracked inventory の範囲では確認できた。
- 実測3は反証。実測4の既存用途は確認したが、そこから導いた P1 は反証。
- P2の独立 validator という核はQ11どおりだが、三 field を「歴史的宣言だけ」とする部分は反証。
- P3は確認。P4の結論はscopeとして可能だが、D126を根拠にした一般化は反証。
- P5の docs-only 判定は DW-G04 の文言どおりで、反証しなかった。

### 凍結 bytes 監査

所見なし。現 SHA-256 は `patches/ledger.json`=`34d6bf…f603`、patch=`07e576…9324`、evidence=`38f5de…4b37`。ledger と patch は `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:29-35` および `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1188-1206` の整合鎖にある。evidence 自身は FROZEN_MANIFEST の literal pin ではない (`docs/decisions.md:5776-5779`)。計画された新規 docs 2件はこの鎖へ入らず、三保護対象の直接・間接変更経路は認めなかった。

## 総括

- **NO-GO**
- blocker は **6件**: 裁定外の field 改名、arm identity 欠落、自己根付き双射/family、cluster 自己申告、decision 偽造、ABA/差替え。
- must-fix は2件、nitは1件。
- 親 brief 自身の最大欠陥は、明示裁定 `artifact_role=qualification` を概念名へ読み替え、P1の改名を無承認で採ったこと。
- protected 3 file の bytes を動かす計画は見つからなかった。