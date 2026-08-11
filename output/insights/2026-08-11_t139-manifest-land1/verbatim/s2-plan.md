必読資料はすべて読めた。ファイル変更・pytest・PBS 投入は行っていない。以下は静的監査であり、緑・赤は主張しない。

結論を先に言うと、現行草案のままの land 1 は NO-GO である。独立した blocker 群は 6 件。また、R1 と R3 を同時に満たす land 2 には、canonical main への `a13` 予約と pilot 実行順序の循環があり、追加裁定なしには実行可能な時系列を構成できない。

## §1 land 1 の 3 文書の内容監査

### 1.1 親の実測値の再計算

| 対象 | 再計算値 | 判定 |
|---|---|---|
| `F_e` | `dce4ae4fed6f4fb33747165c5b92c16d01822850`、HEAD の祖先、rc=0 | 一致 |
| 凍結 core | `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9`、450 行 | 一致 |
| core 221 行、LF 込み | `225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89` | 一致 |
| erratum-1 のみ | `d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82` | 一致 |
| erratum-1 + erratum-2 | `dfb821a5ff0b085f7092bbd5536772a8c6728ec946291a6e6eb61da9fbef678c` | 一致 |
| errata の逆順適用 | 同じ `dfb821…678c` | 一致 |
| 現行 record-items | `1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3` | 一致 |
| 草案 reissue | `5f07e9177736739fdb80a7df00a84c6f84751bf8d3c5e686adc447873a273d54` | 一致 |
| 草案 erratum-2 | `9eb96f88e93f0d027e7f86281ebd7ee00e0cb4d243e0c27edd2afa1e78b4885c` | 一致 |
| `record_items` digest を pin する `.py` | 0 件 | 一致。canonical pin は [decisions.md:12125–12128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12125) の D262 |

### 1.2 `record-items-reissue.md`

#### Q-A 第三分岐

6 条件は、任意の JSON に対する論理的な恒真式ではない。[record-items-reissue.md:90–110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:90) の raw pointer・失敗再計算・単調時刻・marker/run 不在を欠けば拒否できる。

一方で、実世界の「性能 run を実行しなかった」という命題に対しては producer 内で恒真化できる。producer は偽の短い `/proc/stat`、整合する時刻、`null` marker を作り、当該 actual run を receipt から落とせる。6 条件をすべて満たす具体形は [package.md:60–74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/package.md:60) にある。

したがって判定は次のとおり。

- 「raw から失敗が導ける」という receipt 内自己整合性には非恒真。
- 「本当に未実行だった」という外部事実には非識別で、producer が捏造可能。
- [record-items-reissue.md:282–291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:282) はこの非保証を正しく明記している。R2 (a) により、この残余自体は blocker に数えない。

#### Blocker RI-B1 — 前版の受理条件を本文から落とし、非承認 blob への暗黙継承に変えている

草案は変更を「この 3 つだけ」と宣言し、欠落した旧本文を「逐語で有効」と参照するだけである。[record-items-reissue.md:19–27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:19)

受理条件に関係する差分の完全な列挙は次のとおり。

| 現行 record-items の逐語要件 | reissue での状態 |
|---|---|
| `planned_execution.runs[]` の exact 10 key、`predecessor_arm == START`、permutation enum [record-items.md:89–97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:89) | key 集合を削除し、36 要素という件数だけ再掲 [reissue:265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:265) |
| 性能 compile argv・CMake cache との整合、correctness の `source` / `compile.argv` / binary path・size、性能 allocation/run との非同一 [record-items.md:109–119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:109) | trace/analysis boolean と binary SHA 非同一だけを残し、argv/cache/run-scope 条件を削除 [reissue:269–272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:269) |
| `schema_version` const、40/64 hex・repo-relative path、exact 3 arm、ID 一意性、全 foreign key、qsub 失敗 row の保存 [record-items.md:121–134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:121) | 本文から削除 |
| `correctness_evidence[].outputs` は pointer のみ、`declared_use_class` の exact 4 値と非権威性 [record-items.md:136–144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:136) | negative test だけ残し、型・enum・outputs 制約を削除 [reissue:273–275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:273) |
| qsub 前 create-only intent、job preflight collector、intent 全件の exact coverage [record-items.md:146–150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:146) | 本文から削除 |
| writer 自身が同一 snapshot の三つ組と `measurement_head` を照合 [record-items.md:152–155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:152) | 「`PreregBinding` を keyword-only で受ける」まで弱化 [reissue:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:276) |
| `a01`〜`a13`、errata、`argv_raw`、`compile_commands` の行対応表 [record-items.md:159–176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:159) | 表を削除し、新 §4 が一部だけ再記載 |
| 「exec witness と 3 点再 hash は敷居を上げるが閉じない」等の非保証 [record-items.md:201–210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:201) | exec witness・3 点 hash・core §15 との対応を削除 [reissue:292–297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:292) |
| `malformed_reason` は受理入力にしない | 非 null のとき負方向の整合検査に使うへ変更 [reissue:101–107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:101) |
| 前版に存在しない `b03` の長い scope 判断 | 第 4 の実質変更として追加 [reissue:219–229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:219) |

旧文書を「逐語で有効」とする解釈を採ると、受理述語が新 blob と、decision が非承認と名指しする旧 blob の 2 枚にまたがる。採らなければ上表の受理条件が消える。どちらでも一意な凍結述語にならない。

修正は、保持する全条項を reissue に実際に再掲すること。旧 blob の暗黙読込みで済ませてはならない。

#### Blocker RI-B2 — nested exact closure が未完成で、内部矛盾もある

[record-items-reissue.md:130–135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:130) は未閉包 object を閉じたと主張するが、実際に exact key を与えたのは `attempts`、environment observation、allocation、liveness、admission telemetry、cluster slot、TU value の一部だけである。

主な未閉包・矛盾は次のとおり。

- `preregistration`、blob ref、`environment.attestations[]`、`dependency_pins[]`、arm、source、toolchain、dynamic dependency、workload、actual run、correctness build/run scope/output の exact key・型・required/nullability が未定義。
- `translation_units{}` を唯一の `additionalProperties` 例外としている [reissue:242–246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:242)。これは全 object に `additionalProperties:false` を課す [reissue:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:41) および今回の明示要件と衝突する。Draft 2020-12 なら `patternProperties` と `additionalProperties:false` で閉じられる。
- `attempts[]` に `cluster_slot` がなく [reissue:139–143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:139)、allocation にも slot がない [reissue:177–183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:177)。actual run の無い preflight/qsub failure を同じ slot の置換へ束縛できず、`a09` の同一 slot 規則 [addendum-a-reissue.md:562–571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:562) を検査できない。
- `binary_rehash[]` は「3 要素固定」で各要素が `arm` を 1 個だけ持つ [reissue:193–194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:193)。`a05` は 3 arm の executable をそれぞれ 3 点で再 hash する [addendum-a-reissue.md:309–329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:309) ため、必要なのは 9 組または「1 point に 3 arm map」のいずれかである。
- `liveness[]` は `{ordinal,probe,monotonic_ns,raw}` だけで [reissue:196–203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:196)、`a01` が要求する 2 workload × 3 arm の検証 [addendum-a-reissue.md:105–119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:105) と allocation/run を結べない。
- admission の全 kind に `fixed_inputs{B,seed,input_sha256}` を課す [reissue:205–216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:205) が、`a10` の J 導出は Monte Carlo を使用しない [addendum-a-reissue.md:721–722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:721)。J/q/alpha reservation に `B` と `seed` を必須にする意味が定まらない。
- negative test は `admission_telemetry[].returncode` を名指しする [reissue:273–275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:273) が、exact key 集合には `returncode` がない。これは「禁止未知 key」なのか、記録するが非権威なのかを確定していない。
- performance source に `base_tree_sha` を要求する現行 record [record-items.md:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:171) と、`a08` の固定 source triple [addendum-a-reissue.md:401–408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:401) が一致しない。

