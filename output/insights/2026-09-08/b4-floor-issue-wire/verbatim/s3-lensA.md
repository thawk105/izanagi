## 所見

1. **must-fix — 現行 `floor-pair-summary/v2` は、既裁定 D1699 に反する D を生成する。**  
   `s1-brief.md:3-6` と `s2-plan.md:23-30,59` は現行 v2 を権威入力にするが、driver は 3 role を別 session に分け (`floor_pair_driver.py:1257-1288`)、その中央値から D を作る (`floor_pair_driver.py:2585-2595`)。D1699 は candidate/reference を同じ低水準 session で測るよう明示している (`rulings-verbatim.md:218-222`)。現行 v2 との integration test が通ることは、むしろ旧意味を権威化する証拠になる。  
   **放置時の影響:** cross-session drift を含む旧 D の floor が §5 から解決され、分析 verdict に使われる。

2. **must-fix — `nextafter(+∞)` 1 回では、入力 throughput に対する exact D を覆わない。具体的に floor が小さくなる。**  
   plan は top-level float だけを 1 ULP 上げる (`s2-plan.md:67-77`) が、driver は先に binary64 の除算・減算を行う (`floor_pair_driver.py:1358-1363`)。例えば `candidate_1=0.10000000000000003`、`candidate_2=reference=0.1` では、driver の D は `2^-52 = 2.220446049250313e-16`。その直上は `2.2204460492503136e-16` だが、入力 binary64 を exact ratio として計算した D は `1/3602879701896397 ≈ 2.7755575615628914e-16` で、なお大きい。plan 自身もこの限界を認めている (`s2-plan.md:176`)。  
   **放置時の影響:** evaluator の inclusive tie (`p3_b4_analysis_contract.py:525-528`) が非 tie に変わり、片側検定を通しやすくなるため規律 2 違反。issuer 側で summary の source medians から exact に再導出するか、覆えない入力を拒否する必要がある。

3. **must-fix — summary の `candidate_floor` を derivation と再照合する規則がない。**  
   `s2-plan.md:23-30` は derivation の存在と `upper == candidate_floor` しか要求しない。例えば他の全 field を正しく保った canonical v2 に `derivation[].samples[].difference=0.25`、stratum upper `0.25` を置きつつ、top-level `upper=0.0`, `candidate_floor=0.0` とすれば、列挙された条件では通り、authority floor は `5e-324` になる。さらに `upper=False` も Python では `False == 0.0` なので、`upper` の exact float 型を要求しない限り通る。producer 本来の最大集約は `floor_pair_driver.py:2607-2625`、top-level 射影は `:2688-2704`。  
   **放置時の影響:** 受理集合に producer が生成し得ない自己矛盾 summary が入り、floor を任意に小さくして tie を減らせる。

4. **must-fix — 採用記録 gate は採用裁定へ束縛されず、存在検査に留まる。**  
   plan の検証対象は schema、`D<正整数>`、summary path/hash、identity だけ (`s2-plan.md:31-36`)。caller が canonical な `D1` 記録を作れば、実際にその D が存在し floor 採用を記録したかを確認せず発行できる。D1641 が要求するのは測定後の採用裁定を D として記録すること (`rulings-verbatim.md:101-107`)。  
   **放置時の影響:** authority artifact と report の `floor.source.decision_id` が未採用値を「採用済み」と参照する。実 D へ束縛するか、この記録を検証済み採用とは宣言しない必要がある。

5. **must-fix — absent byte 非退行 test の oracle が変更後 composer 自身で、変異帰属が成立しない。**  
   `s2-plan.md:122-126` は public 結果を同じ module の `_build_report_value()`・`_render_markdown()` から作った値と比較する。両 helper に同じ変異を入れると両辺が変わり、test は通る。現行 test も floor/report_scope の一部 (`test_p3_b4_material_report.py:635-660`)、serializer との自己一致 (`:419-473`)、同一実装の 1 回目と 2 回目の保存 bytes (`:1006-1058`) しか見ていない。親 brief の「既存 test が report bytes を守る」 (`s1-brief.md:26`) は誤り。  
   **放置時の影響:** authority 不在時の JSON/Markdown bytes が変わっても全予定 test が緑になり得る。変更前 bytes/digest に独立した固定 oracle が必要。

6. **must-fix — authority present × assembly rejected の意味が未定義で、どちらに実装しても誤表示し得る。**  
   現行 `_load_and_evaluate()` は assembly rejection で evaluator 前に return する (`p3_b4_material_report.py:220-228`)。一方、plan の present helper は無条件に `analysis.floor_argument` を ratio にし、floor を present とする (`s2-plan.md:87-96`)。resolver を early return 後に置けば存在する floor を absent と報告し、前に置けば evaluator を呼んでいないのに「渡した引数」を表示する。予定 test にこの交差ケースはない (`s2-plan.md:124-126`)。  
   **放置時の影響:** report の floor availability または analysis argument が実際の参照・呼出しと食い違う。

7. **親 brief の実測記述の補正。**  
   `s1-brief.md:9` の `floor=None` は現物では `p3_b4_material_report.py:242` であり `:243` ではない。これは **nit**。また「分析 verdict は 1 種類」は successful assembly の評価経路には正しいが、assembly rejection は evaluator を呼ばず `not_evaluated` になる (`p3_b4_material_report.py:220-228,834-841`) ため、材料レポート全経路への一般化は過剰。  
   **放置時の影響:** 値や受理集合は変わらないが、レビュー対象行と到達状態の説明を誤る。

## scope 外だが real

- D1699 に適合する low-level session 構成・新 D の実装自体は driver 側の別 wave。だが、本 wave が現行 v2 を権威化しないことは must-fix の依存境界。
- T-2289 の source-closure receipt 未接続は実在するが、D1530 により本 wave へ同梱しない。
- D1696 の 9 validator は実在する未検査面だが、人手責任に置く既裁定どおり scope 外。上の must-fix はその一般化を要求していない。

## 反証できなかった点

- `candidate_floor` 自体からの direct 変換は単調増加だった。`0.0` と `-0.0` は `5e-324`、`5e-324` は `1e-323` になり、小さくならない。
- `0.9999999999999999` は直上が `1.0` となって発行拒否、`1.0`、負値、非有限値、`1e308` も列挙規則では拒否される。
- float は現契約で実際に拒否される (`p3_b4_analysis_contract.py:233-253,323-325`)。
- closure tuple は両 module で exact 一致しており (`p3_b4_analysis_prereg_consumer.py:98-104`, `p3_b4_analysis_path.py:67-73`)、plan の編集対象外。批准節 pin、既存 `SCHEMA_VERSION` / `GENERATOR_IDENTITY` を変える箇所も見つからなかった。
- schema は plan の「exact schema/format」を文字どおり literal equality で実装すれば、同じ field 名の v3 も拒否される。「新しければ受理する」緩さは plan 上にはない。
- successful assembly については、resolver の `Fraction` を evaluator に渡す方針と wrapper test により、従来どおり `None` を渡す inert 配線は捕捉できる。

## 総括

- 現行 v2 を D1699 適合済みの権威入力として受理しない。
- 1 ULP 加算ではなく、source medians から exact D と最大値を再導出・照合する。
- 採用記録を実際の採用 D へ束縛するか、検証済み採用という宣言を外す。
- absent bytes は変更前の独立 golden で守る。
- authority present × assembly rejected の report 意味と test を明示する。