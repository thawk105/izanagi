## 総括

現行の段 2 プランのまま実装してはいけない。  
最重は S1/S8B の lock-only 経路で、epoch 判定、lock SHA、WAL が同一 snapshot だという保証が計画にない。  
次に、commit witness、`batch_commit_counts == 0`、`verify_configs` など D1246 を越える producer schema 固定がある。  
既存拒否の消失と例外の握り潰しは refuted。ただし 8 変異のうち 1、3、6、8 は再照準が必要。pytest は未実走。

## 所見

- A-01 / 判定 real / scope 内 / S1 は lock-only epoch 判定後に別 read で WAL を取得する (`orchestrator/campaign/s1_report.py:382-424`)。S8B は epoch 射影を先に作り (`orchestrator/campaign/s8b_oracle_report.py:2302-2305`)、後で別に WAL を読む (`orchestrator/campaign/s8b_oracle_report.py:1736-1738`)。lock SHA helper 自体も独立した再読である (`orchestrator/verifier/commit_receipt.py:82-103`)。段 2 の「同一 snapshot の lock SHA」は実装手順に落ちていない / 成果物影響: lock A の E1 判定と lock B に束縛された receipt/WAL を混ぜる余地が残り、D1246 の束縛を証明できない。

- A-02 / 判定 real / scope 内 / D1246 が要求するのは verdict/receipt の束縛である (`docs/decisions.md:40872-40880`)。一方、`commits`、`aborts`、commit witness、`verify_configs` は current producer の診断 schema であり (`orchestrator/campaign/pipeline.py:1244-1308,1410-1462`)、receipt evidence に保存されるのは tag/verdict/certified/result SHA だけである (`orchestrator/verifier/commit_receipt.py:223-237`) / 成果物影響: D1246 に必要ない field drift で正当な certified artifact を拒否する。

- A-03 / 判定 real / scope 内 / `batch_commit_counts == 0` は単なる official 5 campaign の観測ではなく、現行 live producer が非 0 を明示拒否している (`orchestrator/campaign/pipeline.py:1273-1287`)。ただし CCBench は batch commit を独立集計し、TPSにも加える (`external/ccbench/common/result.cc:47-61`) / 成果物影響: 現時点の campaign は壊さないが、将来 verifier が batch trace 帰属を実装して正当に certify しても、persisted helper が旧制約で拒否する。

- A-04 / 判定 real / scope 内 / receipt validator は evidence の全 row に `"serializable"` と `certified is True` を要求する (`orchestrator/verifier/commit_receipt.py:223-237`)。この列を WAL verify 列と完全一致させれば、helper 内の個別 `verdict`/`certified` 検査は含意される。また receipt evidence は非空必須 (`:223-225`) なので「verify 1 件以上」も完全一致から含意される / 成果物影響: 個別検査を外す変異が別検査で赤のままとなり、変異結果を gate の実効性と誤認する。

- A-05 / 判定 refuted / scope 内 / backoff の現在の拒否は、全 committed state の verify 存在と `certified=True` (`orchestrator/campaign/backoff_requested_us.py:567-576`)、adaptive receipt の operation/variant/id (`:607-622`) である。topology は COMMIT と build attempt を既に束縛する (`orchestrator/campaign/wal.py:1488-1518`)。計画どおり共通 helper を先に全 COMMIT へ適用すれば、これらは同等以上の層で拒否される。S6/S8A の現行 stage map は `commit is not None` とするだけで拒否を持たない (`orchestrator/campaign/s6_sort_sweep.py:443-468`, `orchestrator/campaign/s8a_trigger_sweep.py:545-570`) / 成果物影響: 手順 4、7 自体による受理集合の拡大はない。

- A-06 / 判定 refuted / scope 内 / live anomaly は verify record 発行直後に `vr.certified` 偽を abort へ落とす (`orchestrator/campaign/pipeline.py:1319-1333`)。既存 topology、環境契約、source binding は新 helper より前に走る (`orchestrator/campaign/artifact_admission.py:1042-1097`)。epoch gate も view 発行前に残る (`:1147-1172`) / 成果物影響: 計画された配置を守る限り、絶対規律 2、epoch、環境、source binding の既存拒否は弱まらない。

