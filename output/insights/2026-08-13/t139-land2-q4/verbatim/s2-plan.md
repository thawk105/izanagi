結論は **NO-GO** です。(P1) の三点セットは R3(a) に適合しません。所有層の観測値を増やしても、`submit_pilot` が driver handoff を生成できる入力は #4〜#6 が未実装である限り存在せず、admission の受理集合は空のままです。

以下の file:line 設計は、段 4 で blocker を解消する裁定が出た場合の条件付き案です。現状のまま段 5 へ渡してはいけません。

## (A) file:line 粒度の実装プラン

### A.1 新規ファイルと公開 API

| 新規 path | 責務 | 公開 API |
|---|---|---|
| `orchestrator/preregistration/pilot_release.py` | local `main` ref の単一 snapshot から解除 decision を読む。working tree、spool、handoff、環境変数を読まない | `resolve_pilot_release() -> PilotReleaseDecision`。package-level には export しない |
| `orchestrator/preregistration/pilot_submission.py` | 9 前提の逐次判定、create-only intent、driver handoff。qsub は呼ばない | `submit_pilot(*, submission_id: str) -> PilotSubmissionResult` |
| `orchestrator/preregistration/pilot_schedule.py` | `a09` の意味的 schedule を再導出する純関数 | `a09_key(...) -> bytes`、`generate_a09_schedule() -> tuple[A09Block, ...]`、`pilot_a09_schedule() -> tuple[A09Block, ...]`、`render_operational_schedule() -> bytes`、`operational_schedule_digest() -> str` |
| `tools/pegasus/run_t139_pilot.py` | compute-side preflight、検証割当て、性能 slot の 36 run、失敗 evidence の create-only 記録 | `run_pilot_job(*, submission_id: str, attempt_id: str, environ: Mapping[str, str] | None = None) -> int` |
| `tools/pegasus/t139_pilot.pbs` | `gen_S`、1 時間、静的な canonical-main job wrapper | CLI／環境契約のみ。`T139_SUBMISSION_ID` と `T139_ATTEMPT_ID` を厳格検査 |
| `tools/pegasus/submit_t139_pilot.py` | login-side qsub 境界。handoff 再検査、qsub raw の create-only 保存 | `dispatch_pilot(*, submission_id: str, run_command: CommandRunner = subprocess.run) -> PilotDispatchResult`、`main(...) -> int` |
| `tools/pegasus/collect_t139_pilot.py` | qsub failure と job preflight reject を operational attempt fragment に回収 | `collect_pilot(*, submission_id: str) -> PilotCollectionResult`、`main(...) -> int` |
| `orchestrator/tests/test_t139_pilot_submission.py` | 解除権威、9 前提、intent durability、producer claim 非依存 | テストのみ |
| `orchestrator/tests/test_t139_pilot_driver.py` | schedule、PBS preflight、qsub 注入 seam、trace 分離 | テストのみ |
| `orchestrator/tests/test_t139_pilot_collector.py` | exact 12 key、全 intent 被覆、raw pointer、ID 束縛 | テストのみ |

### A.2 `submit_pilot` の署名・戻り値・拒否 enum

提案する公開面は次です。`repository_root`、`claim_scope`、`pilot_ready`、`released`、`a12_passed`、schedule、cluster slot、qsub stdout を受けません。

```python
class PilotRejectionReason(str, Enum):
    P01_PILOT_RELEASE_NOT_FOLDED = "p01_pilot_release_not_folded"
    P02_ALPHA_RESERVATION_NOT_FIXED = "p02_alpha_reservation_not_fixed"
    P03_STRESS_CHECK_NOT_COMPLETED = "p03_stress_check_not_completed"
    P04_RECEIPT_SCHEMA_NOT_BOUND = "p04_receipt_schema_not_bound"
    P05_APPROVAL_MANIFEST_NOT_AVAILABLE = "p05_approval_manifest_not_available"
    P06_PREREG_BINDING_LAYER_NOT_IMPLEMENTED = (
        "p06_prereg_binding_layer_not_implemented"
    )
    P07_DURABLE_INTENT_NOT_CREATED = "p07_durable_intent_not_created"
    P08_DRIVER_OR_COLLECTOR_NOT_BOUND = "p08_driver_or_collector_not_bound"
    P09_PILOT_SLOT_IDENTITY_NOT_FIXED = "p09_pilot_slot_identity_not_fixed"


@dataclass(frozen=True)
class PilotPrerequisiteCheck:
    number: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9]
    state: Literal["satisfied", "rejected", "not_reached"]
    rejection: PilotRejectionReason | None
    evidence: tuple[FileRecord, ...]


@dataclass(frozen=True)
class PilotSubmissionResult:
    disposition: Literal["blocked", "dispatch_handoff_created"]
    owned_layer_ready: bool
    checks: tuple[PilotPrerequisiteCheck, ...]
    rejection_reasons: tuple[PilotRejectionReason, ...]
    intent_refs: tuple[FileRecord, ...]
    handoff_ref: FileRecord | None


def submit_pilot(*, submission_id: str) -> PilotSubmissionResult: ...
```