#### Blocker RI-B3 — `pre_performance_infra_failure` が `a04` より広い

reissue は pre-performance の条件を marker 不在だけにしている。[record-items-reissue.md:65–70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:65)

しかし `a04` は次を固定済みである。

- `a03` 不成立は位置を問わず post-performance、置換不可。
- marker 不在でも性能 raw が 1 件あれば post-performance。
- performance 開始後を pre-performance へ写してはならない。

根拠は [addendum-a-reissue.md:263–306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:263) と core §9 [preregistration.md:237–244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:237)。

現草案だと「marker を消したが performance raw は残る attempt」を pre-performance として受理し、予備置換できる。第三分岐とは別の不正な受理拡大である。

#### Blocker RI-B4 — `a13` は current tip の重複検査だけ

[record-items-reissue.md:215–218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:215) は現在の台帳を読み、重複がないことしか要求しない。過去行を削除して同じ `(family_root, ordinal)` を再利用した履歴を受理する。

これは R3 (a) の append-only 全履歴検査を満たさない。`a13` 自身も create-only・解放不可・canonical ledger の再読を課す。[addendum-a-reissue.md:919–937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:919)

### 1.3 `erratum-core-s7-stresscheck.md`

#### 確認できた点

- `operations` は exact 1 件、locator は core 221 行である。[erratum-core-s7-stresscheck.md:64–85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md:64)
- erratum-1 の locator は 404 / 424 行 [erratum-core-s15.md:59–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:59)。`221 ∉ {404,424}` で非重複。
- 実装も erratum-1 の `_validate_operation_binding` を流用していない。S7 固有 validator は operation 数、対象語句出現数、行、old bytes、1 行性、新 bytes digest を独立に検査する。[erratum.py:397–447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:397)
- 共通化されているのは複数 errata 間の非重複と合成処理だけであり [erratum.py:332–341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:332)、D263 の境界に合う。

#### Blocker ER-B1 — core 333 行と承認済み a12 見出しに同じ較正義務が残る

221 行だけを置換しても、core §14 の 333 行には次が残る。

> `| a12 | weak null の型 I 誤りを較正する事前 simulation の仕様 |`

該当箇所は [preregistration.md:331–334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:331)、LF 込み SHA-256 は `a7852ad9a4812f8adc8ebf33354a5934bd6620205a23defa48732a1737a89952`。

承認済み addendum の見出しにも同じ語が残る [addendum-a-reissue.md:825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:825) 一方、直後の本文は「本 field はその較正を与えない」と明記する [addendum-a-reissue.md:827–838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:827)。

erratum 自身も core 333 行の存在を認識しながら対象外にしている。[erratum-core-s7-stresscheck.md:91–95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md:91)

したがって置換後 core は、§7 では stress check、§14 では calibration specification を要求する二重状態になる。少なくとも次のどちらかが必要だが、ここでは選択してはならない。

- erratum-2 を 2 operation にして core 333 行も exact replacement する。
- core 333 行と承認済み addendum 825 行を扱う別の前向き correction を承認する。

どちらでも erratum-2 blob digest と `composed_sha256` は変わる。現行 `9eb96…` と `dfb821…` は approval-ready ではない。

また、文書の固有検査 4 は「1 行で simulation に言及」までしか課さない [erratum:87–95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md:87) のに、実装は新 bytes の exact SHA を要求する [erratum.py:438–447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:438)。blob 全体の digest pin により直ちに fail-open ではないが、凍結する固有検査文にも exact new bytes/digest を書くべきである。

### 1.4 受領証 JSON Schema blob

#### Blocker SC-B1 — blob が存在せず、現 record から一意に生成できない

第 1 波は schema を作っていないと明記している。[package.md:157–168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/package.md:157)

さらに現在の `jsonschema` は静的 import で 3.2.0、`Draft202012Validator` を持たない。repo の既存経路も Draft 7 である。[collector.py:287–300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/qualification/collector.py:287)、[test_s8b_selector_output.py:98–101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_s8b_selector_output.py:98)

land 1 では JSON を data blob として承認できるが、承認前の meta-schema 検査には、版と実体を pin した Draft 2020-12 validator が別途必要である。land 2 で Draft 7 に読み替える案は不可。

#### schema の必須構造

schema 文書は次を必須とする。

- `"$schema": "https://json-schema.org/draft/2020-12/schema"`
- 外部 `$ref` なし。1 blob 内の `$defs` のみ。
- instance 上の全 object schema に `additionalProperties:false`。
- 全必須 key を `required` に列挙。条件付き不在は key 省略ではなく、明示的な `null` または tagged `oneOf` として record-items 側で確定する。
- `translation_units` は `patternProperties` + `additionalProperties:false`。schema-valued `additionalProperties` は使わない。
- duplicate JSON key は schema 検査前の parser で拒否する。
- foreign key、順序、prefix/双射、実待機時間、binary 非同一、ledger 履歴等は JSON Schema だけでは閉じない。land 2 の固定 semantic validator が再計算する。

#### 全 key・型 inventory

記号は、`○` が exact key 集合まで文書から決まるもの、`△` が key 名はあるが型・nullability・下位 closure が未定のもの、`×` が key 名自体を確定できないもの。以下は現行 record/reissue に現れる key を省略せず列挙している。`×` を独断で補うと受理集合を新設するため、approval-ready schema にはできない。

