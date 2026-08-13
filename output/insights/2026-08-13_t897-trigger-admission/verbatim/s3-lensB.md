静的検査結果です。必読資料はすべて読めました。pytest・実ビルドは実行していません。

### 所見 1 — cache hit 自体は gateway を再発火する

severity: nit

根拠:

- `buildcache.build_v2` は cache 判定前に `require_build_admission` を呼ぶ: `buildcache.py:1273-1277`, cache hit は `:1363-1385`。
- legacy `build` も同様: `buildcache.py:1538-1542`, cache hit は `:1576-1609`。
- sidecar／completion manifest の `validate_build_admission_receipt` は、この entry gate の後段: `buildcache.py:902-915`, `:967-980`。

したがって warm cache、legacy/v2 cache hit、binary の再利用が `buildcache.build*` 経由なら semantic gate は再発火する。WAL replay (`wal.py:1115-1129`) と S8a artifact receipt 読み出し (`s8a_trigger_sweep.py:181-199`) は source-less replay なので別物である。

未実装時の成果物影響: `require_build_admission` を cache 判定後へ移すと、非正準 source の既存 cache binary が semantic 検査なしで certified selection に戻る。

### 所見 2 — `true` hole は coverage/frequency だけでなく S8a stock baseline も止める

severity: must-fix

根拠:

- S8a coverage は template patch 適用後、`true` のまま `derive`/`require` に到達する: `s8a_trigger_coverage.py:153-161`, patch 適用は `:257-268`。
- 結果ファイルの書込みは build・実走の後: `s8a_trigger_coverage.py:321-325`。
- frequency driver も同じ `_build` を import して使う: `s8a_trigger_freq.py:63`, `:147-153`。
- S8a sweep は候補列挙の先頭に `stock` を置く: `s8a_trigger_sweep.py:255-256`。stock は flag 0 だが `TEMPLATE_PATCH` を適用し、hole を置換しない: `:302-303`, `:441-459`。
- pipeline の pre-build reject は receiptless `BUILD_START`/`ABORT` を書く: `pipeline.py:716-738`。

これは P1 の marker-only 判定では「flag 0 の stock baseline も materialized axis」と扱うためである。既存 report は stock を `build-error` としている (`output/.../s8a_trigger_sweep_report...md:17`)が、再走時は `admission-error` に変わる。

未実装時の成果物影響: S8a stock row の abort reason、WAL payload、再走 report が変わり、coverage/frequency は新しい certified 値を生成できない。

### 所見 3 — `(i)` と `(ii)` は再現性が両立しない

severity: must-fix

`(i)` の driver 停止では、現行 `s8a_trigger_gating_coverage.json` の `all_pass=true` と `s8a_trigger_freq_t48.json` の `effective_reasons` 3件が残るだけで、同じ値を現在の gateway 経由では再取得できない。canonical emitter に置換すると stock-equivalent characterization ではなくなる。

`(ii)` の frozen `true` bytes 例外は、32 emitter の受理集合を広げる。また receipt bytes を変えない限り、後段の `validate_build_admission_receipt` は通常の canonical build と例外 build を区別できない。

別裁定で characterization 専用例外を認める場合でも、bytes は手書き文字列や既存 artifact からではなく、`patches/silo-backoff-trigger-gating-variant.patch:101-103` とその固定 SHA から導出する必要がある。ただしこれは T-897 の一般 admission 集合へ追加してはならない。

未実装時の成果物影響: `(i)` では台帳に新しい coverage 値が増えず旧値が現行値として残り、`(ii)` では例外 build が通常 certified receipt と同じ形で再生される。

### 所見 4 — receipt の key 集合と bytes は保全可能

severity: nit

根拠:

- `_ADMISSION_KEYS` は `build_admission.py:428-432`、body と `receipt_sha256` は `:553-566`。
- `s8b_materialization.py:65-95` は review receipt の SHA を計算するだけで、build admission body を変更しない。
- critic projection は伝播された SHA の表示ラベルだけを変える: `orchestrator/critic/digest.py:865-874`, `p3_s4_loop.py:453-470`。
- WAL は receipt の canonicality、伝播 SHA、recovery payload key 集合を検査する: `wal.py:1119-1129`, `:1197-1204`。
- `tools/mutation_fanout.py:45` は別 schema namespace である。

