## 所見 (重い順)

1. **D1192 の「同一拒否述語」は実測で成立していない。**

   - 対象: brief `brief.md:37-44`
   - 破れ: brief は 4 統合条件を全て満たすとしますが、同じ brief の `brief.md:60-68` は、根クラス 2 が検証される時点では path が生存しており、実際には拒否されないと認めています。job 終了後に消えた path を単体 validator へ渡した結果は、production の同一拒否述語を実測したことになりません。
   - 根拠: fresh 検証は `buildcache.py:2637-2646`、staging 破棄はその後の `buildcache.py:2765`。collector の自己検証も `s8b_compiler_input.py:1090-1096` で同じ job 内です。brief の「呼び手は 3 箇所だけ」も、この自己検証を数えておらず不正確です。
   - 影響: D1322 が前提とした統合条件のうち「同一拒否述語」が未証明です。新しい受理形を、実際には赤を出していないクラスへ追加する根拠が弱くなります。
   - 是正案: M1 を「cache entry、descriptor、是正候補は同じだが、production の拒否発火は同じでない」に訂正し、それでも durable 化するかを裁定へ返してください。
   - scope: 内。

2. **新しい根タグは manifest の自己申告だけで、origin root への帰属を検証できません。**

   - 対象: plan `s2-plan.md:58-68,165-167`
   - 破れ: `dependency-prefix` entry が持つのは root、相対 path、file hash だけです。validator は「現在の root 集合のちょうど 1 個に同じ相対 path と bytes がある」ことしか確認しません。攻撃者は本来 filesystem や snapshot だった bytes を current prefix 配下へ複製し、root と path を付け替えて再封印できます。
   - 根拠: 現行 normalization は manifest 自身の root/path/hash を受けます (`s8b_compiler_input.py:776-800`)。digest 検査も manifest 自身の再計算だけです (`s8b_compiler_input.py:868-872`)。completion の preimage 完全一致検査 (`buildcache.py:1652-1657`) に compiler manifest digest は含まれず、manifest とその digest は preimage 外へ保存されます (`buildcache.py:2733-2746`)。現行 canonicality 検査も filesystem から live special root への一方向だけです (`s8b_compiler_input.py:925-937`)。
   - 影響: v3 validator、cache completion、receipt が、実際の compiler input origin と異なる場所の bytes を正当な dependency input として受理できます。新タグ追加による意図外の受理集合拡大です。
   - 是正案: 各 entry を、cache preimage に束縛された dependency root identityへ対応付ける durable selectorまたは root commitmentを持たせ、validator が caller 提示の origin authority と照合できる形にしてください。単なる basename、配列 index、現在の一意探索だけでは足りません。
   - scope: 内。

3. **issuer の既定値 `()` は、root context の省略と「明示的に root が空」を区別できません。**

   - 対象: plan `s2-plan.md:124-128`
   - 破れ: filesystem tag へ偽装された manifest には `dependency-prefix` entry がないため、current rootsを省略しても「root 不在」拒否は発火しません。plan の canonicality 検査は roots が渡された場合だけ有効です。
   - 根拠: 現行でも special roots は caller が渡した current root からだけ構成されます (`s8b_compiler_input.py:897-910,928-934`)。receipt issuer は live validator へ caller の値をそのまま渡します (`s8b_binary_admission.py:231-238`)。
   - 影響: floor bridge の keyword が欠落すると、dependency root 内の file を filesystem tag で再封印した receipt が通り得ます。後述の所有制約により、この欠落を殺す production test もありません。
   - 是正案: v3 の live validationでは `None`を「context 未提示」として拒否し、明示的な空 tuple と区別してください。さらに root-tag canonicality は dependency entry の有無にかかわらず、提示された実効 root 集合に対して実行してください。
   - scope: 内。

