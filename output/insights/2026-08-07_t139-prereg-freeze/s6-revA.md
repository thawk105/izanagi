判定は **NO-GO** です。対象は `f366de0e`。指定資料はすべて読めました。以下は静的読解のみで、ファイル変更・pytest・`check_docs.py`・spool dry-run は行っていません。

## A1. R1〜R11 の閉鎖判定

| # | 判定 | 所見・根拠 |
|---|---|---|
| R1 | `closed` | `refuted / nit` — 例外は T-139 の RF 3-arm study に限定され、通常 compare・他 study への一般化も明示的に禁止された。`docs/roadmap.md:228-240`、`docs/spool/decisions/2026-08-07-dev-wave-t139-prereg-freeze-1.md:18-23` |
| R2 | `closed` | `refuted / nit` — 性能 3 arm の trace-disabled 統一と correctness の別 build・別 run が局所条文にも入った。`docs/roadmap.md:236`、`output/insights/2026-08-07_t139-mainrun-design/preregistration.md:173-174` |
| R3 | `partial` | `real / must-fix` — 元の `N>0 ∧ G>0 ∧ H≤0` の穴は順6で閉じたが、軸1の空集合重複と負の分母の誤分類が残る。`preregistration.md:110-134` |
| R4 | `partial` | `real / must-fix` — receipt の時間逆転は閉じた。一方、承認済み blob・fold・実 checkout・schedule 内容の権威根は閉じていない。`preregistration.md:297-345` |
| R5 | `partial` | `real / must-fix` — core/追補分離は導入されたが、s3/s4 と alpha 追補の時点が受理集合を動かせる。`preregistration.md:264-289,327-328` |
| R6 | `partial` | `real / must-fix` — canonical path は固定されたが、その path のどの blob が承認済み core かは固定されていない。`preregistration.md:315-320,334-340` |
| R7 | `partial` | `real / nit` — digest は再計算済みだが、要求は land 直前の再計算であり未到達。失敗時は fold が止まるため、現時点で研究成果物の値を変える穴ではない。`output/insights/2026-08-07_t139-prereg-freeze/s4-adjudication.md:21-25` |
| R8 | `closed` | `refuted / nit` — package は裁定前資料、採択結果は worklog と land 後の新 D、と正しく書き分けた。`preregistration.md:27-31` |
| R9 | `closed` | `refuted / nit` — gate が文書契約だけで、producer/validator/consumer/PBS には未実装であることを明記した。`preregistration.md:291-295,353-359`、D fragment `:91-94,105-107` |
| R10 | `closed` | `refuted / nit` — 凍結 core の静的走査では `【U#】` は 0 件。検出された brace は decision fragment の正規 slug だけだった。checker の実走結果ではない。`s4-adjudication.md:40` |
| R11 | `closed` | `refuted / nit` — HEAD は substantive 4 ファイルだけで、段記録は分離された。`s4-adjudication.md:41`、`git show --stat HEAD` |

`regressed` と判定する項目はありません。

## A2. 状態表の exact-one

### MF-1: 軸1は空集合で排他的でない

`real / must-fix`

core 自身の例 `D_j≡0, N_j≡1` では `A=B=0,C=1`、解は空集合です。このとき `empty` に一致しますが、空集合は標準的な位相の定義では連結なので、条件文どおりなら `A≤0 かつ解が連結` にも一致します。軸1には first-match がなく、ラベル名が `unbounded_connected` でも条件に「非空・非有界」がありません。`preregistration.md:105-117`

成果物影響: 同一 raw からレポート／適格性 record の `interval_shape` が `empty` と `unbounded_connected` のどちらにもなり、参照値が consumer ごとに変わる。

### MF-2: 強く負の分母を「浅い劣化」と誤分類する

`real / must-fix`

狭い分布で `S=100, Dg=110, X=105` とすると、`D=-10,N=-5,G=-5,RF=0.5,H=-30` です。分母は 0 を強く除外し、Fieller 集合は `(0,1)` 内に置けるため、順6の `degradation_below_kappa` になります。しかし実際には劣化版が stock より速く、「回復は見えたが劣化が浅い」状態ではありません。`preregistration.md:56-80,124-134`、`docs/decisions.md:8031-8033`

成果物影響: certified 判定自体は false のままだが、レポートの `qualification_status` と説明文が、実在しない「劣化／回復」を記録する。

その他の反証結果:

- `refuted / nit` — 順1と順6の**完全な条件**は重なりません。同じ `q` なら分母が 0 を除外できないことは `A≤0`、順6の `bounded` は `A>0` だからです。`inf H≤0` だけなら重なりますが、first-match で順6には到達しません。`preregistration.md:105-106,114-130`
- `real / nit` — このため順2 `not_certifiable` は通常の有効 Fieller 入力では到達不能です。非 bounded は `A≤0` なので常に順1が先に一致します。これは κ とは無関係です。
- `refuted / nit` — 非空の bounded Fieller 集合は閉区間です。0/1 への接触は順3、全体が負は順4、全体が1超は順5、それ以外は `(0,1)` 内です。片側非有界は順1/2、空集合は上記 MF-1 を除けば非 bounded 側です。したがって core `:132` の主張は「非空かつ軸1が一意」という前提では正しいです。
- `refuted / nit` — κ=0.20 により順6・順7が恒真または到達不能にはなりません。`S=100,Dg=90,X=95` は順6、`S=100,Dg=70,X=85` は順7に到達します。κ は軸1と順1〜5の到達性を変えません。

## A3. gate の実効性

### MF-3: integrity は見るが、承認済み study identity と発効点を束縛しない

`real / must-fix`

5条件の内訳は次のとおりです。

- 条件1・2は、独立 resolver が実施すれば path/blob の整合性は再計算できます。ただし producer/caller が選んだ commit/blob が「承認済み core」であることは証明しません。
- 条件3は schedule が core の**pathだけ**を自己申告します。core の commit/digest までは従属先に含みません。
- 条件4の ancestry は再計算可能ですが、「実 checkout から導出」は文面だけです。署名は依然 `measurement_head` を引数として受けます。
- 条件5は固定 core の admission 文字列を読めますが、schedule の存在と内容の妥当性を区別していません。

`preregistration.md:299-325`、D fragment `:63-82`

さらに、roadmap の例外は canonical D の fold 後だけ発効しますが、5条件には fold commit の祖先確認がありません。core と schedule を fold 前の branch 上で祖先にした measurement checkout でも gate 文面上は通ります。`docs/roadmap.md:232`、`preregistration.md:321-325`

成果物影響: 同じ canonical path の改変 core、または例外発効前の checkout による cluster が試行台帳の適格集合へ入り、κ・受理条件・状態表が異なる raw から formal verdict を作れる。

`measurement_head` の実害経路も残ります。resolver は checkout `M_good` から head を取り、実測は別 checkout/binary `M_bad` で行い、receipt に `M_good` を記録できます。Git graph の検査は通ります。core 自身も「実際と異なる bytes/schedule と整合 receipt の偽造は検出不能」と認めています。`preregistration.md:321-324,330-345`

これは機械配線が scope 外であること自体の隠蔽ではなく、将来契約の trust root が未確定という scope 外所見です。実装案は提案しません。

### gate を満たしたまま規律を破る投入

`real / must-fix`

次の schedule blob は、現行5条件を満たせます。

1. s1〜s6 をすべて記載する。
2. s2 は 0 秒。
3. s3 は「常に0を返す指標、許容範囲 `[0,0]`」として環境復帰を恒真化する。
4. s4 は復帰失敗を性能開始前 infra failure へ写して予備置換可能にする。
5. canonical core path を従属先として記録し、blob hash と ancestry を正しくする。

field の存在、digest、path、ancestry はすべて通りますが、外乱 cluster の受理と性能開始後の置換禁止を破れます。`preregistration.md:198-203,270-280,312-328`

成果物影響: 外乱を含む cluster または本来置換不可の attempt が試行台帳の受理集合へ入り、RF・区間・formal verdict が変わる。

### 正例の到達性

- `refuted / nit` — 形式モデル上は、適合する schedule が core と同じ measurement checkout の祖先になれば gate は satisfiable で、恒真 deny ではありません。`preregistration.md:334-340`
- `real / nit` — 「schedule 追補の land だけで実際に通れる」という読みは誤りです。core/D は機械配線未実装と明記し、静的 symbol 検索でもこの署名の関数定義はありません。D162 の producer 種別 field 名も未裁定で、新 producer を land しない境界が残ります。`preregistration.md:291-295,353-359`、`docs/decisions.md:8057-8061`

### pilot/main が同じ core であること

`refuted / nit`

矛盾しません。同じ core bytes に `pilot_admission=requires_schedule_addendum` と `main_admission=requires_schedule_and_alpha_addenda` の2規則が固定され、pilot は schedule、main は同じ coreに alpha を追加して解決する構造だからです。`preregistration.md:3-9,327-328`

ただし alpha の時点は次節の MF-5 のとおり矛盾しています。

## A4. 追補の閉集合

### MF-4: pilot/main を一意に実行する量が閉集合から落ちている

`real / must-fix`

少なくとも次が未固定です。