`authorized` と `pilot_ready` は使いません。ただし名称を避けても、`dispatch_handoff_created` が admission の正例であることは変わりません。

| enum | 前提 | 再導出元 |
|---|---:|---|
| `P01_PILOT_RELEASE_NOT_FOLDED` | #1 | local `refs/heads/main` の [`docs/decisions.md`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/docs/decisions.md:13581) から exact payload を読む。D292 に従い working tree／fragment は不採用 |
| `P02_ALPHA_RESERVATION_NOT_FIXED` | #2 | [`approval_payload.py:129`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/preregistration/approval_payload.py:129) の D282 descriptor と、main snapshot の [`t139-alpha-reservations.jsonl:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/registry/t139-alpha-reservations.jsonl:1) を byte／digest／exact 1 行で照合 |
| `P03_STRESS_CHECK_NOT_COMPLETED` | #3 | commit `2ec790ce...`、SHA-256 `eaf2d51d...` の [`stress-check-simulation.json`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/env/pegasus/t139-a12-stress-check/full-v1/stress-check-simulation.json:1)。60 セル、B、Cartesian product、Clopper-Pearson 上界を再計算し、`claim_scope` は読まない |
| `P04_RECEIPT_SCHEMA_NOT_BOUND` | #4 | [brief:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:67) の固定状態。現 scope では binding API がないため compile-time deny |
| `P05_APPROVAL_MANIFEST_NOT_AVAILABLE` | #5 | [brief:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:68) の固定状態。D282 `F_r`／D291 `F_p` の二重 exact 閉包を新設しないため deny |
| `P06_PREREG_BINDING_LAYER_NOT_IMPLEMENTED` | #6 | [brief:69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:69) と [§6.10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:719)。resolver／`PreregBinding`／認可済み receipt writer がないため deny |
| `P07_DURABLE_INTENT_NOT_CREATED` | #7 | prior checks 成功後だけ O_EXCL、全量 write、file fsync、parent fsync、read-back digest で再導出。[§4.13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:450) |
| `P08_DRIVER_OR_COLLECTOR_NOT_BOUND` | #8 | main snapshot 上の job／submitter／collector bytes、wire schema、preflight 契約を再読して handoff に固定。caller の存在申告は使わない |
| `P09_PILOT_SLOT_IDENTITY_NOT_FIXED` | #9 | `a09` の seed と `key(j,w,p)` から全 schedule を再生成し、pilot prefix が exact slots 1〜8 であることを確認。[a09:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:552)、[§6.8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:677) |

#4〜#6 は「入力から再導出可能な正例」がありません。ここを compile-time deny とすること自体が今回の NO-GO の根拠です。

### A.3 canonical release resolver

識別子には節見出しではなく、canonical decision 節内の exact machine-readable payload を使います。

```text
decision_kind = t139-pilot-submission-release/v1
supersedes_pilot_submission = D292
supersedes_submit_pilot_export = D264
pilot_submission = permitted_only_via_submit_pilot
main_submission = forbidden
d264_submit_pilot_export = permitted
addendum_p_blob = not_approved
p03 = not_determined
source_main_run_gate = not_implemented
```

設計契約は次のとおりです。

