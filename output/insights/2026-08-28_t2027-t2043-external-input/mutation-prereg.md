# B-057 変異事前登録

各変異は新設する焦点 node 1系統だけを狙い、前後層が同じ入力を独立拒否しない位置へ author/review 後に exact replacement を束縛する。

| ID | 実効 gate | 単一変異 | 期待する検出 node | 単一赤理由 |
|---|---|---|---|---|
| M1-SCHEMA-PIN-OMITTED | buildcache identity | v2 manifest schema pinをpreimageから除く | `test_v2_schema_pin_separates_legacy_completion_without_fallback` | 旧v1 entryを選択してしまう |
| M2-FETCH-ROOT-AS-FILESYSTEM | collector分類 | masstree入力をfilesystem rootで保存する | `test_v2_manifest_classifies_fetchcontent_root_relative` | run-local absolute rootがmanifestへ残る |
| M3-CURRENT-BASE-IGNORED | hit validator | recorded/origin rootをcurrent rootの代わりに使う | `test_v2_hit_rebinds_fetchcontent_inputs_to_current_root` | base A→B再束縛が発火しない |
| M4-CURRENT-HASH-SKIPPED | live bytes gate | current FetchContent inputのhash比較を外す | `test_v2_current_fetchcontent_bytes_drift_is_rejected` | 異なるheader bytesを受理する |
| M5-MISSING-INPUT-ACCEPTED | strict resolve | FileNotFoundを無視またはstrictでなくす | `test_v2_missing_current_fetchcontent_input_is_rejected` | 欠落external inputを受理する |
| M6-SYMLINK-COMPONENT-ACCEPTED | path traversal | component no-follow拒否を外す | `test_v2_current_fetchcontent_symlink_component_is_rejected` | 別rootへのsymlinkを受理する |
| M7-ROOT-CANONICALITY-SKIPPED | validator分類 | filesystem tagのsnapshot/FetchContent内着地拒否を外す | `test_v2_rejects_noncanonical_root_tag` | snapshot/external境界をtag偽装で迂回する |
| M8-RECEIPT-RECHECK-OMITTED | issuer | receipt発行時のcurrent root contextを外す | `test_issue_v2_receipt_rechecks_current_fetchcontent_root` | build後差替えをreceiptが検出しない |
| M9-HIT-FALLBACK-ENABLED | cache hit | validation failure後にfresh buildへ進める | `test_v2_hit_validation_failure_never_rebuilds` | invalid selected entryをcache missへ降格する |

通る正例として、base A/Bのrelative pathとhashが一致するv2 hit、snapshot-only v1 receiptのportable validation、system externalの同一絶対path/hashを登録する。これらが赤になる過剰拒否も不合格とする。
