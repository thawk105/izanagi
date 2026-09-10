## pacing 定数の判定 (P2 への回答)

**判定: real。P2 は全体として保護不足の向きに誤っている。ただし 3.0 / 1.0 / 45.0 秒そのものを短くする根拠はなく、最小間隔は維持すべきである。** 問題は特に DBLP で、軸 1 の 45 秒を、その値と組になっていた retry・cooldown なしで継承している点にある。

| host | 軸 3 preflight の形 | exact request 集中 | 軸 1 との比較 |
|---|---:|---:|---|
| arXiv | 373 本。360 本は page size 200、13 本は 1。query 部は 40〜1437 文字、平均 1068.9 | 36 本連続の塊が 10 回 | 軸 1 の既定 page size も 200。3 秒を変える根拠はない |
| OpenAlex | 23 本。10 本は page size 200、13 本は 1。query 部は 62〜1431 文字、平均 529.7 | 多くは他 host と交互 | 軸 1 も page size 200。1 秒は所要をほぼ増やさない |
| DBLP | 1533 本。1525 本は page size 100、8 本は 1。query 部は 32〜87 文字、平均 64.2 | 終端に **1415 本連続** | 軸 1 は同じ page size 100 だが、1 leaf 単位の runner で retry と 45 分 cooldown を持つ |

導出元は、軸 3 の factory (`related_work_search.py:1204-1223`)、360 arXiv / 10 OpenAlex / 1523 DBLP main の生成 (`related_work_search.py:1351-1438`)、control と lookup (`related_work_search.py:1443-1634`)、stream ID sort と preflight 順 (`related_work_search.py:1696-1699,5966-5978`) である。URL 長はこの catalog から `materialize_request` (`related_work_search.py:1840-1871`) を機械再導出した。

軸 1 の page capacity は同じ 200 / 200 / 100 (`orchestrator/axis1_search/runner.py:339-344`)。ただし軸 1 は最大 4 attempt、3→6→12 秒 retry (`runner.py:352-357,1703-1704,1929-1930`) と、DBLP failure 後の 2700 秒 cooldown (`runner.py:42,1959-1974`) を持つ。実測も「45 分冷却後に 30 秒で回復」「7〜10 分冷却後に 45 秒で完走」であり、45 秒単独の安全性を証明していない (`verbatim.md:90-98`)。軸 3 transport は one-shot で (`related_work_search.py:2543-2545`)、非 200 後も preflight loopを継続する (`related_work_search.py:6335-6405`)。

したがって判定は次のとおり。

- arXiv 3 秒、OpenAlex 1 秒: **refuted**。軸 3 固有の証拠から過小・過大とは判定できない。緩めない。
- DBLP 45 秒という床: **単独の床としては refuted できない**。
- 「45 秒だけ移植すれば軸 1 と同等に保護できる」: **real、保護不足**。1415 本連続中に切断が始まっても cooldown せず送り続ける。

成果物影響: DBLP の途中切断後も残り row が `unavailable` へ落ち、valid な bundle/report のまま B2・B5 の観測集合が大量欠損する。

## 所要時間と deadline の判定

**判定: nominal preflight は約 19.5 時間で正しいが、実装が保証する有限上限は存在しない。本走込みが deadline 内という判定もまだできない。**

空の limiter 状態、応答時間 0 として exact な登録順を再生すると、sleep は次になる。

- DBLP: 68,883 秒
- arXiv: 1,090 秒
- OpenAlex: 2 秒
- 合計: **69,975 秒 = 19 時間 26 分 15 秒**

親の計算は `1533×45 + 373×3 + 23×1 = 70,127 秒 = 19 時間 28 分 47 秒`。最初の request や他 host 処理で満たされる間隔を含むため 152 秒だけ過大だが、19.5 時間という丸めは妥当である (`brief.md:53-55`)。

接続・応答時間は単純に 19.5 時間へ加算されない。応答待ちが次の host interval を消化するためである。仮に全 1929 request が「全処理込みで exact 30 秒」で終わると仮定すると、

`1929×30 + 残 sleep 22,830 = 80,700 秒 = 22 時間 25 分`