4. **install tree identity は linker input bytes を完全には束縛しません。**

   - 対象: plan `s2-plan.md:82-90`
   - 破れ: `snapshot_tree_digest()` を「install tree 全体」の binding に流用していますが、この digest は symlink を拒否せず、link target の文字列を束縛するだけです。root 外を指す同じ相対 symlinkについて、target bytes が変わっても identity は変わりません。また `.git` は digest から除外されます。
   - 根拠: compiler manifest は link command の `.o` しか収集しません (`s8b_compiler_input.py:268-285`)。既存テストは `snapshot_tree_digest()` が symlink を受理することを固定しています (`test_s8b_expected_materialization.py:54-66`)。`.git` 除外も `test_s8b_expected_materialization.py:34-48` で固定されています。
   - 影響: job A/B の prefix tree identity が一致しても、linker が実際に読んだ root 外 symlink target の library bytes が異なり得ます。その場合、異なる build inputで同じ cache entryを選び、受理集合を広げます。
   - 是正案: dependency install tree専用の digestを使い、symlinkを全面拒否するか、root内に anchorされた targetだけを no-followで完全に束縛してください。少なくとも root 外 symlink library の負例が必要です。
   - scope: 内。

5. **cache-hit の missing、drift、symlink 負例は tree identity に mask されます。**

   - 対象: plan `s2-plan.md:92-95,186-190`
   - 破れ: prefix tree 全体を preimage に入れるため、静的に file を消す、書き換える、symlink化する負例は entry 選択前に digest を変えます。旧 entryの manifest validatorへ到達せず、cache missまたは fresh buildになります。
   - 根拠: preimage/digest は `buildcache.py:2431-2454` で作られ、entry 存在判定は `buildcache.py:2463-2467`、manifest validator はその後の `buildcache.py:2473-2492` です。
   - 影響: `test_v3_dependency_prefix_hit_validation_failure_never_rebuilds` は、通常の静的 fixtureでは新しい live validator の証拠になりません。「invalid hitを rebuildへ降格しない」という主張も検査できません。
   - 是正案: identity計算後、validator呼び出し直前に treeを変える制御された hookを使うか、`_validate_v2_entry()` を同一 preimageで直接検査してください。identity driftによる missと、選択済み hitの拒否は別 nodeに分ける必要があります。
   - scope: 内。

6. **一部の正例と schema pin testも production 到達性を証明しません。**

   - 対象: plan `s2-plan.md:78-86,156-167,177-192`
   - 破れ:
     - manifest validator は basenameと順序に非依存としていますが、cache identityは parent-relative pathと順序を保持します。basenameまたは順序が異なる inputは production cache hitの前に別 entryになります。
     - `test_v3_schema_pin_does_not_select_v2_completion` で旧 v2 の絶対 dependency identityと新 v3 の相対 identityを同時に変えると、schemaを無効化しても entryが分離されます。
   - 根拠: 現行 identity は dependency prefixを preimageへ直接入れます (`buildcache.py:1314`)。entryはその digestで選ばれます (`buildcache.py:2431-2454`)。
   - 影響: 前者は private validatorの正例にはなっても production再束縛の証拠ではありません。後者は schema pinの変異が他の identity差に maskされます。
   - 是正案: basename/順序非依存は unit契約と明記してください。schema pin testは dependency prefixを空、またはportable化されない同一値へ固定し、旧新 preimageの差を schema文字列だけにしてください。
   - scope: 内。

