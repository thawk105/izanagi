静的結論として、段 2 プランのままでは昇格は不十分です。最大の穴は、再導出の基点となる `measurement_head` が receipt 側の自己申告から独立に束縛されていないことです。

## 所見

### 1. real — `measurement_head` の差し替えで別 commit を権威にできる

標準 verifier が確認するのは次だけです。

- 40 桁 commit 形式と六 trial 間の一致: `s8c_acceptance_receipt.py:449-502`
- report 最上位の `measurement_head` と receipt の一致: `s8c_acceptance_receipt.py:734-740`
- receipt 自身が現行 HEAD に tracked であること: `s8c_acceptance_receipt.py:941-950`

一方、producer の `launch_admission.binding` には独立した `measurement_head` が載りますが、`_verify_v2_trial_arm_execution` は binding の `arm`、`holdout`、`campaign_id` しか比較していません。`measurement_head` は無視されます。`trial_registry.py:4110-4115`、`s8c_acceptance_receipt.py:764-774`

さらに、`_committed_regular_blob` は指定 OID に `ls-tree` / `show` するだけで、現行 HEAD の ancestor か、preregistration 後か、registry に登録された measurement head かを検査しません。`s8c_arm_inputs.py:336-365`

したがって攻撃者は、正しい off artifact が存在する別 commit、さらには現行 HEAD の非 ancestor commit を六 trial 共通の `measurement_head` として receipt/report に書けます。on/swapped は現在の `HOLDOUTS` から導出され、commit が実質効くのは off artifact だけです。`s8c_arm_inputs.py:442-459`

trial-registry の発行経路には ancestor 検査があります。`trial_registry.py:5013-5018`、`trial_registry.py:5622-5631`。しかし公開 `verify_acceptance_receipt` は receipt がその経路で発行されたことを証明せず、その検査を再実行しません。

よって、段 2 プランの新 gate は必ず発火しても、攻撃者が選んだ偽の基点から正しく再導出してしまいます。これは T-1726 の正しさ境界に対する実在する迂回です。

### 2. real — `cells=[]` のまま verified receipt を返せる

`_verify_v2_trial_arm_execution` は `cells=[]` を明示的に許し、`descriptor_proven=False` を返します。`s8c_acceptance_receipt.py:776-822`

最後の拒否条件は、C02 reason が落とされている場合だけです。`c02-arm-binding-unproven` を残せば、空 cell を含む receipt は受理されます。`s8c_acceptance_receipt.py:979-987`

段 2 の新 gate は receipt の digest を freeze 再導出値と比較するだけなので、空 cell でも receipt/report/run-start に正しい expected digest を自己申告すれば通ります。実際にどの descriptor で実行したか、そもそも descriptor が存在したかは証明されません。

- 六 trial 行と六 arm cell の組は parser が閉じる: `s8c_acceptance_receipt.py:403-511`
- 各 report に実行 descriptor が存在することは閉じない: `s8c_acceptance_receipt.py:776-796`
- C02 を残せば verified capability を返す: `s8c_acceptance_receipt.py:1001-1009`

これは「誤った digest」を通す穴ではありませんが、「実際の実行条件が不明なまま expected digest を名乗る receipt」を通す実在する穴です。全 receipt が現在 non-certifying であるため、現時点の成果物影響は別途遮断されています。

### 3. real — freeze 投影は full condition authority ではない

現行 `HOLDOUTS` の各 entry は次の四 keyだけで、段 2 投影はこれをすべて含みます。

- `candidate_id`
- `ycsb`
- `records`
- `threads`

根拠: `s8b_holdout_freeze.py:87-103`

legacy freeze の各 holdout entry はこの四 keyに加えて、次の二 keyを持ちます。schema も六 keyを要求します。`s8b_holdout_freeze.py:1066-1071`

- `unknownness_check`
- `variant_binding`

したがって、厳密な集合は以下です。

- 現行 `HOLDOUTS` entry から落ちる key: なし
- legacy holdout entry から落ちる key: `unknownness_check`、`variant_binding`
- `ycsb` 内から落ちる key: なし。辞書全体を投影するため

条件への影響は異なります。

- `variant_binding`: 実条件を変えます。materialization はここから configuration entry を取得します。`s8b_materialization.py:98-109`。selector basis も workload、`variant_binding`、`derangement` をまとめて hash します。`s8b_selector_freeze.py:299-329`。これを落とした gate を「legacy freeze の条件全体から再導出」と呼ぶのは誤りです。
- `unknownness_check`: workload descriptor 自体は変えませんが、holdout が未知で受入可能だったかという適格性条件を変えます。`conjunction_hits=[]` などは本来別 gate です。`s8b_holdout_freeze.py:1075-1119`