となる。したがって無 retry・有限応答という運用仮定なら、少なくとも丸 1 日を確保するのが現実的な計画値である。

ただしこれは上限ではない。30 秒は connection の socket timeout であり (`tools/run_axis3_search.py:352`, `related_work_search.py:2609-2616`)、`response.read()` に byte ceiling も全体 wall-clock deadline もない。30 秒未満ごとに body を送り続ける相手や巨大 body に対して終了時刻は有限に束縛されない。軸 1 にあった 16 MiB ceiling (`runner.py:35,143-147`) も軸 3にはない。

さらに packed preflight は attempt ごとに started、response-received、response-committed の WAL frame をそれぞれ fsync する (`related_work_search.py:4803-4819,5026-5029,5101-5111,5417-5425`)。計画の limiter state fsync (`plan.md:28-32`) も加えると、正常 1929 本だけで少なくとも `1929×4 = 7716` 回の file fsync がある。finalize は WAL 全体を読み、body を復号して保持し直す (`related_work_search.py:3935-4018,5444-5453`)。これらにも byte/time ceiling はない。

deadline と request 上限の余裕は以下である。

- preflight 1929 本は 20 万本の **0.9645%**。残り 198,071 本。
- 30 日は 2,592,000 秒。nominal preflight 後は 2,522,025 秒、約 **29 日 4 時間 34 分**残る。
- `run-ready` は preflight の first timestamp と attempt 数を引き継ぐ (`related_work_search.py:6905-6909`)。
- 残り時間を DBLP だけへ使っても、45 秒床では最大 `floor(2,522,025/45)+1 = 56,046` 本。arXiv・OpenAlex・I/O があるので実際はこれ未満。

本走の page 数は page-zero の `declared_total` がまだ無いため不明である。従って B5 の live 結果なしに「本走まで 30 日内」は証明できない。成果物影響: deadline 内に収まらない catalog なら preflight report の B5 が否定側となり、本走の受理集合を発行できない。

なお `RUN_DEADLINE` は送信前 `consume` 時だけ検査される (`related_work_search.py:5517-5527`)。送信済み request や finalize を30日で打ち切る process deadlineではない。

## real 所見

1. **`unconfirmed_attempt_intent` の窓は依然として大きく、時間上限もない。**

   sleep を `begin_attempt` 前へ置けば19.44時間の sleep中断は安全になる。しかしその後は、intent の WAL fsyncから transport、無制限 body read、raw WAL fsync、parse、response commit の完了まで pending である (`plan.md:37-49,151`; `related_work_search.py:4983-5034,5551-5600`)。resume は `pending` と `response_received` を区別せず、attempt intent が一つでもあれば即 `unconfirmed_attempt_intent` で停止する (`related_work_search.py:8130-8140,8570-8580`)。raw response が耐久化済みでも同じであることを既存 test 自身が固定している (`test_related_work_search.py:966-1017,2274-2308`)。

   成果物影響: bundle は `in_progress`、preflight report は未 final、`resume --live` は request 0 本で blocked。別 bundle でやり直す場合は availability から全 prefix を再送する。

2. **deadline / 20万上限への到達が、確実に「送っていない pending intent」を作る。**

   計画順は limiter → `begin_attempt` → budget consume (`plan.md:42-47`)。現実装も begin を永続化した後に `budget.consume` する (`related_work_search.py:5563-5583`)。sleep 中に deadline を越えた場合や attempts が既に20万なら、consume が例外を出す前に pending intent が残る。これは送信の曖昧性ではなく、機械的に no-send と分かるのに resume不能となる経路である。

   成果物影響: deadline/上限到達を表す正常な停止 report/checkpointではなく、`unconfirmed_attempt_intent` の袋小路になる。

