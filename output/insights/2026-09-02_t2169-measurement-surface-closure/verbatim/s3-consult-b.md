## P2 の検証

判定は「bench-first 自体は D58 どおりだが、D58 全体が repo-wide に閉じているとは言えない」です。

- screening 時だけ bench が先行します（`orchestrator/campaign/pipeline.py:1553-1565`）。screen-reject は verify 前に ABORT します（同 `:1576-1591`）。

- 生存候補は legacy と追加構成をすべて反復し（同 `:1593-1633`）、完了後にだけ `certified=True` になります（同 `:1634`）。COMMIT は certified、非 ABORT、必要な bench 結果を要求します（同 `:1714-1726`）。

- COMMIT receipt は verifier 発行 capability を要求し、serializable/certified と operation、variant、workload の一致を検査します（`orchestrator/verifier/core.py:224-259`、`orchestrator/verifier/commit_receipt.py:296-340`）。WAL writer も live receipt を再検証します（`orchestrator/campaign/wal.py:692-717`）。

- persisted consumer は同一 attempt の先行 `verify_done`、serializable、certified、anomaly 0、receiptとの一致を再検証します（`orchestrator/campaign/artifact_admission.py:686-770`）。

したがって「certified / COMMIT 候補は全 verify 構成を通す」は成立しています。

成果物影響: この経路では screen-reject の値が certified fitness、COMMIT 受理集合、certified report の順位を変えることはありません。

未認証値の除外も主要経路では成立します。critic loader は BUILD_START と screen ABORT の identity/reason しか読みません（`orchestrator/critic/digest.py:834-854`）。s6 と s8a のレポートは COMMIT がない候補の bench payload を空にします（`orchestrator/campaign/s6_sort_sweep.py:541-557`、`orchestrator/campaign/s8a_trigger_sweep.py:643-659`）。S1 freeze は lock に screening key がある campaign 全体を除外します（`orchestrator/campaign/s1_known_axes_freeze.py:255-275`）。

ただし2点、repo-wide の保証にはなっていません。

- `layer3_report.build_report()` は `HISTORICAL_RAW` view の全 `bench_done` を `runs` へ射影し（`orchestrator/campaign/layer3_report.py:541-552`、同 `:627-657`）、screen-reject を除外しません。`certifying_input=False` なので現行の certified sink ではありません（同 `:672-674`）。D58 の「探索射影にも混ぜない」を逐語どおり読むと境界逸脱です。

  成果物影響: certified 値、順位、受理集合は変わらず、historical Layer3 report の `runs` に未認証値が現れるだけなので、本依頼の分類では nit です。

- screening の適用範囲は機械的に「偵察/8b」に限定されていません。`verify_screening_preimage()` が検査するのは lock 内の同一方針だけです（`orchestrator/campaign/ident.py:160-193`）。`prepare_screening_campaign()` は任意の `base_cfg` に screening を追加でき（`orchestrator/campaign/screening_driver.py:365-418`）、pipeline も preimage 一致しか要求しません（`orchestrator/campaign/pipeline.py:1005-1010`）。

  成果物影響: sanctioned scope 外の caller が screening を使うと、verify 前 reject により COMMIT へ進む受理集合が変わります。これは D58 の適用範囲がコードで閉じていない実在欠陥です。

## P3 の検証

P3 の狭い命題、「`measure_point_floor()` を直接 import できることだけでは欠陥でない」は正しいです。関数は admission を呼ばず、測定 dict を返すだけです（`orchestrator/campaign/between_run_floor.py:202-252`）。

ただし Layer B は閉じていません。

- `_write_out()` は caller 供給の結果を canonical calibration 名で書きます（同 `:255-315`）。先頭 underscore はアクセス制御ではありません。

- consumer は `between_run_noise_*.json` を glob し、任意 schemaを一部許容した上で workload、genome由来 protocol、`0<cv<1` だけを検査します（`orchestrator/campaign/screening_driver.py:305-349`）。生成時の protocol admission、source pin、artifact SHA は要求しません。

