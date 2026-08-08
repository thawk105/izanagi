# 段 2 プラン案

結論は、**実装開始は現時点では NO-GO** です。resolver・receipt・sink の実装形は具体化できますが、段 4 で少なくとも次の 3 点を新 D として確定する必要があります。

1. D234 の「producer 実装 wave に validator / consumer も含む」という一文を、§11 / D162 の段 A→B→C 順序に合わせて限定する。
2. 追補 A の閉集合を `a01`〜`a13` と確定する。§15 の `a01`〜`a12` は凍結 core 内の不整合として訂正せず、解釈だけを新 D に置く。
3. `declared_use_class` の名前・4 値・「利用意図であって適格宣言ではない」という意味を確定する。

静的確認では、fold commit `F=88d68f9127b31df5aafc3d59607896626a1652e8` の core digest は `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9`、現在 HEAD は F の子孫です。作業木は clean です。pytest は実行していません。

## 一次資料の食い違いと P1 の裁定案

凍結 core §11 は明示的に次の順序です。

> 段 A producer を実装する  
> 段 B pilot を走らせる  
> 段 C それを根拠に validator と最初の消費側を実装する

根拠は [preregistration.md:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:258) です。さらに「D162 は書き換えない」と明記されています。

D162 も「機械化は発火条件が揃うまで行わない」とし、3-arm の事前登録計測、環境証明付き receipt、実 consumer hook を条件にしています。[decisions.md:8049](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/decisions.md:8049)

一方 D234 は、validator の独立再計算と consumer 受理判定まで「producer 実装 wave の責務」と書いています。[decisions.md:11065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/decisions.md:11065)

裁定案は次です。

- **P1 は維持し、scope を段 A に限定する。**
- D234 の上記一文を暗黙の D162 supersede とは読まない。D234 自身が D162 を参照し、supersede を宣言していないためです。
- 新 D で「D234 の機械配線一覧は T139 全段の完了範囲を示すが、同一 wave の実装範囲を意味しない。段 C は pilot 後」と限定する。
- validator / consumer を今広げる案は D162 決定 (10) に反するため採りません。

追補 A については、§14 の表が `a01`〜`a13` を列挙し、D234 も primary 系列の有意水準を A に含めています。[preregistration.md:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:320) [decisions.md:10999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/decisions.md:10999)  
したがって resolver は `a01`〜`a13` を要求すべきです。§15 の `a01`〜`a12` を採ると、`a13` を落として pilot 後に primary alpha を選べるため、絶対規律 3 に反します。

## ファイル計画

新設ファイルには現行行番号が存在しないため、架空の番号は付けません。既存ファイルだけ、読んだ現行行を挿入点として示します。

| path | 変更 |
|---|---|
| `orchestrator/qualification/t139_preregistration.py` | 新設。blob ref、sealed `PreregBinding`、resolver、addendum exact-key / semantic 検査 |
| `orchestrator/qualification/t139_raw_receipt.py` | 新設。closed schema 検証、単一 snapshot load、atomic publish、`verify_receipt` |
| `orchestrator/qualification/t139_raw_receipt_schema.json` | 新設。receipt の Draft-07 closed schema |
| `orchestrator/qualification/t139_submission.py` | 新設。`submit_pilot` / `submit_main` と、実際に `qsub` する sink |
| `orchestrator/qualification/t139_preflight.py` | 新設。PBS job の最初の書込み前に binding を再解決する CLI |
| `tools/pegasus/t139_paired_study.pbs` | 新設。T126 の [t126_qualification.sh:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/tools/pegasus/t126_qualification.sh:63) と同型の read-only 前置 |
| `tools/pegasus/admission_registry.json` | [line 166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/tools/pegasus/admission_registry.json:166) の `t141` entry 前へ、job body を `dispatch-required` として挿入 |
| `orchestrator/tests/test_hooks.py` | class 表は [line 1306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/tests/test_hooks.py:1306)、entry 表は [line 1471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/tests/test_hooks.py:1471) の各 `t141` 前へ挿入 |
| `orchestrator/tests/test_t139_preregistration.py` | 新設。resolver と合成 Git repo 正例 |
| `orchestrator/tests/test_t139_raw_receipt.py` | 新設。schema、未知 field、atomic publish、receipt 照合 |
| `orchestrator/tests/test_t139_submission.py` | 新設。sink 必須引数、intent-before-qsub、main の B 要求 |
| `orchestrator/tests/test_t139_pegasus_tools.py` | 新設。PBS 前置が非変異であることを検査 |
| `docs/spool/decisions/2026-08-08-dev-wave-t139-producer-1.md` | 新設、親所有。P1 限定、`a13`、`declared_use_class` を新 D 化 |
| `docs/spool/worklog/2026-08-08-dev-wave-t139-producer-1.md` | 新設、親所有。実装結果・非実走・段 C 残件を記録 |

