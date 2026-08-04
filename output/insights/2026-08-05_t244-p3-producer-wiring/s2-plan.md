必読資料はすべて読み取れました。結論は **NO-GO** です。現 brief の不変条件を守ったまま、段 5 が実行できる正の producer 結線案は成立しません。拒否側だけの CLI を追加しても、D159 が禁じた「未結線 prototype を P3 と数える」状態を増やすだけです（[decisions.md:7890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/decisions.md:7890)）。

以下は、段 4 で scope を改訂する場合の一意な再起票案と、改訂なしなら実装しない根拠です。静的検査のみで、pytest は走らせていません。worktree は clean です。

## 1. 新 leaf の設計と、現 scope で止まる箇所

新設候補は `orchestrator/campaign/reflux_origin_producer.py` とするべきです。新規 file には現時点で実在行番号がないため、架空の行番号は付けません。

公開面は次に閉じます。

```python
class RefluxOriginProducerError(RuntimeError):
    ...

def bind_origin(
    origin_id: str,
    *,
    campaign: CampaignConfig,
    descriptor_binding: Mapping[str, object],
    ccbench_root: Path,
    environment_contract: ExecutionEnvironmentContract,
) -> OriginBinding:
    ...

def commit_candidate_batch(
    binding: OriginBinding,
    *,
    candidate_wires: Sequence[str],
) -> CommittedBatch:
    ...

def tombstone_candidate_batch(
    batch: CommittedBatch,
    *,
    reason: TombstoneReason,
) -> TombstonedBatch:
    ...

def seal_candidate_batch(
    batch: CommittedBatch,
    *,
    results: Sequence[VerifiedCandidateResult],
) -> SealedBatch:
    ...
```

`OriginBinding`、`CommittedBatch`、`VerifiedCandidateResult` は `frozen=True, slots=True` とし、`trial_registry.TrialBinding` の issuer seal の先例（[trial_registry.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/trial_registry.py:103)、[trial_registry.py:976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/trial_registry.py:976)）と同様に private seal を持たせます。ただし ledger 自身が、in-process private call は capability 境界ではないと明記しています（[reflux_origin_ledger.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:4)）。seal は誤用防止であり、権限証明とは名乗りません。

内部状態は次の順で保持します。

- `OriginBinding`: authority manifest、導出済み origin ID/cell key、初期 `OriginSnapshot`、budget policy。
- `CandidateOpening`: slot 番号、正準 wire bytes、16-byte 以上の非ゼロ CSPRNG salt、salted commitment。
- `CommittedBatch`: batch ID、全 opening、`BatchCommitted` の operation ID/base/receipt。
- `PreparedBatch`: outcome/result/constraint の salt、plaintext、commitment、prepared receipt。
- `SealedBatchResult`: ledger から再読した `SealedBatch` と全 receipt。
- crash 用 producer journal: operation ID、元の CAS base、event 全 bytes、salt/opening を各副作用前に fsync。

失敗はすべて `RefluxOriginProducerError("[gate] message")` に包み、原因の `RefluxOriginLedgerError` は `raise ... from exc` で残します。gate は次に固定します。

- `[origin-authority]`: authority entry 不在・読取不能
- `[origin-identity]`: requested ID と manifest digest 不一致
- `[origin-cell]`: observed cell と authority cell 不一致
- `[origin-state]`: terminal/open batch/phase 不正
- `[origin-budget]`: batch minimum、I/Q 残量不足
- `[batch-shape]`: slot 数・wire・commitment 不正
- `[batch-result]`: verifier 結果を二値へ正当に写せない
- `[ledger-cas]`: CAS loser
- `[ledger-replay]`: exact replay を再構成できない
- `[batch-seal]`: prepare/seal/read-back 不一致
- `[producer-journal]`: durable state 不在・破損・binding 不一致

公開 API の正しい呼出順は次です。

