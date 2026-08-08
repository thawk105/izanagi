### 所見 1 — `fields` の境界 grammar がなく exact-key は一意に検査できない

区分: blocker

根拠 (`addendum-a.md:3-8,21-29,39-41,653-662`; `erratum-core-s15.md:99-100`; 実測値): `### a01`〜`### a13` の見出しは正確に 13 個ある。一方、`\ba[0-9]{2}\b` は全文で 42 件、見出し以外に 29 件あり、末尾にも `a03/a12/a10/a05` が現れる。`core_ref`、metadata、`fields` の終端を field 外とする機械 grammar はない。

反例または検算: 全文 regex なら 42 件を拾い、YAML fence を読む実装なら `authority` や `core_ref` も余剰になる。`## fields` 配下の直下 H3 だけを key とする実装なら 13 件になるが、その規則は本文にない。親裁定 `s4-adjudication.md:49,193` はこの穴を閉じた扱いにしている。

成果物影響: resolver ごとに追補 A の受理・拒否が分かれ、同じ blob から pilot 投入可否と台帳の preregistration 参照が変わる。

提案: envelope の exact schema を `{document_kind, core_ref, fields}` 等として明示し、`fields` を機械可読 object にするか、「次の H2 までの直下 H3 だけ」と byte-level parser grammar を固定する。

### 所見 2 — erratum の「2 箇所だけ」は自己記述を信じる恒真検査である

区分: blocker

根拠 (`erratum-core-s15.md:50-68,82-92`; `preregistration.md:404,424`): 対象 core の誤記文字列は実際に 2 箇所だけだが、erratum は構造化された置換 operation を持たない。§5 は何を比較して「§3 の 2 箇所だけ」と判定するかを定義していない。また「承認済み erratum を 1 件だけ引く」は一致件数が 0 件・2 件以上の場合の fail-closed 条件になっていない。

反例または検算: §3 に正しい 2 置換を書き、別段落で第 3 の受理条件を「解釈」として supersede する erratum は、§3 の項目数だけ数える validator を通る。承認行が 2 件なら「先頭の 1 件を引く」実装も文面上排除されない。

成果物影響: erratum が exact-key 以外の受理述語を追加・変更でき、certified 選択とレポートの受理集合が事後に動く。

提案: `operations` を exact 2 要素の構造化配列とし、各要素へ target core digest、旧 byte 列またはその hash、一意な位置、置換 byte 列を固定する。承認 manifest の一致件数は `== 1`、それ以外は解決失敗とする。

### 所見 3 — `approval_fold_commit` と承認済み addendum blob の trust root がない

区分: blocker

根拠 (`addendum-a.md:16-17`; `erratum-core-s15.md:79-97`; `record-items.md:49,167`; `docs/decisions.md:11027-11053`): `F_e` の祖先性は検査するが、どの canonical 決定がどの erratum `(path,commit,sha256)` を承認したかの trusted mapping がない。D234 の resolver も addendum A の承認済み digestを入力・trust root に持たず、receipt 側に四つ組を置くだけである。

反例または検算: producer は exact 13 key を持つ未承認 A′で待機値や閾値を変更し、measurement HEAD の祖先に置けば D234 の (iv)〜(vi) を満たせる。同様に任意の祖先 commit を `F_e` と自己申告しても、現契約は「その commit がこの erratum blob を承認した」ことを再導出できない。

成果物影響: 未承認の閾値・待機・erratum が preregistration binding に入り、適格 cluster 集合と certified verdict が変更される。

提案: canonical fold が持つ one-off approval manifest に、承認対象 A と erratum の exact 四つ組を固定する。resolver は caller/receipt でなくこの manifest から `approval_fold_commit` と blob identity を取得する。

### 所見 4 — 「受理集合は狭い側へしか動かない」は偽である

区分: major

根拠 (`erratum-core-s15.md:43-48,70-75`; `package.md:46-51`; `preregistration.md:404-407,422-427`): 旧 §15 は exact 12、erratum 後は exact 13 を要求する。

反例または検算: `R12={fields=A12}`、`R13={fields=A13}` とすれば exact-key により `R12∩R13=∅` で、どちらも他方の部分集合ではない。§14 と旧 §15 を連言するなら旧受理集合は空で、erratum は空集合から `R13` へ受理を拡大する。§15 だけなら `R12→R13` の置換であり、やはり単調縮小ではない。

成果物影響: package と監査レポートが受理集合の変更方向を誤記し、ユーザーの承認根拠が事実と異なる。

提案: 「矛盾した旧仕様を一意な `R13` に置換するため、旧仕様との単調比較は定義しない」と訂正し、拡張ではないという安全証明に使わない。

### 所見 5 — `a03` は恒真ではないが、最初の run に観測窓が存在しない

区分: blocker