次は変更しません。

- 凍結 core
- `trial_registry.py` — [resolve_measurement_commit:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/trial_registry.py:677)、[assert_prereg_ancestor:738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/trial_registry.py:738)、[_blob_at_commit:755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/trial_registry.py:755) をそのまま再利用する
- `s8b_oracle_artifacts.py`
- `t139_positive_control_probe.{sh,pbs}`
- `FROZEN_MANIFEST` 系の検査

## API と例外

### `t139_preregistration.py`

```python
BlobRefTuple: TypeAlias = tuple[str, str, str]


class T139PreregistrationError(RuntimeError):
    gate: str

    def __init__(self, gate: str, message: str) -> None: ...


@dataclass(frozen=True, slots=True)
class BlobRef:
    commit: str
    path: str
    sha256: str


@dataclass(frozen=True, slots=True, init=False)
class PreregBinding:
    core_ref: BlobRef
    addendum_a: BlobRef
    addendum_b: BlobRef | None
    fold_commit: str
    measurement_head: str
    pilot_admission: Literal["requires_addendum_a"]
    main_admission: Literal["requires_addendum_a_and_b"]

    def __init__(
        self,
        core_ref: BlobRef,
        addendum_a: BlobRef,
        addendum_b: BlobRef | None,
        fold_commit: str,
        measurement_head: str,
        pilot_admission: Literal["requires_addendum_a"],
        main_admission: Literal["requires_addendum_a_and_b"],
        *,
        _seal: object = None,
    ) -> None: ...


def resolve_effective_preregistration(
    repository_root: Path | str,
    *,
    core_ref: BlobRefTuple,
    addendum_a: BlobRefTuple,
    addendum_b: BlobRefTuple | None = None,
) -> PreregBinding: ...


def require_prereg_binding(
    binding: PreregBinding,
    *,
    repository_root: Path | str,
    require_addendum_b: bool,
) -> PreregBinding: ...


def prereg_binding_document(binding: PreregBinding) -> dict[str, object]: ...
```

内部 helper も署名を固定します。

```python
def _coerce_blob_ref(value: object, *, label: str) -> BlobRef: ...
def _blob_at_ref(repository_root: Path, *, ref: BlobRef, label: str) -> bytes: ...
def _parse_core_admission(
    raw: bytes,
) -> tuple[
    Literal["requires_addendum_a"],
    Literal["requires_addendum_a_and_b"],
]: ...
def _parse_addendum(
    raw: bytes,
    *,
    kind: Literal["a", "b"],
    core_ref: BlobRef,
) -> dict[str, Any]: ...
def _validate_addendum_a(fields: Mapping[str, Any]) -> None: ...
def _validate_addendum_b(fields: Mapping[str, Any]) -> None: ...
```

不正な tuple 型・文字列型には `TypeError`、Git blob 不在、digest、schema、依存三つ組、祖先、admission 不一致には `T139PreregistrationError` を送出します。

### `t139_raw_receipt.py`

```python
class T139RawReceiptError(ValueError): ...
class T139ReceiptBindingMismatch(T139RawReceiptError): ...


def validate_raw_receipt(receipt: object) -> dict[str, Any]: ...

def canonical_raw_receipt_bytes(receipt: object) -> bytes: ...

def load_raw_receipt(path: Path | str) -> dict[str, Any]: ...

def publish_raw_receipt(
    repository_root: Path | str,
    *,
    receipt: Mapping[str, Any],
) -> Path: ...

def verify_receipt(
    *,
    binding: PreregBinding,
    receipt: Mapping[str, Any],
) -> None: ...
```

`load_raw_receipt` は [artifacts.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/qualification/artifacts.py:537) の strict loader、publish は [atomic_publish.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/qualification/atomic_publish.py:24) を再利用します。

### `t139_submission.py`

```python
class T139SubmissionError(RuntimeError): ...


def submit_pilot(
    *,
    binding: PreregBinding,
    repository_root: Path | str,
) -> str: ...


def submit_main(
    *,
    binding: PreregBinding,
    repository_root: Path | str,
) -> str: ...


def _submit(
    *,
    stage: Literal["pilot", "main"],
    binding: PreregBinding,
    repository_root: Path | str,
) -> str: ...


def main(argv: Sequence[str] | None = None) -> int: ...
```