- resolver は `Path(__file__)` を repository locator にだけ使い、Git common dir から `refs/heads/main^{commit}` を一度解決します。
- `git show <captured-main>:docs/decisions.md` 相当で blob を読みます。working-tree の `docs/decisions.md` は読みません。
- Git 関連環境変数を除いた環境を使い、main ref が読み取り中に動いたら intent 作成前に拒否します。
- canonical `## D<番号>.` 節内に payload が exact 1 件だけあること、exact key 集合、UTF-8、値を検査します。
- heading は構造境界としてのみ使います。fold 時まで D 番号が不明で、題名は prose drift するため識別子にはしません。
- private bytes parser は fixture でテストできますが、公開 resolver に bytes／root の注入口は作りません。
- 親が書く候補は新規 `docs/spool/decisions/2026-08-13-dev-wave-t139-land2-q4-1.md`。resolver はこの fragment を読みません。
- decision は pilot のみを解き、`main_submission` と D291 の他 3 field を維持します。
- D308 の commit 同居を機械執行する機能は追加しません。

### A.4 `a09` 意味的 schedule

`pilot_schedule.py` の契約は以下です。

- seed は `7df15572...b2615d`。
- `j = 1..13`、`w ∈ {W1,W2}`、`p ∈ {SDX,SXD,DSX,DXS,XSD,XDS}`。
- key は ASCII、末尾 newline なしの  
  `SHA-256("t139-a09-v1|" + seed + "|" + dec(j) + "|" + w + "|" + p)`。
- 各 workload の 6 permutation を `(digest raw bytes, p ASCII)` 昇順に並べ、`block_index` は workload-local 1〜6。
- slot 昇順。奇数 slot は W2→W1、偶数 slot は W1→W2。
- 全 schedule は `13 × 2 × 6 = 156` semantic block。
- pilot は slots 1〜8、`8 × 2 × 6 = 96` block、各 block 3 arm なので 288 run。
- replacement attempt は対象 slot の schedule を再利用し、新しい slot を作りません。
- TPS、失敗理由、runtime 乱数、caller schedule を API 入力にしません。

transport bytes は `t139-a09-operational-schedule/v1` の JSON とし、必ず `authority = "operational-only"` を持たせます。digest 名は `operational_schedule_digest` だけです。

`planned_execution.schedule_sha256`、`schedule_sha256`、canonical TSV、157 行 header 表は生成しません。driver は digest だけでなく JSON を semantic tuple へ戻し、独立生成した tuple と照合します。

### A.5 PBS driver・collector・durable intent の分界

`submit_pilot` は canonical main snapshot と全前提を検査し、成功時だけ intent と handoff を作ります。qsub は呼びません。

intent は検証割当て用 1 件と、性能 slot ごとの attempt 用に作ります。各 intent は create-only で、少なくとも以下を固定します。

- submission／attempt ID
- captured local-main commit と release payload digest
- allocation kind と `cluster_slot_or_null`
- operational schedule FileRecord
- job script／runner／collector FileRecord
- a12／α reservation evidence reference
- trace／analysis build kind
- parent／replacement attempt identity

`dispatch_pilot` だけが qsub を呼びます。テスト seam は keyword-only `run_command` です。CLI から runner を指定する option は作りません。qsub argv は [`dispatch_compute.py:1477`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/tools/pegasus/dispatch_compute.py:1477) の形に合わせ、project `SFC`、queue `gen_S`、`-b 1`、`elapstim_req=01:00:00`、job name、静的 PBS script を exact 配列で組みます。

job 側は benchmark process より先に以下を再検査します。

- `PBS_JOBID` と attempt identity
- canonical main release、intent、operational schedule
- validation allocation が作った immutable binaries
- 性能 build が `CCBENCH_TRACE=0`／`CCBENCH_ADD_ANALYSIS=0`
- correctness/liveness が別 allocation の `TRACE=1`／`ADD_ANALYSIS=1`
- slot ごとの exact 36 run、phase cap、固定 wait、a03 観測窓

preflight reject は O_EXCL の evidence を書き、`performance_started` marker と exec より前に停止します。ただし a03 不成立は仕様どおり開始後 failure に分類し、予備置換しません。

collector は qsub を呼ばず、次の exact 12 key の operational attempt row を作ります。

```text
attempt_id
cluster_slot_or_null
reason_code
replaces_attempt_id
parent_attempt_id
allocation_id
submitted_at_monotonic_ns
intent_ref
qsub_result
performance_started_marker
environment_observations
failure_evidence
```

