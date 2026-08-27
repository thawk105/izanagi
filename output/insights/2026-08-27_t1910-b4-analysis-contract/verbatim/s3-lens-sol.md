## 前提の確認

指定された次の資料を、与えられた bytes の末尾まで読めた。

- 親 brief
- 段 2 plan
- 対象文書 snapshot
- D1082
- D1060
- §5 固定表の機械契約抜粋

読めなかった資料はない。機械契約は抜粋自体が関数呼出の途中で終わっているが、提供された範囲は全て確認した。

Web 検索、書き込み、pytest、その他の実測は行っていない。以下は静的検査だけによる判定である。

## 正しさ境界の所見

### C1. 母集合は現在の plan のままでは凍結されないが、「具体化待ち」を理由に D1082 全体を止める必要はない

- 所見: plan が列挙した将来要件は検査項目であって、閉じた母集合述語ではない。一方、母集合を「閉じた規則」として今凍結し、後で manifest bytes を機械導出することは可能である。
- 根拠: `preregistration-snapshot.md:§5.1` は「B-4 の出力を見る前に freeze」とし、`§7.1` は赤が出なかった block、crash、未到達も削除せず全件報告すると定める。plan 自身も「対象確定後に」「具体的な母集合が得られるまで」と将来判断を残している。
- 成立条件: driver、workload、初期 proposal、赤形状、重複処理、生成失敗、抽出順のいずれかを人が manifest 作成時に選べるなら、実走後の狭窄に使える。manifest の hash だけでは完全性を証明しない。
- 提案: 同じ変更単位で、少なくとも次を全て固定する。

  - source snapshot と候補 driver の有限集合
  - 結果を生成しない probe による driver 選択関数。0 件、複数件も含む
  - workload bytes、proposal 生成器、seed、model、prompt、予算
  - screening を除く赤 category の機械 enum と schema hash
  - 全 scheduled precursor attempt を残す規則。生成失敗、赤の非再現、重複、破損を除外理由にせず状態として残す
  - canonical block id、順序、pilot と正式標本の分割関数
  - source registry から manifest を再生成し、行集合の完全一致を検査する consumer

### C2. 提案された primary outcome は「与えられた AnalysisInput に対して」は純粋だが、分析全体としては閉じていない

- 所見: `expected_n`、`floor_fraction`、block tuple、`precursor_reference_tps` が呼出側の自由入力である。不都合な block を落として `expected_n` も減らす、別 floor を渡す、基準 TPS を変えて tie を動かす余地がある。
- 根拠: `s2-plan.md:primary outcome の純関数`。入力件数検査は、呼出側が渡した `expected_n` と一致することしか検査しない。`preregistration-snapshot.md:§7.2` は manifest と完全性 consumer が存在しないことを明記する。
- 成立条件: raw receipt から `AnalysisInput` への adapter、manifest、floor artifact、n のいずれかが同じ発効 commit に束縛されなければ成立する。
- 提案: 純関数の入口を自由な `AnalysisInput` ではなく、発効 commit、manifest、raw terminal receipt の canonical bytes にする。`expected_n`、floor、block 集合、親 TPS は関数内部で発効版から導出し、呼出側から値として受け取らない。

### C3. status への写像と `analysis_invalid` 後の扱いが未完である

- 所見: 抽象的な順位は決定的だが、raw outcome を `aborted` と `missing` のどちらへ写すかが全域関数になっていない。「fresh な terminal outcome」も機械述語ではない。`analysis_invalid` を最終的に判定不能、protocol violation、再入力のどれへ倒すかも未定である。
- 根拠: `s2-plan.md:primary outcome の純関数`。`preregistration-snapshot.md:§7.1` は停止理由、crash、protocol violation を削除せず報告すると定める。
- 成立条件: report 作成者が raw record を再分類または再入力できる場合。
- 提案: raw event ごとの全域 mapping、terminal receipt の選択規則、block id の型と順序を固定する。入力不正は元行を保持したまま、実験全体を事前固定した分類へ一意に倒す。

### C4. reject の fitness 利用は抽象定義上は防げているが、adapter まで閉じなければ保証にならない

- 所見: `certified` 以外の `fitness_tps=null`、certified が常に非 certified より上という規則は、§4 の正しさ境界を緩めていない。問題は raw からこの型を作る経路である。
- 根拠: `preregistration-snapshot.md:§4` の「reject に fitness を付けない」。plan は非 certified の fitness を `null` と要求する。
- 成立条件: raw reject に性能値が存在しても adapter が黙って捨てる、または status を certified に読み替えられる場合。
- 提案: raw 非 certified に性能値があれば行除外ではなく protocol violation とする。verdict と fitness の出所 receipt を hash で束縛する。

### C5. Q3: `A_min=0.60` の方が主張には適合するが、独立な出所はまだ証明されていない

