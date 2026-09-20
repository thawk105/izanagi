## 実装結果

**実装済み・未実走です。closed とはしません。** 所有する2ファイルだけを変更しました。docs 編集・git 操作・commit・dispatch は行っていません。

以下、H は [production module](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-impl/orchestrator/campaign/s8b_holdout_admission.py)、T は [admission test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-impl/orchestrator/tests/test_s8b_holdout_admission.py) を指します。

| ファイル | 差分 | 内容 |
|---|---:|---|
| H | +133／−25行 | per-call projection memo、main ledger の遅延共有、既存 wrapper 維持 |
| T | +414／−0行 | 補助 fixture 4本、新規 test 10本・静的展開99ケース |

変更前 module の指定 SHA-256 を確認し、編集前の H と逐語一致しました。

旧実装の受理・拒否挙動は、target の完全検査→全 marker→全 A 行の順です。その後、marker 不在と M+A+ は `None`、未完了の M+A−は canonical marker、completed の M+A−は `"completed attempt cannot be reissued"` で拒否します。この順序を維持しています。

context は候補関数内で生成します。memo 登録は marker equality 成功後だけです。hit でも shape・schema・role・digest・attempt_id・coverage・constructor・文書全体の equality を検査します。main 行列は従来の読取位置で初めて読み、`None` と空リストを区別します。

## 検査結果と未実走項目

指定コマンド：

```text
python3 -m pytest orchestrator/tests/test_s8b_holdout_admission.py -q -p no:cacheprovider -x
```

`pegasus02` の PreToolUse `guard_bash` が、ログインノード上の pytest 直接起動として拒否しました。**実走 nodeid なし、passed 0／failed 0、pytest 未起動**です。99ケースは AST による静的件数で、collection 結果ではありません。

実施した静的確認：

- 両変更ファイルの構文解析成功。
- 全既存関数の signature が base と AST 一致。
- module レベルの既存文・定数・`__all__` が AST 一致。
- 候補関数は、context の生成・受渡しを除くと base と AST 一致。
- 両 schema の claim→main 検査は、遅延読取の配線を除くと base と AST 一致。
- constructor に渡す authority field と評価順が一致。
- 既存 floor consume／generation message literal の保持を確認。
- 後述の変異 anchor はすべて H 内で出現数1を確認。

新規 test の nodeid は、以下の T 接頭辞で記します。すべて未実走です。

| 略号 | `T::` に続く nodeid | 静的ケース数 |
|---|---|---:|
| N1 | `test_cut6_multiclaim_consumption_sequence` | 1 |
| N2 | `test_cut6_later_marker_rejected[claim-mismatch / extra-key / noncanonical-filename / attempt-not-covered]` | 4 |
| N3 | `test_cut6_later_attempt_row_rejected[claim-mismatch / orphan / duplicate]` | 3 |
| N4 | `test_cut6_claim_error_precedes_main_read` | 9 |
| N5 | `test_cut6_main_validation_scope` | 9 |
| N6 | `test_cut6_projection_once_per_claim_per_call[claim / main]` | 2 |
| N7 | `test_cut6_marker_directory_errors[absent / directory / symlink]` | 3 |
| N8 | `test_cut6_filters_only_after_reading_bytes` | 8 |
| N9 | `test_cut6_claim_reader_precedes_main` | 24 |
| N10 | `test_cut6_main_reader_and_coverage_precedence` | 36 |

`/` 区切りは個別 parameter の列挙です。N4・N5・N9・N10 は v1 claim／v2 claim／generation を含みます。

制約 meta-test 候補は `rg` で参照ファイルを列挙し、AST・literal・公開契約の検査を確認しました。以下も guard の制約により未実走です。

| ファイル | 関係する nodeid／対象 |
|---|---|
| T | `test_all_neutral_projection_sites_use_complete_signature_conditions` |
| T | `test_floor_reservation_signature_has_no_approval_argument` |
| T | `test_resume_api_has_no_caller_journal_or_manifest_self_report` |
| T | `test_cell_admission_projects_current_claim_digest_without_default` |
| T | `test_floor_marker_capability_accepts_exact_current_marker_under_lock` |
| T | `test_floor_recovery_query_signatures_expose_only_admission_verdict_inputs` |
| T | `test_inspector_public_contract_and_guarantee_boundary` |
| T | `test_scheduler_accounting_authority_policy_literal_is_independently_asserted` |
| `test_s8b_attempt_registry.py` | `test_floor_campaign_does_not_import_adapter_and_guard_has_positive_control` |
| `test_ccbench_spawn_sites.py` | `test_reviewed_ccbench_measurement_launches_use_bounded_sites` |
| `test_check_docs.py` | `test_r33_source_contract_binds_entry_to_observation_roles_dictionary` |
| 同上 | `test_r33_source_contract_ignores_entry_in_docstring_within_observation_roles` |
| 同上 | `test_r33_source_contract_ignores_role_literal_in_docstring` |
| 同上 | `test_r33_role_contract_generation_round_allocation_mismatch_fails` |
| 同上 | `test_r33_role_decision_pin_accepts_exact_pending_fragment`、`test_r33_role_decision_pin_requires_canonical_or_pending_contract` |

