## 1. 現行受理集合の実測

結論から言うと、親 brief の「関所は LLM auditor だけ」は現行 HEAD では反証される。特に指定攻撃 `pro_set_.pop_back();` + 正当な `sort(...)` は、autonomous sort 経路では既存 SWO oracle の単一文検査で機械拒否される。本回答は静的読解であり、pytest／実行テストは行っていない。

### autonomous sort の呼び出し順

1. 提案 JSON の入口

   - `orchestrator/campaign/p3_s4_loop_sort.py:359-360` — JSON として不正なら拒否するが、C++ 内容は見ない。
   - `p3_s4_loop_sort.py:361-363` → `projection_guard.py:283-341` — top/planner/coder/auditor の key 集合を閉じる。`implementation` の存在は要求するが、sort 文法や副作用は見ない。
   - `p3_s4_loop_sort.py:368-370` — `implementation` をそのまま dataclass へ格納する。型注釈だけで実行時検査はない。
   - `p3_s4_loop_sort.py:371` → `auditor_gate.py:132-168` — auditor verdict の schema を検査する。candidate の意味は見ない。
   - `p3_s4_loop_sort.py:376` → `projection_guard.py:365-390` — ledger の excluded token/path を全 nested string から拒否する。一般 C++ 識別子検査ではない。

2. auditor 用 preview。`p3_s4_loop_sort.py:438-453` が `L.quarantine(..., write=False)` を呼び、次の検査を実行する。実 iteration でも `p3_s4_loop_sort.py:152-160` から同じ検査を再実行する。

   `DiffQuarantine.validate()` の固定順は次のとおり。

   - `diff_quarantine.py:422-428` — malformed diff を拒否。
   - `diff_quarantine.py:430-437` — trusted template hole の comment delimiter／行末 backslash 汚染を拒否。
   - `diff_quarantine.py:439-441` —空 diff は通す。
   - `diff_quarantine.py:443-452` —対象外ファイルを拒否。
   - `diff_quarantine.py:454-461` — hunk の HEAD anchor 不一致を拒否。
   - `diff_quarantine.py:463-475` — hole 外の削除を拒否。
   - `diff_quarantine.py:476-488` — hole 外の挿入を拒否。
   - `diff_quarantine.py:489-496` — hole 内の生前処理指令を拒否。
   - `diff_quarantine.py:497-502` —偽 BEGIN/END marker を拒否。
   - `diff_quarantine.py:503-509` — `//` を byte 一致で拒否。
   - `diff_quarantine.py:510-516` — `/*` を byte 一致で拒否。
   - `diff_quarantine.py:517-522` —物理行末 backslash を拒否。
   - `diff_quarantine.py:524-525` —以上がなければ通す。文数、行数、C++ 構造は見ない。

3. generic host-effect scanner

   - `p3_s4_loop.py:242-271` → `coder_effect_gate.py:576-614`。
   - `coder_effect_gate.py:58-105` の process/file/network/thread/escape-hatch 識別子、明示的な無条件 loop、malformed token、256 KiB／4096 token 超過を拒否する。
   - 最長一致 punctuator は `coder_effect_gate.py:177-183`。
   - `pro_set_` と `pop_back` は deny table にないため、指定攻撃はここを通る。
   - したがって brief の「sort 軸には識別子 blacklist が一切かかっていない」も現行 HEAD では誤りである。正しくは「generic blacklist はかかるが、指定識別子を収載していない」。

4. auditor deny-only veto

   - `p3_s4_loop_sort.py:154-160` → `auditor_gate.py:190-231`。
   - machine reject はそのまま維持し、machine pass のときだけ verdict schema と実 diff digest を照合する。
   - `verdict="pass"` は元の machine-pass object を返すだけで、安全性の肯定証明ではない。
   - 指定攻撃に auditor が pass を返すこと自体は可能。

