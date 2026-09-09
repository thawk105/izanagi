## 対応表

ID は各レビュー内の出現順。レビュー所見自体はすべて `real` と独立判定した。

| ID | 元所見 | 対応 | 本体の逐語根拠と判定理由 |
|---|---|---|---|
| A-M1 | `U_flat` が強い低下も `indeterminate` にする | `closed` | [本体 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:286) が `saturated` を「`qhat_i <= 0` かつ `U_i <= 0.05`」、`declining` を「`L_i > 0.05`」とし、`U_flat` は「分類には使わない診断値」とした。 |
| A-M2 | aggregate verdict が排他的でない | `partial` | [本体 §4.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:338) に「上から順」「最初に当てはまった 1 つ」と優先順位は入った。しかし workload の `indeterminate` と `not-observed` の定義は重なりうる。新所見 3。 |
| A-M3 | 局所的な平坦 2 区間を飽和位置にする | `closed` | [本体 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:300) が「`I_j` から `I_6` まで全て `saturated`」を要求し、右で低下へ戻る局所平坦は位置にしない。ただし位置の添字に別の回帰がある。新所見 4。 |
| A-M4 | 全ゼロから正値への遷移が failure でない | `closed` | [本体 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:278) が「`qL` を経ずに直接 cohort を `invalid`」、[§7(14)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:916) も同じ入力を列挙した。 |
| A-M5 | correctness・欠測契約が弱い | `partial` | [本体 §4.6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:360) に counter、正 throughput、rep `0..4`、cell/genome/attempt 束縛が入った。一方、`correctness_mode` は「t2418 と同じ」としか固定されず、現実装にその field がない。新所見 6。 |
| A-M6 | 3 job の環境・source・toolchain 同一性がない | `closed` | [本体 §4.9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:393) が source digest、toolchain、環境契約、較正、3 hash、動作点を 3 lock 間で一致させ、不一致を `invalid` とした。 |
| A-M7 | provenance が自己申告 | `closed` | [本体 §4.8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:386) が「payload から読まず」「admitted WAL の envelope から導出」、trusted lock と厳密一致、とした。 |
| A-M8 | `spec_sha256` の対象 bytes が未定義 | `closed` | [本体 §8.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:943) が raw file bytes、marker 間、fence 除外、UTF-8、LF、末尾改行 1 個、非 canonical JSON を逐語で固定した。 |
| A-M9 | CV gate 0.02 が非前向き一覧から漏れる | `closed` | [本体 §0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:31) に「変動係数の品質 gate 0.02」、§5 に `"two-percent-cv-quality-gate-choice"` が入った。 |
| A-N1 | §6 の参考値が許容された精度根拠でない | `closed` | [本体 §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:879) が「参考値、非規範」「量子化された率から作った変動係数」「格子設計の説明にだけ使う」と限定した。 |
| A-N2 | 半オクターブの対数比レンジが狭い | `closed` | [本体 §4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:175) は `0.34642〜0.34673`。再計算範囲を包含する。 |
| A-N3 | 2000・4000 を外し再現性アンカーを失う | `closed` | [本体 §2.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:114) が「探索の再現性を検証する設計ではない」「比べられるのは 9999 だけ」と明記した。 |
| A-N4 | 左端の飽和位置が左打切り | `regressed` | [本体 §4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:184) は最左位置を 1768 とするが、[§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:300) の一般式は `j=1` で位置 `b_1`、直後は 1768 とする。位置と bracket が内部矛盾した。 |
| B-M1 | `indeterminate` を含む aggregate verdict が非排他 | `partial` | 優先順位は [本体 §4.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:328) に入ったが、§5 の workload 条件は `"all intervals classified"` と書き、`indeterminate` を排除していない。順序依存が残る。 |
| B-M2 | ゼロ境界と counter 定義域が total でない | `partial` | counter 範囲とゼロ→正値は閉じた。一方、[本体 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:283) の zero-dispersion は `indeterminate`、同節の [ゼロ規則](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:311) は両端全ゼロを `saturated` とし、同じ入力に二つの状態を与える。 |
| B-M3 | 必須契約違反が failure に写像されない | `partial` | provenance、動作点、順序、座標、対応は [本体 §7(15–17)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:917) に入った。ただし §4.2 で固定した `measurement_seed` 自体は §7 と spec の failure item にない。 |
| B-M4 | 正規化 field と実在 source path が結ばれない | `partial` | [本体 §5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:602) 自身が `"field_names_are_normalized_and_do_not_yet_exist"` とする。`throughput_tps_reps` は `"existing per-rep throughput values"`、binary は `"build stage record field"` までで exact stage/path/key がない。provenance 8 field のうち 5 field は `analysis_input_contract.fields` にも無い。 |
| B-N1 | 対数比レンジが狭い | `closed` | A-N2 と同じ。`0.34642〜0.34673` は再計算した `0.346422567〜0.346724613` を包含する。 |
| B-N2 | 11 分先例が correctness 5 rep と非同型 | `closed` | [本体 §4.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:225) が「1 cell あたり正しさ検査 1 回の実績」「約 20 分/job」と訂正した。 |

