以下の行番号は、変更前の現行 worktree を基準とする。編集・pytest 実行は行っておらず、静的計画のみである。

## 変更計画 (A)

1. [`tools/check_ai_provenance.py:137`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:137) の `KnownViolationSpec` に、末尾 field `note: str = ""` を追加する。

   - 既存の三引数 constructor は互換のままにする。
   - `HistoryAudit` と `KnownViolationAudit` は `KnownViolationSpec` 自体を保持しているため、構造変更は不要。
   - 既存6件は既定値 `""` のまま、新規7件目だけ非空にする。

2. [`tools/check_ai_provenance.py:146`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:146) の `_KNOWN_VIOLATION_RULING` は変更せず、[`tools/check_ai_provenance.py:177`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:177) の tuple 末尾へ次を追加する。

   - `commit`: `3f2c43d7580b8c26724d90278589862057508965`
   - `expected_finding_kind`: `MISSING_AI_AGENT`
   - `ruling`: `"worklog(293) 2026-08-07 /rulings"`
   - `note`: `trailer は本文に実在するが、`AI-Agent:` と `Co-Authored-By:` の間の空行で Git が trailer block と認識しない形式崩れ`

   `ruling` はリテラルにする。既存定数の書換えは過去6件の裁定出典を偽り、新定数は1回しか使わない不要な間接化になるためである。テスト側にも独立したリテラルを置き、production 定数を oracle にしない。

3. [`tools/check_ai_provenance.py:181`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:181) の `_known_violation_registry()` では、既存検査後・`registry[spec.commit] = spec` の直前へ `note` 検査を追加する。順序は次のまま固定する。

   1. tuple container 型（184行）
   2. `KnownViolationSpec` entry 型（191行）
   3. `commit` の `str` 型 → full SHA → duplicate（196–210行）
   4. `expected_finding_kind` の `str` 型 →許可種別（211–220行）
   5. `ruling` の `str` 型・非空（221–225行）
   6. 新設する `note` の `str` 型
   7. 非空 `note` の改行検査
   8. registry への登録（226行）

   型検査より先に文字列操作をしない。改行は `spec.note.splitlines() != [spec.note]` 相当で判定し、LF・CR・Unicode line separator を一括して拒否する。違反時はそれぞれ識別可能な `RuntimeError`（例: `invalid note type` / `note contains line break`）にする。

   `_known_violation_registry()` は [`_audit_history():1042`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1042) から history 分岐内で遅延実行され、[`main():2010`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2010) の既存 `try` と [`except:2050`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2050) により rc=2 へ畳まれる。既知一覧の出力前なので、破損時 stdout は空のままになる。`--message-file` は引き続き台帳を読まない。

4. [`tools/check_ai_provenance.py:227`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:227) の後へ、単一行を組み立てる `_known_violation_line(spec)` を追加する。

   - 基本形は現行の `sha=… finding=…`。
   - `spec.note != ""` のときだけ末尾へ ` note={spec.note}` を付ける。
   - [`main():2076`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2076) の rc=1側と [`main():2105`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2105) の rc=0側をともにこの helper 経由へ変える。件数行と出力順は変更しない。

   採用理由は、source コメントだけでは実行時に裁定理由が見えず、全7件必須 `note` では過去6件へ未裁定の説明を遡及追加するためである。既定値付き optional field なら、既存6件と synthetic spec の stdout は逐語不変、新規7件目だけを注記できる。

5. 次の受理条件は一切変更しない。

   - [`_known_violation_audit():997`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:997) の full SHA lookup と1000行の期待種別一致。
   - [`_known_violation_audit():1004`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1004) の entry あたり1件だけの消費。
   - [`_audit_history():1146`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1146) の selected-set stale 判定と1154–1169行の rc=2。
   - [`_commit_range():820`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:820) の `--ancestry-path` 範囲式。
   - forward correction、waiver、`AI-Agent-Correction` の全経路。

## 変更計画 (B)

[`_known_spec():266`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:266) の signature は変更しない。`KnownViolationSpec.note` の既定値で既存 synthetic spec は空注記になるためである。現行呼出しは13箇所あり、signature を変えると13箇所へ波及する。新しい不正 `note` テストでは、意図が明白になるよう `KnownViolationSpec(..., note=bad_note)` を直接構築する。

