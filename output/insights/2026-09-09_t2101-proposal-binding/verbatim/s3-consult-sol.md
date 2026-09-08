## 恒真化の可否 (最重要)

- **S1 [real・読解] 現時点の production 受理集合は空であり、検査は今日の formal 実行では発火しない。** 事前登録文書の §5 は `未記入` のまま (`docs/phase3-b4-reflux-ablation-preregistration.md:154-167`) で、全欄を埋めた commit が実走条件 (`:624-626`)。さらに launcher が要求する 3 admission record path (`orchestrator/campaign/p3_b4_admission_record.py:96-102`) は HEAD に存在せず、別 path や未 commit file は拒否される (`:710-739`)。読取り実走でも admission record 3 件、prerun publication 3 artifact とも 0 件だった。したがって親 brief の「今日以降の formal B-4 実行のすべてで発火」は誤りである。

- **S2 [real・読解] ただし、固定した publication root と attempt id に対する比較自体は恒真ではない。不一致入力列は構成できる。**

  1. schema-valid proposal A の hash `H(A)` を attempt `t` に入れ、`issue_b4_prerun_publication` で封印する (`p3_b4_prerun_issuer.py:709-783,822-849`)。
  2. continuation launcher は proposal file をまだ読まず、critic pair を実行して receipt を出し、ready line を待つ (`p3_b4_launcher.py:574-595`)。
  3. 待機中に proposal path へ schema-valid B を置く。例えば base なら `value=21` と `implementation="double now_backoff = 21;"` を揃え、正しい terminal receipt hash を付ける。
  4. ready line 後に driver がその path を読む (`p3_b4_launcher.py:596-609`; `p3_s4_loop.py:2473-2481`)。現行 loader の schema と receipt gate は B を受理する (`p3_s4_loop.py:2025-2103`) が、`H(B) != H(A)` で新 gate は拒否する。

  よって「固定済み root/id の全入力で等式が真」は refuted。ただし S1 のため、現 HEAD の production formal route ではこの列を最後まで実走できない。

- **S3 [real・読解] root を量化すると、実効条件は再び歯止めにならない。** publication root と attempt id は caller が実行時に選ぶ設計 (`stage2-plan.md:52-67`)。issuer は別 root での再発行を明示的に防がず、caller schedule も権威ある母集合に束縛しない (`p3_b4_prerun_issuer.py:8-16,53-64`)。したがって任意の proposal B を作った後、`H(B)` を持つ新 registry を別 root に発行し、その root/id を渡せば必ず通る。plan も別 root 再発行防止を scope 外にしている (`stage2-plan.md:290`)。比較は不一致の組を拒否するが、「事前固定した集合」を証明しない。

## fail-open の抜け穴

- **S4 [refuted・読解] plan を文面どおり実装する限り、列挙された 4 ケースに明示的な fail-open はない。**

  - 束縛引数なし: launcher の `required=True` と 3 driver の B-4 mode 整合検査で拒否 (`stage2-plan.md:127-133`)。
  - publication root が空・相対 path・`None`: `_canonical_absolute_path` が拒否 (`p3_b4_prerun_issuer.py:170-185,1012-1016`)。
  - attempt id 不在・未知: exact 1 件 lookup で拒否。registry 内重複は既存 loader が既に拒否する (`p3_b4_analysis_ledgers.py:470-472,710-769`)。
  - registry/publication 読込み例外: loader は握り潰さず typed error にする (`p3_b4_prerun_issuer.py:1021-1057`)。

  現行コードはそもそもこの束縛を知らないので registry 検査については全て素通しだが、段 2 plan に `if binding is not None` 型の省略分岐は書かれていない。

## 登録値の出所の汚染

- **S5 [real・読解] 登録値は「封印済み registry 由来」ではあるが、その registry 値自体は caller 宣言である。** `issue_b4_prerun_publication` は caller supplied `scheduled_inputs` を受け (`p3_b4_prerun_issuer.py:709-727`)、`initial_proposal_sha256` には小文字 64 hex だけを要求 (`p3_b4_analysis_ledgers.py:339-340`) して、そのまま registry payload へ転記する (`:370-392,670-683`)。proposal B から caller が `H(B)` を計算して新 root を発行する S3 の列は、登録値が比較対象由来になる具体的な汚染経路である。