未実装時の成果物影響: validator が mask、exemption、semantic result を receipt に追加すると outer SHA と cache/WAL/critic projection の全値が変わる。

### 所見 5 — P4 の parser/read failure 方針は実装順を誤ると fail-open

severity: must-fix

根拠:

- `parse_template_file` は全 `OSError` を `None` に変換する: `diff_quarantine.py:557-561`。
- 一方、計画は `FileNotFoundError` のみ no-op、`EIO`/`PermissionError`/`ENOTDIR` は reject としている: `s2-plan.md:94-107`。
- parser を先に呼び、`None` を marker absent と解釈すると、I/O failure が no-op になる。

raw bytes の read で先に `FileNotFoundError` とそれ以外を区別し、その後 parser を呼ばない限り、計画の P4 は成立しない。

未実装時の成果物影響: materialized source の EIO・権限失敗が marker absent と誤認され、admission receipt、certified selection、ledger が生成される。

### 所見 6 — P3 は hole 判定としては正しいが、axis 判定としては弱い

severity: should-fix

根拠:

- 計画の exact one-line／32 emitter bytes／marker uniqueness は妥当: `s2-plan.md:62-92`。
- しかし parser の `if_re` は任意の `#if` を受理する: `diff_quarantine.py:566`。
- validator は `#if BACKOFF_TRIGGER_GATING` の bytes や patch frame 全体を検査せず、hole だけを検査する: `s2-plan.md:66-72`。

したがって、同じ marker と canonical hole を残しつつ別の `#if` 条件へ移した source が「trigger axis」として受理される。これは非正準 hole の bypass ではないが、P1 の「marker = axis materialization」という一般化を崩す。

未実装時の成果物影響: unrelated な conditional source が trigger-axis build として admission され、variant identity・report・manifest の軸帰属が誤る。

### 所見 7 — 既存テストは新 gate の mutation attribution になっていない

severity: should-fix

根拠:

以下の `test_campaign.py` nodeid は、新 validator ではなく既存の `pipeline._require_materialized_trigger_predicate` を直接呼ぶ、またはそれに依存する。

- `test_trigger_binding_rejects_materialized_predicate_with_outer_spaces`
- `test_trigger_binding_rejects_materialized_predicate_with_leading_tab`
- `test_trigger_binding_rejects_materialized_predicate_with_leading_vertical_tab`
- `test_trigger_binding_rejects_materialized_predicate_with_leading_form_feed`
- `test_trigger_binding_rejects_materialized_predicate_with_leading_non_breaking_space`
- `test_trigger_binding_rejects_materialized_predicate_with_leading_ideographic_space`
- `test_trigger_binding_rejects_materialized_predicate_with_trailing_space`
- `test_trigger_binding_rejects_materialized_predicate_with_four_space_indent`
- `test_trigger_binding_rejects_materialized_predicate_with_crlf_line_ending`
- `test_trigger_binding_rejects_materialized_predicate_with_cr_only_line_ending`
- `test_trigger_binding_rejects_crossed_materialized_predicate_and_mask`

根拠箇所は `test_campaign.py:5393-5409`, `:5629-5665`。generic validator を削除しても、既存 binding 検査が同じ reject を出すため、これらは赤くならない。canonical mask 20 + binding mask 21 は、新 gate が通過してから既存 mask 検査が落とす組合せである。

さらに gate が先に発火すると、binding mask 検査 (`pipeline.py:787-798`)、legacy sidecar (`buildcache.py:902-915`)、v2 manifest identity (`:967-980`) は実行されない。

未実装時の成果物影響: mutation matrix が緑でも semantic gate が削除され、非正準 binary が後段の既存検査を通って certified になる可能性が残る。

### 所見 8 — 既存 pytest の「新 gate による赤集合」は静的には空

severity: nit

正しい no-op 条件（target 不在・marker 不在）を実装する限り、既存 pytest nodeid で確実に赤くなるものは静的にはありません。`pytest` は未実行です。

実際、

