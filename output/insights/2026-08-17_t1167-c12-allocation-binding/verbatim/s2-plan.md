## (a) 縮小後の allocation 節

現行 C12 は `single_process_required` と `single_process` / `allow_resume` を要求している (`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:455-510`)。

変更前の該当値は逐語で次のとおり。

```json
"field_paths": [
  "run_trial.env_contract",
  "run_trial.calibration_receipt",
  "run_trial.allocation_receipt",
  "run_trial.single_process",
  "run_trial.allow_resume"
],
"reachable_from": [
  "main -> run_trial -> env_contract.lookup",
  "run_trial -> execution_guard.attest_and_build_receipt",
  "run_trial -> reservation.single_process_required -> campaign launch"
]

"field_paths": [
  "lookup(env_tag)",
  "ExecutionEnvironmentContract.calibration_ref",
  "ExecutionEnvironmentContract.isolation_policy.single_process",
  "ExecutionEnvironmentContract.isolation_policy.allow_resume"
],
"reachable_from": [
  "run_trial -> lookup -> attestation and reservation consumers"
]

{
  "artifact_kind": "allocation_consumer",
  "path": "orchestrator/campaign/reservation.py",
  "field_paths": ["single_process_required(isolation_policy)"],
  "reachable_from": [
    "run_trial -> single_process_required -> campaign launch"
  ]
}

"proof": "The production 8c launcher must consume the registered environment, calibration and allocation attestations and reject multi-process or resume paths before launch."
"negative_control_id": "nc_c12_resume_or_multi_process_allowed"
"static_only_note": "Only committed enforcement reachability and attestation schemas are checked; no live allocation or post-run environment observation is required."
```

変更後の C12 全体は、次を逐語案とする。

```json
{
  "condition_number": 12,
  "required_evidence": [
    {
      "artifact_kind": "workload_supervisor",
      "path": "orchestrator/campaign/p3_autonomous_workload_trial.py",
      "field_paths": [
        "run_trial.env_contract",
        "run_trial.calibration_receipt",
        "run_trial.reservation_binding",
        "run_trial.reservation_check"
      ],
      "reachable_from": [
        "main -> run_trial -> env_contract.lookup",
        "run_trial -> execution_guard.attest_and_build_receipt",
        "run_trial -> reservation.read_binding -> reservation.check_reservation -> campaign launch"
      ]
    },
    {
      "artifact_kind": "environment_contract",
      "path": "orchestrator/campaign/env_contract.py",
      "field_paths": [
        "lookup(env_tag)",
        "ExecutionEnvironmentContract.calibration_ref"
      ],
      "reachable_from": [
        "run_trial -> lookup -> attestation consumer"
      ]
    },
    {
      "artifact_kind": "execution_guard",
      "path": "orchestrator/campaign/execution_guard.py",
      "field_paths": [
        "attest_and_build_receipt(contract, verified_calibration)"
      ],
      "reachable_from": [
        "run_trial -> attest_and_build_receipt -> campaign launch"
      ]
    },
    {
      "artifact_kind": "allocation_consumer",
      "path": "orchestrator/campaign/reservation.py",
      "field_paths": [
        "ReservationBinding.job_id",
        "ReservationBinding.boot_id",
        "ReservationBinding.deadline_epoch",
        "read_binding(environ)",
        "check_reservation(binding, required_s, safety_margin_s, environ)"
      ],
      "reachable_from": [
        "run_trial -> reservation.read_binding -> reservation.check_reservation -> campaign launch"
      ]
    }
  ],
  "consumer_requirement": {
    "path": "orchestrator/campaign/p3_autonomous_workload_trial.py",
    "entrypoints": [
      "main",
      "run_trial"
    ],
    "proof": "The production 8c launcher must consume the registered environment and calibration attestations plus a reservation binding, and before launch reject a mismatched PBS job, a mismatched boot, or insufficient time remaining before the reservation deadline."
  },
  "negative_control_id": "nc_c12_reservation_check_bypassed",
  "machine_checkable": true,
  "static_only_note": "Only committed reachability and reservation code shape for PBS job, boot and deadline binding are checked; no live allocation or post-run environment observation is required. This check does not establish process exclusivity or resume rejection."
}
```

