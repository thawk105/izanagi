# 段 4 裁定 — [T-2145] sort SWO oracle の受理言語を検証済み IR へ縮める

親 = dev-wave manager。基準 = 着手時 local main `82a259c0a`。裁定時 main = `2fa13a262`。

## 裁定 inbox の再走査 (DW-S04)

wave 開始後に main へ着地した裁定は **D1475〜D1485 の 11 件** (worklog entry 1188、
/rulings 全件 第 2 回)。この範囲を `sort` / `oracle` / `IR` / `受理` / `comparator` /
`SWO` / `文法` で走査した結果 **該当 0 件**。[T-2145] の台帳本文も entry 1188 で
書き換わっておらず持ち越しのままである。本 wave を縛る新裁定は無い。

## 親 brief の誤りの訂正 (レンズ B 所見 10 が実測で覆した)

brief と段 2 プランは「`test_sort_swo_oracle.py` は D669 で受入全走から恒久除外されている」
と書いた。**これは現行コードと一致しない。**
`orchestrator/test_selection_contract.py:61` は `SANCTIONED_EXCLUSIONS = ()` の空 tuple であり、
`tools/run_tests.py:185` はその空集合を runtime の active table として使う。
D669 は decisions に残るが、除外を解除した裁定は見当たらず、実装側の表だけが空になっている。
**本 wave は現行コードを事実として扱う** — すなわち当該 file は受入全走に載る。
D669 と実装の不一致そのものは本 wave の主題ではないので追わない (`DW-G05`)。
新設 node の実行コストは、この事実を前提に裁定する (R6)。

## 所見の裁定

| # | 所見 | 裁定 | 根拠 |
|---|---|---|---|
| A1 | 親実測だけでは全受理集合の包含を証明していない | **real・採用** | 測っていない層の列挙は正しい。主張を縮める (R8) |
| A2 | evaluator 食い違いの具体条件。ただし一致検査が生きていれば拡大しない | **real・採用** | 一致検査を load-bearing と明記する |
| A3 | 行列不一致の帰属が未解決 | **real・採用** | R1 で確定 |
| A4 | `while(true){break;}` 反証は一般証明ではない (nit) | **real・採用 (nit)** | 記述を「admitted 実体を build するから安全」へ改める |
| A5 | 79 値から certified 15 組への漏出は無い | **refuted (漏出無しを確認)** | 5 層の配線を辿った証拠が十分。P1-d を維持 |
| A6 | 79 値は全件 SWO。証明の種類が変わる | **real・採用** | 保証境界の書き換えで明示 (R10) |
| A7 | critic が新 rejection を受理できない | **real・採用 (must-fix)** | R3 |
| A8 | UNAVAILABLE が黙って PASS になる経路は無い | **refuted (経路無しを確認)** | 現行 fail-closed を維持 |
| B1 | IR admission と effect gate が二重権威 | **refuted** | R2。既存 backoff 軸が同じ並びで承認済み |
| B2 | 旧 validator は恒真化。compile 対象が未確定 | **real・採用** | R1 |
| B3 | canonical 79 の実測だけでは包含の完全証明にならない | **real・採用** | R1 が materialize 側で解消、R8 で主張を確定 |
| B4 | 変更が効く層の scope 不足 | **real・採用** | R5 |
| B5 | critic digest が新 reason を受理できない | **real・採用 (A7 と同一)** | R3 |
| B6 | 変異 node が全件未実在 | **real・採用** | R9 |
| B7 | D345 の contract ID 閉包は閉じている | **refuted (閉じているを確認)** | プラン維持 |
| B8 | D901 の cache 束縛だけ欠ける | **real・scope 外** | R7 |
| B9 | campaign identity の説明が旧実験のまま | **real・採用 (must-fix)** | R4 |
| B10 | 79 TU node は受入全走にも載る | **real・採用** | R6。親 brief の誤りを覆した |

## R1 — compile 対象と行列不一致の帰属 (最重要)

