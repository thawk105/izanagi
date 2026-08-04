## 1. 現状の実測

基準は `HEAD=50db269ae2cb6aa6ef14b8179b0f71f0c4074e63`。以下は静的実測であり、pytest は実行していない。

1. provider 注入

   - `run_trial()` は `providers`、`drive`、`preview` を公開引数として受ける（`orchestrator/campaign/p3_autonomous_workload_trial.py:1518-1534`）。
   - 現在拒否されるのは `allow_pegasus_compute_transport=True` かつ `providers is not None` の組合せだけ（同 `:1547-1554`）。
   - それ以外では注入 provider を `dict(providers)` として採用し（同 `:1636-1647`）、注入 `preview` と `drive` をそのまま `_finish_trial()`、`_run_workload()` へ渡す（同 `:1659-1678`, `:1087-1105`）。実際の呼出点は `preview(...)` が `:1377`、`drive(...)` が `:1451-1461`。
   - したがって transport opt-in でない現行経路では三つとも素通りする。これは既存の fixture テストが積極的に利用している。

2. role 間 session 共有

   - `ClaudeProjectedRoleProvider` は instance ごとの `_observed_session_ids` を作る（`orchestrator/campaign/claude_projected_provider.py:173-178`）。
   - 重複検査と記録もその instance 内だけ（同 `:290-296`, `:327`）。
   - `_provider_set()` は planner/coder/auditor/critic ごとに別 instance を生成する（`orchestrator/campaign/p3_autonomous_workload_trial.py:943-959`）。
   - よって同じ `session_id` を planner instance と coder instance が返しても、双方のローカル集合では初出となり素通りする。現行テストに cross-role 負例はない。

3. 未予約 token

   - `run_trial()`、`_finish_trial()`、`main()` のいずれにも P5 用 token は存在しない（同 `:1044-1065`, `:1518-1535`, `:1697-1725`）。したがって未発行・再使用を判定する入口自体がない。
   - `CoderBuildAuthority` は別目的の先例である。sealed constructor は `orchestrator/campaign/build_admission.py:117-126`、argparse action 発行は `:253-259`、未発行・二重使用拒否は `:292-310`。ただし `run_trial()` で要求されるのは `do_build=True` の場合だけ（`p3_autonomous_workload_trial.py:1565-1568`）で、P5 formal 経路や provider/session には効かない。

## 2. 設計

新規 leaf は `orchestrator/campaign/formal_trial_gate.py` とする。`reservation.py`、`session_ledger`、既存の多数の `*_admission` と二義化しない名称である。

予定 API は次のとおり。

```python
FORMAL_TRIAL_GATE_RECEIPT_SCHEMA = "formal-trial-gate-receipt/v1"

class FormalTrialGateError(RuntimeError): ...

class FormalTrialGateVerdict(str, Enum):
    ACCEPT = "accept"
    REJECT_UNDECIDABLE = "reject-undecidable"
    REJECT_PROVIDER_KIND = "reject-provider-kind"
    REJECT_PROVIDERS = "reject-providers"
    REJECT_DRIVE = "reject-drive"
    REJECT_PREVIEW = "reject-preview"

@dataclass(frozen=True, slots=True, init=False)
class FormalTrialGateToken:
    _nonce: str

class CrossRoleSessionTracker:
    def observe(self, *, role_name: str, session_id: str) -> None: ...

@dataclass(frozen=True, slots=True, init=False)
class FormalTrialGateContext:
    session_tracker: CrossRoleSessionTracker
    def as_receipt(self) -> dict[str, object]: ...

def add_formal_trial_provider_argument(
    parser: argparse.ArgumentParser,
    *,
    choices: Sequence[str],
    provider_dest: str = "provider",
    token_dest: str = "formal_trial_gate_token",
) -> None: ...

def evaluate_formal_trial_gate(
    *,
    provider_kind: str,
    providers_injected: bool,
    drive_is_builtin: bool,
    preview_is_builtin: bool,
) -> FormalTrialGateVerdict: ...

def require_formal_trial_gate(
    token: FormalTrialGateToken | None,
    *,
    provider_kind: str,
    providers_injected: bool,
    drive_is_builtin: bool,
    preview_is_builtin: bool,
) -> FormalTrialGateContext | None: ...

def validate_formal_trial_gate_receipt(
    value: object,
) -> dict[str, object]: ...
```

