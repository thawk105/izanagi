## 総括

現行 HEAD `38f173cb` に対する read-only 実装プランは、C09 を build report 専用の Layer 3 acceptance gate、C10 を実 byte 再読型 verifier として配線する形です。受領証は top-level に `cross_binding_receipt_sha256` を追加し、schema は v3 へ上げます。実装・pytest 実走は行いません。

1. 変更単位

| file | 関数・位置（現行 HEAD） | 内容 |
|---|---|---|
| `orchestrator/campaign/trial_registry.py` | import block 31-35 | `assert_campaign_layer3_chain` と `verify_s8c_cross_binding` を同 module から直接 import |
| 同上 | `assert_trial_registry_acceptance` 2557、特に 2836 の後、2843 の前 | `do_build` 別 C09 gate、C10 呼び出し、受理前失敗処理 |
| 同上 | receipt 構築 2905-2934 | `"no-build"` reason と、6 report 分の C10 受領証 aggregate digest を receipt に格納 |
| `orchestrator/campaign/autonomous_trial_completeness.py` | import 28-35 | `wal`、`CampaignLayout` などを追加 |
| 同上 | `_bound_regular_bytes` の後、現行 475 と `_canonical_descriptor_digest` 477 の間 | `read_and_verify_bytes` を新設 |
| 同上 | `verify_autonomous_trial_files` の前、現行 3008 | `verify_s8c_cross_binding` と build/no-build receipt projection を新設 |
| `orchestrator/campaign/s8c_acceptance_receipt.py` | 定数 23-53、`AcceptanceReceipt` 111-126 | v2 を previous schema として保存し、現行 v3 と `cross_binding_receipt_sha256` を追加 |
| 同上 | `parse_acceptance_receipt_bytes` 293-465 | v1/v2/v3 の top-level key 集合を分離し、v3 field を検査 |
| 同上 | `verify_acceptance_receipt` 843-921 | v2 と v3 の arm binding / reason 検査を共通化 |
| `orchestrator/tests/test_trial_registry.py` | acceptance tests 964 以降、receipt exact assertion 1006-1027、1540-1549、2562-2590 | no-build reason、v3 receipt、C09/C10 の順序と負例を追加 |
| `orchestrator/tests/test_autonomous_trial_completeness.py` | Layer 3 tests 2970-3610 の近傍、または EOF 3844 の前 | C10 の実 artifact fixture と byte mutation tests を追加 |
| `orchestrator/tests/test_s8c_acceptance_receipt_v2.py` | fixture 64-157、EOF 433 の前後 | v2 historical receipt と v3 receipt の両方を検査 |
| `orchestrator/tests/test_s8c_preregistration_predicates.py` | snapshot 139-166 | C09/C10 を `EVIDENCE_UNDEFINED` へ更新 |
| `orchestrator/tests/test_s8c_preregistration_invariant.py` | CHECKS 43-85、EXCLUSIONS 87-123 | brief の3件の pin を CHECKS へ移動 |
| `orchestrator/tests/test_reflux_originless_compatibility.py` | `_project_t822_receipt_v2_to_v1` 594-689 と呼び出し箇所 | v3 receipt field と `no-build` reason を消費して旧 v1 projection へ戻す |

`p3_autonomous_workload_trial.py:2729` の producer 側 Layer 3 呼び出しは既存形を維持します。評価器、契約 JSON、凍結 record も変更しません。

2. C09 の実装形

`assert_trial_registry_acceptance` の各 report について、現行 2836 の `assert_execution_digest_chain` が通った直後、現行 2843 の `accepted.append` より前に次の順序で実行します。

- `report["do_build"] is False` の場合は C09 Layer 3 を呼ばず、`no_build_seen = True` とする。
- `report["do_build"] is True` の場合は、`cells` が list かつ要素1件であること、cell が Mapping で `campaign_root` があることを要求する。
- `campaign_root = Path(cell["campaign_root"]).resolve(strict=True)` とし、`output_root = campaign_root.parent.parent` とする。
- `assert_campaign_layer3_chain(report=report, output_root=output_root)` をその report に対して実行する。
- `AutonomousTrialCompletenessError`、path 解決失敗、campaign root 欠落は `TrialRegistryError` に変換する。
- Layer 3 が正常終了した report だけが次の C10 gate と `accepted.append` に進む。