この逐語案の projected semantic hash は `f386c2c8305b60c7f91a5457d41d6a3f146aad0a46a59e475ce4318446f81b86`。算出規則は `orchestrator/campaign/s8c_preregistration.py:389-397`。

`single_process` と `allow_resume` は両方落とす。両者は isolation policy の独立 field (`orchestrator/campaign/env_contract.py:64-77`) であり、PBS job・boot・期限を検査する `read_binding` / `check_reservation` の入力ではない (`orchestrator/campaign/reservation.py:159-175,218-270`)。特に `allow_resume` を残すと、今回明示的に失効させる resume 拒否保証を C12 に残すことになる。production の `IsolationPolicy` 自体は変更しない。

## (b) 判定器の改訂形

`field_paths` / `reachable_from` は parser が非空文字列として読むだけである (`orchestrator/campaign/s8c_preregistration_evidence.py:208-264`)。したがって C12 の hard-code を契約と同期させる。

`orchestrator/campaign/s8c_preregistration_evidence.py:288-302` 付近へ call keyword 抽出 helper、同 `:564` の直前へ次の独立 helper を置く。

```python
def _c12_allocation_binding_verdict(
    workload_supervisor: ast.Module,
    allocation_consumer: ast.Module | None,
) -> tuple[core.PredicateStatus, ReasonCode] | None:
    ...
```

判定内容は次の連言とする。

- `allocation_consumer` に top-level `read_binding` / `check_reservation` がある。
- `read_binding` が `ReservationBinding(...)` の keyword として `job_id` / `boot_id` / `deadline_epoch` を設定する。実体は `reservation.py:159-175`。
- `check_reservation` が `"PBS_JOBID"`、`binding.job_id`、`boot_id_read_fn`、`binding.boot_id`、`binding.deadline_epoch`、`_require_capacity` を消費する。実体は `reservation.py:218-270`。
- `main` から `run_trial`、`run_trial` から `read_binding` と `check_reservation` が到達可能である。

どれかが欠ければ次を返し、成立時は `None` を返す。

```python
(
    core.PredicateStatus.UNSATISFIED,
    ReasonCode.ALLOCATION_ENFORCEMENT_CONSUMER_ABSENT,
)
```

`_evaluate_c12` では現行の supervisor 欠落判定と env gate を同じ順序で残す (`s8c_preregistration_evidence.py:564-584`)。その直後で helper を呼び、非 `None` なら `_result` に変換する。helper 成立時も既存終端の `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` へ進めるだけで、`SATISFIED` は返さない (`:592-610`)。

reason code は新設不要。既存 `allocation-enforcement-consumer-absent` を維持するため、`ReasonCode` / `REASON_CODES` の値域変更も不要 (`:48-87`)。

ただし evaluator の拒否意味を変更するので、`DECIDER_VERSION` は `s8c-decider/v1` から `s8c-decider/v2` へ同一 commit で bump する (`orchestrator/campaign/s8c_preregistration.py:49-52`; D458 は `docs/decisions.md:19099-19117`)。

## (c) 実データ発火テスト

`orchestrator/tests/test_s8c_preregistration_predicates.py:99-132` の snapshot テスト群の直後へ、次の node を追加する。

```text
orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer
```

具体形は次のとおり。

```python
root, head = _snapshot_current_commit(tmp_path)
condition = M.load_contract_bytes(CONTRACT_FILE.read_bytes()).condition(12)
paths = {
    item.artifact_kind: item.path
    for item in condition.required_evidence
}
supervisor_raw = core.read_blob_at(
    root, head, paths["workload_supervisor"]
)
allocation_raw = core.read_blob_at(
    root, head, paths["allocation_consumer"]
)
assert supervisor_raw is not None
assert allocation_raw is not None

supervisor = ast.parse(supervisor_raw)
allocation = ast.parse(allocation_raw)
assert {"read_binding", "check_reservation"} <= M._functions(allocation)
assert M._c12_allocation_binding_verdict(supervisor, allocation) == (
    core.PredicateStatus.UNSATISFIED,
    M.ReasonCode.ALLOCATION_ENFORCEMENT_CONSUMER_ABSENT,
)
```

