## 前提の確認

指定された以下の資料をすべて読み取れた。

- `s1-brief.md`
- `verbatim-t2113-ledger.txt`
- `verbatim-d1355.txt`
- `verbatim-d1357.txt`
- `verbatim-d344.txt`
- [sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2113-sort-oracle-ir-liveness/orchestrator/campaign/sort_swo_oracle.py:1)
- [s6_sort_sweep.py の生成器と CANDIDATES](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2113-sort-oracle-ir-liveness/orchestrator/campaign/s6_sort_sweep.py:109)
- [sort_comparator_authority.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2113-sort-oracle-ir-liveness/orchestrator/campaign/sort_comparator_authority.py:25)
- [op_element.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2113-sort-oracle-ir-liveness/external/ccbench/include/op_element.hh:16)
- [silo_op_element.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2113-sort-oracle-ir-liveness/external/ccbench/cc/silo/include/silo_op_element.hh:39)
- [ycsb.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2113-sort-oracle-ir-liveness/external/ccbench/include/ycsb.hh:35)

`orchestrator/tests/test_sort_swo_oracle.py` は変更提案の対象に含めない。書き込み・pytest・compile・driver 実行はいずれも行っていない。

親 brief と現物の相違・注意点は次のとおり。

- brief の exact binding アンカー `sort_comparator_authority.py:58` は空行。関数は `:59`、実際の型・byte exact 検査は `:62-65`。
- brief の割当順 `sort_swo_oracle.py:1183-1184` は一行ずれている。現物は `aliases = new Tuple[4]` が `:1182`、`separate[0..5]` が `:1183`、`:1184` は TupleBody 初期化ループ。
- brief `:97-99` の独立 C++ ground truth は実 `WriteElement<Tuple>` ではなく代理型を使う前提であり、D344 `:6-9,27-30` の「実型 harness」とは同一証拠ではない。型付き IR が型反射等を受理しないため技術的には強い近似になるが、現行 oracle TU そのものとの一致を証明したとは報告できない。
- `rcdptr_` 順位は corpus bytes 単独からは導出できない。`pointer_kind/pointer_slot` は corpus にあるが、その意味づけは TU の `sort_swo_oracle.py:1196-1198`、割当順は `:1181-1183` にある。親 brief の「corpus から導出」は「corpus と現在の TU 記述から導出」の意味に限定すべきである。

## IR 型定義

driver では raw member 名を入力値にせず、次の閉じた tagged tuple とする。組み込みの `tuple` と `str` の exact type を要求し、暗黙変換を認めない。

```text
Field     := "storage" | "key" | "pointer"
Direction := "asc" | "desc"

IR :=
  ("const_false",)
| ("single", Field, Direction)
| ("lex2", Field, Direction, Field, Direction)
    制約: first_field != second_field
```

renderer 内だけに次の固定写像を持つ。

```text
"storage" -> "storage_"
"key"     -> "key_"
"pointer" -> "rcdptr_"
```

15 件の authority IR 値は次のとおり。

| name | IR |
|---|---|
| `s_asc` | `("single","storage","asc")` |
| `s_desc` | `("single","storage","desc")` |
| `k_asc` | `("single","key","asc")` |
| `k_desc` | `("single","key","desc")` |
| `p_asc` | `("single","pointer","asc")` |
| `p_desc` | `("single","pointer","desc")` |
| `sk_aa` | `("lex2","storage","asc","key","asc")` |
| `sk_ad` | `("lex2","storage","asc","key","desc")` |
| `sk_da` | `("lex2","storage","desc","key","asc")` |
| `sk_dd` | `("lex2","storage","desc","key","desc")` |
| `sp_aa` | `("lex2","storage","asc","pointer","asc")` |
| `sp_ad` | `("lex2","storage","asc","pointer","desc")` |
| `sp_da` | `("lex2","storage","desc","pointer","asc")` |
| `sp_dd` | `("lex2","storage","desc","pointer","desc")` |
| `nosort` | `("const_false",)` |

ただし driver の受理範囲はこの15値に閉じず、同じ型の全値を受理する。

- `const_false`: 1
- `single`: `3 fields × 2 directions = 6`
- `lex2`: `3 first × 2 distinct second × 2 × 2 directions = 24`
- 合計31値