5. SWO oracle

   - `p3_s4_loop_sort.py:162-220` → `sort_swo_oracle.py:1419-1654`。
   - `sort_swo_oracle.py:446-463` — marker、`#if/#else/#endif` の一意性と順序を検査。
   - `sort_swo_oracle.py:486-548` —先頭が非修飾 `sort`、外側括弧が対応し、閉じ括弧以後が `;` だけである単一文を要求。
   - 構造通過後は `sort_swo_oracle.py:1497-1527` の trusted control、`:1529-1540` の実型 candidate compile、`:1624-1654` の有限 corpus 実行へ進む。
   - oracle 側 `sort` は comparator 呼び出しごとに例外、corpus mutation、反復不一致を検査する (`sort_swo_oracle.py:766-803`)。
   - 既存境界テストも `sort(...); other();` を `not-a-single-sort-statement` で拒否している (`test_sort_swo_oracle.py:297-312`)。

したがって指定攻撃を先頭へ置いた

```cpp
pro_set_.pop_back();
sort(write_set_.begin(), write_set_.end(),
     [](const WriteElement<Tuple>& a, const WriteElement<Tuple>& b) -> bool {
       return a.key_ < b.key_;
     });
```

は `qualified-or-non-sort-callee`、末尾へ置いた形は `not-a-single-sort-statement` で、auditor pass 後に機械拒否される。

6. oracle 通過後

   - `loop.py:195-198` と `pipeline.py:743-758` が `source_digest.resolve_evidence()` を再実行する。
   - `source_digest.py:560-654,669-708,839-892` は条件 macro、include、tracked path、source identity を検査するが、sort の純粋性文法は持たない。
   - `build_admission.py:615-675,743-764` は materialized trigger predicate だけを検査する (`:627`, `:754`)。sort の検査はない。
   - `buildcache.py:1323-1326,1547-1554` は evidence、commit、allowlist、cache identity を再検査して compiler へ進めるが、sort hole の能力制約はない。

よって最終裁定は次のとおり。

- autonomous `CoderProposalSort` 経路について、指定した二文攻撃が auditor だけを関所として build へ進む、という主張は反証される。
- 一方、既に materialize された source を `pipeline.evaluate()` や `buildcache.build()` へ直接渡す経路は quarantine／auditor／SWO oracle を通らない。この経路では parent が指摘した residual attack が残る。
- `write_set_` permutation 計装は `transaction.cc:395-418` にあるが、`pro_set_` の縮小は検出しない。この部分の親 brief の観測は有効である。

## 2. 判定器の文法

### producer 契約の逐語引用

`.claude/agents/coder-v4-autonomous-sort.md:84-89` は次のとおり。

> **Closed-region 制約 (D23 道Y、hook が機械執行する部分と auditor が目視する部分の併用):**
> - 新しいヘッダ取り込み・型/関数/マクロ/グローバル変数の追加は禁止
> - 生の前処理指令 (`#if`/`#ifdef`/`#define`/`#include` 等) は禁止
> - `implementation` 内では `//`・`/*`・行末 backslash `\` を禁止する (文字列リテラル・raw string 内も禁止)。説明文はコード内に埋めず `justification` フィールドへ書く
> - 非決定ビルトイン (現在時刻・乱数等) は禁止
> - 既存 silo API を呼ぶ straight-line code のみ (副作用のある呼び出し・ループ・例外送出は不可)

併せて `coder-v4-autonomous-sort.md:78-82` は、利用可能な値を `storage_`、`key_`、`rcdptr_` に閉じ、lambda signature を変更不可としている。

| 契約項目 | 機械検査可能性 |
|---|---|
| header/type/function/macro/global の追加禁止 | hole 全体を固定 `sort` envelope と単一 return-expression に閉じれば検査可能。任意 C++ を許したままでは不可能。 |
| 生前処理指令禁止 | 現行 byte gate と新 lexer の双方で可能。 |
| comment/backslash 禁止 | 現行 byte gateに加え、直接 build 経路用 materialized-source 検査でも可能。 |
| 非決定 builtin 禁止 | open-world C++ identifier のままでは完全検査不能。識別子を parameter と三 field に閉じ、callee production を持たせない場合のみ機械保証できる。 |
| straight-line／副作用／loop／throw 禁止 | loop、throw、複数 statement、assignment、capture、call、dereference は構文で落とせる。任意の「既存 API call」が副作用なしであることは C++ 意味解析なしには判定不能。 |

したがって P2 は無条件には成立しない。提案文法は `:78-82` の「利用可能 API は三 field だけ」を閉じた契約として採用する場合に限り、「producer の意味契約を機械化する」と説明できる。

また D344 は、C++ 文法を compiler に委ね、構造検査を単一 `sort(...)` 文までに留めると決定している (`docs/decisions.md:15215-15218`)。pure-field AST 案も既裁定の非対称構成と衝突するとして退けている (`:15245-15249`)。今回の grammar gate はこの部分を明示的に supersede する新 D が必要で、「既存判断を変えない単なる実装」とは記録できない。

### 推薦する compositional grammar v1

新規 `orchestrator/campaign/sort_hole_language.py` に、外部依存なしの lexer＋recursive-descent parser を置く。

```bnf
<implementation> ::= sort ( <begin> , <end> , <lambda> ) ;

