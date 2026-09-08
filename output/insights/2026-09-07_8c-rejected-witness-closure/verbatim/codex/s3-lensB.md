## must-fix

1. **「不整合を閉じる」は過大で、「WAL 側の不整合を閉じる」が正確。**  
   [s1-brief.md:1](/home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s1-brief.md:1)、同 `:5` は全体を閉じる表現だが、`OriginProducerInputs.result_record_bytes` は外部注入のまま ([p3_autonomous_workload_trial.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/p3_autonomous_workload_trial.py:429)、同 `:1653-1665`) で、構築は [test_p3_autonomous_workload_trial.py:10624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_p3_autonomous_workload_trial.py:10624) の 1 件だけ。plan 自身も [s2-plan.md:315](/home/SFC/tanab/.claude/jobs/96047219/wave/artifacts/dev-wave-rejected-witness-closure/s2-plan.md:315) で認めている。  
   放置すると、成果物の受理集合を「production rejected projection が到達可能」と過大記録する。実装後に通るのは、外部 producer が同じ正規化で `physical_result.constraint_sha256` を作った場合の FC07 だけである。

2. **「受理集合を狭める」は誤り。変更は非単調な schema migration。**  
   [s1-brief.md:49](/home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s1-brief.md:49) は narrowing とするが、現在通る旧 3-field fixture ([reflux_origin_fixture_builder.py:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/reflux_origin_fixture_builder.py:381)) は変更後 FC07 へ移り、現在 FC07 の production `verify` 形状 ([pipeline.py:1601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/pipeline.py:1601)) は、整合する record があれば P6 まで進む。  
   放置すると、formal consumer の受理集合差分を誤って一方向と記録する。certified 選択は不変だが、FC07 の入力受理集合は「旧形を除外し、新形を追加」である。

3. **既存到達例では report の reason は変わらない。**  
   [s1-brief.md:57](/home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s1-brief.md:57) は reason が変わるとするが、repo 内唯一の入力構築は現在の fixture でも既に `P6Unavailable` へ到達し、変更後も同じ reason になる。変わるのは fixture record/source-closure の digest、それに連鎖する receipt と `formal_receipt_sha256` / `evidence_root_sha256` ([reflux_formal_consumer.py:953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:953)、同 `:1057-1082`)。projection は report ([p3_autonomous_workload_trial.py:3618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/p3_autonomous_workload_trial.py:3618))、lifecycle (`:4955-4960`)、acceptance receipt ([trial_registry.py:6295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/trial_registry.py:6295)) へ伝播する。  
   ledger event は両結果とも同じ `OriginSealed(aborted=True, constraint_class_sha256s=())` ([reflux_origin_client.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_origin_client.py:195)、同 `:259-275`)。この区別を落とすと report/reference の実差と ledger 不変性を取り違える。

判定順は、FC09 class exact (`reflux_formal_consumer.py:1031`) → FC04 → FC05B/FC03/FC05C → FC06 → verifier policy → FC07 (`:1040`) → aggregate FC09 (`:1043`) → FC10 (`:1048`) → P6 (`:1071`) である。**FC08 は enum 自体に存在しない** (`:100-113`)。整合する外部 record があれば FC07 の次は aggregate、FC10、P6。record が同じ digest 規則で作られなければ FC07 の witness一致で止まる。

## 4 語の独立走査

全 repo、`.git` と保護された `output/s8b-freeze` を除く走査結果は次のとおり。

- `witness_class_sha256s`: 33 hit、21 file。live な旧-field前提は `reflux_formal_consumer.py:874`、`reflux_origin_fixture_builder.py:385`、`test_reflux_formal_consumer.py:927,951`。同 test `:850` は意図的な legacy 負例なので残してよい。変更後の helper/local 名に同語が残っても旧 WAL field 前提ではない。
- `candidate_attributable`: 33 hit、19 file。旧-field前提は `reflux_formal_consumer.py:871`、fixture `:383`、legacy 負例 `test_reflux_formal_consumer.py:848`。`reflux_source_closure.py:370,381` と `test_reflux_source_closure.py:305` は verifier-policy の別 field `candidate_attributable_rejected` であり、取り残しではない。
- `truncated`: 1,372 hit、389 file。FC07 の旧 field に該当する live hit は consumer `:872`、fixture `:384`、legacy 負例 test `:849` の 3 箇所だけ。残りは WAL tail、診断切詰め、sort oracle、履歴ログなど別意味か歴史資料である。
- `wal.abort.payload.witnesses`: 10 hit、9 file。live な変更対象は `reflux_source_closure.py:86` と fixture builder `:312` の 2 件だけ。残りは `docs/decisions.md:52220`、`docs/worklog.md:1146`、現在の brief、T2353 の README・s1・s2・s3Bという履歴記録である。

`output/insights` の関連 hit は T941、T2257、T2293、T2353 と本 wave の brief に集中する。いずれも当時の旧形状または検出経緯を凍結した資料で、live consumer の旧名前前提ではない。plan の移行後に残る旧形の実行可能箇所は、意図的な legacy 負例だけである。

