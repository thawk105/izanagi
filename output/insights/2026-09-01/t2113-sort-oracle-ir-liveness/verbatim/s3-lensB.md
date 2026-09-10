## 前提の確認

指定された 5 文書と、検査に必要な repo 内アンカーをすべて読めた。read-only の静的検査のみで、pytest・compile・driver 実行・書き込みは行っていない。

結論を先に述べる。段 2 driver は完全に無測定ではなく、render 済み lambda を proxy C++ で実行し、Python evaluator との有限 corpus 一致を測る。しかし、現行実型 oracle の再現性ではなく、driver 内で共通設計された renderer・corpus 解釈・allocator・validator の自己整合を主に測る。現状のまま `PASS` を生死確認の「真」に使うことはできない。

## 所見

1. **Q2 の ground truth は proxy であり、対象の現行 oracle ではない。**

   - 所見: プラン自身が `ground_truth_scope="typed-field-proxy"` と認めている一方、親 brief は実 oracle が masstree 未設定で実行不能と明記する。これは「現行 2 corpus の関係行列を再現した」という Q2 ではなく、代理型で同様の行列を作れたという別の測定である。
   - 根拠 file:line: `s2-plan.md:103-116,160-162`、`s1-brief.md:93-99`、`verbatim-d344.txt:6-9,27-30`。現物 TU は `sort_swo_oracle.py:789-793,1182-1206` で実型を使う。
   - これが真なら生死確認の結論がどう変わるか: proxy が一致しても `q2_proxy=true` にしかできない。`q2_actual` は `UNAVAILABLE` のままであり、全体を `PASS`、すなわち「実装 wave へ進める」としてはならない。
   - scope 内か外か: scope 内。Q2 の測定対象そのものの問題である。

2. **Python evaluator と C++ harness は、別 evaluator ではなくても同じ誤読を共有できる。**

   - 所見: 許されている実装経路は、driver が `_CORPUS_TOPOLOGY` を一度読み、それを Python 行列と C++ literal の双方へ展開する構成である。さらに Python の `pointer_rank` と C++ arena の配置順も同じ driver 作者が対になるよう記述する。例えば `pointer_kind` の意味を双方で入れ替える、または誤った rank 順になるよう proxy arena を構築すれば、両者は全セル一致しても現行 TU と異なる。
   - 根拠 file:line: `s2-plan.md:105-118,126-160,192-205`。権威ある corpus は `sort_swo_oracle.py:629-665`、kind の実際の意味は `:1196-1198`、実配置順は `:1181-1190`。
   - これが真なら生死確認の結論がどう変わるか: `q2=true` は「二つの実装が一致」ではなく「同じ driver 内の想定が自己整合」となる。実 TU から取得した行列、または実 TU の allocation・corpus 構築をそのまま通した実行との比較がない限り Q2 は未証明。
   - scope 内か外か: scope 内。ground truth の独立性検査である。

3. **`UNAVAILABLE` が、設計上の偽を隠す経路になっている。**

   - 所見: 31 IR を一つの生成 TU に束ねた場合、一つの renderer 出力が不正 C++なら compile 全体が失敗する。これは「その IR/emitter が表現・再現できない」という偽である可能性が高いが、プランでは一律 `UNAVAILABLE` になる。同様に、生成 harness 自身の process 異常や protocol 実装不良も環境故障と区別されない。`q2` が boolean なのか unavailable 時に null なのかも未定義である。
   - 根拠 file:line: `s2-plan.md:114-116,200-224`。D344 が `UNAVAILABLE` としたのは compiler 不在や trusted 正例 TU の失敗等の環境故障である (`verbatim-d344.txt:18-20,37-38`)。
   - これが真なら生死確認の結論がどう変わるか: trusted positive control が成功した後の生成 IR compile failure は `FAIL`、driver 自身の protocol/codegen 不良は別の `DRIVER_ERROR` とすべきである。実 oracle は現在環境上 `UNAVAILABLE` なので、proxy 成功で上書きできない。
   - scope 内か外か: scope 内。結果分類の健全性である。

4. **Q3 の 6 probe は主要な whitelist 条件を測っていない。**

   - 所見: 負例は未知 opcode、bool、トップレベル raw string の三つだけで、arity、field domain、direction domain、重複 field、余分 payload を通らない。field whitelist を実装し忘れても、この三負例だけなら Q3=true にできる。counter も同じ driver 内の sink を観測するだけで、実 ingestion 経路の fail-closed 性は示さない。
   - 根拠 file:line: `s2-plan.md:166-185`。現在の合成出力は `CoderProposalSort.implementation: str` (`p3_s4_loop_sort.py:124-133`) で、実 agent schema も C++ 文字列を出す (`.claude/agents/coder-v4-autonomous-sort.md:118-128`)。
   - これが真なら生死確認の結論がどう変わるか: Q3 の unit-level true は実インタフェースの生存証拠にならない。JSON wire → decode → production 相当 admission → render/evaluator/source sink の経路を通すまで Q3 は未証明。
   - scope 内か外か: 欠陥の確認は scope 内。production parser の実装変更は次 wave で scope 外だが、liveness driver 内で wire 経路を模擬することは scope 内。