<begin>          ::= write_set_ . begin ( )
<end>            ::= write_set_ . end ( )

<lambda>         ::= [ ] ( <param-a> , <param-b> ) -> bool <body>
<param-a>        ::= const WriteElement < Tuple > & <optional-a>
<param-b>        ::= const WriteElement < Tuple > & <optional-b>
<optional-a>     ::= a | ε
<optional-b>     ::= b | ε

<body>           ::= { return <expression> ; }

<expression>     ::= <conditional>
<conditional>    ::= <logical-or>
                   | <logical-or> ? <expression> : <conditional>
<logical-or>     ::= <logical-and> ( || <logical-and> )*
<logical-and>    ::= <bit-or> ( && <bit-or> )*
<bit-or>         ::= <bit-xor> ( | <bit-xor> )*
<bit-xor>        ::= <bit-and> ( ^ <bit-and> )*
<bit-and>        ::= <equality> ( & <equality> )*
<equality>       ::= <relational> ( ( == | != ) <relational> )*
<relational>     ::= <shift> ( ( < | <= | > | >= ) <shift> )*
<shift>          ::= <additive> ( ( << | >> ) <additive> )*
<additive>       ::= <multiplicative> ( ( + | - ) <multiplicative> )*
<multiplicative> ::= <unary> ( ( * | / | % ) <unary> )*
<unary>          ::= ( ! | ~ | + | - ) <unary> | <primary>
<primary>        ::= true | false | nullptr | <number>
                   | <field-ref> | ( <expression> )

