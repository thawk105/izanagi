## 総括

変更 file 数: 3 file。

変更箇所数: 現行行番号基準の論理 edit cluster 44 箇所。driver 19、test 17、文書 8。

新設テスト数: 負例 4 件。それぞれ同じ test 内で v4 正例も先に通す。

受理集合の変化: v4 の `{constant, symmetric-modulo}` × μ 6 点、完全な残差 12 cell、上限 exact 1.0 の spec だけを受理し、v3、binary を含む grid、1.0 以外の上限、cell 除外面を持つ spec を新たに拒否する。その他の μ・workload・実行・解析規則の閉集合は従来どおり。

未解決の論点: 裁定パッケージ候補 3 件。D1057 の supersede、2 水準化後の主張範囲、`SPACE_VERSION` / `TRIAL` の版上げ要否。

## driver 実装プラン

対象: [b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:80)

### 直接編集する 19 箇所

1. `:80-101`
   - `MEANS_US` は `(2, 5, 10, 25, 50, 100)` のまま。
   - `SHAPES` を `(("constant", 0), ("symmetric-modulo", 1))` にする。
   - `SHAPE_CODES` / `SHAPE_NAMES` はその閉集合から再生成されるため、`encode("binary", ...)` と `decode(2000+mu)` は拒否へ変わる。
   - `POINTS_PER_BLOCK = 3 + len(MEANS_US) * len(SHAPES)`、すなわち 15 を導入し、散在する 21 をこの値へ束ねる。
   - 将来の `run_probe` が 12-cell result を v1 と称さないよう、`PROBE_SCHEMA` は `/v2` へ上げる。既存の凍結済み 18-cell `/v1` は変更しない。
   - `SPACE_VERSION`、`TRIAL` は式・符号化空間が不変なので本案では据え置く。版上げ要否は後述の裁定候補。

2. `:153`
   - `_SPEC_SCHEMA` を `izanagi-b10-backoff-shape-preregistration/v4` に変更する。

3. `:215-258`
   - `PreregistrationSpec` に、v4 で追加する `registration_rules` の immutable fieldを追加する。
   - 値は例えば `tuple[tuple[str, str], ...]` とし、canonical JSON 以外に可変 dict を保持しない。

4. `:489-554`
   - `encode` / `decode` のロジック自体は維持し、縮んだ map により code 2 を driver API で拒否する。
   - `factorial_genomes()` は自動的に 12 点になる。
   - `named_genomes()` と `block_run_order()` の 21 hard-code を `POINTS_PER_BLOCK` に置換する。
   - `grid.references` は `none`、`adaptive`、`zero-loop` の 3 点を据え置く。したがって block あたりは `3 references + 12 factorial = 15`。

5. `:800-844`
   - machine spec の top-level exact key set に `registration_rules` を追加する。
   - v4 だけを受理する。
   - `expected_supports` から binary を削除し、次の 2 行だけを順序込みで受理する。
     - `constant / code 0 / mu`
     - `symmetric-modulo / code 1 / closed-half-width-mu/2-through-3mu/2`

6. `:844` の直後
   - `registration_rules` を exact object として parse する。提案する閉集合は次のとおり。
     - `shape_eligibility_criterion = no-unsuppressed-linear-mu-gain-in-mixer-high-bit-frequency`
     - `shape_eligibility_evidence = formula-only-not-observed-deviation`
     - `shape_exclusion_granularity = whole-shape-only`
     - `means_us_and_cell_partition = unchanged`
     - `physical_residual_cell_policy = evaluate-all-registered-cells-without-exemption`
     - `throughput_decision_procedure = unchanged-and-independent-of-a2`
     - `shape_rule_formulation_timing = after-physical-residual-probe-before-shape-grid-throughput`
   - threshold、cell ID、deviation 条件、免除 list を表現する field は設けない。

7. `:917-934`
   - `expected_families` を workload ごとの `symmetric-modulo` だけにする。
   - 閉集合と順序は `write-heavy`、`balanced`、`read-heavy` の 3 族。