これは既存 opcode の制約を一般化するだけで得られる、原則のある最小の真部分包含である。15件はそのうち `1 + 6 + 8` 件となる。

## Q1 の検査手順

権威 source は [s6_sort_sweep.py:143-158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2113-sort-oracle-ir-liveness/orchestrator/campaign/s6_sort_sweep.py:143)。`sort_comparator_authority.py:54-65` もここから index を作るため、別の literal コピーを ground truth にしてはならない。

検査は次の順序に固定する。

1. `CANDIDATES` が15件、name が重複なし、name 集合が上表と exact 一致することを検査する。
2. 各 authority IR を admission validator に通す。
3. admission 済み IR だけを独立 renderer へ渡す。
4. `rendered.encode("utf-8")` と対応する `CANDIDATES` の `implementation.encode("utf-8")` を直接比較する。`.strip()`、改行分割、空白正規化、改行コード変換は一切しない。
5. 全15件が等しいときだけ Q1=true。一件でも name 欠落・余分・重複・byte 不一致なら Q1=false。最初の不一致 byte offset と両方の長さを出力する。

render 規則は `s6_sort_sweep.py:109-137` を独立に再現する。

- 昇順: `a.<member> < b.<member>`
- 降順: `b.<member> < a.<member>`
- 先頭行は2空白から開始。
- lambda 行は7空白から開始。
- body は9空白。
- `lex2` の `:` は `_two` 内の32空白に `_mk` の9空白を足した41空白。
- closing `});` は7空白。
- 行区切りは byte `0x0a` のみ。
- 末尾 newline は付けない。
- `const_false` だけは引数名なしの `_NOSORT_IMPL` とし、通常 renderer の `a, b` lambda を流用しない。

## Q2 の検査手順

ground truth は driver が生成・compile・実行する独立 C++ harness の324 bit 行列とする。Python evaluator 自身が期待行列を生成して、それを ground truth と呼んではならない。

C++ harness は次を満たす。

- `Storage` は `enum class Storage : std::uint32_t`。
- `key_` は `std::string`、入力は octal byte literal と明示長から構築する。
- `rcdptr_` は `Tuple*`。
- proxy `WriteElement<Tuple>` はこの3 field だけを持つ。受理 IR がこの3 field の `<`、`!=` 以外を表現できないため、レイアウトや `sizeof` の違いは観測不能にする。
- `aliases[4]` を先に、`separate[6]` を順番に単調増加 arena 上へ placement construct する。
- 31 IR 全件について、renderer が作った C++ lambda を実際に compile して呼ぶ。C++側でIRを再解釈する別 evaluatorは作らない。
- `sort_swo_oracle.py:961-977`／`:1375-1385` と同じ3 order で要素を配置し、element id による canonical row-major `lhs*18+rhs` に戻す。
- 出力は `(ir_index, corpus_id, order_id, 324文字の0/1)`。欠落・重複・非0/1・長さ不正は Q2 判定ではなく `UNAVAILABLE/protocol-invalid` とする。

Python evaluator は `_CORPUS_TOPOLOGY` `sort_swo_oracle.py:629-648` を入力とし、各 field を次のように比較する。

| field | Python 規則 | C++ と一致する根拠・危険 |
|---|---|---|
| `storage_` | `0 <= value <= 0xffffffff` の Python `int` をそのまま unsigned 順で比較 | 実型は `op_element.hh:19`、underlying type は `ycsb.hh:35`、構築時 cast は `sort_swo_oracle.py:1200`。corpus は `0x80000000`～`0xffffffff` を含む (`:633-637,642-646`)。`int32` 化・符号拡張・`ctypes.c_int32` 化は禁止。 |
| `key_` | Python `bytes` の lexicographic 比較 | 実型は `op_element.hh:20`。`std::string_view(pointer,size)` から構築するため埋込みNULも保持される (`sort_swo_oracle.py:1200-1202`)。corpus は `b"\0"`, `b"a\0"`, `b"\x80"` を含む。PythonでUnicode化、NUL終端化、signed-char 配列化しない。C++ harness は手書き `char < char` ではなく `std::string::operator<` を使う。 |
| `rcdptr_` | 下記 `pointer_rank` の整数比較 | 実型は `op_element.hh:21`。ただし無関係なC++ object pointer間の組込み `<` は移植可能な数値順保証ではない。したがって C++ 実測一致が必須で、Python順位だけから真としない。 |