- 読んだ値は `ScreeningConfig.floor` へ入り（同 `:407-447`）、`baseline_tps * (1-k*floor)` の棄却閾値になります（`orchestrator/campaign/pipeline.py:1573-1591`）。

したがって「直接呼べること自体」は非欠陥ですが、直接測定した値を `_write_out()` へ渡した場合に D1373 の CLI admission を経たことを consumer が区別できません。P3 を P5 の閉包根拠には使えません。

成果物影響: 読み込まれる floor が変わると screen-reject 判定が反転し、verifyとCOMMITへ進む候補集合が変わります。

## P4 の検証

floor CLI が verifier を呼ばないこと自体は欠陥ではありません。

CLI は protocol source の text-level trace hook 証拠を先に要求し（`orchestrator/campaign/between_run_floor.py:351-366`）、その後に `trace=False` build を測ります（同 `:371-403`）。D1373 が明記したとおり、この predicate 自身も verifier 成功を証明しません（同 `:111-121`）。

ただし「noise 較正であって性能主張でない」は限定が必要です。

- floor は candidate throughput の性能主張ではありませんが、screening の比較閾値として実際に受理集合を変えます（`orchestrator/campaign/screening_driver.py:410-447`、`orchestrator/campaign/pipeline.py:1573-1591`）。

- `screening_driver.py:311` の glob は `between_run_noise_*.json` のみを読みます。`pegasus_floor_scoping.py` の出力は `scoping_between_run_*.json` なので、この consumer には名称で到達しません（`orchestrator/campaign/pegasus_floor_scoping.py:195-200`）。止めているのは `eligible_for_compare` ではなく filename と出力経路です。

- B10 文書の4 SHAは現物 bytes と一致しました（`docs/b10-backoff-shape-preregistration.md:206-217`）。しかし SHA 表は machine spec 外です。parser は machine block を読み（`orchestrator/campaign/b10_backoff_shape_sweep.py:816-833`）、floor artifact を再読せず固定の参考値だけを検査します（同 `:1196-1231`）。

- B10 の judge は `reference_widths` を判定に使わず、paired effectとHolmを計算します（同 `:1733-1789`）。参考幅は provenance/report にだけ複写され（同 `:2624-2635`、`:2705-2710`）、レポートも `official certification: false` です（同 `:2647-2656`）。

成果物影響: B10 の SHA表や参考幅は正式 verdict、順位、受理集合を変えません。screening floor のほうは候補受理集合を変えるため、P4 を「純粋に記述的」と説明するのは誤りです。

## P5 の検証

P5 は棄却すべきです。「D1360、D58、certified writer authorization の3層で全経路が塞がる」はコードの事実ではありません。

決定的な反例は `s8c_result_judge` です。

- `judge()` は raw throughput を直接受理します（`orchestrator/campaign/s8c_result_judge.py:472-492`、`:1959-2028`）。

- correctness は caller 供給の boolean/string です（同 `:452-459`）。

- attestation は raw values の自己計算 SHAと、任意の非空 issuer 名しか要求しません（同 `:495-529`）。外部 trust root を照会するコードはありません。

- `source_binding` も caller が `_ContrastParams` と manifest の両側へ同じ文字列を置けば一致します（同 `:129-144`、`:293-315`、`:1626-1628`）。exact private 型は module attribute として構築可能で、既存テストも直接構築しています（`orchestrator/tests/test_s8c_result_judge.py:99-104`）。

- その値から順位が導出されます（`orchestrator/campaign/s8c_result_judge.py:1607-1623`）。`publish_result_table()` は `official_conclusion`、`official_status`、`selection_evaluation` を書きます（同 `:2316-2358`、`:2413-2438`）。

- publication が要求する ratified floor receipt は実在する provenance検査ですが（同 `:2124-2180`、`:2191-2238`）、observation correctness や throughput とは束縛されていません。

