## 前提の確認

指定された 6 資料をすべて全文読了し、repo 内の実装・T396 先例を静的に照合した。書き込み、pytest、compile、driver、oracle 実行は行っていない。したがって Q1〜Q3 は未実測であり、緑とは判定しない。

アンカー訂正は 2 点ある。

- exact binding の関数は `sort_comparator_authority.py:59`、実検査は `:62-65`。brief の `:58` は空行。
- allocator 順は `sort_swo_oracle.py:1182-1183`。brief の `:1183-1184` は一行ずれている。

## 所見

**所見 1 — proxy は型分岐攻撃を表現不能にするが、実型保証の代替にはならない。現プランの Q2 は生死判定として不足している。**

- 所見: 31 値 IR が唯一の入力となり、raw C++ の別入口が消えるなら、`sizeof` / type trait / cast による候補側の型分岐は構造的に不可能になる。この意味では D344 の模擬型穴は閉じる。しかし段 2 の Python evaluator と proxy C++ harness は依然として模擬意味系であり、「現行 oracle の実型関係行列を再現した」という証拠にはならない。raw C++ を比較対象に戻せば、例えば proxy の `sizeof` のときだけ `<`、実型のときは `<=` を返す comparator が具体的な反例になる。31 値内でも pointer `<` は実型オブジェクトの関係と compiler に依存するため、proxy の単調 address 順と一致する保証がない。
- 根拠 file:line: D344 は実型を必須とする `verbatim-d344.txt:6-13,27-34`。段 2 は proxy を採用する `s2-plan.md:105-124` 一方、自身も実 oracle 実測ではないと認める `:160-162`。現行 TU は実 header を include する `sort_swo_oracle.py:789-792`、実 `WriteElement<Tuple>` を呼ぶ `:934-959`。実 field 型は `external/ccbench/include/op_element.hh:19-21`、継承・追加状態は `external/ccbench/cc/silo/include/silo_op_element.hh:39-79`。
- 成果物影響: proxy 一致だけなら材料レポートの値は `typed-field-proxy/provisional` に限る。`q2=true`、台帳上の「生死確認=true」、実装 wave 起票、certified 選択結果の oracle receipt 置換へ昇格させてはいけない。実型 conformance が不可なら Q2 は `UNAVAILABLE` とするのが D344 の境界に整合する。
- scope: driver と判定語彙の修正は本 wave scope 内。実型 end-to-end 実測が環境上できなければ実施自体は scope 外でもよいが、その不在を PASS に変換することは scope 内で禁止すべき。

現行 TU が持ち、proxy evaluator へ置き換えると失われる保証は少なくとも次である。

- 実型での member lookup、access、operator overload、暗黙変換、実 header/macros/ABI による compile 可否。
- 実 ctor、実 layout/alignment/lifetime、実 allocator 上の pointer semantics。
- materialized statement 自身と proposal bytes の対応。
- 実 comparator の throw、abort、call-count 異常。
- 3 process/order 間の relation 不一致検出。
- read-only corpus、seccomp、専用 protocol 経路。
- compiler、compile flags、dependency manifest、TU bytes を含む receipt。

これらは `sort_swo_oracle.py:934-959,1170-1239,2442-2483,2610-2629` に実装されている。

**所見 2 — IR 導入後の受理権威が未定義で、T396 と同型の二重化または弱い gate の恒真化が起こる。**

- 所見: 現在は autonomous sort と certified `sort_best` で権威が異なる。IR parser を両方へ雑に差すと、31 値 membership と 15 組 exact binding が同じ artifact に並ぶ。D1357 に従えば certified `sort_best` の権威は name/IR または name/canonical-render の exact binding 一本でなければならず、31 値 parser はその権威を名乗れない。
- 根拠 file:line: T396 の破棄理由は「同じ hole に受理権威が二つ並ぶ」ことだった `output/insights/2026-08-15_t396-hole-allowlist-refuted/README.md:22-28`。現行 autonomous 経路は `p3_s4_loop.py:275-292` の quarantine/effect gate、`p3_s4_loop_sort.py:151-169` の auditor、`:170-229` の SWO oracle。構造 gate は `sort_swo_oracle.py:523-585,2687-2700`。certified 選択の exact binding は `sort_comparator_authority.py:54-65`、生成・再検証は `s1_known_axes_freeze.py:494-540,842-850`。
- 成果物影響: certified 選択結果では exact binding を残し、31 値を権威集合として流用してはならない。材料レポートには次表の役割分離を明記する必要がある。台帳に単に「IR gate 導入」と書くと、どの reject が実効だったか失われる。
- scope: 役割設計と材料レポートへの明記は本 wave scope 内。実配線変更は後続 wave。

