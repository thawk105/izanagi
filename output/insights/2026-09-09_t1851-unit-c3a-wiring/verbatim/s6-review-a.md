## 総括

blocker 1 は通常の fresh/retry 経路では閉じたが、cut-6 の M+A- resume 経路に残っているため、全体としては未閉鎖である。  
holdout inspector は source/test とも byte 不変で、現在の通常/finalize-pending の v5 prefix capture 位置も最終 attempt terminal 後になっている。  
一方、competing journal が実 probe の raw 値を捨てて矛盾した値を記録する問題と、v5 prefix 被覆 test が result producer を検査しない問題がある。  
adapter fix 2 は安全に制限されているが、実装上の受理集合は広げており、親裁定の 2 点以外の変更として明示が必要である。  
pytest は実行していない。以下は指定どおり静的読解と grep/git diff による判定である。

## 所見 RA-1 — cut-6 M+A- resume で blocker 1 が残る

**real、[実測]**

根拠:

- `consume_attempt_ticket()` は marker を先に作り、その後 ledger を追記するため、crash で M+A- が実在し得る。`orchestrator/campaign/s8b_holdout_admission.py:4388-4392`
- cut-6 判定はその M+A- を replay 対象として返す。`s8b_holdout_admission.py:5230-5311,5330-5352`
- runner は verdict が true なら通常の `_run_session()` に戻す。`orchestrator/campaign/s8b_floor_campaign.py:6409-6436`
- resume 後の新 pre-probe が competing だと、既存 marker を残したまま `_finish_session()` で competing completion を書く。`s8b_floor_campaign.py:8954-8972`
- inspector はこの marker + competing completion を必ず `attempt-ledger-coverage-mismatch` で拒否する。`s8b_holdout_admission.py:6733-6741`
- 既存 cut-6 test は `measure_fn` を注入した legacy 経路であり、新しい certified 経路を通らない。`orchestrator/tests/test_s8b_floor_campaign.py:10674-10735`

成果物影響: resume campaign が admission self-check で停止し、v5 result、certified 選択、レポートを完成できない。

推奨: blocker 1 を閉鎖済みにしない。M+A- replay が competing completion に変換されない semantics を再裁定し、同じ crash cutを作って実 inspector まで通す既存テストの再照準が必要である。inspector は緩めないこと。

## 所見 RA-2 — competing session が probe raw 値を偽って記録する

**real、[実測]**

根拠:

- phase 1 は実際の `rc/stdout/stderr/competing` 全体を launcher 私有 state に保存する。`orchestrator/campaign/s8b_floor_attempt_launcher.py:416-435`
- しかし competing branch はそれを使わず、常に `{"rc": 0, "stdout": "", "stderr": "", "competing": True}` を journal へ書く。`orchestrator/campaign/s8b_floor_campaign.py:8960-8972`
- `rc=0` かつ空 stdout は従来の strict classifier では検査不能な組合せであり、旧経路は raw 出力を journal に残す契約だった。`s8b_floor_campaign.py:1695-1722`
- 新 test 自身が `"stdout": "competitor"` を probe から返す一方、記録値との等値を検査していない。`orchestrator/tests/test_s8b_floor_campaign.py:14769-14789,15092-15106`
- 実 inspector も raw の整合を再導出せず `competing` の bool だけを見る。`s8b_holdout_admission.py:6607-6615`

成果物影響: result.sessions と journal の probe 証拠が実測値と異なり、競合除外の理由をレポートから監査できない。分類結果自体は launcher の実 bit に従うが、証拠値は虚偽になる。

推奨: 現在の二段 API では raw を私有化したまま campaign に四 field を正直に記録できないため、親裁定へ戻すこと。少なくとも実 raw に見える偽の四 field を出力してはならない。

## 所見 RA-3 — v5 prefix 被覆 test は result producer の被覆を守っていない

**real、[実測]**

根拠:

- `test_v5_prefix_covers_every_consumed_non_competing_session` は 2 clean + 1 competing を作るので空集合ではない。`orchestrator/tests/test_s8b_floor_campaign.py:15004-15034,15081-15087`
- ただし test は全 session 後に `_capture_floor_attempt_registry_prefix()` を直接呼び、その直後に同じ registry を読んで比較するだけである。`test_s8b_floor_campaign.py:15035-15089`
- `assemble_result()`、通常 finalize、または `result["attempt_registry"]` をこの test は通さない。
- live verifier は報告された `row_count` までの prefix が一致すればよく、live registry に後続行があっても受理する。`orchestrator/campaign/s8b_attempt_registry.py:1050-1086`
- したがって producer が 1 件目の terminal 後の古い prefix を result に載せる変異でも、この名指し test は赤にならない。

成果物影響: 回帰時に v5 result が後続の emit 済み terminal を proof から落としても、当該 test と prefix inspector の組合せだけでは検出できない。

