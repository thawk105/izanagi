## 前提の確認

指定された 8 資料を全て末尾まで読めた。Web 検索、書き込み、pytest、checker の再実行は行っていない。親が報告したテスト結果を緑として再主張しない。

算術と二項尾確率は独立に再計算した。結論は、`155` という算術自体は正しいが、現在の検定・成立規則・母集合契約を合わせると統計契約はまだ主張を支えない、である。

## must-fix

### 1. `n = 155` は最終的な成立規則の検出力 0.80 を与えない

- 所見: 計算式の算術は正しい。しかし正規近似が対象にする平均検定と、実際の「厳密符号検定かつ `A >= 0.60`」という成立規則は一致しない。
- 根拠: 式の未丸め値は `154.56393080049415` なので ceil は `155`。一方、tie なし、真の `A = 0.60` という最も単純な場合、片側符号検定の棄却域は `W >= 89`、実サイズは `0.038437986`、検出力は `0.770390461` である。さらに判定規則が標本値 `A_hat >= 0.60` も要求するなら `W >= 93` が必要になり、成立確率は `0.534813919` まで落ちる。もし判定規則の `A` が母数を指すなら、そもそも観測値から直接判定できない。また `Var(X) <= 1/4` だけでは `Var(mean X) <= 1/(4n)` にならず、block 間独立性または共分散契約が必要である。
- 成果物影響: 真に `A = 0.60` の実験でも約 46.5%が判定不能となり、レポートと台帳の「成立」集合が目標検出力から大幅に縮む。
- 具体的な修正案: `A` と `A_hat` を区別し、検出力を最終判定関数そのものについて exact に計算する。`A_min` を power 計算上の対立値とするなら `A_hat >= A_min` gate を外すか別の記述的条件にする。母数が `0.60` 以上であることを成立条件にするなら、帰無境界を `0.60`、対立値をそれより大きい値として固定し、片側信頼下限または対応する exact test で n を再設計する。block 間の独立性、または cluster 単位も明記する。

### 2. 厳密符号検定の二項帰無分布には、文書にない強い交換可能性が必要

- 所見: tie を除けば二項分布になるという組合せ上の説明は、各 block を独立に確率 1/2 で交換できる強い帰無仮説の下でだけ正しい。estimand の弱い帰無 `A = 0.50` からは導けない。
- 根拠: 反例として、tie のない 2 block で on 勝率をそれぞれ `0.9` と `0.1` とする。均等に block を選ぶ estimand は `A = 0.50` だが、独立な勝数 `W` の分布は `(0,1,2) = (0.09,0.82,0.09)` であり、`Binomial(2,0.5) = (0.25,0.50,0.25)` ではない。現在の文書は block 内のランダムな arm 割当、独立な実行順割当、または block ごとの sharp null を固定していない。
- 成果物影響: 二項 p 値が実際の帰無分布より小さくなり、成立として受理される block 集合と集約レポートが変わりうる。
- 具体的な修正案: 帰無仮説を逐語で固定する。推奨は、各 block の複製実行 slot への on/off 割当と実行順を独立な 1対1 ランダム化で事前生成し、その schedule hash を manifest に束縛すること。その強い交換可能性が成立しないなら、弱い平均帰無に有効な検定へ変更する。なお、強い交換可能性を仮定すれば tie は交換で不変なので、非 tie 数 `m` 上の符号検定との同値性自体は正しい。

### 3. 「不成立」の分岐は現在の片側 p 値では到達不能

- 所見: on 優越の上側片側 p 値を使いながら、「p が 0.05 以下かつ `A < 0.50`」を不成立条件にしている。この条件は符号検定では成立しない。
- 根拠: `A < 0.50` なら非 tie 中の on 勝数は中央より下にあり、上側尾確率は大きくなる。強い逆向き効果でも上側 p 値は 0.05 以下にならない。
- 成果物影響: off が明確に優越する結果も全て判定不能となり、レポートと台帳の「不成立」集合が空になる。
- 具体的な修正案: `p_on` を上側尾、`p_off` を下側尾として別々に定義する。両方向を正式分類に使うなら、exact な両側検定を用いて符号で方向を決めるか、両尾への alpha 配分を事前固定する。単純に両尾を各 0.05 とすると全体サイズが増えるため不可。