| object path | exact key と型 | 状態 |
|---|---|---|
| root | `schema_version:string`, `study_id:string`, `declared_use_class:string`, `study_stage:string`, `series_id:string`, `parent_series_id:string\|null`, `preregistration:object`, `environment:object`, `measurement_checkout:object`, `dependency_pins:array`, `arms:object`, `allocations:array`, `planned_execution:object`, `actual_runs:array`, `correctness_evidence:array`, `liveness:array`, `admission_telemetry:array`, `attempts:array` | key は ○、const/enum/ID grammar の一部が RI-B1 で欠落 |
| `BlobRef` | `path:string`, `commit:string(hex40)`, `sha256:string(hex64)` | △。共通形として必要だが reissue に定義なし |
| file pointer | `path:string`, `size:integer`, `sha256:string(hex64)` | ○ |
| `preregistration` | `core:BlobRef`, `addendum_a:BlobRef`, `addendum_b:BlobRef\|null`, `fold_commit:string(hex40)`, `errata:array` | △。前 4 key と errata は別節で名指しされるが、統合した exact set が未記載 |
| `preregistration.errata[]` | `path:string`, `commit:string`, `sha256:string`, `approval_fold_commit:string` | ○ [record-items.md:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:175) |
| `environment` | `env_tag:string`, `attestation_mode:string`, `attestations:array` | △ |
| `environment.attestations[]` | item key 未定義 | × |
| `measurement_checkout` | `repository_head:string(hex40)`, `ccbench_head:string(hex40)` | ○ |
| `dependency_pins[]` | item key 未定義 | × |
| `arms` | `stock:Arm`, `mode1:Arm`, `modeX:Arm` | ○ |
| `Arm` | `compile:object`, `binary:FileRef`, `built_outside_allocation:object`, `toolchain:object` | △ |
| `Arm.compile` | `source:object`, `mode_macro:string`, `configure_argv:string[]`, `translation_units:object`, `identity_sha256:string`, `trace_enabled:boolean`, `analysis_enabled:boolean`, `cmake_cache:object`, `compile_commands:FileRef` | ○ key、型制約は一部 △ |
| `Arm.compile.source` | `repo_commit:string`, `ccbench_pin:string`, `base_tree_sha:string`, `patch_path:string`, `patch_sha256:string` | key は ○。`base_tree_sha` と a08 の固定 triple が不一致 |
| `cmake_cache` | `trace:integer\|boolean`, `add_analysis:integer\|boolean` | key は ○、型表現が未確定 |
| `translation_units` | dynamic repo-relative path → TU value | key grammar は記載済み。`patternProperties` が必要 |
| TU value | `normalized_argv:string[]`, `sha256:string` | ○ |
| `built_outside_allocation` | `artifact_path:string`, `size:integer`, `sha256:string` | ○ |
| `toolchain` | `compiler_path:string`, `compiler_version:string`, `compiler_sha256:string`, `link_argv:string[]`, `dynamic_deps:array`, `elf_interpreter:string` | ○ key |
| `dynamic_deps[]` | item key 未定義 | × |
| `allocations[]` | `allocation_id:string`, `allocation_role:string enum`, `path_choice:string enum`, `path_choice_intent:FileRef`, `node:string`, `requested_walltime_s:integer`, `internal_deadline_s:integer`, `started_at_monotonic_ns:integer`, `ended_at_monotonic_ns:integer`, `accounting_trace:FileRef`, `exclusivity:object`, `phase_caps:array`, `phase_events:array`, `binary_rehash:array` | ○。ただし attempt/slot/PBS job との結合 key が欠落 |
| `exclusivity` | `method:string`, `raw:FileRef` | ○ key、method enum 未定義 |
| `phase_caps[]` | `phase:string enum`, `cap_s:number`, `sub_cap_s_or_null:number\|null` | ○ |
| `phase_events[]` | `phase:string enum`, `event:string enum`, `monotonic_ns:integer` | ○ |
| `binary_rehash[]` | `point:string enum`, `arm:string enum`, `sha256:string`, `monotonic_ns:integer` | ○ key、配列 3 要素指定は a05 と矛盾 |
| `planned_execution` | `workloads:object`, `schedule_seed:string`, `schedule_algorithm:string const`, `schedule_sha256:string`, `cluster_slots:array`, `runs:array` | ○ |
| `workloads` | `W1:Workload`, `W2:Workload` | ○ |
| `Workload` | `driver_argv:string[]`, `effective_flags:object`, `opt_parameters:object` | ○ |
| `effective_flags` | `clocks_per_us:number`, `epoch_time:number`, `extime:number`, `thread_num:integer`, `ycsb_max_ope:integer`, `ycsb_rmw:integer`, `ycsb_rratio:integer`, `ycsb_tuple_num:integer`, `ycsb_zipf_skew:number` | ○、[addendum-a-reissue.md:371–383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:371) |
| `opt_parameters` | `ADD_ANALYSIS`, `BACK_OFF`, `KEY_SIZE`, `MASSTREE_USE`, `NO_WAIT_LOCKING_IN_VALIDATION`, `PARTITION_TABLE`, `PROCEDURE_SORT`, `SLEEP_READ_PHASE`, `VAL_SIZE`, `WAL`: 各 integer | ○、[addendum-a-reissue.md:385–391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:385) |
| `cluster_slots[]` | `cluster_slot:integer`, `workload:string`, `block_index:integer`, `permutation:string enum` | ○ |
| `planned_execution.runs[]` | `run_id:string`, `cluster_slot:integer`, `workload:string`, `block_index:integer`, `permutation:string`, `planned_ordinal:integer`, `position:integer`, `predecessor_arm:string`, `arm:string`, `preceding_wait:object` | exact set は現行文書にのみ存在。reissue 本文へ再掲が必要 |
| planned `preceding_wait` | `kind:string`, `required_s:number` | ○ |
| `actual_runs[]` | 明記済み key は `run_id`, `attempt_id`, `allocation_id`, `preceding_wait`, `binary_sha256`, `exec_witness`, `argv_sha256`, `argv_raw`, `run_log`。実行順・position・predecessor・timestamp・raw TPS は概念だけで key spelling が未定義 | × |
| actual `preceding_wait` | `kind:string`, `required_s:number`, `monotonic_start_ns:integer`, `monotonic_end_ns:integer` | ○ |
| `exec_witness` | `path:string`, `inode:integer`, `size:integer`, `sha256:string`, `monotonic_ns:integer` | ○ |
| `argv_raw`, `run_log` | 各 `FileRef` | ○ |
| `correctness_evidence[]` | `build:object`, `run_scope:object`, `outputs:FileRef[]`。同一 arm を表す key/location が未定義 | × |
| correctness `build` | `source:object`, `compile:object`, `binary:FileRef` | △ |
| correctness `compile` | `identity_sha256:string`, `argv:string[]`, `trace_enabled:boolean const true`, `analysis_enabled:boolean const true` | ○ key。cache/compile_commands との関係は未定義 |
| correctness `run_scope` | allocation/run を指す必要だけ記載。exact key 未定義 | × |
| `liveness[]` | `ordinal:integer`, `probe:string enum`, `monotonic_ns:integer`, `raw:FileRef` | ○。ただし arm/workload/allocation scope が欠落 |
| `admission_telemetry[]` | `ordinal:integer`, `kind:string enum`, `receipt:FileRef`, `fixed_inputs:object`, `ledger_evidence:object\|null` | ○ key、tag ごとの nullability は未定義 |
| `fixed_inputs` | `B:integer`, `seed:string`, `input_sha256:string` | ○ key、J/q/alpha への適用が矛盾 |
| `ledger_evidence` | `ledger_path:string`, `family_root:string`, `ordinal:integer`, `reservation_entry_sha256:string`, `reservation_commit:string` | ○ |
| `attempts[]` | `attempt_id:string`, `reason_code:string enum`, `replaces_attempt_id:string\|null`, `parent_attempt_id:string\|null`, `allocation_id:string\|null`, `submitted_at_monotonic_ns:integer`, `intent_ref:FileRef`, `performance_started_marker:object\|null`, `environment_observations:array`, `failure_evidence:object\|null` | ○。ただし `cluster_slot` と qsub raw が欠落 |
| marker | `path:string`, `size:integer`, `sha256:string`, `created_at_monotonic_ns:integer` | ○ |
| `failure_evidence` | `kind:string enum`, `pointer:FileRef` | ○ |
| `environment_observations[]` | `ordinal:integer`, `scope:string enum`, `run_id_or_null:string\|null`, `stat_before_raw:FileRef`, `stat_after_raw:FileRef`, `stat_before:integer[]`, `stat_after:integer[]`, `monotonic_start_ns:integer`, `monotonic_end_ns:integer`, `load1_diagnostic:number`, `malformed_reason_or_null:string\|null` | ○ |
| `returncode` | admission telemetry の exact key に存在しない | schema 上は禁止未知 key。negative test の意味を文書で明記する必要あり |

