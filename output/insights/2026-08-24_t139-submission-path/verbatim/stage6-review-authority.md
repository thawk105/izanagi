## 所見

1. **F1 — real / blocker**

   - 場所: [_binding.py:56](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_binding.py:56)、[_manifest.py:402](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:402)、[_semantic_validator.py:594](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_semantic_validator.py:594)
   - 具体的失敗: `_record_from_refs` は `approval_manifest=approved.approval_ref` を設定しており、これは新manifestではなくD282 `docs/decisions.md` BlobRefである。`_require_manifest_matches_approval`も同じD282 refを要求する。semantic validatorはreceiptの8-key preregistrationをこのrecordへ完全一致させ、D282 blobを再検査する。そのため、publishされたreceiptからD574 manifest、projection、index-v2 authorityを復元できない。逆に正しい新manifest BlobRefを記録したreceiptは拒否される。
   - 推奨fix: D574 viewでは`record.approval_manifest=approved.manifest_ref`とし、照合側も`approved.manifest_ref`を要求する。旧fixtureの期待を変えず、new fieldsを持たないlegacy D282 authorityだけ`approval_ref`へfallbackさせる。
   - DW-G05成果物影響: 正例publishが成功しても成果物はD574 authorityを記録していない。DW-G05のprivate receiptをcanonicalなD574承認済み成果物とは扱えない。

2. **F2 — real / blocker**

   - 場所: [approval_payload.py:224](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/preregistration/approval_payload.py:224)、[_manifest.py:243](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:243)、[_manifest.py:267](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:267)
   - 具体的失敗: `_load_approved_manifest_from_refs`はcaller指定のmanifest/projection refsからsealed `ApprovedManifest`を発行する。両projectionにD282 predecessorとD574 literalをコピーし、同じ任意index BlobRefを入れれば、固定source refsを使わずに`_require_vector_index`を通過できる。HEAD単独やmanifest単独はauthorityにならないが、callerが選んだ協調済み二blobはauthorityになれる。stage5の「caller指定digestはauthorityになりません」は成立しない。
   - 推奨fix: sealed objectをmintする経路では、refsが`T139_APPROVAL_MANIFEST_REF`と`T139_VECTOR_APPROVAL_REF`にexact一致することを必須化する。変異検査用のexplicit-ref parserは残せるが、非固定refsからcapabilityを返してはならない。
   - DW-G05成果物影響: 任意vector indexを承認済みとしてprivate receiptをpublishでき、DW-G05 gateの唯一authorityという主張が崩れる。

3. **F3 — real / blocker**

   - 場所: [_manifest.py:34](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:34)、[_manifest.py:227](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:227)、[_manifest.py:315](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:315)、[test_t338_submission_gate_unit1.py:147](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit1.py:147)
   - 具体的失敗: seal判定はexact typeとimport可能なmodule tokenだけである。fixture自身が`object.__new__`、token、`object.__setattr__`でsealed objectを偽造しており、これは実装保証を恒真化している。さらに`_assert_approved_manifest_intact`はD282 payloadから`target_core`、`approved_blobs`、`composed_sha256`を再構築して比較しない。攻撃者は固定D282/D574 refsと正しいindexを残したまま、任意core/blob集合を持つobjectを作り、自己整合するrecordとbindingを発行できる。
   - 推奨fix: new authority fieldsがあるobjectは、固定D282 payloadと固定D574 refsからcanonical viewを再構築し、全fieldをexact比較する。legacy missing-field branchは残してよいがwriterで必ず拒否する。subclassは現状どおりexact typeで拒否する。
   - DW-G05成果物影響: 未承認coreやartifactを承認済みとするreceiptがpublish可能であり、成果物のpreregistration trust chain全体が無効になる。

4. **F4 — real / must-fix**

   - 場所: [_writer.py:71](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:71)、[_writer.py:79](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:79)、[_writer.py:80](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:80)
   - 具体的失敗: binding発行時、semantic前、semantic後のauthority/root再検査はある。しかしsemanticが読んだcompile commands、CMakeCache、logsなどのraw bytesは、最後の`binding.assert_intact`では再検査されない。別processがsemantic読取後からcreate-only writeまでにraw evidenceを差し替えられる。mutable objectにもline 80から81の競合窓が残る。
   - 推奨fix: semanticで検証したraw evidenceのdescriptorまたはstat/digest snapshotをpublishまで保持し、repository lock下で最終照合とcreate-only publishを行う。少なくとも全raw fileRecordを最終再読し、atomic publish直前の同一性を確認する。
   - DW-G05成果物影響: 単独実行では顕在化しないが、並行変更時には検証済みraw evidenceとpublish時点のrepository状態が一致しないreceiptを残せる。

5. **F5 — refuted / nit**

   - 場所: [_manifest.py:271](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:271)
   - 具体的失敗: 固定正常経路に対するD282 predecessor、D574 canonical authority、base/effective foldの片側変更はexact tuple比較で拒否される。新foldを履歴探索して発効する処理もない。
   - 推奨fix: F2とF3を閉じた上で、このexact比較を維持する。
   - DW-G05成果物影響: この項目単独の成果物影響はない。