**裁定: admission は raw テキストを受け、canonical 形へ正準化し、正準形を材へ再 materialize する。
compile 対象・build 対象・照合対象はすべてこの正準形に一致させる。行列不一致は
`UNAVAILABLE` とし、候補の `REJECT` にしない。**

根拠は**既存の承認済み実装がすでにこの形である**ことである。backoff 軸は
`orchestrator/campaign/p3_s4_loop.py:359`-`:375` で、effect gate 通過後に
`validate_backoff_implementation(implementation)` を呼び、受理したら
`canonicalize_backoff_implementation(implementation)` の結果で
`render_hole(base_text, marker, canonical)` を**やり直して** materialize している。
つまり build に入るのは候補の raw bytes ではなく正準形である。

これを sort へ対称に置くと、両レンズの対立が同時に解ける。

- レンズ A の「renderer を candidate TU の代用品にするな」は満たされる。renderer 出力は
  代用品ではなく**実際に build される実体そのもの**になるからである。
- レンズ B の「正準形を compile するなら不一致は oracle 故障」は成立する。候補には
  正準形の token 列以外を build へ入れる自由が無く、不一致は evaluator・compiler・TU・
  pointer mapping の drift でしか起きない。D344 決定 4 の「候補に帰属できない故障は
  `REJECT` ではなく `UNAVAILABLE` とし、受理集合・fitness・試行台帳に混ぜない」に該当する。
- 規律 2 は緩まない。不一致が `PASS` になる経路は作らない。`UNAVAILABLE` は
  `s1_direct_comparison.py:958`-`:968` で retryable、`p3_s4_loop_sort.py:225`-`:234` で
  attempt-infra として WAL に残り停止する。どちらも受理集合を広げない。

正準化は**意味を保存する範囲に限る**。admission は token 列が 79 値のいずれかの正準 token 列と
完全一致することを要求し、token 間の空白だけを自由にする。コメント、行連結、raw string、
UCN、代替トークンは受理しない。これにより「正準化が意味を変えない」ことが構成的に従う。

## R2 — 受理権威の役割分離 (台帳が求めた 4 点の第 1)

**裁定: 二重権威ではない。レンズ B 所見 1 は refuted。ただし表現は改める。**

`coder_effect_gate` は `p3_s4_loop.py:330`-`:358` で `passed=False` を作る経路しか持たない
**deny-only の veto** であり、候補を受理する権限を持たない。T-396 で破棄された設計は
同じ hole を独立に**受理と主張できる**機構が 2 つ並ぶ形であり、deny-only の前置 veto は
それに当たらない。決定的な根拠は、**backoff 軸が既に「effect gate → 軸固有文法 admission」の
並びで承認・稼働している**ことである (`p3_s4_loop.py:330`-`:375`)。これが T-396 の失敗型なら
backoff 側が先に壊れている。

本 wave 後の役割は次で確定する。

| 機構 | 位置づけ |
|---|---|
| sort IR admission | **(a) 受理権威。** sort comparator 言語へ入れてよいと言える唯一の機構 |
| `_validate_single_sort_statement` | **(b) 恒真化。** 正準形にだけ適用する事後条件。gate として数えない |
| `coder_effect_gate.DENY_TABLE` | **(c) 別の関心事。** 全 hole 共通の deny-only veto。受理はしない |
| `check_relation_matrix` | **(b) 恒真化 (候補 gate として)。** 79 値は構成上すべて SWO。trusted 行列の違反は evaluator 故障 |
| 実 TU conformance 照合 | **(c) 別の関心事。** 候補ではなく実装・環境の drift 検出器。違反は `UNAVAILABLE` |
| `sort_comparator_authority` | **(a) 別 domain の受理権威。** certified `sort_best` の 15 組専用。触らない |

**恒真化する 2 者を実効 gate として数えない。** 成果物には「候補の SWO 違反を動的に見つける
gate」ではなく「構成的に SWO な言語への membership + 実 TU conformance」と書く。

## R3 — critic consumer の取り残し (must-fix)