- qsub failure でも row を省略せず、`allocation_id = null`。
- `qsub_result.raw` は rc／stdout／stderr の create-only raw FileRecord。
- job preflight reject は `failure_evidence.pointer` へ結びます。
- durable intent と attempt row は exact 1:1。欠落、余剰、重複を拒否します。
- collector 出力は operational fragment であり、受領証 publish、§7.1 semantic validator、`schedule_sha256` を実装しません。

### A.6 既存ファイルの変更点

| 既存箇所 | 条件付き変更 |
|---|---|
| [`orchestrator/preregistration/__init__.py:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/preregistration/__init__.py:1) と [`:8`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/preregistration/__init__.py:8) | package docstring を pilot-only gate の存在に更新し、`PilotPrerequisiteCheck`、`PilotRejectionReason`、`PilotSubmissionResult`、`submit_pilot` を export。`PreregBinding`／receipt API は export しない |
| [`addendum_envelope.py:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/preregistration/addendum_envelope.py:1)、[`blobref.py:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/preregistration/blobref.py:1)、[`erratum.py:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/preregistration/erratum.py:1) | 「本 wave では実装しない」を「本 module では提供しない」へ変更。各 leaf module が gate でない契約は維持 |
| [`test_t139_preregistration_binding.py:904`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/tests/test_t139_preregistration_binding.py:904) | forbidden 集合から `submit_pilot` だけを除去。変更後は `resolve_effective_preregistration`、`PreregBinding`、`verify_receipt`、`verify_prereg_receipt`。別 assertion で `submit_pilot` と結果型の package export を要求 |
| [`test_t139_stress_check_simulation.py:21`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/tests/test_t139_stress_check_simulation.py:21) | `FORBIDDEN_D264_NAMES` から `submit_pilot` だけを除去。変更後は 3 名。なお [`423-429`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/tests/test_t139_stress_check_simulation.py:423) には `stress_check_simulation` leaf 自体が `submit_pilot` を持たない assertion を別理由で残す |
| [`tools/pegasus/admission_registry.json:160`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/tools/pegasus/admission_registry.json:160) | 新規 4 実行体を exact 登録。job runner／PBS は `dispatch-required`。submitter／collector は入力 cap を証明できた場合だけ `local-ok` |
| [`tools/pegasus/README.md:17`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/tools/pegasus/README.md:17) | 実行 site 表と、pilot の login→compute→collector 手順を追加 |
| `docs/spool/decisions/2026-08-13-dev-wave-t139-land2-q4-1.md` | 親のみ。pilot release と D264 の `submit_pilot` 禁止解除を同じ decision に置く |

変更しない箇所も明示します。

- [`approval_payload.py:166-175`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/preregistration/approval_payload.py:166) は内部で、resolver が導出した root を渡して再利用します。package export はしません。
- [`qualification/submission.py:143-164`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/orchestrator/qualification/submission.py:143) は変更しません。現行コードは既に short-write loop と file／directory fsync を持つため、protocol だけを新規 intent writer へ写します。
- [`dispatch_compute.py:350-365`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/tools/pegasus/dispatch_compute.py:350) と [`1466-1505`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/tools/pegasus/dispatch_compute.py:1466) は変更せず、runner seam と qsub argv の参考に限定します。
- [`collect_receipt.py:33-64`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/tools/pegasus/collect_receipt.py:33) は変更せず、strict JSON／FileRecord pattern の参考に限定します。
- `main_submission`、approval manifest、`PreregBinding`、receipt writer、semantic validator、canonical schedule は実装しません。

## (B) (P1) の評価

### 判定

(P1) は R3(a) に適合しません。

`A(x)` を「`submit_pilot(x)` が qsub 可能な driver handoff を生成する」とし、`O(x)` を「所有層が ready と報告する」とします。R3 が制約するのは admission の `A` です。(P1) が非空にするのは補助観測 `O` にすぎません。

#4〜#6 が未実装なので、全入力について `A(x) = false` です。`owned_layer_ready`、拒否理由、`authorized` という単語の不使用は、この受理集合を変えません。