設計要点は次のとおり。

- `evaluate_formal_trial_gate()` は副作用のない pure evaluator。exact `bool` でない入力も `REJECT_UNDECIDABLE` とする。
- `require_formal_trial_gate()` が薄い stateful wrapper。token が `None` なら直ちに `None` を返し、現行挙動を保存する。
- token 提示時は exact 型、同一 process の private argparse action による発行、未使用を順に検査し、提示時点で claim する。後続 seam 検査が拒否しても token は再利用できない。
- `CrossRoleSessionTracker` は `session_id -> role_name` を process 内で共有し、二度目の観測を拒否する。durable ledger、CAS、再起動後 replay は持たない。
- receipt は nonce を含めず、次の exact body とする。

```json
{
  "schema_version": "formal-trial-gate-receipt/v1",
  "receipt_id": "<独立に生成した lowercase 64-hex>",
  "token_policy": "provider-parser-action-process-local-single-use",
  "provider_policy": "owned-claude-projected-provider-set",
  "drive_policy": "producer-builtin",
  "preview_policy": "producer-builtin",
  "role_session_policy": "shared-process-local-cross-role-tracker"
}
```

`receipt_id` は token nonce とは別物であり、run-start/report の照合を非恒真にするための相関 ID に限る。認証や durable authority とは名乗らない。

PROV 裁定案:

- PROV-1: 採用。token、seam evaluator、session tracker、receipt validator を一 leaf に閉じる。
- PROV-2: 採用。ただし「main が発行」を、`--provider claude-headless` を処理する private argparse action が自動発行する形に具体化する。新しい opt-in flag は作らない。fixture 選択時は token を発行しない。
- PROV-3: 採用。token 非提示の programmatic `run_trial()` は provider/drive/preview 注入を含め現行保存。token 提示時だけ三 seam を identity で閉じる。
- PROV-4: 採用。`_provider_set()` が一つの `CrossRoleSessionTracker` を四 provider に渡す。
- PROV-5: 採用。formal consumer は receipt の両側存在、exact schema、`receipt_id` を含む一致、`provider=="claude-headless"` との整合だけを検査する。receipt を必須化する新 flag・全 Claude artifact への遡及必須化はしない。

## 3. 配線

1. `orchestrator/campaign/p3_autonomous_workload_trial.py`

   - `:36-112`: direct-script/package の各 import 分岐から新 leaf を同一 module identity で読む。既存の top-level `campaign.build_admission` import に無条件で混ぜない。
   - `:560-580`: `_preview` 定義後に `_BUILTIN_PREVIEW = _preview`、`_BUILTIN_DRIVE = trigger.drive_iteration` を固定し、`run_trial()` の default と formal identity 検査の双方で使う。
   - `:913-965`: `_provider_set(..., cross_role_session_tracker: CrossRoleSessionTracker | None = None)` を追加。非 `None` なら exact 型かつ `kind=="claude-headless"` を要求し、四 provider に同一 object を渡す。
   - `:1044-1065`: `_finish_trial(..., formal_trial_gate: FormalTrialGateContext | None = None)` を追加。
   - `:1158-1199`: formal context がある場合だけ report と run-finish 前の journal projectionに receipt を記録する。実際の journal 宿主は後述の run-start とし、run-finish の key は増やさない。
   - `:1518-1569`: `formal_trial_gate_token: FormalTrialGateToken | None = None` を追加。既存引数検査後、`run_root.mkdir()` より前に `require_formal_trial_gate()` を呼ぶ。
   - `:1610-1621`: formal 時だけ `run-start.formal_trial_gate_receipt` を追加。
   - `:1636-1647`: formal context の共有 tracker を `_provider_set()` に渡す。
   - `:1659-1678`:同じ sealed context を `_finish_trial()` に渡す。
   - `:1697-1704`:現在の `--provider` 定義を `add_formal_trial_provider_argument()` に置き換える。
   - `:1759-1775`: parser が作った `args.formal_trial_gate_token` を `run_trial()` へ渡す。
   - `MAX_APPROVED_GENERATIONS`（`:131-132`）と `_validate_generation_budget()`（`:247-256`）は変更しない。