5. **31 値は「原則のある最小」とは証明されておらず、過小・過大の両方を持つ。**

   - 所見: `depth≤2` と相異なる field という閉包原則を先に仮定すれば31だが、その深さ上限の根拠がない。現 agent 契約は「1つ以上の field の辞書式順序」を典型形とし、3段を禁じていない。三 field を重複なしで許す自然な正規形なら `1 + 6 + 24 + 48 = 79` 値になる。一方、31中 pointer を含む18値は、無関係 object pointer の組込み `<` を portable な trusted semantics として扱えない。
   - 根拠 file:line: `s2-plan.md:69-76,241-253`、`.claude/agents/coder-v4-autonomous-sort.md:78-82,104-114`。pointer の危険はプラン自身も `s2-plan.md:124,253` で認める。
   - これが真なら生死確認の結論がどう変わるか: 31全一致でも「合成余地を保った」とはいえない。逆に pointer rank を IR 意味論として固定すれば trusted 評価は可能になるが、現行 C++ pointer `<` と同じ意味だとは別途実型測定なしにいえない。
   - scope 内か外か: scope 内。親 brief の P1d と段2の拡張生死条件を直接検査している。

   同一 field の2段比較を落とすこと自体は正規化として根拠を付けられる。`f != f ? cmp1(f) : cmp2(f)` は、非同値時に `cmp1`、同値時には第二比較も false なので単一比較 `cmp1` と同値である。ただし、driver が拒否するだけでなく、wire format と合成 agent 契約でこの canonicalization を明記する必要がある。

6. **Q1 は完全な恒真ではないが、測るのは表現性より replica の正確さである。**

   - 所見: renderer は `_one/_single/_two/_mk/_NOSORT_IMPL` の同じ規則を再実装し、手列挙した IR と比較する。失敗条件は実在するが、主に IR/name の転記ミス、空白の複製ミス、上流 generator の更新、別 tree の import である。いずれも IR 言語が comparator を表現不能である反証ではない。
   - 根拠 file:line: `s6_sort_sweep.py:109-158`、`s2-plan.md:49-101`、親の事前結論 `s1-brief.md:61-76`。
   - これが真なら生死確認の結論がどう変わるか: Q1 pass は `emitter_byte_conformance=true` と呼ぶべきで、生死確認を進める新情報には乏しい。Q1 false も直ちに「IR 方向は死」とせず、replica defect と表現不能を分離する必要がある。
   - scope 内か外か: scope 内。

   「表現できる」の独立な証拠には、実 authority literal を変更せず実型 harness で実行した行列と、IR の denotational evaluator の行列を比較する必要がある。IR→C++ の byte 一致は exact binding 用の補助検査として残せるが、主検査にはしない。

7. **proxy と実型の差は storage/key にはなく、pointer IR にだけ具体的な残余がある。**

   - 所見: `storage_`・`key_` だけを読む IR については、proxy が同じ `Storage` と `std::string` を持つ限り、実型の `op_`、`body_`、private storage、`sizeof` の差を式から観測できない。この範囲には結論を変える具体的 IR はない。pointer については、`p_asc/p_desc` と pointer を含む lex2 が具体的な影響候補である。
   - 根拠 file:line: 実 field は `external/ccbench/include/op_element.hh:16-34`、追加 layout は `external/ccbench/cc/silo/include/silo_op_element.hh:39-80`。実 arena は `sort_swo_oracle.py:817-827,1182-1198`。proxy は `s2-plan.md:109-114`。
   - これが真なら生死確認の結論がどう変わるか: storage/key-only 結果は強い proxy 証拠として残せる。pointer を含む18/31値、既存 authority では6/15値は実型で確認するまで条件付きであり、全体 Q2 を真にできない。現在の単調 arena と一般的 ABI では同順位になる見込みは強いが、静的検査だけで実一致とは書けない。
   - scope 内か外か: scope 内。

8. **100行は物理的には圧縮可能だが、独立実験としての監査可能性を壊す。**

   - 所見: Python の join と巨大な一行 string を使えば C++ source 生成を14物理行に押し込める。しかし exact 3-field 型、arena、36 corpus element、3 order、31個の異なる lambda、canonical reindex、protocol を14行で監査可能に書くのは現実的でない。削減順位1〜3は検査範囲を減らさないが、4は生成 C++ の複雑さを行数から隠すだけである。
   - 根拠 file:line: `s2-plan.md:187-205,226-233`。
   - これが真なら生死確認の結論がどう変わるか: 現行の数値的範囲は黙って削られないものの、必要な positive control、独立 corpus path、状態分類を追加すると100行の監査可能な driver は成立しない。プラン自身の規則どおり `DW-G01 line budget infeasible` と報告すべきである。
   - scope 内か外か: scope 内。

