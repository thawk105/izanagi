## 総括

1.

- 所見: unit 正例と負例は、計画どおり実装すれば実 `ConditionArmRecord` と実 `require_condition_gate_family` を通る。主な反証は、事前生成 record を返す stub が driver から evaluator への引数結合を検査しなければ恒真化すること、手組み green record を `_issue_arm_record` で偽造できること、(P1) と (P4) が証拠範囲を過大に述べていることの三点である。
- 根拠 file:line: `s2-plan.md:64-88`、`orchestrator/campaign/paper_story_a2_certification.py:613-695`、`orchestrator/campaign/condition_meaning_gate.py:963-988,3837-3947`、`brief.md:21-33,64-67`
- 成果物への影響 1 行: 放置すると unit は緑でも driver が別 request/tree の record を認証でき、材料レポートは保存されていない admission や未実行の層を参照しうる。
- real か nit か: real

## 正例の機構通過

1.

- 所見: 反証なし。計画の正例は evaluator だけを差し替え、実 evaluator が発行した exact `ConditionArmRecord` を driver から実 family へ渡すため、既存の「record と family の両方が stub」という形にはならない。family 関数を事前に別名保存し、その戻り値を期待値に使うことまで固定すべきである。
- 根拠 file:line: `s2-plan.md:64-70`、`orchestrator/campaign/paper_story_a2_certification.py:655-695`、`orchestrator/campaign/condition_meaning_gate.py:3837-3882,3885-3947`。対照として既存検査は `orchestrator/tests/test_paper_story_a2_certification.py:185-223` で record と family の双方を stub にしている。
- 成果物への影響 1 行: この形なら receipt の record ID、admission、canonical JSON は実 family の判断を参照し、fabricated admission による certified 結果を防ぐ。
- real か nit か: real（反証なし）

2.

- 所見: ただし計画の「call count と request 順」だけでは evaluator seam が入力を無視できる。具体的には driver の `evaluate_define_supply_effectuation(captured, ...)` の `captured` を `object()` に変える変異、または `requested_value=value` を `requested_value=defaults[macro]` に変える変異でも、stub が呼出し順だけで事前生成 record を返せば family と receipt は緑になる。各 stub で `_captured is captured_sentinel` と exact `DefineRequest`、`cxx`、`cmake`、meaning declaration を検査する必要がある。
- 根拠 file:line: `orchestrator/campaign/paper_story_a2_certification.py:618-629,655-667`、`s2-plan.md:68-70`。family は渡された record 同士の request digest を照合するだけで、driver がその場で作った request や captured tree とは照合しない (`orchestrator/campaign/condition_meaning_gate.py:3911-3919`)。
- 成果物への影響 1 行: 放置すると別 tree・別値から得た record で当該 cell の receipt を作れる driver 変異が unit を通り、certified 選択結果の参照先が実際に build した木から外れる。
- real か nit か: real

3.

- 所見: 実 g++ / CMake fixture で得る green supply record は exact schema を通る。一方、evidence の手組みは真正性を証明しない。具体例は、同じ `BACKOFF_FIXED=5` request について `_SUPPLIED` の green evidence をコピーし、実際には `preprocess-bytes-identical` で赤になる `_IGNORED` を測ったことにして `_issue_arm_record(..., terminal_status="green", reason_code="requested-default-preprocess-different")` を呼ぶ入力である。family は現在の captured root を受け取らないため、この issued record を受理できる。
- 根拠 file:line: `_issue_arm_record` は構造検査後に issuer capability を付ける (`orchestrator/campaign/condition_meaning_gate.py:963-988`)。green schema は digest の形式と内部関係を検査するが前処理 bytes や現在の capture へ再結合しない (`:3429-3590`)。実 `_IGNORED` の拒否は `orchestrator/tests/test_condition_meaning_gate.py:575-597`、実 green と integrity 検査は `:479-492`。
- 成果物への影響 1 行: 手組み案を採ると実 evaluator が拒否する supply を integrity 緑として family に渡せ、受理集合と receipt の参照事実が広がる。実 fixture 案はこの偽造経路を使わない。
- real か nit か: real

## 負例の恒真性