- 所見: 二案では `0.60` を推す。この実験の主張は「次の synthesis が良くなる」という機序主張であり、「大効果」を主張していない。`0.71` は net win が 42 percentage point に達する水準で、慣用的な大効果分類をこの estimand の重要性へ流用することになる。`0.60` は net win 20 percentage point で、機序証拠の最低線としてより整合する。
- 根拠: `preregistration-snapshot.md:§2.1` の狭い機序主張。§9 の既知結果は on 相当だけで、paired `A` は計算できない。plan は `0.60` を提示するが、値の外部根拠や選定履歴を示していない。
- 成立条件: `0.60` が n や予算を見て選ばれた場合、または既知結果を見た人物の裁量だけで選ばれた場合。
- 提案: `0.60` はユーザー裁定で明示確定し、「既知結果、pilot、算出された n、予算を入力にしていない」という選定根拠を同じ変更に残す。

n の実行可能性を見て `A_min` を選ぶことは、D1082 の導出方向を逆転させる。pilot 由来の n を見た場合は直接の pilot 独立性違反である。最悪分散で計算した n を見た場合も、pilot 違反という狭い名称を外れてなお、重要性を実行可能性へ合わせる恒真化であり不可である。

### C6. Q4: pilot は不要であり、残す利益より選択自由度の方が大きい

- 所見: D1082 は pilot の使用を許しているので、pilot が存在するだけで裁定違反とは言えない。しかしこの設計では pilot を削る方が拘束力が高い。
- 根拠: `X_i` は `{0, 1/2, 1}` なので分散は常に `1/4` 以下。plan の式では、pilot の隣接 10 pair が全て同値の場合だけ `v_upper` が約 `0.2399` へ下がり、1 pair でも差があればほぼ `1/4` に cap される。block id の付け方が未束縛なら、この隣接 pair 自体も操作点になる。
- 成立条件: pilot 割当、block id、実行順のどれかを pilot outcome 後に変えられる場合。
- 提案: `v_upper=1/4` を固定し、pilot を廃止する。plan の normal approximation をそのまま使う場合、`A_min=0.60` なら `n=155`、`A_min=0.71` なら `n=36` となる。ただしこれは exact label-swap test の 80% power を証明する値ではない。採用前に、凍結した代替分布または保守的な power 定義との整合を検証する必要がある。

## 整合・実効性の所見

### E1. Q1: driver と軸が未確定であることは D1082 後に判明した新事実ではない

- 所見: 新事実ではない。D1060 が sanctioned CLI 不在という機械的理由を既に逐語で記録し、その後の D1082 が一括凍結を裁定している。裁定者がこの制約を知ったうえで、別々の時期の裁量凍結を禁じたと読むのが自然である。
- 根拠: `D1060.md` の「その条件を満たす sanctioned CLI が存在しない」と、`D1082.md` の「4 項目を一括で凍結する」。
- 成立条件: plan が D1060 と同じ既知事実だけを理由に D1082 の実施を拒む場合。
- 提案: 「着地させない」という plan の総括は退ける。未確定 driver を引数に取るだけの曖昧な族ではなく、driver の機械選択規則まで含む全域関数として凍結する。

### E2. Q2: 閉じた規則の後で manifest bytes を機械具体化することは、別時期の裁量凍結には当たらない

- 所見: 当たらない。ただし後の変更が「値の手入力」ではなく、先に凍結した関数の一意な出力であることが必要である。
- 根拠: D1082 自身が pilot から n を後で導出する形を許している。したがって「裁量の凍結」と「機械出力の materialize」を区別しなければ、D1082 は内部的に実現不能になる。
- 成立条件: source registry の hash、生成器、完全性 checker、canonical 順序が同じ凍結単位に入り、後の manifest が再生成結果と exact equality になる場合。
- 提案: manifest の削除、追加、並べ替え、driver の手動差替えは全て `design_not_feasible` にする。manifest hash を記録するだけでは不足で、source registry との完全一致検査を必須にする。

### E3. bare な節参照は ancestry を空洞化する

- 所見: 同一 commit 内の完成した参照先なら ancestry で束縛できるが、P3 の bare 参照だけでは不十分である。現 checker は参照先の存在、型、意味、hash を検査しない。
- 根拠: `admission-section5-contract.py.txt:assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel` の docstring は、検査対象を「source cells and three values, not types or rendered meaning」と限定する。`preregistration-snapshot.md:§1` 自身も空欄版を祖先に持つだけの空洞化を警告する。
- 成立条件: sentinel を節名へ置換した後、参照先や実装を別 commit で変更できる場合。
- 提案: 各セルに少なくとも定義 hash を持たせる。母集合は manifest hash と件数、n は数値と単位と導出契約 hash、primary は実装 path と code hash を記録し、admission consumer が検証する。実走成果物は最終発効 commit を記録し、初期 draft の祖先性だけでは受理しない。

### E4. P1 の実装面ゼロは凍結の実効性を落とす

