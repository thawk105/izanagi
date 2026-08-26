## 前提の確認

次の必読資料を全文読めた。

- 親 brief
- 対象文書 snapshot
- D1082
- D1060
- 実行責任者の裁定控え
- §5 固定表の機械契約抜粋

参考資料も読めた。

- `docs/phase3-8c-preregistration.md` の §5、§5.1 の先例
- `orchestrator/campaign/p3_b4_admission_record.py` のラベル、sentinel、表検査
- `orchestrator/campaign/p3_s4_loop.py` の outcome と `fitness_tps` の形
- repo 内の対象文書は snapshot と byte 一致した。

読めなかった資料はない。Web 検索、書き込み、pytest、その他の実測は行っていない。

結論を先に述べると、現時点では D1082 の 4 項目を正当に一括凍結する差分は着地できない。対象 driver と軸だけでなく、workload と初期 proposal の母集合・生成規則・抽出測度が未確定だからである。将来選ばれる `(driver, axis)` を引数にした `U(driver, axis)` は母集合の族であって、現在凍結された一つの母集合ではない。

## plan

対象ファイルは `docs/phase3-b4-reflux-ablation-preregistration.md` のみとする。

1. `## 5. 実走前に数値で埋める欄` の固定表では、以下を行う。

   - `赤 precursor の母集合 (workload・赤形状・初期 proposal)` は、具体的な母集合が得られるまで `未記入` のまま残す。将来値を参照するだけの文字列で埋めない。
   - `アームあたり block 数 n と検定単位` は、検定単位と導出関数を本文で凍結しても、数値 `n` が未導出なので `未記入` のまま残す。
   - `primary outcome の演算定義 (純関数)` は、本文が確定した変更単位で `§5.1.1「primary outcome の純関数」` へ差し替えられる。
   - `実行責任者・開始時刻` は `実行責任者=thawk105; 開始時刻=未記入` とする。開始時刻の sentinel により admission は閉じたままになる。

2. `### 5.1 欄別の解除条件` の最後の `開始時刻` bullet の後、`## 6. 実走の前提条件` の前に `#### 5.1.1 分析契約の一括凍結` を置く。

   `### 5.2` は採らない。§0 は規範の置き場を §5.1 と §7 に限定しているため、§5.2 に置くと規範性が曖昧になる。§5.1 配下なら §0 を変更せずに済む。

3. 母集合については、次が同じ変更単位で exact に固定できるまで着地を止める。

   - 対象 driver と軸
   - workload の canonical bytes
   - screening を除いた赤形状の閉じた集合
   - 初期 proposal の canonical bytes の有限集合、または結果非依存の完全な生成・抽出規則
   - precursor の共通 parent snapshot
   - pilot と正式標本の disjoint な割当規則
   - 母集合から block を抽出する確率測度または決定的順序
   - 母集合に不足がある場合を `design_not_feasible` に倒す規則

   最も堅い形は、対象確定後に precursor manifest の canonical bytes と hash を事前 commit し、その全行を母集合とする方式である。成功例だけを manifest に載せる経路を防ぐ生成・完全性規則も必要になる。

4. `## 9. 改訂時点の既知結果台帳` では、表の後にある「既知結果に informed された登録追試」の段落の直後、`## 10.` の前へ、D1082 凍結時点で新規 B-4 outcome を見ていない旨を追加する。

5. 静的検査では次を確認する。

   - `## 5.` と `### 5.1` の間は非空 12 行のまま。
   - 表ヘッダ、10 ラベル、行数を変更しない。
   - 値セルに `|` を入れない。
   - sentinel が残るため admission が期待どおり失敗する。
   - §5.1 の「対象 driver と軸」bullet、§7.2、§8、§10 は byte 非接触。
   - `docs/phase3-main-experiment.md` は全体を byte 非接触。

## 凍結本文の草案

母集合の逐語については、現在の資料だけからは正当なものを書けない。例えば「選択された driver と軸に適合する全 precursor」と書く案は、将来の target 選択によって母集合を狭められるため不可である。「事前 manifest の全行」と書く案も、manifest の生成規則と hash が無い現在は空の参照になる。

したがって、以下は母集合が exact に確定した後、同じ変更単位へ組み込むための逐語草案であり、現状のまま部分着地させてはならない。

表の到達形は次のとおり。