`assert_campaign_layer3_chain` は `cells=[]` なら内部 loop が空のまま戻るため、`do_build=True and not cells` を acceptance 側で先に拒否します。これが P5 の抜け道を塞ぐ部分です。build report の `layer3_report.json` 欠落、persisted report と fresh rebuild の不一致も chain 呼び出しで失敗し、receipt 作成まで到達しません。

no-build の場合は acceptance 自体を落としません。現行の構造的非 certifying 方針を維持し、receipt 集約時に次の literal を acceptance 本体へ置きます。

`if no_build_seen: reason_codes.append("no-build")`

この文字列は評価器を満たすためだけの未使用 literal ではなく、`do_build=False` という report の実値から、Layer 3 未実行であることを receipt の非 certifying reason に投影するものです。receipt の `"certifying": False` は現行 2931 のまま変更しません。

3. C10 の実装形

`read_and_verify_bytes` のシグネチャは次の形にします。

`read_and_verify_bytes(value, *, root, expected_sha256, gate, label) -> tuple[Path, bytes]`

処理は以下です。

- 相対 path は `root / value` に正規化し、絶対 path はそのまま検査する。
- `_bound_regular_bytes` を通して root 外、symlink、非 regular file、path traversal を拒否する。
- 読み直した bytes の SHA-256 が `expected_sha256` と一致しなければ `AutonomousTrialCompletenessError`。
- path と実 bytes を返す。

`verify_s8c_cross_binding` のシグネチャは次の形にします。

`verify_s8c_cross_binding(*, report, events, run_root, output_root=None) -> dict[str, Any]`

build mode では12 fieldをすべて実値で束縛します。

| field | 実際の source key / bytes |
|---|---|
| `input_payload_sha256` | `events` の `event=="role-attempt"` 各 event の `input_payload_sha256`。`provider_artifacts.payload_path` を読み、同じ hash であることを確認 |
| `raw_response_path` | 同じ role event の `raw_response_path` |
| `raw_response_sha256` | role event の `raw_response_sha256` と raw response bytes の再計算値 |
| `provider_payload_sha256` | role event の `provider_payload_sha256`。`provider_artifacts.payload_path` の実 bytes hash と比較 |
| `provider_envelope_sha256` | role event の `provider_envelope_sha256`。`provider_artifacts.envelope_path` の実 bytes hash と比較 |
| `proposal_path` | `report["cells"][*]["generations"][*]["proposal"]["path"]` |
| `proposal_sha256` | 同 proposal object の `sha256` と proposal bytes の再計算値 |
| `build_records` | `campaign_root/runs/wal.jsonl` を `wal.read_records_checked` で再読した build-side record projection |
| `bench_records` | 同 WAL の `stage=="bench_done"` record projection。`layer3_report["runs"]` と supervisor の `generation["harness"]["records"]["bench_done"]` に一致させる |
| `artifact_refs` | persisted `layer3_report.json` の `artifact_refs` 各 `{path, sha256}`。campaign root 基準で全件再読 |
| `source_refs` | WAL record と `loop_state.json` の whiteboard から `canonical_record_ref` を再計算し、layer3 の `source_refs` と exact multiset 比較 |
| `admission_decision` | cell の `admission_decision`、persisted layer3 の同 key、`require_admitted_campaign(..., purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE).decision.as_receipt()` の三者 exact 比較 |

WAL については `campaign_root/runs/wal.jsonl` 自体を `admission_decision["wal_sha256"]` と `artifact_refs` の hash の両方で検査します。`campaign.lock` は `admission_decision["campaign_lock_sha256"]` で検査します。`build_records` と `bench_records` は別々の固定 projection にし、WAL の未分類 record を黙って捨てないよう、union が再読した全 record になることも確認します。