- A-07 / 判定 refuted / scope 内 / 共通 22 site の `ArtifactAdmissionError` は通常伝播し、Layer3 は hard error へ変換する (`orchestrator/campaign/layer3_report.py:684-694`)、autonomous completeness も失敗へ変換する (`orchestrator/campaign/autonomous_trial_completeness.py:4422-4430,4959-4967`)。backoff の `RuntimeError` は `measure()` の binding load から伝播する (`orchestrator/campaign/backoff_requested_us.py:947-968`)。S1 issue は sample を作らず (`orchestrator/campaign/s1_report.py:473-480`)、certified gate を fail にする (`:897-909`)。S8B の issue は `protocol_violation` (`orchestrator/campaign/s8b_oracle_report.py:1609-1627`) となり judge が拒否する (`orchestrator/campaign/s8b_oracle_judge.py:244-254`) / 成果物影響: 4 種の例外変換が無害な診断へ格下げされる consumer は確認できない。

- A-08 / 判定 real / scope 内 / 親 brief は certified consumer を full admission 呼び出しと定義して「22 site 全て chokepoint」と結論するが、backoff (`orchestrator/campaign/backoff_requested_us.py:444-501`)、S1 (`orchestrator/campaign/s1_report.py:382-424`)、S8B (`orchestrator/campaign/s8b_oracle_report.py:547-590`) は lock-only/raw-WAL 経路である / 成果物影響: 正しい閉包は 16 module/22 full-admission site と 3 lock-only site、合計 19 module/25 literal purpose site。

- A-09 / 判定 real / scope 内 / tracked corpus の v1 事実は限定的である。テストは repo の全 32 lockを v1 と固定するが、うち `output/campaigns` は 30、残り 2 は insight evidence である (`orchestrator/tests/test_artifact_admission.py:793-813,840-858`)。一方、新規 certified lock の通常生成は v2 (`orchestrator/campaign/ident.py:546-561`)。外部 B10 campaign は repo 外 root を正式入力にする (`orchestrator/tests/test_b10_extended_figure_provenance.py:21-24,87-111`)。また実 artifact を E1 fixture へ昇格して certified consumer に渡す test がある (`orchestrator/tests/test_bench_first_real_wal.py:244-305`) / 成果物影響: 「repo 内の現存 30 campaign は既に E0 で拒否される」までは正しいが、「既存保存成果物の consumer を壊さない」への一般化は成立しない。

- A-10 / 判定 real / scope 内 / S6/S8A は `_load_certified_rows()` で中央 admission を通してから row を作る (`orchestrator/campaign/s6_sort_sweep.py:472-482`, `orchestrator/campaign/s8a_trigger_sweep.py:574-584`)。中央で全 COMMIT を検査する計画なら、row helper 失敗を起こす view は発行されない / 成果物影響: 行単位 helper とその変異は恒真な二重 gate になり、余分な source 編集と偽の mutation score を生む。

## 過剰と判断した述語

削るべきもの:

- `commits > 0`、`aborts >= 0`。現行 producer の正常性条件ではあるが、D1246 の receipt/WAL verdict 対応づけには不要。維持するなら「persisted verify payload schema を固定する」という別裁定が必要。
- `commit_witness` exact 2 key、`commit_counts == commits`、`batch_commit_counts == 0`。live producer の trace 完全性 gate は維持する (`orchestrator/campaign/pipeline.py:1251-1297`) が、persisted common helper へ複製しない。
- `workload` の exact key 集合。必要なのは receipt evidence と照合する非空 `tag` だけであり、将来の補助 metadata を拒否すべきでない。
- `verify_configs == 順序保持 deduplicate(tags)`。receipt validator は COMMIT terminal payload の bytes を既に束縛する (`orchestrator/verifier/commit_receipt.py:208-219`)。S1 固有の必須 config 判定は既存 consumer に残る (`orchestrator/campaign/s1_report.py:325-341`)。

残すべきもの:

- 同一 variant、同一 attempt、COMMIT より前の verify 列の選択。
- `anomalies` の exact int 0。receipt evidence に anomalies が無いため、絶対規律 2 のため独立に必要。
- durable receipt validator 全体。
- receipt operation と COMMIT attempt の一致。
- receipt evidence と WAL の `(workload_tag, verdict, certified)` 列の完全一致。

`batch_commit_counts == 0` は現在の live gate としては正しいが、共通 persisted helper では削るべきである。将来 batch trace が certify 可能になった際は producer/verifier 側の裁定だけで移行でき、T-2061 が将来 schema を先回りして固定しない形になる。

## 恒真の疑いがある述語

- COMMIT `build_attempt_id` の非空 exact str: full admission と backoff では topology が既に保証する (`orchestrator/campaign/wal.py:1488-1497`)。さらに receipt operation は validator により非空 str (`orchestrator/verifier/commit_receipt.py:208-219`) で、COMMIT attempt との一致を残すなら個別検査を外しても拒否される。単独変異で受理される入力を示せない。
- `verdict == "serializable"` と `certified is True`: validated receipt evidence と列完全一致が残る限り恒真。単独で外しても `certified=False` 入力は receipt validator/equality で拒否される。
- verify 1 件以上: receipt evidence が非空必須で列完全一致するため恒真。明示件数検査を外して受理される入力を示せない。
- `workload.tag` の非空性: receipt evidence 側の非空 tag と完全一致させるなら含意される。workload object の余分な key を拒否する部分だけが実発火するが、それは過剰。
- S6/S8A の行単位 helper: 中央 chokepoint 後の view では失敗入力が到達せず恒真。