この表の `×` と矛盾を解消せず、架空の key を補った JSON Schema を承認してはならない。

#### 行対応表

| 正本の要求 | schema path |
|---|---|
| core/追補/errata/fold 束縛 [core:285–289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:285) | `preregistration.*` |
| environment・checkout・dependency [core:289–291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:289) | `environment`, `measurement_checkout`, `dependency_pins` |
| allocation・実順序・raw TPS [core:292–297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:292) | `allocations[]`, `planned_execution.runs[]`, `actual_runs[]`, `attempts[]` |
| `a01/a06` | allocation role、path choice、walltime、phase caps/events |
| `a02` | planned/actual `preceding_wait` |
| `a03` | `attempts[].environment_observations[]` |
| `a04` | marker、actual raw、`failure_evidence`、`reason_code` semantic branch |
| `a05` | arm binary/toolchain、exec witness、binary rehash |
| `a07` | workloads、effective flags、option map、actual argv/log |
| `a08` | source、configure argv、TU、cache、compile commands |
| `a09` | seed、algorithm、cluster slots、planned schedule |
| `a10` | J transcript。Monte Carlo 用でない fixed input 形を別途確定 |
| `a11` | q transcript |
| `a12` | stress-check transcript。`calibration_simulation` という kind 名も訂正対象 |
| `a13` | `ledger_evidence` と全履歴 semantic verifier |
| correctness/liveness 分離 [core:208–217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:208) | `correctness_evidence`, `liveness`, performance arm/allocation との非同一制約 |

### 1.5 承認 decision payload

現草案をそのまま承認する場合の観測値は以下だが、上記 blocker により使用してはならない。

- record reissue: commit `50b9c8de86685eaf7d828de1b61d87e07f8ef41e`、SHA `5f07e9…3d54`
- erratum-2: commit `9bed0a481204521d34a03e9877fcf7f46510d495`、SHA `9eb96f…885c`
- order: `[t139-core-s15-exactkey-v1, t139-core-s7-stresscheck-v1]`
- composed: `dfb821a5…678c`

approval-ready payload は、修正後 3 blob を先に commit した `B_docs` を使い、次の形にする。

```text
decision_kind = t139-preregistration-approval-supersession/v1

forward_supersedes:
  - D262
  - D263.reason[第2 erratum は既に承認済み、という事実文だけ]

preserved_decisions:
  - D263 の erratum_id 別 validator、未知 ID fail-closed
  - D264 の gate 完成までの非 export

target_core:
  path   = output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  commit = 88d68f9127b31df5aafc3d59607896626a1652e8
  sha256 = ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9

approved_blobs:
  addendum_a:
    path   = output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md
    commit = 622bd786191d40bda388596fa2adbf119ee84c9a
    sha256 = f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec
  derivation_map:
    path   = output/insights/2026-08-08_t139-r4-env-probe/derivation-map.md
    commit = 7ec088163dee920f0b8e1e9783faa6e36b22b730
    sha256 = bf5b6783b5a1a0b6c495618fe5292a968e44712d857cf84bdc436dcf027f6025
  erratum_t139_core_s15_exactkey_v1:
    path   = output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md
    commit = 1d235e0e455020cf54e66cf83304961910c369d8
    sha256 = a1abc60ef8e3f4346f61fbdd8282c295f353ca272062af02a856e3c5de9dd6d3
  record_items:
    path   = output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md
    commit = <B_docs>
    sha256 = <修正後 blob SHA-256>
  receipt_schema:
    path   = output/insights/2026-08-10_t139-manifest-land1/receipt-schema-v1.json
    commit = <B_docs>
    sha256 = <Draft 2020-12 schema の SHA-256>
  erratum_t139_core_s7_stresscheck_v1:
    path   = output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md
    commit = <B_docs>
    sha256 = <修正後 erratum SHA-256>

erratum_application_order =
  [t139-core-s15-exactkey-v1, t139-core-s7-stresscheck-v1]

composed_sha256 = <修正後 erratum から再計算>

non_approved_for_post_F_r_manifest:
  record_items_legacy:
    path   = output/insights/2026-08-08_t139-addendum-a/record-items.md
    commit = 1d235e0e455020cf54e66cf83304961910c369d8
    sha256 = 1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3
```

非承認文は次の意味を逐語で持たせる。

> D262 時点での歴史的な承認記録は改変しない。ただし `F_r` 以後の T-139 approval manifest において、旧 record-items blob `195702…8fd3` は `record_items` role の承認対象ではなく、resolver はこれを拒否しなければならない。

`commit` は decision/fold commit ではなく、3 blob が既に存在する fold 前の wave commit `B_docs` である。`F_r` はこの decision を fold した後で初めて生まれ、land 2 manifest が literal に参照する。

## §2 land 1 の実行手順

現時点では §1 の blocker 解消まで開始不可。解消後の手順は次のとおり。

### 2.1 local main から専用 worktree を作る

```bash
REPO_MAIN=/work/1/SFC/tanab/izanagi
LAND1_WT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-land1
LAND1_WAVE=dev-wave-t139-manifest-land1

git -C "$REPO_MAIN" status --short --branch
BASE_MAIN=$(git -C "$REPO_MAIN" rev-parse --verify refs/heads/main)

git -C "$REPO_MAIN" worktree add \
  -b worktree-dev-wave-t139-manifest-land1 \
  "$LAND1_WT" \
  "$BASE_MAIN"
```

第 1 波 tip や現在の w2 tipは branch 起点にしない。

### 2.2 第 1 波からファイル単位でのみ取り出す

```bash
git -C "$LAND1_WT" restore \
  --source=50b9c8de86685eaf7d828de1b61d87e07f8ef41e \
  -- output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md

git -C "$LAND1_WT" restore \
  --source=9bed0a481204521d34a03e9877fcf7f46510d495 \
  -- output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md
```

この 2 path を修正し、新規 schema を
`output/insights/2026-08-10_t139-manifest-land1/receipt-schema-v1.json`
へ置く。`orchestrator/` 配下へ schema を置くと land 1 の実装面になり得るため避ける。

第 1 波の commit を cherry-pick しない。特に次の未 land fragment はコピーしない。

- `docs/spool/decisions/2026-08-10-dev-wave-t139-manifest-w1-1.md`
- `docs/spool/worklog/2026-08-10-dev-wave-t139-manifest-w1-1.md`