- 所見: consumer がまだ無いことは、実装を後回しにする理由にならない。結果を見る前に adapter、完全性検査、primary 関数を固定することが本作業の目的である。
- 根拠: snapshot §7.2 は file-drawer、pair 完全性、receipt shopping が未強制と明記する。さらに plan は `2^n` 全列挙を要求するが、`n=155` なら直接列挙は実行不能である。
- 成立条件: 実装が pilot または正式結果の後に書かれる場合。
- 提案: 同じ変更単位に、raw-to-status adapter、manifest 完全性検査、primary outcome、n 導出、exact test の同値な動的計数実装と conformance fixture を含める。

### E5. D1082 は値や順位の内容まで裁定していない

- 所見: plan は `A_min=0.60`、pilot 20、alpha、power、片側検定、status 順位、欠測順位、`analysis_invalid` を新たに決めている。D1060 は tie、欠測、非 certified の順位を明示的に裁定へ返しており、D1082 は凍結時期と依存方向だけを決めたと読むべきである。
- 根拠: `D1060.md:却下した選択肢`、`D1082.md:決定`。
- 成立条件: 段 4 の明示裁定なしに plan の草案を本文へ入れる場合。
- 提案: これらを裁定対象として明示し、承認後に一括反映する。§10 の probe、proposal 因果束縛、pair 完全性が解決済みであるとは書かない。

### E6. P4 は fail-closed だが §0 と文字どおりには整合しない

- 所見: `実行責任者=thawk105; 開始時刻=未記入` は admission を閉じる点では正しい。一方、§0 の「未記入の欄には placeholder 語だけを置く」とは衝突する。
- 根拠: `preregistration-snapshot.md:§0` と plan の複合セル。親 brief と機械契約は `未記入` の部分一致拒否を前提にする。
- 成立条件: 行を一つの「欄」と解釈する場合。
- 提案: §0 に、この複合行だけは固定書式による部分記入を許す例外を明記する。条件文をセルへ入れず、開始時刻が決まるまで fail-closed を維持する。

## 親 brief P1-P6 への反証

- P1「実装面ゼロ」: 反証する。現在 consumer が無いからこそ、結果前に実装と conformance を固定すべきである。docs だけでは input adapter と manifest 完全性が自由なまま残る。

- P2「§5.2 に置く」: 反証する。§0 は規範の置き場を §5.1 と §7 に限定する。§5.1 配下へ置くか、§0 自体を明示変更する必要がある。

- P3「3 セルは定義への参照だけ」: そのままでは反証する。参照先の same-commit hash と意味検査があれば成立し得るが、現 checker にその能力はない。

- P4「責任者と未記入時刻の複合セル」: 正しさ上は反証できない。sentinel により fail-closed になる。ただし §0 との整合修正が必要である。

- P5「効果尺度は確率優越 A」: 尺度については反証できない。ordinal な correctness-first outcome と整合する。ただし具体値 `0.60` は未裁定で、出所の記録が要る。

- P6「数値 n は今は確定できない」: 方法上の主張は反証する。最悪分散 `1/4` を使えば pilot なしで数値化できる。現時点で未確定なのは `A_min` と妥当な power 定義であって、pilot が必須だからではない。導出関数と block 単位を凍結する部分は D1082 と整合する。

## 反証できなかった点

- plan の n 式は、式面だけを見れば pilot 平均、観測 `A`、status 比率などを引数から排除しており、`A_min` を pilot から導出する恒真化にはなっていない。
- D1082 は pilot が n と分散上限へ影響すること自体を明示的に許している。完全に事前固定された割当なら、pilot 使用だけを裁定違反とは言えない。
- 抽象化後の順位規則は決定的であり、certified を非 certified より下へ倒さず、reject に fitness を付けない。
- 入力件数不一致や precursor hash 不一致を行削除ではなく `analysis_invalid` にする方向は、§7.1 の全件報告と整合する。
- 完成した参照先を同一 document commit に含め、実走がその exact commit を記録するなら、節参照それ自体が必ず ancestry を破るわけではない。
- §9 の既知結果だけから paired `A=0.60` を逆算した証拠は見つからなかった。ただし独立な値であることを示す積極的な provenance もない。
- 対象 driver と軸が現在未確定であるという plan の事実認定自体は正しい。反証したのは、それを D1082 不実施の理由にした結論である。

## 総括

段 2 plan の「D1082 の差分はまだ着地させない」は採れない。driver と軸を埋められない理由は D1060 時点で既知であり、その後に D1082 が一括凍結を命じている。閉じた規則と後日の機械 manifest 具体化を区別すべきである。

ただし親 brief の P1 と P3、および plan の primary 草案も、そのままでは形だけの凍結になる。安全な着地点は、同じ変更単位で母集合の全域規則、独立に裁定した `A_min`、pilot なしの保守的 n 契約、raw bytes から始まる executable primary function、完全性 checker を固定する形である。後から許されるのは、その契約が一意に生成した manifest と数値を記入することだけである。

§5.1 と §10 の未了機構は未了のまま保持し、最終発効 commit が記録されるまで admission と実走を閉じる必要がある。