`_submit` 自身が `qsub` を実行する唯一の関数です。`submit_pilot/main` だけでなく `_submit` にも `binding` を keyword-only で要求します。

### `t139_preflight.py`

```python
def main(argv: Sequence[str] | None = None) -> int: ...
```

成功は無出力 rc=0、admission reject は JSON 1 行・rc=3、入力・Git operational failure は JSON 1 行・rc=4 とします。

## 受領証の closed schema

### 全 key

Top-level exact key は次の 18 個です。

```text
schema_version
study_id
declared_use_class
study_stage
series_id
parent_series_id
preregistration
environment
measurement_checkout
dependency_pins
arms
allocations
planned_execution
actual_runs
correctness_evidence
liveness
admission_telemetry
attempts
```

各 object の exact key は次です。

| object | exact key |
|---|---|
| `preregistration` | `core`, `addendum_a`, `addendum_b`, `fold_commit` |
| blob ref | `commit`, `path`, `sha256` |
| `environment` | `env_tag`, `attestation_mode`, `attestations` |
| attestation row | `allocation_id`, `mode`, `evidence` |
| `measurement_checkout` | `repository_head`, `ccbench_head` |
| dependency pin row | `name`, `pin_kind`, `pin`, `evidence` |
| `arms` | `stock`, `mode1`, `modeX` |
| arm row | `source`, `binary`, `compile`, `built_outside_allocation` |
| source identity | `commit`, `path`, `sha256` |
| binary identity | `path`, `sha256` |
| compile identity | `identity_sha256`, `argv` |
| allocation row | `allocation_id`, `node`, `started_at`, `ended_at`, `accounting`, `exclusivity` |
| `planned_execution` | `schedule_id`, `seed`, `runs` |
| planned run row | `run_id`, `workload`, `block_index`, `position`, `arm`, `previous_arm`, `wait_before_s` |
| actual run row | `run_id`, `workload`, `block_index`, `position`, `arm`, `previous_arm`, `wait_before_s`, `attempt_id`, `allocation_id`, `started_at`, `ended_at`, `raw_tps`, `command` |
| command evidence | `argv`, `started_at`, `ended_at`, `returncode`, `stdout`, `stderr` |
| correctness row | `arm`, `workload`, `trace_binary`, `verifier_argv`, `inputs`, `outputs` |
| liveness row | `allocation_id`, `timestamp`, `kind`, `evidence` |
| admission row | `attempt_id`, `gate`, `timestamp`, `returncode`, `stdout`, `stderr` |
| attempt row | `attempt_id`, `submission_id`, `attempt_index`, `allocation_id`, `scheduler_request_id`, `measurement_started_at`, `reason_code`, `replaces_attempt_id`, `qsub` |
| file evidence | `path`, `size`, `sha256` |

追加制約は次です。

- 全 object を `additionalProperties: false`。
- `study_id = "t139-rf-partial-recovery"`。
- `study_stage ∈ {"pilot","main"}`。
- `declared_use_class ∈ {"official","exploration","qualification","dry"}`。
- `environment.env_tag = "pegasus"`、`attestation_mode = "required"`。
- `arms` は `stock/mode1/modeX` の exact 3 arm。
- `attempt.reason_code ∈ {"completed","pre_measurement_infrastructure","post_measurement_failure","correctness_anomaly"}`。
- `main` では `addendum_b` が blob ref、pilot では `null` または binding と一致する ref。
- duplicate key、NaN/Infinity、非 canonical JSON、symlink、読取り中 inode 変化を拒否する。
- qsub 失敗 attempt は `allocation_id`、`scheduler_request_id`、`measurement_started_at` を `null` にできるが、row 自体は省略できない。

### §12 との写像