現在の TU から導かれる順位は次である。

```text
pointer_kind == 0: rank = 0             # nullptr
pointer_kind == 1: rank = 1 + slot      # aliases[0..3] -> 1..4
pointer_kind == 2: rank = 5 + slot      # separate[0..5] -> 5..10
```

根拠は以下。

- corpus は `pointer_kind/pointer_slot` を保持する: `sort_swo_oracle.py:631-647`、canonical label は `:683-686`。
- kind→pointer の意味は `:1196-1198`。
- arena は cursor を alignment まで切り上げ、その後単調に進める: `:817-827`。
- active 時の `new/new[]` は arena へ流れる: `:842-854`。
- mmap 後、arena active にして aliases、separate の順で割り当てる: `:1170-1183`。
- TupleBody 等の追加割当はその後の `:1184-1190` なので、10個の Tuple pointer の相対順位を変えない。

したがって順位は「corpus データ単独」では導出不能だが、「corpus の kind/slot ＋ 現在の TU の意味づけ・記述順」からは導出できる。`CORPUS_SHA256` だけではこの規則を pin できないため、将来の evaluator は少なくとも `TU_TEMPLATE_SHA256` と同時に束縛する必要がある。

Python 行列は、各 corpus・IR について

```text
py[c,ir][lhs*18+rhs] = eval_ir(ir, element[lhs], element[rhs])
```

とする。Q2=true の必要十分条件は、authority 15件すべてについて次が成立すること。

```text
cpp[c,ir,order0] == cpp[c,ir,order1] == cpp[c,ir,order2]
                 == py[c,ir]
```

比較対象は `2 corpora × 15 IR × 3 orders × 324 cells`。一セルでも不一致なら Q2=false とし、`ir/name, corpus, order, lhs, rhs, cpp, python` を出す。

P1d 用の生死判定は同じ条件を31 IR 全件へ広げる。`2 × 31 × 3 × 324` が全一致した場合だけ `extended_ir_reproducible=true` とする。

proxy C++ は技術的 liveness ground truth であって、実 oracle TU の直接実測ではない。実型 oracle との end-to-end 比較ができなければ、出力に `ground_truth_scope="typed-field-proxy"` を固定し、「現行 oracle matrix を実測済み」とは書かない。

## Q3 の検査手順

inspection point は renderer、Python evaluator、C++ source 生成より前の `admit(raw)` 一箇所とする。

検査順は以下に固定する。

1. `type(raw) is str` なら `raw-cpp` として拒否。
2. `type(raw) is not tuple` なら型不一致。
3. opcode が exact `str` でない、arity 不一致、field/direction が exact `str` でない場合は型不一致。
4. opcode が `const_false/single/lex2` 集合外なら未知 opcode。
5. field/direction が閉じた domain 外、または `lex2` の field 重複なら拒否。
6. 通過した canonical IR だけを render/evaluate リストへ追加する。

具体的 probe は次の6件。

| 種類 | 通る正例 | 落ちる負例 |
|---|---|---|
| 未知 opcode | `("single","key","asc")` | `("call","key","asc")` |
| 型不一致 | `("lex2","storage","asc","pointer","desc")` | `("single","key",True)` |
| 任意 C++ 文字列 | `("const_false",)` | `"return a.key_ < b.key_;"` |

Q3=true は「正例3件が admission を通り、負例3件が期待分類で拒否され、負例について render/evaluator/C++ source append の各 counter が増えない」場合だけとする。単に例外が出たことだけでなく、評価前拒否を counter で確認する。

## driver の構造

repo 外 driver の物理行を次の100行に割り当てる。