`load_legacy_freeze` の固定 SHA-256 により legacy bytes 自体の差し替えは拒否されます。`s8b_ratified_freeze.py:1409-1427`。穴は raw bytes の非束縛ではなく、receipt の実行条件へ投影されない意味領域が残ることです。

### 4. 疑い — `DERANGEMENT` の exact 束縛は無いが、現行二要素では誤写像を作れない

段 2 helper は legacy document の `derangement` と現在の `DERANGEMENT` を比較しません。resolver は現在の source mapだけを使います。`s8b_holdout_freeze.py:100-104`、`s8c_arm_inputs.py:445-458`

ただし現行条件では、

- holdout 名集合は legacy と source で exact 比較される
- 要素は `rr80` と `rr20` の二つだけ
- 自己写像を拒否する
- 往復二-cycleを要求する

ため、有効な写像は `rr80 ↔ rr20` の一通りしかありません。余分な未使用 keyは入り得ますが六セルの条件は変わりません。

したがって exact 比較の欠落自体は事実ですが、現行二要素集合で誤った swapped 条件を通す具体的経路は確認できません。ここは「未確定」ではなく、現行構造では検出力不足に直結しない疑いです。

### 5. real — expected `arm_binding_digest` 比較は純増検出力ゼロ

既存 gate はすでに次を要求します。

`B_receipt = hash(holdout, arm, C_receipt)`

根拠: `s8c_acceptance_receipt.py:803-809`

段 2 の新 gate は次を追加します。

1. `C_receipt = C_expected`
2. `B_receipt = hash(holdout, arm, C_expected)`

しかし既存述語と 1 が真なら、2 は決定論的に必ず真です。したがって expected `arm_binding_digest_sha256` の比較は防御の重複であり、受理集合を追加では狭めません。

純増検出力を持つのは expected content digest の比較です。freeze document と現在の `HOLDOUTS` の比較も、source drift に対しては純増です。

### 6. real — プランどおり配置すれば発火漏れや早期 return はない

この点についてプランは成立します。

- v2/v3 は parser が H1/H2 × on/off/swapped の六セル集合を強制する: `s8c_acceptance_receipt.py:403-511`
- `verify_acceptance_receipt` は六 trial を無条件にループする: `s8c_acceptance_receipt.py:962-978`
- 段 2 の指示どおり `_assert_rederived_trial_arm_execution` を既存検査後に無条件で呼べば、verified return に到達する全 v2/v3 trial で新 gate が走る
- `verify_acceptance_receipt` 自体が公開入口で、最後に sealed value を返す: `s8c_acceptance_receipt.py:918-1009`
- `require_current_verified_receipt` も内部で `verify_acceptance_receipt` を再実行する: `s8c_acceptance_receipt.py:1012-1026`
- `parse_acceptance_receipt_bytes` は公開ですが、返すのは未検証の `AcceptanceReceipt` であり `VerifiedAcceptanceReceipt` ではない

verified receipt を返す API 関数に、世代分岐や早期 return による発火しない経路は見つかりません。所見 1 は発火回避ではなく、新 gate が信じる入力の汚染です。

### 7. real — v1 receipt は現行 `layer3_report` 成果物へ入れない

v1 を含む全 schema は parser で `certifying=false` に固定されます。`s8c_acceptance_receipt.py:393-401`。verified capability の `certifying` もその値を返します。`s8c_acceptance_receipt.py:155-157`

`build_accepted_report` は再検証後、直ちに `verified.certifying is True` を要求します。`layer3_report.py:617-624`。さらに docstring 自身が certified-selection consumer は存在しないと明記しています。`layer3_report.py:611-615`

したがって v1 receipt が `layer3_report` 経由で certified artifact に効く現存経路はありません。v1 が T-1726 の再導出対象外でも、現在の成果物経路には残存露出しません。将来の certifying schema は別問題です。

### 8. real — positive control は既存 gate を通り、新 content gate だけで落ちる

段 2 の mutant は静的には妥当です。ただし descriptor 値は文字列ではなく整数 `80 -> 79` とするのが正確です。descriptor producer は整数を格納し、schema も整数 0..100 を要求します。`s8b_descriptor.py:114-125`、`s8b_descriptor_schema.json:9-15`

既存 gate を通る理由は次です。

- `79` は descriptor schema 上も有効
- `launch_admission.binding.ycsb_rratio` は既存 verifier の比較対象外: `s8c_acceptance_receipt.py:764-774`
- forged descriptor から content digest を再計算すれば descriptor hash 検査を通る: `s8c_acceptance_receipt.py:788-795`
- binding digest を再計算すれば既存 tuple 検査を通る: `s8c_acceptance_receipt.py:803-809`
- receipt/report/run-start の三箇所を同期すれば equality を通る: `s8c_acceptance_receipt.py:798-821`
- report/journal SHA-256 を同期すれば reference hash を通る: `s8c_acceptance_receipt.py:963-972`
- 六 report の descriptor は残るため C02 reason-drop 検査も通る: `s8c_acceptance_receipt.py:979-987`
- H1 の他二 arm は 50 と20なので、79 mutant は実質的に pairwise distinct を維持する: `s8c_acceptance_receipt.py:512-522`