2. `orchestrator/campaign/claude_projected_provider.py`

   - `:22-35`: `CrossRoleSessionTracker` と `FormalTrialGateError` を import。
   - `:96-124`: constructor に `cross_role_session_tracker: CrossRoleSessionTracker | None = None` を追加し、artifact directory 作成前に exact 型を検査する。
   - `:173-178`: instance-local `_observed_session_ids` は残し、共有 tracker を別 field に保持する。
   - `:290-327`:現行の instance-local 検査後、成功 envelope を返す直前に共有 tracker の `observe()` を呼ぶ。tracker 拒否は `PredictionRunnerError` に cause-chain 付きで変換する。

3. `orchestrator/campaign/autonomous_trial_completeness.py`

   - `_check_run_envelope()` の `:347-423` に optional receipt 検査を追加する。
   - journal/report の片側だけに field がある場合、schema/key/value/receipt-id が不正な場合、二つの有効 receipt が一致しない場合、receipt があるのに provider が `claude-headless` でない場合を拒否する。
   - 両方に field がない既存 artifact は従来どおり受理する。
   - `SCHEMA_VERSION` / `REPORT_SCHEMA_VERSION` は v2 のまま。receipt 自身が v1 schema を持つ。

変更前後の受理集合:

| 入力 | 変更前 | 変更後 |
|---|---|---|
| token なしの `run_trial()` | 現行どおり | 完全に同じ |
| token なし＋注入 providers/drive/preview | 受理 | 受理のまま |
| main の fixture | 受理 | token 非発行、受理のまま |
| main の claude-headless＋owned/default seam | 受理 | parser token を claim して受理 |
| formal token＋providers 注入 | 受理可能 | artifact 作成前に拒否 |
| formal token＋drive または preview 注入 | 受理可能 | artifact 作成前に拒否 |
| 偽造・未発行・再使用 token |概念なし | fail-closed 拒否 |
|異なる role の同一 session ID |受理 |二番目の provider invocation を invalid として拒否 |
|receipt が両方欠落した既存 artifact |受理 |受理のまま |
|receipt の片側欠落・未知 key・不一致 |現在は未知 field として素通り |formal consumer が拒否 |

## 4. artifact への記録

- Journal: `run-start` event にだけ `formal_trial_gate_receipt` を追加する。token 非提示時は key 自体を置かない。
- Report: root に同名 field・同一 body を追加する。token 非提示時は key 自体を置かない。
- `run-finish`、role-attempt、transport-admission、cell、Layer-3 admission decision には追加しない。
- nonce、claimed set、session tracker 内部表は一切 serialize しない。
- consumer は `receipt_id` が lowercase 64-hex であることと両 projection の一致を検査する。receipt_id は認証情報ではない。

既存 strict-key 検査への影響は次の全箇所で、いずれも赤くならない配置である。

- `autonomous_trial_completeness.py:303-309`: `transport-admission` exact keys。ここへ追加しない。
- 同 `:969-970`: Layer-3 `admission_decision` exact keys。変更しない。
- 同 `:979-980`: `validator` exact keys。変更しない。
- 同 `:981-982`: `overlay` exact keys。変更しない。
- 同 `:36-44`, `:271-275` の event-kind 閉集合にも新 event を足さない。
- report root と run-start は現在 exact-key 閉集合ではないため、選択した field 追加だけで既存 strict-key 検査が赤くなる箇所はゼロ。
- 新 leaf の receipt validator に、新しい exact-key 検査を一つ設ける。これは formal receipt が存在するときだけ発火する。

## 5. テスト計画

