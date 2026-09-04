## 緑へ倒れる経路

重大な反例が存在する。計画の分類器は root bytes の出現を `__FILE__` 展開に結び付けず、差分区間内の同じ bytes をすべて置換する。根拠は `s2-plan.md:33-43` と、`root_dependent_builtin_paths` が依存ファイル内の単純な token 検索にすぎない `orchestrator/campaign/condition_meaning_gate.py:2028-2063`。

具体例として、

```text
requested source root = b"/srv/ccbench"
control source root   = b"/srv/ccbench/stock"
```

preprocess 出力を次にする。

```python
requested = (
    b'static constexpr const char *semantic_mode = "/srv/ccbench";\n'
    b'static constexpr const char *file_probe = "/srv/ccbench/include/probe.hh";\n'
)
control = (
    b'static constexpr const char *semantic_mode = "/srv/ccbench/stock";\n'
    b'static constexpr const char *file_probe = "/srv/ccbench/stock/include/probe.hh";\n'
)
```

`file_probe` は本物の `__FILE__` 展開とするため、`root_dependent_builtin_paths` は非空になる。一方、`semantic_mode` は実行時に観測可能な本物の意味差である。計画どおり requested 側の `/srv/ccbench` をすべて `/srv/ccbench/stock` に置換すると control bytes と完全一致し、`root_diff_has_residual=False` で緑になる。

これは dependency closure の hash 差でも止まらない。closure equality は非 inert 分岐だけにある `condition_meaning_gate.py:2434-2440` から動かさない計画だからである (`s2-plan.md:19-29`)。

部分文字列でも同じ穴がある。

```python
requested = b'const char *mode = "/srv/ccbench-v2";\n'
control   = b'const char *mode = "/srv/ccbench/stock-v2";\n'
```

単純走査は `/srv/ccbench` を token 境界や生成元に関係なく置換する。別の依存に未使用の `__FILE__` があれば P1-4 も満たせる。

曖昧入力については次のとおり。

| 入力 | 計画どおりなら |
|---|---|
| 置換対象 0 個 | `s2-plan.md:26-29,77-80` により赤。反証なし。 |
| 置換後も長さまたは bytes が違う | 完全一致検査で残差扱い。反証なし。 |
| 通常の改行を含まない root が行途中にある | 行単位 opcode は行内部を切らない。反証なし。 |
| control root が requested root の子 | 一回走査と非再走査なら二重置換しない。反証なし。 |
| root bytes が別の値の部分文字列 | 上記のとおり緑へ倒れる。 |
| source/build の requested token が重複または競合 | `s2-plan.md:40` は固定順を定める一方、`s2-plan.md:29` の「曖昧なら赤」の判定条件を定義していない。固定順だけで済ませる実装は緑になりうる。 |

成果物影響: この入力は supply を red から green に変え、`condition_meaning_gate.py:3743-3748` により certified selection の受理集合へ意味の異なる個体を追加し、材料レポートと試行台帳がその green record/admission を参照する。

## 負例の恒真性

提案された負例自体は恒真ではなく、新分類器まで到達する。`s2-plan.md:91-129` のとおり両 header に `__FILE__` を追加し、control だけに `+ 1` を入れる。owner TU は requested 側で `include/backoff.hh` を include し、control 側も対応する stock header を includeする (`fixtures/condition_meaning_gate/supplied/cc/silo/transaction.cc:12-14`, `supplied/stock/cc/silo/transaction.cc:7-9`)。inert では closure equality を行わないため、計画変更後は classifier に入る。

ただし、この負例を含め正例も通す弱い実装を構成できる。

```python
for replace_opcode in opcodes:
    changed = requested_chunk.replace(requested_root, control_root)
    residual |= changed != control_chunk
green = replacement_count > 0 and not residual
```

この実装は `+ 1` が残るため負例を赤にし、正例も緑にする。しかし前節の `semantic_mode` まで root として畳み、意味差を緑にする。すなわち負例が検査するのは「root 置換後に残る通常 bytes」だけであり、「置換した bytes が本当に置き場所由来か」ではない。

既存の `test_backoff_fixed_minus_one_requires_stock_preprocess_identity` (`orchestrator/tests/test_condition_meaning_gate.py:1265-1283`) は root builtin がなく、置換数 0 と通常残差の両方で赤になる。新機構の P1-4、置換数、残差判定のどれを検査したか分離できない。

成果物影響: 現行の正負例を全通過する実装でも、意味の異なる個体を certified selection と材料レポートへ混入させられる。

## 正例の機構通過

計画された正例は現行実装に対して赤になる。