6. **F6 — unclear / nit**

   - 場所: [_semantic_validator.py:1030](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_semantic_validator.py:1030)
   - 具体的失敗: 通常分岐はcompile commandsのsibling pathを導出し、`read_relative_regular_bytes`でraw CMakeCacheを読み、raw値をline 1093-1098でpositive根拠にする。申告3値はその後の不一致拒否だけなので、コメントと条件は逆転していない。ただし`cmake_cache_path`と`cmake_cache_record`を関数自体は受け入れる。schemaが将来これらを許すと非siblingを選べる。投影資料にはschema定義がないため現行production到達性は断定できない。
   - 推奨fix: production pathでは常にcompile commandsからsiblingを導出し、override fieldsを明示拒否する。
   - DW-G05成果物影響: 現行shape gateでoverrideが拒否される限り影響なし。許可されている場合だけraw三脚保証が崩れる。

7. **F7 — refuted / nit**

   - 場所: [_writer.py:22](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:22)、[_writer.py:81](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:81)
   - 具体的失敗: writerは固定private namespaceへ入力`raw_bytes`そのものを渡し、qsub、driver、exportを呼ばない。`__all__=()`も維持され、implementation.patchにD264/D292変更はない。
   - 推奨fix: 変更不要。
   - DW-G05成果物影響: private receipt publishと投入解除は分離されている。

8. **F8 — refuted / nit**

   - 場所: [index-v1.json:1](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/fixtures/t338_submission_gate/conformance/index-v1.json:1)、[index-v2.json:1](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/fixtures/t338_submission_gate/conformance/index-v2.json:1)
   - 具体的失敗: index-v1 SHA-256は固定値`c66953...0643`と一致し、index-v2先頭42 entryはv1と完全一致した。implementation.patchには旧vector、`test_spool_fold.py`、worklogの変更hunkがない。entry 874本文の独立byte hashは投影資料外だが、このpatchによる変更はない。
   - 推奨fix: 変更不要。親工程でentry 874の既存pin検査だけ継続する。
   - DW-G05成果物影響: 世代境界に新たな破壊は確認できない。

## stage4裁定への直接攻撃

- [stage4-ruling.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage6/inputs/stage4-ruling.md:25)の「caller指定refは持たない」は、explicit-ref loaderがsealed authorityを発行する実装を禁止できていない。
- [stage4-ruling.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage6/inputs/stage4-ruling.md:28)の「sealした唯一のeffective authority」は、import可能tokenと`object.__new__` fixtureを前提にすると成立しない。sealではなくcanonical再導出が必要である。
- stage4は新manifestをauthorityへ追加したが、実receiptの`preregistration.approval_manifest`をD282から新manifestへ移す要件を落としている。この欠落がF1へ直結した。
- projection JSONは`decision_kind`と`forward_supersedes`を名乗る一方、裁定は「新decisionではない」とする。runtimeはD574 exact foldへ固定されているため新fold発効はしていないが、artifact名称とauthority意味の境界は曖昧である。これはnitとしてhandoffへ明記すべきである。
- `fold_commit`とerratumの`approval_fold_commit`をD282 baseのまま残す意味も裁定に明記されていない。`approval_manifest`修正とは分離し、これらがbase foldを表すという契約を記録すべきである。

## trust chain表

| 段 | 正常経路 | 評価 |
|---|---|---|
| D282 base | 固定`D282_DECISIONS_REF`をhistorical blobから読む | exact |
| D574 projection blobs | source定数でmanifest/payloadをpin | 正常wrapperはexact、explicit seamは迂回可能 |
| predecessor/fold | 両projectionをD282 base、D574 effective、D574 canonical refへ比較 | exact |
| vector index | payload refとmanifest refを一致させhistorical digestを読む | 正常経路はexact、協調済みcaller refsで差替可能 |
| ApprovedManifest | projection値を保持 | tokenだけではoriginを証明しない |
| receipt record | `approval_manifest`へD282 refを格納 | blocker、新manifestがtrust chainから脱落 |
| binding | 発行時と再検査時にroot、Git、projectionを確認 | canonical payload全fieldの再導出不足 |
| semantic | receipt record完全一致、raw evidence再読 | 逐次実行は強いがpublishまでの競合窓あり |
| publish | 同一`raw_bytes`を固定namespaceへcreate-only渡し | 維持 |
| qsub/export | 呼出しなし、非export | D292/D264と分離 |

## scope外

- B2 sealed series/receipt-set、producer、driver、collector、report、ledger consumer、D292解除は今回実装しない。F1-F4修正後も親のhandoffとinsightへ未完境界として残す。
- D264の4名前export、PBS/qsub、live receipt、計算資源には到達していない。
- pytestは実行しておらず、緑とは判定しない。stage5記録どおり既存pytestは0件実走である。

## 総括

stage6受理は不可。F1のreceipt authority欠落、F2のcaller-selected projection mint、F3の偽造可能sealがblockerである。F4のraw evidence TOCTOUもproductionで修正すべきである。raw CMake三脚、exact raw bytes、create-only、D292/D264分離、旧index世代不変は今回の投影範囲では維持されている。