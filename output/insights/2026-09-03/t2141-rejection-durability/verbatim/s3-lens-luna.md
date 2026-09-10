## 所見一覧

1. `p3_b4_raw_record_producer.py:1665-1672,1849-1851` — deferred を記録しないため「rejection 後に deferred、leaf は absent」を古い rejection で説明済みと誤認し、材料レポートの非保証が誤って落ちる。台帳は最新状態を欠き、certified 選択は未接続なので直接不変。
2. `s2-plan.md:40,44` — 未終端 tail を無視したまま `O_APPEND` すると、次の event が tail に連結して newline 終端済みの不正行になり、以後 loader、assembly、材料レポートが恒久的に fail-closed する。成功公開の受理集合は不変だが台帳参照が失われる。
3. `p3_b4_raw_record_producer.py:1781-1804` — batch の collection 型不正は publication 検証より先に返るため、`s2-plan.md:52-55` の「validated publication へ記録」は現行順序のままでは実現不能。順序を変えるなら二重不正時の rejection 値が変わり、変えなければ台帳と材料レポートに記録が残らない。
4. `p3_b4_prerun_issuer.py:369-379` と `p3_b4_analysis_ledgers.py:1050-1084` — planned mapping は全 scheduled attempt、manifest は先頭 201 eligible だけであり、全 absent planned leaf を coverage 判定すると非選択 attempt が永久に unresolved になる。母数値は復元できるが材料レポートの受理条件が未定義。
5. `attempt_registry_core.py:233-250` と `p3_b4_prerun_issuer.py:1081-1094` — chain head の外部 commitment が無いため、完全行単位の末尾切断や file 全削除は検出不能。event count、棄却率、理由が過少化し、材料レポートの参照値が変わるが成功公開集合は不変。
6. `p3_b4_raw_record_producer.py:128-133,1725-1771,1894-2058` — 共通の `B4RawRecordRejection` に assembly だけ ledger snapshot を付ける方法が未定義。field を足せば単発・batch rejection と report の `assembly.reason` wire shape も変わり、足さなければ assembly rejection に snapshot を付けられない。
7. `p3_b4_raw_record_producer.py:1739-1741,1791-1804` — publication 検証そのものの rejection には信頼できる記録 root が無く、brief が名指す全 `B4RawRecordRejection` の耐久化には届かない。保証を「publication 検証後の producer rejection」に明示的に狭める必要がある。
8. `s2-plan.md:121-136` — listed tests には concurrent append、ledger symlink、未終端 tail 後の再 append が無く、`flock`、`O_NOFOLLOW`、tail 方針を抜いても全記載 test が緑になりうる。成果物影響を検査できないため nit ではなく実効性不足。
9. `p3_b4_raw_record_producer.py:453-472` — brief の「0o700 real-parent 検査」は実在せず、既存 directory の mode は検査しない。現行成果物値への直接影響は示されないため nit。
10. `p3_b4_prerun_issuer.py:432-440` — planned path が固定 leaf の祖先になれるのは publication root だけ、という `s2-plan.md:21-24` の説明は誤りで、root より上の祖先もある。新規発行では既存 leaf 検査が通常拒否するが reload predicate 自体は閉じておらず、nit。

## file:line の食い違い

主要な参照先は実在した。特に次は記載どおりである。

- producer: `:21-36`, `:52-55`, `:105-117`, `:120-161`, `:267-307`, `:453-558`, `:640-652`, `:1665-1672`, `:1725-1771`, `:1774-1891`, `:1894-2058`, `:2061-2076`
- issuer: `:40-48`, `:362-397`, `:418-440`, `:455-467`, `:621-623`, `:650-657`, `:737-740`, `:1056-1067`, `:1100-1119`, `:1178-1190`
- material report: `:38-43`, `:53-58`, `:89-97`, `:183-239`, `:665-797`, `:800-828`, `:849-921`
- analysis ledger: `:546-592`, `:595-639`, `:772-811`
- contract、WAL、layout: `p3_b4_analysis_contract.py:59-67`, `wal.py:406-427,933-1123`, `layout.py:203-208`, `model.py:28-36`
- tests: raw producer `:802-805,1101-1115,1183-1199,1330-1384`、issuer `:218-223,534-571,596-623`、material report `:183-240,223-226`