| 対象 | 変更前に pin していたもの | 変更後に pin するもの | 落ちる検出力 |
|---|---|---|---|
| [`test_known_violation_ledger_is_exactly_six_literal_entries:1323`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1323) | 台帳が厳密に6件で、`3f2c43…` が不在 | `...exactly_seven_literal_entries` へ改名し、7件の順序・full SHA・種別・各 ruling・既存6件の `note=""`・新規注記を独立リテラルで完全一致。`len == 7` と exact commit set も維持 | 「3f2c43…を拒否する」検出だけが裁定どおり消える。無断8件目や旧6件の drift は引き続き exact tuple で落ちる |
| [`test_known_violation_ledger_matches_real_commit_findings:1370`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1370) | 実在6 commit が各期待 finding を生成し、既知6件になる | commits と期待列へ `3f2c43… / missing-ai-agent` を追加し、findings/corrected/waived が空、known が7件であることを pin | なし。実履歴との照合対象が1件増える |
| [`test_empty_registry_restores_all_six_real_findings:1809`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1809) | 台帳を空にすると6件（missing AI 5、missing Codex 1）が復元 | `...all_seven_real_findings` へ改名し、production known=7、空台帳 findings=7、missing AI=6、missing Codex=1 を pin | なし。新 entry が underlying finding を消していないことも追加で検出する |
| [`test_unledgered_3f2c43d7580b_remains_new_and_rc1:1832`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1832) | rc=1、known 行なし、missing finding と通常の「1違反」 | `test_ledgered_3f2c43d7580b_is_known_and_rc0` へ反転。rc=0、当該 full SHA・kind・note を持つ exact `known-violation` 行、`known-violations=1`、`1 件、新規違反なし`、stderr 空を pin | この node 単体では raw finding の stderr 検出を失う。上記「real commit findings」と「empty registry」の2本が raw finding の実在と復元を代替 pin する |

1832行テストの変更後 stdout oracle は次の3行にする。

```text
check_ai_provenance: known-violation sha=3f2c43d7580b8c26724d90278589862057508965 finding=missing-ai-agent note=trailer は本文に実在するが、`AI-Agent:` と `Co-Authored-By:` の間の空行で Git が trailer block と認識しない形式崩れ
check_ai_provenance: known-violations=1
check_ai_provenance: 1 件、新規違反なし
```

[`test_broken_registry_types_are_rc2:1496`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1496) の既存 parametrize には混ぜず、その直後へ独立した `test_broken_registry_note_is_rc2` を追加する。

- `non-str`: `note=None`
- `newline`: `note="first\nsecond"`
- どちらも、対象 commit 自身が `missing-ai-agent` を生成し、他 field は完全に妥当な matching spec とする。
- rc=2、対応する note 診断、stdout 空を pin する。
- matching finding を持つ入力にすることで、note guard を除去した場合は stale 等の後段拒否に救われず rc=0 まで到達し、変異理由を一意にする。

[`test_known_violation_stdout_is_public_on_rc0_and_rc1:1766`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1766) は変更せず残す。`_known_spec()` の空 note に対する現行逐語 stdout を rc=0/rc=1 の両方で pin し、空注記へ誤って `note=` を出す退行を検出する。

## 波及の静的列挙

### 関数・データの caller