8. `:940-998`
   - `pairs_per_family = 18` と `enumeration = all-2^18` は維持する。1 族は 3 blocks × μ 6 点だからである。
   - `construct-all-18-within-block-paired-relative-effects` も維持する。
   - `holm-adjust-all-six-families` だけを `holm-adjust-all-three-families` に変更する。
   - driver 内に、族数を語として埋めた他の literal はない。`:1375` の `three independent paired blocks` は block 数なので維持する。

9. `:1000-1061`
   - `maximum_absolute_deviation_pct_exclusive` は「正なら可」から、数値として exact `1.0` のみ可へ強化する。
   - `expected_residual_cells` は縮小後の `SHAPES` から 12 cell を生成する。
   - 順序は各 μ ごとに `constant`、`symmetric-modulo`。
   - 行 key の exact set を維持し、cell-level `excluded`、`warning`、`waiver` などの追加を拒否する。

10. `:1100-1143`
    - parse 済み `registration_rules` を `PreregistrationSpec` に格納する。
    - `physical_residual_values` は 12 行になる。

11. `:1146-1190`
    - `validate_runtime_physical_residual()` は observed cell closure と全件走査を維持する。
    - 防御的に limit が `1.0` であることも再確認する。
    - 全 12 cell の最大絶対偏差を計算し、`>= 1.0` を従来どおり拒否する。cell 単位の continue、免除、警告化は追加しない。

12. `:1311-1383`
    - `search_config.shape_codes`、block order、family size、residual values は spec 由来の 2 形・15 point・3 族・12 cell になる。
    - `spec_content` の `21 genomes` を `15 genomes` に変更する。3 blocks、screening 無しは維持する。

13. `:1767-1858`
    - probe harness build は `MEANS_US × SHAPES` により 12 target だけを生成する。
    - compile command 件数の literal 18 は、登録 cell 数との比較または 12 に変更する。
    - code 2 binary を probe driver からも発行しない。

14. `:1919-1935`
    - `_shape_differences()` の literal tupleを `("symmetric-modulo",)` にする。
    - output は 12 ではなく、μ ごとの constant contrast 6 行になる。

15. `:1938-2057`
    - `_validate_probe_result()` の期待 cell 閉集合を 12 にする。
    - 18-cell error literal を 12 または「登録 grid と不一致」に変更する。
    - `/v2` + 12 cells + 6 differences を受理する。歴史的 `/v1` 18-cell artifact はこの新 validator の入力にせず、§4 の開示元としてだけ扱う。

16. `:2215-2220`
    - `_block_record_filename()` の `schedule_index < 21` を `< POINTS_PER_BLOCK` に変更する。

17. `:2394-2406`
    - point name regex を `r"(constant|symmetric-modulo)-mu([0-9]+)"` に変更する。
    - `binary-mu2` などは `_name_metadata()` で明示的に拒否される。
    - code 2 は `EXPECTED_HOLE_LINE` と `exact_model()` には残るが、`encode`、`decode`、spec、named genome、block order、probe、name parser の全入口で driver が発行・受理しない。

18. `:2727-2757`
    - verify 完了件数 21 を `POINTS_PER_BLOCK`、すなわち 15 に変更する。

19. `:2896-2905`
    - perf 完了条件を `len(block_ids) * POINTS_PER_BLOCK`、すなわち workload あたり 45 records に変更する。

### `SHAPES` / `MEANS_US` の全 reader

直接 reader は以下で尽きる。

- 定義・派生 map: `:90-93`
- encode/decode: `:489-503`
- factorial grid: `:514-525`
- block order: `:539-554`
- spec の μ と shape 検査: `:825-844`
- residual cell closure: `:1019-1023`
- probe target build: `:1792-1796`
- shape difference: `:1925-1928`
- probe result closure: `:2009-2012`
- probe execution loop: `:2620-2631`

`("symmetric-modulo", "binary")` の直書きは `:921` と `:1927` の 2 箇所だけで、ほかにはない。別形式の binary 列挙は name regex `:2401` にある。