supervisor 側は各 generation の `harness["variant"]` と WAL の `bench_done.variant` を一対一に対応させ、`harness["records"]` の stage payload、`generation["bench_wall_seconds"]`、WAL の `bench_wall_s` を比較します。variant 欠落、重複、WAL 側の対応 record 欠落は失敗です。

再利用する既存 helper は次のとおりです。

- `_bound_regular_bytes`
- `_decode_canonical_object`
- `_check_registered_proposal`
- `_check_registered_provider_artifacts`
- `_require_exact_layer3_admission_decision`
- `canonical_record_ref`
- `_layer3_report._variant_rows`
- `_layer3_report._view_row`
- `wal.read_records_checked`
- `require_admitted_campaign`

no-build mode では build artifact が存在しないことが正規状態です。そのため、`do_build=False` なら verifier は raw/provider/proposal/WAL の不存在を build proof として通さず、`mode: "no-build"`、`unbound_fields`、実際の `trial_id`、cell 数、journal event の logical id だけを含む非証明 receipt projection を返します。receipt には no-build の状態を記録しますが、C10 の12 fieldを束縛したとは扱いません。build mode での欠落は必ず失敗です。

返す一 report 分の受領証は次の論理形です。

`{"schema_version": "p3-8c-cross-binding-receipt/v1", "trial_id": ..., "mode": "build", "bindings": {12 field}, "receipt_sha256": ...}`

`receipt_sha256` は `receipt_sha256` 自身を除いた canonical JSON の hash とします。acceptance は6 reportを trial_id 順に並べ、

`{"schema_version": ".../v1", "trials": [{"trial_id": ..., "receipt_sha256": ...}]}`

を `_canonical_json_bytes` で hash し、receipt top-level の `cross_binding_receipt_sha256` に格納します。最後の report の digest だけを保存する形にはしません。

呼び出し順は次です。

`_assert_snapshot_completeness`  
→ `assert_execution_digest_chain`  
→ C09 の `assert_campaign_layer3_chain`  
→ C10 の `verify_s8c_cross_binding`  
→ `accepted.append`  
→ 6件全体の lifecycle snapshot と receipt 作成

したがって C09/C10 のいずれかが失敗すれば `accepted` に入らず、`_exclusive_create_acceptance_receipt` も実行されません。現行関数内の registry lookup は read-only の事前照合であり、formal acceptance の append と receipt issuance は上記 gate の後です。

receipt schema は v3 にします。

- `PREVIOUS_SCHEMA_VERSION = ".../v2"` を追加。
- `SCHEMA_VERSION = ".../v3"` に変更。
- v1/v2 用の旧 top-level key set は保存。
- 現行 `_TOP_LEVEL_KEYS` に `cross_binding_receipt_sha256` を追加。
- v3 ではこの field を `_require_sha256` で必須化。
- v1/v2 は field なしで引き続き parse 可能。
- v2/v3 の arm execution 検査、C02 reason 検査は共通化。
- v1 の旧 mandatory reason は変更しない。

4. 恒真性の否定

- no-build gate: 現行 `test_trial_registry.py:_base_report` の `do_build=False`、`cells=[]` で `"no-build"` が追加され、receipt は非 certifying になる。
- build-cell 欠落 gate: 同じ fixture の `do_build` だけを `True` にすると `cells=[]` のため `TrialRegistryError`。
- campaign root gate: `_complete_report` の `cells[0]["campaign_root"]` を1行削除すると `output_root` を導けず失敗。
- Layer 3 chain gate: `_layer3_campaign` の persisted `runs[0]["median_tps"]` を `125162981` に変えた既存 mutation で fresh rebuild 不一致となり失敗。
- raw response gate: 実 build fixture の `raw_<invocation_id>.txt` を1 byte変更し、role event の `raw_response_sha256` を旧値のままにすると失敗。
- provider gate: 既存 provider fixture の `provider_envelope_sha256` を `"c"*64` に変える mutation で失敗。
- proposal gate:既存 registered fixture の proposal `digest` を `"e"*64` に変える mutationで失敗。
- WAL gate: `admission_decision["wal_sha256"]` を旧値のまま WAL の `bench_done` bytes を変更すると失敗。
- bench gate: WAL の `bench_done.payload["bench_wall_s"]` を変更し、supervisor の `bench_wall_seconds` を旧値のままにすると失敗。
- artifact gate: persisted layer3 の `artifact_refs` から1行を削除すると exact set または再読対象の不足で失敗。
- source gate: persisted layer3 の `source_refs` から1件を削除すると canonical ref multiset 不一致で失敗。
- admission gate: cell と persisted layer3 の `admission_decision["classification"]` の片方だけを変更すると三者比較で失敗。
- receipt schema gate: v3 receipt から `cross_binding_receipt_sha256` を1行削除すると exact top-level key 検査で失敗する。