食い違いは次のとおり。

- `s1-brief.md:54` の reload anchor `p3_b4_prerun_issuer.py:1007-1046` は関数入口と固定 3 file の読取までで、planned path と count の実復元は `:1081-1119`。段 2 plan の anchor は正しい。
- `s1-brief.md:51` の batch 戻り口 `:1836-1885` は途中で切れており、例外結果の構築と return は `:1836-1891`。
- `s1-brief.md:25` の「0o700 検査」は、実コード `:453-472` では「新規 mkdir の mode が 0o700」であって既存 mode の検査ではない。
- `s2-plan.md:146` の「deferred を記録すると no-publish 契約が壊れる」は誤り。別 leaf への状態 event は planned success leaf の no-publish 契約と両立する。
- `s2-plan.md:150` の「chain は欠落を検出する」は中間欠落には正しいが、完全 suffix 欠落と file 削除には正しくない。
- 提案定数 `B4_RAW_RECORD_REJECTIONS_NAME` は当然ながら現コードにはまだ存在しない。追加予定箇所と export 箇所は実在する。

## 相乗り可否の再測定

既存経路への完全な相乗り先は無く、新しい leaf 一種という結論自体は妥当である。

- issuer 固定 artifact は相乗り不可。registry と manifest の bytes は receipt descriptor に pin され、後追記すると `p3_b4_prerun_issuer.py:1056-1067` で publication が失効する。receipt の scheduled count、planned mapping、issuer commitment は再利用できる。
- admission record は Git 上の事前 admission を検証する read-only verifier で、事後 producer outcome の writer、path、schema を持たない。
- `B4RegistryViolation` は器としても不足する。`p3_b4_analysis_ledgers.py:562-570` が保持するのは attempt、block、5 値の reason、evidence hash だけで、producer の code、artifact、field、detail を復元できない。`append_registry_violation` も file writer ではなく新しい in-memory registry 値を返すだけである。完全情報を別 artifact に置けば結局新 leaf が必要になる。
- campaign WAL は campaign root 配下で、publication root から常に特定できない。stage 語彙と終端順序も producer rejection 用ではない。
- 成功 attempt leaf への union は `PLANNED_PATH_CONFLICT` と leaf 自身の IO error を記録できず、assembly schema も壊す。

したがって「既存 receipt の母数と mappingを再利用し、専用 leaf を一種だけ足す」は最小である。ただし各 absent の説明まで閉じるなら、同じ leaf に rejection だけでなく deferred を限定的な別 event kind として残す必要がある。

## consumer 側で復元できない残り

- 実験母数は復元できる。receipt から全 scheduled count と全 planned path、manifest から分析対象 201 block を得られる。ただし report では「scheduled 母数」「manifest 選択数」「成功・rejection・deferred・未試行」を別々に定義すべきである。
- intact な scoped rejection event については、attempt ID、code、artifact、field、detail を復元できる。
- deferred は復元できない。特に過去 rejection の後に deferred が起きた場合、古い rejection が現在の absent 理由として誤用される。
- event 無しは未試行、append failure、完全削除を区別できない。ここでは非保証を残すしかない。
- `attempt_id=None` は証拠自体を読めても候補へ join できない。
- publication validation failure は信頼できる root に束縛できず、publication-root consumer から復元不能。
- scheduled だが manifest 非選択の attempt は、registry と manifest の差から `not_selected` と説明できる。plan の単純な「absent + matching rejection」判定ではこの説明を使っていない。
- 完全 suffix truncation と ledger 削除は有効な空または短い chain と区別できない。
- shared rejection 型の扱いを決めない限り、assembly rejection と ledger snapshot を一つの戻り値から同時に読める保証も未完成である。