| §12 必須項目 | receipt key |
|---|---|
| core / A / B 三つ組、fold commit | `preregistration.{core,addendum_a,addendum_b,fold_commit}` |
| 環境タグ・環境証明 | `environment.{env_tag,attestation_mode,attestations}` |
| repo / CCBench HEAD | `measurement_checkout.{repository_head,ccbench_head}` |
| dependency pin | `dependency_pins[]` |
| build identity・compile argv・外部 build binary hash | `arms.*.{compile,binary,built_outside_allocation}` |
| allocation ID・node・時刻・会計・単独性 | `allocations[]` |
| 3 arm source / binary / compile identity | `arms.{stock,mode1,modeX}` |
| planned / actual order、位置、直前 arm、timestamp、TPS | `planned_execution.runs[]`, `actual_runs[]` |
| correctness の再実行可能な証拠 | `correctness_evidence[]` |
| liveness / admission telemetry | `liveness[]`, `admission_telemetry[]` |
| 全 attempt・理由・置換関係・親系列 | `attempts[]`, `parent_series_id` |
| 利用意図だけの種別 | `declared_use_class` |

適格性 field の拒否点は、JSON schema の top-level および全 nested object の `additionalProperties:false` と、`validate_raw_receipt()` の exact-key 再検査です。`qualification_status`、`pairing_valid`、`accepted`、`validator_identity`、`validator_result`、`correctness_clean` は schema に存在せず、未知 field として拒否します。

### `declared_use_class` と `artifact_role`

既存 `artifact_role` は `8b-oracle-exploration-artifact/v1` の文書部品種別で、値は `manifest / observations / verdict` です。[s8b_oracle_artifacts.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/s8b_oracle_artifacts.py:26) [s8b_oracle_artifacts.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/s8b_oracle_artifacts.py:169)

`declared_use_class` は receipt 全体の利用意図であり、別軸です。

- `official`: 正式 study で使う意図
- `exploration`: 探索限定
- `qualification`: validator へ審査提出する意図
- `dry`: 非測定 dry-run

いずれも合格・適格を意味せず、consumer の受理入力にしてはいけません。現 production code に `declared_use_class` の既存 hit はなく、`artifact_role` の意味を上書きしません。

## Admission resolver の実装対応

追補 blob の物理形式は次に固定します。

```json
{
  "schema_version": "t139-preregistration-addendum-a/v1",
  "core_ref": {
    "commit": "...",
    "path": "...",
    "sha256": "..."
  },
  "fields": {
    "a01": {},
    "...": {},
    "a13": {}
  }
}
```

B は schema version を `...addendum-b/v1`、field を `b01`〜`b03` とします。top-level は `schema_version/core_ref/fields`、`core_ref` は `commit/path/sha256` の exact key です。

| D234 条件 | 担当検査 |
|---|---|
| (i) canonical core path | `_coerce_blob_ref()` が `path.encode("utf-8")` と canonical ASCII bytes を exact 比較 |
| (ii) blob 実在、caller digest、承認済み digest | `_blob_at_ref()` が `_blob_at_commit()` で読む。同じ関数が caller SHA と照合し、さらに `F:<canonical path>` を毎回読み SHA-256 を比較 |
| (iii) core commit が F の子孫 | `assert_prereg_ancestor(repository_root, prereg_commit=F, measurement_commit=core_ref.commit)` |
| (iv) A の解決と従属三つ組 | `_parse_addendum(..., kind="a")` が addendum blob digest、`core_ref` exact key/value を照合 |
| (v) exact-key と越境禁止 | `_validate_addendum_a()` が `set(fields) == {"a01",...,"a13"}`、B は `{"b01","b02","b03"}`。a03/a04 と B の q 非関与を semantic 検査 |
| (vi) core/A/B が measurement HEAD の祖先 | `resolve_measurement_commit()` で HEAD を一度だけ導出し、各 ref に `assert_prereg_ancestor()` |
| (vii) admission 要求充足 | `_parse_core_admission()` が凍結 header の `pilot_admission` / `main_admission` を読み、A/B の存在と解決済み状態を照合 |

`measurement_head` は resolver の引数にしません。`resolve_measurement_commit()` の戻りを binding に格納します。

a03/a04 の構造は少なくとも次を要求します。

- a03: `metric_source.kind="allocation_observation"`、非空 evidence pointer、上下端が有限で `lower < upper`。literal / constant source、無限区間、範囲なしを拒否。
- a04: `before_measurement` と `after_measurement` を分離し、後者に `pre_measurement_infrastructure` を指定できない。
- B の schema には primary alpha、`q`、critical value を置ける key を作らない。

ただし「実装が実際には定数を返す」「有限だが物理的に常に通る範囲」は静的 resolver だけでは証明できません。段 C validator が raw evidence から再計算する必要があります。

## Sink 側認可

