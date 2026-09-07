結論は must-fix 0 件です。実装は段 4 裁定どおりで、pin、11-file 閉包、4 変異の照準にも scope 内の欠陥は見つかりませんでした。

### Pin 値の取り違えはなく、2 個の同一 golden は契約どおりである

種別: refuted

根拠: fixture terminal は [reflux_origin_fixture_builder.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_builder.py:363) で production outer shape と payload を組み、同 file:391-405 がその records を projection に、同 file:423-477 が projection digest を result evidence に入れる。read-only の in-memory 再計算結果は次のとおり baseline と一致した。

- ordered projection: `975 / 271323c60ad2af8b4034872096d5c1c5066f26c6c85689252dd5ce762ddd3bc6`
- result evidence: `1848 / 631a5fa04f9cc1a5442c5660410bb27b1ad03ef76f5da3fe3d4603ac5577c82c`
- outer commitment: `5aaf3851fe1c8b55ee009a35b9f319cc1feee93d45df7a99c68a56da8bba6cf7`
- wrong-domain digest: `515e7f7ca39461903b9d3291dd010b9576732ff2674f1b29e677aba6032399c3`

[test_reflux_origin_fixture_builder.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_origin_fixture_builder.py:107) は baseline 全 entry を、別定義の canonical JSON と SHA-256 で builder 実物から再計算して exact 比較する。したがって 11-file 走の緑は、少なくとも現在の builder 出力と pin の byte-level 一致を含意する。[focus1-summary.txt:1](/home/SFC/tanab/.claude/jobs/7c254b34/tmp/t2353/logs/focus1-summary.txt:1)

一方、この緑だけでは「fixture terminal の意味が production 契約と同じ」ことまでは独立に証明しない。repository test が outer keys を直接固定するのは trigger だけである。[test_reflux_origin_fixture_builder.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_origin_fixture_builder.py:321) ただし production 契約は別途 [model.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/model.py:98) と [wal.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/wal.py:424) に一致している。

`_RECORD_RAW_GOLDEN` と `_LEDGER_EVIDENCE_DIGEST_GOLDEN` は取り違えではない。[reflux_result_evidence.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_result_evidence.py:65) が「別 helper だが契約上同値」と明記し、同 file:333-350 の両 helper は同じ canonical raw bytes に SHA-256 を適用している。

影響: pin は変更後 fixture の実物を正しく参照しており、fixture report・台帳 digest に stale 値は残らない。

分類: nit

### 11-file の保守的閉包に追加漏れはない

種別: refuted

根拠: `_wal_records()` の caller は [reflux_origin_fixture_builder.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_builder.py:391) と同 file:611-624、`build_ordered_wal_projection()` は同 file:423-471 と [test_reflux_result_evidence.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_result_evidence.py:50) へ波及する。`build_fixture_repository()` は同 file:667-688 から 33 record を生成し、直接 caller は formal consumer、origin binding、origin client、source closure、P3 trial、fixture-builder test に閉じる。

その caller の caller として見つかる追加 test module は、[test_reflux_originless_compatibility.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_originless_compatibility.py:13) が P3 test helper を importし、同 file:126-144 で origin-enabled 経路を実行する 1 fileだけである。これが既に第 11 fileとして焦点走に含まれている。

位置参照も、ordered WAL の terminal を取る production 箇所は [reflux_formal_consumer.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:858)、対応 test は [test_reflux_formal_consumer.py:632](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:632) および同 file:927,951 に閉じる。`reflux_origin_ledger.py` の `records[-1]` は ledger chain headであり別 record 型である。

なお terminal 形状の最小挙動閉包なら、recovery envelope だけを使う `test_reflux_origin_topology.py` と launch admission だけを使う `test_trial_registry.py` は過剰で、9 fileになる。11 fileは module-import を含む保守的閉包として正しい。

影響: fixture 変更による report・台帳・formal consumer 経路は焦点走に含まれており、未実走の既知 consumer は残らない。

分類: nit

### qualification `artifacts.py` の `terminal.get("verify_configs")` は同じ形状不整合ではない

種別: refuted

根拠: [artifacts.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/qualification/artifacts.py:772) の `QualificationEventSink.emit()` は WAL record ではなく pipeline payload を直接受ける。[pipeline.py:1802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/pipeline.py:1802) も `commit_payload` を渡している。sink は [artifacts.py:853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/qualification/artifacts.py:853) でその payload 自体を canonical JSON envelope にし、同 file:982-1003 で decodeした値を、同 file:1082-1094 で `terminal` として読む。したがって `verify_configs` はここでは意図どおり root fieldである。