新規ファイルは `orchestrator/tests/test_formal_trial_gate.py` 一本にまとめる。既存テストの assert・fixture・期待値は編集しない。

新規 node:

- `test_missing_formal_token_is_noop_for_all_public_seams` — token なしなら三 seam が非正準でも evaluator wrapper は現行経路を変えない。
- `test_formal_gate_rejects_each_injected_seam_before_artifact[providers]` — providers だけ注入した formal run を拒否。
- 同 `[drive]` — drive だけ注入した formal run を拒否。
- 同 `[preview]` — preview だけ注入した formal run を拒否。
- `test_formal_gate_rejects_non_projected_provider_before_artifact` — formal token と fixture provider の組合せを拒否。
- `test_formal_gate_rejects_bad_token_before_artifact[wrong-type]` — exact token 型でない値を拒否。
- 同 `[unissued-exact]` — sealed 型でも issued set にない nonce を拒否。
- `test_formal_gate_token_is_claimed_once_even_when_seam_rejected` —一度提示した token は拒否 run 後にも再利用不可。
- `test_formal_gate_rejects_undecidable_boolean_input` — pure evaluator の非 exact-bool 入力を拒否。
- `test_main_issues_token_only_for_claude_headless[claude-headless-present]` — main の Claude 選択が parser-issued token を `run_trial()` へ渡す。
- 同 `[fixture-absent]` — fixture の既存 CLI は token 非提示。
- `test_provider_set_shares_exact_tracker_across_four_roles` —四つの factory call が同一 tracker object を受ける。
- `test_projected_provider_rejects_unknown_tracker_type_before_artifact` — tracker の判定不能型を副作用前に拒否。
- `test_projected_providers_reject_cross_role_session_reuse` —別 instance 二つに同一 session ID を返し、二番目を拒否。
- `test_projected_providers_accept_distinct_cross_role_sessions` —別 session ID 二つは受理。
- `test_formal_provider_init_failure_records_paired_receipt_without_token_nonce` — provider 初期化失敗の partial artifact にも journal/report の一致 receipt が残り、nonce は残らない。
- `test_nonformal_provider_init_failure_omits_receipt` — token なしの同じ失敗 artifact は新 field を持たない。
- `test_formal_receipt_consumer_rejects_boundary_mutation[missing-journal]`
- 同 `[missing-report]`
- 同 `[unknown-key]`
- 同 `[unknown-policy]`
- 同 `[malformed-receipt-id]`
- 同 `[receipt-id-mismatch]`
- 同 `[fixture-provider]`

既存テストへの静的波及は次のとおり。これらは期待値を変更せず再実行対象にする。

