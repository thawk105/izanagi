# 実装プラン

以下の行番号は現 checkout の編集前アンカーである。静的読解のみで、編集・pytest 実行はしていない。

結論から言うと、親 brief の P1 の受理集合に同意する。ただし、nullable 引数を多数持つ一つの gate ではなく、「正式登録」と「明示探索」を別関数に分け、双方から sealed な launch admission を返す方が安全である。

また、全 scope を 1 wave に入れるのは推奨しない。T-468 の approval artifact が実在せず、既存 Layer 3 renderer は acceptance より前に動くため、U-4 を含む最小 land と receipt/downstream wave を分ける。

## U-4 — 最優先 gate 設計

### 採る案

`orchestrator/campaign/trial_registry.py:46-49` の `HOLDOUT_BINDINGS` から次を導出する。

```python
HOLDOUT_WORKLOADS = frozenset(
    binding["workload"] for binding in HOLDOUT_BINDINGS.values()
)
```

`p3_autonomous_workload_trial.py:171-175` の `WORKLOADS` は使わない。現在 `rr80` / `rr20` がそこに無くても U-4 gate 自体が発火し、将来 `WORKLOADS` に追加されても gate が消えないためである。

正式系と探索系を次の二入口に分ける。

```python
def admit_preregistration(
    *,
    effective_preregistration: EffectivePreregistration,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
) -> TrialLaunchAdmission:
    ...
```

```python
def admit_unregistered_exploratory(
    *,
    trial_id: str,
    workloads: Sequence[str],
    allow_unregistered_exploratory: bool,
    repository_root: Path,
    registry_path: Path,
) -> TrialLaunchAdmission:
    ...
```

`TrialLaunchAdmission` は private seal 付き immutable dataclass とし、少なくとも次を持つ。

```python
mode: Literal["registered-effective", "explicit-unregistered-exploratory"]
certifying: bool
reason_code: str
trial_id: str
workloads: tuple[str, ...]
binding: TrialBinding | None
_seal: object
```

### 拒否条件

正式入口 `admit_preregistration` は次を拒否する。

- `EffectivePreregistration` 以外、偽造・古い digest・別 commit の capability。
- capability の `commit` と manifest の `prereg_commit` が不一致。
- manifest または registry が operation HEAD に未 commit、working bytes と HEAD blob が不一致。
- manifest に trial ID が一意に存在しない。
- manifest の holdout singleton と要求 workload が不一致。
- registry に manifest の完全一致 registration が無い。
- 同じ trial ID の lifecycle start が既に存在する。

探索入口は次を拒否する。

- `allow_unregistered_exploratory is not True`。
- `set(workloads) & HOLDOUT_WORKLOADS` が非空。opt-in でも拒否する。
- trial ID が registry に既登録。
- registry の存在・HEAD blob・working bytesを一意に検査できない。
- 不正 trial ID、重複 workload、無効 repository。

CLI flag は `--allow-unregistered-exploratory` とする。既定値は `False`。

### 通る正例

初期化済み Git repository、registry 未作成、未登録 `trial_id="fixture-abc-g1"`、`workloads=("ycsb-a",)`、manifest 無し、`allow_unregistered_exploratory=True` は通す。

戻り値は次で固定する。

```json
{
  "mode": "explicit-unregistered-exploratory",
  "certifying": false,
  "reason_code": "explicit-unregistered-exploratory"
}
```

同じ条件で flag 無しなら拒否する。`workloads=("rr80",)` なら flag があっても拒否する。

### producer への結線

`orchestrator/campaign/p3_autonomous_workload_trial.py:614-650` の `_trial_launch_binding` を `_trial_launch_admission` に置換する。

```python
def _trial_launch_admission(
    *,
    trial_manifest: Path | None,
    trial_id: str,
    workloads: Sequence[str],
    generations: int,
    allow_unregistered_exploratory: bool,
    effective_preregistration: EffectivePreregistration | None,
) -> TrialLaunchAdmission:
    ...
```

`run_trial()` は `run_root.mkdir()` より前、現行 `1760-1792` の位置で admission を再導出する。CLI preflight から渡された admission も seal、HEAD、manifest、registry を再検証する。

