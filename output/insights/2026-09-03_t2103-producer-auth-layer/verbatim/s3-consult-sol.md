## 総括

静的検査結果は plan 拒否である。

名目上は 12 負例中 6 件が層を分離するが、R 系を一貫して扱うと C1 系 3 件だけになり、独立した分離パターンは `(issuer=SURVIVED, raw=KILLED, frozen=KILLED)` の 1 種しかない。

また、D 系を全候補 SURVIVED のまま全件 KILL 規則へ入れているため「採用候補なし」が事前確定し、raw 候補は自己ファイルへの guard 追加で固定 SHA-256 と必ず不一致になる。

指定された callee はすべて実在し、記載された producer SHA-256 も一致したが、pytest と変異実走は行っていない。

## 結論が事前に決まっている箇所

- `s2-plan.md:7` と `s2-plan.md:61` は全 12 負例 KILLED を採用条件にしながら D-P/D-T/D-C を全候補 SURVIVED と事前登録しているため、`s2-plan.md:9` の「完全な認証層なし」以外の decision fragment を生成できない。

- `s2-plan.md:65` は D 系を「対照としてのみ」と呼びながら分母へ残しており、比較結果では D 系を採用分母から外すか、D 系を拒否できる第 4 候補を追加しない限り採否規則が無内容になる。

- 表面上の層分離は `s2-plan.md:55` から `:60` の 6 件だが、既存 raw assembly を全候補の実運用経路へ含めれば R 系は全候補 KILLED、追加認証だけを比較すれば全候補 SURVIVED になるため、実質的な分離は C1-P/C1-T/C1-C の 3 件、独立パターンでは 1 種だけである。

- `verbatim-d1345.md:4` が要求する「未 pin の別 producer」に直接該当するのは R 系だけだが、その差は `p3_b4_raw_record_producer.py:1928` から `:1948` の既存再導出から生じるため、新設する 3 認証 prototype の比較結果ではない。

## 恒真な保証

- `s2-plan.md:27` の raw guard を `assemble_b4_raw_analysis` 本体へ追加すると producer 自身の bytes が `s2-plan.md:3` の固定 SHA-256 から変わるため、POS-1 を含む全入力で guard が常に偽になり、固定値を prototype 後に更新するなら「結果を見て更新しない」という事前固定条件を作り直す必要がある。

- issuer predicate が偽になるのは issuance 前に正規 path の bytes が変わった場合、raw predicate が偽になるのは assembly 時に正規 path の bytes が変わった場合、frozen predicate が偽になるのは consumer 時の receipt digest が固定値と違う場合だけであり、`s2-plan.md:58` から `:63` のように正規 source が不変の別 producer と下流改変では全 predicate が常に真になる。

- `p3_b4_analysis_prereg_consumer.py:1044` から `:1047` は `_CLOSURE_PATHS` の全 member を必ず読み、`p3_b4_analysis_path.py:504` から `:516` は同 tuple から receipt member を必ず作るため、`s2-plan.md:36` の「producer member が存在する」はこの生成経路の候補集合では恒真であり、独立した拒否能力として数えられない。

- `s2-plan.md:22` の issuer loader 検査が偽になる入力は sealed field または commitment の改変であって別 producer の実行ではないため、loader 成功を producer provenance の認証結果として比較表へ加算してはならない。

## 機構を通らない緑

- `issue_b4_prerun_publication`、`load_b4_prerun_publication`、`assemble_b4_raw_analysis`、`generate_verified_analysis_source_closure_receipt`、`evaluate_b4_artifacts` はそれぞれ source の `:707`、`:1007`、`:1894`、`:1092`、`:199` に実在するため、callee 名の不存在はない。

- 実 material-report 経路は `p3_b4_material_report.py:196` で必ず assembler を通り、`:224` では receipt なしで evaluator を呼ぶのに、`s2-plan.md:77` と `:114` は frozen 測定だけ assembler と material-report を避けた直接 evaluator probe にするため、その緑は実運用経路で frozen guard が有効なことを証明しない。

- R 系を issuer または frozen の実経路へ流すと `p3_b4_raw_record_producer.py:1942` で先に拒否される一方、期待 SURVIVED を得るには raw assembly を迂回する必要があるため、`s2-plan.md:10` の「改変判断値が分析へ到達した」を同じ harness で満たせない。

- `s2-plan.md:71` の「各組を別 process」だけでは、同じ process 内で issuance 後に source bytes を変更しても既に import 済みの producer code は変わらないため、C1 の SURVIVED を主張するには reload または issuance 後の別 process 実行を事前登録しなければならない。