実際、テスト fixture は `correctness_gate_passed=True`、自己計算 hash、`issuer="test-gate-issuer"` だけで accepted observation を作り（`orchestrator/tests/test_s8c_result_judge.py:156-193`）、official/selection table を生成しています（同 `:1749-1773`）。これは保証の positive control ではなく、自己申告入力が通る witness です。

成果物影響: caller が throughput を変えるだけで `within_config_rank`、`official_status`、`official_conclusion`、`selection_evaluation` が変わります。これは certified report・順位へ直接影響する実在欠陥です。

一方、pipeline COMMIT 経路そのものは前述の verifier capability とreceiptで閉じています。したがって結論は「pipeline WAL は閉じているが、repo全体は閉じていない」です。

## 見かけの gate

- `ELIGIBLE_FOR_COMPARE=False` は payloadへ書かれるだけです（`orchestrator/campaign/pegasus_floor_scoping.py:41-43`、`:187-194`）。production consumer はなく、test が値を確認するだけです（`orchestrator/tests/test_pegasus_floor_scoping.py:165-180`）。specific scoping出力を止めている実体は外部出力要求（`orchestrator/campaign/pegasus_floor_scoping.py:107-127`）と filename 不一致です。

  成果物影響: flag を反転しても certified 値、順位、受理集合は変わらないため nit です。

- `s8c_result_judge` の correctness boolean、非空 issuer、自己 hash、opaqueだがcaller生成可能な `source_binding` は、すべて見かけの gate です（`orchestrator/campaign/s8c_result_judge.py:452-529`、`:1626-1628`）。

  成果物影響: これらを満たすだけで caller 値が official conclusion と順位へ到達するため、nitではありません。

- 同型の「書くだけの不適格 marker」は `paper_gain_eligible=False`（`orchestrator/campaign/backoff_extended_sweep_report.py:37-49`）、`headline_eligible=False`（`orchestrator/campaign/backoff_profile.py:1127-1154`）、`fitness_eligible=False`（`orchestrator/campaign/t152_write_intent_coverage.py:773-795`）にもあります。repo静的検索ではproduction側の拒否判断に使う読者を確認できませんでした。

  成果物影響: marker 自体は値、順位、受理集合を変えないため nit です。これらの成果物が安全だという結論は、markerではなく個別consumerの admissionから立証する必要があります。

## certified writer 境界の署名

`require_certified_writer_authorization(a, env_tag=e, clocks_per_us=c, numactl=n, env_contract=b)` の実質的な署名は次です。

`G(a,e,c,n,b) -> registered_contract` となるのは、以下がすべて真のときです。

- `a` が exact `AuthorizedContract` で、current PID、process seal、process-local cache identityに一致する（`orchestrator/campaign/execution_guard.py:44-69`）。

- activation serial/hash、active contract、generation registry、contract object identityが一致する（同 `:70-104`）。

- `e`、`c`、`tuple(n)` が登録 contract と完全一致する（同 `:120-135`）。

- Pegasus computeでは active state中の `attestation_mode=required` contract が一意で、それが対象 contractである（同 `:136-159`）。

- `b` が指定された場合は exact contract型で登録 contract と等しい（同 `:160-169`）。

拒否するものは、偽造/別process/stale authorization、未登録env、runtime値不一致、Pegasus required contractの非一意、build selector不一致です。

通すものは、公開 `env_contract.authorize(env_tag)` が発行した current processのreceiptと一致するruntime値です（`orchestrator/campaign/env_contract.py:846-878`）。

重要なのは、この関数が correctness、verifier verdict、genome、source、binary、throughput、WALを一切検査しないことです。pipelineでも build前の `:1030-1036` で呼ばれ、buildは `:1197-1263`、verifierは `:1472-1516` です。