集計は `closed` 12、`partial` 6、`regressed` 1、`not-addressed` 0。

## 再計算

### 格子

§4.1 の `round(9999 / 2^(k/2))` を、正の 0.5 は大きい側へ丸めて再生成した。

| k | 丸め前 | 物理値 | raw |
|---:|---:|---:|---:|
| 6 | 1249.875000 | 1250 | 3250 |
| 5 | 1767.590176 | 1768 | 3768 |
| 4 | 2499.750000 | 2500 | 4500 |
| 3 | 3535.180353 | **3535** | 5535 |
| 2 | 4999.500000 | 5000 | 7000 |
| 1 | 7070.360705 | **7070** | 9070 |
| 0 | 9999.000000 | 9999 | 11999 |

したがって erratum 1 の結論どおり、本文の `3535 / 7070` が正しく、旧裁定 literal `3536 / 7071` は誤り。

§5 の 4 か所との照合結果はすべて一致した。

| §5 の箇所 | 期待値 | 判定 |
|---|---|---|
| `grid.formal_tail_values_us` | 1250, 1768, 2500, 3535, 5000, 7070, 9999 | 一致 |
| `grid.analysis_values_us` | 境界 1000 + 上記 7 点 | 一致 |
| `grid.encoded_static_points` | raw 3000, 3250, 3768, 4500, 5535, 7000, 9070, 11999 | 一致 |
| `binary_identity.physical_amounts_us` | 1000, 1250, 1768, 2500, 3535, 5000, 7070, 9999 | 一致 |

指定 seed で昇順 8 点を 1 回 shuffle した測定順も 3 workload とも全点一致した。

- write-heavy: `2500, 3535, 1250, 1000, 1768, 9999, 5000, 7070`
- balanced: `1250, 5000, 1000, 7070, 3535, 1768, 2500, 9999`
- read-heavy: `3535, 1250, 7070, 2500, 1768, 5000, 9999, 1000`

### 多重度と検出力

18 区間それぞれで `qL` と `qU` の 2 本を使うため、36 の片側限界という計数は正しい。片側確率は `0.05/36 = 0.001388888889`。自由度 8 では、

- `t(1 - 0.05/36, 8) = 4.25564232`
- tail の実際の `h` 範囲: `0.346422567〜0.346724613`
- `CV=0.006151493748` を両端へ置いた `U_flat`: `3.2557〜3.2585%`
- 旧短区間 8000→8944: `9.7772%`
- 旧短区間 8944→9999: `9.7805%`

よって [本体 §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:879) の自由度 8、`t=4.2556`、半オクターブ 3.26%、短区間 9.78% はすべて一致する。

有限な正値区間では `qL <= qU` なので `U >= L`。したがって `U <= 0.05` と `L > 0.05` は同時成立せず、通常区間の `saturated` と `declining` は排他的である。

### 探索値

生 rep の算術平均から倍増あたり低下率 `1 - exp(qhat log(2))` を再計算した。

| workload | 区間 | 点推定 |
|---|---|---:|
| write-heavy | 2000→4000 | 32.2867% |
| write-heavy | 4000→9999 | 34.1552% |
| balanced | 2000→4000 | 33.4821% |
| balanced | 4000→9999 | 37.0730% |
| read-heavy | 2000→4000 | 29.7998% |
| read-heavy | 4000→9999 | 30.4222% |

範囲は **29.7998〜37.0730%**。したがって [本体 §2.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:100) の `29.8〜37.1%` は正しい。

生配列からの最大 sample CV も、abort が `0.00615149374828`、throughput が `0.00650835780708` で、§5 の値と一致した。

### 失敗条件と探索走

散文は 18 項、§5 は 23 item だが、機械 spec が散文の複合項を分割した差である。散文 13 を 4 item、15 を 2 item、trace binary 取り違えを独立 item にしており、数だけの不一致は `refuted`。

探索走を formal 入力へ当てると、少なくとも「正しさ 5 rep 不足」「整数 counter 不在」「探索標本混入」「run kind/provenance 不一致」「格子・順序不一致」「correctness mode 不在」が発火する。これは探索の再利用を拒否する意図どおりであり、回帰ではない。

## 新しい所見

### [real] [must-fix] 両端全ゼロが `indeterminate` と `saturated` の双方になる

[本体 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:283) は `v_i + v_prev == 0` を先に評価して `indeterminate` とする。一方、同節は [両端全ゼロ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:313) を `saturated` とする。§5 も同じ二規則を別表に置き、両表間の precedence がない。

成果物影響: 同じ全ゼロ区間から workload state と aggregate verdict が変わる。

文書内で zero-abort 規則を通常分類より先に置き、zero-dispersion を「両端全ゼロを除く」と限定する必要がある。