<field-ref>      ::= a . <field> | b . <field>
<field>          ::= storage_ | key_ | rcdptr_
```

字句・意味規則は BNF と同じ契約 ID に含める。

- whitespace は ASCII の space、tab、LF、CR、form-feed、vertical-tab。token 間だけで無視する。
- identifier、number、multi-character punctuator は最長一致。`!=` は `!` より先、`&&` は `&` より先、`->` は `-` と `>` より先に token 化する。
- `<number>` は標準組込み integer／floating literal と標準 suffix のみ。user-defined suffix、string、character、raw string は拒否する。
- field 型を `storage=Storage`、`key=std::string`、`record=Tuple*` として推論する。field を含む算術・bitwise は、現在の型で候補側 operator call／mutation 能力を生じない組み合わせだけを許す。string の `+`、pointer arithmetic、dereference、address-of は拒否する。
- call、subscript、member chaining、cast、assignment、increment/decrement、comma、nested lambda、capture、declaration、`new/delete/throw` の production は持たない。
- unnamed parameter は参照不可。これにより `return false;` の正例は通る。
- SWO はこの文法の保証に含めない。既存 oracle が有限反例検出器として後段に残る。

これは comparator の完成形を列挙する allowlist ではない。recursive expression、任意 nesting、条件演算、任意 literal により受理集合は非有限で、composer は新しい式を合成できる。一方、能力 atom は三 field の値読取りと純粋 operator に閉じる。

### 判定順と上限

先行 wave の規律をそのまま継承する。

1. exact `str` 型
2. 正規化前 UTF-8 raw size、最大 4096 byte
3. ASCII／許可文字
4. 最長一致 token 化、whitespace と EOF を除き最大 512 token
5. parse、同時 open parenthesis 最大深度 64
6. parameter binding／型・operator 能力検査

`!` は削除せず、C++ と同じ unary precedence で解析する。したがって `!a.storage_ != b.storage_` は `(!a.storage_) != ...` と読み、型段で拒否する。`!(a.storage_ != b.storage_)` は通る。`! =` は二 token になり文法拒否する。

公開 API は次の形にする。

```python
SORT_HOLE_GRAMMAR_ID: str
check_sort_hole_implementation(value: object) -> SortHoleLanguageResult
check_materialized_sort_hole(genome: Genome, evidence: SourceEvidence) -> SortHoleLanguageResult
require_materialized_sort_hole(genome: Genome, evidence: SourceEvidence) -> None
```

`SortHoleLanguageResult` は `passed`、閉じた `reason_code`、`grammar_id` だけを持ち、候補本文、未知 token、文字位置、例外本文を返さない。

## 3. 配線先

### 現在の materialization 経路

| 経路 | 現在の file:line |
|---|---|
| autonomous preview | `p3_s4_loop_sort.py:438-453` → `p3_s4_loop.quarantine()` |
| autonomous iteration | `p3_s4_loop_sort.py:142-153,318-329` → quarantine → auditor → oracle → `run_campaign()` |
| autonomous fixture CLI | `p3_s4_loop_sort.py:538-563` |
| S6 candidate identity materialization | `s6_sort_sweep.py:318-333` |
| S6 normal evaluation | `s6_sort_sweep.py:336-366` → `run_campaign()` |
| S6 screening | `s6_sort_sweep.py:369-375` → `screening_driver.py:144-197` → `pipeline.evaluate()` |
| S1 `sort_best` | `s1_direct_comparison.py:643-709` が comparator を quarantine＋SWO oracle へ通し、`:925-974` が `pipeline.evaluate()` へ渡す |
| S8B binding | `s8b_materialization.py:125-146` が `prepare_cell()` へ委譲 |
| S8B oracle | `s8b_oracle_driver.py:1462-1527` → shared binding → `pipeline.evaluate()` |
| S8B floor | `s8b_floor_campaign.py:2070-2124` → shared binding → `buildcache.build_v2()` |
| campaign wrapper | `loop.py:92-102,195-260` → `pipeline.evaluate()` |
| direct evaluator | `pipeline.py:572-634,740-778` → legacy/v2 build (`:851-897`) |
| direct builders | `buildcache.py:1230-1326` と `:1514-1554` |

### 実装する配線

1. `p3_s4_loop.py:242-275`

   generic host-effect scannerの後、source write の前に、marker が `silo-writeset-sort` の場合だけ `check_sort_hole_implementation()` を呼ぶ。

   既存の `std::system`／loop 系テストを引き続き `HOST_EFFECT` として分類するため、順序は必ず

   `DiffQuarantine → HOST_EFFECT → SORT_HOLE_LANGUAGE → write`

   とする。

2. `diff_quarantine.py:41-48`

   `DiffRejectSubtype.SORT_HOLE_LANGUAGE = "sort-hole-language"` を追加し、固定 reason code と grammar ID を rejection digest へ載せる。

3. `loop.py:195-237`

   `resolve_evidence()` の直後、`variant_id` と terminal WAL skip の前に materialized source を再検査する。これにより invalid source を「既評価」として黙って skip しない。拒否時は固定 `reason="sort-hole-language-reject"` の abort とし、candidate text は WAL に載せない。

4. `pipeline.py:743-782`

   current `SourceEvidence` の一致確認後、capability／admission 導出前に再検査する。失敗は pre-build `admission-error` として `build_start`／compiler へ到達させない。

5. `buildcache.py:1323-1326` と `:1547-1554`

   `_validate_request_evidence()` の直後、commit検査、cache lookup、configure より前に再検査する。legacy `build()` と `build_v2()` の両方が必須で、片方だけでは S8B floor または通常 campaign が漏れる。

6. materialized frame 検査

   `SORT_VARIANT != 0` の silo genome では、`transaction.cc` に一意な sort marker、固定 `#if SORT_VARIANT/#else/#endif`、固定 stock branch があることを要求し、その active hole を抽出して同じ grammar へ渡す。marker 欠落、重複、frame 変更は拒否する。

   `SORT_VARIANT == 0` は active implementation を持たない stock control として通す。inactive branch 内の説明 comment を implementation として解析しない。