`EXPECTED_HOLE_LINE` `:122`、`FORMULA_SHA256` `:123`、patch SHA、`exact_model()` の code 2 branch `:557-577` は変更しない。

## test 実装プラン

対象: [test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:86)

### 既存 test / fixture の変更 17 箇所

1. `:86-126`
   - `_complete_records()` と `_physical_residual_values()` は `B.SHAPES` を読むため、自動的に 2 形、12 residual rows になる。
   - `_physical_residual_values()` は binary 固有前提を持たない合成 fixture であり、loop closure 以外は変更不要。

2. `:129-241`
   - `_spec_dict()` を v4 にする。
   - shape rows から binary を削除する。
   - `registration_rules` の exact 正例を追加する。
   - Holm family を 3 族にする。
   - `holm-adjust-all-three-families` に変更する。
   - `pairs_per_family=18` と `all-2^18` は維持する。

3. `:268-329`
   - `_probe_result()` は 12 cells を生成する。
   - `shape_extra` の binary entryを削除する。
   - difference rows は 6 になる。
   - schema は `B.PROBE_SCHEMA` の `/v2`。

4. `:551-565`
   - matching preregistration 正例の residual 件数を 12 にする。
   - shape 2、Holm 3、limit 1.0、registration rules を追加確認する。

5. `:568-571`
   - `test_m09_shape_code_three_is_rejected_instead_of_falling_back` は binary 前提ではない。
   - C++ の code `>=3` fallback を driver が受理しない検査なので、変更せず維持する。

6. `:574-583`
   - M10 の underexposed target を `binary` から `symmetric-modulo` に置換する。
   - `indeterminate`、17 pairs、p=1.0 の期待は変更しない。

7. `:628-657`
   - `test_m14_different_random_mixers_are_rejected_for_one_reason` は dormant binary branch を直接変異する binary 前提の test である。ただし hole line が不変なので削除も緩和もせず維持する。
   - `test_cpp_pair_average_is_exact_mean_for_an_alternate_odd_mixer` も binary 前提。`B.encode("binary", 25)` は新 driver で拒否されるため、C++ hole の dormant code 2 を検査する literal `2025` に置換する。pair-sum の期待値は変更しない。

8. `:701-714`
   - P06 は canonical v4 文書自体を parse する正例に寄せる。
   - shapes 2、families 3、residual 12 を確認する。
   - pairs 18 は維持する。
   - runtime maximum は実値 `0.5616942857142844` を確認する。

9. `:801-809`
   - probe output の cells 18→12、differences 12→6。

10. `:905-910`
    - `test_p02_all_18_encodings_are_bijective` を `...all_12...` に改名し、12 を期待する。
    - 同じ test 内で `encode("binary", 2)` と `decode(2002)` が `ValueError` になることを追加する。

11. `:919-929`
    - reference は依然 3 点なので test 名は維持する。
    - full grid count 21→15。

12. `:931-951`
    - 手計算上の binary は dormant C++ branch の性質を検査している。test 名とコメントを「登録 2 形と dormant binary」を区別する表現へ直し、数理期待は維持する。

13. `:954-967`
    - binary arms test は production `encode()` を使わず `2000 + mean_us` で dormant branch を検査する。
    - symmetric bounds は従来どおり production `encode()` を使う。

14. `:970-974`
    - block order 長を 21→15。集合一致と 3 block の相異性は維持する。

15. `:1068-1091`
    - missing / uncertified / unstable の target family を binary から symmetric-modulo に変更する。
    - indeterminate の期待は維持する。

16. `:1094-1102`
    - `test_cell_effects_cover_all_54_factorial_cells_with_ci` を 36 cells に変更する。
    - 算術は 3 workloads × 2 shapes × 6 means = 36。

17. `:1118-1146`
    - registered branch の照合 loop は `B.SHAPES` により 2 形になる。
    - 独立 C++ pair oracle は dormant binary も引き続き検査するが、binary の encoded 値だけ literal code 2 で構成する。
    - formula、bounds、pair-sum の期待は変更しない。

### 新設する負例 4 件