- **S6 [refuted・読解] helper 内で proposal field、環境変数、proposal path、file 名を expected hash として読む経路は plan にはない。** proposal document 側の自己申告 hash は closed schema の未知 key として拒否できる (`projection_guard.py:291-350`)。直接の自己比較ではなく、問題は caller が選べる publication の権威と発行時点にある。

## 変異の帰属不成立

- **S7 [real・読解] real admission record を使う end-to-end 変異では、projection closure gate が先に赤になる。** `p3_s4_loop.py` と `p3_b4_launcher.py` は closed-critic projection closure の member (`p3_b4_closed_critic.py:623-670`)。比較を外す変異だけでも closure hash が変わり、launcher は driver 前に `assert_b4_document_projection_closures_are_live` を実行する (`p3_b4_launcher.py:352-359`; `p3_b4_closed_critic.py:687-706`)。したがって赤の原因は proposal binding ではなく `[admission-mismatch]` になり得る。

  既存 test fixture は mutant の live bytes から admission expectation を再生成する (`test_p3_b4_closed_critic.py:675-723`) ので、この先行赤を回避できる。ただしそれは production の固定 admission を使う試験とは別物である。mutation 証拠は「動的 fixture 下の比較単体」と「固定 admission が closure drift を拒否する試験」を区別して記録する必要がある。

- **S8 [real・読解] missing-binding の変異は二重 gate によって帰属が隠れる。** plan は launcher argparse と各 driver の両方で必須化する (`stage2-plan.md:129-133`)。helper を fail-open にするだけなら argparse/driver gate が赤を維持し、driver gate を外すだけなら argparse が赤を維持する。missing-root/id のテストを helper 直呼び、driver argv、launcher forwarding の各境界に分けない限り、どの変異を検出した赤か確定しない。

  一方、S2 の B を使う mismatch 変異は既存 schema、receipt、value/literal attribution を全て通せるので、それらが先に赤を出す問題は refuted。

## 過剰拒否

- **S9 [real・読解] plan は registry の precursor hash と、critic 後に消費される next-synthesis proposal を同一物として扱っている。** 事前登録の estimand は「同じ赤 precursor から行う次の 1 synthesis」 (`docs/phase3-b4-reflux-ablation-preregistration.md:60-63`)。registry の初期 proposal は precursor の bootstrap 集合を表し (`:367-380`)、raw producer も `initial_proposal_sha256` を `precursor_hash` として出力する (`p3_b4_raw_record_producer.py:2027-2037`)。対して launcher の `--proposal` は critic pair 実行後に driver へ渡される次 synthesis (`p3_b4_launcher.py:574-607`)。

  同じ block の on/off が異なる critic 出力から異なる正当な proposal を作れば、単一の `initial_proposal_sha256` には高々一方しか一致しない。両方へ一致を強制すれば、treatment が proposal 本文へ反映される余地を消す。receipt key の除外だけではこの object identity の食い違いを解決しない。

- **S10 [real・実走] canonical serializer の実際の区別は plan 記載どおりだった。** repo 実装 (`attempt_registry_core.py:197-206`) を read-only で実行した結果:

  - `1` と `1.0`: 異なる canonical bytes/hash。
  - `0.1` と `1e-1`: 同一 hash。
  - whitespace、key 順: parse 結果が同じなら同一 hash。
  - Unicode normalization: 行わないため、`U+00E9` と `U+0065 U+0301` は異なる hash。
  - duplicate key:通常 loader は最後の値を採り、その単一値と同じ hash。base K2 だけは既存 hook で拒否 (`p3_s4_loop.py:2026-2035`)。

  base driver は `1` と `1.0` の双方を proposal 型で受け得て (`p3_s4_loop.py:383-392`)、attribution は float 比較 (`:1393-1407`)、実 genome は `int(coder.value)` (`:1628-1629`) なので実行候補は同じになる。それでも hash は異なる。正当性を「document exact value」に置くなら意図的差異だが、「実行候補の意味」に置くなら過剰拒否であり、plan はこの identity 選択を裁定していない。

  また authoritative issuer-side proposal producer が repo に無いため、issuer と loop が同じ正当な proposal から別 hash を出す現行 production 列は構成不能である。plan の正例が同じ新 helper で registry 値も計算するだけなら、相互運用性ではなく自己一致しか実証しない。

## 親の実測値の検算