**裁定: 採用・scope 内。** 新設 gate の追加ではなく、既存 producer/consumer 契約の修正である。
`orchestrator/critic/digest.py:390`-`:399` の `structure` reason の閉じた集合へ
`sort-ir.*` の admission reason を追加する。R1 により行列不一致は `UNAVAILABLE` になるので、
`mutation` kind と reason は**追加しない** (レンズ B 所見 5 の後段どおり)。

## R4 — campaign identity の説明 (must-fix)

**裁定: 採用・scope 内。** `p3_s4_loop_sort.py:314`-`:319` の `spec_content` は
campaign identity の preimage (`ident.py:212`-`:218`) に入るため、raw C++ 独立合成を
名乗ったままにすると、新 campaign の proof chain が実験の中身と食い違う。
D1451 が求める「別実験になる点の明示」はここに書くのが正しい位置である。
`spec_content`、`CoderProposalSort` の説明、agent 契約を同じ変更単位で更新する。
**D344 は元の raw 実験について有効なままと明記し、supersede したとは書かない。**

## R5 — 実装 scope

追加する層 (レンズ B 所見 4 のうち採用分)。

- `orchestrator/campaign/p3_s4_loop.py` — sort marker (`"silo-writeset-sort"`) の
  admission 分岐。backoff 分岐 (`:359`-`:375`) と対称に置く
- `orchestrator/campaign/p3_s4_loop_sort.py` — `spec_content` と proposal 説明
- `orchestrator/critic/digest.py` — structure reason の追加
- `orchestrator/tests/conftest.py:576`-`:606` — 新 TU node の oracle environment registry 登録

触らない層。`s1_known_axes_freeze.py` と `sort_comparator_authority.py` (D1357、P1-d)。
`s1_direct_comparison.py` は production 編集不要 (15 組が新 admission を通ることは実測で確認済み)。

## R6 — 79 値 conformance 検査の実行形

**裁定: 単一 batch TU で 79 comparator を compile し、153,576 セルを全件照合する。**

理由は R6 の前提が変わったことである。当該 file は受入全走に載る (上記訂正)。
79 回の独立 compile を受入全走と 3 変異走で反復すると 316 回以上の TU compile が増える。
**検査範囲は 1 セルも減らさない。** 失うのは「79 値それぞれが独立の public compile /
preflight / postflight を通る」保証であり、これは**明記する**。public 経路そのものは
既存 node が被覆しており、本 node の目的は evaluator の conformance である。
受入全走から外す案は採らない (新しい selection policy 裁定が要るため)。

## R7 — D901 の cache 束縛の一般化

**裁定: 本 wave では採らない。scope 外。** D901 は backoff 軸限定の裁定であり、
sort へ広げるのは `DW-G03` の族一般化に当たる。独立 2 例の要件を満たさず、
かつレンズ B が「certified 値・受理集合・参照が変わる具体例は未確認」と実測している。
仮想リスク向けの機構を足さないという依頼にも反する。
裁定パッケージへ「D901 を backoff 限定のまま維持する」を推奨として載せる。

## R8 — 受理集合の包含の証明 (台帳が求めた 4 点の第 4)

**裁定: 主張は次の形で確定する。**

R1 により、admission を通った候補が**材へ入る実体は 79 個の正準形のいずれかに限られる**。
したがって materialize される受理集合はちょうど 79 個であり、その全件が現行の
`_validate_single_sort_statement` と `coder_effect_gate.scan_host_effects` を通ることは
親が段 1 で実測済みである (失敗 0)。**materialize 面での包含はこれで閉じる。**

**主張してよい:** 本変更後に build へ入りうる sort comparator の集合は 79 個の正準形に等しく、
その全件が変更前の 2 つの受理 gate を通る。現行の権威集合 15 件はその真部分集合である
(byte exact、欠落 0 を実測)。

