## 総括

静的に 331 node を production 実体へ逆引きし、F1〜F4 の境界候補を **26 function** に絞った。判定は **hold 4 / keep 18 / unsure 4**。30 件以下なので打ち切りはない。

`hold` の baseline 実測合計は **0.179 秒**。parametrize された function は suffix を除いた function 単位で合算した。

重要な結論は次のとおり。

- F1 の署名・外部 trust root は実装されておらず、保留対象の番人は見つからない。明示的な「trust root 不在」宣言の検査は `keep`。
- F2 の land / spool fold の commit 束縛は、成果物 provenance というより live admission・防壁である。すべて `keep`。
- 明確な `hold` は、非 test caller が存在しない公表台帳の R2 性質――`(root, kind, ordinal)` 一意性と append-only 履歴――の 4 function。
- F4 の D282 approval parser は非 test caller が 0 だが、追補 P の未実装 blob 凍結そのものか、既承認 bytes の基盤かが混在する。2 function を `unsure` とした。
- 実 ROOT を履歴走査へ渡す node、凍結チェーン 5 系統、toolchain binding の現行 live 検査は各所有 wave または正しさ・測定公正側なので候補外。

pytest は実行していない。秒数は指定された `baseline.xml` のみから取得した。worktree は clean で、編集・commit はしていない。

## 絞り込み表