| 面 | IR 後の役割 |
|---|---|
| IR parser | autonomous proposal の唯一の source-language admission |
| `_validate_single_sort_statement` | trusted renderer 出力に対しては恒真。renderer/materializer drift 検査として残すならそう明記 |
| `coder_effect_gate` | canonical renderer が固定表現だけを出すなら恒真。raw C++ 別入口の監視以外の受理権威にはならない |
| SWO oracle | 廃止するなら「呼ばれない」と receipt を改版。残すなら実型 renderer-conformance gate として位置付ける |
| exact binding | certified `sort_best` の唯一の選択権威。31 値一般 admission と混同しない |

**所見 3 — 「規律 2 に従い受理集合が狭まる」は、現状では集合間写像が未定義で証明されていない。**

- 所見: raw C++ 文字列集合と IR tuple 集合は別の集合なので、そのままでは部分集合関係を述べられない。`render(IR)` を介し、全 render 値が現在の quarantine、effect gate、構造 gate、実型 SWO oracle を通ることまで示して初めて縮小を主張できる。段 2 は proxy までしか示さない。
- 根拠 file:line: 現行構造 reject は `sort_swo_oracle.py:523-585`、effect reject は `coder_effect_gate.py:527-562,576-610`、実 oracle の NONDETERMINISTIC/AXIOM reject は `sort_swo_oracle.py:2442-2483`。段 2 の比較先は proxy `s2-plan.md:103-162`。
- 逆に広がる具体経路:
  - `while (true) { break; }` の後に key `<` を返す raw comparator は extensional には `single/key/asc` と同じだが、現行 effect gate は無条件 loop として reject し、IR は accept する。
  - `"return a.key_ < b.key_;"` は現行 outer-shape gate でも reject される一方、対応する IR は accept する。これは段 2 自身の probe `s2-plan.md:177-185` でも確認対象になっている。
  - pointer rank evaluator が accept しても、実型 oracle が pointer relation の order 不一致または SWO 反例を返す可能性がある。
  - IR evaluator が relation matrix を直接作り、`p3_s4_loop_sort.py:185-219` の呼出し自体を削れば、現行 oracle が reject した compile/runtime/anomaly は観測されなくなる。
- 成果物影響: 材料レポートは「構文能力を縮める見込み」と「現行 accepted-render set の部分集合」を分ける必要がある。後者未証明のまま true とすると certified 選択結果が現行 reject を取り込み、台帳の「規律 2 不変」が偽になる。
- scope: 部分集合の定義と 31 canonical rendering の production-gate conformance 条件は本 wave scope 内。全 integration 実装は後続 scope。

**所見 4 — 現行 TU pin は既存 receipt の drift を捕捉するが、段 2 driver の pointer 規則は TU 変更後も黙って PASS できる。**

- 所見: `TU_TEMPLATE_SHA256` は現行 TU の allocation/mapping bytes を含むため、既存 oracle receipt には有効である。しかし段 2 driver は hash を出力するだけで、proxy allocation と `pointer_rank` を TU から導出も照合もしない。例えば TU を `separate` 先行 allocation に変えても、driver の proxy と Python がとも旧「aliases 先行」のままなら相互一致し、新しい TU hash を添えて PASS できる。
- 根拠 file:line: corpus hash はデータだけ `sort_swo_oracle.py:679-709`。pointer の意味と allocation は `:1170-1202`。TU hash は worker/broker source 全体を取る `:1621-1670`、contract component に入る `:2546-2580`、receipt は現行値と比較される `s8b_sort_swo_receipt.py:114-137,170-177`。一方、段 2 は順位を固定式として埋め込み `s2-plan.md:126-143`、出力へ hash を載せるだけ `:210-221`。
- version pin の評価:
  - `CORPUS_SHA256`: allocation 順変更を捕捉しない。
  - `TU_TEMPLATE_SHA256`: 現行 oracle の source-byte drift と古い receipt は捕捉する。
  - `CONTRACT_VERSION` / `AXIOM_CHECKER_VERSION`: 単なる固定整数 `sort_swo_oracle.py:47-51` で、自動検出器ではない。
  - `AXIOM_CHECKER_IMPLEMENTATION_SHA256`: 列挙された既存関数だけが対象 `:2486-2545`。新 IR evaluator/pointer rank は追加しなければ閉包外。
  - compiler version: receipt には記録される `:216-248` が、contract component には入らず、portable validator は既知 compiler 値との一致を要求しない。