### 2.3 3 blob を先に commit し、hash を commit object から計算する

```bash
git -C "$LAND1_WT" add -- \
  output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md \
  output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md \
  output/insights/2026-08-10_t139-manifest-land1/receipt-schema-v1.json

git -C "$LAND1_WT" commit -F /absolute/path/to/blob-commit-message
B_DOCS=$(git -C "$LAND1_WT" rev-parse HEAD)

git -C "$LAND1_WT" show \
  "$B_DOCS:output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md" |
  sha256sum

git -C "$LAND1_WT" show \
  "$B_DOCS:output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md" |
  sha256sum

git -C "$LAND1_WT" show \
  "$B_DOCS:output/insights/2026-08-10_t139-manifest-land1/receipt-schema-v1.json" |
  sha256sum
```

schema は Draft 2020-12 対応 validator の実体・版・argv も記録して meta-schema 検査する。Draft 7 で代用しない。

### 2.4 新しい land 1 専用 spool fragment を作る

作るのは次だけ。

- `docs/spool/decisions/2026-08-10-dev-wave-t139-manifest-land1-1.md`
- 受入実測後に `docs/spool/worklog/2026-08-10-dev-wave-t139-manifest-land1-1.md`

decision fragment は `wave: dev-wave-t139-manifest-land1` とし、`B_DOCS` と上で計算した digest を literal に持たせる。D262 は編集せず、前向きな新 decision にする。

worklog の `完了` / `更新` を使う場合、`base:` は現在の実体 item の SHA-256 であり、carry stub 自身の SHA ではない。[worklog spool README:81–86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/spool/worklog/README.md:81)

```bash
python3 tools/check_docs.py
python3 tools/spool_fold.py --dry-run
```

`check_docs.py` は stale `base` を検出しないため、`--dry-run` が必須である。[spool README:69–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/spool/README.md:69)

wave 側で `spool_fold.py` の実 fold を実行してはならない。fold は land tool が ff-only 後、同じ lock の中で行う。[spool README:82–99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/spool/README.md:82)

### 2.5 実装 byte が混入していないことの機械検査

許容 path を次の 5 本に固定する。

```text
output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md
output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md
output/insights/2026-08-10_t139-manifest-land1/receipt-schema-v1.json
docs/spool/decisions/2026-08-10-dev-wave-t139-manifest-land1-1.md
docs/spool/worklog/2026-08-10-dev-wave-t139-manifest-land1-1.md
```

次の比較の出力が空でなければ停止する。

```bash
TIP=$(git -C "$LAND1_WT" rev-parse HEAD)

comm -3 \
  <(printf '%s\n' \
    output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md \
    output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md \
    output/insights/2026-08-10_t139-manifest-land1/receipt-schema-v1.json \
    docs/spool/decisions/2026-08-10-dev-wave-t139-manifest-land1-1.md \
    docs/spool/worklog/2026-08-10-dev-wave-t139-manifest-land1-1.md |
    LC_ALL=C sort) \
  <(git -C "$LAND1_WT" diff --name-only "$BASE_MAIN..$TIP" |
    LC_ALL=C sort)
```

さらに mode/gitlink も検査する。

```bash
git -C "$LAND1_WT" diff --raw "$BASE_MAIN..$TIP"
git -C "$LAND1_WT" diff --summary "$BASE_MAIN..$TIP"
git -C "$LAND1_WT" diff --check "$BASE_MAIN..$TIP"

git -C "$LAND1_WT" diff --quiet "$BASE_MAIN..$TIP" -- \
  orchestrator tools hooks .claude .agents
```

判定基準は「実装行が 0」ではなく、実装 path の blob OID と mode に差が 1 byte もないことである。

### 2.6 docs-only でも受入全走を行う

docs-only は子実装を省けるだけで、受入実測は免除されない。[dev-wave core:11–15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/dev-wave/core.md:11)、[同:79–80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/dev-wave/core.md:79)

lease 取得後、最新 local main を取り込み、`HEAD..main == 0` を確認する。[pegasus-runbook.md:757–810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/pegasus-runbook.md:757)

```bash
export IZANAGI_WAVE_LEASE_DIR=/work/1/SFC/tanab/dev-wave-jobs/land-lease

LATEST_MAIN=$(git -C "$LAND1_WT" rev-parse main)
python3 tools/wave_land_window.py claim \
  --wave "$LAND1_WAVE" \
  --main-sha "$LATEST_MAIN"
```

`state` を JSON parse し、exact `acquired` のときだけ続ける。取得後に main が進んでいれば、runbook の `--no-ff --no-commit` 手順で provenance 付き merge commit を作る。更新後に allowlist と spool dry-run を再実行する。

```bash
T_ACCEPT=$(git -C "$LAND1_WT" rev-parse HEAD)
python3 tools/run_tests.py --force-dispatch
```

記録する証拠は、argv、`T_ACCEPT`、main SHA、queue/request/node、rc、passed/failed/skipped、duration、toolchain skip の有無。今回の read-only 監査ではこのコマンドを実行していない。

実測値を worklog fragment に記録して docs-only commit を 1 つ載せた後は、無限再走を避けるため次を行う。

1. `T_ACCEPT..final tip` が worklog/spool/output のみであることを exact path 比較。
2. `rg` でその path を読むテストを列挙。
3. 少なくとも `test_check_docs`、`test_spool_fold`、該当する frozen artifact/T-139 test を `tools/run_tests.py --force-dispatch` 経由で再走。
4. `check_docs.py` と `spool_fold.py --dry-run` を再実行。

これは repo の既存慣行にも一致する。[worklog 361:61–66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/archive/worklog-phase3-0810-361.md:61)

### 2.7 最終検査と land

```bash
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
python3 tools/spool_fold.py --dry-run
python3 tools/check_ai_provenance.py
```

最新 main 取り込み後の SHA を `TESTED_MAIN`、最終 tip を `TESTED_TIP` とし、監査列を exact `A..T` 順で渡す。

```bash
TESTED_MAIN=<受入直前に取り込んだ local main SHA>
TESTED_TIP=$(git -C "$LAND1_WT" rev-parse HEAD)

mapfile -t AUDITED < <(
  git -C "$LAND1_WT" rev-list --reverse "$TESTED_MAIN..$TESTED_TIP"
)

LAND_ARGS=(
  --main-worktree "$REPO_MAIN"
  --wave-worktree "$LAND1_WT"
  --tested-main-sha "$TESTED_MAIN"
  --tested-wave-tip-sha "$TESTED_TIP"
)

for COMMIT_SHA in "${AUDITED[@]}"; do
  LAND_ARGS+=(--audited-commit "$COMMIT_SHA")
done

python3 tools/dev_wave_land.py "${LAND_ARGS[@]}"
```

`dev_wave_land.py` は申告列と `git rev-list --reverse A..T` の完全一致を検査する [dev_wave_land.py:1078–1110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/tools/dev_wave_land.py:1078) うえで、main を ff-only にし、同じ lock 内で fold する [dev_wave_land.py:2380–2411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/tools/dev_wave_land.py:2380)。引数契約は [dev_wave_land.py:2429–2455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/tools/dev_wave_land.py:2429)。