- `KnownViolationSpec` の production constructor は現行6箇所（148、153、158、163、168、173行）に新規1箇所を追加する。テスト側は `_known_spec()`、exact-ledger oracle 6箇所、broken-type 2箇所、新設 note テストが直接構築する。
- `_known_violation_registry()` の caller は [`_audit_history():1042`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1042) の1箇所だけ。
- `_known_violation_audit()` の production caller は [`_audit_history():1148`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1148) の1箇所。直接 test caller は `test_known_violation_exact_sha_with_shared_eight_digit_prefix`。
- `_ledger_policy_is_visible()` の caller は [`_audit_history():1160`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1160) の1箇所。
- `_known_violation_line()` の caller は `main()` の rc=1・rc=0出力ループ2箇所だけに限定する。
- `_audit_history()` は `main()` と、次の直接 test caller を持つ: `test_known_violation_ledger_matches_real_commit_findings`、`test_known_violation_requires_exact_full_sha_positive_and_negative_pair`、`test_known_violation_expected_kind_coexists_with_other_new_finding`、`test_known_violation_suppresses_only_one_expected_finding`、`test_empty_registry_restores_all_six_real_findings`、`test_forward_correction_acceptance_is_commit_order_invariant`、`test_known_violation_composes_with_forward_correction`、`test_known_violation_composes_with_waiver`、`test_audit_history_concurrency_high_water_follows_audit_workers` 内の `measure`、`test_audit_history_is_identical_across_worker_counts_and_ancestry`、`test_audit_history_findings_follow_input_order_under_skewed_latency`、`test_audit_history_empty_range_returns_zero_findings`、`test_audit_history_propagates_first_exception_in_input_order`。

`main()` の signature は変えない。AST 静的走査ではテスト内に65 direct call、61 test ownerと `_run_range` がある。全 test owner は次のとおり。

- 台帳・通常監査: `test_broken_registry_types_are_rc2`、`test_broken_short_sha_registry_is_rc2_but_message_file_is_unchanged`、`test_history_gate_starts_at_policy_epoch_and_rejects_followup`、`test_known_violation_missing_expected_finding_diagnoses_regression`、`test_known_violation_off_head_policy_guard_is_stale_rc2`、`test_known_violation_other_kind_does_not_hide_selected_stale`、`test_known_violation_outside_range_is_not_stale_end_to_end`、`test_known_violation_selected_clean_entry_is_stale_rc2`、`test_known_violation_stdout_is_public_on_rc0_and_rc1`、`test_unledgered_3f2c43d7580b_remains_new_and_rc1`。
- CAB/message-file: `test_cab_default_history_is_nonretroactive_and_rejects_post_policy`、`test_cab_explicit_ranges_accept_pre_policy_and_reject_post_policy`、`test_cab_policy_git_error_fails_closed_with_rc2`、`test_cab_policy_introduction_commit_itself_rejects_split_cab`、`test_cab_policy_is_detected_on_range_from_separate_lineage`、`test_cab_policy_remains_effective_after_policy_text_is_deleted`、`test_cab_post_policy_parser_failure_fails_closed_with_rc2`、`test_cab_pre_policy_range_does_not_call_canonical_parser`、`test_message_file_accepts_contiguous_cab_without_policy_history`、`test_message_file_always_rejects_split_cab_without_policy_history`、`test_message_file_gate_uses_staged_paths`、`test_message_file_malformed_merge_head_fails_closed`、`test_message_file_merge_head_read_error_fails_closed`、`test_message_file_parser_failure_fails_closed_with_rc2`、`test_merge_preflight_and_history_count_all_parent_different_resolution`、`test_merge_preflight_and_history_ignore_side_only_implementation_path`。
- correction/waiver: `test_forward_correction_git_object_backend_failure_is_rc2`、`test_forward_correction_message_file_finds_candidate_on_merge_side`、`test_forward_correction_message_file_rejects_missing_target_object`、`test_forward_correction_message_file_rejects_second_candidate`、`test_forward_correction_message_file_rejects_target_outside_parent_ancestry`、`test_forward_correction_message_file_success_is_preflight_only`、`test_regular_message_file_acceptance_does_not_require_correction_target`、`test_waiver_message_file_docs_only_change_is_not_counted`、`test_waiver_message_file_gate_exempts_staged_implementation_paths`。
- site/dispatch: `test_compute_and_other_sites_audit_locally`、`test_default_login_admission_uses_login_headroom_grant_budget`、`test_dispatch_exception_is_folded_into_infra_rc`、`test_failed_provenance_scope_oom_attestation_refuses_with_infra_rc`、`test_force_dispatch_login_bypasses_provenance_headroom_and_queue`、`test_force_dispatch_provenance_compute_and_other_audit_locally`、`test_force_dispatch_provenance_suspect_still_returns_infra_rc`、`test_login_history_audit_dispatches_to_compute_and_returns_child_rc`、`test_login_local_scope_returns_child_rc_without_dispatch`、`test_login_message_file_is_dispatch_exempt`、`test_login_message_file_returns_before_admission_gate`、`test_previous_provenance_cap_estimate_dispatches_without_local_scope`、`test_provenance_cap_oom_changed_tree_does_not_dispatch`、`test_provenance_cap_oom_dirty_before_unchanged_after_dispatches_once`、`test_provenance_headroom_and_queue_four_quadrants`、`test_provenance_headroom_short_queue_unavailable_cap_oom_stops`、`test_provenance_headroom_short_queue_unavailable_zero_budget_stops`、`test_provenance_login_headroom_import_failure_dispatches`、`test_provenance_queue_state_import_failure_is_dispatch_available`、`test_provenance_releases_budget_lease_on_interrupt`、`test_provenance_scope_infra_does_not_become_audit_failure`、`test_provenance_without_range_uses_operation_and_releases_lease`、`test_suspect_history_audit_never_enters_local_admission`、`test_suspect_history_audit_refuses_with_infra_rc_without_dispatch`、`test_suspect_history_refusal_observes_queue_once_and_includes_hint`、`test_without_force_dispatch_provenance_login_with_headroom_runs_local`。

