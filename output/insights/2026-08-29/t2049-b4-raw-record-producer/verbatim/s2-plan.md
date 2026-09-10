## 現状の確認

親の主要前提に食い違いはなかった。静的読解と実 artifact の確認結果は次のとおり。

- raw schema は [`p3_b4_analysis_adapter.py:37`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_adapter.py:37) の `p3-b4-raw-analysis/v1` で、top/block/arm の exact key set は [`p3_b4_analysis_adapter.py:175`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_adapter.py:175) で閉じている。JSON は [`p3_b4_analysis_adapter.py:390`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_adapter.py:390) で `parse_float=Fraction` により bytes から読むため、decoded mapping や binary float を経由した入力は受けない。
- non-executed 5 分類は [`p3_b4_analysis_adapter.py:474`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_adapter.py:474) で全て `missing` へ写る。COMMIT/success、ABORT/diff-quarantine/rejected、その他 ABORT/fail の写像も同所で確定している。
- `evaluate_b4_artifacts` は [`p3_b4_analysis_path.py:174-196`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_path.py:174) で raw の block 順、各 block の arm 順に宣言 hash を列挙し、受領 bytes 列と一対一、同順、重複なしで照合する。統合順序は [`p3_b4_analysis_path.py:199-365`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_path.py:199) に固定されている。
- source artifact の意味を独立再導出する producer は存在しない、という自己申告も [`p3_b4_analysis_path.py:1-16`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_path.py:1) で確認した。
- closure は [`p3_b4_analysis_path.py:67-73`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_path.py:67) の 5 file であり、consumer は [`p3_b4_analysis_prereg_consumer.py:751-754`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:751) で AST literal 一致を要求する。新 module はここへ加えない。
- 実 WAL は [`model.py:23-32`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/model.py:23) の小文字 `commit` / `abort` を使う。実 campaign の [`runs/wal.jsonl:5`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:5) には `fitness_tps:491796.5` があり、[`loop_state.json:5`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/loop_state.json:5) には 4 whiteboard 行がある一方、WAL の COMMIT は 3 件だった。WAL と checkpoint を行番号や件数だけで対応させてはならない、という親の観測を再確認した。
- この実 campaign の [`campaign.lock:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/campaign.lock:1) は `reflux:"on"` を持つが `b4_protocol` marker を持たず、root に `b4_launch_context.json`、critic receipt、consumption record もない。値域確認には使えるが、正式 B-4 の通る正例には使えない。

追加で明らかになった設計上の注意が二つある。

- campaign root だけでは critic receipt を発見できない。consumption record が保存するのは receipt hash、campaign、arm、iteration、pair id であり、元 receipt の path は保存しないためである [`p3_s4_loop.py:1310-1324`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1310)。したがって producer API は on/off terminal receipt path を証拠 locator として受け、内容、hash、campaign、arm を自ら検証する必要がある。
- `drive_iteration` の `stop_reason` は戻り値と表示にしか残らず [`p3_s4_loop.py:1480-1490`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1480)、checkpoint schema に stop reason はない [`p3_s4_loop.py:727-739`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:727)。producer は推測せず、source artifact に `observed` / `not-applicable` / `missing` の状態付きで記録する。

親報告の 49 passed は今回は再実行していない。read-only 制約に従い、確認は静的読解だけである。

## 実装 plan

### 変更面

新規追加だけに閉じる。

- `orchestrator/campaign/p3_b4_raw_record_producer.py`
- `orchestrator/tests/test_p3_b4_raw_record_producer.py`

既存 5-file closure、adapter、contract、ledger、analysis path の構造は変更しない。

### 新 module の予定構成

`orchestrator/campaign/p3_b4_raw_record_producer.py` の予定 line 配置は次のとおり。

- `:1-55` — B-4 専用であること、非 scope、source artifact が外部証拠の hash binding であることを明記する module docstring と import。
- `:56-105` — schema version と閉じた enum。
- `:106-190` — 公開 dataclass。
- `:191-300` — binary float を拒否する canonical JSON serializer、十進 token、strict JSON loader。
- `:301-380` — registry/manifest の strict load、完全性再生成、block/attempt lookup。
- `:381-590` — campaign lock、sidecar、WAL、checkpoint、critic receipt、consumption record、commit receipt の同一 snapshot 読取と分類。
- `:591-680` — source artifact の exact schema 検証と raw arm への射影。
- `:681-770` — B-4 専用の排他 durable publish。
- `:771-870` — arm 1 件の逐次追記。
- `:871-1010` — 402 source artifact の完全性確認と raw 文書組立て。
- `:1011-1040` — `__all__`。CLI や `main()` は置かない。

公開型と署名は次に固定する。

```python
class B4RawEvidenceIssueCode(str, Enum):
    MISSING = "missing"
    ILL_TYPED = "ill_typed"
    NONCANONICAL = "noncanonical"
    HASH_MISMATCH = "hash_mismatch"
    BINDING_MISMATCH = "binding_mismatch"
    AMBIGUOUS = "ambiguous"
    SLOT_CONFLICT = "slot_conflict"
    PARTIAL_WRITE = "partial_write"
    DURABILITY_UNKNOWN = "durability_unknown"
    INCOMPLETE_SET = "incomplete_set"
    DECIMAL_NOT_TERMINATING = "decimal_not_terminating"


@dataclass(frozen=True, slots=True)
class B4RawEvidenceIssue:
    artifact: str
    field: str
    code: B4RawEvidenceIssueCode


@dataclass(frozen=True, slots=True)
class B4ArmArtifactRequest:
    block_id: str
    arm: B4Arm
    campaign_root: Path
    on_terminal_receipt_path: Path | None
    off_terminal_receipt_path: Path | None


@dataclass(frozen=True, slots=True)
class B4RawRecordRejection:
    schema_version: str
    block_id: str | None
    arm: B4Arm | None
    issues: tuple[B4RawEvidenceIssue, ...]


@dataclass(frozen=True, slots=True)
class B4ArmSourceArtifactWrite:
    schema_version: str
    block_id: str
    arm: B4Arm
    manifest_ordinal: int
    execution_slot: int
    path: Path
    canonical_bytes: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class B4RawAnalysisWrite:
    schema_version: str
    path: Path
    canonical_bytes: bytes
    sha256: str
    source_artifact_paths: tuple[Path, ...]
    source_artifact_bytes: tuple[bytes, ...]


def append_b4_arm_source_artifact(
    *,
    record_root: Path,
    scheduled_registry_bytes: bytes,
    analysis_manifest_bytes: bytes,
    request: B4ArmArtifactRequest,
) -> B4ArmSourceArtifactWrite | B4RawRecordRejection: ...


def assemble_b4_raw_analysis(
    *,
    record_root: Path,
    scheduled_registry_bytes: bytes,
    analysis_manifest_bytes: bytes,
) -> B4RawAnalysisWrite | B4RawRecordRejection: ...
```

`request` は disposition、precursor、throughput、treatment、contamination、protocol flag、execution slot を受けない。これらを caller 宣言にすると producer が単なる serializer になるため、全て artifact から導出する。

### 既存 module の再利用点

- registry は [`load_scheduled_attempt_registry`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_ledgers.py:702)、manifest は [`load_analysis_manifest`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_ledgers.py:1100) で canonical bytes を検証する。
- [`assert_analysis_manifest_complete`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_ledgers.py:1132) と [`verify_assignment_schedule`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_ledgers.py:1180) を arm 追記時と最終組立て時の両方で再実行する。
- lock は [`wal._decode_lock_for_b4_classification`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/wal.py:454) が返す一組の raw bytes / decoded value を使う。marker 判定は [`wal._has_exact_b4_protocol_marker`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/wal.py:481)、campaign id は [`wal._b4_campaign_id_from_lock`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/wal.py:551) から導出する。
- WAL 各 frame は [`wal.parse_line`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/wal.py:318) で exact key、duplicate、stage、payload domain を検査する。ただし出力する throughput はこの関数の float 値を使わず、同じ frame bytes を `parse_int` / `parse_float` で十進 lexeme として別途読む。
- checkpoint は [`state_from_dict`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:763) で closed schema と値域を検査する。WAL と checkpoint は [`p3_b4_closed_critic.py:731-766`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_closed_critic.py:731) と同様に前後 2 回読みし、組が変化したら拒否する。
- critic pair は [`assert_b4_arm_pair`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_closed_critic.py:1847) で terminal receipt と関連 artifact を検証する。producer はさらに terminal receipt bytes の前後一致、`evidence_class=="certified"`、campaign、arm、iteration、admission sidecar を検査する。
- COMMIT の埋込み receipt は [`validate_serialized_receipt`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/verifier/commit_receipt.py:202) へ、同じ lock snapshot の hash と WAL terminal payload を渡す。不在 lock は [`CAMPAIGN_LOCK_ABSENT_SHA256`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/verifier/commit_receipt.py:23) を使う。
- raw projection 後は [`block_status_from_raw_arm`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_adapter.py:474) と同じ条件を内部検査に使う。

### artifact ごとの読取 field

| artifact | 読む field | 根拠 |
|---|---|---|
| scheduled registry | `attempt_id`, `registry_ordinal`, `block_id`, `driver`, `initial_proposal_sha256`, reference 3 field | [`B4ScheduledAttemptInput`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_ledgers.py:123)、wire payload は [`:362-384`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_ledgers.py:362) |
| analysis manifest | `attempt_id`, `block_id`, `driver`, reference 3 field、`assignment_schedule` | [`B4AnalysisManifestRow`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_ledgers.py:181) |
| campaign.lock | B-4 marker、`reflux`、driver identity、campaign id、raw bytes hash | [`wal.py:454-581`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/wal.py:454) |
| `b4_launch_context.json` | `campaign_id`, `arm`, `driver_kind`, `admission_record_sha256`, `launch_context_sha256` | writer は [`p3_b4_launcher.py:386-429`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_launcher.py:386)、closed key 検査は [`:446-510`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_launcher.py:446) |
| critic terminal receipts | `evidence_class`, `pair_id`, `arm`, `campaign_id`, `model_snapshot`, prompt/projection/digest hash、admitted WAL hash、loop-state hash、iteration | [`B4ClosedCriticReceipt`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_closed_critic.py:233)、strict loader は [`:1436-1588`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_closed_critic.py:1436) |
| critic admission sidecar | admission record hash、expected model/prompt/projection | schema は [`p3_b4_closed_critic.py:360-388`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_closed_critic.py:360)、production writer は [`:1265-1275`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_closed_critic.py:1265) |
| consumption record | terminal receipt hash、campaign、arm、iteration、pair id、decision hash | [`p3_s4_loop.py:1310-1324`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1310) |
| WAL | suffix の terminal `stage`、ABORT `payload.reason`、COMMIT `payload.fitness_tps`、埋込み commit receipt | stage vocabulary は [`model.py:23-32`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/model.py:23)、実 writer は [`wal.py:640-669`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/wal.py:640) |
| loop state | top-level `iteration`, `start_wall`, `reverse_recommendations`; 末尾 whiteboard の `iteration`, `result` | [`p3_s4_loop.py:727-802`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:727) |

### arm source artifact の exact schema

schema version は `p3-b4-arm-source-artifact/v1`。次の key set を再帰的に閉じる。

```text
{
  schema_version: "p3-b4-arm-source-artifact/v1",

  binding: {
    manifest_sha256: sha256,
    registry_sha256: sha256,
    manifest_ordinal: int >= 0,
    attempt_id: nonempty str,
    block_id: nonempty str,
    precursor_hash: sha256,
    reference_tps: JSON decimal token,
    reference_snapshot_hash: sha256,
    reference_receipt_hash: sha256,
    assignment_schedule: ["on","off"] | ["off","on"]
  },

  identity: {
    arm: "on" | "off",
    execution_slot: 0 | 1,
    campaign_id: nonempty str | null,
    campaign_id_verified: bool,
    driver_kind: "base" | "sort" | "trigger" | null
  },

  treatment: {
    fired: bool,
    initial_snapshot_sha256: sha256 | null,
    model_snapshot: nonempty str | null,
    role_file_sha256: sha256 | null,
    effective_prompt_sha256: sha256 | null,
    projection_sha256: sha256 | null,
    digest_sha256: sha256 | null,
    pair_admitted_view_equal: bool | null,
    pair_loop_state_equal: bool | null,
    pair_iteration_equal: bool | null
  },

  outcome: {
    execution_disposition:
      "executed" | "duplicate" | "dry-pass" | "stopped-before" |
      "crash" | "terminal-record-absent",
    wal_terminal_stage: "commit" | "abort" | null,
    terminal_stage: "COMMIT" | "ABORT" | null,
    terminal_reason: nonempty str | null,
    stop_reason: {
      status: "observed" | "not-applicable" | "missing",
      value: nonempty str | null
    },
    budget: {
      status: "observed" | "missing",
      iteration_before: int | null,
      iteration_after: int | null,
      iterations_consumed: 0 | 1 | null
    },
    whiteboard_result: "success" | "rejected" | "fail" | null,
    verdict: "certified" | "rejected" | "aborted" | "missing",
    anomaly_class: nonempty str | null,
    performance_present: bool,
    throughput: JSON decimal token | null
  },

  protocol: {
    lock_snapshot_binding: check,
    b4_marker: check,
    campaign_identity: check,
    launch_sidecar: check,
    critic_admission: check,
    critic_receipt: check,
    critic_consumption: check,
    wal_terminal: check,
    checkpoint_alignment: check,
    commit_receipt: check
  },

  evidence: {
    campaign_lock_path: "campaign.lock",
    campaign_lock_sha256: sha256,
    campaign_lock_absent: bool,
    launch_sidecar_path: "b4_launch_context.json",
    launch_sidecar_sha256: sha256 | null,
    wal_path: "runs/wal.jsonl",
    wal_sha256: sha256 | null,
    loop_state_path: "loop_state.json",
    loop_state_sha256: sha256 | null,
    critic_terminal_receipt_path: str | null,
    critic_terminal_receipt_sha256: sha256 | null,
    critic_peer_terminal_receipt_path: str | null,
    critic_peer_terminal_receipt_sha256: sha256 | null,
    critic_admission_sidecar_sha256: sha256 | null,
    critic_admitted_view_sha256: sha256 | null,
    critic_loop_state_sha256: sha256 | null,
    critic_consumption_record_path: str | null,
    critic_consumption_record_sha256: sha256 | null,
    commit_receipt_id: sha256 | null,
    commit_receipt_sha256: sha256 | null
  },

  evidence_gaps: [
    {artifact: str, field: str, code: B4RawEvidenceIssueCode}
  ]
}
```

`check` は `"pass" | "fail" | "not-applicable"` の exact 3 値とする。未実行 arm では実行にしか存在しない証拠を `not-applicable` とし、開始済みなのに必須証拠が欠ける場合は `fail` とする。

§7.1 との対応は次のとおり。

- arm、campaign id: `identity.arm`、`identity.campaign_id`
- 初期 snapshot hash: `treatment.initial_snapshot_sha256`
- model/prompt/projection hash: `treatment.model_snapshot` と 3 hash
- WAL path/hash: `evidence.wal_path`、`evidence.wal_sha256`
- 停止理由: `outcome.stop_reason`
- 予算消費: `outcome.budget`
- verdict: `outcome.verdict`
- anomaly class: `outcome.anomaly_class`。ABORT では WAL `payload.reason` を改名せず格納する
- 性能値の有無: `outcome.performance_present` と `outcome.throughput`

`source_artifact_sha256` は source artifact 自身には入れない。canonical bytes を完成後に外側で hash し、raw arm だけへ書くため、自己参照を作らない。

### raw 文書の exact schema

schema は既存 adapter の key setをそのまま使う。

```json
{
  "schema_version": "p3-b4-raw-analysis/v1",
  "blocks": [
    {
      "block_id": "manifest row block_id",
      "reference_tps": 100.0,
      "reference_snapshot_hash": "sha256",
      "reference_receipt_hash": "sha256",
      "assignment_observation": ["on", "off"],
      "arms": [
        {
          "arm": "on",
          "execution_disposition": "executed",
          "whiteboard_result": "success",
          "terminal_stage": "COMMIT",
          "terminal_reason": null,
          "throughput": 491796.5,
          "precursor_hash": "sha256",
          "treatment_fired": true,
          "contaminated": false,
          "protocol_ok": true,
          "source_artifact_sha256": "sha256"
        },
        {
          "arm": "off",
          "execution_disposition": "terminal-record-absent",
          "whiteboard_result": null,
          "terminal_stage": null,
          "terminal_reason": null,
          "throughput": null,
          "precursor_hash": "sha256",
          "treatment_fired": false,
          "contaminated": false,
          "protocol_ok": true,
          "source_artifact_sha256": "sha256"
        }
      ]
    }
  ]
}
```

正確な順序規則は次とする。

- `blocks`: manifest row 順。
- `arms`: 常に `[on, off]`。実行順は `assignment_observation` にだけ持たせる。
- `source_artifact_bytes`: manifest row 順、その中で `[on, off]`。slot 順ではない。
- `assignment_observation`: source artifact の `execution_slot=0,1` を並べた arm 列。manifest schedule をコピーしない。

`protocol_ok` は source の protocol check に `"fail"` が一つもない場合に真とする。`contaminated` は receipt pair の admitted-view 不一致、または block 内二つの `initial_snapshot_sha256` 不一致を根拠に真とし、単なる証拠欠落は protocol failure で扱う。

### terminal と disposition の写像

新 module の `:470-525` に `_classify_outcome_from_snapshots()`、`:600-625` に `_raw_terminal_stage()` を置く。

- `wal stage == STAGE_COMMIT`、suffix terminal が一意、checkpoint が一世代だけ進み `result=="success"`、正の `fitness_tps` がある場合だけ `executed` / `COMMIT`。
- `wal stage == STAGE_ABORT`、`reason=="diff-quarantine"`、checkpoint が一世代だけ進み `result=="rejected"` の場合だけ `executed` / `ABORT`。
- その他の一意な ABORT と `result=="fail"` は `executed` / `ABORT`。
- receipt の admitted WAL と現在 WAL が同一で checkpoint だけ一世代進んだ場合は `duplicate`。
- receipt consumption 後、WAL suffix なし、iteration も進まず入口停止が構造的に確定できる場合は `stopped-before`。
- newline 未終端 suffix は `crash`。正しく framed されているが terminal がない場合は `terminal-record-absent`。
- formal B-4 は `--no-build` を拒否するため [`p3_s4_loop.py:1267-1272`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1267)、producer が artifact 不在から `dry-pass` を推測する分岐は置かない。

小文字から大文字への唯一の写像は次の literal dict とし、未知値に fallback を置かない。

```python
_RAW_TERMINAL_STAGE = {
    STAGE_COMMIT: B4RawTerminalStage.COMMIT,
    STAGE_ABORT: B4RawTerminalStage.ABORT,
}
```

### 十進 token

新 module `:191-300` に B-4 専用 serializer を置く。

- WAL frame は一度 `wal.parse_line` で schema 検証し、同じ frame bytes を duplicate-aware `json.loads` に `parse_int` / `parse_float` callback を渡して lexeme として読む。
- `fitness_tps` はその lexeme をそのまま source と raw の unquoted JSON number token に出す。float へ変換しない。
- manifest の `[numerator, denominator]` は `Fraction` のまま扱い、2 と 5 だけを素因数に持つ場合に限り有限十進 token へ変換する。有限十進で表せない値は `decimal_not_terminating` として拒否し、丸めない。
- private serializer は `bool`、`int`、`str`、`None`、list、dict、検証済み decimal token だけを受け、key sort、最小 separator、UTF-8、`allow_nan=False`、末尾 newline なしで canonical bytes を作る。

### 逐次追記と durability

保存 layout は次に固定する。

```text
<record_root>/
  arms/
    000-slot-0.json
    000-slot-1.json
    ...
    200-slot-0.json
    200-slot-1.json
  p3_b4_raw_analysis.json
```

- `append_b4_arm_source_artifact` は execution slot を引数に取らない。対象 block の slot 0 が空なら 0、valid な他 arm が既に占有していれば 1 とし、同 arm の再追記、壊れた既存 slot、第三件目を構造化拒否する。
- これにより first/second append が `assignment_observation` の権威になる。schedule と違う順でも拒否せず、その順を raw に残して既存 contract に protocol violation を判定させる。
- publish は同一 directory に exclusive temp を作り、`os.write` の短い書込みを loop、file `fsync`、`os.link(temp, target)` による no-replace publish、directory `fsync`、temp unlink、再度 directory `fsync` の順とする。既存 B-4 consumption writer の [`p3_s4_loop.py:1325-1393`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1325) を局所的な手本として再利用する。
- temp suffix の乱数はファイル衝突回避だけに使い、artifact、identity、認証、再実行判定へ入れない。新しい protocol nonce ではない。
- link 前の crash は target 不在なので再試行可能。link 後かつ directory fsync 前の失敗は `durability_unknown` とし、target を削除も上書きもしない。
- visible target へ直接書かないので、部分書込み target は作らない。既に存在する部分ファイルを修復する分岐も置かない。
- raw は source artifact が 201×2 全て揃い、余分、重複、壊れた canonical bytes がない時だけ同じ排他 publish で一度作る。一括 API だけにはしない。

## (P1) への立場

### (P1-a) `treatment_fired`

結論は親の provisional 裁定を支持する。off も、off 条件が閉じた critic invocation に実際に届き、赤詳細を落とした digest が検証できた場合は `true` である。

根拠は controller が arm ごとに [`make_critic_digest(... reflux=(arm=="on"))`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_closed_critic.py:882) を呼び、その digest、arm、campaign、iteration、WAL snapshot を receipt に焼くこと [`p3_b4_closed_critic.py:958-981`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_closed_critic.py:958) にある。

producer は次を全て満たす selected receipt に限り `fired=true` とする。

- on/off pair が `assert_b4_arm_pair` を通る。
- `evidence_class=="certified"`。
- selected receipt の `arm`、campaign、driver、iteration が source campaign と一致する。
- receipt bytes と関連 artifact bytes が検証中に変化しない。
- consumption record が selected terminal receipt hash と一致する。
- on では receipt の on digest、off では receipt の off digest が使われている。

off を arm label だけで偽にする分岐は置かない。contract が両 arm true を全 201 block に要求することは [`p3_b4_analysis_contract.py:727-731`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_contract.py:727) と一致する。

### (P1-b) `precursor_hash`

`precursor_hash` は caller、campaign basename、receipt 自己申告、定数のいずれからも受けない。manifest row の `attempt_id` をキーに sealed registry の一意な `B4ScheduledAttemptInput` を引き、その `initial_proposal_sha256` を使う。

source artifact には同時に `registry_sha256`、`manifest_sha256`、`manifest_ordinal`、`attempt_id`、`block_id` を持たせる。最終組立てでも registry/manifest を bytes から再ロードし、完全性を再検査して同じ lookup を繰り返すため、block 内で同じ定数を書くだけでは通らない。

これは schedule/seed issuer を新設せず、既に封印された registry を precursor の唯一の権威として使う設計である。receipt の `admitted_view_sha256` は別に `initial_snapshot_sha256` として保持し、二つを取り違えない。

### (P1-c) 逐次追記の粒度

粒度は arm 1 件である。block 1 件を待たず、各 campaign 完了直後に 1 source artifact を排他 publish する。

execution slot は引数でなく同じ block の source artifact の publish 順から決める。201 個の独立 block に各 2 slot を持つため、途中 crash でも既に durable な arm を作り直さず、全 402 件が揃った時だけ raw を組み立てられる。

この API と実行直後の呼出しを接続する sanctioned command は T-2051 の責務である。本 wave は接続を実装しないが、command が slot を自己申告できない API 形にはしておく。

### (P1-d) source artifact の自己参照

source artifact は自身の hash を含めない。代わりに次の外部 bytes を path/hash で束縛する。

- campaign.lock の同一 raw snapshot、または固定 absence digest
- launch sidecar
- 現在 WAL 全 bytes
- 現在 loop state bytes
- selected/peer critic terminal receipt
- critic admission sidecar
- receipt が保存した admitted WAL と loop-state hash
- consumption record
- COMMIT の serialized verifier receipt

COMMIT receipt の検証と B-4 marker/campaign classification は同じ `lock_snapshot` 変数だけを使う。分類用と receipt 用に `campaign.lock` を二度読む実装にはしない。

source artifact hash はこれら外部 digest を含む canonical bytes の結果であり、raw の `source_artifact_sha256` はその結果を外側から宣言する。したがって「producer が任意値を書き、その任意値自身だけを hash した」構造にはならない。

## test 設計

新規 test file は `orchestrator/tests/test_p3_b4_raw_record_producer.py` とし、予定構成は次とする。

- `:1-180` — ledger/manifest factory と production writer を通した WAL/checkpoint helper。WAL や loop-state JSON を手書きしない。
- `:181-310` — decimal、lowercase/uppercase stage、outcome classifier。
- `:311-470` — receipt、lock snapshot、precursor binding。
- `:471-620` — arm 単位 durable append、slot 順、collision、partial write。
- `:621-760` — 402 件組立て、source byte 順、raw schema、欠測保持。
- `:761-840` — closure 非変更と実 campaign regression。

通る正例は、201 block 全てについて schedule 順に on/off の「campaign root 未到達」を 402 source artifact として逐次追記するケースとする。全 row が `terminal-record-absent` から `missing` へ写り、raw parser、source hash 対応、`evaluate_b4_artifacts` を通って `indeterminate` になることを確認する。

主な負例は次のとおり。各項目で受理と拒否の含意を分ける。

- precursor を定数へ差し替える。
  受理の含意: block 内二 arm の一致だけで任意 precursor を通せ、P1-b の reward hack が残る。
  拒否の含意: registry の `attempt_id -> initial_proposal_sha256` と一致する正例だけが残る。

- lock を分類後に差し替え、古い receipt と新しい marker を組み合わせる。
  受理の含意: D1240 の二重読取 bypass が復活する。
  拒否の含意: 最初から安定した physical lock、または最初から不在の固定 digest は引き続き扱える。

- off receipt を valid にしたまま `treatment_fired=false` を期待する。
  受理の含意: 全 201 block が treatment shortage になり、実験が構造的に判定不能になる。
  拒否の含意: certified off digest が赤詳細非掲載を証明した場合は `true` になる。

- receipt pair の admitted WAL だけを不一致にする。
  受理の含意: 異なる precursor view を同じ clean pair として比較できる。
  拒否の含意: row は落とさず `contaminated=true` へ写り、contract が `indeterminate` にする。

- receipt pair の loop-state hashまたは iteration を不一致にする。
  受理の含意:予算と世代が異なる pair を treatment 差として読める。
  拒否の含意: source は残るが `protocol_ok=false` となり、protocol violation が contamination より先に立つ。

- WAL の `commit` をそのまま raw に出す、または未知 stage を uppercase 化する。
  受理の含意: adapter の closed enum を回避する別 vocabulary が生じる。
  拒否の含意: literal `commit -> COMMIT`、`abort -> ABORT` だけが通る。

- `fitness_tps:491796.5` を float 経由で再出力する。
  受理の含意: lexical decimal と binary float の差が source/raw hash と floor 境界へ混入する。
  拒否の含意:同じ WAL lexeme を保存する正例と、exact に生成できる manifest reference は通る。

- off を先、on を後に append したのに manifest schedule を raw へコピーする。
  受理の含意: assignment violation が producer 内で洗い落とされる。
  拒否の含意: raw は `["off","on"]` を保持し、既存 adapter が `assignment_followed=false` を導く。

- 同じ arm を二度 append する。
  受理の含意: duplicate producer call が反対 arm の slot を占有し、402 件の見かけ上の完全性を作れる。
  拒否の含意:既存の一意な arm artifact は変更されず、`slot_conflict` が返る。

- 片方の slot、余分な第三 artifact、壊れた canonical source artifact のいずれかを置く。
  受理の含意: file-drawer、余分な都合のよい行、部分書込みを raw 組立てで黙認できる。
  拒否の含意:exact 201×2 の正例だけが raw publish に進む。

- file write、file fsync、directory fsync を各段で失敗させる。
  受理の含意:部分 source や durable でない raw を成功として返せる。
  拒否の含意:link 前は target 不在、link 後の不確定状態は `durability_unknown` となり、既存 target は上書きされない。

- 実 campaign `p3-s4-loop-s4-autonomous-0b53a387` を formal B-4 source として与える。
  受理の含意:`reflux:on` だけで正式 marker、launch sidecar、receipt を代用できる。
  拒否の含意:同 campaign は lowercase stage と decimal field の production-format regression fixture としては使えるが、正式標本には昇格しない。

既存 [`test_p3_b4_analysis_path.py:462-549`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/tests/test_p3_b4_analysis_path.py:462) の hash swap、extra、duplicate source bytes 検査も回帰対象に含める。新 test では producer の戻す `source_artifact_bytes` をそのまま同 API へ渡し、独自の並べ替え helper を挟まない。

## 実装しないこと

- sanctioned command、CLI、`main()`、402 campaign の起動や orchestration。
- schedule/seed issuer、registry/manifest generator の変更。
- report generator、論文 cell の充填、certified-selection connection。
- `evaluate_b4_artifacts` の呼出しを production command へ接続する作業。
- analysis closure への新 module 追加、closure 5 file の AST shape や schema の変更。
- generic trial-record framework、他 ablation への抽象化。
- 新しい署名、認証 seal、protocol nonce、一回性台帳。source artifact 群は本成果物そのものであり、別の台帳は作らない。
- receipt の非保証を新しい暗号機構で閉じる作業。既存 receipt、sidecar、WAL、lock の durable projectionだけを使う。
- 欠けた stop reason、walltime、throughput、campaign id を timestamp、basename、現在時刻、既存 variant の値から補完すること。
- primary outcome の計算、verdict report、性能測定、正式 B-4 実走。
- 現在の実 campaign artifact の変更。
- この read-only 段での pytest 実行。

## 総括

新 module は arm 1 件を最小 durable 単位とし、201 block の各 2 slotへ排他追記する。source artifact は sealed registry の precursor、同一 lock snapshot、WAL、checkpoint、critic pair、consumption record、commit receiptへ束縛し、全 402 件が揃った時だけ既存 exact raw schemaを manifest順、arm `[on, off]` 順で生成する。

P1 では、off の valid treatment も `true`、precursor は sealed registry の `initial_proposal_sha256`、slot は producer の publish 順、source hash は外部証拠 digest の束として扱う。これにより新しい署名や台帳を足さず、producer と durable writer だけを埋められる。