各 test は最初に無変異の `_spec_dict()` が parse できることを確認し、その後だけ変異を拒否させる。

1. `test_v4_spec_including_binary_shape_is_rejected()`
   - 負例: v4 `grid.shapes` に `{name:"binary", code:2, ...}` を加え、`PreflightError("prereg-spec")`。
   - 通る正例: exact 2-shape `_spec_dict()`。

2. `test_physical_residual_limit_other_than_exact_one_is_rejected(limit)`
   - `limit` は少なくとも `0.5` と `2.0` で parameterize する。
   - 負例: `maximum_absolute_deviation_pct_exclusive = limit` を parser で拒否。
   - 通る正例: numeric `1.0`。
   - 既存 M18 は「実測値が上限を超える場合」の runtime test なので、そのまま残す。

3. `test_spec_has_no_observed_deviation_based_cell_exclusion_surface()`
   - 負例:
     - residual row に `exclude_if_absolute_deviation_pct_gte` を追加する。
     - または `physical_residual.excluded_cells` を追加する。
     - いずれも exact key set で拒否する。
   - 通る正例: 12 cell 全件を持ち、`evaluate-all-registered-cells-without-exemption` を固定した spec。

4. `test_schema_v3_document_is_rejected_after_v4_positive_control()`
   - 負例: 正例の schema だけを `/v3` に戻して拒否する。
   - 通る正例: `/v4`。

既存 test の期待値反転、緩和、skip、削除は行わない。

## 文書実装プラン

対象: [b10-backoff-shape-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/docs/b10-backoff-shape-preregistration.md:8)

### §0 `:8-20`

現在は placeholder 発効手順を記述している。これを v4 発効版の状態へ更新する。

- probe は既に 18 cells で完了済み。
- hole line、patch SHA、formula SHA が同一なので、constant / symmetric-modulo の 12 cells を逐語転記した版を発効版とする。
- probe 再走はしない。
- R1 は probe 後に定式化したこと、shape-grid throughput は未観測であることを明示する。

ここには 3 形・18 cell・6 族の直接 literal はないが、placeholder 状態が現状と不一致。

### §2 `:32-60`

3 形前提は `:43-55`。

- 「3 段階」を「2 形の対比」に変更する。
- binary rowを登録表から削除する。
- constant と symmetric-modulo の式上の性質を説明する。
- binary は歴史的候補として別段落で式を開示し、登録対象ではないとする。
- R1 は「binary のような直接の `μ(p-1/2)` 利得を持たず、formula 上の modulo-bias residual にだけ依存する形」と正確に書く。
- 「p に対して厳密に一次不変」とは書かない。symmetric-modulo の係数は `E[r]-μ` で、厳密な 0 は別仮定を要するためである。

### §3 `:62-78`

直接の数値前提はないが、`:66-68` の「待ち方が throughput を動かすか」の射程を狭める。

- registered contrast は constant 対 symmetric-modulo の 1 contrast/workload。
- binary や 3 水準の dose-response、ばらつき全般への一般化は主張しない。
- throughput 未観測時点で R1-R5 と v4 grid を固定した、という限定主張を追加する。

### §4 `:80-104`

現在は新 probe と A-2 が未開示。次を追加する。

- 18-cell probe の identity、18 行の full-precision deviation、4 binary failures。
- probe が合成 loop の `start` 列を測っただけで、formal throughput の列や分布ではないという限界。
- 公平 bit 仮定なら 100,000 calls の binary mean の相対 SE は約 0.158%、4.3503% は約 27.5 SE であり、単なる calls 増加を設計根拠にしないこと。
- A-2 の rr5 `-46.3902%`、rr50 `-65.9080%`、outer `reject`。
- 「開示した事実」と「固定する規則」を分離する新小節。
- R1 は probe 後に定式化したため binary 除外自体を事前登録とは呼ばない。
- A-2 は μ、throughput 判定、等価域などを変更する根拠にしていない。

### §5 `:106-506`

ここが 3 形・18 residual cells・6 Holm families の主な正本。