## 測らずに真を返す経路

1. Q1 は、authority を作った生成規則を再記述し、その規則から手で作った IR を戻すため、正しく転記すればほぼ予定どおり true になる。これは generator replica の一致であり、意味論的表現性の独立測定ではない。

2. Q3 は、`str` を tuple-only validator へ渡すだけで raw C++ 拒否を true にできる。field whitelist、duplicate field、arity の検査が欠落していても用意された三負例は通る。

3. Q2 は、Python rank に合わせて同じ driver が proxy allocation 順を作れば全セル一致する。実 TU の allocation や実型 relation は通らない。

4. 実 oracle が masstree 未設定で使えないままでも、proxy Q2 と unit Q1/Q3 が成功すれば、単一の `status=PASS` を生成できる。これが最も重大な無測定 true 経路である。

## 測らずに偽を返す経路

1. Q1 renderer の空白・改行・引数名の転記ミスで byte mismatch にすれば、IR 自体は表現可能でも Q1=false になる。これは表現不能ではなく emitter defect である。

2. future IR を JSON array で送る自然な wire formatでは、`["single","key","asc"]` は Python decode 後に `list` となる。`type(raw) is tuple` を要求すると正しい IR を型不一致として拒否し、実際の合成経路は全滅する。

3. 現 agent が許されている三段辞書式 comparator を出した場合、31値 grammar はそれを拒否する。Q3 の用意された probes は成功しても、合成可能性については実質 false である。

4. proxy の pointer `<` が実 TU と異なる挙動を示せば Q2=false になりうるが、それだけでは trusted evaluator の設計が死んだのか、proxy 型・配置差なのかを区別できない。

## driver 設計の是正案

1. 結果を少なくとも次へ分離する。

   - `q1_byte_conformance`
   - `q2_proxy`
   - `q2_actual`
   - `q3_validator_unit`
   - `q3_wire_ingress`
   - `status = PASS | FAIL | UNAVAILABLE | DRIVER_ERROR`

   `q2_actual` が unavailable なら全体 PASS を禁止する。既に観測した semantic false は、別項目の unavailable より優先して残す。

2. Q1 の主検査は、実 authority comparator literal を変更せず compile・callした関係行列と、IR evaluator の行列との比較にする。byte一致は exact emitter の補助検査へ格下げする。

3. Q2 は proxy と実型を別実験にする。実型測定では現行 `_CORPUS_CPP`、allocation、pointer-kind 解釈を通し、driver が `pointer_rank` に合わせた arena を新設しない。現在の環境では `q2_actual=UNAVAILABLE` と正直に終了する。

4. compile/run の前に trusted positive control を置く。positive control 成功後の個別 IR compile failure は `FAIL`、driver protocol 不良は `DRIVER_ERROR`、compilerや依存解決不能だけを `UNAVAILABLE` とする。31件を一括 compileするなら、失敗時に個別化できる仕組みも要る。

5. Q3 は JSON bytes から開始し、将来の wire shapeを明示する。少なくとも以下を同じ ingress 経路へ通す。

   - 未知 opcode `["call","key","asc"]`
   - bad field `["single","key_);...","asc"]`
   - bad direction
   - bad arity・余分 payload
   - duplicate field
   - `lex3`
   - 現行 `implementation` raw C++ object
   - 正しい JSON array/object

   render/evaluator/source append は poison sink にし、負例が到達すれば即失敗させる。

6. IR 値域は agent 契約から先に導出する。三 field の重複なし辞書式をすべて許すなら79値である。同一 field の反復は単一比較へ canonicalizeできる。pointer は「現行 C++ `<` を再現する」のか「明示的 `pointer_rank` 意味論へ変更する」のかを裁定し、後者なら既存 comparator との非同値を隠さない。

7. これらを100行に監査可能に収められなければ、検査を圧縮せず `DW-G01 line budget infeasible` とする。

## 総括

段 2 driver が実際に測るのは、proxy C++ 上の有限 corpus と Python evaluator の一致、および driver 内 validator/renderer の自己整合である。現行実型 oracle の関係行列、実 serialization/ingress の拒否、現合成 agent が出しうる範囲の維持は測らない。

したがって現プランから許される結論は次までである。

- Q1: byte-conformance は真になる見込みが強いが、表現性の独立証拠ではない。
- Q2: proxy は実測可能だが、actual は現在 `UNAVAILABLE`。
- Q3: unit validator の定義確認に留まり、実経路は未証明。
- 31値域: 最小性なし。三段を落として過小、pointer 18値について意味論未確定で過大。
- 総合: `PASS` 不可。現 driver 設計による生死確認は未成立であり、実装 wave を開始する根拠にはならない。