- `test_p3_autonomous_workload_trial.py`: `test_fixture_trial_runs_ycsb_abc_and_binds_descriptor`, `test_generation_one_recipient_wiring_uses_role_projection`, `test_generation_one_finite_metrics_preserve_recipient_units_and_report_schema`, `test_invalid_role_is_single_attempt_and_stops_cell`, `test_run_trial_rejects_unapproved_budget_before_artifact_creation`, `test_run_trial_rejects_compute_build_before_artifact_or_provider`, `test_run_trial_other_build_requires_parser_authority_before_artifact`, `test_8c_internal_entrypoints_have_no_site_injection_surface`, `test_finish_trial_direct_compute_build_rejects_before_provider`, `test_run_trial_build_public_entry_passes_exploration_layout_to_trigger`, `test_supervisor_error_still_writes_partial_terminal_report`, `test_run_trial_closes_owned_providers_in_reverse_order`, `test_run_trial_does_not_close_injected_providers`, `test_provider_set_closes_partial_projected_provider_set_in_reverse_order`, main 系 7 node（`:1348`, `:1373`, `:1398`, `:1413`, `:1436`, `:1453`, `:1479`, `:1499`）、projected provider 系 6 node（`:1687`, `:1715`, `:1742`, `:1773`, `:1827`, `:1852`）。
- `test_autonomous_trial_completeness.py`: `_verify()` を通る全 node、すなわち `test_p1_complete_three_cell_fixture_passes` から `test_state_machine_rejects_nonprefix_roles` までの `:448-1142` にある 34 node、および `test_terminal_projection_and_journal_hash_are_independent_gates`, `test_run_start_scalar_envelope_fields_are_bound`, `test_report_attempt_journal_path_is_bound_to_verified_file`, `test_journal_seq_gap_is_rejected`。producer 直結の `test_m4a_producer_supervisor_error_preserves_constructed_generation`, `test_role_append_io_failure_cannot_publish_incomplete_report`, `test_journal_change_after_verifier_read_is_fail_closed`, `test_completeness_failure_is_not_caught_and_report_is_not_written`, `test_direct_cli_starts_with_clean_pythonpath` も対象。
- `test_claude_transport.py` の collateral: `test_cli_flag_default_and_all_four_wiring_links_are_explicit`, `test_provider_set_passes_one_immutable_receipt_object_to_four_roles`, `test_m10_real_providers_share_run_admission_without_resolving_per_role`, projected provider constructor系 4 node（`:1086`, `:1135`, `:1171`, `:1202`）、`test_p1_flag_omitted_run_trial_has_no_transport_io_or_fields`, `test_p2_flag_on_run_trial_admits_compute_wrapper_with_real_providers`, `test_success_consumer_keeps_valid_receipt_in_journal_and_report`, `test_terminal_events_keep_transport_receipt`, `test_opt_in_report_and_opt_out_report_field_boundaries`。
- `test_build_admission.py`: production fileを変更しないため直接波及はゼロ。`test_coder_requires_parser_issued_run_token` と `test_cli_nonce_is_not_serialized` は設計先例としてのみ使う。

## 6. 変異事前登録の候補

| 1 行変異 | kill を期待する node |
|---|---|
| `if token is None: return None` を削除 | `test_missing_formal_token_is_noop_for_all_public_seams` |
| token exact-type 条件を `if False` | `test_formal_gate_rejects_bad_token_before_artifact[wrong-type]` |
| issued-set membership 条件を `if False` | 同 `[unissued-exact]` |
| claimed-set membership 条件を `if False` | `test_formal_gate_token_is_claimed_once_even_when_seam_rejected` |
| non-exact bool を `ACCEPT` にする | `test_formal_gate_rejects_undecidable_boolean_input` |
| provider-kind 拒否条件を `if False` | `test_formal_gate_rejects_non_projected_provider_before_artifact` |
| providers 注入拒否を `if False` | seam node `[providers]` |
| drive identity 拒否を `if False` | seam node `[drive]` |
| preview identity 拒否を `if False` | seam node `[preview]` |
| parser action の Claude token 発行を `None` にする | main node `[claude-headless-present]` |
| parser action が fixture にも token を発行する | main node `[fixture-absent]` |
| `_provider_set()` で loop ごとに新 tracker を渡す | `test_provider_set_shares_exact_tracker_across_four_roles` |
| provider constructor の tracker 型拒否を無効化 | `test_projected_provider_rejects_unknown_tracker_type_before_artifact` |
| `CrossRoleSessionTracker.observe()` の重複条件を `if False` | `test_projected_providers_reject_cross_role_session_reuse` |
| provider の共有 `observe()` 呼出しを削除 | 同 node |
| run-start への receipt 追加を削除 | `test_formal_provider_init_failure_records_paired_receipt_without_token_nonce` |
| report への receipt 追加を削除 | 同 node |
| consumer の片側欠落条件を `if False` | mutation node `[missing-journal]` / `[missing-report]` |
| receipt exact-key 条件を `if False` | mutation node `[unknown-key]` |
| policy literal 検査を `if False` | mutation node `[unknown-policy]` |
| receipt-id 形式検査を `if False` | mutation node `[malformed-receipt-id]` |
| journal/report receipt 一致条件を `if False` | mutation node `[receipt-id-mismatch]` |
| receipt/provider 整合条件を `if False` | mutation node `[fixture-provider]` |
| token なしでも receipt を無条件追加 | `test_nonformal_provider_init_failure_omits_receipt` |