```markdown
|赤 precursor の母集合 (workload・赤形状・初期 proposal)|§5.1.1「赤 precursor の母集合」|
|アームあたり block 数 n と検定単位|未記入|
|primary outcome の演算定義 (純関数)|§5.1.1「primary outcome の純関数」|
|実行責任者・開始時刻|実行責任者=thawk105; 開始時刻=未記入|
```

`開始時刻` bullet の後、`## 6.` の前へ挿入する本文のうち、母集合以外は次で固定できる。

```markdown
#### 5.1.1 分析契約の一括凍結 (D1082)

##### 最小重要効果

最小重要効果は確率優越 `A_min = 0.60` とする。単位は無次元、尺度は `[0, 1]`、大きいほど
on が良い。差なしは `A = 0.50` であり、検出対象の差は `delta = 0.10` である。
`A = 0.60` は、tie を半分ずつ数えた後で on の勝ち率が off の勝ち率を 20 percentage point
上回ることに等しい。この差より小さい改善は B-4 の機序証拠として重要と扱わない。

この値は pilot の平均、観測された `A`、status 構成、赤形状の頻度、欠測率、分散、対象 driver、
対象軸のいずれも入力にせず、pilot より前に固定する。pilot の結果を理由に `A_min` を上下させない。

##### primary outcome の純関数

入力型を次で固定する。

- `CanonicalDecimal` は、符号と指数表記を持たない有限の 10 進文字列であり、10 進有理数として
  exact に解釈する。
- `ArmObservation` は
  `status in {certified, rejected, aborted, missing}` と
  `fitness_tps: CanonicalDecimal or null` の組である。
  `certified` のときだけ `fitness_tps` を有限の正として要求し、その他では `null` を要求する。
  `duplicate`、`dry-pass`、`stopped-before`、crash、および fresh な terminal outcome が無い場合は
  `missing` へ写す。行自体を削除しない。
- `Block` は `block_id`、共通の `precursor_hash`、正の `precursor_reference_tps`、
  `on: ArmObservation`、`off: ArmObservation` を持つ。
  `precursor_reference_tps` は、赤を生じた proposal 自身ではなく、両アームが分岐する直前の
  共通 certified parent snapshot の session-level `fitness_tps` とする。arm 内前後の別々の
  参照点を使わない。
- `AnalysisInput` は、正の整数 `expected_n`、`floor_fraction: CanonicalDecimal`、
  `Block` の tuple を持つ。`floor_fraction` は `[0, 1)` とし、全 block に同じ値を使う。

各 arm の順位を次で固定する。

1. `certified`
2. `rejected` と `aborted`
3. `missing`

`rejected` と `aborted` は互いに tie とする。`missing` はすべての観測済み非 certified より下とする。
`certified` は性能値にかかわらず、すべての非 certified より上とする。

両 arm が `certified` の block では、
`gain_arm = fitness_tps_arm / precursor_reference_tps - 1` とする。
`abs(gain_on - gain_off) <= floor_fraction` なら tie とし、それ以外は `gain` が大きい arm を上位とする。
境界値は tie に含める。両 arm が非 certified の場合は上の固定順位だけを使う。

block score `X_i` は、on が上位なら `1`、tie なら `1/2`、off が上位なら `0` とする。
出力型 `PrimaryOutcome` は、`block_id` 順の `X_i` の tuple と、
`A_num = sum(2 * X_i)`、`A_den = 2 * expected_n`、`A = A_num / A_den` の exact な有理数である。
入力 block 数が `expected_n` と異なる、`block_id` が重複する、型条件に違反する、または
on/off が同じ `precursor_hash` に束縛されていない場合は、行を除外せず出力全体を
`analysis_invalid` とする。

確率優越 `A` は、母集合から事前規則どおりに選ばれた一つの block について、
`P(on が上位) + 1/2 * P(tie)` と定義する。標本推定値は上記の `A_num / A_den` である。
同じ入力 bytes から常に同じ値が出る。filesystem、時刻、環境変数、乱数、network、model、
pilot、global state のいずれも参照しない。

##### n の導出と検定単位

検定単位は block とする。一つの block 内の on/off は同じ precursor に対する pair であり、
iteration や session 内 rep を独立な検定単位へ昇格させない。

帰無仮説は arm label の block 内交換可能性、対立仮説は on 優越の片側とする。
各 block 内で on/off label を入れ替える `2^n` 通りを全列挙し、
`T = sum(2 * X_i)` について `T_perm >= T_observed` を tail に含める exact paired
label-swap test を用いる。有意水準は片側 `alpha = 0.05`、目標検出力は
`1 - beta = 0.80` とする。primary comparison は一つなので、現行の B-4 family では
Holm 補正後の値は未補正値と同じである。成立には補正後 `p <= 0.05` と
`A >= A_min` の両方を要求する。

pilot は正式標本と重ならない事前割当 20 block とし、block score `X_1, ..., X_20` だけを
分散上限の導出へ使う。pilot block は事前割当 `block_id` 順に並べ、`k = 10` として
`Y_j = (X_(2j-1) - X_(2j))^2 / 2` を作る。99% の分布非依存上側境界を

`v_upper = min(1/4, mean(Y_j) + (1/2) * sqrt(ln(100) / (2 * k)))`

と固定する。pilot が 20 block を満たさない、正式標本と重なる、または純関数が
`analysis_invalid` を返す場合は `n` を導出せず `design_not_feasible` とする。

`z_0.95 = 1.6448536269514722`、`z_0.80 = 0.8416212335729143` とし、

`n0 = max(5, ceil(((z_0.95 + z_0.80)^2 * v_upper) / (0.10^2)))`

を、`A = 0.50` に対して `A = 0.60` を検出する prospective normal approximation による
必要 block 数とする。凍結済み母集合から pilot と重ならない相異なる block を `n0` 件確保できる
場合だけ `n = n0` とする。確保できない場合は `n` を予算に合わせて切り下げず、
`design_not_feasible` とし、実走するなら事前に記述統計限定へ変更する。

`n` の関数引数に pilot の平均、pilot で観測した `A`、効果方向、status 比率、欠測率、
赤形状別の成績、driver・軸の選択、順位規則、tie 規則を入れない。
pilot が影響できるのは上式の `v_upper` と、それから導かれる `n` だけである。
数値 `n` を導出して §5 の値セルへ記入し、その版を commit するまで同セルの `未記入` を消さない。
```