推奨: この既存 test を、複数 clean session の result を実際に組み立て、result の proof が最後の launcher terminal 後の live 全行数/head と一致する検査へ再照準すること。

## 所見 RA-4 — adapter fix 2 は安全だが、実装上の受理集合は広げている

**real、[実測]**

根拠:

- reserve/classify/observation-start の core 呼出しが plain v2 profile から validating profile へ変更された。`orchestrator/campaign/s8b_attempt_registry.py:2557-2584,2759-2843,3011-3062`
- 変更前は既存 sealed terminal が 1 件あるだけで次の transition が無条件拒否され、変更後は検証済み terminal history が受理される。これは operational acceptance set の拡大である。
- 拡大は無制限ではない。terminal file、digest、binding、durable identity は transition 前後で再検証され、private issuer と sealed row 等値も要求される。`s8b_attempt_registry.py:1478-1498,1501-1613,2206-2260`
- tampered evidence の負例と plain profile の拒否対照も実体を通している。`orchestrator/tests/test_s8b_attempt_registry.py:4977-5041`

成果物影響: 2 件目以降の clean attempt とその terminal が registry/result に載せられるようになる。無ければ production campaign は完成しない。

推奨: correctness gate の弱体化ではなく、 accidental over-rejection の限定解除であると記述する。ただし「受理集合を広げていない」とは書かず、親裁定の 2 点以外の第三の受理変更として明示的に追認対象へ入れること。

## 所見 RA-5 — 「旧束縛は retry 側で 0 を強いた」は正しい

**refuted、[実測]**

根拠:

- base は `retry_ordinal` を非 null 非負整数に限定した。`21dfbe0f3:orchestrator/campaign/s8b_terminal_evidence.py:760-768`
- base はそれを `slot_id[4]` に束縛した。`21dfbe0f3:.../s8b_terminal_evidence.py:1140-1157`
- production reserve は `attempt_ordinal != 0`、すなわち `slot_id[4] != 0` を拒否する。`orchestrator/campaign/s8b_attempt_registry.py:2532-2541`
- campaign retry は `1..retry_slots_per_cell` を要求する。`orchestrator/campaign/s8b_floor_contract.py:259-270`

成果物影響: なし。production 到達可能な retry slot に限定すれば、旧検査は retry ordinal に常に 0 を要求し、正規 retry terminal を作れなかった。

推奨: 主張は維持してよいが、「production reserve を通過した v2 slot では」と射程を明示するとより正確である。

## 所見 RA-6 — 「訂正は受理の緩和ではない」は無限定には誤り

**real、[実測]**

根拠:

- base は planned の `None` を型検査で拒否したが、現行は `None` を受理する。`21dfbe0f3:.../s8b_terminal_evidence.py:767` と現行 `orchestrator/campaign/s8b_terminal_evidence.py:760-770`
- 現行は measurement ordinal 0 に `None`、正値にはその正値を要求する。`s8b_terminal_evidence.py:1143-1163`
- 同時に、旧来通った planned `0` と retry の recovery-axis `0` は新たに拒否される。したがって新旧の受理集合は同一でも包含関係でもない。

成果物影響: 実装値は intended axis に合っているが、erratum の表現のままでは、planned `None` と retry 正値を新規受理する事実が ruling/report から隠れる。

推奨する正しい表現: 「これは単調な gate 弱体化ではない。旧誤軸の受理形を拒否し、campaign 契約が要求する planned `None` と retry measurement ordinal を新たに受理する、受理集合の置換である。意図した軸への束縛強度は上がる」。

## 所見 RA-7 — holdout inspector の competing/marker 規則は不変

**refuted、[実測]**

根拠:

- `git diff --numstat 21dfbe0f3..HEAD -- orchestrator/campaign/s8b_holdout_admission.py` は空。
- base/HEAD blob はともに `fab28e9d31b1602e012790ff6610ef2020eafd77`。
- 対応 test blob も base/HEAD ともに `cd2f820eec03668d52e02629d827699798ad204a`。
- 現行 inspector は non-competing に marker 必須、pre-probe competing に marker 禁止の連言を維持している。`s8b_holdout_admission.py:6577-6582,6733-6741`

成果物影響: inspector 自体による受理集合の拡大はない。RA-1 は inspector を緩めた結果ではなく、producer/replay の取り残しである。

推奨: 変更不要。RA-1 を inspector 側で救済しないこと。

## 所見 RA-8 — pre-probe 偽装拒否は type だけではない

**refuted、[実測]**

根拠:

- exact type、発行 state membership、owner identity、one-shot、origin capability seal、公開 bit と封印値の一致をすべて検査する。`orchestrator/campaign/s8b_floor_attempt_launcher.py:405-462`
- caller-constructed exact object、spoofed type、異なる capability origin、再利用がそれぞれ別 test で拒否される。`orchestrator/tests/test_s8b_floor_attempt_launcher.py:2392-2525`
- 再利用 test は第二回呼出し前後の registry/capture effects 不変も確認する。`test_s8b_floor_attempt_launcher.py:2405-2448`