7. policy／cache／WAL binding

   `build_admission.py:458-466` の policy preimage に

   ```python
   "sort_hole_grammar": SORT_HOLE_GRAMMAR_ID
   ```

   を追加する。`ident.py:39-52` が policy preimage を campaign identity に入れ、`buildcache.py:600-601` が admission receipt SHA を cache key に入れるため、旧 WAL、旧 cache、旧 portable admission receipt は新 gate 合格扱いにならない。

   これは全 admission-aware campaign の policy hash を回転させる。trigger の受理集合は変えないが、identity／cache は全体で cold invalidate される点を新 D に明記する。

`p3_s4_loop_sort.py`、`s6_sort_sweep.py`、`s1_direct_comparison.py`、S8B wrapper 自体は編集しない。共有 seam と下流再検査で全経路を覆う。

## 4. pin 閉包

| 編集面 | pin／trust root と必要更新 |
|---|---|
| 新規 `sort_hole_language.py` | 新規なので既存 SHA pin はない。load-bearing source として `campaign_lock.py:29-38` の `CONTRACT_LOADER_RELATIVE_PATHS`、`qualification/contract.py:38-76` の `REQUIRED_CODE_IDENTITY_PATHS` へ追加する。 |
| `p3_s4_loop.py`／`diff_quarantine.py` | `known_axes_freeze` 内の path SHA pin は検索範囲内にない。挙動は `test_p3_s4_loop.py:148-215,846-903`、`test_p3_s4_loop_sort.py:381-429`、`test_diff_quarantine.py` が固定する。 |
| `loop.py`／`pipeline.py` | `campaign_lock.py:29-38` の enforcement source closure に既収載。exact closure test は `test_t671_source_binding.py:22-31,119-143`。`pipeline.py` はさらに `qualification/contract.py:59` の T126 code identity 対象。 |
| `buildcache.py`／`build_admission.py` | `qualification/contract.py:60-61` の T126 code identity 対象。`test_t126_pegasus_tools.py:1441-1489` が exact set と tracked blob を検査する。policy／receipt 境界は `test_build_admission.py:233-299,576-671`。 |
| `campaign_lock.py`／`contract_loader_binding.py` | closure を 8 path から 9 path にするため `campaign_lock.py:27-38`、`contract_loader_binding.py:49-52`、`test_t671_source_binding.py:22-31,119-143` を同時更新する。 |
| grammar ID | canonical grammar preimage から SHA-256 を導き、テスト側に期待 ID を literal pin する。受理集合変更時は version、期待 ID、新 D、境界テストを同時更新する。 |
| C++ 型の意味 | `external/ccbench/include/op_element.hh:16-22` の `Storage/std::string/Tuple*` と `cc/silo/include/silo_op_element.hh:39-71` に依存する。`CURRENT_PIN` は admission policy に既に含まれる (`build_admission.py:461`)。pin 前進時は operator 能力表を再監査する。 |
| role 契約 | `.codex/role-adapters/coder-v4-autonomous-sort.json:163-185` が role source SHA を pin する。role は編集しない。編集が必要になれば明示承認、adapter／manifest 再生成が別途必要。 |

### 凍結検証を落とすファイル

次の production files は編集禁止とする。

- `orchestrator/campaign/s6_sort_sweep.py` は `known_axes_freeze.json:200-202,426-428,633-635` に、key `_genome(1) and candidate space` と SHA-256 が記録されている。
- `orchestrator/campaign/p3_s4_loop_sort.py` は同 `:205-207,431-433,638-640` に、key `_BASE used by _genome(1)` と SHA-256 が記録されている。
- 同じ二ファイルは `measurement_freeze.json:227-234` と `t080_freeze_migration.py:92-101` にも pin される。
- `s1_known_axes_freeze.verify_document()` は live bytes を再計算して不一致を拒否する (`s1_known_axes_freeze.py:832-857`)。したがって上記二ファイルを編集すると凍結検証は実際に落ちる。
- trigger 側 `s8a_trigger_sweep.py` も known/measurement freeze と `t080_freeze_migration.py:91-102` に pin されるため触らない。
- `sort_swo_oracle.py` は D344 の独立契約と receipt/hash テストを持つため変更しない。

既存 T126 artifact、campaign lock、WAL、cache、S8B portable receipt は新 policy hash と一致しなくなる。これは accidental drift ではなく D345 に従う意図的な世代分離として記録する必要がある。