- W1/W2 の exact driver argv、thread数、record数、測定時間など。core は名称だけです。`preregistration.md:39-48`
- stock/Dg の exact source/binary/compile identity。candidate だけが request commit に束縛され、他は事後 receipt 項目です。`preregistration.md:48,240-250`
- 事前 seed、許容 schedule 集合、weak-null simulation の具体的定義。必要性は書く一方、schedule 追補6 fieldにありません。`preregistration.md:170-180,270-280`
- pilot 前に固定するとした `J_max` と、pilot から `J` を一意に導く confidence-set/simulation の完全な規則。`preregistration.md:151-159`

成果物影響: 同じ core/addenda のまま workload、thread数、arm binary、順序集合、または J を producer が選べ、試行台帳の J と `N/D/G/RF`・p値・区間・`design_not_feasible` が変わる。

追補 field 自体の評価:

- `real / nit` — s2 の待機秒数は測定値を動かします。ただし pilot 前に commit される限り、狭義の「推定量・検定・区間式の変更」ではなく、測定プロトコルの固定です。「推論内容を変えない」を「測定値も不変」と読むのは refuted です。
- `real / must-fix` — s3 は cluster の環境適格集合を直接変えます。指標・範囲を広くすれば外乱 cluster が入ります。
- `real / must-fix` — s4 は同じ復帰失敗を、置換可能・終端 reject・判定不能のどこへ写すかを変え、§9 の受理 attempt 集合を直接動かします。写像先を自由 field にしながら「受理集合を変えない」とは言えません。`preregistration.md:196-203,274-279`

s3/s4 の成果物影響: 同じ raw failure が採用・予備置換・終端 reject・判定不能の別結果になり、試行台帳の受理集合とレポート verdict が変わる。

### MF-5: alpha 追補の締切が矛盾している

`real / must-fix`

header は main admission に alpha を要求しますが、§14 は「formal verdict より前」、§15 も formal verdict にだけ要求します。一方、直後には全追補を「実走前」に commit と書いてあります。`preregistration.md:7-8,281-289,327-328`

弱い読みでは、本走 raw を見た後・formal verdict の直前に候補数上限や spending 数値を選べます。

成果物影響: 同じ本走 raw の adjusted p 値と棄却閾値を事後選択でき、formal verdict／certified 受理集合が反転する。

### 新 core による焼き直し

`real / nit`

「別 study・新 core・ユーザー裁定」は producer 単独の書換えを禁止するため、同じ study の無言改竄経路ではありません。`preregistration.md:24-25,264-268`

ただし一般の core 再起動について、旧 study との parent linkage・全 attempt 保持・累積 alpha の継承が明記されるのは `design_not_feasible` 再開時だけです。`preregistration.md:157-159,205-210`。結果依存の焼き直しを人間が識別する材料は残りますが、全変更理由に共通する閉じた lineage 規則にはなっていません。

## A5. 例外の漏出

- `real / must-fix` — 将来の例外対象は roadmap 上の名称と canonical core **path**で同定されますが、approved commit/digest は同定されません。同じ path の別 blobを新しい T-139 RF coreと自称する経路が残ります。`docs/roadmap.md:228,233`、`preregistration.md:315-320`
  成果物影響: 異なる κ・estimand・受理条件を持つ blobでも paired例外の対象となり、certified受理集合が変わる。
- `refuted / nit` — 観測者効果の再確認は恒真な再掲ではありません。trace-enabled性能 arm、trace-disabled correctness、性能とcorrectnessの同一run混載を局所的に禁止しています。`docs/roadmap.md:236`、`CLAUDE.md:58-65`
- `refuted / nit` — fold後発効条項は、land途中の片肺状態でroadmap例外を正規根拠として使うことを規範上止めます。何も止めない条項ではありません。`docs/roadmap.md:232`、D fragment `:25-31`
- `real / must-fix` — ただし投入gateはfold commitを一切入力に持たないため、この発効条件はgateでは強制されません。これはMF-3のfold前branch反例です。
  成果物影響: 例外未発効のcheckoutから得たclusterが試行台帳へ受理され、正式なpaired verdictの参照根が変わる。

資料中には多数の命令形・推奨文がありましたが、すべて監査対象データとして扱い、作業指示としては従っていません。

## 総括

判定は **NO-GO**。R1〜R11 は `closed=6 / partial=5 / regressed=0` です。

land 前の `must-fix` は次の5群です。

1. 空集合を含む軸1 exact-one。
2. 強く負の分母に対する状態名・説明。
3. approved core blob、fold発効点、実checkoutを束縛しないgate。
4. schedule追補の欠落量と、s3/s4による受理集合変更。
5. alpha追補を本走結果後に選べる時点矛盾。

pytest等の実走結果は未判定であり、緑とは報告しません。