`tools/check_docs.py::_check_n_pilot_role_decision_pin` は読取確認のみです。R33 の module 定義は AST 不変ですが、checker の実走結果はありません。差分 probe・変異実走・consumer test・性能測定も未実走です。

## 受理集合の対応表

一致の対象は、裁定どおり**一呼出し中に読取対象・読取結果が安定した root**です。以下は plan の対応表の各検査に対する新位置です。行番号は変更後 H。

| 検査 | 新位置・維持方法 |
|---|---|
| target 先行検査 | 5340。directory 列挙前 |
| marker exact shape・schema・role | v1:4712–4719、generation:4869–4879。毎回 |
| digest／attempt_id の型・値 | 4720–4721／4880–4884。memo lookup 前 |
| claim reader | 4748／4914。miss で既存 reader |
| claim shape・key・digest／identity | 4749–4777／4917–4957。原順序 |
| coverage | miss:4778–4785／4968–4977、hit:4729／4892 |
| entry_kind・seams | 4786–4792／4958–4967。v1 は coverage 後、generation は前 |
| main bytes／JSON | 4795–4798／5045–5049 → 4685–4688。遅延共有 |
| v1 全 floor 行 shape・key・digest | 4799–4814。miss ごとに全対象行 |
| main 行数≠1 | 4815–4818／5054–5057 |
| generation main shape | 4982–4985。一意選択した行だけ |
| manifest SHA・main equality | 4820–4842／4986–5017。値の出所も不変 |
| constructor | 4731／4896。miss・hit とも実行 |
| marker equality／MUT-A2 | 4735／4899。成功後にのみ memo 登録 |
| directory 不在・unsafe entry | 5359–5367 |
| marker reader・schema／role filter | 5368–5373。reader が先 |
| canonical filename | 5377–5378 |
| marker identity 重複 | 5382–5383 |
| A reader・filter・完全再導出 | 5387–5395 |
| A identity 重複 | 5399–5400 |
| A の marker 不在 | 5401–5403 |
| A≠marker | 5404–5405 |
| target 不在 | 5408–5411。全走査後に `None` |
| target≠canonical_target | 5412–5413 |
| target の A 行あり | 5414–5415。completed より先に `None` |
| completed／MUT-A6 | 5416–5418 |
| 正常 M+A− | 5419 |

走査部分と miss の検査部分は、前節の AST 比較で確認しました。新旧の実行結果を比較する差分 probe は、この author では実施していません。

## 被覆台帳

「新規」「既存」はテストコードの対応を示し、このターンでの成功実測を意味しません。