`ast` import は同テストの import 部 (`test_s8c_preregistration_predicates.py:1-20`) へ追加する。

既存 `_snapshot_current_commit` は契約の全 required path を列挙し、各 source を実 repository の `HEAD:<path>` blob からコピーするため利用可能である (`:66-87`)。契約だけは未 commit の新 bytes で上書きするが、`reservation.py` と `p3_autonomous_workload_trial.py` は HEAD blob のままである (`:75-86`)。

この実データでは reservation 側の両関数は実在する一方 (`reservation.py:159,218`)、8c `run_trial` の production body には両呼出しがない (`p3_autonomous_workload_trial.py:2845-3224`)。したがって helper が consumer 欠落を検出したことを pin できる。テストは未実走。

## (d) negative control

ID は次へ変更する。

```text
変更前: nc_c12_resume_or_multi_process_allowed
変更後: nc_c12_reservation_check_bypassed
```

`_NEGATIVE_CONTROL_RE = nc_c([0-9]{2})_[a-z0-9_]+` は新 ID を既に受理するので変更不要 (`s8c_preregistration_evidence.py:37,241-244`)。

`orchestrator/tests/test_s8c_preregistration_predicates.py:406-425` の C12 token supervisor は、policy 属性ではなく次を呼ぶ形へ置換する。

```python
def run_trial():
    contract = lookup()
    attest_and_build_receipt(contract)
    binding = read_binding(environ)
    check_reservation(
        binding,
        required_s=1,
        safety_margin_s=0,
        environ=environ,
    )
    return binding

def main():
    return run_trial()
```

allocation module は `def single_process_required(): pass` を捏造せず、`git show HEAD:orchestrator/campaign/reservation.py` の実 blobを fixture repo へ入れる。変更箇所は `_negative_control_case` の C12 branch (`:466-479`)。

負例変異は次の 1 回置換とする。

```text
check_reservation(binding, required_s=1, safety_margin_s=0, environ=environ)
→
is_reservation_required(contract.isolation_policy)
```

期待値は既存どおり `UNSATISFIED / allocation-enforcement-consumer-absent` (`:534-543`)。これは旧 single-process policy へ戻しても新 allocation binding を満たさないことを検出する。

`NEGATIVE_CONTROL_CASES` の key は新 ID へ変更する (`:483-490`)。旧 parametrized node は新 ID の node に置換される。なお、この control の supervisor は依然 synthetic なので、実データ発火の証拠には数えない。(c) の HEAD blob test だけをその証拠とする。

## (e) g4 record 生成手順

`prepare_revision` は世代鎖を `--commit` の tree から検証する一方、新しい本文と evidence contract は worktree から読む (`orchestrator/campaign/s8c_preregistration.py:1837-1900`)。したがって順序は固定される。

1. author の JSON・evaluator・test・`DECIDER_VERSION=v2` と、親の事前登録本文変更を、未 commit の同一 worktree に揃える。
2. g4 がまだ存在しないことを確認する。現行世代は g1〜g3 (`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g3.json:1`)。
3. repo root を cwd にして、変更を commit する前に次を実行する。

```bash
python3 -m orchestrator.campaign.s8c_preregistration prepare-revision \
  --repo-root . \
  --commit HEAD \
  --ruling-reference D441 \
  --revision-reason '2026-08-16 /rulings 全件 第3回 択(c)（D441 の C12 構造衝突を解消）: 条件12の allocation 証拠を read_binding/check_reservation による PBS job・boot・期限の束縛へ縮小し、単独性と resume 拒否の要求を除外'
```