### 4. 4 分類の判定関数が全域でなく、分類名も §7.1 と一致しない

- 所見: `analysis_invalid` の最終分類がない。per-arm の `treatment_fired` を block 単位でどう集約するかも未定義で、`protocol_status` の値域もない。また protocol violation を優先検出しながら実験全体を「判定不能」とするため、§7.1 の独立した「protocol violation」分類が実験レベルでは消える。
- 根拠: 入力にはアームごとの boolean と `protocol_status` があるが、判定規則は単数の `treatment_fired` と「protocol violation がある」を参照するだけである。重複 ID、hash 不一致、型違反は出力無効になるが、その後の扱いがない。非 tie 数 `m = 0` の p 値規約もない。
- 成果物影響: 同じ raw record が実装者の解釈により成立、判定不能、protocol violation の別々の台帳行へ写りうる。
- 具体的な修正案: block status と実験 verdict を分離した全域関数を置く。enum、raw からの写像、`treatment_fired` の arm 別期待値、invalid input、`m = 0` を全て定義する。実験 verdict を4分類にするなら、最優先の違反は `protocol violation` と返す。判定不能へまとめるなら、§7.1 を3分類の実験 verdictと行単位の violation flag に書き換える。

### 5. 母集合規則はまだ一意な出力を定めず、D1082 の一括凍結を満たさない

- 所見: 母集合セルを `未記入` に残すことだけが問題なのではない。§5.1.1 の規則自体が、後で決まる driver、軸、`PerfConfig`、bootstrap 集合、attempt 数、source registry、生成器を自由入力にしており、現在は一つの母集合でなく母集合の族である。
- 根拠: driver 候補集合と選択関数は将来の別 commit、workload は将来校正される `PerfConfig`、初期 proposal は「事前に固定した集合」としか書かれず、予定 attempt の件数も固定されていない。生成器と source registry は「再生成できなければならない」だけで path、blob、hash がない。この状態で「4項目の規則と値を同じ変更単位で凍結した」とする §5.1.1 と §9 の宣言は成立しない。
- 成果物影響: 後から driver、workload、bootstrap、attempt 数を選ぶことで manifest の行集合と primary の受理集合を結果に都合よく変更できる。
- 具体的な修正案: 母集合セルには、例えば `population_spec=<path>; spec_sha256=<64hex>; source_registry_sha256=<64hex>; generator_blob=<git-blob>; expected_analysis_rows=155` のような実在する固定値を書く。その spec に候補 driver 集合、exact probe、0件・複数件規則、`PerfConfig` hash、bootstrap bytes、seed、model/prompt、attempt 数、canonical 順序を内包させ、consumer が manifest との exact equality を検査する。これらの実値を今書けないなら、セルを `未記入` に保つこと自体は正直だが、D1082 履行済み・一括凍結済みとは書けない。

### 6. 「全 manifest 行」「screening 除外」「全 attempt 保持」と n の関係が矛盾する

- 所見: 母集合を manifest の全行と定義する一方、screening-only は母集合に入れず、生成失敗・非再現・重複・破損を含む全予定 attempt は manifest に残すとしている。さらに manifest が155行を超えた場合の分析対象選択がない。
- 根拠: `preregistration-after.md` 234-253 行では同じ manifest が、母集合、除外後の赤 precursor、全 attempt 台帳という3役を担う。§7.1 は treatment 未発火も全件報告する。純関数は block 数が n と違えば無効なので、156行以上でも154行以下でもそのままでは解析不能になる。
- 成果物影響: screening-only、生成失敗、重複、余剰行を含める解釈では有効 n と A が変わり、除外する解釈ではレポートと台帳の行集合が変わる。
- 具体的な修正案: `scheduled_attempt_registry` と `analysis_manifest` を分離する。全 attempt は前者へ必ず残し、screening-only 等には固定 enum の理由を付ける。後者は事前固定した eligibility predicate と canonical 順序から決定する。最大 attempt 数と「先頭155 eligible 行」などの選択関数を結果前に固定し、155未満なら `design_not_feasible`、余剰行も registry では全件報告とする。