影響: この reader を WAL payload lookupへ変更すると、逆に qualification evidence の正しい受理集合を壊す。今回の成果物への波及はない。

分類: nit

### terminal の outer shape・重複・root shadow は依然閉じていない

種別: real

根拠: canonical-list 経路は [reflux_result_evidence.py:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_result_evidence.py:601) で `wal.parse_line()` を通らず、同 file:652-658 は record が dictで attempt が一致することしか要求しない。consumer は [reflux_formal_consumer.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:822) で root fieldを payloadより優先し、同 file:858-878 で末尾 record の `stage` と必要 fieldだけを見る。

そのため `{stage:"abort", build_attempt_id:..., candidate_attributable:true, truncated:false, witness_class_sha256s:[...]}` のような flat record、余分 key、payload/root shadow、正しい末尾の前に置いた余分 terminal は引き続き受理可能である。

影響: production shapeでない evidenceでも FC07を越えて receipt、report参照を得られる受理集合の広がりが残る。ただし certified 選択は復活せず、台帳は abortedのままである。

分類: scope 外・裁定パッケージ候補

### M1 は accepted 正例 1 nodeで変更行まで一意に到達する

種別: refuted

根拠: [test_reflux_formal_consumer.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:858) は physical resultと ledger memberを acceptedへ同期し、production commit terminalを構築する。同 file:881-883 と焦点走は、無変異時に全前段を越えて P6Unavailableへ到達することを確認済みである。[focus1-summary.txt:3](/home/SFC/tanab/.claude/jobs/7c254b34/tmp/t2353/logs/focus1-summary.txt:3)

M1では [reflux_formal_consumer.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:862) の比較だけが abort要求へ変わるため、赤の原因はこの FC07 conjunctだけに絞れる。

kill予測の完全集合:

- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_accepts_production_commit_terminal_shape`

影響: M1を見逃すと production accepted terminalが再び FC07となり、report の receipt/evidence参照が nullへ戻る。

分類: nit

### M2 は baseline rejected 正例で一意に捕捉できる

種別: refuted

根拠: default fixture は [reflux_origin_fixture_builder.py:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/reflux_origin_fixture_builder.py:376) の abort terminalを全 recordに使い、[test_reflux_formal_consumer.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:423) は無変異時に P6Unavailableまで到達する。M2では [reflux_formal_consumer.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:868) だけが commit要求へ変わり、最初の rejected terminalで FC07になる。したがって baseline正例を witnessにすれば前段拒否との混同はない。

kill予測の完全集合:

- `test_reflux_formal_consumer.py::test_exact_fixture_contract_reaches_only_p6_unavailable`
- `test_reflux_formal_consumer.py::test_live_producer_trigger_without_source_reaches_only_p6_unavailable`
- `test_reflux_formal_consumer.py::test_live_producer_trigger_with_source_reaches_only_p6_unavailable`
- `test_reflux_formal_consumer.py::test_verbatim_producer_records_with_only_attempt_transplanted_reach_p6`
- `test_reflux_formal_consumer.py::test_fc09_rejects_kmax_excess`
- `test_reflux_formal_consumer.py::test_fc09_rejects_query_floor_mismatch`
- `test_reflux_formal_consumer.py::test_fc10_rejects_origin_containing_all_tombstone_batch`
- `test_reflux_formal_consumer.py::test_receipt_has_exact_keys_independent_canonical_bytes_and_no_self_digest`
- `test_reflux_formal_consumer.py::test_receipt_rejects_wrong_input_state_commitment`
- `test_reflux_formal_consumer.py::test_receipt_rejects_wrong_terminal_payload_digest`
- `test_reflux_formal_consumer.py::test_receipt_exact_operation_replay_returns_cached_decision`
- `test_reflux_formal_consumer.py::test_receipt_same_operation_different_payload_is_rejected`
- `test_reflux_formal_consumer.py::test_terminal_projection_is_one_nested_key_with_closed_reason`
- `test_p3_autonomous_workload_trial.py::test_origin_public_path_preserves_capability_identity_and_projects_terminal`

最後の node は [test_p3_autonomous_workload_trial.py:10778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_p3_autonomous_workload_trial.py:10778) が P6Unavailableと非 null参照を要求するため赤になる。`test_fc09_rejects_nonexact_rejected_class_set` は [reflux_formal_consumer.py:1031](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:1031) の前置 FC09で止まるため、kill集合には入らない。

影響: M2を見逃すと全 production rejected projectionが witness検査より前の stage比較で拒否され、後段 reasonと receipt参照が失われる。

分類: nit

### M3 も accepted 正例 1 nodeで一意に捕捉できる

種別: refuted

根拠: commit比較を `terminal.get("kind")` へ戻すと、[test_reflux_formal_consumer.py:869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_formal_consumer.py:869) の production-shaped terminalには root `kind` がない。他の入力は無変異時に P6Unavailableまで通るため、赤はこの reader差し戻しに限定できる。

kill予測の完全集合:

- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_accepts_production_commit_terminal_shape`