| R3 が挙げた実装 | 所有層の提案テスト | 最終 admission | 区別できるか |
|---|---|---|---|
| 正しい gate | #1〜#3、#8、#9 は ready。#4〜#6 で block | 常に block | 正しいという正例を作れない |
| `a09`／`a12` 不在で拒否 | 実 a12 と生成 a09 を使うテストで owned layer が reject から ready へ変わる | 常に block | 所有層では区別可能 |
| binding を一度も検査せず常に拒否 | `prerequisite_layer_not_implemented` を定数で返せば正しい候補と同じ出力を作れる | 常に block | **区別不能** |
| どの入力も読まず `raise` | structured result を要求すれば区別できる | raise | 表面的には区別可能 |

特に 3 行目が残るため、「4 実装すべてを区別する」という [brief:86-90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-land2-q4/s1-brief.md:86) の主張は成立しません。

さらに二つの矛盾があります。

- #7 の durable intent は、正しい順序では最終 admission 成功後、qsub より前に作ります。#4〜#6 が deny なら作れず、所有 6 前提の正例に #7 を含められません。
- deny の前に intent を作って #7 を満たすと、拒否された submission の intent が残ります。§4.13 の全 intent exact 被覆を満たすには qsub を呼んでいない attempt の `qsub_result` を発明する必要があり、不適合です。
- test fixture 内の release decision は parser の正例にはなりますが、D292 が要求する canonical fold の正例ではありません。
- 「canonical に marker があれば payload が一致する」という条件付きテストは、land 前には前件偽です。D308 が問題にした「一度も発火しない束縛検査」に当たり、R3 の正例には数えられません。
- D264 は [`12199-12204`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-q4/docs/decisions.md:12199) で空実装・恒真 deny stub を明示的に却下しています。

採れる代案は二つありますが、どちらも今回の裁定 scope 外です。

1. #4〜#6 を実装し、実 binding を通る入力から `dispatch_handoff_created` が得られる本当の正例を同じ land に入れる。これは明示的な scope 拡大です。
2. 成果物を `prepare_pilot_operational_assets` として schedule／driver／collector だけに限定し、`submit_pilot` export と解除 decision を延期する。これは scope 縮小です。

したがって、現 scope を広げも狭めもしない条件では代案はなく、**NO-GO** です。

## (C) 検査の純増検出力

以下は blocker 解消後の条件付き test inventory です。

| 新設検査 | 無い場合に変わるもの |
|---|---|
| `test_submit_pilot_signature_has_no_authority_inputs` | caller が root、release bool、claim、slot、schedule を選べる API が入り、受理集合が拡大する |
| `test_release_reads_one_exact_payload_from_local_main_ref_only` | worktree／spool／env の未 fold decision が #1 を満たし、release reference が変わる |
| `test_release_preserves_main_and_other_d291_states` | pilot release が `main_submission` や他 3 field まで動かす |
| `test_no_producer_declared_fields_reach_admission` | `claim_scope` や §8 の申告 field が gate 入力となり、producer が受理を選べる |
| `test_alpha_reservation_rederived_from_d282_and_main_blob` | ordinal、family root、ledger bytes が違っても #2 が通る |
| `test_a12_completion_recomputed_without_claim_scope` | `pilot_ready`／`verdict` の自己申告だけで #3 が通る、または 60 セルの欠落を受理する |
| `test_unimplemented_4_5_6_block_before_intent_or_handoff` | 未実装層を飛ばして handoff／intent が生成され、受理集合が非裁定に広がる |
| `test_all_intents_are_create_only_and_fsynced_before_handoff` | intent の bytes、存在順序、FileRecord が qsub 後に変えられる |
| `test_existing_intent_is_not_overwritten` | 同一 path の intent digest が attempt 間で変化する |
| `test_a09_key_and_order_golden` | permutation 順が実装値や runtime 乱数で変わる |
| `test_a09_full_domain_and_pilot_prefix` | slot／workload／block の件数、pilot の 288 run、消費 slot が変わる |
| `test_a09_parity_and_replacement_reuse_slot` | 先行 workload の均衡または replacement の slot identity が変わる |
| `test_operational_transport_never_emits_schedule_sha256` | operational digest が canonical receipt field を占有し、閉包 4 を無断採用する |
| `test_submitter_exact_qsub_argv_uses_injected_runner` | project、queue、walltime、job script が変わる。またはテストが実 qsub を呼ぶ |
| `test_submitter_refuses_unbound_handoff_before_runner` | `submit_pilot` を経ない raw qsub が scheduler request を作れる |
| `test_job_preflight_rejects_before_marker_or_exec` | forged handoff が performance marker／benchmark process まで進む |
| `test_performance_and_correctness_allocations_are_separate` | trace-enabled code が性能成果物へ混ざる |
| `test_qsub_raw_is_create_only_for_every_returncode` | qsub failure の raw reference が欠落・上書きされる |
| `test_qsub_failure_attempt_has_exact_12_keys` | qsub failure row が省略され、`attempts[]` の母集合が縮む |
| `test_preflight_reject_binds_failure_pointer` | job-side reject の原因 pointer が消える、または別 attempt を指す |
| `test_attempts_exactly_cover_durable_intents` | 欠落／余剰／重複 attempt が receipt 下流へ流れる |
| `test_collector_rejects_symlink_digest_and_job_id_mismatch` | FileRecord が別 bytes／別 job の証拠を参照する |
| `test_collector_is_operational_only` | collector が未認可の receipt writer／semantic validator／canonical schedule を名乗る |
| D264 の既存 2 検査の期待値変更 | canonical decision と export 面が矛盾し、禁止解除範囲が `submit_pilot` より広がる |