## 5. 境界テスト

### positive controls の静的確認

`positive-controls.txt` の sort 部分を読むと、実体は次の 16 control である。

- `positive-controls.txt:11-21` —一 field 昇降順 6 件。
- `:23-37` —二 field ternary 辞書式 8 件。
- `:39` — unnamed parameter＋`return false;` 1 件。
- `:9` — `STOCK_IMPL_NOTE` という説明文字列 1 件。

前者15件はすべて提案文法で受理できる。使用 token は固定 envelope、三 field、`<`、`!=`、`?:`、`false` だけである。

一方、次の1件は文法で受理できない。

> `SORT_VARIANT=0 の #else 枝 (テンプレ骨格そのまま) = sort(write_set_.begin(), write_set_.end()) — WriteElement::operator< による (storage_, key_) 昇順 2 段辞書式 (silo_op_element.hh)`

これは `s6_sort_sweep.py:154-160` の provenance 用 `STOCK_IMPL_NOTE` であって、hole へ materialize される C++ implementation ではない。実装文字列は15件しかなく、D298 も「`s6_sort_sweep` の15件」と記録している (`docs/decisions.md:13840-13842`)。

したがって「grammar が sort 16文字列を全受理」は満たせない。散文を特例受理すると非 C++ を gate-pass にする。境界テストは次の二層へ訂正するのが妥当である。

- implementation grammar positive: 実コード15件を全受理。
- system positive: `SORT_VARIANT=0` の stock materializationを受理し、説明文字列自体は parser に渡さない。

### 具体的な正例

```cpp
sort(write_set_.begin(), write_set_.end(),
     [](const WriteElement<Tuple>& a, const WriteElement<Tuple>& b) -> bool {
       return a.storage_ != b.storage_
           ? a.storage_ < b.storage_
           : a.key_ < b.key_;
     });
```

```cpp
sort(write_set_.begin(), write_set_.end(),
     [](const WriteElement<Tuple>& a, const WriteElement<Tuple>& b) -> bool {
       return a.storage_ < b.storage_
           || (a.storage_ == b.storage_ && a.key_ < b.key_);
     });
```

```cpp
sort(write_set_.begin(), write_set_.end(),
     [](const WriteElement<Tuple>&, const WriteElement<Tuple>&) -> bool {
       return false;
     });
```

### 拒否ベクタ

- 指定攻撃の前置／後置二文。
- lambda 内の状態変更:

```cpp
sort(write_set_.begin(), write_set_.end(),
     [&](const WriteElement<Tuple>& a, const WriteElement<Tuple>& b) -> bool {
       pro_set_.pop_back();
       return a.key_ < b.key_;
     });
```

- `[this]`、`[&]`、`[=]` capture。
- `write_set_.clear()`、`pro_set_.size()`、`std::rand()`、`clock()`。
- `a.rcdptr_->field`、`*a.rcdptr_`、`a.key_[0]`。
- `a.storage_ = b.storage_`、`++a.storage_`、comma expression。
- `throw 1;`、`while (...)`、`for (...)`、`try/catch`、二つ目の `return`。
- `std::sort(...)`、二引数 `sort(...)`、変更された begin/end、二つ目の `sort`。
- `const auto&` generic lambda。role の固定 signature 外として拒否する。
- `#include`、`#define`、`//`、`/*`、行末 backslash、string/raw string。
- marker 欠落／重複、`#if SORT_VARIANT` 改変、stock branch 改変。

### token・資源境界

- `: :`、`= =`、`! =`、`& &`、`&&&`、`===`、`- >` は拒否。
- `!=`、`&&`、`->` は単一 token として受理。
- `!(a.storage_ != b.storage_)` は受理し、`!a.storage_ != b.storage_` は型段で拒否。
- 4096／4097 byte、512／513 token、深度64／65を対にする。
- 複数違反入力で `type → raw size → character → token count → parse/depth → semantic` の reason 優先順位を固定する。

### 配線・mutation test