`_RunScopeBinding` (`p3_autonomous_workload_trial.py:274-282`) は nullable `TrialBinding` ではなく必ず `TrialLaunchAdmission` を保持する。`_run_workload()` (`1355-1391`) の「scope が無ければ探索 gate を直接呼ぶ」fallback は削除し、scope 無しを拒否する。これにより private worker の直接呼出しから holdout gate を迂回できない。

`run-start` (`1828-1846`) と report (`1283-1321`) の双方に同一の `launch_admission` object を記録し、`autonomous_trial_completeness.py:371-465` で完全一致を検査する。

## 編集面の地図

### `orchestrator/campaign/s8c_preregistration.py`

- `1614-1619`
  - 既存 `effective_at(repo_root, commit="HEAD") -> Optional[EffectivePreregistration]` は変更しない。
- `1745-1749` の digest helper 後に追加:

```python
def require_effective_preregistration(
    capability: EffectivePreregistration,
    *,
    repo_root: Path | str,
    commit: str,
) -> ActivationReport:
    ...
```

C の `activation_report_at()` を再計算し、`report.effective`、commit、`report_digest_sha256` の三つを照合する。capability object 単体を authority として信用しない。

### `orchestrator/campaign/trial_registry.py`

- `41-67`
  - lifecycle/receipt schema version、`DEFAULT_LIFECYCLE_PATH`、`DEFAULT_RECEIPT_DIR`、exact key 集合を追加。
- `78-130`
  - `TrialLaunchAdmission`、`TrialLifecycleToken`、`AcceptanceResult` を追加。
  - `TrialBinding` に `activation_report_digest_sha256` を追加。
- `302-321`
  - 既存 `load_trial_manifest(path)` の本体を contract 名の `load_manifest(path)` に移す。
  - `load_trial_manifest` は互換 wrapper に限定し、production call path は `load_manifest` を使う。
- `904-1017`
  - `_derive_launch_binding` は internal helper として維持。
  - `load_launch_binding(...) -> TrialBinding` を正式入口 `admit_preregistration(...) -> TrialLaunchAdmission` に置換。
- `1020-1061`
  - 現在は未登録 ID を通す `assert_unregistered_for_exploratory(...)` を、既定拒否の `admit_unregistered_exploratory(...)` に置換。
- `1064-1073`
  - `assert_campaign_binding(binding, actual_campaign_id=...)` を contract 名 `bind_trial_arm(...)` に改名。
  - ただしこの改名だけで C02 を充足扱いにしない。
- `1076-1295`
  - lifecycle の locked append/read、receipt 用 report/journal snapshot hash、registry の一意 introduction commit 検査を追加。
- `1298-1428`
  - 既存:

```python
def assert_trial_registry_acceptance(
    *,
    manifest_path: Path,
    report_paths: Sequence[Path],
    repository_root: Path,
    registry_path: Path,
) -> AcceptanceSummary:
```

  - 変更後:

```python
def accept_trial(
    *,
    effective_preregistration: EffectivePreregistration,
    manifest_path: Path,
    report_paths: Sequence[Path],
    repository_root: Path,
    registry_path: Path,
    lifecycle_path: Path,
) -> AcceptanceResult:
    ...
```

  - receipt path は caller に選ばせず、`receipts/<manifest_sha256>.json` に導出する。
  - 旧関数名を残す場合も non-certifying 互換 wrapper とし、production CLI は `accept_trial` のみ呼ぶ。
- `1431-1477`
  - stdout summary に `receipt_path` と `receipt_sha256` は表示してよいが、下流は stdout/rc を authority にしない。
  - CLI adapter は `effective_at()` API から capability を作り、`accept_trial` に渡す。

### `orchestrator/campaign/p3_autonomous_workload_trial.py`

- `26-106`: preregistration API import を追加。
- `274-282`: run scope を `TrialLaunchAdmission` 必須へ変更。
- `614-650`: `_trial_launch_binding` を `_trial_launch_admission` に置換。
- `1168` の直前に追加:

```python
def mark_experiment_indeterminate(
    *,
    lifecycle: TrialLifecycleToken,
    journal: AttemptJournal,
    error: Mapping[str, str],
) -> None:
    ...
```