### [real] [must-fix] zero-dispersion 区間では必須の `U_flat` を計算できない

正値で両端の 5 rep が完全同値なら `v_i+v_prev=0`、`nu=0/0` である。それでも [本体 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:297) は `U_flat` を「必ず併記」、§5 は `"u_flat_is_reported"` とする。`U_flat` は同じ未定義の t 分位点を必要とする。

成果物影響: 文書自身が実在すると認める zero-dispersion 入力で、適合 report を生成できない。

zero-dispersion では `U_flat=null` と理由を出すなど、診断値の total な表現を文書と spec で固定すべきである。

### [real] [must-fix] workload 状態は排他でなく first-match 順序に依存する

§5 の条件 `[indeterminate, declining, declining, declining, declining, saturated]` を考えると、「少なくとも 1 区間が indeterminate」と「all intervals classified and no persistent location」がともに成立する。また suffix に saturated が 2 個あれば、JSON の `"all intervals classified and a persistent saturation location exists"` とも重なる。散文の saturated 条件だけは `saturated` または `declining` に限定され、JSON とも一致しない。

成果物影響: rule 配列の順序または散文・JSONのどちらを採るかで workload state と aggregate verdict が変わる。

後二条件を明示的に「indeterminate が 0 件」とすれば、first-match に依存せず排他的になる。

### [real] [must-fix] `j=1` の飽和位置と bracket が三通りに割れている

[本体 §4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:300) の一般式では、全 6 区間が saturated の場合は `j=1`、位置は `b_1`、bracket は `[b_0,b_1]`。ところが直後は「最も左の位置は 1768」「bracket は `[1250,1768]`」、§5 も `reported_location=b_j` と `minimum_resolvable_location_us=1768` を同時に持つ。

成果物影響: 全区間 saturated の正常入力で、位置 1250、位置 1768、左打切りのみ、のいずれを報告するか一意でない。

`b_i` の添字、`j=1` の report literal、左打切り bracket を具体値で一本化する必要がある。

### [real] [must-fix] field の「出所」は追加されたが source path 契約になっていない

[本体 §5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:602) は正規化 field が現 producer に存在しないと認めつつ、throughput を `"existing per-rep throughput values"`、binary digest を `"build stage record field"` とだけ記す。`campaign_id`、lock digest、attempt、WAL record digest、source measurement は required provenance にあるが `analysis_input_contract.fields` に source がない。さらに `throughput_tps_cv` は非権威とした report の `cv` を source にしている。

成果物影響: consumer ごとに report、in-memory capture、WAL のどれを読むかが変わり、受理・拒否および CV が変わる。

各 normalized field に exact WAL stage、payload key、envelope key、導出式を固定する必要がある。

### [real] [must-fix] correctness 5 rep と mode 比較が投入可能性まで閉じていない

現実装は [T2418 loader](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1080) で `committed_verify` が非空かつ全件 certified かだけを見ており、件数 5 を検査しない。report に `correctness_mode` もない。一方、本体は 5 record と「t2418 と同じ mode」を要求するが、[§8 の投入前条件](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:864) は consumer、counter、provenance の 3 件だけである。

成果物影響: 記載された投入前条件をすべて満たしても、最初の formal cohort が failure 1 または 18 で必ず invalid になりうる。

docs-only の範囲で、投入前条件へ「5 verify record/cell の発行確認」と、比較対象となる探索 mode identity の exact な導出元を追加すべきである。

### [real] [nit] 地図が旧 `U_flat` gate の説明を残している

[地図](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md:29) は述語を「対数傾き・同時上限・検出力の事前条件」と説明するが、修正後は `U_flat` を分類から外した診断値である。

成果物影響: normative な受理集合は変わらないが、地図の要約が旧 2 分割を案内する。

### refuted とした懸念

- 通常の正値区間で `saturated` と `declining` が同時成立する: `refuted`。
- 上限継続条件により `saturated` が到達不能になる: `refuted`。例えば `D,D,D,D,S,S` で位置は存在する。
- 多重度 36 が実際の限界本数と違う: `refuted`。
- §6 の 4 数値、§2.3 の点推定、格子、raw、測定順が誤っている: すべて `refuted`。
- 探索走が新 failure に当たること自体が回帰: `refuted`。formal への流用禁止を正しく発火させている。

## 総括

格子、3535/7070、raw、3 測定順、多重度 36、§6 の検出力値、探索点推定はすべて正しい。  
レビュー所見 19 件は `closed` 12、`partial` 6、`regressed` 1 で、全面的には閉じていない。  
主要な残件は、全ゼロ規則の衝突、zero-dispersion での `U_flat` 未定義、workload state の順序依存、`j=1` の位置矛盾である。  
field source と correctness mode/5 rep の投入前契約も、現実装へ一意に結び付いていない。  
したがって fix 後文書は数値面は成立するが、formal verdict を一意に生成する事前登録としては未完成である。  
read-only の静的検査だけを行い、コード・test・gate の変更や pytest は要求していない。