どの終了経路でも lease を release する。

## §3 land 2 の実装プラン

### 3.1 実装単位、依存、行数

| 単位 | 編集面・既存根拠 | production | test | 依存 | pilot 1 本最小 |
|---|---|---:|---:|---|---|
| U0 approval manifest | 新規 `output/insights/.../approval-manifest.json`、`orchestrator/preregistration/approval_manifest.py`。根拠は [blobref.py:76–135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:76)、[erratum.py:470–509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:470) | 260 | 320 | `F_r` | 必須 |
| U1 resolver / opaque `PreregBinding` | 新規 `orchestrator/preregistration/resolver.py`, `binding.py`、後で [__init__.py:1–28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/__init__.py:1)。祖先検査の根拠 [trial_registry.py:671–746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/campaign/trial_registry.py:671) | 520 | 650 | U0 | 必須 |
| U2 Draft 2020-12 schema loader・semantic verifier・writer・`verify_prereg_receipt` | 新規 `orchestrator/preregistration/receipt_schema.py`, `receipt.py`。land 1 の schema blobを manifest から読む。単一 snapshot の根拠 [collector.py:287–300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/qualification/collector.py:287) | 1,500 | 1,050 | U0,U1 | 必須 |
| U3 `a13` alpha ledger | 新規 `orchestrator/preregistration/alpha_ledger.py`, tracked JSONL、[dev_wave_land.py:1839–1965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/tools/dev_wave_land.py:1839) の lock/fold 配線。全履歴先例 [trial_registry.py:1415–1457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/campaign/trial_registry.py:1415)、[同:1895–1935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/campaign/trial_registry.py:1895) | 520 | 650 | U1、時系列裁定 | 必須 |
| U4 schedule・durable intent・PBS preflight・submitter | 新規 `orchestrator/qualification/t139_schedule.py`, `t139_submission.py`, `tools/pegasus/submit_t139_pilot.py`, policy JSON。根拠 [submission.py:143–173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/qualification/submission.py:143)、[qsub_binding.py:30–92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/qualification/qsub_binding.py:30) | 800 | 850 | U1,U2,U3 | 必須 |
| U5 実 driver・iteration correctness | 新規 `orchestrator/qualification/t139_driver.py`, `tools/pegasus/t139_pilot.pbs`。process-group/receipt 根拠 [t126_driver.py:866–1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/qualification/t126_driver.py:866)、時間予算 [addendum:77–119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:77) | 1,500 | 1,400 | U2,U4 | 必須 |
| U6 collector・binding-required receipt publish | 新規 `orchestrator/qualification/t139_collector.py`, `tools/pegasus/collect_t139_pilot.py`。失敗回収先例 [collector.py:335–612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/qualification/collector.py:335) | 850 | 900 | U2,U4,U5 | 必須 |
| U7 8+2 campaign sequencer | 新規 `orchestrator/qualification/t139_pilot_campaign.py` | 300 | 350 | U6 | 除外。verification + pilot 1 は CLI で順次駆動可能 |
| U8 certified eligibility・J・選択 | 新規 `orchestrator/campaign/t139_pilot_analysis.py`。`a10` の J 導出 [addendum:630–753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:630) | 750 | 900 | U7、適格 8 本 | 除外。1 本では `n_p=8` を満たさず定義不能 |
| U9 材料 report・試行台帳 consumer | 新規 `orchestrator/campaign/t139_material_report.py`、[layer3_report.py:179–227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/campaign/layer3_report.py:179)、[trial_registry.py:2178–2432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/campaign/trial_registry.py:2178) を根拠に拡張 | 600 | 750 | U8 | 除外。receipt 1 本の検証には不要 |

最小集合 U0〜U6 は production 5,950 行 + test 5,820 行 = **11,770 行**。schema JSON も production に含む。

R4 全 scope の U0〜U9 は production 7,600 行 + test 7,820 行 = **15,420 行**。

「pilot 1 本」は性能 cluster 1 本を指す。その前に `a01` の verification allocation 1 本が必須なので、最小 E2E でも PBS 割当ては計 2 本である。U7〜U9 は最小集合から外せるが、R4 により land 2 完了前にはすべて必要であり、最小集合だけを land してはならない。

### 3.2 D264 の非 export 解除

現状は docstring と `__all__` が 4 名前の不在を固定している。[__init__.py:1–28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/__init__.py:1)、[test_t139_preregistration_binding.py:865–876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:865)

解除は次の条件をすべて満たす 1 commit で行う。

1. manifest が literal `F_r`、全 blob triple、errata order、composed digest、運用境界を持つ。
2. resolver が manifest を唯一の trust root とし、実 checkout から `measurement_head` を導出する。
3. `PreregBinding` は `init=False` または非公開 seal を持ち、caller が構築できない。
4. schema、全 semantic checks、full-history alpha ledger、writer sink、durable intent、PBS preflight、collector が実装済み。
5. hermetic two-commit repo + stub qsub/driver の正例が、実 qsub を呼ばず receipt publish まで通る。
6. negative tests と mutation が登録どおり検出する。

公開場所は前向き decision で明示する。

- `orchestrator.preregistration.resolve_effective_preregistration`
- `orchestrator.preregistration.PreregBinding`
- `orchestrator.preregistration.verify_prereg_receipt`
- `orchestrator.qualification.submit_pilot`

T-139 の `verify_receipt` は公開しない。既存 T-080 の [t080_freeze_migration.py:1957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/campaign/t080_freeze_migration.py:1957) は改名・変更しない。manifest に次の機能対応を置く。

```text
document_term = verify_receipt
implementation_api = orchestrator.preregistration.verify_prereg_receipt
```

D264 の旧 4 名前検査は、旧 `verify_receipt` が引き続き無いことと、新しい exact 4 API が上記条件成立時だけ公開される検査へ置換する。恒真 deny stub は作らず、leaf を module-private で完成させてから一度に export する。

### 3.3 `verify_prereg_receipt` の構造化理由

返却形は次の exact payload とする。

```text
PreregReceiptVerification:
  schema_version
  disposition             # accepted | rejected | indeterminate
  binding_sha256
  receipt_sha256
  predicates[]
  root_reason_ids[]

PredicateResult:
  predicate_id
  state                   # satisfied | violated | unavailable
  stage
  reason_code
  json_pointer_or_null
  expected_constraint
  observed_digest_or_null
  evidence_refs[]
  depends_on_reason_ids[]
  retryability            # never | same_bytes | new_external_state
```

主な `reason_code` は `receipt_io`、`duplicate_json_key`、`schema_violation`、`binding_mismatch`、`history_rewrite`、`dangling_reference`、`schedule_mismatch`、`attempt_outcome_mismatch`、`a03_evidence_mismatch`、`correctness_separation_mismatch`、`alpha_reservation_mismatch`。

これは pass/fail の言い換えではない。各 reason は、失敗した predicate、JSON pointer、期待制約、観測証拠 digest、上流依存を持ち、例えば「schema が壊れた」と「alpha 履歴が書換えられた」と「schedule predecessor が違う」を因果的に区別する。例外もこの形へ正規化し、未知例外は `indeterminate` かつ非受理とする。