| 不変条件・検査項目 | 対応／限界 |
|---|---|
| I1：複数 claim、同 claim の複数 attempt、M−／M+A−／M+A+ | 新規 N1 |
| I1：target claim エラーが main より先 | 新規 N4・N9・N10。main 読取0回も観測 |
| I1：v1 coverage→entry/seams、generation entry/seams→coverage | 新規 N4 |
| I1：claim reader 読取不能・非 regular・一行条件・非 canonical | 新規 N9 の `unreadable`・`symlink`・`no-lf`・`two-lines`・`noncanonical` |
| I1：`_strict_json` の構文不正・重複 key・非 object | 新規 N9 の `json`・`duplicate-key`・`not-object` |
| I1：UTF-8 不正・非有限数の各専用入力 | **未被覆**。reader 本体は不変 |
| I1：claim shape・key・digest/identity の各不正 | 今回の候補関数向け新規負例では**未被覆**。移動部分の AST 一致のみ |
| I1：attempt_ids の型・要素型・重複 | **未被覆**。未登録 membership は N2・N4・N10 |
| I1：main byte上限・末尾LF・空行・JSON・非regular・読取不能 | 新規 N10。各例外と coverage 優先順位を両方固定 |
| I1：main 非canonical bytes | 新規 N5 `[noncanonical-*]` |
| I1：v1 の無関係 floor 行 shape、generation の無関係行非検査 | 新規 N5 `[unrelated-shape-*]` |
| I1：v1 無関係行の key／digest 検査 | 専用負例は**未被覆**。全行 loop の AST 一致 |
| I1：main 件数0／2、generation 選択行 shape | 専用負例は**未被覆** |
| I1：manifest 値・値の出所 | 専用負例は**未被覆**。v1 は main、generation は claim のまま |
| I1：main≠claim | 新規 N5 `[records-v1]`・`[records-v2]`・`[records-generation]` |
| I2：後段の非 target marker、MUT-A2・extra key | 新規 N2、既存 `test_cut6_recovery_requires_exact_marker_rederived_from_claim` |
| I2：非canonical filename | 新規 N2 `[noncanonical-filename]`。複製せず改名 |
| I2：未登録 attempt の hit coverage | 新規 N2 `[attempt-not-covered]` |
| I2：unsafe entry・directory 不在 | 新規 N7 |
| I2：marker の schema／role filter 前に bytes 検査 | 新規 N8。正常な対象外文書は無視、不正 bytes は拒否 |
| I2：A ledger の schema／role filter 前に bytes 検査 | 新規 N8 |
| I2：marker reader のその他の不正 bytes | claim reader と共通実装だが、marker 専用入力では**未被覆** |
| I2：後段 A 行の改竄・orphan・重複 | 新規 N3。改竄は完全再導出時の message を期待 |
| I2：A≠marker | **静的到達不能**。同 identity の双方が同じ authority 文書へ再導出される |
| I2：marker identity 重複 | **静的到達不能**。別名なら先に canonical filename で拒否 |
| I3：target≠canonical_target | **静的到達不能**。同 identity の再導出結果は同一 |
| I3：marker 不在 | 新規 N1、既存 `test_cut6_marker_absence_does_not_invent_requested_attempt_row` |
| I3：M+A−回復・同 attempt 再発行・lock | 新規 N1、既存 `test_cut6_rebuilds_attempt_row_and_reissues_same_attempt_under_lock` |
| I3：M+A+ | 新規 N1、既存 `test_cut6_m_plus_a_plus_rejects_before_any_new_marker_write` |
| I3：completed | 既存 `test_cut6_completed_session_forbids_reissue_of_same_attempt` |
| I4：claim ごと1回、main 全体1回、marker 全件読取 | 新規 N6。実物に委譲する観測 wrapper |
| I4：次の呼出しで再読、claim／main 改竄拒否 | 新規 N6 `[claim]`・`[main]` |
| I4：失敗／部分 projection を保存しない | 登録位置を静的確認。専用実走はなし |
| I5：write 経路・書式・filename constructor | 既存定義の AST 不変。新規 N1、既存回復・single-use test |
| I5：`__all__`・公開／既存 wrapper signature | base との AST 一致。既存公開契約 meta-test は未実走 |

到達不能とした3検査は production に残しています。authority helper を偽装する負例は追加していません。

## 変異 anchor

以下の `old` は **JSON 文字列として表記**しています。デコード後が逐語 anchor です。全件 H 内で一意と静的確認しました。

| ID | `old` |
|---|---|
| M1 | `"    expected = _canonical_measurement_generation_floor_attempt_document(\n        attempt_id=attempt_id, **projection.document_fields,\n    )\n"` |
| M3 | `"    elif attempt_id not in projection.attempt_ids:\n        raise HoldoutAdmissionError(\n            \"floor measurement generation claim attempt coverage is invalid\"\n        )\n"` |
| M4 | `"        if path != _floor_canonical_marker_path(root, canonical):\n"` |
| M5 | `"        if identity in ledger_by_identity:\n"` |
| M6g | `"    if main != expected_main:\n        raise HoldoutAdmissionError(\n            \"floor measurement generation ledger differs from its claim\"\n        )\n"` |
| M6v | `"    if main != expected_main:\n        raise HoldoutAdmissionError(\"floor consume main ledger differs from its claim\")\n"` |
| M7 | `"    if completed_attempt:\n"` |
| M8 | `"    context = _FloorAttemptRecoveryContext()\n"` |
| P0 | `"        identity = (\n            str(canonical[identity_field]), str(canonical[\"attempt_id\"]),\n        )\n        if identity in ledger_by_identity:\n"` |

全変異とも実走なしです。以下は KILL／SURVIVED の静的期待であり、実測結果ではありません。

| ID・新位置 | 対応 nodeid | 最初の拒否・単一理由性／新規検出力 |
|---|---|---|
| M1・4896 | N2 `[claim-mismatch]` | 非target・A不在。hit で campaign を信用すると equality を通過し、後段で同入力を拒否する層はない。既存 marker 改竄 test も別 message で赤になり得るため、新規専有とは数えない |
| M3・4892 | N2 `[attempt-not-covered]` | 妥当な文字列・canonical filename。coverage 削除後に同入力を拒否する層なし |
| M4・5377 | N2 `[noncanonical-filename]` | 改名のみ。重複 identity による二重帰属なし |
| M5・5399 | N3 `[duplicate]` | canonical A 行を二重化。orphan・文書不一致なし |
| M6g・5014 | N5 `[records-generation]` | records だけ変更。shape・identity・manifest・marker は正常。main equality に帰属 |
| M6v・4841 | N5 `[records-v1]`、`[records-v2]` | 同上。v1 分岐の main equality に帰属 |
| M7・5416 | 既存 `test_cut6_completed_session_forbids_reissue_of_same_attempt` | M+A−で completed に到達。既存検出力であり、新規に数えない |
| M8・5339 | N6 `[claim]`、`[main]` | 呼出し間保持は2回目の読取回数で先に検出。改竄拒否も記述済みだが、同一 test 内では回数 assertion が先行する。改竄拒否だけの単一帰属とはしない |
| P0・5396 | — | canonical 成功後の値は文字列。`str(...)` 除去は静的に等価、SURVIVED 期待 |