## scope 逸脱と効かない追加

hash chain とその改変 matrix は、本題の「return 前に耐久化し、後で理由を読む」ためには必須でない。しかも head が pin されないため削除耐性は得られない。canonical JSONL、issuer commitment、closed issue schema、fsync までに絞れば本題は閉じ、chain 関係の負例だけが赤になる。これは自己追加した corruption gate の検査であり、成果物の正常値や成功受理集合は変わらない。

反実仮想では次が問題になる。

- `flock` を抜く: 記載された test は全て逐次なので赤にならない。
- `O_NOFOLLOW` を抜く: ledger leaf の symlink test が無いため赤にならない。
- 未終端 tail の特別扱いを抜く: test が無いため赤にならない。現案の扱いは次回 append を壊すので、WAL と同様に append 前に拒否するか、有効 prefix へ明示修復する必要がある。
- root directory の毎回 `fsync` を初回作成時だけへ減らす: 既存 entry の後続 append の耐久結果は同じで、一般的な failure injection 一件だけでは差を検出できない。
- Markdown の event count 表示を抜く: JSON を機械可読正本とする要件は変わらず、記載テストにも専用 assertion がないため赤にならない。nit。
- ledger bytes と全 parsed events の双方を report に重複埋込みする案は一方だけでも復元可能である。独立再照合は内部整合性を検査するが、両方を恒久 wire contract にする必要性は示されていない。

逆に、deferred event、manifest 対象に限定した coverage 判定、batch validation precedence、未終端 tail の動作 test は仮想リスクではなく、現プランの到達可能な入力で結果が変わるため本題に必要である。

## 受入時間の見積り

過去実測は raw producer test file が 451.31 秒から 26.25 秒、後の取り込み後実測が 28.98 秒である。今回の単発 rejection assertion は既存 `:1101-1115` へ相乗りでき、実証拠生成を増やす必要はない。

過去の `/tmp` 実測 48.5 ms/fsync を使うと、file と root directory の二回 fsync は一 event 約 97 ms、201 event で約 19.5 秒である。毎 append の全 ledger reload は二次コストになるが、201 行なら証拠生成よりは小さい見込みである。

既存の一実 pair + replica fixture、material report の module fixture、request schema 段の安価な rejection を再利用すれば、追加分は概ね 5から25秒、関連 file 合計でも静的には約 60 秒以内が目安である。

ただし plan は「全 candidate を説明する fixture」の作り方を固定していない。ここで `_evidence_scope` を 201 回使うと、再び 402 real invoke と約 4000 durable file write を生み、過去の約 451 秒を再現する。201 rejection は unknown-field など evidence derivation 前の入力で作り、実 rejection は既存一件だけに限定すべきである。

また corruption matrix は一つの安価な ledger fixture を複製して使い、各 case で 201-block evidence を再生成してはならない。pytest は実行しておらず、この見積りは静的である。

## 総括

- 新しい専用 leaf 一種という配置判断と、既存経路へ相乗りできない判定は妥当。
- 最重要欠陥は deferred 非記録で、古い rejection による absent 理由の誤帰属と非保証の誤削除が起きる。
- 未終端 tail 後の append は ledger を壊し、batch collection rejection の記録も現行順序と両立しない。
- scheduled 全体と manifest 201 件の coverage domain を分ける必要がある。
- head を pin しない hash chain は suffix 欠落を検出せず、現 scope では削除候補。
- publication 検証前 rejection は耐久化対象外であることを保証文に明記すべき。
- 以上を直すまで、段 2 plan はそのまま採ってはいけない。
- fixture 再利用を明記すれば受入時間は約 60 秒以内、明記しなければ 451 秒再発の危険がある。