- `test_build_admission.py` の synthetic root は `/evidence/ccbench`: `test_build_admission.py:50-69`。
- S8a sweep の admission test は target file を作らない: `test_s8a_trigger_sweep.py:355-374`, `:439-462`。
- build-site cache-hit test は synthetic `ccbench` root: `test_build_site_gate.py:197-208`, `:452-460`。
- 実 external stock source は marker 0。
- `test_campaign.py:5582-5627` は canonical hole、負例群は旧 binding helper 直結。

逆に、missing target を誤って reject すると、少なくとも次が nodeid 単位で赤くなる。

`test_clean_repo_pinned_stock_is_derived_without_authority`, `test_dirty_noop_does_not_derive_stock`, `test_stock_requires_repo_declared_pin`, `test_registered_generator_receipt_derives_machine`, `test_generator_receipt_from_another_run_is_rejected`, `test_review_receipt_is_exactly_source_bound`, `test_generator_and_review_receipts_are_ambiguous`, `test_coder_requires_parser_issued_run_token`, `test_cli_nonce_is_not_serialized`, `test_persistent_receipt_has_exact_full_canonical_body`, `test_persistent_receipt_rejects_unknown_key_and_outer_sha_mutation`, `test_receipt_validation_binds_source_root` (`test_build_admission.py`)。

未実装時の成果物影響: no-op を誤分類すると、既存の synthetic admission、cache-hit、receipt key 集合の検査が大量に赤くなり、stock／report の従来値も維持できない。

### P 判定

severity: should-fix

根拠:

| 判定対象 | 判定 |
|---|---|
| P1 | `real`（materialization の観測信号として）。ただし active axis の一般判定としては `refuted`。S8a stock は flag 0 でも marker を持つ。 |
| P2 | `real`（live require と archival replay の責務分離）。ただし全 artifact の遡及的 semantic admission まで保証する主張は `refuted`。 |
| P3 | hole の exact predicate は `real`。axis frame／条件まで含む完全な受理述語という主張は `refuted`。 |
| P4 | `refuted`。非 FNF read failure は marker 観測不能でも reject しなければ fail-open になる。 |
| P5 | live build gateway の中央結線としては `real`。全成果物・全 consumer を覆う scope 主張は `refuted`。 |

未実装時の成果物影響: P1/P5 を無条件に一般化すると、certified selection と floor/oracle manifest に「gateway を通っていない既存 binary／receipt」が混入する。

## scope 外の実所見（ruling package 候補）

### S8b content-addressed binary store の admission 非束縛

severity: should-fix

根拠:

- portable binary schema は binary/hash/store path を持つが admission receipt を持たない: `s8b_floor_campaign.py:175-180`。
- resume は store の存在と SHA だけを確認する: `s8b_floor_campaign.py:2051-2070`, 呼出し `:3289-3290`。
- oracle 実走前も store hash のみを検査する: `s8b_oracle_driver.py:918-949`。
- 本ファイル自身も既知限界として明記している: `s8b_floor_campaign.py:40-48`。

T-897 の scope では修正しない。別 ruling で binary store に build-admission SHA／source semantic provenance をどう束縛するかを決めるべきである。

未実装時の成果物影響: admission 未証明の既存 binary でも hash が一致すれば floor の測定値、manifest、oracle report に使われる。

### Historical receipt / frequency artifact の再検証不足

severity: should-fix

根拠:

- WAL replay は receipt key／SHA／topology を検証するが live source semantic は見ない: `wal.py:1115-1129`。
- S8a frequency artifact も receipt mapping の canonicalityだけを検証する: `s8a_trigger_sweep.py:161-199`。
- 現行の `effective_reasons` は既存 `s8a_trigger_freq_t48.json` から継続利用される。

これは P2 の replay I/O を変更する提案ではなく、別途 artifact generation epoch／semantic provenance を裁定すべき scope 外問題である。

未実装時の成果物影響: gate 導入前に生成された `all_pass`、`effective_reasons`、certified sweep report が、現行 semantic gate による再生成なしで引き続き採用される。

## 総括

live の `build`／`build_v2` と cache hit は中央 gateway で閉じられる。一方、`true` hole の coverage 再取得、S8a stock baseline、parser の I/O 例外処理、mutation attribution は land 前に明示的な裁定または補強が必要です。S8b binary store と historical receipt の再検証は T-897 scope 外の ruling 候補です。