既存 D235 の閉包は、上位 caller ではなく [pipeline.evaluate:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/pipeline.py:476) の必須 keyword-only `authorization_contract` に置かれ、実処理前の [line 595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/pipeline.py:595) で検査されます。loop と screening は単にそれを渡す呼出し経路です。[loop.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/loop.py:255) [screening_driver.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/screening_driver.py:187)

T139 の経路は次に固定します。

```text
t139_submission.main
  -> resolve_effective_preregistration(...)
  -> submit_pilot(*, binding=...) / submit_main(*, binding=...)
  -> _submit(*, binding=...)
       -> require_prereg_binding(...) で現在 HEAD から全条件を再解決
       -> submission-intent.json を create-only publish
       -> subprocess.run(["qsub", ..., "tools/pegasus/t139_paired_study.pbs"])
```

`subprocess.run(["qsub", ...])` は `_submit` 本体に直接置きます。binding を受けない `_run_qsub()` のような下位関数は作りません。これにより、新 caller が `submit_pilot/main` を飛び越えても、実 sink の signature で止まります。

PBS 側も二重化します。

```text
t139_paired_study.pbs
  -> admission document を read-only で開く
  -> commit blob の t139_preflight.py を stdin 実行
  -> resolver が binding / HEAD / refs を再解決
  -> 成功後に初めて mkdir / trap / staging / producer write
```

T126 では qsub invocation claim が [submit_t126_qualification.sh:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/tools/pegasus/submit_t126_qualification.sh:677) で qsub より先に作られています。この順序を踏襲します。

なお、新 PBS wrapper の測定本体は追補 A の a01〜a09 が未確定なため、現 brief からは完全には起草できません。**前置だけを持つ空 wrapper を land して「producer 実装済み」と数えてはならない**ため、P5 は追補 A または固定 producer body の指定が stage 4 で得られるまで blocker です。

## §13 否定検査の帰属と変異

新設ファイルには実在 line がないため、変異位置は `path::symbol` で示します。数字を捏造しないためです。実装後の mutation preregistration では、その commit の実 line に再固定します。

| # | 帰属 | 変異位置・置換 | kill する検査 |
|---|---|---|---|
| 1 failed 投入を ledger/raw 双方から落とす | 段 A | `t139_submission.py::_submit` の intent publish を削除し qsub へ直行。同時に `t139_raw_receipt.py::publish_raw_receipt` の `receipt_attempt_ids == intent_attempt_ids` を `<=` に変更 | intent が qsub より前に存在し、receipt が intent 全件を exact 被覆する検査 |
| 2 親系列 ID で alpha reset | 段 C | 将来 validator の canonical root 再導出を `receipt["parent_series_id"]` 信用へ置換 | 段 C の累積台帳 test |
| 3 anomaly を clean と申告 | 段 A | schema に `correctness_clean: boolean` を追加、または evidence row を bool に置換 | evidence pointer 以外を未知 field として拒否 |
| 4 適格性 field を追加 | 段 A | top-level `additionalProperties:false` を `true` へ置換 | `qualification_status/pairing_valid/validator_result` の各拒否 test |
| 5 `J-1` cluster を受理 | 段 C | 将来 validator の `observed_j == preregistered_j` を `>= preregistered_j - 1` に置換 | 段 C sample-size test |
| 6 order 不一致 / wait 不足を受理 | 段 C | 将来 validator の planned/actual exact 比較、wait 下限比較を no-op 化 | 段 C schedule/wait test |
| 7 core 別 blob / 追補余剰 | 段 A | `_blob_at_ref`: approved digest 比較を caller digest との自己整合だけへ置換。`set(fields) == expected` を `expected <= set(fields)` へ置換 | fold digest test、missing/extra exact-key test |
| 8 a03 恒真 / post failure を pre failure へ写す | 段 A | `_validate_addendum_a` の constant/finite-range 拒否を削除。`after_measurement` に pre-measurement code を許可 | a03/a04 parameterized test |
| 9 fold 前 checkout を受理 | 段 A | `F -> core_ref.commit` の ancestor 検査を削除または向きを逆転 | F と別 branch の pre-fold fixture rejection |

## テスト計画

### `test_t139_preregistration.py`