production の直接入口は [`__main__:2121`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2121)。CLI launcher は `tools/task_run_check.py`、`tools/pegasus/dispatch_compute.py`、`tools/dev_wave_land.py` の message-file preflightで、いずれも `known-violation` recordを parseしていない。

### 共有 helper / fixture

- `_known_spec()` の既存13 caller: `test_known_violation_requires_exact_full_sha_positive_and_negative_pair`、`test_known_violation_exact_sha_with_shared_eight_digit_prefix`、`test_broken_short_sha_registry_is_rc2_but_message_file_is_unchanged`、`test_known_violation_expected_kind_coexists_with_other_new_finding`、`test_known_violation_suppresses_only_one_expected_finding`、`test_known_violation_selected_clean_entry_is_stale_rc2`、`test_known_violation_missing_expected_finding_diagnoses_regression`、`test_known_violation_other_kind_does_not_hide_selected_stale`、`test_known_violation_outside_range_is_not_stale_end_to_end`、`test_known_violation_off_head_policy_guard_is_stale_rc2`、`test_known_violation_stdout_is_public_on_rc0_and_rc1`、`test_known_violation_composes_with_forward_correction`、`test_known_violation_composes_with_waiver`。
- 新 note テストは既存 `_init_repo()` / `_commit()` と pytest built-in の `tmp_path`、`monkeypatch`、`capsys` を使う。
- `rg -n '@pytest\.fixture' orchestrator/tests/test_check_ai_provenance.py` は hit 0 件。repository-local fixture はない。

### stdout 依存

既存テストで `known-violation` stdout に依存するものは全3本。

- `test_known_violation_stdout_is_public_on_rc0_and_rc1`: exact stdout。空 note の互換 pin として変更しない。
- `test_unledgered_3f2c43d7580b_remains_new_and_rc1`: record 不在を pin。新仕様へ反転し、注記付き exact record を pin する。
- `test_broken_short_sha_registry_is_rc2_but_message_file_is_unchanged`: rc=2時の record 不在を pin。変更しない。

検索結果:

- `rg 'check_ai_provenance: known-violation '` は production 2箇所、上記 exact test 2箇所だけ。
- `rg 'known-violations='` は production 2箇所、同 test 2箇所、`docs/provenance/audit.md` 1箇所だけ。
- `rg 'KNOWN_PROVENANCE_VIOLATIONS|known-violation' --glob '*.py'` から production/test 2ファイルを除外すると hit 0 件。
- `rg 'worklog\(293\) 2026-08-07 /rulings' --glob '!output/**'` は現状 hit 0 件。
- `rg 'note=' tools/check_ai_provenance.py orchestrator/tests/test_check_ai_provenance.py` は現状 hit 0 件。

## 変異候補