- **S11 [real/refuted・読解と読取り実走] 6 項目の判定。**

  1. 実行経路は概ね real。ただし continuation では proposal load 前に critic pair と launcher sidecar 書込みがある (`p3_b4_launcher.py:574-607`)。
  2. launcher と 3 driver が prerun publication を知らない、は real。
  3. `initial_proposal_sha256` が 64 hex 検査だけ、proposal canonical 規約と production producer がない、は real。
  4. `load_b4_prerun_publication` が registry/manifest/receipt を再検証する、は real (`p3_b4_prerun_issuer.py:1009-1177`)。
  5. artifact 0 件は読取り実走で再現したが、「したがって今日以降の formal 全実行で発火」は refuted。§5 未発効かつ admission record 0 件なので formal production 自体が開始不能。
  6. 63-path campaign-lock closure について `p3_s4_loop.py` が外、launcher が内という局所事実は real (`campaign_lock.py:60-113`)。しかし「pin 閉包全体」の一般化は不完全。両 file は別の closed-critic projection closure に入り、全 3 driver の hashへ効く (`p3_b4_closed_critic.py:623-670`)。現在は preregistration の projection 値が `未記入` で admission record も無いため、既存の凍結 literal を動かさない、までは real。将来の formal activation 時に新 projection 値と admission record が必要ない、という含意は false。

## scope 外の層と裁定パッケージ候補

- **S12 [real・読解] runtime の成功した束縛が downstream 証拠に残らず、attempt を後から付け替えられる。** launcher sidecar は campaign/arm/driver/admission だけで、publication root、receipt hash、attempt id、observed proposal hashを持たない (`p3_b4_launcher.py:390-403`)。raw producer は後から caller supplied `attempt_id` を受け (`p3_b4_raw_record_producer.py:920-942`)、その id の registry/manifest 行を選び (`:945-984`)、driver だけを campaign receipt と比較 (`:1976-1982`) した後、registry の hash を `precursor_hash` として新たに転記する (`:2027-2037`)。

  再現列は、同じ driver の manifest 行 A/B を用意し、A の id/hash で campaign を通した後、A を報告せず同じ campaign roots を B の request として渡すこと。runtime に A を使った証拠が無いため、B の planned path と `precursor_hash` へ再帰属できる。plan は raw/material 層を変更しない (`stage2-plan.md:294-296`)。

  **裁定候補:** 既存 launch/campaign evidence に publication receipt identity、attempt id、observed proposal hash を耐久化し、raw producer が同じ値を再導出できるところまで T-2101 の完了条件に含める。これを含めない限り「registry ラベルの事後選択」は閉じない。

- **S13 [real・読解] registry-only attempt を実行できる。** manifest は eligible 先頭 201 行だけ (`p3_b4_analysis_ledgers.py:1071-1105`) だが、plan は manifest membership を明示的に要求しない (`stage2-plan.md:76`)。202 行 publication の 202 番目を attempt id に指定すれば、hash 一致時に loop gate は通る。raw producer は後で manifest 不在を拒否する (`p3_b4_raw_record_producer.py:945-954`) が、build/WAL/campaign は既に実行済みになる。

  **裁定候補:** 「formal B-4 = manifest の 201 行」にするなら、既に load 済みの manifest membership と registry row の driver 一致を実行前条件へ含める。registry 全行を実行可能とするなら、201 試行を事前固定したという主張とは分離が必要である。

- **S14 [real・読解] 上流の proposal identity が未裁定。** S9 のとおり `initial_proposal_sha256` が precursor proposal なのか、arm ごとの next-synthesis proposal なのかで必要 schema が異なる。

  **裁定候補:** D1343 の「提案」がどの artifact を指すかを明示する。precursor なら loop の `--proposal` と比較してはならず、既存 receipt/WAL/checkpoint から precursor を束縛する必要がある。next synthesis なら一 block 一 hash では on/off の別提案を表せず、arm 別の事前固定可能性そのものを再裁定する必要がある。

## 総括

固定した publication root/id に限れば、新比較は実際に不一致を拒否でき、恒真ではない。一方、現 HEAD の production formal 入力集合は空であり、今日発火する gate ではない。

さらに plan のままでは、caller が publication root/id を選び直せること、成功した束縛が raw 層へ残らないこと、registry の precursor hash と critic 後の next-synthesis proposal を混同していることにより、「事前固定した 201 試行」の証明にはならない。特に S9 と S12 は実装開始前に裁定が必要であり、段 2 plan をそのまま author へ渡すべきではない。pytest は未実走、file 編集・commit は行っていない。