- 成果物影響: 材料レポートの `tu_template_sha256` は情報欄にしかならず、pointer rule の証明にはならない。後続 receipt は IR schema/parser/renderer/evaluator/pointer mapping、TU hash、compiler policyを一つの contract digest に束縛しない限り certified と呼べない。台帳には「現行 pin が future evaluator を自動保護する」と書いてはいけない。
- scope: driver の false-PASS 防止条件と将来 contract 要件の明記は scope 内。receipt 実装は後続 scope。

**所見 5 — D1355 は技術方向を選んだが、D344 の研究上の実験変更を明示的には裁定していない。**

- 所見: 新しい D1355 は typed IR 方向の生死確認を行う権限としては読める。しかし D344 がユーザー裁定へ返した論点は「技術的に可能か」ではなく、raw C++ 独立合成という D39 の実証点を別実験へ変えてよいかである。D1355 はこの損失に触れていないため、暗黙 supersede と断定できない。
- 根拠 file:line: D344 の却下とユーザー返却は `verbatim-d344.txt:40-44`。D1355 の採用理由は出所保証と最適化圧力であり `verbatim-d1355.txt:3-20`、D39 実験同一性への裁定はない。段 2 自身も衝突残存を認める `s2-plan.md:235-253`。
- 成果物影響: 生死確認が真でも主張できるのは「typed field-comparison IR は技術的に実装可能」ということまで。raw C++ 実験と同値、D39 を保存、D344 を supersede、直ちに certified 選択 interface を置換可能、とは主張できない。台帳は実装 wave 起票と併せて明示裁定待ちを残す必要がある。
- scope: 衝突の明記と結論制限は scope 内。どちらの研究実験を採るかの裁定自体はユーザー scope。

## 親 brief への反証

**(P1a) — 15 件の表現可能性**

- 所見: 「表現できる」は真になる見込みが強いが、生死判定としてはほぼ恒真。
- 恒真方向: grammar と手書き IR 表を `CANDIDATES` の `_single/_two/_NOSORT_IMPL` に合わせて設計しているため、表現性自体は構成から得られる `s6_sort_sweep.py:109-158`。
- 過大方向: byte roundtrip の成功は renderer の 15 literal 一致しか示さず、現行 gate への包含、実型 evaluator、D39 の保存を示さない。
- 過小方向: 15 件だけでは autonomous synthesis の余地を検査しない。stock を含めない点は D1357 上は正しい。
- 成果物影響: `q1=true` は材料レポートの formatter/authority compatibility 値に限定する。単独で台帳を真または実装可にしない。
- scope: 内。

**(P1b) — 関係行列の再現**

- 所見: 「条件つき真」ではなく、現時点では未実測かつ proxy 限定。
- 恒真方向: storage/key は同じ値データと同じ基本比較へ落とすので一致しやすい。Python evaluator が作った期待値同士を比べる構成よりは proxy compile が強い。
- 過大方向: pointer 順位を corpus 由来とする `s1-brief.md:66-70` は誤り。実型/TU/compiler を通さない結果を「現行関係行列」と呼べない。
- 過小方向: 2 corpus は現行 oracle 自身の有限境界なので Q2 の比較範囲としては正しいが、production renderer と実型 conformance が欠ける。
- 成果物影響: 実型一致なしでは `q2=UNAVAILABLE` または別名の `proxy_q2=true/false` とする。
- scope: 判定語彙は内、実型実測は環境依存。

**(P1c) — fail-closed parser**