cross-role test は必ず別 provider instance 二つを使う。同一 instance を使うと既存 `_observed_session_ids` が mutant を殺し、共有検査の恒真な正例になってしまう。

## 7. 実装順序と所有

実装単位は分けず、一人の author worker が次を一続きで所有する。

1. `formal_trial_gate.py` と新規テストの leaf 単体境界。
2. `p3_autonomous_workload_trial.py` の parser/token/seam/receipt 配線。
3. `claude_projected_provider.py` の共有 tracker 配線。
4. `autonomous_trial_completeness.py` の optional receipt consumer。
5. 新規 test file の統合境界。

token 型、module identity、receipt schema、tracker identity が相互依存するため、leaf と三つの consumer を別 author に分割しない。段3・段6の敵対レビューだけを独立並列化する。

D96 の新 D と境界テストは同一最終 commit に含める。親が mutation 実走、受入、spool fragment、commit を所有し、author worker はコードとテストだけを所有する。pytest 実測は親が `tools/run_tests.py` 経由で行う。

## 8. リスク

- P1 wave は `p3_autonomous_workload_trial.py` の表現・emitter 配線、P3 wave は同ファイルの run lifecycle と `autonomous_trial_completeness.py` の artifact schema を編集する可能性が高い。これら二ファイルで overlap を検出したら停止し、rebase・force・手動合成で迂回しない。
- `campaign.formal_trial_gate` と `orchestrator.campaign.formal_trial_gate` の二重 import は exact token/tracker 型を壊す。新 leaf は既存の direct/package import 分岐と同じ `orchestrator.campaign` identity に統一する。
- 固定 literal だけの receipt を二つ比較すると一致検査が恒真になる。独立 `receipt_id` と mismatch test を必須にする。
- consumer は receipt の両側削除を検出できない。既存 token 非提示 artifact を受理する制約と両立しないためであり、P5 の credit は「main の Claude 経路が runtime で発行・記録した process 内 run」に限定する。
- private argparse action、module private seal、issued/claimed set、tracker は同一 process の悪意ある Python callerや monkeypatch に対する security boundary ではない。
- process 再起動、別 process、registry 全削除、receipt コピー、crash replay、CAS、durable anchor は閉じない。すべて P3 の職掌である。
- direct `run_trial(token=None)`、`_run_workload()`、`_finish_trial()`、`drive_iteration()` は非 formal 経路として残る。formal と名乗れるのは receipt 付き main/Claude 経路だけ。
- `MAX_APPROVED_GENERATIONS=1` の cap-lift、固定5-bit IR、emitter、origin ledger、`docs/phase3-main-experiment.md` には触れない。

## 総括

推奨案は PROV-1〜PROV-5 をすべて採用し、PROV-2 の「main だけが発行」を「既存 `--provider` の private argparse action が `claude-headless` 選択時に自動発行する」と具体化するものである。新しい opt-in flag を設ける案は、利用者が flag を省くだけで正式 CLI 経路から P5 を外せるため不採用とする。一方、fixture と programmatic token 非提示 run は既存受理集合を保持する。

採否が割れ得る第一の論点は、formal receipt を全 Claude artifact に遡及必須化するかである。本案は既存期待値を変えないため optional pairing を採り、両側削除を検出できない限界を明記する。第二は receipt を固定 literal にするかである。固定値同士の一致検査は恒真になるため、token nonceとは独立した `receipt_id` を加え、二つの有効だが不一致な receipt を作れる境界テストを置く。第三は同一 process 内の private state に security credit を与えるかであり、本案は与えない。得られるのは、main の Claude 経路における三 seam の拒否、四 role 間 session 重複の拒否、parser-issued token の一回使用という P5 の process-local misuse prevention だけである。

D96 に従い、この限定された受理集合、既定経路不変、閉じていない P3 境界、却下案を新しい decisions spool fragmentへ記録し、新規境界テストと同一 commit に含める。実装・pytest・書込みは本段では行っていない。