- `1168-1352`
  - `_finish_trial` に lifecycle token を渡す。
  - `1231-1265` の production exception path で `mark_experiment_indeterminate()` と `trial_registry.forbid_trial_restart()` を呼ぶ。
  - report/run-start に exact `launch_admission` を記録。
- `1355-1391`: direct workload call は sealed run scope 無しなら拒否。
- `1685-1704`
  - `run_trial` へ追加:

```python
allow_unregistered_exploratory: bool = False
effective_preregistration: EffectivePreregistration | None = None
trial_admission: TrialLaunchAdmission | None = None
```

  - `trial_binding` は `trial_admission` に置換。
- `1760-1792`: admission と lifecycle start を artifact 作成前に確定。
- `1928-1957`: `--allow-unregistered-exploratory` を追加。
- `1981-2019`: manifest 有りなら `effective_at(ROOT, manifest.prereg_commit)` を API 呼出しし、admission を `run_trial` へ渡す。

### 新設 `orchestrator/campaign/s8c_acceptance_receipt.py`

責務は次だけに限定する。

- receipt exact schema/canonical JSON の parse。
- duplicate key、NaN、未知 key、非正規 path の拒否。
- receipt path と manifest hash の対応検査。
- receipt bytes が Git HEAD に tracked かつ working bytes と一致することの検査。
- 参照 report/journal/lifecycle/registry/Layer 3 bytes の再 hash。
- sealed `VerifiedAcceptanceReceipt` の発行。

`trial_registry` と `layer3_report` の循環 import を避けるため、receipt parser を独立 module にする。

### `orchestrator/campaign/autonomous_trial_completeness.py`

- `122-174` 付近に `read_and_verify_bytes(path, declared_sha256)` を追加。
- `1015-1110` の Layer 3 chain 検査後に追加:

```python
def verify_s8c_cross_binding(
    *,
    report_path: Path,
    attempt_journal_path: Path,
    campaign_output_root: Path,
) -> CrossBindingReceipt:
    ...
```

次の実在 field/bytes を再読する。

- `input_payload_sha256` (`p3_autonomous_workload_trial.py:916`)
- `raw_response_path` / `raw_response_sha256` (`968-969`)
- provider payload/envelope hashes
- `proposal_path` から導出した proposal bytes
- campaign WAL の build/bench records
- Layer 3 の `artifact_refs` / `source_refs` / `admission_decision` (`layer3_report.py:467-468`)

単なる field 存在確認ではなく、参照先 bytes を再 hash する。

### `orchestrator/campaign/layer3_report.py`

既存 `build_report()` (`367-474`) と `render()` (`477-502`) は acceptance より前に使われるため、receipt 必須には変更しない。

`render` 後に post-acceptance 専用入口を追加する。

```python
def build_accepted_report(
    campaign_dir: Path,
    *,
    trial_id: str,
    acceptance_receipt: VerifiedAcceptanceReceipt,
    generated_from_head: Optional[str] = None,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    ...
```

この関数は次を満たさなければ拒否する。

- receipt raw bytes が tracked。
- `receipt.certifying is True`。
- receipt の trial/campaign ID が対象 campaign と一致。
- receipt に記録された Layer 3 SHA と persisted/fresh rebuild bytes が一致。
- report/journal/registry/manifest/lifecycle hashes が現在 bytes と一致。

既存 generic `build_report()` は「材料 report」であり、certified selection の入口として扱わない。

現 checkout に 8c certified-selection consumer は存在しない。そのため、将来の consumer は必ず `build_accepted_report` を呼ぶ、という実結線が追加されるまでは T-470 全体の完了を主張しない。

### evidence files

- `orchestrator/campaign/s8c_preregistration_evidence.py:51-87`
  - contract entrypoint に対応する精密 reason code を追加。
- `409-511`
  - C03/C08 の readiness evaluator を追加。
  - C04/C09/C10 の既存 evaluator を、SAT 判定ではなく readiness 判定として利用。
- `621-666`
  - `machine_checkable:false` のままでも、named consumer が欠ければ `UNSATISFIED`、配線済みなら `EVIDENCE_UNDEFINED` を返す。