- `test_resolver_accepts_descendant_core_and_exact_addendum_a_in_synthetic_repo`
- `test_resolver_derives_measurement_head_from_checkout`
- `test_resolver_signature_has_no_measurement_head_parameter`
- `test_resolver_rejects_noncanonical_core_path`
- `test_resolver_rejects_missing_blob_and_wrong_declared_digest`
- `test_resolver_rejects_core_digest_different_from_fold_blob`
- `test_resolver_rejects_core_commit_not_descended_from_fold`
- `test_resolver_rejects_addendum_core_triple_mismatch`
- `test_resolver_rejects_missing_or_extra_addendum_a_key`
- `test_resolver_requires_a13`
- `test_resolver_rejects_missing_or_extra_addendum_b_key`
- `test_resolver_rejects_constant_or_unbounded_recovery_rule`
- `test_resolver_rejects_post_measurement_failure_remap`
- `test_resolver_rejects_nonancestor_core_and_addenda`

正例 fixture は monkeypatch で F を差し替えません。

1. tmp repo を `git init`。
2. 現 repo から実 F object/history を fetch。
3. F から子 commit C を作る。core bytes は変更しない。
4. C の三つ組を記した `a01`〜`a13` exact 追補 A を C2 に commit。
5. HEAD=C2 で public resolver を呼び、`measurement_head == C2` と成功を確認。

これで production 定数と production resolver を通し、gate が恒真 deny でないことを示します。

### `test_t139_raw_receipt.py`

- `test_valid_raw_receipt_round_trips_canonical_json`
- `test_declared_use_class_is_required_and_closed`
- `test_artifact_role_is_unknown_in_t139_receipt`
- `test_eligibility_and_validator_fields_are_unknown`
- `test_correctness_boolean_claim_is_rejected`
- `test_duplicate_nonfinite_noncanonical_and_symlink_inputs_are_rejected`
- `test_all_attempt_intents_must_have_exact_receipt_rows`
- `test_atomic_publish_reuses_only_identical_bytes`
- `test_verify_receipt_accepts_matching_binding`
- `test_verify_receipt_rejects_each_core_addendum_fold_and_head_mismatch`
- `test_verify_receipt_does_not_compute_eligibility`

### `test_t139_submission.py`

- `test_submit_functions_require_keyword_only_binding`
- `test_forged_or_stale_binding_stops_before_qsub`
- `test_submit_pilot_accepts_a_only_binding`
- `test_submit_main_rejects_binding_without_addendum_b`
- `test_submission_intent_is_durable_before_qsub`
- `test_failed_qsub_attempt_remains_in_intent_authority`
- `test_private_qsub_sink_also_requires_binding`

### `test_t139_pegasus_tools.py`

- `test_pbs_script_passes_bash_syntax`
- `test_preflight_rejection_is_nonmutating_and_starts_no_producer`
- `test_preflight_success_reaches_the_first_write_sentinel`
- `test_preflight_helper_is_loaded_from_binding_source_commit`
- `test_static_preflight_precedes_mkdir_trap_and_redirect`
- `test_positive_control_probe_bytes_are_unchanged`

テスト実測は親が `tools/run_tests.py` 経由で行います。この段 2 では未実行です。

## 並列分割

| 単位 | 所有ファイル | 依存 |
|---|---|---|
| U0 親裁定 | decisions fragment のみ | 最初。P1、a13、field 名を確定 |
| U1 resolver | `t139_preregistration.py`, `test_t139_preregistration.py` | U0 |
| U2 receipt | `t139_raw_receipt.py`, schema JSON, `test_t139_raw_receipt.py` | U1 の `PreregBinding` API |
| U3 sink / preflight | `t139_submission.py`, `t139_preflight.py`, PBS、submission / Pegasus tests | U1。P5 の producer body が確定していること |
| U4 registry | `admission_registry.json`, `test_hooks.py` | U3 の path 確定後 |
| U5 親記録 | worklog fragment、必要なら決定 fragment の実績補足 | U1〜U4 と親の実測後 |

U2 と U3 は U1 の API commit を展開した後に並列化できます。編集所有はすべて素集合です。U4 は新 path が確定してから行い、U5 は実装 worker に渡しません。

## 総括

- 段 A の resolver・receipt・sink だけを実装し、validator / consumer は段 C へ送る。
- F 時点 blob を毎回読み、caller 自己整合ではなく承認済み digest と照合する。
- 追補 A は `a01`〜`a13`、B は `b01`〜`b03` の exact-key とする。
- receipt は raw evidence だけを持ち、適格性・pairing・validator field を未知 field として拒否する。
- qsub 実体 `_submit` 自体に必須 keyword-only `binding` を置く。
- 合成 Git repo の通る正例を必須にする。
- **判定: NO-GO。** P1/D234 の限定、新 D、追補 A/PBS body の仕様確定後に GO。