- copied fixture 作成位置は `test_condition_meaning_gate.py:142-145`。
- 追記予定の `__FILE__` は `s2-plan.md:91-100`。
- requested owner は `transaction.cc:13` から patched header を、control owner は stock `transaction.cc:8` から stock header を読む。
- dependency file の実際の閉包を読み込むのは `condition_meaning_gate.py:2166-2173`。
- header 内の `__FILE__` は `root_dependent_builtin_paths` に入る (`condition_meaning_gate.py:2062-2063`)。
- stock 時は source/control root が needle に追加され (`condition_meaning_gate.py:2420-2424`)、出力に root があれば `preprocess-root-dependent-builtin` で赤になる (`condition_meaning_gate.py:2425-2433`)。

fixture の意味行は requested の `include/backoff.hh:5` と control の `stock/include/backoff.hh:1` で一致する。したがって追記後の差は `__FILE__` のパス行となり、現行 guard の対象である。少なくとも現行の raw mismatch 判定 `condition_meaning_gate.py:2452-2456` でも赤になる。

ただし test-first の「赤」だけには二理由がある。旧 root guard と raw mismatch の双方が同じ正例を拒否するためである。変更後に新 reason、digest 不一致、replacement、residual false まで検査する `s2-plan.md:102-113` は新機構を通る確認になる。

未被覆なのは build-root 対応、root 候補の重複、insert/delete、全出力を先に正規化する実装である。正例は source-root 置換だけを通る。

成果物影響: 正例の変更後 green は A-2 admission を変えるので material。ただし未被覆変異が残ると、同じ green reason の受理集合が意図以上に広がる。

## 計画と D1523 の整合

元オブジェクトを物理的に変更しない点は担保される。`_PreprocessResult` は frozen で bytes を保持する (`condition_meaning_gate.py:628-646`)、digest は compiler stdout から作る (`condition_meaning_gate.py:2189-2192`)、evidence に元 digest/length を残す (`condition_meaning_gate.py:2220-2246`)。この限定では反証なし。

しかし D1523 の正しさ上の理由とは整合しない。`s2-plan.md:33-50` は raw diff を得た後、すべての非 equal 区間を root 置換した bytes で判定する。equal 区間は元から判定へ影響しないため、実質的には「比較結果に影響する全 bytes を畳んでから比べる」形である。処理順が diff 後になっただけで、誤った畳み方が本物の差を隠す問題は残る。

さらに新 evidence は interval 数、使用 mapping、residual bool だけで、元 preprocess bytes や各差分 span を保存しない (`s2-plan.md:59-70`)。validator は raw digest 不一致を確認できても、置換位置が `__FILE__` 由来だったかを再検証できない。`s2-plan.md:46-50` の immutability と digest 契約は「元 bytes が違った」ことしか保証せず、D1523 の `d1523-verbatim.md:13-18` が要求する差の性質を保証しない。

P1 の評価は次のとおり。

- P1-1: 直接の緑化原因ではない。ただし「linemarker を持つ」という `brief.md:72-73` の前提は、実装が `-P` を付ける `condition_meaning_gate.py:1990-1991` と矛盾する。provenance には使えない。
- P1-2: 弱化。root bytes の境界と生成元を問わない一方向置換が意味差を隠す。
- P1-3: 弱化。build root まで許可対象を広げる一方、root-dependent builtin との対応を証明しない。
- P1-4: 弱化。`__FILE__` は展開された必要すらなく、コメント、inactive branch、未使用 macro 内でも raw substring 検索により非空になる (`condition_meaning_gate.py:2028-2063`)。
- P1-5: 反証なし。別 reason と digest 不一致契約は旧 identity reason の意味を守る。
- P1-6: 単独では裁定どおりだが、上記分類器と組み合わせると hard red を unsound green に置き換える箇所になる。

D1523 と整合させるには、少なくとも置換可能 span を独立した compiler observationなどで root-dependent builtin の展開箇所へ束縛し、単なる同一 bytes の文字列リテラルを許可しない必要がある。由来を証明できない場合は赤へ倒すべきである。

成果物影響: 計画のままでは D1523 が却下した事故型が新 reason の下で再現し、certified な選択結果、材料レポート、試行台帳の値と参照を変える。

## 親 brief の実測と一般化の検査

`brief.md:21-26` の「debug.hh が `__FILE__` を7箇所で使うので A-2 inert は構造的に常時赤」という一般化は、射影資料からは成立しない。

現行 guard に必要なのは次の二条件である。