- `s8c_preregistration_evidence_contract.v1.json`
  - **編集しない**。必要な entrypoint 名は既に記録済みであり、変更すると protected hash が変わって g2 と人間 ruling reference が必要になる。
- `test_s8c_preregistration_invariant.py:30-40`
  - 新設 module/test を holdout contamination 検査対象へ追加。

## U-1 — sealed capability の必須境界

必須引数は `effective_preregistration` とする。

- launch admission:
  - `trial_registry.admit_preregistration(..., effective_preregistration=...)`
  - `p3.run_trial(..., effective_preregistration=...)`
- post-run acceptance:
  - `trial_registry.accept_trial(..., effective_preregistration=...)`

探索入口だけは capability を受け取らず、常に non-certifying とする。`run_trial` の union 型は branch adapter の都合であり、manifest 有り branch では `None` を即拒否する。

照合対象は capability の型だけではない。

1. manifest の `prereg_commit`
2. capability の `commit`
3. `activation_report_at(C)` の再計算結果
4. capability の `report_digest_sha256`

の完全一致を要求する。祖先 commit の capability は拒否する。

### API に限定する理由

N1 の欠陥は `python -m orchestrator.campaign.s8c_preregistration` が core class を `__main__` と package module の二つに分裂させることにある。CLI subprocess の JSON/rc を launch authority にすると、正常な API 判定まで恒久的に閉じる。

したがって P3 CLI adapter は、別 CLI を subprocess 実行せず、import 済み package module の `effective_at()` を直接呼ぶ。acceptance も同じ API object を受け取る。

### N1 修復の推奨

本 wave では直さないことを推奨する。

- 現状は fail-closed で誤受理を起こさない。
- U-4 が最優先であり、module identity 修復は production gate と独立。
- `sys.modules` alias 等の修復は direct-script/package import の回帰面が広い。

別タスクで `python -m ... check` と package API が同じ `PredicateResult` / `PredicateStatus` class identity を使うテストを追加する。production 配線はその修復を待たない。

## U-5 + T-470

### 一回性の記録場所

新設 artifact として、明示的に次を提案する。

```text
output/s8c-trial-registry/lifecycle.jsonl
```

これは「実在する」とは主張しない新設 path である。

start row の exact fields:

```text
schema_version
event
trial_id
manifest_sha256
measurement_head
activation_report_digest_sha256
started_once
restart_forbidden
```

terminal row の exact fields:

```text
schema_version
event
trial_id
terminal_status
report_sha256
attempt_journal_sha256
```

`record_trial_start_once()` は `fcntl` lock 下で全 ledger を strict parseし、trial ID が一度でも start 済みなら、別 `run_root` でも拒否する。未使用なら start row を fsync append し、sealed `TrialLifecycleToken` を返す。

`forbid_trial_restart(token)` は ledger を再読し、token と start row の完全一致を確認する。正常終了と indeterminate の双方で terminal row を一度だけ append する。SIGKILL 等で terminal が無くても start row が残るので再実行は拒否され、acceptance は terminal 欠落を拒否する。

注意点として、この ledger は同一 working registry を共有する process 間では原子的だが、別 worktree/別 clone にまたがる project-global CAS ではない。そこまでの保証には T-469 の外部 append-only ledger が必要であり、この wave で過大主張しない。

### acceptance receipt schema

新設 schema 名を次で固定する。

```text
p3-8c-trial-acceptance-receipt/v1
```

receipt path:

```text
output/s8c-trial-registry/receipts/<manifest_sha256>.json
```

top-level exact fields:

```text
schema_version
manifest_path
manifest_sha256
prereg_commit
activation_report_digest_sha256
registry_path
registry_commit
registry_introduction_commit
registry_blob_sha256
lifecycle_path
lifecycle_blob_sha256
cross_binding_receipts
cross_binding_receipt_sha256
arm_binding
certifying
non_certifying_reason_codes
trials
```

`cross_binding_receipts[]`:

```text
trial_id
sha256
```

`trials[]`:

```text
trial_id
arm
holdout
campaign_id
status
do_build
measurement_head
report_path
report_sha256
attempt_journal_path
attempt_journal_sha256
layer3_reports
```

`layer3_reports[]`:

```text
campaign_id
path
sha256
```

path はすべて repository-relative POSIX path、trial は `trial_id` 順、Layer 3 は `campaign_id` 順とする。canonical JSON 1 行 + LF で exclusive-create し、既存 receipt の置換は無条件拒否する。

既存 artifact から採る field は現物確認済みである。上記 receipt field 名自体はこのプランで新たに固定する名前であり、既存 artifact に存在すると仮定していない。

`certifying=True` は少なくとも次の conjunction とする。

- capability 再検証済み。
- registry/manifest/lifecycle が exact。
- 六 trial がすべて complete。
- 全 trial が `do_build=True`。
- arm binding が declared-only ではない。
- 全 build report の Layer 3 chain が再検証済み。
- C10 cross-binding bytes がすべて一致。
- manifest indeterminate marker が無い。
- canonical registry authority が解決済み。

それ以外でも receipt は negative outcome の記録として発行できるが、`certifying=False` と exact reason list を持ち、accepted Layer 3 consumer は拒否する。

### rc を使わない結線

下流が受け取るのは `VerifiedAcceptanceReceipt` である。これは tracked file の raw bytes、SHA-256、parsed value を保持する sealed object とする。

- acceptance CLI の rc=0 は receipt の代用品にならない。
- stdout の summary を保存しても receipt にはならない。
- receipt path が無い、untracked、bytes 不一致、`certifying=False` のいずれも下流拒否。
- `build_accepted_report()` の signature に return code 引数を設けない。

## T-468 — canonical authority

完全な T-468 は現物だけでは書けない。

確認できた事実は次のとおり。

- `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json:1` は実在するが、`ruling_reference` は `null`。
- `docs/decisions.md:5486-5517` の D116 は 8c に human receipt を新規輸入しないと定めている。
- `docs/worklog.md:628-642` は後から「T-295 approval record に registry commit を含める」と要求している。
- checkout 内に T-295 用 approval record schema/path/artifact は無い。
- `s4-ruling.md:57-67` も新設 artifact の SAT 化を禁じ、親 brief P4 は実在確認を条件にしている。

したがって、実装できるのは次までである。

- registry path の unique introduction commit。
- 各履歴状態が strict prefix extension。
- merge DAG に二つの非互換 registry genesis が無い。
- receipt の `registry_commit` / `registry_introduction_commit` / `registry_blob_sha256` の照合。

これは registry history の一意性であり、approval authority ではない。T-468 全体は次の設計メモに留める。

> T-295 approval record の canonical path、exact schema、issuer/commit 束縛が存在しないため、registry commit との結線は未実装。再開条件は、人間裁定が実在 artifact を指定するか、authority を `effective_at(C)` + unique registry introduction commit へ改訂すること。未解決中は receipt を certifying にしない。

架空の `approval.json` 等は作らない。

## 既存テストへの波及

### reason/status が落ちる nodeid

readiness evaluator を named contract に合わせると、少なくとも次が落ちる。

- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_missing_target_module_is_capability_probe_not_exception`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_noop_and_token_only_fixtures_never_satisfy[nc_c04_partial_crash_survives-C04]`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_noop_and_token_only_fixtures_never_satisfy[nc_c09_acceptance_skips_layer3-C09]`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_noop_and_token_only_fixtures_never_satisfy[nc_c10_raw_response_unbound-C10]`

`test_missing_target_module...` の line 147 は、generic な `trial-registry-capability-absent` から、C03 の exact consumer を示す `manifest-registry-consumer-absent` へ更新する。module 自体が無い fixture は `EVIDENCE_UNDEFINED`、module はあるが `load_manifest` / `accept_trial` が欠ける fixture は `UNSATISFIED` と分ける。

parameterized negative control は、token-only 正例を `EVIDENCE_UNDEFINED` のまま保ち、mutation 側だけ exact `UNSATISFIED` に変える。

- C04: `crash-policy-cell-partial`
- C09: `formal-acceptance-layer3-consumer-absent`
- C10: `cross-binding-verifier-incomplete`

`status != SATISFIED` のような甘い assertion には変更しない。

### U-4 による既存 positive の変更

次は「無条件 pass」から「明示 opt-in で pass」へ変更する。