5. 既存テストへの影響

P4 は `do_build=False` については同意しますが、`cells=[]` については現行 HEAD と完全には一致しません。`_base_report` は 392 行で `cells=[]` ですが、`_complete_report` は 774 行で1 cellを生成します。したがって実装は「cells 数」ではなく `do_build=False` を no-build の判定軸にします。

既存 acceptance fixture は赤にしません。

- `do_build=False, cells=[]` は no-build receipt projection になり、acceptance は継続。
- `do_build=False, cells=[...]` も Layer 3 は呼ばず、no-build reason を付けて継続。
- no-build report の raw path や proposal path は、build mode でないため C10 の byte reread 必須入力にはしません。
- `do_build=True` で campaign chain が欠落する fixture は production を緩めず赤にします。

ただし receipt の exact assertion は意図的に更新が必要です。

- 完全な no-build report は `["no-build", "t468-approval-authority-absent"]`。
- `cells=[]` を含む partial 集合は `["c02-arm-binding-unproven", "no-build", "t468-approval-authority-absent"]`。
- v2 receipt fixture は `PREVIOUS_SCHEMA_VERSION` を明示して旧形を維持。
- 現行 acceptance fixture は v3 field と aggregate digest を期待。
- `test_reflux_originless_compatibility.py` は v3 field と no-build reason を消費してから、凍結済み v1 view の旧 reason に戻す。

6. pin 閉包の全件

brief の3件に加え、次を更新します。

- `C09 / trial_registry.py / assert_campaign_layer3_chain`  
  EXCLUSIONS の `different-module-token` から CHECKS へ移動。
- `C10 / autonomous_trial_completeness.py / verify_s8c_cross_binding`  
  `declared-unimplemented-token` から CHECKS へ移動。
- `C10 / trial_registry.py / verify_s8c_cross_binding`  
  同じく CHECKS へ移動。
- `s8c_acceptance_receipt.py:24` の `SCHEMA_VERSION` を v3 化。
- 同ファイルの `_TOP_LEVEL_KEYS:38-53` に `cross_binding_receipt_sha256` を追加し、v1/v2旧集合を別名で保存。
- `parse_acceptance_receipt_bytes:304-307` の schema 別 exact key 選択。
- `AcceptanceReceipt:111-126` の新 field。
- `verify_acceptance_receipt:898-912` の v2/v3 共通検査。
- `test_trial_registry.py:1007` の v2 literal と reason exact assertion。
- 同 2562 の `test_acceptance_v2_has_no_certifying_issuance_branch` は v3 名へ変更し、`certifying=True` が存在しない pin は維持。
- `test_s8c_acceptance_receipt_v2.py` の `receipt.SCHEMA_VERSION` 参照は historical v2 では `PREVIOUS_SCHEMA_VERSION` に変更。
- 同ファイルに v3 positive / missing-field tests を追加。
- `test_reflux_originless_compatibility.py:594` の projector は v3 field を `pop` し、64桁 hash であることを確認してから v1 へ投影。現在の reason は `no-build` を含む v3 shape に更新。
- `_PRE_WAVE_ORIGINLESS_BASELINE` の v1 exact key 集合と旧 reason は変更しない。
- `test_s8c_acceptance_receipt.py` の v1 fixture、`test_layer3_report.py` の v1 receipt fixtureは変更しない。