## pin 閉包の 4 通りの再走査

1. **64桁 hex literal:** `orchestrator/tests` の `.py + .json` では 799 matching lines、1,034 literal occurrences。影響対象 hash に一致した実行可能 pin は `reflux_origin_fixture_baseline.json` の 5 entry と `test_reflux_result_evidence.py:24-27` の 4 literalだけ。第三の file は無い。
2. **長さ literal:** baseline の `962 / 975 / 14909 / 1848 / 1697` と、`test_reflux_result_evidence.py:150` の `1848` が該当する。後者は同じ第 2 pin file 内で、record 内の変更値がすべて64桁 digestなので長さは不変。第三の pin ではない。
3. **生成関数全 caller:** builder の直接 caller は10 test file、間接 callerは `test_reflux_originless_compatibility.py:13,126-140` の1 file。後者は generation-two viewだけを比較する (`:659-683`) ため、terminal receipt digestの追加 literal pinはない。
4. **`orchestrator/tests` 外:** builder symbolと影響対象 hashの実行可能 hitは0件。見つかるのは T2353 の凍結 insight/logだけで、受入を拘束しない。

連鎖は正しく5 entryへ届く。`_RUNTIME_FIELD_PATHS` は [reflux_source_closure.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_source_closure.py:74) で定義され、成果物と `:224-237` で exact 比較される。fixture の文字列 `:310-313` を変えると source-closure raw/digestが変わり、`build_result_evidence_record` `:434`、`build_recovery_envelope_inputs` `:514`、`build_launch_admission_inputs` `:553` へ伝播する。別枝で ordered WAL `:391-405` も変わる。したがって plan の baseline 5 entryと golden 4 literalは閉じており、第三の operational pin は無い。

## 焦点走 file 集合の差分

参照関係から得た集合は plan `s2-plan.md:273-287` の12 fileと**完全一致し、差分0**。

- production module直接参照は7 file。
- fixture builder直接参照は10 file。
- 和集合は11 file。
- P3 test helper経由の `test_reflux_originless_compatibility.py` を加えて12 file。

`test_p3_build_authority_cli.py:114` に P3 test file名の文字列があるが、low-level issuer allowlistであり変更 module/fixture出力の consumerではない。新規 test fileの追加は計画されておらず、file集合メタテスト更新は該当しない。

## 親 brief への指摘

アンカー表の件数は独立走査でも次のとおりで、件数訂正はない。

- WAL commit の `verify_configs` writerは `pipeline.py:1821,1836` の2箇所。`paper_story_a1_paired.py:5154` に同名 report fieldがあるが、`wal.commit.payload` writerではない。
- abort terminal の `candidate_attributable`、`truncated`、`witness_class_sha256s` producerは各0件。`witnesses` producerも0件。
- `OriginProducerInputs(...)` の構築は `test_p3_autonomous_workload_trial.py:10624` の1件だけ。
- abort payloadの `verify` は `pipeline.py:1601-1604` で `trace_dir` を除去し、残る key集合は brief と一致する。
- verifier-policy実 fileは無く、schema値の実体は fixtureとtestだけ。

誤りは件数ではなく、brief `:49-52` の「受理集合を狭める」と `:57-58` の「report reason が変わる」、およびタイトルの full closure 表現である。

## scope 外だが real

- **result-evidence producerと共有 constraint-class導出:** production WAL側は修理されるが、同じ正規化で `physical_result.constraint_sha256` を発行する record producerが無い。端から端まで閉じるには必要だが、明示 scope 外なので裁定パッケージ候補。
- **DW-G05上の位置付け:** certified 選択、材料レポート、ledger eventは変わらない。production artifact pathも無いため、実差を示せるのは formal-consumer入力の受理集合とfixture由来のreceipt/reference hashだけである。これを成果物影響と認めない場合は `docs/dev-wave/core.md:77-81` により nit/backlog。明示 overrideとして進めるかは裁定事項。
- terminal outer key集合・型・重複・root shadow未閉包はD1715どおりrealだが、本変更が新設した穴ではなくscope外。

## refuted

- **第三の pin がある疑い:** 4経路すべてで否定。実行可能 pin fileは既知の2件だけ。
- **baseline 5 entryが不足する疑い:** 依存グラフ上、5 entryでexact。authority manifestとexecution provenanceは不変。
- **焦点走に consumer test漏れがある疑い:** 直接・間接参照の和集合がplanと一致。
- **アンカー表の producer件数誤り:** `verify_configs` 2 writer、旧abort field各0、`OriginProducerInputs`構築1を確認。
- **変更後も fixtureがFC07で止まる疑い:** planned fixtureが正規形digestを実物から導出する限り、FC07後はaggregate、FC10を通ってP6へ進む。

## 総括

実装は WAL consumer側の名前不整合を閉じ、pin閉包と焦点走集合も漏れていない。  
ただし production result-record producer不在のため、端から端までの本番閉包とは書けない。  
受理集合は narrowingではなく旧形除外・新形追加の非単調変更である。  
certified選択とledger値は不変で、実差はfixture hashとreceipt/report参照に限られる。