- `test_trial_registry.py::test_p9_prime_existing_registry_unregistered_exploratory_id_passes`
- `test_p3_autonomous_workload_trial.py::test_p9_exploratory_run_with_absent_registry_preserves_report_shape`
- `test_p3_autonomous_workload_trial.py::test_p9_prime_m27_prime_existing_registry_unregistered_exploratory_passes`

名前も `...explicit_opt_in...passes_non_certifying` に変える。ほかの manifestless `A.run_trial(...)` positive fixturesにも `allow_unregistered_exploratory=True` を明記する。autouse fixture で暗黙に許可してはいけない。

正式 manifest fixture は real repository が未発効なので、U-1 以外の mutation test に限り test-only capability/validator fixture を注入する。production API へ registry/evaluator injection 引数は追加しない。

## 12 述語の不変条件

SATISFIED 0 件は次で保つ。

- evidence contract の `machine_checkable:false` は変更しない。
- readiness evaluator の成功値は `EVIDENCE_UNDEFINED` に固定し、SATISFIED を返さない。
- `is_satisfied()` は引き続き exact `PredicateStatus.SATISFIED` だけを真にする。
- `test_candidate_is_not_effective_and_has_zero_satisfied_predicates` の exact 12 件/0 件 assertion を維持。
- receipt/lifecycle の存在を発効証拠として扱わない。

full wiring で `UNSATISFIED → EVIDENCE_UNDEFINED` へ動かす対象は次である。

- C03: `load_manifest` + `accept_trial`
- C04: `mark_experiment_indeterminate` + `forbid_trial_restart`
- C08: `admit_preregistration` + `accept_trial` + exact `effective_at(C)`
- C09: formal acceptance から Layer 3 chain への call
- C10: `verify_s8c_cross_binding` + acceptance call

C02 はこの wave では動かさない。`bind_trial_arm` という関数名だけでは、contract が要求する run-start/report/campaign/proposal/invocation 全 sink の injective arm binding にならないため、`arm-binding-declared-only` または `arm-binding-proof-undefined` を維持する。

C01/C05/C06/C07/C11/C12 も現状の `EVIDENCE_UNDEFINED` のままとする。

## 新設テスト

| gate | negative control | positive control | 既存重複 |
|---|---|---|---|
| U-4 既定拒否 | `test_manifestless_unregistered_launch_is_rejected_by_default_before_artifacts` | `test_explicit_non_holdout_exploration_is_non_certifying` | 既存 P9 positive を更新するため positive は重複 |
| U-4 holdout 逃げ道無し | `test_holdout_exploratory_opt_in_is_rejected_from_holdout_bindings` | 登録 branch の admission 単体 positive | 既存は「登録済み ID の manifest 無し」だけ。未登録 holdout は純増 |
| sealed activation | `test_admit_preregistration_rejects_none_forged_parent_and_digest` | `test_require_effective_preregistration_accepts_exact_recomputed_test_capability` | constructor 偽造拒否は既存、再計算照合は純増 |
| restart | `test_same_trial_id_with_different_run_root_is_rejected` | `test_first_trial_start_records_single_lifecycle_row` | fresh run-root gate は同一 path のみ。両方純増 |
| crash | `test_crash_marks_manifest_indeterminate_and_restart_remains_forbidden` | `test_complete_trial_records_one_terminal_row` | 純増 |
| acceptance receipt | `test_accept_trial_refuses_existing_or_noncanonical_receipt` | `test_accept_trial_writes_canonical_exclusive_receipt` | report/journal acceptance 自体は重複、receipt bytes は純増 |
| receipt revalidation | `test_verified_receipt_rejects_report_or_journal_byte_change` | `test_verified_receipt_accepts_matching_tracked_bytes` | acceptance 中 snapshot race と異なる post-receipt 検査なので純増 |
| downstream | `test_build_accepted_report_rejects_missing_untracked_or_noncertifying_receipt` | `test_build_accepted_report_accepts_matching_certifying_fixture` | 純増。T-468 authority fixture が定義されるまで positive は land しない |
| registry history | `test_registry_authority_rejects_incomparable_genesis_commits` | `test_registry_authority_returns_unique_introduction_commit` | prefix history は既存、genesis/DAG authority は純増 |
| C03/C08 readiness | `test_noop_and_token_only_fixtures_never_satisfy[...]` に exact mutation cases 追加 | named wiring が `EVIDENCE_UNDEFINED` | 純増 |
| 0 SAT | 既存 candidate invariant | なし。発効 positive を作らないこと自体が契約 | 重複 |