### 3.4 `a13` append-only 全履歴検査

manifest / resolver / report に同一 bytes で置く wording は次とする。

> この保証は、指定された一つの canonical local main、その Git common directory、`tools/dev_wave_land.py` を通り同一 land lock 下で取り込まれた予約履歴、およびその全履歴を毎回再検査する trusted resolver/report の範囲に限る。独立 clone、別 common directory、権威台帳外の投入、履歴を共有しない writer、同一権限の非協調 writer、canonical main の外で作られた競合予約は保証しない。

manifest はこの文字列を `operational_boundary` に持つ。resolver は literal 一致を要求し、report はコピーでなく manifest bytes から再取得して同じ文字列を出す。

全履歴 verifier は次を行う。

1. shallow repository、replace ref、graft を拒否。
2. 固定 genesis/family root `88d68f…` から `measurement_head` まで `--full-history --reverse` で台帳 path を走査。
3. introduction が exact 1 回、regular 100644 であることを要求。
4. 各世代の blob が直前 blob の byte-prefix であることを要求。削除、truncate、既存行編集、並べ替え、rename/copy、delete-and-recreate を拒否。
5. JSONL 各行を duplicate-key 拒否付きで parse し、canonical bytes と末尾 LF を照合。
6. `(family_root, ordinal)` の全履歴一意性、current study の `F` / `k=1`、解放・tombstone 不在を検査。
7. receipt の `reservation_entry_sha256` と、当該行が初めて出現した `reservation_commit` を再導出。
8. resolver、receipt verifier、report consumer がそれぞれ全履歴を再走し、receipt の current-tip 申告を信用しない。

#### 新しい時系列 blocker

`a13` は pilot より前に canonical ledger へ reservation が存在することを要求する。[addendum-a-reissue.md:919–929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:919)

しかし R1 は次を同時に要求する。

1. land 2 前には manifest/producer を land しない。
2. manifest/producer/pilot は同一 land。
3. pilot は reservation が canonical main に入った後でなければ投入不可。
4. `dev_wave_land.py` は完成済み tested tip を一度だけ ff/fold する。

すると、

```text
reservation を canonical main に land
    → pilot 実行
    → receipt/result を commit
    → 同じ land の tested tip を land
```

の最初と最後に 2 回の main 更新が必要になる。land lock を 9〜11 時間保持しても、最初の ff 時点で将来の receipt を含む tested tip は存在しない。

これは R1 と R3 の再解釈ではなく、両者を同時に適用したときの新しい因果循環である。解決案をこちらで選んではならない。少なくとも「reservation の先行 main commit を land と数えるか」「別の canonical CAS/ref を認めるか」「eventual land を canonical とみなすか」のユーザー裁定が要る。

### 3.5 iteration 毎 correctness verifier

「iteration」は新しい candidate/source/build identity を作る反復と定義する。固定済み T-139 candidate の pilot cluster 8 本は同じ iteration 内の測定反復である。

- iteration 冒頭で verification allocation を 1 本投入。
- 性能 3 arm の trace-disabled/analysis-disabled build と、correctness/liveness 用の trace-enabled/analysis-enabled 3 build を同 allocation で生成。
- correctness は 2 workload × 3 arm を実行し、証拠 pointer と build identity を receipt に記録。
- anomaly は終端 reject。性能 allocation は 1 本も投入しない。
- 成功後だけ immutable performance binary を performance allocation へ stage。
- 各 performance attempt は verification receipt、source identity、performance binary digest を参照し、3 点 rehashする。
- trace-enabled binary/run を性能 allocation に入れない。core の分離規則は [preregistration.md:208–209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:208)。

candidate/build を変えた場合は同一 pilot の継続にせず、新 iteration として再び別 verification allocation を要求する。「8 cluster ごとに trace run」を性能 allocation 内で行う案は `a01` の verification 1 本契約と絶対規律 1 の双方に反する。

## §4 1 wave 可否の判定

### 計算

- 実装総量: production 7,600 + test 7,820 = **15,420 行**
- 最小 vertical slice: **11,770 行**
- 必須 PBS: verification 1 + 適格 pilot 8 = **9 allocation**
- 予備を使う最大: 1 + 8 + 2 = **11 allocation**
- 各 allocation: 3,600 秒
- 逐次 walltime: 必須 9 時間、最大 11 時間
- 受入全走: 516 秒 = 8.6 分、最終 1 回だけでも必要
- これに queue 待ち、collector、失敗時 replacement、mutation、docs/provenance、land が加わる。

理論上は verification 後に複数 performance allocation を並列化すれば allocation critical path を 2 時間へ下げられる。しかし、core は pilot 1 本目から scheduler 会計を検証し「1 本ずつ保守的に上限を更新」とする。[preregistration.md:271–276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:271) また、PBS allocation は node 専有を保証せず、単独性確認は計算 node 上で必要である。[pegasus-runbook.md:617–623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/pegasus-runbook.md:617)

したがって 8 本同時投入を 1-session 可否の前提にはできない。

### 判定

**land 2 は 1 wave＝1 session には収まらない。**

構造的に安全な session checkpoint は次の 2 つである。

- **pilot 1 本まで:** verification + performance cluster 1 本を完了し、実 qsub、collector、receipt、会計単価まで E2E で確認できる。残り 7 本へ費用を投じる前の最も安全な中断点。ただし J/適格集合/選択/report は未定義。
- **pilot 8 本まで:** pilot raw が科学的に完結し、U8/U9 が実行可能になる。最終 land 候補に近いが、consumer/report/registry と受入が残る。

R1 の「同一 land」により、pilot 1 本地点での中間 land は不可。安全なのは、同じ未 land branch と durable artifact を別 session が引き継ぎ、最終的に 1 回だけ land する形に限られる。もし「wave」を「land 1 回」ではなく「単一 session」と同一視するなら、どちらの切り方も新裁定が必要である。

さらに §3.4 の reservation 循環が解決されるまでは、pilot 1 本地点自体へ到達できない。

## §5 変異事前登録の候補

以下は実装前登録候補であり、まだ実行していない。