3. **計画した pacing 観測は WAL から exact に再導出できない。**

   計画は limiter state に小数秒を保存し、通常 report は limiter 観測、resume/validator は WAL `intent_at` から exact 再導出するとしている (`plan.md:34-35,63-77`)。しかし `intent_at` は `_format_time` で microsecond を落として保存される (`related_work_search.py:3521-3523,5015-5016`)。例えば実間隔 3.2 秒が WAL では 4 秒になり得る。さらに intent は実 HTTP send より前で、actual send は `connection.request` 時点である (`related_work_search.py:2614`)。

   成果物影響: report v2 と WAL の exact equality validator が正常 bundle を拒否するか、整数化された intent 間隔を「実観測 request 間隔」と誤記録する。

4. **OpenAlex は単独では枠内だが、並行 axis 1 と安全に共存しない。**

   軸 1 の観測した 1 窓100 request (`verbatim.md:31-33`) と依頼の limit 1000、runner が `X-RateLimit-Credits-Used` を request credit として読む実装 (`runner.py:511-538`) から、1 request = 10 credits。軸 3 は `10 main + 8 control + 5 lookup = 23` 本なので `23×10 = 230 credits`、単独なら770残る。

   しかし limiter/quota state は bundle-local (`runner.py:1612-1615`; `plan.md:148`)。並行 axis 1 が77本を超えると `23 + axis1 > 100 request`、すなわち1000 credits超過となる。軸 3には成功 responseの remaining を使った pre-send reserve gateがなく、最初の OpenAlex 429だけが全停止する (`related_work_search.py:6235-6301`)。後続 OpenAlex 429は `unavailable` にして DBLPまで続行する (`related_work_search.py:5694-5702,6335-6405`)。

   成果物影響: 最初なら `wire_attempt_count=1` の429 stop report、後続なら OpenAlex row が `unavailable` の1929-attempt reportとなり、B2/B5の集合が変わる。

5. **test は実時間 sleep を避けられるが、計画の更新面と所要台帳が不足している。**

   計画した mutable fake clock/fake sleeper 自体は正しい (`plan.md:105-130`)。一方、現 fixture は固定 clock のまま1929本を送る (`test_related_work_search.py:271-288,1089-1101`)。fake sleeper「だけ」でなく、この clock も対で差し替えなければならない。また `_run_stream` へ limiter を必須追加する計画 (`plan.md:56`) に対し、既存 direct call が複数残る (`test_related_work_search.py:1140-1142,1169-1174,1598-1603,2134-2136`)。

   現台帳は全22,157 nodeidで合計14,766.477秒、約4時間6分。対象 fileだけでも108 nodeid、201.309秒であり、38、30、25、21、20、18、8.8秒の重量 nodeを含む (`acceptance_duration_ledger.json:1595-1702,22160-22164`)。新 nodeidと1929 observation検査は所要を正に増やすが、planには台帳更新がない。

   成果物影響: test実装後の acceptance duration ledger が node集合・durationとも旧値のままになり、受入全走の時間見積りが過小になる。

## refuted 所見

1. **committed prefix の残り行継続は refuted。正常に commit 済みで pending が無い場合は本当に残り行へ進む。**

   WALから attempted ID と次の登録 row を再導出し (`related_work_search.py:8141-8155`)、未 attempt の planned rowだけを送る (`related_work_search.py:8274-8287`)。既存 testも1928本 prefixから最後の1本を選ぶことを固定している (`test_related_work_search.py:2582-2591`)。

   成果物影響: clean boundaryでの停止なら既存 prefixを保ち、最終 reportの1929本集合を再構成できる。

2. **記録 commit が HEAD を動かすだけで seal/resume が壊れる、は refuted。**

   `register` はその時点の実装 HEAD を registration inputsの `commit` と sealの `resolved_head_commit` に固定する (`tools/run_axis3_search.py:119-152`; `related_work_search.py:3453-3455`)。後の検証は sealed resolved commitを再利用しつつ、現在 HEADとは8 fileの blob一致だけを見る (`related_work_search.py:3489-3508,3093-3105`)。global HEAD identityを比較しないことも test済み (`test_related_work_search.py:2003-2007`)。

   成果物影響: registration成果物 commitや新実行記録 commitがclosure 8 fileを変えない限り、seal・bundle・resumeの参照は変わらない。