成果物影響: 偽 pre-probe が clean phase 2 を通って registry terminal を発行する経路は確認できない。

推奨: この面は変更不要。

## 所見 RA-9 — ordinal 負例の両軸は分離されている

**refuted、[実測]**

根拠:

- terminal leaf test は measurement ordinal 2、recovery ordinal 0 を明示し、0 への置換を拒否する。`orchestrator/tests/test_s8b_terminal_evidence.py:840-856`
- durable replay test は measurement ordinal 1、recovery ordinal 0 を明示する。`orchestrator/tests/test_s8b_attempt_registry.py:4282-4337`
- planned 正例/負例も `None` と非 null を別々に通している。`test_s8b_terminal_evidence.py:800-837`

成果物影響: 誤って recovery 軸へ戻しても fixture の軸同値によって見逃す問題はない。

推奨: 変更不要。

## blocker 1 が閉じたかの判定 (残る経路の全列挙)

**判定: 未閉鎖。残る competing 経路は cut-6 M+A- replay の 1 系統で、planned/retry の両方に作用する。**

- fresh planned: phase 1 competing なら `consume_attempt_ticket()` より前に return。marker なし、launcher なし。閉じている。
- fresh retry: 同じ `_run_session()` と `_run_certified_floor_session()` を通る。閉じている。
- phase 1 probe の例外: fresh では marker 消費前に `CampaignAbort`。閉じている。
- 通常 resume の未開始 attempt: fresh と同じ。閉じている。
- cut-6 verdict false、M-、または既に A+ の attempt: `_run_session()` を呼ばない。新規 competing completion はない。
- **cut-6 verdict true の M+A-:** marker は前 process ですでに存在する。再 probe が competing なら launcherと再 consumeを呼ばず competing completion を書くが、既存 marker は残る。inspector が拒否する。**これが残存経路。**
- 同じ M+A- で phase 1 が例外になった場合も、marker を保持したまま run-level aborted となる。誤受理はしないが、resume 完遂不能になる同系列の stranded state である。
- clean pre-probe 後の launcher例外: marker は存在するが competing completion は書かれず campaign が abort する。blocker 1 の competing 誤組合せではない。
- post-probe competing: pre-probe は clean で実測開始済みなので marker があるのが正しい。
- finalize-pending: runner、probe、consume、launcherを呼ばない。新しい経路はない。

## 恒真な検査の判定

real は 2 件である。

- `test_v5_prefix_covers_every_consumed_non_competing_session` は非空集合を使う点は正しいが、result producer の prefix capture を通さないため、名前が謳う result proof の被覆保証としては恒真寄りである。
- competing inspector test は実 inspector を通し marker/registry 不在を実測する点は正しいが、probe raw の保存を検査しないため、実装が `"competitor"` を捨てて矛盾した raw 値を出していても通る。

以下の疑いは refuted である。

- inspector stub 使用: 実 `inspect_floor_holdout_admission_evidence()` を呼んでいる。
- pre-probe が type 検査だけ: issuer state、owner、origin seal、one-shot まで検査している。
- v5 prefix test が空集合: clean attempt を 2 件明示している。
- ordinal 負例で両軸同値: terminal/replay の双方で軸を異なる値にしている。

## 受理集合を広げた箇所の判定

- holdout inspector の predicate、marker 連言、対応 test は byte 不変。ここでの拡大はない。
- ordinal 訂正は親裁定範囲だが、planned `None` と retry の measurement ordinal を新規受理するため、文字どおりには受理集合を変更している。同時に旧誤軸形を拒否するので単調な緩和ではない。
- 親裁定の 2 点以外では、adapter fix 2 が「sealed terminal 後の次 transition」を新規受理している。full evidence replay と private issuer 検査に限定されており、invalid evidence の受理拡大は見つからないが、operational acceptance set の拡大ではある。
- 型検査または連言を外した追加箇所は、production source の差分検索では上記 ordinal の nullable 化以外に見つからなかった。
- validator predicate ではないが、competing producer が実 probe と矛盾する session record を新たに到達可能にしている。これは成果物の到達集合に対する実質的な拡大である。

## erratum の 2 主張の検算

1. **「旧束縛は retry 側で恒真に 0 を強いる検査だった」: 正しい。**  
   ただし正確には「production reserve を通過した v2 slot では `attempt_ordinal` が常に 0 なので、旧 retry 束縛は 0 を要求した」である。

2. **「訂正は緩和ではない」: 無限定には誤り。**  
   planned `None` と retry measurement ordinal は以前拒否され、現在は受理される。一方、planned `0` と retry recovery-axis `0` は以前通り得て、現在は拒否される。したがって「受理集合を広げていない」ではなく、「受理集合を intended axis へ置換し、正しさ gate の意味的強度は上げた」と表現すべきである。