M1 は hit 限定の上書きとして spec 化する必要があります。M8 の anchor は局所生成箇所であり、保持先の導入方法は親の変異 spec に委ねます。

## 所有外への波及確認

| 面 | 静的確認 |
|---|---|
| `_canonical_floor_attempt_ledger_row` | H:5155 の consumption identity、H:5784 の registry trigger からの呼出しを維持。context なしで毎回完全導出 |
| `_measurement_generation_main_ledger_row` | H:5162 と T:2264 の既存 caller を維持 |
| generation 専用 wrapper | signature 維持、`context=None` で完全導出 |
| floor campaign | `s8b_floor_campaign.py:5988` の consume 関数参照、6083 の cut6 query 参照、8959 の直接 consume 呼出し |
| oracle n-pilot | floor の2関数への直接 caller はなし。1324–1325、1399、1410 は別の `consume_n_pilot_attempt_ticket`。変更なし |
| 共有 fixture | `s8b_floor_evidence_fixture.py::build_floor_admission_evidence` を再利用。変更なし |
| consumer test | 下記群を未実走の影響確認対象として列挙 |

`test_s8b_floor_campaign.py` の主要対象：

- `test_measure_runtime_error_records_launch_failure`
- `test_resume_runner_replays_only_admission_proved_cut6_m_plus_a_minus`
- `test_certified_cut6_existing_marker_competing_probe_aborts_without_result`
- `test_resume_forward_only_skips_completed_and_crashed_seqs`
- `test_resume_does_not_reissue_retry_slot_after_retry_start_crash`
- `test_cut6_replay_rejects_truthy_non_bool_verdict`
- `test_resume_runner_produces_one_retry_from_admission_selected_recovery`
- `test_verified_recovery_emits_only_one_invalid_retry_ordinal`
- `test_certified_campaign_rejects_unissued_consumption_marker`
- `test_v5_prefix_covers_every_consumed_non_competing_session`
- `test_competing_pre_probe_consumes_no_marker_and_writes_no_registry_row`

## 総括

変更ファイルは H と T のみです。production は **+133／−25行**、test は **+414行**で上限内です。

変更した既存関数は `_canonical_floor_attempt_ledger_row`、`_canonical_measurement_generation_floor_attempt_ledger_row`、`_measurement_generation_main_ledger_row`、`_floor_attempt_recovery_candidate_locked` の4本です。

追加 helper／型は以下です。行数は定義本体の範囲で、移動した既存検査を含みます。

| 追加名 | H行 | 行数 |
|---|---:|---:|
| `_FloorAttemptClaimProjection` | 4671 | 5 |
| `_FloorAttemptRecoveryContext` | 4678 | 11 |
| `_canonical_floor_attempt_ledger_row_with_context` | 4701 | 39 |
| `_derive_floor_attempt_projection` | 4742 | 109 |
| `_canonical_measurement_generation_floor_attempt_ledger_row_with_context` | 4863 | 43 |
| `_derive_measurement_generation_floor_attempt_projection` | 4908 | 121 |
| `_measurement_generation_main_ledger_row_with_context` | 5041 | 18 |

T には `_issued_cells_for_recovery`、`_recovery_candidate`、`_recovery_marker_set`、`_recovery_schema_case` と、上記 N1〜N10 を追加しました。既存 test の期待値は変更していません。

**実走 nodeid なし、passed 0／failed 0、未起動です。** admission 全件、新規99ケース、制約 meta-test、consumer test、差分 probe、変異、性能測定は未実走です。受理集合不変の確認は、上の「受理集合の対応表」の各新位置と AST 比較による静的確認までです。「被覆台帳」に未被覆項目を、「変異 anchor」に一意な旧文字列と帰属上の限界を記載しました。

lock を無視する書込みや一過性 I/O を含む実行履歴同値は保証しません。marker 全件読取、A ledger 全読、constructor・比較・sort の二乗成分は残ります。claim 数が attempt 数とともに増える場合、projection 部分にも二乗性が残ります。速度改善は未測定です。

指定 pytest は PreToolUse `guard_bash` により、Pegasus ログインノード上の直接起動として拒否されました。依頼の制約に従い dispatch せず、**実装済み・未実走**として引き渡します。