3. **bundleを元の絶対 pathから動かすと検証不能、は refuted。ただし compatible checkoutは必要。**

   `--bundle` は origin argvへ絶対 pathで焼かれる (`related_work_search.py:446-487`)。しかし bundle内部参照はroot相対 (`related_work_search.py:6967-6974`) で、validatorはorigin argvを再解析するだけで現在の検証rootとの一致を要求しない (`related_work_search.py:7293-7308`)。resume側は新しい resume argvの `--bundle` を現在rootへ結び直す (`related_work_search.py:8525-8534`)。

   worktree撤去後も bundle移動自体は可能。ただし production validationは現在 checkoutのclosure 8 blobsとHEAD一致を再要求し、catalog/sealも明示入力が必要 (`related_work_search.py:7260-7280`)。sealed commit相当の checkoutを再作成できることが条件である。

4. **OpenAlex 23本だけで1000-credit枠を超える、は refuted。**

   導出は `23×10=230`。他 producerが無ければ枠の23%である。成果物影響: daily creditだけを理由に availability 429を予想する必要はない。

5. **計画された新test自身が19.5時間 sleepする、は refuted。**

   mutable fake clock/sleeperを全該当 callへ正しく渡せば実時間 sleepは0。既存 test fileには直接起動 harnessも既にある (`test_related_work_search.py:2879-2886`)。新規 test file計画ではないため、追加 harnessは不要である。

## nit

- 親の19.5時間計算は152秒だけ保守側。成果物やdeadline判定を変える差ではない。
- 射影された軸 1 runnerはquery bytesを自前で持たず、別catalogの `build_request`へ委譲する (`runner.py:416-419`)。したがって軸 1 と軸 3のquery文字数の exact 比較はこの射影だけでは成立しない。「同一3索引だから同じrequest負荷」というP2の根拠は、少なくとも証明済みとは扱えない。
- `--bundle` の旧絶対 pathは provenanceとして残るため、移動後の読者には旧pathであることを明記した方がよいが、validator failureにはならない。

## 裁定パッケージ候補

1. **同一 login nodeの外部 producer排他**

   裁定問い: 軸 3 live preflight中、同一3 hostへ送る別bundle/waveを禁止するか。推奨はこの一走に限った運用排他。これが無ければOpenAlex credit、host間隔、N4はいずれもbundle内観測だけでは確定しない。根拠: `plan.md:148`、`runner.py:1612-1615`。

2. **DBLP failure後の扱い**

   裁定問い: 45秒継続で残りを `unavailable` にするか、軸 1と同様にcooldown後の再開を要求するか。推奨は後者。45秒床は絶対に緩めない。根拠: `verbatim.md:90-98`、`runner.py:1959-1974`。

3. **pending intentの回復強度**

   裁定問い: raw response耐久化済み intentを回復可能とするか、現状どおりbundle放棄と全再走だけを許すか。これは one-shot receipt・重複送信・予算会計の契約判断であり、pacing実装だけで決めるべきではない。根拠: `related_work_search.py:8130-8140,8570-8580`。

4. **transportの有限上限**

   裁定問い: 無制限 body/read時間を受け入れるか、body ceilingと全attempt wall-clock ceilingを契約へ追加するか。追加すると失敗分類と受理集合が変わり得るため、実装案ではなく事前裁定が必要。根拠: `related_work_search.py:2609-2619` と軸 1の `runner.py:35,143-147`。

## 総括

P2の床を短くする理由はない。一方、**DBLP 45秒をcooldownなしで1415本連続へ適用することと、bundle間を共有しないOpenAlex pacing/quotaは保護不足**である。

live preflightの正常時所要は約19時間26分、30秒全attempt仮定で約22時間25分なので、運用上は丸1日が目安になる。しかし無制限 body readとWAL finalizeのため、コードが保証する有限上限はない。

最も危険なのは、sleep後の `begin_attempt` からcommitまでの長い pending窓と、deadline/20万上限検査をintent後に行う順序である。process deathや正常な予算拒否でも resume不能になり得る。対して、sealのHEAD closure順序、記録commit、外部bundle path、clean committed-prefix resumeは成立している。