- 所見: standalone parser の Q3 は定義上ほぼ恒真であり、integration の fail-closed 性を示さない。
- 恒真方向: exact tuple/str と閉じた opcode/domain を実装してから 6 例を投げるため `s2-plan.md:164-185`。
- 過大方向: legacy `implementation: str` 入口が残らないこと、parser より前に render/evaluate する別経路がないこと、保存済み raw artifact を再検証できることは検査していない。
- 過小方向: tuple/field の負例は局所 parser には十分だが、receipt/schema/agent interface の移行条件は範囲外。
- 成果物影響: `q3=true` は「toy admission function の単体性質」。certified 受理経路の fail-closed 証明には使えない。
- scope: 内。

**(P1d) — 15 より広い IR が必要**

- 所見: 15 値だけでは空振りという診断は正しい。しかし 31 値にすれば「合成の余地」が十分になる、または「最小」とする結論は支持されない。
- 恒真方向: 31 は有限直積の機械列挙なので、数え上げと 15 の包含は構成上ほぼ恒真。
- 過大方向: 31 も結局は有限 production からの選択であり、T396 が確認した D344 の実験変更を解消しない。数学的にも「最小」は未証明で、15 に非 authority 1 値を加えただけでも真部分包含になる。
- 過小方向: 同じ合成原理なら lex3、より長い辞書式比較、他の純粋な field 式も自然に導ける。31 は raw C++ 能力に対して大幅に過小。
- 成果物影響: `ir_domain_size=31` は一つの liveness fixture 値に留め、「最小 IR」「D39 を保つ合成空間」と材料レポートや台帳に記載しない。certified `sort_best` へ31値を流用すると逆に D1357 の15組を広げる。
- scope: 内。

## 段 2 プランへの反証

**所見 — PASS の論理式が一意でない。**

- 所見: Q2 は15件で定義され `s2-plan.md:151-158`、31件は別 field `extended_ir_reproducible` `:160` だが、出力 `status` が extended を必須とする式はない `:210-224`。総括だけが31件全一致を生死条件にする `:255-260`。
- 根拠 file:line: 上記。
- 成果物影響: `q1=q2=q3=true, extended_ir_reproducible=false, status=PASS` という誤解可能な成果物が生成できる。`status=PASS iff q1 && q2 && q3 && extended_ir_reproducible && actual_type_conformance` と明文化すべき。actual 実測なしなら `PROVISIONAL` または `UNAVAILABLE`。
- scope: 内。

**所見 — “ground truth” と “typed-field-proxy” が矛盾している。**

- 所見: `s2-plan.md:105` は proxy C++ を ground truth と呼び、`:162` は実 oracle ground truth でないと限定する。前者の語が材料レポートで一般化される危険がある。
- 根拠 file:line: `s2-plan.md:103-105,160-162`。
- 成果物影響: 名称を `proxy_conformance_baseline` に変え、`current_oracle_matrix` と分離する。台帳の真偽は後者で決める。
- scope: 内。

**所見 — hash の記録と束縛が混同されている。**

- 所見: driver は current hash を出すだけで、pointer rank/proxy TU がその hash の意味と一致するか検査しない。
- 根拠 file:line: `s2-plan.md:126-143,208-221`、`sort_swo_oracle.py:1621-1670,2546-2580`。
- 成果物影響: 材料レポートの hash は参照情報に降格する。将来 evaluator contract の必須構成要素一覧を別途残す。
- scope: 内。

## 総括

今のまま dispositive な生死確認として実行してはいけない。proxy driver 自体は予備材料として実行可能だが、PASS を T-2113 の真や実装着手条件へ昇格させないことが条件である。

最低限、実行前に次を変える必要がある。

- proxy Q2 と実型 production conformance を別結果にする。
- PASS の論理式へ31値全件と実型 conformance を明示的に入れる。
- `render(IR)` を介した現行受理集合との包含条件を定義する。
- autonomous IR admission と certified 15組 exact binding の権威を分離する。
- pointer rank、IR grammar/parser/renderer/evaluator、TU、compiler policy を一つの contract へ束縛する要件を残す。
- D1355 が D344/D39 の実験変更まで supersede するかを、実装 wave 前に明示裁定へ返す。

proxy が真だった場合に主張してよいのは、「15 literal を表現でき、現在の proxy 型・compiler 上では31 field-comparison の Python/C++ 行列一致が観測され、toy parser が指定負例を拒否した」までである。「現行 oracle 行列を再現した」「規律2上の真部分集合である」「実型保証を保った」「D39 と同じ実験である」「certified 選択結果を置換できる」とは主張してはいけない。