1.

- 所見: 反証なし。計画の負例では差し替え自身は例外を投げず、issued red record を返す。実 family が `admitted=False` を返し、その後に driver が `CertificationError` を送出する。弱い実装として `admission.admitted` を無視して直ちに `receipts.append(...)` する driver を構成すると、family は正常 return するため例外が発生せず、計画の `pytest.raises(CertificationError)` で落ちる。driver の例外を握りつぶして receipt 作成へ進む変異も同じく落ちる。
- 根拠 file:line: red record の発行は `orchestrator/campaign/condition_meaning_gate.py:963-988`、false 判定は `:3921-3947`、driver の拒否は `orchestrator/campaign/paper_story_a2_certification.py:669-685`、計画の直接 false assertion と driver 例外 assertion は `s2-plan.md:78-88`。
- 成果物への影響 1 行: この負例は red supply を無視して receipt や certified campaign を作る受理集合拡大を阻止する。
- real か nit か: real（反証なし）

2.

- 所見: この負例が証明するのは「実 family が issued red を拒否し、driver が伝搬すること」までであり、実 supply evaluator が `configure-failed` を生成することではない。red record には green の exact evidence schema が適用されず、`configure-failed` の reason vocabulary も検査されないため、負例名や報告で実 configure failure と表現してはならない。
- 根拠 file:line: arm 固有 schema は `terminal_status == "green"` の場合だけ呼ばれる (`orchestrator/campaign/condition_meaning_gate.py:3863-3867`)。計画は red record を直接 `_issue_arm_record` で作る (`s2-plan.md:78-81`)。
- 成果物への影響 1 行: family/wiring の負例と明記すれば成果物値は変わらないが、実 configure 負例と記録すると材料レポートが未実行の観測を参照する。
- real か nit か: nit

## 実走予測の裏取り

1.

- 所見: `_dependency_closure` は owner TU を自動追加しない。depfile の全 entry を走査し、source root 配下なら `source/<relative>` にするだけである。ただし caller が `source/cc/silo/transaction.cc` の存在を分類前に必須化するため、classifier へ到達した経路では owner identity は必ず集合内にある。この限定付きで計画と一致する。
- 根拠 file:line: 走査と identity 化は `orchestrator/campaign/condition_meaning_gate.py:2021-2071`、owner 必須検査は `:2172-2188`、classifier 呼出しは `:2553-2568`。計画の主張は `s2-plan.md:34-39`。
- 成果物への影響 1 行: depfile が owner を欠けば root-only green ではなく `owner-tu-unresolved` の赤となり、cell-0 receipt と campaign は生成されない。
- real か nit か: real（限定付き反証なし）

2.

- 所見: 実 CMake が owner operand を絶対 path で出すなら、`__FILE__` は `<variant-root>/cc/silo/transaction.cc` の形になり、計画どおり classifier が発火する見込みである。しかしコード自身はその spelling を保証しない。具体的に compile argv が owner を相対 path で渡し、requested/control の展開行がそれぞれ `../../../variant/cc/silo/transaction.cc` と `../../../stock/cc/silo/transaction.cc` になれば、closure identity は owner に解決できても requested line に絶対 `source_root/` prefix がなく、replacement count は 0、residual は true になる。
- 根拠 file:line: owner 選択時には path を resolve するが (`orchestrator/campaign/condition_meaning_gate.py:1638-1669`)、preprocess は元の argv を保持して実行する (`:1940-1993,2110-2155`)。classifier は exact `requested_source_root + b"/"` のみ置換する (`:2283-2329`)。
- 成果物への影響 1 行: 実 compile argv が相対形なら予測に反して stock cell が `stock-inert-mismatch` となり、admission、receipt、campaign の現行追認は得られない。
- real か nit か: real

3.