4. 生成先が `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g4.json` であることを確認する。basename は `v1` のままだが、record schema は `s8c-prereg-condition-freeze/v2`、`decider_version` は `s8c-decider/v2` になる (`s8c_preregistration.py:40-53,1808-1834`)。
5. `generation_number=4`、`supersedes_sha256=2b28cde32feaa4509ff6c8cfe382240d7b4d2d8f919608a6199f2b282c2f23e1`、`ruling_reference=D441`、および exact JSON 案なら `evidence_contract_sha256=f386c2...f81b86` を確認する。
6. code・test・JSON・docs・g4 を同じ commit に含める。protected bytes を先に commit してから g4 を作る順序は、世代なし変更として検証不能になる (`:1473-1506`)。
7. commit 後に `check --repo-root . --commit HEAD` と親所管の受入を行う。C12 は未充足なので `check` の全体 rc=1 / `NOT_EFFECTIVE` が想定形であり、rc=0 を期待してはならない (`:1971-2012`)。

`ruling_reference` は D441 が妥当で、他により適切な既存 D はない。D441 は不存在 symbol、実 consumer 欠落、消える single-process / resume 保証を直接記録している (`docs/decisions.md:18421-18480`)。D438 は g3 の改訂、D439 は手続、D431/D435 は周辺原則であり、本縮小の内容参照には弱い (`:17873-17911,18127-18139,18247-18332,18333-18365`)。後発の択 (c) 自体は D441 に逐語記録されていないため、`revision_reason` に直接残す。

## (f) 事前登録本文の改訂

条件 12 は `docs/phase3-8c-preregistration.md:215-220` を次へ置換する。

```markdown
12. **計測環境の allocation binding** が、campaign launch 前に
    `reservation.read_binding` で予約 record を読み、`reservation.check_reservation` で現在の
    `PBS_JOBID`、boot ID、予約 deadline と必要残時間を照合する
    (Pegasus の場合は環境専用 runbook に従う)。現行 (2026-08-17) の `reservation.py` には
    両関数が実在するが、8c supervisor の `run_trial` から両者へ到達する production consumer は
    ないため、本条件は未充足である。本条件は単一 allocation / node / process での完遂または
    resume 禁止を要求しない。
```

「既知の構造衝突」の導入文 (`:268-271`) は第 4 世代を反映して次へ変更する。

```markdown
**既知の構造衝突 (2026-08-15 実測、2026-08-17 第 4 世代で更新)。** 下は「実装が足りない」型では
なく、契約・裁定・git の性質が互いに矛盾している型である。**いずれも、未定義・エラーを
充足側へ倒して解いてはならない。** (a)〜(c) は第 3 世代 (D438) が受理集合を 1 bit も広げずに
解消し、(e) は第 4 世代が要求を実現可能な範囲へ縮小した。(d) は未解消であり、(e) の
production consumer 欠落も未解消である。
```

衝突 (d) の直後、現行 `:295-297` と「本手続きが主張しないこと」`:299` の間へ次を挿入する。

```markdown
- **衝突 (e) 条件 12 の実在しない allocation 述語 — 第 4 世代で契約の形を縮小した。**
  旧契約は production に存在しない `single_process_required(isolation_policy)` と、
  8c launcher が single-process / resume 禁止を launch 前に強制する証明を要求した。
  ユーザー裁定 (2026-08-16 /rulings 全件 第 3 回、択 (c)) により、証拠を実在する
  `reservation.read_binding` / `reservation.check_reservation` が担う PBS job ID・boot ID・
  予約期限の binding だけへ縮小した。**この改訂後は、正式 8c が単一 allocation / node /
  process で完遂されること、および launcher が multi-process または resume を launch 前に
  拒否することを、条件 12 は要求も証明もしない。** 現行 8c の `run_trial` から両 reservation
  関数への production 到達は無いため、条件 12 は引き続き未充足であり、受理集合は広がらない。
```

本文と evidence contract は凍結範囲である (`:240-250`)。上記編集を確定してから g4 を生成し、その後は句読点や折返しも変更せず、変更する場合は g4 を削除・再生成する。

## (g) 受入で赤になる nodeid

契約・ID・decider を先に変え、対応するテスト期待値をまだ直していない状態では、静的に次が赤になる。