新 resolver は legacy H1/on の expected 80 descriptor を導くため、receipt の79 digestとの比較で初めて落ちます。positive control として有効です。未実走です。

## 親 brief と段 2 プランへの訂正

### real — DW-G05 と `layer3_report:618` の解釈が誤り

親 brief `brief.md:15-18` は「`require_current_verified_receipt` の緑だけで受理され、論文数値を決めうる」としています。しかし実際には `layer3_report.py:623-624` の `certifying=true` gate が必ず後続し、現行 receipt は全世代 false 固定です。

`layer3_report.py:618` は呼出し位置として正しいものの、「戻り値をそのまま信じる唯一の下流」という `brief.md:29` の意味付けは誤りです。直接 consumer ではありますが、到達不能な certifying pathです。

### real — P4 は verifier 専用の性質ではない

`resolve_arm_input` 自身が現在の `HOLDOUTS` を読むため、この性質は全 caller に共通です。`s8c_arm_inputs.py:442-459`

`trial_registry._expected_registered_arm_execution_record` も同じ resolver を呼ぶだけで、legacy freeze を直接 load しません。`trial_registry.py:5320-5333`。producer 側には別途四-key legacy projection の束縛があります。`p3_autonomous_workload_trial.py:854-877`。したがって「registry の resolver は歴史的 freeze から独立再導出済み」と読むなら誤りです。

### real — 「純増」は限定付きでのみ正しい

`brief.md:31-35` の定義どおり「標準 verifier 単独」に限定すれば、expected content digest 比較は純増です。

リポジトリ全体では、trial-registry 発行経路がすでに expected arm execution と比較します。`trial_registry.py:5643-5652`。したがって repository-wide の新規検出力ではありません。また expected binding digest の比較部分は所見 5 のとおり純増ゼロです。

### real — アンカー表の不正確箇所

- `_formal_profile_source_record (851)` は誤り。関数開始は `p3_autonomous_workload_trial.py:854`、legacy load は856、authority 比較は861-877です。851は前 helper の失敗行です。
- `trial_registry.launch_admission_record (4098)` は関数アンカーとしては正しいですが、`ycsb_rratio` 一本という証拠は `trial_registry.py:4110-4115` です。また同じ binding に `measurement_head` も載る点を親は評価していません。
- `layer3_report.py:618` は verifier 呼出しだけを示し、受理を示しません。受理可否には少なくとも623-624が必要です。
- `trial_registry.py:5320` は current resolver による再導出の証拠ですが、legacy freeze からの直接再導出の証拠ではありません。
- `_arm_binding_digest:684` と `resolve_arm_input:434` の関数位置自体は正しいです。ただし実際の信頼境界を示す行はそれぞれ684-692、442-459です。

### 疑い — P2 の「v4 は provenance だけ」という根拠は広すぎる

`brief.md:48-50` は `measurement_head` があれば再導出可能としますが、その field 自体が独立束縛されていません。また `variant_binding` は現行 receipt digest に入らない実条件です。

これだけで v4 必須とは確定できません。`measurement_head` は既存 launch binding との照合で閉じられる可能性があります。一方、full freeze condition を対象にするなら「v4 の純増は provenance のみ」という断定は未確定です。

## 総括

1. **最重度 real:** receipt が名乗る未束縛の `measurement_head` をそのまま再導出基点にするため、正しい off artifact がある別 commit を指して新 gate を通せます。
2. **real:** 親 brief の論文成果物影響は現行コードでは成立しません。全 receipt が non-certifying で、`layer3_report` が必ず拒否します。
3. **real:** 四-key投影は `variant_binding` を落とすため、full legacy condition authority の再導出にはなっていません。
4. **real:** `cells=[]` と C02 reason を組み合わせれば、実行 descriptor が一切無いまま expected digest の自己申告を verified receipt にできます。
5. **real:** expected `arm_binding_digest` 比較は既存 gate と expected content equality から恒真になり、純増検出力はゼロです。
6. **real:** 段 2 どおり無条件配置すれば、v2/v3 六セルの発火漏れや verified-return の早期迂回はありません。
7. **real:** 80→79 mutant は、整数79を使い三者 digest を同期すれば既存 gate を通り、新 content gate だけで落ちる有効な positive control です。
8. **real:** v1 receipt の現行 certified artifact 経路は存在しません。

書込み、pytest、project import、Web 検索はいずれも行っていません。全項目未実走で、静的検査のみです。