| nodeid | 族 | production 実体 | 保留可否 | 判定根拠 | 実測秒 | 唯一検出者か |
|---|---|---|---|---|---:|---|
| `test_t810_preregistration.py::test_preregistration_contains_adjudicated_upper_closure` | F1 | `orchestrator/campaign/t810_preregistration.py:443-457` `_validate_schema` | keep | 署名を維持する検査ではなく、外部 trust root が**無い**という限界を機械可読に保つ。T-810 admission の過大主張防止。 | 0.004 | はい |
| `test_dev_wave_land.py::test_provenance_receipt_rejects_each_bound_field` | F2 | `tools/dev_wave_land.py:1535-1566` `_verify_provenance_receipt` | keep | tip・checker blob・実行 bytes・rc を land 前に再照合する防壁の自己完全性。D320 対象外。 | 0.056 | はい、4 field の独立照合として |
| `test_dev_wave_land.py::test_provenance_audit_rejects_executed_bytes_mismatch` | F2 | `tools/dev_wave_land.py:1469-1519` `_audit_provenance_history` | keep | 実際に起動する checker と commit blob の一致を守る land admission。[T-905] 型の guard bytes 防壁。 | 0.030 | はい |
| `test_dev_wave_land.py::test_provenance_receipt_rejects_tip_that_moves_during_audit` | F2 | `tools/dev_wave_land.py:1469-1519` `_audit_provenance_history`; `:1535-1566` `_verify_provenance_receipt` | keep | audit 中の HEAD 移動を拒否する TOCTOU 防壁。保留すると未監査 tip を land し得る。 | 0.167 | はい、統合経路として |
| `test_spool_fold.py::test_plan_fold_observes_standalone_head_and_symbolic_ref` | F2 | `tools/spool_fold.py:376-442` `_observe_origin` | keep | fold transaction の入力 identity を実 Git から観測する live admission。外部公開 provenance ではない。 | 0.032 | はい |
| `test_spool_fold.py::test_plan_fold_rejects_origin_not_matching_observed_git` | F2 | `tools/spool_fold.py:376-442` `_observe_origin` | keep | caller 宣言と実 HEAD/ref の不一致を拒否する。land の正しさゲート。 | 0.039 | はい |
| `test_spool_fold.py::test_transaction_id_binds_origin_closure_and_before_exists` | F2 | `tools/spool_fold.py:2245-2283` `_plan_transaction_id` | keep | transaction ID の衝突・取り違えを防ぐ原子 transaction 契約。 | 0.039 | はい |
| `test_spool_fold.py::test_mark_and_finalize_require_commit_identity_and_phase` | F2 | `tools/spool_fold.py:3241-3283` `mark_fold_committed` / `finalize_fold` | keep | commit 済みでない transaction の finalize を防ぐ CAS/admission。 | 0.050 | はい |
| `test_spool_fold.py::test_commit_identity_gate_rejects_mode_only_manual_fold_commit` | F2 | `tools/spool_fold.py:3146-3238` `verify_fold_commit_identity` | keep | mode-only 差分を含む偽 fold commit の受理を防ぐ。 | 0.087 | はい |
| `test_spool_fold.py::test_commit_identity_gate_rejects_extra_state_external_path` | F2 | 同上 | keep | state 外 path を同じ commit に混入させる land を拒否する。 | 0.078 | はい |
| `test_spool_fold.py::test_commit_identity_gate_rejects_target_status_only` | F2 | 同上 | keep | A/M status の単独改変を拒否する admission。 | 0.086 | はい |
| `test_spool_fold.py::test_commit_identity_gate_rejects_target_blob_oid_only` | F2 | 同上 | keep | plan の after bytes と commit blob の不一致を拒否する。 | 0.090 | はい |
| `test_spool_fold.py::test_commit_identity_gate_rejects_gc_status_only` | F2 | 同上 | keep | GC 対象が削除として commit されなかった場合を拒否する。 | 0.076 | はい |
| `test_spool_fold.py::test_receipt_v2_contains_independently_observed_git_values` | F2 | `tools/spool_fold.py:2469-2490` `plan_fold` の receipt 生成 | keep | fold receipt を実観測した base/tip/ref に束縛する live land 記録。 | 0.047 | はい |
| `test_spool_fold.py::test_receipt_parser_enforces_positional_v2_cutover` | F2 | `tools/spool_fold.py:1631-1695` `_receipt_records` | keep | v2 後に弱い legacy receipt へ戻る downgrade を拒否する。 | 0.001 | はい |
| `test_t793_publication_ledger.py::test_publication_identity_literals_and_schema_are_exact` | F3 | `orchestrator/publication/ledger.py:21-33` module constants | unsure | R2 の原子性ではなく、実装済みの公表台帳識別束縛。D320 対象とも読めるが、T-793 R3 の訂正基盤でもある。 | 0.001 | いいえ。正例でも一部固定 |
| `test_t793_publication_ledger.py::test_one_canonical_publication_entry_is_structurally_readable` | F3 | `orchestrator/publication/ledger.py:198-252` `_parse_entry` / `_load_ledger_bytes` | unsure | 未使用公表層の正例だが、R2 原子性より広い schema/admission を覆うため一括保留は危険。 | 0.015 | いいえ |
| `test_t793_publication_ledger.py::test_reservation_writer_and_success_admission_apis_do_not_exist` | F3 | `orchestrator/publication/ledger.py:1-6` module surface。対象関数は意図的に不存在 | keep | 見送った予約 writer や成功 API が無断で復活しないことを固定する D320 整合の負面防壁。 | 0.001 | はい |
| `test_t793_publication_ledger.py::test_primary_entry_space_is_rejected_before_publication_identity` | F3 | `orchestrator/publication/ledger.py:187-202` `_require_primary_disjoint` | keep | T-793 R3 の「primary と publication の root は別」という実測訂正を支える admission。R2 保留とは別。 | 0.012 | はい |
| `test_t793_publication_ledger.py::test_duplicate_root_kind_ordinal_identity_is_rejected` | F3 | `orchestrator/publication/ledger.py:228-252` `_load_ledger_bytes` | hold | R2 の `(root, ordinal)` 一意性そのもの。公表 reader の非 test caller は 0。 | 0.011 | はい |
| `test_t793_publication_ledger.py::test_unchanged_ledger_bytes_across_merge_history_are_accepted` | F3 | `orchestrator/publication/ledger.py:311-361` `_ledger_history_tip` | hold | 見送り対象の append-only 履歴 gate の positive control。gate と同時に保留可能。 | 0.045 | はい、過剰拒否の正例として |
| `test_t793_publication_ledger.py::test_committed_non_prefix_ledger_history_is_rejected` | F3 | `orchestrator/publication/ledger.py:311-361` `_ledger_history_tip` | hold | 公表台帳の prefix-only 原子履歴を維持する R2 番人。2 parameter node 合算。 | 0.082 | はい |
| `test_t793_publication_ledger.py::test_committed_delete_and_recreate_is_rejected` | F3 | `orchestrator/publication/ledger.py:311-361` `_ledger_history_tip` | hold | 公表台帳の削除・再作成を履歴全体で拒否する恒久 provenance。 | 0.041 | はい |
| `test_t139_approval_payload.py::test_real_fr_payload_has_exact_approved_values` | F4 | `orchestrator/preregistration/approval_payload.py:166-171` `load_approval_payload`; `:174-380` `_parse_approval_payload` | unsure | 非 test caller は 0 だが、追補 P の未承認 blob だけでなく D282 の既承認 7 blob・alpha 台帳まで一括固定する。保留範囲を分離できていない。 | 0.096 | はい、実 D282 全体の exact 値として |
| `test_t139_approval_payload.py::test_alpha_reservation_missing_descriptor_key_is_rejected` | F4 | `orchestrator/preregistration/approval_payload.py:359-368` `_parse_approval_payload`; `:512-530` `_make_alpha_descriptor` | unsure | 公表 R2 と恒久 approval parser の境界。追補 P blob 凍結だけを狙って保留できる node ではない。 | 0.019 | はい |
| `test_t139_approval_payload.py::test_alpha_reservation_commit_must_remain_unpinned` | F4 | `orchestrator/preregistration/approval_payload.py:519-524` `_make_alpha_descriptor` | keep | commit pin を新設しないという粗い provenance 方針を直接固定する。保留すると逆方向の回帰を見逃す。 | 0.018 | はい |