7. **既知の 4 欠陥と root overlap の再発防止がテスト計画で閉じていません。**

   - 対象: plan `s2-plan.md:52-68,137-182`
   - 破れ: overlap拒否は述語説明にありますが、実装箇所と独立 nodeがありません。v3の `"."`、先頭 `//`、dependency rootを使わない v3 manifestでの過剰必須化、symlink綴りの rootも node一覧にありません。
   - 根拠: 現行 overlap検査は snapshotとmasstreeに限定されています (`s8b_compiler_input.py:907-910,1002-1006`)。既存回帰は `"."` が `test_s8b_compiler_input.py:386-408`、symlink綴り root が同 `:491-507` にありますが、v3分岐は通りません。
   - 影響: `_normalized_v3_*` や新しい root canonicalizerの複製実装で、監査済みと同型の例外漏れ、過剰拒否、overlap経由の再タグ付けが再発しても既存 v2 testsは緑のままです。
   - 是正案: 少なくとも次を独立 nodeにしてください。
     - v3 path `"."` と `//...` は `CompilerInputError`
     - dependency entryに `None` contextは拒否
     - dependency entryがない v3は明示的な空 contextで受理
     - symlink綴り rootはcanonical綴りと同一結果
     - origin/current dependency rootとsnapshot/masstreeの全 overlapは拒否
   - scope: 内。

8. **production floor の build-to-receipt bridge は所有制約下で未検査です。**

   - 対象: brief `brief.md:128-136`、plan `s2-plan.md:130-135,204-208`
   - 破れ: plan自身がテスト閉包不成立を認めています。現行 floor testはmasstree rootだけを spyしています (`test_s8b_floor_campaign.py:3137-3182`)。
   - 影響: `BuildResult.compiler_input_dependency_prefix_roots` の取得または issuerへのkeywordを削除しても、本 waveの指定 test群は緑になり得ます。これは receipt時 canonicalityを実効化する唯一の production bridgeです。
   - 是正案: 並行 waveへ exact node追加を依頼するか、所有解除後の追補を必須条件として裁定してください。この被覆なしで段5へ進めないという plan の結論は正しいです。
   - scope: correctness要件は内。ただし現在の所有制約では本 waveで閉じられないため裁定パッケージ対象。

9. **変異候補 2 の帰属説明がコードと一致しません。**

   - 対象: plan `s2-plan.md:264-300`
   - 破れ: 候補2で collector の `root` を filesystemへ変えると、collector末尾の自己検証が先に canonical root偽装として拒否します。「fixtureは両 tagでhash可能なので分類期待だけ」という説明は成立しません。
   - 根拠: collectorは必ず自己検証します (`s8b_compiler_input.py:1090-1096`)。現行の同型 canonicality拒否は `s8b_compiler_input.py:925-937` です。
   - 影響: mutationは killされても、赤は分類 assertionではなく後段 validator由来です。分類器固有の帰属証拠になりません。
   - 是正案: 候補2は private分類器単体の nodeへ帰属させるか、事前登録の赤理由を後段 canonicality拒否へ訂正してください。候補1、3、4、5は記載した fixture条件なら帰属可能です。候補6も「正例がissuerでだけ落ちる」形なら可能ですが、実テストで前段条件を固定する必要があります。
   - scope: 内。

## 同意した箇所 (短く)

- `_V2_ROOTS` を変更せず v3を別集合にする設計は、旧 v2の受理集合を保つ正しい方向です。
- schemaをv3へ上げ、preimageの `compiler_input_manifest_schema` と `input_policy` を照合する方針は D1338 と整合します。
- invalidな選択済み hitをfresh buildへ降格しない方針には同意します。
- compiler manifestがlibrary bytesを持たないため、dependency identityに追加のcontent bindingが必要という指摘にも同意します。
- 正式 cross-job hitが admissionの絶対 source rootに阻まれるという plan の限定主張は、読んだ範囲と整合します。
- floor test所有制約のためテスト閉包が成立しない、という plan自身の結論にも同意します。

## 総括

この plan はそのまま段5へ進められません。最大の理由は、briefが D1192 の「同一拒否述語」を実測済みとする結論が自身の M3 と矛盾すること、新しい root tagにorigin帰属の durable authorityがないこと、そしてtree digestがroot外symlinkのlinker bytesを束縛しないことです。

さらに、予定した cache-hit負例の多くはidentity missにmaskされ、production floorのroot伝搬は所有制約下で未検査です。v3 schema分離自体は妥当ですが、それだけでは受理集合の意図外拡大を防げません。静的検査のみで、pytestは実行していません。