## 数え方の後付け

- `s2-plan.md:118` は 3 層の guard と固定 trust anchor を新規 production module に置く一方、`:108` から `:114` はその file を production file 数から除いているため、記載どおり採用する場合の見積りは少なくとも issuer `2`、raw `2`、frozen `4` であり、表の `1/1/3` を比較成果物へ転記できない。

- `s2-plan.md:8` は複数候補が全件 KILLED の場合に「変更閉包が最小」を選ぶが、file 数、pin 数、test 波及数、wire 変更数の優先順位または合成規則を定めていないため、`change-closure.json` を事前生成しても decision の選び方は結果後に変更できる。

- `s2-plan.md:103` は frozen の mirrored tuple を各 1 pin と数える一方、issuer の dataclass、commitment、issue、load にまたがる path/hash 利用は 1 literal site に集約して 1 pin とするため、物理配置を変えるだけで候補順位が変わる指標になっている。

## 親 brief の誤り

- `s1-brief.md:25` から `:31` の source anchor は実在して内容も概ね一致するが、`p3_b4_analysis_path.py:504` から `:516` は現在の bytes を hash 化するだけなので、「5-file pin」を固定期待 digest による改変拒否と解釈した受理集合は誤りである。

- `s1-brief.md:47` から `:49` の P2 は raw assembly の拒否能力をゼロと一般化しているが、`p3_b4_raw_record_producer.py:1928` から `:1948` と `test_p3_b4_raw_record_producer.py:1295` から `:1306` が判断値改変の既存拒否を既に実装・検査しているため、比較表は prototype 追加前の baseline KILLED を別列に持つ必要がある。

- `s1-brief.md:32` の「M01〜M18 は 18/18 KILLED」は `verbatim-t2049-mutation-table.md:25` と `test_p3_b4_raw_record_producer.py:1174` が M13 を正例としている事実と矛盾し、source の `test_p3_b4_raw_record_producer.py:807` から `:810` も ID と callable test の対応しか証明しないため、比較 report と decision から 18/18 実測済みの記述を外す必要がある。

- `s1-brief.md:44` から `:46` の P1 は二つの測定方式を実測比較せず一時変異を選ぶ設計判断であり、frozen の closure 費用が最小かを測った根拠として decision に引用できない。

## scope 外だが成果物に効く層

- frozen 候補を実際に効かせるには `p3_b4_material_report.py:224` の production callsite から receipt を渡す変更が必須なので、実験では省略しても「本採用時の必須変更、scope 外、closure 1 file」と裁定パッケージへ明記する必要がある。

- D 系を採用条件に残すなら、`p3_b4_analysis_path.py:306` から `:315` の digest 対応だけでなく raw judgment と source object の judgment を照合する下流 payload-binding 層が必要であり、これを候補外の裁定事項にしなければ受理集合は永久に D-P/D-T/D-C を含む。

- `s2-plan.md:118` の experiment module に置く固定 trust anchor は本採用時の所有者、更新条件、正規 producer 更新との同時変更規則が未定なので、恒久 file 数と pin 数を確定する前に別の裁定パッケージが必要である。

## 変異の帰属が不成立な箇所

- R-P/R-T/R-C の raw KILLED は `p3_b4_raw_record_producer.py:1942` の既存 `source_rederivation` に帰属し、新設 hash guard は正規 source 不変のため真なので、比較結果の `rejecting_function` は既存 baseline と prototype 寄与を分離しなければならない。

- R 系は実経路では issuer/frozen 候補でも raw assembly に拒否され、直接 probe では issuer/frozen を通るため、`s2-plan.md:75` から `:77` のどこを判定境界とするか固定しない限り落ちる判定が一つに定まらない。

- D-P/D-T/D-C は `p3_b4_analysis_path.py:309` から `:315` の digest 検査を通り通常 verdict へ進むため、どの拒否理由にも帰属しない負例であり、mutation ではなく明示的な共通穴 control として別分母に移す必要がある。

- `s2-plan.md:46` から `:48` は意味上の P/T/C しか定めず exact old bytes、new bytes、変更対象 arm、適用順を固定していないため、将来の `mutation-prereg.md` が実走前に exact 置換を固定しない限り単一理由性を後付けできる。

## nit

なし。上記はすべて matrix、受理集合、変更閉包、decision fragment、または一次資料参照を変える指摘である。