- 所見: `root_dependent_builtin_paths` が非空になる根拠には反証なし。depfile に `include/debug.hh` が含まれ、それが source root 配下の code-owned file で raw `__FILE__` を含むなら、その identity が集合へ入る。location-only 判定は requested/control のどちらか一方でも非空ならよい。
- 根拠 file:line: code-owned 判定と token 検出は `orchestrator/campaign/condition_meaning_gate.py:2047-2064`、最終三条件は `:2332-2345`。計画は `s2-plan.md:37-40`。
- 成果物への影響 1 行: 実 depfileと絶対 path 条件が成立すれば stock arm は root-location-only green となり、4-cell attempt の admission と campaign 到達が可能になる。
- real か nit か: real（反証なし）

## 層 4 修正案の向き

1.

- 所見: lexical shape の分類漏れを exact path pair で追加受理する案は、現在 `stock-inert-mismatch` の入力を green に変えるため受理集合を広げる。depfile に owner がない場合に owner を closure へ補う案も、従来 `owner-tu-unresolved` だった入力を後段の green へ進めうるので同じ向きである。tree/patch の実差を直して現行 classifier に適合させる案だけは gate の受理集合を変えない。計画は「受理集合変更なら裁定へ返す」と明記しており、この点は反証なしだが、実装前の hard stop として扱う必要がある。
- 根拠 file:line: 現行の red/green 分岐は `orchestrator/campaign/condition_meaning_gate.py:2250-2346,2578-2588`、計画の二修正案は `s2-plan.md:51-56`、裁定へ返す条件は `s2-plan.md:109` と `brief.md:66`。brief の非拡大不変条件は `brief.md:56-60`。
- 成果物への影響 1 行: 裁定前に入れると certified 選択、材料レポート、試行台帳の受理集合が旧実装より広がり、旧赤を新緑として参照する。
- real か nit か: real（裁定返却の記載には反証なし）

## 親 brief の (P) と実測値

1.

- 所見: (P1) は evidence 境界を弱める。production attempt が admission 後に失敗すると、発火した admission の canonical 証拠が残らない。具体例は `run_campaign` が例外を投げる場合に加え、summary を返しても `len(summary.results) != len(cells)` または `summary.skipped != 0` となる入力である。この場合 line 3141 で失敗し、line 3142 の receipt 代入に到達しない。従って「正例」は attempt 成功と receipt 保存までを条件にしなければならない。
- 根拠 file:line: family context 到達は `orchestrator/campaign/paper_story_a2_certification.py:3111-3116`、campaign は `:3127-3139`、完走検査と receipt 代入の順は `:3140-3142`。親自身も欠落を認識している (`brief.md:31,46-47`、`s2-plan.md:44-49`)。
- 成果物への影響 1 行: 失敗 attempt を正例扱いすると、材料レポートが receipt のない job log を admission 証拠として参照し、試行台帳の「発火済み」が検証不能になる。
- real か nit か: real

2.

- 所見: (P4) と親の実測一般化は一部誤りである。cell-0 の両 arm の後、実 family admission は必ず実行され、その `admitted=False` を見て拒否行が作られる。未実行なのは cell-1 の arm/admission、cell-0 を含む receipt append、yield、campaign である。「4 cell の admission が一度も実行されていない」または「admission 自体が未到達」は成立しない。
- 根拠 file:line: cell-0 の両 arm は `orchestrator/campaign/paper_story_a2_certification.py:613-668`、family call は `:669-673`、false check と例外は `:674-685`、receipt append はその後の `:686-695`。誤った主張は `brief.md:24-27` と `s2-plan.md:110`。
- 成果物への影響 1 行: 放置すると insight と試行台帳は実行済みの cell-0 admission を未実行と記録し、次 wave の未検査層と参照先を誤る。
- real か nit か: real

3.

- 所見: 提示された拒否行から導ける実測範囲は rr5 だけである。拒否メッセージが非 green record だけを列挙するため、BACKOFF_FIXED meaning が green だったという推論は正しい。一方、rr50 に同じ拒否が出た証拠は射影内にないので、「A-2 4 cell 全体で同じ未到達だった」までは一般化できない。
- 根拠 file:line: 射影された一次行は `verbatim-rulings.md` 末尾の rr5 rejection、親の出典指定も `brief.md:21-23` で rr5 のみ。非 green 限定列挙は `orchestrator/campaign/paper_story_a2_certification.py:675-680`。
- 成果物への影響 1 行: rr50 の一次 log を追加参照しなければ、材料レポートの 4-cell 未到達主張は 2 cell 分を無根拠に一般化した値になる。
- real か nit か: real