「CLI rc=0 だが receipt 無し」を拒否する test は `test_success_status_without_receipt_bytes_is_rejected` とし、rc を verifier API の入力にはしない。

## runbook 本文案

`docs/phase3-s8c-autonomous-trial-runbook.md:55-102` へ、実装時に次の趣旨を追記する。

> manifest を伴わない §§3.1–3.3 の起動は未登録探索であり、`--allow-unregistered-exploratory` の明示指定が必要である。省略時は run root 作成前に拒否する。明示指定した run は `launch_admission.certifying=false` を journal/report に記録し、正式選択の入力にはならない。
>
> この opt-in は holdout 束縛 workload には適用できない。H1/H2 に触れる起動は、登録済み manifest、manifest の `prereg_commit` と一致する `effective_at(C)` capability、未消費 trial ID をすべて要求する。現 repository は 12 述語 SATISFIED 0 件なので、正式 H1/H2 launch が通ることを期待してはならない。
>
> acceptance の成功 exit code や stdout は証拠ではない。`output/s8c-trial-registry/receipts/<manifest_sha256>.json` を commit し、下流はその raw bytes と参照 artifact の SHA-256 を再検証する。receipt が無い、untracked、non-certifying の場合は accepted Layer 3 を生成しない。

既存 3.1/3.2/3.3 の各コマンド例には `--allow-unregistered-exploratory` を追加する。

## 実装単位と依存順

full scope の file ownership は次の素集合にする。

1. Capability unit
   - `s8c_preregistration.py`
   - `test_s8c_preregistration_core.py`

2. Receipt-format unit
   - 新設 `s8c_acceptance_receipt.py`
   - 新設 `test_s8c_acceptance_receipt.py`

3. Cross-binding unit
   - `autonomous_trial_completeness.py`
   - `test_autonomous_trial_completeness.py`

4. Registry unit
   - `trial_registry.py`
   - `test_trial_registry.py`

5. Launcher unit
   - `p3_autonomous_workload_trial.py`
   - `test_p3_autonomous_workload_trial.py`

6. Downstream unit
   - `layer3_report.py`
   - `test_layer3_report.py`

7. Evidence unit
   - `s8c_preregistration_evidence.py`
   - `test_s8c_preregistration_predicates.py`
   - `test_s8c_preregistration_invariant.py`
   - evidence contract JSON は編集しない

8. Docs unit
   - `phase3-s8c-autonomous-trial-runbook.md`

依存順は `(1, 2, 3) → 4 → 5 → 6 → 7 → 8`。同一 file を複数 unit に持たせない。

全 scope は一 wave に収めない方がよい。最小 land 可能集合は次である。

- U-4 の二入口 gate。
- U-4 formal branch に必要な U-1 launch-side capability 再検証。
- sealed launch admission の journal/report 記録。
- CLI explicit opt-in。
- U-4 negative/positive controls。
- runbook 更新。

対象は capability、registry、launcher、対応 test、runbook のみ。U-5 lifecycle、receipt、cross-binding、post-acceptance Layer 3 は次 waveへ送る。T-468 approval binding と実 certified-selection consumer は、実在 authority artifactまたは新しい人間裁定が得られるまで設計メモに留める。

## 総括

- (a) 採る U-4 設計: holdout は登録済み manifest + exact `effective_at(C)` 必須、非 holdout の manifestless run だけ明示 opt-in・non-certifying で許可する二入口 gate。
- (b) 最小 land 可能集合: U-4 + launch 側 U-1 capability 検証 + sealed admission 記録 + tests + runbook。
- (c) 最大の技術的リスク: post-run receipt を既存 pre-acceptance Layer 3 経路へ循環なく結線し、かつ別 worktree をまたぐ一回性と不在の T-295 approval authority を過大主張しないこと。