- 新規 `test_sort_hole_language.py` — grammar、15 control、stock metadata 分離、全拒否境界。
- `test_p3_s4_loop_sort.py:97-100` — `_CLEAN_IMPL` を固定 signature に直す。`_NON_SWO_IMPL` は grammar を通る `return a.key_ != b.key_;` に替え、oracle reject の期待値は維持する。
- `test_p3_s4_loop_sort.py:381-429` —既存 host-effect subtype を維持し、指定攻撃が `SORT_HOLE_LANGUAGE` で source write 前に落ちることを追加。
- `test_s6_sort_sweep.py:211-216` —15 candidate の shared quarantine pass を維持。
- `test_campaign.py` — `run_campaign` の terminal skip 前、`pipeline.evaluate` の build_start 前、legacy build の cache hit 前で拒否することを個別 spy で固定。
- `test_buildcache_v2.py` — `build_v2` が cache claim／toolchain configure 前に拒否することを固定。
- `test_build_admission.py` — policy preimage と grammar ID、旧 policy receipt 拒否、cache key 世代差を固定。
- `test_t671_source_binding.py`／`test_t126_pegasus_tools.py` —新 module の trust closure 収載を固定。
- mutation 事前登録では、各配線 call の削除、`passed` 条件の反転、policy key の削除、最長一致順序の逆転、上限比較の off-by-one を独立 mutant とし、それぞれ一つ以上の境界テストで殺す。

テストは未実行であり、緑とは報告しない。

## 6. D96 手続

`docs/spool/decisions/2026-08-15-dev-wave-t396-hole-allowlist-1.md` に `{{D:sort-hole-language}}` の新 D を置き、実装・境界テストと同じ commit に含める。

新 D の骨子は次のとおり。

**決定**

- sort hole に compositional pure-expression grammar v1 を導入する。
- comparator 完成形の有限列挙ではなく、三 field 上の再帰的 expression を許す。
- shared quarantine、`run_campaign`、`pipeline.evaluate`、legacy/v2 build で同一判定器を再実行する。
- grammar ID を build admission policy、campaign identity、cache identity、portable receipt 世代へ束縛する。
- generic host-effect gate、auditor deny-only veto、SWO finite oracle は別責務として残す。
- D344 の「構造は単一 sort 文まで」と typed grammar 却下部分を、本件の明示裁定範囲で supersede する。
- positive corpus は「15 implementation＋1 stock metadata」に訂正し、散文を C++ として受理しない。

**射程**

- `silo-writeset-sort`、silo protocol、`SORT_VARIANT != 0` に限定。
- trigger、backoff、他 marker の受理集合は変更しない。
- libclang 等の外部 parser、sandbox、全 C++ 意味証明、SWO 全入力証明は導入しない。
- marker 外の手動 transaction.cc 改変、shell／直接 CMake materializer、arbitrary binary path、evidence取得後の ABA は残余として明記する。
- 指定二文攻撃は autonomous 経路では既に SWO structure gate が拒否していた事実を記録し、新 gate の効果を「最初の防壁」と誇張しない。
- global admission policy hash の回転により、sort を使わない既存 campaign も identity/cache 世代が変わることを明記する。

**却下案**

- `pro_set_`／`pop_back` 等の blacklist 追加だけ — alias、別 member、間接呼出しを閉じない。
- comparator 完成形15件の有限 allowlist —合成を選択へ変える。
- auditor だけ — digest は帰属確認で、安全性の肯定証明ではない。
- autonomous driver だけ — sweep、direct comparison、pipeline、buildcache を漏らす。
- quarantine だけ —手動 materialization、cache、replay を漏らす。
- compiler／SWO oracle だけ —単一文構造は守れても、member-scope の状態到達を一般には閉じない。
- libclang／外部 C++ parser — gate 実行環境へ新しい外部依存を持ち込む。
- stock の説明文を grammar 特例にする —非 C++ を受理する。
- role を先に狭める —明示承認と adapter repin が必要で、本計画の P2 前提を外れる。

## 総括

- 指定二文攻撃は autonomous 経路では既存 SWO oracle が既に拒否しており、親 brief の auditor-only 前提は反証される。
- 新 gate の実効的価値は、契約の早期機械執行と、直接 `pipeline`／`buildcache` 経路の閉鎖にある。
- 実装は15件の実 C++ positiveを保ち、stock の散文1件は別 interface の control として扱う。
- 最大の未確定点は、D344 の compiler-authoritative 判断を supersede する裁定と、global policy hash 回転の影響を許容するかである。