- preamble `:108-113`: placeholder 説明を発効版説明へ変更。
- `:118`: schema v4。
- `:123-167`: shape 2、reference 3 の閉集合。
- `:168-245`: 各 block の run order を 21→15。
- `:278-305`: Holm family 6→3。
- `:306-345`: pairs 18 と `all-2^18` は維持し、Holm literal だけ three にする。
- `:348-478`: binary 6 rows を削除し、残る 12 rows を実測値へ置換。
- `registration_rules` を追加し、R1-R5 と formulation timing を機械可読に固定する。

発効版へ転記する 12 行は次の値。

| shape | μ | realized | commanded | deviation_pct |
|---|---:|---:|---:|---:|
| constant | 2 | 4223.59116 | 4200 | 0.5616942857142844 |
| symmetric-modulo | 2 | 4218.32476 | 4200 | 0.43630380952381964 |
| constant | 5 | 10538.38268 | 10500 | 0.3655493333333392 |
| symmetric-modulo | 5 | 10544.10586 | 10500 | 0.42005580952380633 |
| constant | 10 | 21035.41464 | 21000 | 0.16864114285713835 |
| symmetric-modulo | 10 | 21047.27694 | 21000 | 0.22512828571428448 |
| constant | 25 | 52530.59194 | 52500 | 0.05827036190475891 |
| symmetric-modulo | 25 | 52275.76334 | 52500 | -0.427117447619052 |
| constant | 50 | 105021.8346 | 105000 | 0.020794857142859006 |
| symmetric-modulo | 50 | 104692.05524 | 105000 | -0.29328072380952236 |
| constant | 100 | 210029.9768 | 210000 | 0.014274666666668573 |
| symmetric-modulo | 100 | 210487.20626 | 210000 | 0.23200298095238395 |

最大絶対偏差は 0.5616942857142844% で、exclusive 1.0% 未満。

### §6 `:508-522`

3/18/6 の直接前提は `:511`。

- 「18 対」は維持する。これは residual cell 数ではなく、1 family あたりの 3 blocks × 6 μ の paired effects。
- 「6 族 Holm」だけを「3 族 Holm」に変更する。
- brief 内の「12 対 / 3 族」は静的構造と矛盾するため採用しない。

### §8 `:539-547`

現状に 3 形・18・6 の直接 literal はない。

- 報告対象を workload/block ごとの 15 point、Holm 3 族として明確化する。
- binary を測った、3 水準を比較した、binary 除外が事前登録だった、という表現を禁止する。
- probe 18-cell 開示、登録 residual 12-cell、v4 binding を区別して報告させる。

### §9 `:549-556`

現状に直接の 3 形・18・6 前提はない。

- binary を含む 3 水準 shape comparison と full variance dose-response を未取得事項へ追加する。
- B-10 の他の既存未取得事項は変更しない。

## 受理集合の変化

`v4 + exact 2-shape grid + unchanged μ/workload/execution/analysis + complete 12-cell residual table + exact 1.0 exclusive limit` を受理し、旧 v3、binary を含む spec、limit が 1.0 以外、残差 cell の欠落・追加・観測値条件による除外を新たに拒否する。

## 本 wave 外へ送る裁定パッケージ候補

1. D1057 supersede
   - 「odd mixer だから実走の最上位 bit がちょうど半々」という premise が probe により成立しなかった事実。
   - 新しい R1 は「厳密な p 不変」ではなく「binary の直接的な μ 利得を持たない」という式上の構造基準として記録する。

2. 論文上の主張範囲
   - 2 形では constant 対 symmetric-modulo の contrast はできるが、3 水準のばらつき dose-response は閉じない。
   - binary を含む完全な shape ladder は未取得として残す。

3. campaign version policy
   - 本案では式と encoding space が不変なので `SPACE_VERSION` / `TRIAL` の v2 を維持し、spec SHA と schema v4 で identity を分離する。
   - 「登録 subgrid の縮小も space version 上げの対象」とするなら別裁定で v3 化する。

pytest、build、その他の動的検査は指示どおり実行していない。以上は射影資料の全文通読と静的参照検査だけに基づく計画である。