## 保留の実装方針

今回 `hold` とした 4 function は、growth-tests wave が新設中の `orchestrator/tests/growth_test_holds.py` に相乗りする。新しい hold 機構は作らない。

台帳 entry は次の契約へ完全に揃える。

- key は `.py` を含む `basename::function`。
- `release_condition` は `"explicit-user-command-only"`。
- 解除は `IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command` のみ。
- `conftest.pytest_collection_modifyitems` では、該当 node に `xdist_group("real-repo")` を先に付け、その後 `pytest.mark.skip` を付ける。
- `keep` と `unsure` は台帳へ入れない。
- growth wave の台帳が未 land の現 branchでは二重実装せず、land 順序を前提条件にする。

この F3 slice では、まず **test skip のみ**が妥当である。`orchestrator/publication/ledger.py` は非 test caller が 0 であり、production の `_load_ledger_bytes` や `_ledger_history_tip` を迂回させると受理集合を変更する一方、現時点の実行時間削減には寄与しない。

production 自体も保留すると親が裁定する場合は、内部比較を「成功扱い」で飛ばしてはならない。公開入口 `read_publication_ledger` で機械可読な typed hold を返し、内部の一意性・履歴検査だけを静かに fail-open にしない方式が必要になる。これは今回の test 番人保留より広い受理集合変更なので、段 4 の明示裁定対象とする。

## 既存の前例との整合

`orchestrator/tests/test_s8b_oracle_driver.py:469-472` は、既定 skip・明示 env opt-in という意味では今回の恒久 hold と揃えられる。

ただし同 file の `:624-677` は、T-080 helper の consumer を **6 function / 11 node** に厳密固定している。したがって直接 decorator を増減する方式は採らない方がよい。今回の 4 `hold` はその 6 function に含まれず、中央台帳 + collection hook 方式ならこの meta-testを変更する必要もない。

すなわち、既存前例から継承するのは「既定 skip・明示 opt-in・解除条件の検査」であり、実装場所は growth wave の中央台帳へ統一する。

## 明示的に候補外とした境界

- 現行 `toolchain_binding.py` の 7 test は、T-871〜T-874 の未実装拡張ではなく、floor / silo の live toolchain 照合である。測定公正のため `keep` 側だが、表の候補には入れていない。
- `test_t793_approval_guard.py` は T-864 の新 target schema ではなく、fold 時の未確定 marker を拒否する R4 admission。`keep`。
- T-810 approval receipt の raw digest 検査は外部署名ではなく、現行 preregistration admission。`keep`。
- dev-wave checker の runner bytes/hash trust-root 検査は防壁の自己完全性であり、F1 の承認署名ではない。
- 実 ROOT を O(commits) の公表台帳履歴走査へ渡す node は growth-tests wave 所有として候補から外した。
- 資源予約、campaign origin ledger、Python function signature の語彙一致はすべて誤マッチ。

## リスク

test skip だけなら production の受理集合は直ちには変わらないが、次の唯一検出力が通常受入から消える。

- `(family_root, kind, ordinal)` 重複の拒否。
- 同一 bytes の merge history を受理する positive control。
- committed ledger の truncate / rewrite 拒否。
- ledger path の削除・再作成拒否。

特に後ろ 3 件は同じ `_ledger_history_tip` の負例・正例セットである。一部だけ保留すると、残したテストが過剰拒否または不十分拒否を区別できなくなるため、4 function は同じ hold 単位として扱うべきである。

`unsure` の D282 parser 2 件を追加で保留すると、非 test caller が 0 なので即時の production 影響は小さい一方、既承認 7 blob と alpha descriptor の exact 解釈を検出する者が消える。追補 P blob だけを分離できる test / production 検査点が現状ないため、親はこの 2 件を保留せずユーザーへ返すのが安全である。