**主張してはいけない:** 全 consumer 経路を通した完全な包含証明。レンズ A が列挙した
diff 検疫・auditor・依存検証・broker 実行・build・S1/floor consumer・receipt・台帳は
親 probe の測定範囲外である。最終確認は段 6 の実 TU 全件一致と public 境界の実走に委ねる。

## R9 — 変異事前登録 (DW-M01)

段 2 の候補から、R1 の裁定に合わせて改訂する。**登録名は予定名であり、実装後に
collected nodeid の実在を親が再確認する** (レンズ B 所見 6)。
F568 のとおり contract identity を pin する node はどの変異でも落ちるので、
`test_contract_manifest_hashes_and_literal_are_exact_snapshot` と
`_CURRENT_ORACLE_CONTRACT_ID_GOLDEN` による赤は**どの変異の kill 根拠にも数えない**。

| # | 変異 | 機構固有の落ち先 (予定名) |
|---|---|---|
| M1 | admission の duplicate-field 拒否を削除 | `..._rejects_non_ir_before_environment[duplicate-field]` |
| M2 | admission を素通りさせ、非 IR を固定 IR として扱う | `..._rejects_non_ir_before_environment[generic-lambda]` |
| M3 | renderer の asc/desc operand を反転 | `test_sort_ir_domain_roundtrips_all_79_values` |
| M4 | evaluator が `storage_` を signed 32bit と解釈 | batch conformance node |
| M5 | pointer rank の aliases / separate を逆転 | batch conformance node |
| M6 | `key_` を最初の NUL で切る | batch conformance node |
| M7 | 実 TU 不一致時に `UNAVAILABLE` を返さず PASS する | `..._mismatch_is_unavailable_not_pass` |
| M8 | contract components から pointer mapping key を削除 | `test_contract_digest_binds_sort_ir_grammar_and_pointer_mapping` |
| M9 | 正準化を省いて raw を materialize する | `test_materialized_hole_is_canonical_form` |
| M10 | **過剰拒否の正例対照** — admission が 15 組のいずれかを拒否する | `test_sort_authority_15_is_byte_exact_subset_of_rendered_ir_domain` |

M2 は「例外で死ぬ」変異にしない (レンズ B 所見 6)。M10 は `DW-M01` が
受理集合を縮小する wave へ課す**承認外の過剰拒否の正例**である。
M4〜M6 は batch conformance node 1 本を共有するため、T-2113 と同じく
判別力のある IR を各 1 件ずつ用意して単一理由性を確保する。

## R10 — 保証境界の書き換え

`SORT_SWO_GUARANTEE_BOUNDARY` (`sort_swo_oracle.py:89`-`:93`) と module docstring から
「報告行列が真の関係であることを保証しない」を削除し、次の範囲へ置き換える。

- admitted IR、versioned corpus、contract 束縛済み pointer mapping に限り、
  trusted evaluator が関係行列を生成し、実 TU の全観測行列との byte exact 一致を PASS 条件にする
- 任意 C++ 全入力に対する SWO の証明ではない
- **候補の SWO 違反を動的に探す gate ではなくなった**ことを明記する (A6/R2)
- 供給網検証は現行どおり。本 wave で広げない

同じ旧文言を持つ `s8b_sort_swo_receipt.py` も同じ変更単位で更新する。

## 新しい policy 選択の要否

**無し。** R7 (D901 の一般化) と「79 compile node を受入全走から外す」の 2 つが
新 policy になりうる択一だったが、どちらも**採らない**裁定にしたため発生しない。
他はすべて D344 決定 4、D345、D1357、D1451、`DW-G03`、`DW-M01`、規律 2 から導ける。
ユーザーへ返すのは裁定パッケージの推奨 1 件 (D901 を backoff 限定のまま維持) だけであり、
これは本 wave の実装を止めない。

## 段 5 の分割

実装子 1 本。admission・正準化・renderer・evaluator・contract・呼び出し側・critic・
保証境界は producer/consumer 契約が 1 単位であり分割すると契約が壊れる
(並行 fix が契約を壊す既知の型)。テストも同じ子が書く。