次は補助検査または nit であり、R3 の正例として数えません。

- `owned_layer_ready` の理由コード順や表示文だけを固定する検査は diagnostics の値しか変えず、最終受理集合を変えません。
- land 前に前件偽となる「marker が存在すれば payload 一致」は conditional smoke にすぎません。
- dataclass の `repr`、enum 定義順、CLI help 文言、docstring の逐語一致は nit です。
- fixture だけで canonical decision を合成する検査は parser 単体検査であり、D292 の権威検査ではありません。

## (D) 見積りと並列分割

現裁定に従う実作業量は production 0 行、test 0 行です。NO-GO のため段 5 へ進めません。

blocker 解消後の条件付き見積りは次です。

| 単位 | production | test | file 所有 | 依存 |
|---|---:|---:|---|---|
| U1 release／admission／intent | 520〜680 行 | 650〜850 行 | `pilot_release.py`、`pilot_submission.py`、`test_t139_pilot_submission.py` | 先行 |
| U2 schedule／PBS／driver | 850〜1,150 行 | 850〜1,100 行 | `pilot_schedule.py`、`run_t139_pilot.py`、`t139_pilot.pbs`、`submit_t139_pilot.py`、driver test | U1 の wire contract 後 |
| U3 collector | 260〜360 行 | 350〜500 行 | `collect_t139_pilot.py`、collector test | U1 の wire contract 後 |
| U4 親 integration | 25〜45 行 | 25〜40 行 | `__init__.py`、既存 docstring、既存 D264 tests、registry、README、decision fragment | U1〜U3 後、段 4 の明示裁定後 |
| 合計 | 1,655〜2,235 行 | 1,875〜2,490 行 | — | — |

分割は U1 を先行し、その commit／patch で wire types を固定してから U2 と U3 を並列にします。U2 と U3 は同じ directory を使っても編集 file は素集合です。U4 は親だけが所有し、特に D264 の既存期待値と decision fragment を実装子へ渡しません。

静的検査のみ実施しました。Web 検索、pytest、build、qsub、pilot 投入は行っていません。worktree 差分は 0 で、未実走検査を緑とは報告しません。

## 総括

- 本 wave の現 scope に対する判定は NO-GO です。
- #4〜#6 が未実装なので、`submit_pilot` の最終受理集合は空です。
- 所有層の ready は admission の正例ではありません。
- `authorized` という名前を避けても受理集合は変わりません。
- binding を検査しない恒真 deny 実装を、提案テストでは区別できません。
- #7 の durable intent は最終 admission 前に作れず、所有層正例にもできません。
- fixture decision は parser を試せても D292 の canonical fold を証明しません。
- 条件付き marker 検査は land 前には発火せず、D308 の束縛検査になりません。
- compliant な正例には #4〜#6 の実装が必要ですが、今回は scope 外です。
- scope を守ったまま採れる代案はありません。
- 将来の resolver は local main ref の exact payload だけを権威にすべきです。
- `a09` は意味的に再導出し、digest は operational-only とすべきです。
- qsub は注入可能な driver 境界だけに置き、collector と分離すべきです。
- D264 の期待値変更は段 4 の明示裁定後に親が渡すべきです。
- Web、pytest、build、qsub は実行しておらず、変更も加えていません。