根拠 (`addendum-a.md:87-129,135-138`; `record-items.md:159-160`; `t139_positive_control_probe.sh:327-345,454-515`; `limited-screen.tsv:1-37`; `pegasus-runbook.md:15-21,33-48`; 実測値): 有効な非負 counter なら指標範囲は `[0,48]`、閾値 1.0 は busy 比率 `1/48=2.0833%` なので形式上は恒真でない。一方、36 run に対し待機境界は `24+11=35` 個しかなく、最初の run には「待機末尾 10 秒」がない。probe bundle 内の `/proc/stat` counter 証拠は検索 0 件で、記録は load1 のみである。

反例または検算: run 1 に observation を必須化すると規定待機がなく拒否、任意の preflight 10 秒を流用すると未登録の実装裁量になる。`/proc/stat` が 8 列未満、`total=0`、counter 差分不正の場合も zero-fill・拒否・別分類のどれか未定である。`10.000±0.100` 秒自体は単調時計の絶対 deadline で実装可能だが、未実走である。

成果物影響: validator の実装差で全 cluster 拒否または run 1 の無検査受理となり、適格 J と certified 結果が変わる。

提案: 初回固定待機を追加するか preflight の最後 10 秒を明示的に idle window とし、時間表へ帰属させる。8 列未満・負差分・`total≤0` は fail-closed と固定する。R4 probe は main と同じ `gen_S` を原則とし、`qstat -Q` 確認なしの `debug` 代用を認めない。

### 所見 6 — marker と raw を両方消せば開始前へ写せる

区分: blocker

根拠 (`addendum-a.md:140-155`; `record-items.md:92-100,121-127,139-143,160-161,171-180`): record schema は marker 不在かつ raw 痕跡ありを post 側へ倒すが、marker 不在だけで pre を許す。marker の create-only 性は削除不能性や collector からの独立性を保証しない。

反例または検算: durable intent を書いた後に性能 run を開始し、marker を書かないか削除し、run log・`actual_runs` も削除する。attempt rowだけを `pre_performance_infra_failure`、marker=`null` として残せば exact intent coverage を満たし、置換可能になる。

成果物影響: 不利な性能 attempt を開始前失敗へ写して予備と置換でき、採用 cluster と certified 選択が選別される。

提案: pre 側は marker 不在ではなく、trusted collector／scheduler が固定した「性能 process 起動前の外部証拠」を必須にする。証拠欠落・矛盾は post または非置換の判定不能へ倒し、marker は producer が削除できない append-only 領域へ置く。

### 所見 7 — 秒数は合うが grace 契約は cap を 10 秒超過する

区分: major

根拠 (`addendum-a.md:47-82,188-197`; `s4-adjudication.md:25`; `t139_positive_control_probe.sh:511-512`; `run-16-W2-stock-r1.log:8,11`): 再計算は A=`2400`、B=`2340`、予備=`3300` で親の数字と一致する。しかし「cap 到達時に TERM、その 10 秒後に KILL」と「grace は同じ cap に算入」は同時に成立しない。

反例または検算: cap 15 秒なら文面どおりでは TERM が t=15、KILL が t=25 となる。grace を cap 内に入れるには TERM を t=5 に送る必要がある。probe の timeout は executable 全体を包むので W2 の 100000-record table build も 15 秒に含まれ、実際に完了した witness にはなるが、elapsed と余裕幅は記録されておらず将来 36 run の保証にはならない。

成果物影響: phase cap 違反の判定と台帳の phase elapsed が実装ごとに最大 10 秒ずれ、attempt の失敗分類が変わる。

提案: `TERM_at=cap−10`, `KILL_at=cap` と固定し、cap が aggregate phase か各 run/build subprocess かも明示する。15 秒は「一度通った feasibility witness」とだけ位置づける。

### 所見 8 — `a08` の macro 分離は意図的だが、最終 argv と compiler identity は未確定

区分: blocker

根拠 (`addendum-a.md:258-313`; `t139_positive_control_probe.sh:392-424`; `compile-argv-stock.transaction.argv:1,17-23`): `-DCCBENCH_TRACE` は共通 template から macro map へ意図的に分離されており、単純な欠落ではない。しかし `{PREFIX}`、`{TP}`、`{gcc}`、`{g++}` の展開規則、共通 argv と macro map の結合位置・順序が追補にない。実 compiler は `/bin/g++` だが、期待 digest は固定されず事後記録だけである。

反例または検算: validator A は symlink 解決前の `/bin/g++`、validator B は realpath や別 module の gcc を `{g++}` として正規化できる。どちらも symbolic template と自己整合し、異なる compiler bytes・最終 argv・binary を受理できる。

成果物影響: arm の build identity が一意に凍結されず、異なる性能 binary が同じ preregistration として certified レポートへ入る。