| 変異位置 | 無効化する層と赤くなる test node | 前後の別拒否層 | 赤理由の一意性 |
|---|---|---|---|
| [`tools/check_ai_provenance.py:177`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:177) の新 entry を削除／SHA drift | `test_ledgered_3f2c43d7580b_is_known_and_rc0` | 当該 commit に correction/waiver はなく、他6 entryもSHA不一致 | raw missing findingが新規へ戻り rc=0→1、という1理由 |
| 新設 `_known_violation_line()` の note suffix を削除 | 同 `test_ledgered_3f2c43d7580b_is_known_and_rc0` | 台帳照合とrcは正常に通り、別の出力層はnoteを補わない | exact stdout の note 欠落だけで赤 |
| [`_known_violation_registry():221`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:221) 後の note 型検査を無効化 | `test_broken_registry_note_is_rc2[non-str]` | 入力commitは期待 finding を持ち、他fieldも妥当なので stale/normal violation はない | rc=2→0だけに帰属 |
| 同所の改行検査を無効化 | `test_broken_registry_note_is_rc2[newline]` | 同上。formatter は改行入り文字列をそのまま出せるため後段拒否なし | rc=2→0と壊れた stdout recordだけに帰属 |
| [`_known_violation_audit():1004`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1004) の一回消費 guard を無効化 | `test_known_violation_suppresses_only_one_expected_finding` | synthetic inputには同種2件以外の拒否要因なし | 2件目の `duplicate-kind` が消える1理由 |
| [`_audit_history():1154`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1154) の stale raise を無効化 | `test_known_violation_missing_expected_finding_diagnoses_regression` | selected commitは通常greenで correction/waiver なし | stale rc=2がrc=0になる1理由 |

候補から外すもの:

- `KnownViolationSpec.note` の既定値自体を非空へ変える変異は、既存6 entry・13個の `_known_spec()` caller・stdout exact testを同時に変え、赤理由が分散するため外す。
- `_known_violation_registry()` 呼出し全体を削除する変異は、型、SHA、kind、stale、entry照合を一度に無効化するため外す。
- rc=0/rc=1の出力式を別々に変異させる案は、共通 `_known_violation_line()` へ集約する設計により不要になる。

full SHA と期待種別については、既存の `test_known_violation_requires_exact_full_sha_positive_and_negative_pair`、`test_known_violation_exact_sha_with_shared_eight_digit_prefix`、`test_known_violation_expected_kind_coexists_with_other_new_finding`、`test_known_violation_other_kind_does_not_hide_selected_stale` を変更せず保持する。

## リスクと未解決

- (P1)〜(P4) に反対はない。
- (P1): optional `note` と条件付き出力が、既存6件の逐語互換と新規注記の公開を両立する。source コメントのみ、全件必須はいずれも不採用。
- (P2): 既存裁定定数を維持し、新裁定はentry内リテラルにする。
- (P3): 4テストは削除せず、仕様変更部分だけを正方向へ反転する。1832行で失うraw-error pinは他2テストで代替する。
- (P4): `str` → line-break の順で fail-closedにする。`splitlines()` によりCR/LF以外の行区切りも拒否する点だけ、provisional の意図を狭めず強化する。
- D221は三要素schemaと記述しているため、optional `note` 追加の設計記録は親の decisions fragmentで補足が必要。`docs/provenance/audit.md` のrc/stale契約と `docs/provenance/correction.md` は実装上変更不要で、docs編集は親のscopeとする。
- repository内に record parserは見つからなかったが、未記録の外部parserが固定field数を仮定している可能性は残る。空note出力を逐語不変にし、変更面を新規1 entryへ限定して緩和する。
- pytest・full監査とも未実行であり、合格は主張しない。実測は親が行う。

## 総括

- 台帳へ `3f2c43… / missing-ai-agent` を7件目として追加し、別裁定rulingと単一行noteを持たせる。
- noteは既定空、型・改行をhistory分岐内で検査し、破損は既存経路でrc=2にする。
- stdoutは共通formatterでrc=0/1とも同じ条件付きnote形式にする。
- 既存4テストは7件仕様へ反転し、raw finding・exact台帳・注記公開を別々にpinする。
- 履歴、correction、範囲式、full SHA×kind、一entry一件、staleの各契約は変更しない。