影響: M3を見逃すと accepted production terminalだけが FC07へ戻り、旧 fixture形状への依存が再発する。

分類: nit

### M4 は baseline exact比較 1 nodeだけを殺す

種別: refuted

根拠: [test_reflux_origin_fixture_builder.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/tests/test_reflux_origin_fixture_builder.py:107) は baseline dictと全 builder再計算値を exact比較するため、projection hashの 1 文字変更で必ず赤になる。`F.baseline()` の他 callerは同 file:122-128だけだが、そこは `build_result_evidence_record` entryとの不等価を検査しており、projection entryだけを変えるM4では赤にならない。

kill予測の完全集合:

- `orchestrator/tests/test_reflux_origin_fixture_builder.py::test_baseline_schema_and_every_entry_match_independent_recalculation`

影響: M4を見逃すと baseline上の ordered projection参照だけが実物から外れる。本番 certified 選択や台帳には直接影響しない。

分類: nit

### Diff に揮発値の焼き込みや test 弱化はない

種別: refuted

根拠: actual `git diff HEAD` は [implemented.patch:1](/home/SFC/tanab/.claude/jobs/7c254b34/tmp/t2353/verbatim/implemented.patch:1) と一致する5 fileだけである。追加値は model定数、固定 fixture値、実物から導いた digestだけで、commit hash、PWD、時刻、working tree hashはない。既存 test変更も、terminal fieldを payloadへ移したことに合わせた path修正と、verify-order testを正しい production outer shapeへ移したものだけで、assertion削除や許容条件緩和はない。[implemented.patch:149](/home/SFC/tanab/.claude/jobs/7c254b34/tmp/t2353/verbatim/implemented.patch:149)

影響: 再実行環境による pin変動や、不正 terminalを既存 testが新たに許す変更は発生しない。

分類: nit

### 修理後も certified 選択は復活せず、変わるのは accepted report の reasonと参照だけである

種別: refuted

根拠: production pipelineの certified判定は formal consumerより前の [pipeline.py:1627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/pipeline.py:1627) から同 file:1668で確定し、commit payload/WALは同 file:1762-1800で書かれる。formal consumerは全検査成功後も [reflux_formal_consumer.py:1071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_formal_consumer.py:1071) で常に P6Unavailableを返す。reportは [p3_autonomous_workload_trial.py:3618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/p3_autonomous_workload_trial.py:3618) でその projectionを載せるが、clientは P6Unavailableと FormalContractRejectedの双方を [reflux_origin_client.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2353-terminal-stage/orchestrator/campaign/reflux_origin_client.py:208) で受け、同 file:259-268で同じ `OriginSealed(aborted=True)` に写す。

影響: accepted production terminalの reportは `FC07 / null refs` から `P6Unavailable / receipt・evidence digest refs` へ変わるが、certified選択集合と台帳の aborted terminalは変わらず、rejected側は witness producer不在のため FC07のままである。

分類: nit

## 総括

must-fix:

- 0 件。

scope 外・裁定パッケージ候補:

- terminal outer keys、型、重複、root shadow、terminal個数を閉じる gate。これは実在する受理集合の広がりだが、段 4 裁定4により本 wave の must-fixではない。

4変異はいずれも実効 gateへ照準済みで、代案への再照準は不要です。親の「accepted terminalが FC07を通って P6Unavailableへ進むだけで、certified選択は復活しない」という結論は正しいです。