1. authority から得た `AuthorityManifest` に対して `derive_origin_id()`（[reflux_origin_ledger.py:430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:430)）。
2. requested ID と byte-exact 比較。
3. 同じ manifest に `derive_cell_key()`（[reflux_origin_ledger.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:434)）。
4. live campaign から再導出した cell と比較。
5. `read_origin()`（[reflux_origin_ledger.py:2777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2777)）で authority membership、phase、budget counter を読む。
6. 全候補収集後、`commit_event(..., BatchCommitted(...))`（[reflux_origin_ledger.py:2784](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2784)）。
7. 全 verifier 結果の取得後、同 API で `BatchResultsPrepared`。
8. 同 API で `BatchSealed`。
9. `read_sealed_batch()`（[reflux_origin_ledger.py:2804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2804）を再読し、その戻り値だけを report へ公開する。

各 commit の次 base は `receipt.current_state_commitment` を使います。exact replay 後は、当該 operation 直後を表す `resulting_state_commitment` と現在の global state が異なり得るためです（[reflux_origin_ledger.py:2549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2549)）。

ただし、この設計は現 API では実装不能です。`OriginSnapshot` は manifest、cell key、budget policy、open batch ID を返しません（[reflux_origin_ledger.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:496)）。authority manifest を読む公開 API もありません。private `_production_store()` / `_locked()` / authority entry を新 leaf から使う案は、固定公開 API を迂回するため採りません。

さらに production runtime の genesis は明示的に禁止されています（[reflux_origin_ledger.py:2265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2265)）。公開 API は `_locked(..., create=False)` へ入り、未作成 runtime の lock さえ作りません（[reflux_origin_ledger.py:1375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1375)）。現 authority は空です（[reflux_origin_authority_v1.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_authority_v1.json:1)）。したがって段 4 は、少なくとも「固定 authority binding reader」と「production runtime bootstrap 主体」を別 scope で裁定する必要があります。

## 2. authority manifest 13 field の live 導出可能性

判定記号は、○＝既存の canonical deriv出が実在、△＝素材はあるが manifest 用 digest 規則が未定、×＝live campaign 入力に source がない、です。

| field | 判定 | 実在 source と問題 |
|---|---:|---|
| `authority_series_id` | × | authority 発行値であり、live campaign に source がない。設計も authority-issued としている（[README.md:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/output/insights/2026-08-01_t244-reflux-design/README.md:207)）。 |
| `spec_content_sha256` | △ | `CampaignConfig.spec_content` は実在する（[model.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/model.py:62)、[p3_autonomous_workload_trial.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:546)）。ただし manifest 用の encoding/domain-separated digest 規則は未実装。 |
| `ccbench_commit_oid` | △ | config に入るのは `d706650` の短縮 PIN（[pin.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/pin.py:26)、[p3_autonomous_workload_trial.py:555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:555)）。manifest は 40hex を要求する（[reflux_origin_ledger.py:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:364)）。実 submodule の `HEAD^{commit}` を解決する新規規則が必要。 |
| `axis_semantics_sha256` | △ | marker、source、5 要因集合は実在する（[axis_trigger_gating.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/axis_trigger_gating.py:22)、[axis_trigger_gating.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/axis_trigger_gating.py:45)）。どの file/field bytes をどう束ねるか未定。 |
| `workload` | ○ | descriptor は deterministic projection（[s8b_descriptor.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/s8b_descriptor.py:85)）、SHA は `projection_record.output_sha256`（[s8b_descriptor.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/s8b_descriptor.py:194)）、records/threads は trial で 100000/4（[p3_autonomous_workload_trial.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:528)）。 |
| `verifier_policy_sha256` | △ | `legacy+s2` token は config に入る（[p3_s4_loop_trigger_gating.py:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:449)）。token、validator code、build-admission policy のどれを preimage とするか未定。 |
| `environment_contract_sha256` | ○/時系列不適合 | contract 自身に canonical SHA がある（[env_contract.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/env_contract.py:145)）。ただし現 trial は environment を `drive_iteration()` 内で初めて解決する（[p3_s4_loop_trigger_gating.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:701)）ため、batch commit 前の binding と同じ contract を drive に強制する口がない。 |
| `candidate_ir` | △ | `schema_ref` は `SCHEMA_ID`（[reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_ir.py:19)）から導出可能。`canonical_emitter_sha256` は emitter が実在しても（[reflux_ir.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_ir.py:117)）digest preimage が未定。 |
| `role_bundle_sha256` | △ | role file/contract と個別 SHA は実在する（[p3_autonomous_workload_trial.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:177)、[p3_autonomous_workload_trial.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:424)）。4 role の順序、file/prompt の aggregate schema がない。 |
| `recipient_projection_schema_sha256` | × | coder 入力は inline dict 構築（[p3_autonomous_workload_trial.py:1495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1495)）で、独立した schema artifact がない。 |
| `budget_policy` | × | campaign/run CLI から導く値ではなく authority が注入する immutable policy（[reflux_origin_ledger.py:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:206)、[decisions.md:7208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/decisions.md:7208)）。公開 reader がない。 |
| `stock_certification_ref` | × | field は必須だが（[reflux_origin_ledger.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:228)）、8c launch と特定 artifact を結ぶ登録がない。 |
| `structural_zero_evidence_ref` | × | 候補 artifact はある（[s8a_trigger_gating_coverage.json:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json:49)）が、manifest への選定・SHA binding がない。しかも artifact は `linux-baremetal` なのに clocks は 2100（同 [line 2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json:2)、[line 5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json:5)）、現 registry の linux-baremetal は 1800（[env_contract.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/env_contract.py:169)）。そのまま採用できない。 |

cell key は descriptor、axis semantics、verifier policy、environment contract の4 digestです（[reflux_origin_ledger.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:434)）。axis と verifier の canonical digest がないため、**observed cell 自体が現在は再導出不能**です。したがって full manifest の authority-only field を信用して補っても、live cell binding は成立しません。

## 3. batch 形成の具体案と、8c での衝突

scope 改訂後に採る呼出順は次です。

1. `_run_workload()` の campaign identity/freshness 確定部（[p3_autonomous_workload_trial.py:1402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1402)）で `OriginBinding` を検証する。
2. planner は現行どおり1回（[p3_autonomous_workload_trial.py:1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1475)）。
3. 現在1回の coder 呼出しになっている範囲（[p3_autonomous_workload_trial.py:1495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1495)）を、`batch_cardinality_min` 個の candidate slot 収集へ分ける。
4. 各 coder event の `attempt` は現行どおり厳密に1、`retry=False` のままにし、`candidate_index` と一意な invocation ID を別軸にする。`attempt=2` へ変えてはならない（producer は [line 918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:918)、consumer は [autonomous_trial_completeness.py:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:192)、境界テストは [test_autonomous_trial_completeness.py:678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/tests/test_autonomous_trial_completeness.py:678)）。
5. N 回すべての coder 呼出しが終わった後に、全 N commitment を1件の `BatchCommitted` として commit。
6. 同じ wire が2回以上返っても補充呼出しはしない。salted commitment は全 slot 分 commit し、その直後に `BatchTombstoned` を commitして終了する。preview は0回、I/Q は返却しない。ledger は tombstone 後も I/Q を保持する（[reflux_origin_ledger.py:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1026)、既存期待は [test_reflux_origin_ledger.py:832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/tests/test_reflux_origin_ledger.py:832)）。
7. distinct の場合だけ、現在 line 1533 から始まる preview/auditor/drive 部を candidate ごとの helper に抽出する（[p3_autonomous_workload_trial.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1533)）。
8. 全 candidate の検証完了後に `BatchResultsPrepared`、`BatchSealed`、`read_sealed_batch`。
9. report へ使う plaintext は `read_sealed_batch` の戻り値だけにする。

期待する call trace は厳密に次です。

```text
planner
coder[0] ... coder[N-1]
batch-committed
preview[0], auditor[0], drive[0]
...
preview[N-1], auditor[N-1], drive[N-1]
batch-results-prepared
batch-sealed
read-sealed-batch
report publication
```

ただし、この順を現行 8c に入れるには未裁定変更が必要です。

- report は `roles` の各 role を1 object としてしか表せません（[autonomous_trial_completeness.py:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:633)）。journal に複数 coder を残すと report/journal bijection（[autonomous_trial_completeness.py:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/autonomous_trial_completeness.py:916)）が必ず赤になります。
- 解決には opt-in report v3 の `reflux_batch.candidates[]` を追加し、consumer を同じ変更単位で拡張する必要があります。これは D96 の新 decision と境界テストを要する受理集合変更です（[decisions.md:4271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/decisions.md:4271)）。P4 と「受理集合を変えない」に反します。
- `drive_iteration()` は呼ぶたびに E-loop の `state.iteration` を増やします（[p3_s4_loop_trigger_gating.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:729)）。「ledger の1 batch iteration」と「E-loop の N iteration」を同一 generation にどう写すか未裁定です。
- drive は seal 前に provenance/WAL/checkpoint を書きます（[p3_s4_loop_trigger_gating.py:714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:714)、[p3_s4_loop_trigger_gating.py:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:736)）。seal まで結果を公開しない D159 の契約（[decisions.md:7876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/docs/decisions.md:7876)）を、現 artifact topology では満たせません。
- malformed coder/provider crash を batch commit 前に消費する reservation event がありません。`BatchCommitted` は既に得た candidate commitment を要求します（[reflux_origin_ledger.py:900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:900)）。「planner 前に予約し、provider crash も no-refund」という設計本文（[README.md:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/output/insights/2026-08-01_t244-reflux-design/README.md:277)）を producer だけでは実装できません。

## 4. opt-in 配線

scope 改訂後の挿入点は次です。

- `run_trial()` の keyword-only 引数末尾（[p3_autonomous_workload_trial.py:1685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1685)）へ `reflux_origin: str | None = None`。
- CLI parser の `--max-generations` 周辺（[p3_autonomous_workload_trial.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1932)）へ `--reflux-origin`、既定値は literal `None`。
- `run_trial()` 呼出し（[p3_autonomous_workload_trial.py:2002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:2002)）へそのまま転送。
- top-level import block（[p3_autonomous_workload_trial.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:37)）には producer/ledger を追加しない。`reflux_origin is not None` の branch 内だけで lazy import。
- origin は workload descriptor を含むため、単一 `--reflux-origin` で A/B/C の複数 cell を回してはならない。現 flag 形を維持するなら opt-in は workload singleton を要求する。複数 workload を許すなら `workload=origin_id` mapping へ CLI 契約を変更する別裁定が必要。

既定 path の byte 不変は次で固定します。

1. 既存 `test_fixture_trial_runs_ycsb_abc_and_binds_descriptor` の期待値を一切変更しない。同テストは1 generation/role、12 role events、report/proposal の現在形まで固定しています（[test_p3_autonomous_workload_trial.py:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/tests/test_p3_autonomous_workload_trial.py:519)）。
2. frozen clock/provider を使い、引数省略と `reflux_origin=None` の `attempts.jsonl`、`report.json`、proposal bytes が完全一致する新テストを置く。
3. subprocess 内で default trial を実行し、終了後も `orchestrator.campaign.reflux_origin_ledger` と `reflux_origin_producer` が `sys.modules` に無いことを assert。
4. AST で `--reflux-origin` の default が literal `None` であることを、既存 `--max-generations` literal 1 テスト（[test_p3_autonomous_workload_trial.py:480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/tests/test_p3_autonomous_workload_trial.py:480)）と同型で固定。

空 authority の拒否だけを実装する案は採りません。現 runtime も未作成なので、実際には「unknown origin」より先に lock 不在で止まり、producer admission の発火証拠になりません。

## 5. crash / CAS / replay

ledger 単体は次を既に保証しています。

- exact committed request は `replayed=True` で返る（[reflux_origin_ledger.py:2526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2526)）。
- CAS mismatch は event append 前に拒否する（[reflux_origin_ledger.py:2559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2559)）。
- durable prepared operation は同じ origin/operation/base/event だけが継続できる（[reflux_origin_ledger.py:2618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2618)）。
- incomplete tail は replay 前に切り戻す（[reflux_origin_ledger.py:2468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2468)）。

producer 側は、各 event の `operation_id / expected_state_commitment / event / salts / openings` を commit 前に durable journal へ保存し、再開時には最初に同じ request をそのまま再送する必要があります。CAS mismatch を見て provider や preview を再呼出ししてはいけません。

crash 窓ごとの扱いは次です。

- coder 前・candidate commit 前: 現 FSM には予約がないため、crash を no-refund にできない。blocker。
- `BatchCommitted` commit 中: producer journal から exact retry。
- commit 後・評価途中: phase が `BATCH_COMMITTED` なら同 batch を tombstone。既に実行した build は再実行しない。
- 全結果保存後・prepare 中: 同じ `BatchResultsPrepared` を exact retry。
- `RESULTS_PREPARED` 後: 保存済み salt/opening から同じ `BatchSealed` だけを送る。ここでは tombstone 不可（[reflux_origin_ledger.py:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:1026)）。
- seal 応答喪失: 同じ seal を exact retry後、`read_sealed_batch`。
- CAS loser: candidate/provider を再呼出しせず `[ledger-cas]` で停止。同一 origin の state が進んだ場合、hidden constraint set を snapshot から読めないため自動 rebase しない。

しかし現 `run_trial()` は既存 run root を明示的に拒否し、resume を scope 外としています（[p3_autonomous_workload_trial.py:1786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/p3_autonomous_workload_trial.py:1786)）。また snapshot から open batch ID を復元できません。このため end-to-end crash replay は現 brief では実装不能です。producer journal の固定保存場所、resume admission、既存 harness artifact の再検証を別裁定する必要があります。

## 6. テスト計画

scope 改訂後に追加する nodeid 骨子です。既存期待値は変更しません。

`orchestrator/tests/test_reflux_origin_producer.py`

- `test_p01_bind_calls_derive_origin_cell_then_read_in_order`  
  origin/cell の再導出を飛ばして caller handle を信用する欠陥を落とす。
- `test_p02_origin_or_cell_mismatch_stops_before_ledger_or_provider_side_effect`  
  field mismatch 後も `read_origin` や provider に進む欠陥を落とす。
- `test_p03_full_candidate_set_is_committed_before_first_evaluation`  
  candidate 0 の preview が coder N−1/commit より先に走る欠陥を call trace で落とす。
- `test_p04_duplicate_wire_commits_then_tombstones_without_preview`  
  duplicate の補充、refund、preview 到達を落とす。
- `test_p05_commit_prepare_seal_then_public_read_is_the_only_plaintext_source`  
  prepare 前 reveal、seal 前 publish、cached result 公開を落とす。
- `test_p06_cas_loser_never_reinvokes_candidate_provider_or_preview`  
  CAS retryで候補生成や verifier を再実行する欠陥を落とす。
- `test_p07_exact_replay_after_each_producer_fault_boundary_is_idempotent`  
  operation/base/event/salt を再生成する欠陥を落とす。
- `test_p08_nonqualifying_failure_tombstones_without_installing_constraint`  
  build error、timeout、role-invalid を exact-mask cut に誤変換する欠陥を落とす。
- `test_p09_fixture_store_is_the_only_repository_injection_surface`  
  production root/path injection を公開 API に混ぜる欠陥を落とす。

テストは既存形どおり、完全な temp Git repository と committed authority を作り（[test_reflux_origin_ledger.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/tests/test_reflux_origin_ledger.py:185)）、`_fixture_store_for_test()`（[reflux_origin_ledger.py:2317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/campaign/reflux_origin_ledger.py:2317)）だけを使います。production API の path は monkeypatch しません。新 leaf の private test port が、同じ engine を `_read_origin_locked` / `_commit_locked` / `_read_sealed_batch_locked` へ結ぶ形にします。

`orchestrator/tests/test_p3_autonomous_workload_trial.py`

- `test_reflux_opt_in_invokes_n_coders_then_commit_then_n_previews`
- `test_reflux_candidate_slots_keep_attempt_one_retry_false`
- `test_reflux_opt_in_requires_one_workload_before_run_root_or_provider`
- `test_reflux_opt_out_does_not_import_ledger_and_preserves_artifact_bytes`
- `test_cli_reflux_origin_default_is_literal_none_and_forwards_exact_id`
- `test_empty_authority_rejects_before_run_root_provider_and_build_preparation`

consumer 変更を段 4 が承認した場合だけ、`orchestrator/tests/test_autonomous_trial_completeness.py` に次を追加します。

- `test_reflux_batch_report_journal_bijection_covers_every_candidate_slot`
- `test_reflux_batch_rejects_missing_duplicate_or_reordered_candidate_slot`

既存 `attempt=2` 拒否（[test_autonomous_trial_completeness.py:678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/orchestrator/tests/test_autonomous_trial_completeness.py:678)）は変更しません。

## 7. 変異事前登録候補

新 leaf は未作成なので、架空の行番号は付けません。下表の symbol と old/new を先に登録し、実装後の段 4 matrix で実在行へ pin します。

| # | file / symbol | old → new（一行） | 第一失敗 |
|---|---|---|---|
| M1 | producer / `bind_origin` | `if derived_origin_id != requested_origin_id:` → `if derived_origin_id == requested_origin_id:` | `test_p02...` の `[origin-identity]` assert |
| M2 | producer / `bind_origin` | `if derived_cell_key != observed_cell_key:` → `if derived_cell_key == observed_cell_key:` | `test_p02...` の `[origin-cell]` assert |
| M3 | trial / candidate loop | `range(binding.batch_cardinality_min)` → `range(1)` | `test_reflux_opt_in_invokes_n...` の coder count assert |
| M4 | producer / evaluation gate | `if batch.phase != "BATCH_COMMITTED":` → `if False:` | `test_p03...` の commit-before-preview trace assert |
| M5 | producer / duplicate gate | `if len(set(candidate_bytes)) != len(candidate_bytes):` → `if False:` | `test_p04...` の preview count `== 0` |
| M6 | producer / salt generation | `salt = secrets.token_hex(16)` → `salt = "01" * 16` | `test_p05...` の origin-wide salt uniqueness assert |
| M7 | producer / receipt chaining | `base = receipt.current_state_commitment` → `base = receipt.resulting_state_commitment` | `test_p06...` の replay後 next-base assert |
| M8 | producer / post-seal publication | `revealed = ledger.read_sealed_batch(origin_id, batch_id)` → `revealed = expected_opening` | `test_p05...` の最終 ledger call assert |
| M9 | trial / lazy branch | `if reflux_origin is not None:` → `if True:` | `test_reflux_opt_out...` の `sys.modules` assert |
| M10 | trial / CLI | `parser.add_argument("--reflux-origin", default=None)` → `default=""` | `test_cli_reflux_origin...` の AST literal-None assert |
| M11 | trial / opt-in event | `"attempt": 1` → `"attempt": candidate_index + 1` | `test_reflux_candidate_slots...` の全 attempt `== 1` |
| M12 | completeness / reflux scan | `for candidate in reflux_batch["candidates"]:` → `for candidate in reflux_batch["candidates"][:1]:` | `test_reflux_batch_report_journal_bijection...` の multiset assert |
| M13 | producer / nonqualifying result | `if result.is_nonqualifying_failure:` → `if False:` | `test_p08...` の tombstone/constraint-empty assert |
| M14 | producer / duplicate tombstone | `BatchTombstoned(batch.batch_id)` → `BatchTombstoned("wrong-batch")` | `test_p04...` の terminal phase/tombstone count assert |

## 8. scope 外だが real な所見

次は本 wave で独断実装せず、段 4 の裁定パッケージへ返すべきです。

- authority manifest を返す固定・committed reader と production runtime bootstrap の主体。現公開 API 不変条件のままでは解けない。
- 8c report v3 と completeness consumer の D96 変更。複数 coder を journal にだけ隠す案は不可。
- `--reflux-origin` と複数 workload の cardinality。単一 ID を三つの cell に流用してはならない。
- environment contract を batch commit 前に固定し、同じ exact object を drive sink まで運ぶ契約。
- ledger 1 batch iteration と E-loop N iterations の意味対応。
- producer journal、resume admission、途中 build artifact の再検証・tombstone 規則。
- candidate commit 前 crash/provider failure を no-refund にする reservation event。現 FSM の受理集合変更を要する。
- qualifying correctness red を独立 WAL 読取から exact-mask constraint へ変換する translator。単なる `outcome=="aborted"` は設計本文の条件を満たさない（[README.md:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/output/insights/2026-08-01_t244-reflux-design/README.md:119)）。
- no-build opt-in の扱い。設計本文では diagnostic run は origin 外（[README.md:286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-producer-wiring/output/insights/2026-08-01_t244-reflux-design/README.md:286)）なので、`--no-build --reflux-origin` を受理する根拠がない。
- P7/formal report/proof chain は引き続き別面。ただし D159 により、これを欠く間は P3 充足と記録できない。

## 総括

- 必読資料は全件読了し、静的検査だけを行った。  
- 現 brief の不変条件下では、正の producer 結線を実装できる一本の plan は存在しない。  
- 最大の blocker は、observed cell の axis/verifier digest が未定で、authority manifest の公開 reader もないこと。  
- production runtime bootstrap が禁止されているため、authority を後で登録しても公開 API は起動できない。  
- 複数 coder は `attempt=1` の candidate slot として表せるが、report/completeness の D96 改訂が必須である。  
- crash/no-refund を満たすには producer journal、resume、commit 前 reservation の追加裁定が要る。  
- 段 4 は本 wave を「実装しない」と裁定し、authority reader/bootstrap・report v3・resume/reservation を再 brief すべきである。