```text
01-05  imports、repo root/CXX 引数、s6_sort_sweep と sort_swo_oracle の読込
06-09  Field/Direction/opcode/member-map、N=18 の確認
10-26  authority 15件の (name, IR) 列挙
27-37  admit(raw): raw C++、container、opcode、arity、exact type、domain 検査
38-49  cmp_expr()/render(): const_false/single/lex2 と exact whitespace
50-54  CANDIDATES 重複・name集合・UTF-8 byte比較、Q1 mismatch 作成
55-60  全31 IR の機械列挙、Q3 の正負6 probe と評価前 counter
61-69  pointer_rank、field_value、eval_ir、Python 18x18 matrix
70-83  C++ source生成:
       exact3 field型、単調arena、2 corpus、3 order、sort interceptor、
       31個のrender済みlambda呼出し、canonical bit出力
84-89  一時dirへ source、CXX compile/run、終了値・record shape検査
90-94  order間一致、C++対Python一致、current15/extended31 の最初の差分
95-100 canonical JSON(sort_keys=True) 出力、semantic false/UNAVAILABLE のexit分離
```

入力は `repo_root` と `CXX` のみ。corpus・候補 literal・hash は repo 現物から読む。任意 IR や C++ を CLI から受け取らない。

出力は最低限次を含む canonical JSON とする。

```text
q1, q2, q3
extended_ir_reproducible
authority_count, ir_domain_size
corpus_sha256, tu_template_sha256
ground_truth_scope
first_q1_mismatch
first_q2_mismatch
q3_cases
status = PASS | FAIL | UNAVAILABLE
```

compile 不可・process 異常・出力 protocol 異常は Q2=false に混ぜず `UNAVAILABLE`。semantic mismatch だけを false とする。

100行を超えそうな場合の削減優先順位は次のとおり。

1. success ごとの個別 matrix hash・pretty print・説明文を削る。
2. 全 mismatch 列挙を最初の一件だけにする。
3. argparse、色付き出力、独自例外 class を削り、固定 positional 引数にする。
4. C++ source の定型部を一行一要素の文字列配列へ圧縮する。

15件列挙、31件の拡張範囲、2 corpus、3 order、18x18 全セル、Q3 の6 probe は削ってはならない。それでも100行に入らなければ、検査範囲を黙って減らさず `DW-G01 line budget infeasible` と報告する。

## 親 brief への反証

(P1d) は正しい。

15件だけを受理する型を作ると、その値域の濃度は `CANDIDATES` と同じ15であり、name を IR tuple に置き換えただけである。これは D344 `:41-44` が却下した「合成が事前 allowlist からの選択に化ける」構成そのものになる。Q1 と Q3 は型定義からほぼ恒真になり、生死確認として空振りする。

測るべき最小の原則的範囲は、上記の全31値である。

```text
const_false
+ 全 field の単一比較
+ 相異なる任意2 field の辞書式比較
```

これは既存15件を真部分集合として含み、第一 field・第二 field・方向を合成側が独立に選べる。31件すべてを同じ C++ 対 Python の18x18基準で評価できる。

ただし31値に広げても、D344 の実験同一性問題は消えない。raw C++ 合成を typed field-comparison synthesis に変更する事実は残る。従って技術的 liveness が真でも、「D1355 が D344 のこの部分を supersede する」という明示裁定なしに、raw C++ 独立合成と同じ実験だとは扱えない。

また pointer 比較6件は重大な条件付きである。現在の割当順位は復元できるが、無関係 object pointer の組込み `<` を portable semantics として trusted evaluator に移植することはできない。C++ ground truth との実測一致、TU hash への束縛、または将来 IR で pointer の意味を明示的 rank として再定義する必要がある。後者は現行 C++ comparator の意味を変更するため、別の裁定を要する。

## 総括

- Q1 は真になる見通しが強い。15 literal は `_single/_two/_NOSORT_IMPL` から決定的に生成されるが、未実測。
- Q2 は条件付き。storage と key は型対応を明確にできる。pointer rank は現在の TU から復元できるが corpus 単独ではなく、C++ pointer `<` の移植性もない。C++対Python全セル一致を実測するまで真ではない。
- Q3 は validator の構造上は真になる見通しが強いが、評価前 counter を含む6 probe は未実行。
- wave の有効な生死条件は、authority 15件だけでなく31 IR 全件について Q2 が成立し、pointer 条件と D344/D1355 の裁定衝突を明示すること。

15件だけを測る、proxy harness を実 oracle 実測と呼ぶ、pointer rank を corpus hash だけに帰属させる、または未実行検査を真と記録する場合、この生死確認は空振りになる。