- `orchestrator/tests/test_s8c_preregistration_core.py::test_current_evidence_contract_hash_is_frozen` — 旧 hash literal (`test_s8c_preregistration_core.py:1153-1156`)。逐語 JSON 案なら `f386c2...f81b86` へ更新。
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_satisfiable_predicate_requires_negative_control` — contract ID と `NEGATIVE_CONTROL_CASES` の不一致 (`test_s8c_preregistration_predicates.py:493-512`)。
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_noop_and_token_only_fixtures_never_satisfy[nc_c12_resume_or_multi_process_allowed-C12]` — 旧 fixture / ID。新 node は `[nc_c12_reservation_check_bypassed-C12]` (`:515-543`)。
- `orchestrator/tests/test_s8c_preregistration_core.py::test_decider_version_mutation_is_generation_mutated` — mutation literal `v2` が新しい正常値と同じになる (`test_s8c_preregistration_core.py:1531-1538`)。
- `orchestrator/tests/test_s8c_preregistration_core.py::test_mismatched_decider_version_is_not_effective` — mismatch fixture の `v2` が一致値になる (`:2011-2025`)。
- `orchestrator/tests/test_s8c_preregistration_core.py::test_invalid_running_decider_version_cannot_activate` — record の期待 literal `v1` が古くなる (`:2042-2060`)。
- `orchestrator/tests/test_s8c_preregistration_core.py::test_valid_hostile_str_subclass_cannot_fake_decider_version_match` — 同じく record 期待 literal (`:2063-2083`)。
- `orchestrator/tests/test_s8c_preregistration_core.py::test_activation_report_digest_binds_decider_and_projection_fields` — replacement `v2` が baseline と同じになり、digest 差が消える (`:2086-2102`)。

g4 を同時生成しなければ、次も赤になる。

- `orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain` (`test_s8c_preregistration_invariant.py:125-159`)。

一方、指定された gap ledger node は現行 bytes と本プランでは赤にならない。

- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review` の C12 は引き続き `UNSATISFIED / environment-contract-consumer-absent` (`test_s8c_preregistration_predicates.py:108-132`)。env gate が allocation helper より先に短絡するためであり (`s8c_preregistration_evidence.py:564-591`)、期待値を変更してはならない。
- `...::test_current_repository_snapshot_has_zero_satisfied_predicates` (`test_s8c_preregistration_predicates.py:99-105`) と `...::test_candidate_is_not_effective_and_has_zero_satisfied_predicates` (`test_s8c_preregistration_invariant.py:199-212`) も変更せず、受理集合不変の guard とする。

## 未解決・親裁定が要る点

- `allow_resume` の扱いは解決済みとして「落とす」を推奨する。残す根拠は現行 production にも今回の「PBS job・boot・期限だけ」という裁定にもない (`env_contract.py:65-77`; `reservation.py:159-270`)。
- D441 は利用可能な唯一の内容上の参照だが、後発の択 (c) 自体は同見出しに記録されていない。新 D を捏造せず、D441 を `ruling_reference`、直接裁定を `revision_reason` に残す形を親が明示的に採用する。
- [T-1202] 取り込み後は `_evaluate_c12` と gap ledger node を再読する。現 worktree からは env reason 不変しか導けず、並行 wave の未確認 bytes を前提に期待値を先回り変更できない。
- projected contract hash は上記 JSON を逐語採用した場合だけ有効。文言を変えた場合は最終 bytes から再計算する。

## 総括

- C12 は PBS job・boot・期限の reservation binding だけへ縮小し、単独性と resume 拒否を明示的に保証外へ出す。
- allocation 判定は独立 helper 化し、実 HEAD の `reservation.py` と 8c supervisor に対して consumer 欠落を pin する。
- helper が成立しても終端は `EVIDENCE_UNDEFINED` のままで、`SATISFIED` 経路は増やさない。
- JSON・本文・`DECIDER_VERSION=v2`・g4・テストを同一 commit に束縛する。
- 最大のリスクは [T-1202] 取り込み後の env gate / gap ledger 競合。pytest・受入は本作業では実走していない。