4.

- 所見: (P2) は family/wiring 負例としては受理集合を弱めないが、実 evaluator 負例ではない。(P3) は広げる修正を裁定へ返す限り反証なし。旧 T-2022 reject を歴史的事実として維持し、現行 gate の根拠に使わない整理にも反証なし。
- 根拠 file:line: `brief.md:64-67`、`s2-plan.md:99-109`、red を拒否する実 family は `orchestrator/campaign/condition_meaning_gate.py:3921-3947`。
- 成果物への影響 1 行: この境界を明記すれば旧 reject の値と参照は不変で、新 attempt だけが現行 gate 後の独立材料になる。
- real か nit か: real（反証なし）

## 変異の帰属

1.

- 所見: family と driver の責務は二段で分離できる。`condition_meaning_gate.py:3921` を red も green 扱いする変異は、driver 実行前の `admission.admitted is False` で kill する。`paper_story_a2_certification.py:674-685` で admitted を無視する、条件を反転する、または `CertificationError` を握りつぶす変異は、直接 family assertion が成功した後の driver `pytest.raises` で kill する。これは単一理由性がある。
- 根拠 file:line: `s2-plan.md:78-88,135-138`、`orchestrator/campaign/condition_meaning_gate.py:3921-3926`、`orchestrator/campaign/paper_story_a2_certification.py:674-685`
- 成果物への影響 1 行: family の受理集合拡大と driver の拒否無視を別々に帰属でき、どちらが certified campaign を通したか試行台帳で混同しない。
- real か nit か: real（反証なし）

2.

- 所見: `paper_story_a2_certification.py:686-695` の serialization 省略・payload 置換は正例の canonical 完全一致、`:675-684` の detail 脱落は負例の exact substring、`:613-668` の cell-1 または片 arm skip は receipt 数と evaluator call count で kill される。これらも一変異ずつなら単一理由性がある。
- 根拠 file:line: `s2-plan.md:69-70,82-88,137-139`、実処理は `orchestrator/campaign/paper_story_a2_certification.py:613-695`
- 成果物への影響 1 行: receipt の欠落・参照違い・拒否 detail 消失が個別に検出され、材料レポートの canonical record と失敗理由が保たれる。
- real か nit か: real（反証なし）

3.

- 所見: kill が不足する位置は evaluator 呼出しの引数である。`paper_story_a2_certification.py:658` または `:665` の `captured` を別 object にする変異、`:624` の requested value を default にする変異は、stub が事前生成 record を呼出し順で返すだけなら生存する。call count ではなく全引数の exact assertion を追加すべきである。
- 根拠 file:line: 変異位置は `orchestrator/campaign/paper_story_a2_certification.py:618-629,655-667`。計画は回数と request 順のみを明記する (`s2-plan.md:70`)。D1522 は差し替えの実効発火を要求する (`verbatim-rulings.md:34-46`)。
- 成果物への影響 1 行: 未対処なら別 capture・別値を評価した record で receipt を作る driver 変異が残り、certified 結果の tree/value 参照がずれる。
- real か nit か: real

4.

- 所見: 負例を production 相当の `BACKOFF_NOINLINE` 付き genome にすると、driver の message は family が受理する `unestablished` まで「非 green」として列挙するため単一理由表示にならない。計画の「各 evaluator 1 回」を守り、負例 genome を `BACKOFF_FIXED` 一件だけにすれば単一理由性は成立する。
- 根拠 file:line: formatter は全 `terminal_status != "green"` を列挙する (`orchestrator/campaign/paper_story_a2_certification.py:675-680`) が、family は `unestablished` を受理する (`orchestrator/campaign/condition_meaning_gate.py:3922-3926`)。計画の一回固定は `s2-plan.md:88`。
- 成果物への影響 1 行: 複数 macro のままでは試行台帳の拒否 detail に非原因 arm が混ざるが、一件 genome なら reject の原因参照を一意に保てる。
- real か nit か: real

静的検査のみで、pytest や実 CCBench は実走していない。