1. 実際の compiler dependency file に含まれる code-owned ファイルのどれかが raw bytes として `__FILE__` または `__BASE_FILE__` を持つ (`condition_meaning_gate.py:2020-2063,2166-2173`)。
2. requested/control preprocess 出力のどれかに build/source/control root の exact bytes がある (`condition_meaning_gate.py:2416-2427`)。

`debug.hh` の token 数だけでは、A-2 owner TU `cc/silo/transaction.cc` の実 dependency closure に同ファイルが含まれること、該当 token が active に展開されること、展開結果に物理 root が残ることのいずれも証明しない。また guard は token を検出した依存と、root needle が現れた出力位置を結び付けていない。したがって仮に reason が `preprocess-root-dependent-builtin` でも、「debug.hh の展開が原因」とは帰結できない。

射影対象には `external/ccbench/include/debug.hh` と実際の A-2 owner TU/include graph が含まれていないため、7箇所という数と実 closure membershipは独立に再確認できなかった。これは非包含の証明ではなく、親 brief の裏取り不足である。射影内の fixture owner は `<atomic>`, `<cstdint>`, `backoff.hh` だけを include し (`supplied/cc/silo/transaction.cc:1-13`)、debug.hh を根拠にしていない。

別原因の候補は、別の code-owned dependencyにある未展開 `__FILE__` と、configure defineや通常の文字列リテラル由来の root bytes の組み合わせである。guard が発火しなければ、別 root による raw mismatch は `stock-inert-mismatch` (`condition_meaning_gate.py:2452-2456`) になる。

成果物影響: 「常時赤」の原因を誤認したまま guard を外すと、本来別原因で赤だった cell まで緑化し、A-2 の certified 集合と後続レポート、台帳参照を広げる。

## 変異の位置と単一理由性

- `condition_meaning_gate.py:2425-2433` 相当で inert に旧 guard を残す変異: 変更後の正例が kill する。最終実装に classifier が存在する前提では単一理由になる。
- 新 helper の transformed bytes 完全一致判定 (`s2-plan.md:42-43`) を「root が1個あれば成功」にする変異: 新負例が kill する。ただし evaluator が residual true のまま green を出すだけの変異は、予定 validator `s2-plan.md:77-80` も同じ入力を拒否するため単一理由でない。
- residual の計算自体を常に false にする変異: 新負例が green となり、負例の `root_diff_has_residual is True` 期待で直接 kill できる。
- P1-4 の非空条件を削除する変異: 現行 `test_condition_meaning_gate.py:1265-1283` は置換数 0 と通常残差でも赤になるため kill できない。inactive `__FILE__` もない semantic-root-only 負例が必要。
- 実置換数 `> 0` を削除する変異: evaluator 条件、予定 validator、raw 不一致後の完全一致という三層が重なり、現計画では単一理由性がない。
- insert/delete を許す変異: 提案負例は2行の replace opcode であり kill しない。root を含む純 insert と純 delete を別々に登録する必要がある。
- build-root mapping を削除する変異: 正例は source-root の `__FILE__` だけなので生存する。build-root-only 正例が必要。ただし build root を受理対象にする正当性自体も未証明である。
- 最長一致、同長固定順、非再走査を崩す変異 (`s2-plan.md:40`): fixture の source/build candidate は競合しないため、多くが生存する。競合 mapping 専用入力が必要。
- 差分区間だけでなく全 requested 出力を先に `.replace` する変異: raw digest を置換前に保存すれば正例、負例、schema 負例をすべて通せる。D1523 が要求した構造差を現テストは kill しない。
- blind byte substitution をそのまま採る変異: 前節の `semantic_mode` 反例でのみ kill できる。現計画の最重要な未登録変異である。
- validator の type/schema 箇所 `condition_meaning_gate.py:3302-3412` 相当: `s2-plan.md:131-133` の forged-record 負例が直接 kill するが、classifier の正しさは検査しない。

成果物影響: 生存変異は同じ new green reason の受理範囲を広げるため nit ではなく、certified selection、材料レポート、試行台帳の全てに影響する。

## 総括

計画は元 bytes を物理的には保存するが、「root と同じ bytes が差分にある」ことと「その差が root-dependent builtin 由来である」ことを混同している。具体的な意味差を緑にできるため、このまま author 段へ渡すのは正しさ境界上危険である。

最低限、次を計画へ追加する必要がある。

- 本物の `__FILE__` 差と semantic root literal 差を同居させ、必ず赤にする負例。
- inactive/comment 内の `__FILE__` と semantic root 差を組み合わせた負例。
- build-root-only、insert、delete、競合 root mapping の個別テスト。
- 許可 span を builtin 展開の生成元へ束縛する設計。束縛不能なら赤。

pytest は実行しておらず、以上は指定資料だけによる静的検査である。