### 7. `precursor_reference_tps` が存在しない場合と、その参照先の一意性が未定義

- 所見: 赤 precursor 自身は rejected なので certified ではない。共通 certified parent を参照する設計は両アーム共通基準としては整合しうるが、その ancestor がない、複数候補がある、同じ workload/env の有効 TPS receipt がない場合の処理がない。
- 根拠: 入力型は正の値を要求するだけで、どの snapshot hash と throughput receipt から導くかを束縛していない。型違反時は出力無効になるが、最終分類は未定義である。後から遠い ancestor を選ぶと floor による tie 境界も変わる。
- 成果物影響: 参照 ancestor の選択または欠測時の代替によって certified 同士の tie、block score、A、最終受理が変わる。
- 具体的な修正案: 各 manifest 行に `reference_snapshot_hash`、throughput receipt hash、`PerfConfig`、`env_tag` を固定し、「赤 precursor の直前にある最も近い certified ancestor」など一意な選択関数を定義する。0件・複数件・receipt 不一致は行削除や arm 別基準への変更をせず、実走前 `design_not_feasible` または固定済みの protocol classification に倒す。

### 8. 非 certified の順位規則が自己矛盾している

- 所見: 番号付き順位では `rejected/aborted > missing` だが、直後に「非 certified 同士は常に tie」と書いている。`missing` も status 上は非 certified なので両方を同時には満たせない。
- 根拠: `preregistration-after.md` 304-312 行。番号付き規則では rejected 対 missing は勝敗、文章どおりなら tie になる。
- 成果物影響: rejected 対 missing の block score が `0/1` と `1/2` の間で変わり、A、p 値、成立集合が変わる。
- 具体的な修正案: 「観測済み非 certified である `rejected` と `aborted` の間だけ常に tie」と限定し、`missing` はその集合に含めないと逐語で書く。

## nit

- なし。上記はいずれもレポート、台帳、受理集合の少なくとも一つを変更するため nit ではない。

## 反証できなかった点

- `X` が `{0, 1/2, 1}` に限られるなら、単一 block score の分散上限が `1/4` であることは正しい。
- 正規近似式の算術結果が `155` であることは正しい。
- 強い block 内交換可能性と独立な一様 label swap を仮定すれば、tie は swap で不変であり、非 tie 数 `m` 上の厳密符号検定は全 label-swap 分布と一致する。
- `A = 0.60` が net win 20 percentage point に相当する説明は正しい。
- screening-only の除外理由は treatment の定義単体とは整合する。問題は全 attempt を同じ manifest の全行とした bookkeeping との衝突である。
- protocol violation 1件で成立を禁止すること自体は、厳しいが保守的な事前規則として妥当であり、成立を不当に得る経路ではない。違反が必ず生じる証拠もないため恒真な拒否とは反証できない。
- certified を非 certified より優先し、rejected/aborted の throughput を使わない中心規則には、正しさゲートの緩和や reject への fitness 付与は見つからなかった。
- 現 bytes が sentinel により fail-closed であるという親の報告は静的内容と整合する。ただし checker やテストは再実行していない。

## 総括

現差分はそのまま着地不可である。最大の問題は、`155` の丸めではなく、実際の成立規則に対する検出力が約 `0.535` にしかならないこと、符号検定の exact 性に必要な交換可能性が未契約であること、母集合がまだ後続判断へ依存していることである。

D1082 を満たすには、実在する population spec とその全入力を同じ変更単位で固定し、attempt registry と analysis manifest を分離したうえで、全域な4分類関数と実際の最終判定に対応する power 設計へ改める必要がある。