| # | 変異位置 | 期待する受理集合の変化 | 期待 node |
|---:|---|---|---|
| M1 | manifest resolver から literal `F_r` 祖先検査を削除 | `F_r` より前・別 decision の blob が通り拡大 | `test_manifest_requires_literal_approval_fold_ancestor` |
| M2 | manifest の record/schema/erratum triple の SHA 比較を caller 値との自己整合へ置換 | 未承認 blob が通り拡大 | `test_caller_refs_cannot_replace_approved_blob_set` |
| M3 | `DRAFT_ERRATA` を approved membership に混ぜる | 未承認 erratum が通り拡大 | `test_draft_erratum_is_not_approved_by_manifest` |
| M4 | composed digest または errata order の照合を削除 | 部分適用・別順序が通り拡大 | `test_manifest_order_and_composed_digest_are_exact` |
| M5 | `PreregBinding` に public constructorを戻す | forged binding から submit/write が通り拡大 | `test_binding_cannot_be_constructed_outside_resolver` |
| M6 | `measurement_head` を public 引数にする | caller 選択 checkout が通り拡大 | `test_measurement_head_is_derived_from_checkout` |
| M7 | schema の nested object 1 個を `additionalProperties:true` にする | eligibility/verdict 等の未知 field が通り拡大 | `test_every_instance_object_schema_is_closed` |
| M8 | `required` から marker/intent/raw pointer の 1 key を除く | 不完全 receipt が通り拡大 | `test_every_declared_key_is_required_or_explicitly_nullable` |
| M9 | Draft 2020-12 を Draft 7 validator で読む | unevaluated keyword の差により受理集合が実装依存化 | `test_schema_requires_draft_2020_12_engine` |
| M10 | duplicate-key reject を通常の `json.loads` 後へ移す | 同名 key 二値 receipt が通り拡大 | `test_duplicate_json_keys_fail_before_schema_validation` |
| M11 | full-history ledger 検査を current tip の重複検査だけへ戻す | 削除後の `(F,1)` 再利用が通り拡大 | `test_alpha_ledger_rejects_delete_and_reuse_history` |
| M12 | prefix 検査を set inclusion に弱める | 過去行編集・並べ替えが通り拡大 | `test_alpha_ledger_every_generation_is_strict_byte_prefix` |
| M13 | manifest/report/resolver の boundary wording を 1 byte 変える | 互いに異なる保証境界を名乗る artifact が通る | `test_operational_boundary_is_byte_identical_everywhere` |
| M14 | qsub の後に submission intent を書く | receipt に残らない orphan execution が生じ、受理集合が拡大 | `test_intent_is_durable_before_qsub_invocation` |
| M15 | qsub 非 0 row または job-preflight reject を collector が無視 | favorable attempt だけの receipt が通り拡大 | `test_every_canonical_intent_has_exactly_one_attempt_row` |
| M16 | a09 schedule を runtime random、または replacement に新 slotを採番 | 未登録 schedule が通り拡大 | `test_schedule_and_replacement_slot_are_rederived_exactly` |
| M17 | `/proc/stat` readerを定数 fixtureへ置換 | fabricated a03 evidence が producer testを通り拡大 | `test_a03_reader_captures_two_real_raw_snapshots` |
| M18 | marker 不在だけで pre-performance と分類 | performance raw を持つ attempt が置換可能になり拡大 | `test_raw_performance_trace_cannot_map_to_pre_failure` |
| M19 | correctness を全 pilot 後に一度だけ実行、または性能 allocation 内へ移す | correctness 未確認/trace-enabled 性能値が通り拡大 | `test_verification_precedes_every_performance_allocation_and_is_disjoint` |
| M20 | `binary_rehash` を 3 arm 合計 3 件にする | 2 arm の各時点 hash を欠く allocation が通り拡大 | `test_all_three_arms_have_all_three_rehash_points` |
| M21 | receipt writer から keyword-only binding 再検査を外し、caller 前段だけで検査 | alternate writer path が forged receipt を publishでき、拡大 | `test_only_binding_required_sink_can_publish_receipt` |
| M22 | structured reason を `{"passed":false}` だけへ縮める | 因果 reason contract の受理集合が非構造化 payload まで拡大 | `test_rejection_contains_causal_predicate_and_evidence_edges` |
| M23 | 適格 8 本を 7 本で可、または予備 2 本を母数へ合算 | `n_p=8` 未充足または reserve 混入でも J を出し、拡大 | `test_pilot_requires_exactly_eight_eligible_nonreserve_clusters` |
| M24 | consumer が `declared_use_class` / `reason_code` / `exclusivity` / `returncode` を受理入力に使う | producer 自己申告で certified 集合が変わり拡大・縮小 | `test_declared_receipt_values_are_not_acceptance_dependencies` |
| M25 | report が failed attempt を落とす、または cached verdict を使い validator を再実行しない | favorable subset/stale verdict が formal reportへ入り拡大 | `test_report_and_trial_registry_rerun_validator_and_cover_all_attempts` |

wave 前の実コードと同型の必須変異は M26 として独立登録する。

```python
def require_exact_fields(
    blob: bytes,
    expected: frozenset[str] = T139_EXACT_FIELDS,
) -> None:
```

これは現に [addendum_envelope.py:152–158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/addendum_envelope.py:152) に存在する caller-selectable API である。

- **変異:** approved resolver が専用 `require_approved_addendum_a_fields()` ではなく、`expected={a01,…,a12}` を渡した `require_exact_fields()` を呼ぶ。
- **期待変化:** `a13` を欠く addendum が通り、受理集合が拡大。
- **期待 node:** `test_approved_resolver_cannot_supply_a_caller_selected_field_set`。

これは架空の禁止形ではなく、wave 前の実コードと逐語同型である。

## §6 親 brief の誤り

実測値の不一致は 0 件だった。誤りは測定から導いた一般化・実装可能性に 7 件ある。

| P | 判定 |
|---|---|
| P1 [brief:56–57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s1-brief.md:56) | local main から docs-only branch を切る方向自体は正しい。ただし branch 起点だけでは w1 fragment/実装混入を証明しないので、§2 の exact path allowlist が必要。これは不備だが独立の誤った事実としては数えない。 |
| P2 [brief:58–59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s1-brief.md:58) | **誤り 1:** reissue と exact 1:1 の schema を直ちに書けるという一般化は偽。複数 object の key 名自体が未定義。**誤り 2:** Draft 2020-12 の validation 実体を依存計画に含めていない。現環境は 3.2.0/Draft 7。 |
| P3 [brief:60–63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s1-brief.md:60) | **誤り 3:** `dfb821…` を approval-ready composed digest として固定しているが、core 333 行の較正義務が残る。**誤り 4:** payload が receipt schema/erratum-2 の完全な approved triple と D263 の事実誤り supersession を明示していない。 |
| P4 [brief:64–65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s1-brief.md:64) | b03 公表台帳を scope 外とする点は確定裁定と整合。誤りなし。 |
| P5 [brief:66–69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s1-brief.md:66) | **誤り 5:** 4,900–6,000 production + 2,550–3,200 test は R4 の consumer/report/全履歴/2020-12 schema を過少計上。再見積りは 7,600 + 7,820。**誤り 6:** 問題を「land 2 を分割するか」だけに還元し、複数 session で同一未 land branch を継承する場合と、R1/R3 の reservation 時系列循環を区別していない。 |
| P6 [brief:70–71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s1-brief.md:70) | **誤り 7:** 「pilot の 8 slot」は不正確。`a09` は slot 1〜13 全表を導出し、pilot はそのうち適格 8 本を消費、replacement は同 slot を再利用する。また並列性は runbook だけの問題ではなく、1 本ずつの費用更新と環境干渉を含む事前登録上の制約である。 |

## 総括

1 wave 可否: **不可**。実装 15,420 行、PBS 9〜11 時間相当、かつ R1/R3 の reservation 時系列 blocker がある。  
land 1 の 3 文書に見つけた blocker 級欠陥: **6 件**。  
pilot 1 本までの最小集合: **11,770 行**（production 5,950 + test 5,820）。  
親 brief の誤り: **7 件**（実測値の不一致 0、一般化・実装計画の誤り 7）。