§9 へ挿入する逐語は次でよい。

```markdown
**2026-08-27 の D1082 分析契約凍結時点:** 上表の 2 件以外に、新たな B-4 の next synthesis、
primary outcome、secondary outcome は生成も閲覧もしていない。分析用 pilot もまだ実施していない。
```

## 機械契約への適合

### 条件

- active な `## 5.` と `### 5.1` はそれぞれ exactly 1 件で、前者が先。
- 両見出しとその間に fenced code または HTML comment が無い。
- 両見出し間の非空行は exactly 12 行。
- 先頭 2 行は逐語で次と一致する。

```markdown
|欄|値|
|---|---|
```

- 各データ行は `|` で始まり `|` で終わり、中身を `|` で分割したセル数が exactly 2。
- 値セル内の `|` は不可。
- label と value は strip 後に NFKC 正規化され、default-ignorable または `Cf` 文字を含めない。
- label の重複は不可。
- label の exact 集合は次の 10 件。

  1. `対象 driver と軸`
  2. `赤 precursor の母集合 (workload・赤形状・初期 proposal)`
  3. `アームあたり block 数 n と検定単位`
  4. `primary outcome の演算定義 (純関数)`
  5. `floor (対象動作点で再実測した between-run floor) の artifact パスと hash`
  6. `校正済み `PerfConfig` (records / threads / reps / extime) の artifact パスと hash`
  7. `総計測予算 (role query 数・build/verify/bench admission 数・累積 bench 秒) と arm ごとの上限`
  8. `env_tag (実測環境)`
  9. `model snapshot / prompt hash / projection hash`
  10. `実行責任者・開始時刻`

- 全 value は非空で、NFKC 正規化後に予約 sentinel を含まないことが admission 成功条件。
- 部分一致で拒否される sentinel は `未記入`、`要記入`、独立語の `TBD`、`TODO`、`FIXME`、`PLACEHOLDER`、`N/A`、`NA`。Latin sentinel は大文字小文字を区別しない。
- value 全体が `x`、`-`、`--`、`---`、`—`、`…`、`...` のいずれかでも拒否。
- model 行は sentinel 解消後、model 名と 2 個の lower-case SHA-256 を持つ専用正規表現への full match と、外部 expected 値との一致も必要。

### 提案差分の判定