提案: build 種別・arm ごとの最終 configure argv 配列を、token 展開・realpath・順序まで固定する。compiler/toolchain は承認済み path/version/bytes digest を A に pin し、事後 hash はその照合値にする。

### 所見 9 — top-level 18 key は正しいが nested schema は closed schema になっていない

区分: blocker

根拠 (`record-items.md:33-43,152-167`): top-level は実数えで 18 key、追加 nested field も追補外 field 違反ではない。しかし `additionalProperties:false` を全 nested object に課す一方、`phase_caps[]`、`phase_events[]`、durable intent pointer、`binary_rehash[]`、`translation_units{}`、`cluster_slots[]` の exact keys・型・必須性・cardinality が列挙されていない。

反例または検算: `a07` の 9 flag は全 30 performance log で表と一致し、W1 の省略 `ycsb_rratio=50` と W2 の省略 `ycsb_rmw=0` は effective map 不一致で落とせる。したがって既定値変更の穴は値レベルでは閉じた。しかし receipt は actual argv の raw bytes/pointer でなく producer の `argv_sha256` だけなので、明示 argv の exact 比較は再計算不能である。同様に `translation_units{}` の完全性も元 `compile_commands.json` なしでは証明できない。

成果物影響: validator ごとに required/optional と配列完全性が変わり、同じ receipt の適格性・J・台帳状態が分岐する。

提案: 実 JSON Schema 相当の一枚へ落とし、全 object の exact keys、required/null、enum、配列長、参照整合性を列挙する。actual argv と `compile_commands.json` は path/size/hash 付き raw pointer を必須化する。

### 所見 10 — 性能 build の生成元が二義的である

区分: major

根拠 (`addendum-a.md:45-51,63-69,157-174`; `record-items.md:102-112,158,162`): 主経路は性能 build を「割当て外」で作る一方、検証割当てでも性能 3 arm と correctness 3 arm の計 6 build を作る。

反例または検算: 「割当て外」を全 scheduler allocation 外と読めば、同じ nominal performance configuration を外部と検証割当てで 2 回 build するが、bytes の一致保証はなく後者の記録先もない。「性能割当ての外」と読んで検証割当ての build を使うなら、`built_outside_allocation` という schema 名・path choice と矛盾する。

成果物影響: `arms.*.binary` がどちらの build を指すかで実行 binary digest とレポートの build provenance が変わる。

提案: 検証割当てを唯一の performance binary producer にするか、検証割当てから性能 3 build を削除するかを一択で固定し、使用しない binary は生成しない。

### 所見 11 — 状態名は明瞭だが R4(a) 後の承認単位が未定義

区分: major

根拠 (`package.md:19-30,181-196,200-212`; `record-items.md:13-20`; `docs/dev-wave/core.md:60-63`): 3 段階名は「文書発効」と「pilot 投入可能」を明確に分け、DW-G04 に反する実装済み主張もしていない。一方、R4(a) では現 addendum A を凍結せず再発行するとしながら、erratum と record-items の承認を先に fold するのか、全 3 本を承認待ちへ戻すのかを書いていない。

反例または検算: ユーザーが「R4(a)、erratum/schema は承認、凍結も承認」と返すと、現在 A は凍結不可なのに一部だけ stage 2 へ進める読みと、全体を stage 1 に留める読みが成立する。probe 結果が指標や schema も変えた場合、先行承認済み schema と再発行 A が不整合になる。

成果物影響: 台帳の状態名、approval fold commit、A/erratum/schema の参照組が異なる時点を指し、pilot admission の前提集合が曖昧になる。

提案: R4(a) の遷移を decision matrix にし、原則は「現 3 本すべて stage 1 のまま、新 A と整合確認済み erratum/schema を再度一括承認」とする。独立承認を許すなら、その対象 blob と再審査条件を個別に固定する。

## 総括

- blocker: **7 件**
- 判定: **NO-GO**。現成果物の承認・凍結および pilot 投入へ進めない。
- ユーザー裁定が要る点:
  1. R1 は、trusted one-off approval manifest を新設して exact 2-operation erratum を採るか、新 core に戻すか。
  2. R4 は `gen_S` で環境 probe を行って A を再発行するか、未実測閾値を受け入れるか。ただし初回待機窓と malformed counter の規則はどちらでも修正必須。
  3. 性能 binary を検証割当てで一度だけ作るのか、全 allocation 外で作って検証割当ての性能 build を削るのか。
  4. R4(a) 時に erratum/schema を独立承認するか、3 本を一括で再提出するか。
  5. package の R2・R3・R5 は既提示どおり未裁定のまま。

テスト・build・Pegasus 実走は行っていない。上記は全文読解、hash、ログ、算術、静的検索による所見であり、緑は主張しない。