したがって起票元の「official commit writer は certified 判定後に閉じている」は、この関数については誤りです。正しい署名は「certified writer用の実行環境 authorization」です。correctness closure は後段の全verify完了（`orchestrator/campaign/pipeline.py:1593-1634`）、COMMIT前条件（同 `:1714-1726`）、receipt付きWAL append（同 `:1756-1772`）の合成です。

成果物影響: この authorization 単体を correctness gate と誤認すると、s8cのような別sinkを見落とし、未認証値によるofficial conclusionと順位変更を許します。

## 不在証明の質

caller 0、private名、`__all__` 非掲載は到達不能の証明になりません。

- `s8c_result_judge` は production callerが見つからなくても、`judge` と `publish_result_table` を明示公開しています（`orchestrator/campaign/s8c_result_judge.py:33`）。必要なprivate型も通常import後に構築できます（同 `:129-186`）。

- certified-writer inventory test は固定caller集合を検査しています（`orchestrator/tests/test_campaign.py:5328-5354`）。同テスト自身も `getattr`、`partial`、container経由を unresolved と分類しています（同 `:4888-4962`）。これは既知sourceのdrift検査であり、sinkの到達不能証明ではありません。

十分な不在証明は、caller列挙ではなく、sink側で受理可能な値の署名を示し、その値が verifier成功点でしか発行できないこと、測定値、source/build identity、terminal payloadへ束縛されることを確認することです。pipeline COMMITではそれが capabilityとreceiptで確認できます（`orchestrator/verifier/core.py:162-217`、`orchestrator/verifier/commit_receipt.py:296-340`）。s8c observationでは確認できません。

対照的に、現行 Layer3 accepted report は「callerがいない」より強く閉じています。builderは `certifying=True` receiptを要求しますが（`orchestrator/campaign/layer3_report.py:682-702`）、receipt parserは accepted bytesの `certifying` を必ずFalseに固定します（`orchestrator/campaign/s8c_acceptance_receipt.py:420-423`、`:561-576`）。この矛盾は静的に到達不能を示します。

## 判定の限界

- pytest、build、benchmark、測定は実行していません。テスト成功については根拠なしです。

- 静的読解は runtime monkeypatch、dynamic import、`eval`、checkout外のpublisherやissuerを閉じません。動的参照がAST inventoryで unresolvedになる例は `orchestrator/tests/test_campaign.py:4888-4962` にあります。

- s8c outputはrepository外のabsolute pathを要求します（`orchestrator/campaign/s8c_result_judge.py:2284-2313`）。checkout外でその表がさらにどう配布・承認されるかは証明できません。

- 文書の4 SHAと現物bytesの一致は確認しましたが、そのbytesが正しい測定から生成されたこと、当時verifierを通ったことは証明しません。artifact自身には性能値とrun commandしかありません（例: `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json:1-55`）。

- 人手転記、filesystem権限、symlink/TOCTOU、実行中の差替えは本調査では未検査です。単一 file:line の根拠なしです。

- 本回答はレンズBのsink境界調査であり、全producer件数の閉包一覧ではありません。全経路の件数については根拠なしです。

## 総括

- P2: bench-firstとpipeline COMMITの正しさ境界は成立。ただしscreening適用範囲はgeneric APIで閉じず、historical Layer3には未認証bench値が出ます。

- P3: 「直接呼べるだけでは欠陥でない」は正しいものの、直接生成値からcanonical floor artifact、screening閾値までの経路は閉じていません。

- P4: floor CLIがverifierを呼ばないこと自体は非欠陥。ただしfloorは純粋な記述値ではなくscreening受理集合を変えます。B10のSHA表は文書上の出典で、実行時gateではありません。

- P5: 棄却。`s8c_result_judge` はcaller自己申告のcorrectness、issuer、hashからofficial conclusionと順位を生成できるため、repo全体はclosedではありません。

最重要の実在欠陥は、`s8c_result_judge` のobservation correctness attestationが権威へ束縛されていない点です。次点はD58の適用scopeがgeneric screening APIで強制されていない点です。