一方、`anomalies=1`、`commits=0`、`aborts=-1`、witness count 不一致、batch=1、workload extra key、verify_configs 不一致は、各検査を外せば他を満たす persisted record を構成できる。ただし後五者は「実効だが D1246 の scope を越える」述語である。

## 変異事前登録の再照準案

1. `certified is True` 除去: 無効。receipt validatorと列一致が同じ入力を拒否する。個別変異を削除し、receipt/WAL evidence 列比較そのものの変異へ統合する。
2. `anomalies == 0` 除去: 有効。receipt、verdict、certified は正常のまま WAL `anomalies=1` のみとする。
3. attempt 一致除去: 現案の単純な ID 改変は topology で先に赤になる。attempt A が正常 verify 後 ABORT、attempt B が verify 無しで self-consistent receipt付き COMMIT、という topology-valid 2 attempt 入力へ変更する。
4. durable validator 呼び出し除去: 有効。operation/evidence は一致したまま terminal payload のみ receipt と不一致にする。
5. receipt operation 一致除去: self-consistent な「別 operation」の receipt が必要。`campaign_receipt()` は operation を独立指定できる (`orchestrator/tests/commit_receipt_support.py:47-68`) ため、receipt IDまで正しく再発行して COMMIT attempt だけを違わせる。
6. evidence 列比較除去: 単純 workload 改変では `verify_configs` も赤になる。WAL tag と COMMIT `verify_configs` を同時に `s2` へ揃え、terminal hashも再発行する一方、receipt evidence は `legacy` のままにする。
7. 先頭 COMMIT だけ検査: topology-valid な別 variant/attempt の第2 COMMITにだけ terminal mismatch receiptを置く。他 gate の赤理由を混ぜない。
8. S6/S8A 行 helper 除去: 無効。中央 helperが先に拒否する。S6/S8A変異は削除し、3 bypassそれぞれの helper 結線除去変異へ置換する。

承認外の過剰拒否を検出する正例変異は現案にない。少なくとも次を追加する:

- red verify後にABORTした attemptと、正常COMMIT attemptが同居する campaignを通す。mutantは「全 verify を正常必須」に広げる。
- COMMIT無し campaignを通す。mutantは「campaignにCOMMIT必須」とする。
- `HISTORICAL_RAW` は不完全receiptでも従来どおり読める。mutantはhelperを両 purposeへ適用する。
- 同一 tag の複数 repetitionを通す。mutantはverify tagを一意必須にする。
- 補助述語を残す場合は `aborts > 0` の正常例を置き、`aborts == 0` への過剰強化を殺す。

## 親 brief の誤り

- `brief.md:34-66` の「19 module / 22 site」と「22 site 全て chokepoint」は、3 lock-only siteを表へ含めながら集計から落としている。正しくは 19 module/25 site。
- `(P2)` の「S6/S8Aは行単位 helper がないと1 variant anomaly campaignを通す」は、中央で全 COMMIT を検査する段 2 設計では偽。
- 「repo 内30 campaignがv1」の正確な範囲は tracked `output/campaigns` だけ。repo 全体では evidence lockを含め32 v1であり、repo 外 official campaign、通常生成される v2、実 artifact をE1へ昇格する testには一般化できない。
- なお親 brief 自体の `brief.md:99-100` は実測を段 2 に要求しているだけで、「30件だから全 consumer 非破壊」という実測結論は本文にはない。その結論を親 brief の確定事実として扱うのも誤り。

## 段 2 プランの誤り

- S1/S8B の同一 snapshot 契約が実装手順にない。epoch、lock SHA、WAL readを一つの安定化手順へまとめ、前後 lock SHA一致を最低限要求すべき。
- D1246 を persisted verify payload 全体の schema validatorへ拡張している。auxiliary counter、witness、workload exact key、verify_configsは削るべき。
- S6/S8A の行単位 helperとstage map改変は中央全COMMIT gate後には冗長。CertifiedCampaignViewを信頼境界とし、行側はCOMMIT recordの有無だけを射影すべき。
- 変異 1、3、6、8 は別 gateと赤理由が競合する。上記の再照準が必要。
- 負例除去変異だけで、受理集合を承認以上に縮める実装を殺す正例変異が登録されていない。