- 非空行数: **PASS**。表はヘッダ 2 行とデータ 10 行のまま。挿入節は `### 5.1` の後なので計数範囲外。
- ヘッダ exact 一致: **PASS**。変更しない。
- label exact 集合: **PASS**。label を一文字も変更しない。
- 各行 2 セル: **PASS**。提案 value に `|` は無い。
- default-ignorable、format 文字: **PASS**。提案 value には含めない。
- sentinel-free admission: **FAIL、意図どおり**。未確定欄に加え、実行責任者の複合セルにも `開始時刻=未記入` が残る。
- admission の fail-closed: **PASS**。checker は複合セル内の `未記入` も部分一致で拒否するため、責任者だけ埋めても実走許可にはならない。
- model expectation 行: **未到達、意図どおり**。同セルは `未記入` のままであり、その前段で admission が拒否される。

したがって固定表の構造契約は破らず、文書全体の admission は閉じたままになる。

## 親の裁定 P1-P6 への判定

|裁定|判定|理由|
|---|---|---|
|P1 実装面ゼロ|採る|対象は docs 1 ファイルに限定され、現時点では正式 B-4 consumer も無い。Python 実装を足すと scope を越える。ただし prose の純関数は機械強制されないため、実走前には conformance consumer が別途必要。|
|P2 最小重要効果を表外の §5.2 に置く|採らない|表外に置く点は正しいが、§0 が規範を §5.1 と §7 に限定している。§5.1 配下の `#### 5.1.1` に置く。|
|P3 3 セルを定義参照で埋める|採らない|primary は参照でよい。母集合は未確定なので不可。`n` は導出関数を本文で凍結しても数値未導出であり、参照だけで埋めると checker が「n 記入済み」と誤認する。|
|P4 責任者だけ埋め、開始時刻 sentinel を残す|採る|`未記入` はセル内部分一致でも拒否される。構造検査を通しつつ admission を閉じる exact な fail-closed になる。|
|P5 最小重要効果を確率優越 A で固定|採る|primary 自身が ordinal な paired outcome なので同じ尺度で固定できる。値は `A_min=0.60`、無次元、高いほど on 優越とする。|
|P6 数値 n でなく導出関数と block 単位を凍結|採る|D1082 と現 §5.1 に整合する。ただし数値 `n` のセルは pilot 後まで sentinel のままにする。|

## 残る恒真化・空洞化の余地

- 最大の blocker は母集合である。将来の `(driver, axis)`、workload、proposal manifest を参照するだけでは、母集合を後から選べる。
- manifest を導入しても、その manifest の生成・完全性 consumer が無ければ成功例だけを載せられる。
- T1912 相当の pair 完全性、precursor hash、on/off receipt、proposal、block id の機械束縛は未実装である。receipt shopping が残る。
- 純関数は prose のみであり、raw outcome から `ArmObservation` への adapter を別実装にすれば順位を変えられる。
- `floor_fraction` は将来値である。floor campaign の選択や artifact 差し替えが閉じていなければ certified 同士の tie を動かせる。
- missing を最下位に固定しても、arm 依存の crash や欠測は因果効果と運用障害を混ぜる。規則を後から選ぶ余地は閉じるが、解釈上の問題は残る。
- certified を常に非 certified より上としたため、極端に遅い certified も reject より上になる。これは正しさ優先の明示的選択であり、性能だけの優越とは読めない。
- exact label-swap test の exact 性は、block 内 arm label の交換可能性と pair の完全性に依存する。現状はその割当 consumer が無い。
- pilot の 20 block 固定、正式標本との非重複、事前 `block_id` 順は文書規範に留まり、機械束縛されない。
- `A_min=0.60` 未達でも p 値だけ有意になる場合があるため、成立判定には必ず両 gate を要求する必要がある。
- n の式は prospective normal approximation であり、exact test の検出力保証そのものではない。この限定を落とすと過大主張になる。
- §5 checker は値の型・意味・参照先の存在を検証しない。参照文字列だけで sentinel を消すと形式だけ発効できる。
- §7.2 が記す file-drawer、off 汚染、pair 不完全性は、この docs 差分では閉じない。
- 既知の on 相当結果 2 件を見た後の設計である。§9 の「informed された登録追試」という限定は維持しなければならない。

## 総括

現 checkout に対する安全な結論は、**D1082 の差分はまだ着地させない**である。母集合を具体的かつ後から狭められない形にできないまま、参照文字列で §5 を埋めると一括凍結が空洞化する。

先に対象 driver・軸、workload、初期 proposal の有限 manifest または完全な生成・抽出規則を確定し、その後、母集合・`A_min=0.60`・n 導出関数・primary 純関数を一つの変更単位で凍結する。その同じ差分で `thawk105` と §9 の未閲覧記録を入れる。数値 n と開始時刻を含む sentinel は、それぞれの正規の導出・決定まで残す。