検索した範囲では、上記以外に C09/C10 の production call name、receipt top-level exact set、現行 schema literalを固定する追加 pin はありません。契約 JSON、evaluator、producer の既存 Layer 3 call は変更しません。

7. 新規テスト

- `test_trial_registry.py::test_acceptance_no_build_adds_reason_without_layer3_call`  
  正例は6件の `do_build=False` fixture。Layer 3 spy が呼ばれず、receipt に `"no-build"`。負例は reason 追加行を除去し、exact reason assertionを赤にする。
- `test_trial_registry.py::test_acceptance_build_without_cells_fails_before_receipt`  
  正例は実 campaign root を持つ build report。負例は `do_build=True` のまま `cells=[]` にし、`TrialRegistryError` と receipt 未作成を確認する。
- `test_trial_registry.py::test_acceptance_calls_c10_before_accepted_append`  
  正例は verifier が呼ばれ、正常終了後にだけ acceptance が進む。負例は verifier を1 reportで失敗させ、receiptが作られないことを確認する。さらに AST で verifier call が `accepted.append` より前にあることを pin する。
- `test_trial_registry.py::test_v3_receipt_contains_aggregate_cross_binding_digest`  
  正例は6件の per-report digestから再計算した値と top-level fieldが一致。負例は per-report digestの1件を変え、期待値比較を赤にする。
- `test_autonomous_trial_completeness.py::test_read_and_verify_bytes_rejects_changed_bytes`  
  正例は実 regular file と正しい hash。負例は1 byte変更のみで失敗。
- `test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_positive_binds_all_fields`  
  正例はraw response、provider payload/envelope、proposal、campaign lock、WAL、loop state、layer3 reportを実際に配置した build fixture。12 fieldの receipt projectionを確認。
- `test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_rejects_each_reference_mutation`  
  raw path、provider hash、proposal bytes、WAL bench record、artifact ref、source ref、admission decisionを各1項目ずつ mutation。各負例は対応する1行または1 byteの削除・変更で赤になる。
- `test_autonomous_trial_completeness.py::test_verify_s8c_cross_binding_no_build_is_explicitly_unbound`  
  正例は `do_build=False`。`mode="no-build"` と unbound field を返す。負例は同じ report を `do_build=True` に変更し、build input欠落で失敗。
- `test_s8c_acceptance_receipt_v2.py::test_v2_historical_receipt_without_cross_binding_field_still_verifies`  
  正例は旧 v2 key集合。負例は v2に新 fieldだけを追加し、exact keyで失敗。
- `test_s8c_acceptance_receipt_v2.py::test_v3_requires_cross_binding_receipt_sha256`  
  正例は v3 receipt。負例は top-level fieldの1行削除、または hashを64桁未満にして失敗。
- `test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review`  
  C09/C10 が `EVIDENCE_UNDEFINED` / `completion-proof-not-machine-checkable`。
- `test_s8c_preregistration_invariant.py::test_machine_contract_function_names_exist_and_checked_set_is_exact`  
  briefの3件を CHECKS に移し、EXCLUSIONS の完全一致を更新。

8. P1-P5 の評価

- P1 は同意。`_evaluate_c09` と `_evaluate_c10` に SATISFIED の成功枝がなく、最終状態は `EVIDENCE_UNDEFINED`。
- P2 は条件付きで同意。no-build は `"no-build"` reasonで表現できるが、build reportのchain欠落は reasonだけで済ませず `TrialRegistryError` で receipt issuanceを止める。
- P3 は配置には同意。ただし v2の exact schemaを黙って拡張せず、v3へ上げて v1/v2 historical parserを保存する。
- P4 は `do_build=False` について同意。`cells=[]` は `_base_report` には当たるが、`_complete_report` は1 cellを作るため、判定は `do_build` に置く。既存 no-build acceptanceは継続させる。
- P5 は修正が必要。`cells[].campaign_root` の親の親から `output_root` を導く方式は正しいが、build reportのcellが0件なら chainを呼ばずに通してはならない。`do_build=True and cells=[]` は先に拒否する。