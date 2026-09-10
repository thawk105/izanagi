## 実装単位

### A. S1: typed verifier result の保持

- 所有 path:
  - `orchestrator/campaign/pipeline.py`
  - 新規 `orchestrator/tests/test_pipeline_verify_result_retention.py`
- 依存: 無し。B/C がこの単位の `EvalResult` field 名に依存する。
- local verifier が返した exact `VerifyResult` を rejected terminal まで運ぶ。accepted では最終値を保持せず、remote fan-out から wire payload を typed 値へ復元しない。

### B. S2: ordered WAL / provenance producer

- 所有 path:
  - `orchestrator/campaign/reflux_result_evidence.py`
  - `orchestrator/tests/test_reflux_result_evidence.py`
- 依存: A の `VerifyResult | None` の意味だけ。
- `wal.ordered_attempt_frames()` を再利用し、source WAL prefix、ordered projection、execution provenance を content-addressed、create-only で発行する。新 production module は作らない。

### C. S3: `run_campaign()` issuer

- 所有 path:
  - `orchestrator/campaign/loop.py`
  - 新規 `orchestrator/tests/test_reflux_campaign_issuer.py`
- 依存: A、B。
- origin issuance context がある一件 campaign だけ、terminal WAL 追記後、次 genome へ進む前に B の実 issuer を呼ぶ。issue 例外は既存の `eval-exception` 変換範囲外から伝播させる。

### D. S4: origin runtime forwarding と公開 caller

- 所有 path:
  - `orchestrator/campaign/p3_autonomous_workload_trial.py`
  - `orchestrator/campaign/p3_s4_loop_trigger_gating.py`
  - `orchestrator/tests/reflux_origin_fixture_builder.py`
  - `orchestrator/tests/test_p3_autonomous_workload_trial.py`
  - `orchestrator/tests/test_reflux_formal_consumer.py`
- 依存: B の issuance context、C の追加 keyword。
- `OriginTrialRuntime` から query 固有 context と物理 campaign config/output root を drive へ渡す。既存 `p3_autonomous_workload_trial.main()` に明示 fixture-origin mode を足し、`run_origin_trial()` と公開 fixture client factory を通す。

4 単位の production 所有 path は素集合である。A/B が型と関数 signature を先に固定すれば、C/D は並列実装できる。

## file:line プラン

### A. S1: `pipeline.py`

- `pipeline.py:50-52`
  - `orchestrator.verifier.model` import に `VerifyResult` を追加する。

- `pipeline.py:300-310` の既存
  ```python
  @dataclass
  class EvalResult:
      ...
      verdict: str = ""
      notes: List[str] = field(default_factory=list)
  ```
  の末尾へ次を追加する。
  ```python
  build_attempt_id: str = ""
  verify_result: Optional[VerifyResult] = None
  ```
  `build_attempt_id` は S3 が WAL attempt を曖昧な再走査で選ばないための既存 producer 値である。

- `pipeline.py:470-476` の既存
  ```python
  class _RepetitionExecutionOutcome:
      verify_payload: Optional[Dict[str, Any]] = None
      verification_capability: Optional[object] = None
      abort: Optional[_RepetitionAbortOutcome] = None
  ```
  に
  ```python
  verify_result: Optional[VerifyResult] = None
  ```
  を追加する。

- `pipeline.py:608-666`
  - `run_verifier(...)` が返した exact `verify_result` を、certified/rejected の双方で `_RepetitionExecutionOutcome(verify_result=verify_result, ...)` に載せる。
  - `result_to_dict()` による wire projectionは従来どおりで、typed 値の代替にしない。

- `pipeline.py:870-1035`
  - `_admit_verify_fanout_result()` の全 return は `verify_result=None` のままとする。
  - remote `outcome["detail"]["verify"]` や `verify_payload` から `VerifyResult` を再構成しない。

- `pipeline.py:1694, 1724-1727, 1837`
  - 生成済み `build_attempt_id` を、pre-build abort と通常の `EvalResult` の双方へ設定する。

- `pipeline.py:1851-1866` の既存
  ```python
  def _abort(reason, note, extra=None, workload_tag=None) -> EvalResult:
  ```
  を
  ```python
  def _abort(
      reason, note, extra=None, workload_tag=None,
      *, verify_result: Optional[VerifyResult] = None,
  ) -> EvalResult:
  ```
  とし、非 `None` は `type(value) is VerifyResult` を要求して `res.verify_result` へ設定する。既存 bench/build abort は既定 `None` のまま。

- `pipeline.py:2052-2078`
  - `_project_repetition_outcome()` の冒頭で `res.verify_result = None` とし、前 pass/repetition の値を消す。
  - `outcome.abort is not None` の場合だけ、
    ```python
    _abort(..., verify_result=outcome.verify_result)
    ```
    とする。
  - 成功 repetition の typed 値は capability 発行後に破棄する。

- `pipeline.py:2080-2120`
  - repetition 開始時にも `res.verify_result = None` を維持し、最初の成功結果が後続の timeout/remote failure に残らないようにする。

- `pipeline.py:631-654` に対応する loop 側の synthetic `EvalResult` には、判明した attempt ID だけを設定し `verify_result=None` とする。

### B. S2: `reflux_result_evidence.py`

- `reflux_result_evidence.py:39-71`
  - 次を公開 API に加える。
  ```python
  ResultEvidenceIssuanceContext
  ProducedOrderedWalProjection
  produce_ordered_wal_projection
  issue_campaign_result_evidence
  ```

- `reflux_result_evidence.py:129-149`
  - schema 定数は変更しない。
  - content path の固定 prefix のみ追加する。
  ```python
  _CONTENT_ROOT = PurePosixPath(
      "reports/reflux-result-evidence-content/v1"
  )
  ```

- `reflux_result_evidence.py:229-275`
  - 次の immutable context を追加する。
  ```python
  @dataclass(frozen=True, slots=True)
  class ResultEvidenceIssuanceContext:
      origin_capability: OriginBindingCapability
      evidence_root: Path
      batch_id: str
      query_ordinal: int
      iteration_index: int
      replicate_ordinal: int
      p6_plan: Mapping
      trial_binding: Mapping
      origin_binding: Mapping
      verifier_policy_bytes: bytes
      expected_record_path: str
  ```
  `origin_binding` と `trial_binding` は capability/launch digest から親で構成するが、ここで exact schema と capability との一致を再検査する。

- `reflux_result_evidence.py:830-905`
  - `_ensure_parent_directories()` を再利用する private raw-byte writer を追加する。
  - open flags は必ず
    ```python
    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    ```
    とし、全 bytes write、file fsync、parent fsync、read-back exact 一致を要求する。
  - `FileExistsError` を成功扱いにせず発行失敗とする。`os.replace()` は使わない。

- `reflux_result_evidence.py:972-1001`
  - content digest を計算後、物理 campaign root の evidence-root 相対 prefix 下へ書く。
  - `campaign_rel = Path(layout.root).relative_to(context.evidence_root)` を root confinement 検査後に使う。

- `reflux_result_evidence.py:1061-1093`
  - `_canonical_wal_interval()` の逆向き producer を追加する。実装は再 serialize した WAL を source とせず、`wal_codec.ordered_attempt_frames()` の physical offsets/raw frame を使う。
  - 正例の projection は:
    ```python
    {
        "schema_version": "ordered-wal-projection/v1",
        "source_wal_ref": {"path": ..., "sha256": ...},
        "byte_start": frames[0].byte_start,
        "byte_end": frames[-1].byte_end,
        "build_attempt_id": build_attempt_id,
        "records": [
            {
                "variant": frame.record.variant,
                "stage": frame.record.stage,
                "env_tag": frame.record.env_tag,
                "ts": frame.record.ts,
                "payload": frame.record.payload,
            }
            for frame in frames
        ],
    }
    ```
  - `frames` 非空、隣接 frame の `byte_end == 次の byte_start`、全 attempt 一致、末尾が commit/abort、末尾 `byte_end == source prefix length` を要求する。
  - source blob は terminal 時点の `wal.jsonl[0:byte_end]`。これにより後続追記に依存しない一方、projection の byte offset は元 WAL と同じである。

- 3 種の相対 path は次で固定する。`<physical>` は outer evidence root から当該 `layout.root` への相対 path。
  ```text
  <physical>/reports/reflux-result-evidence-content/v1/source-wal/<source_sha256>.jsonl
  <physical>/reports/reflux-result-evidence-content/v1/ordered-wal/<projection_sha256>.json
  <physical>/reports/reflux-result-evidence-content/v1/execution-provenance/<provenance_sha256>.json
  ```

- `reflux_result_evidence.py:1014-1058`
  - execution provenance producer を `_validate_execution_provenance()` と同じ exact 8 key で作る。
  - 値は以下から取る。
    - `build_attempt_id`: `EvalResult.build_attempt_id`
    - `campaign_id`: logical `trial_binding.campaign_id`
    - `campaign_run_identity`: `run_campaign` が確定した physical `cid`
    - `workload`: capability
    - `contract_sha256`: authorized contract
    - `trigger_binding`: projection 内の唯一の実 `trigger_binding` WAL frame から再導出
    - `execution_receipt_sha256`: actual execution receipt canonical bytes
  - receipt 欠落、contract と capability の環境 digest 不一致、trigger frame がゼロ/複数なら発行拒否する。

- `reflux_result_evidence.py:493-614, 720-760, 891-905`
  - `issue_campaign_result_evidence()` は全構造を memory 上で構成し、最初に `derive_physical_result()` と `assemble_result_evidence_record()` を通す。
  - その後だけ source blob -> projection -> provenance -> `issue_result_evidence_record()` の順で create-only 発行する。
  - `expected_record_path` と `result_evidence_relative_path(record).as_posix()` は write 前に一致させる。
  - accepted は `verify_result=None`、rejected は A が保持した値を渡す。`derive_physical_result()` の三方向分岐は変更しない。

- `orchestrator/tests/test_reflux_result_evidence.py:524-556`
  - 既存 `test_wal_ordered_attempt_frames_preserve_order_and_physical_offsets` を producer 正例の土台に使う。
  - 実 `wal.log()` で連続 attempt を書き、producer -> `resolve_content_addressed_ref()` -> `_resolve_ordered_wal()` を通して raw interval 一致を検査する。
  - 負例は既存テストと同様に別 attempt frame を間へ挟み、非連続区間として発行前に拒否され、3 file/record が作られないことを検査する。
  - truncated final frame、symlink ancestor、既存 digest path、read-back mismatch も発行失敗にする。

### C. S3: `loop.py`

- `loop.py:26-47`
  - `reflux_result_evidence` と `ResultEvidenceIssuanceContext` を import する。

- `loop.py:240-270` の既存 signature 末尾へ:
  ```python
  result_evidence_context: Optional[ResultEvidenceIssuanceContext] = None,
  ```
  を追加する。既存全 caller は既定 `None` で変更不要。

- `loop.py:280-393`
  - context 非 `None` のときだけ、exact context 型、`len(genomes) == 1`、`balanced_schedule is None` を最初の durable write より前に要求する。
  - originless ではこの分岐へ入らず、WAL payload、summary、report 用 state を一切増やさない。

- `loop.py:412-419`
  - `context.evidence_root` は既存実 directory、かつ `output_root` と同じ outer root へ解決されることを要求する。
  - physical `layout.root` がその下にあることを確認する。

- `loop.py:522-539`
  - identity-error の `EvalResult` に生成済み `attempt_id` を設定する。typed result は `None`。

- `loop.py:631-654`
  - catch した eval exception で replay から active attempt が一意なら、その ID を synthetic `EvalResult.build_attempt_id` にも設定する。
  - result-evidence issue 自体はこの `try` 範囲へ入れない。

- `loop.py:655-667`
  - `_PreparedEvaluation` 分岐の後、`s.results.append(r)` より前に:
  ```python
  if result_evidence_context is not None:
      issue_campaign_result_evidence(
          layout=layout,
          context=result_evidence_context,
          build_attempt_id=r.build_attempt_id,
          verify_result=r.verify_result,
          authorized_contract_sha256=authorized_contract.contract_sha256,
          execution_receipt=execution_receipt,
          campaign_run_identity=cid,
      )
  ```
  を置く。
  - これが terminal WAL 後、次 genome 前の発火点である。
  - `ResultEvidenceError` / `ResultEvidenceIssuanceRefused` を `eval-exception` abort に変換しない。既に terminal の attempt へ二重 abort を足さず、そのまま campaign failure とする。

- `loop.py:668-692`
  - balanced branch と campaign 最終 log/return には issuer を置かない。ここでは複数 result と複数 attempt の対応が一意でない。

- 新規 `test_reflux_campaign_issuer.py:1`
  - origin context 付き一件 campaign で、実 terminal WAL を producer が読み、record pathが作られる正例。
  - issuer の create-only failure が `run_campaign()` 外へ伝播し `CampaignSummary` を返さない負例。
  - context `None` の同一 drive で、WAL bytes と layer3 report の非揮発入力 bytes、ならびに新規 file 集合が変更前と完全一致する負例兼互換性検査。

### D. S4: runtime と caller

- `p3_autonomous_workload_trial.py:43-54`
  - `reflux_result_evidence` と public source-closure validator を import する。

- `p3_autonomous_workload_trial.py:461-471`
  - `OriginProducerInputs` に次を追加する。
  ```python
  batch_id: str
  query_ordinal: int
  ```
  `result_record_bytes` は fixture scope の companion record 群として残す。本 wave では ledger batch producer topology を新設しない。

- `p3_autonomous_workload_trial.py:475-491`
  - `OriginTrialRuntime` に in-process の
  ```python
  issued_result_record_paths: list[Path] = field(default_factory=list)
  ```
  を追加する。wire/report へは投影しない。

- `p3_autonomous_workload_trial.py:1644-1796`
  - batch ID、query ordinal 0..32、evidence root の実 path、`generations == 1` を origin-bound fixture slice の admission 時に検査する。
  - `producer_inputs.evidence_root` と `campaign_output_root` は同じ解決済み root に固定する。
  - production authority は引き続き拒否し、fixture client だけを許す既存 capability 条件を変えない。

- `p3_autonomous_workload_trial.py:4895-4918`
  - 33 physical identities/run plan は既存どおり producer-owned とする。
  - active `query_ordinal` の `OriginCampaignRun` を一件選ぶが、複数 query を一 run に詰めない。

- `p3_autonomous_workload_trial.py:3938-4043`
  - origin runtime がある場合:
    - logical `prepared.campaign` の代わりに `origin_runtime.campaign_runs[query_ordinal].campaign` を drive へ渡す。
    - layout は
      ```python
      exploration_campaign_layout(
          campaign_run_identity,
          str(origin_runtime.campaign_output_root),
      )
      ```
      とする。
    - originless branch の既存 `exploration_campaign_layout(campaign_id)` は変更しない。

- `p3_autonomous_workload_trial.py:2323-2362`
  - `_drive_s8c_generation()` に optional `result_evidence_context` と `campaign_output_root` を追加する。
  - `drive is trigger.drive_iteration` の場合だけ `drive_kwargs` へ渡す。caller-injected drive へ勝手に渡さない。

- `p3_autonomous_workload_trial.py:4340-4377`
  - drive 直前に `ResultEvidenceIssuanceContext` を構成する。
  - 7 入力の出所:
    - capability: `runtime.capability`
    - evidence root: `runtime.producer_inputs.evidence_root`
    - batch ID: `runtime.producer_inputs.batch_id`
    - query ordinal: `runtime.producer_inputs.query_ordinal`
    - p6 plan: `run_plan_input` の hypothesis/validation digest と query 0/非0による purpose
    - trial binding: launch digest + capability の logical campaign/workload
    - origin binding: capability の authority/source/cell/workload/policy/environment fields
  - iteration/replicate ordinal と expected evidence path は `runtime.run_plan.members[q]` から取得し、caller の同名自己申告を使わない。

- `p3_autonomous_workload_trial.py:4378-4405`
  - actual drive が戻った後、`context.evidence_root / context.expected_record_path` を read-back し、runtime の issued path に一件だけ登録する。
  - harness outcome/report へ新しい key を足さず、`autonomous_trial_completeness` の exact schema を動かさない。

- `p3_autonomous_workload_trial.py:1840-1891`
  - `_complete_origin_runtime()` は active `(batch_id, query_ordinal)` の caller-supplied bytes を disk の freshly issued bytes に置換して formal consumer へ渡す。
  - 同じ key が複数、issued path がゼロ/複数、disk bytes が非 canonical なら停止する。
  - fixture ledger が保持する evidence digest と新 bytes が異なれば、既存 FC01 のまま失敗させる。ledger member を書き換えて帳尻を合わせない。

- `p3_s4_loop_trigger_gating.py:644-662`
  - `_assert_layout_matches_campaign()` に optional outer root を追加し、origin branch はその root から期待 physical layout を導く。

- `p3_s4_loop_trigger_gating.py:734-749`
  - `_run_one_iteration_resolved()` に optional issuance context/output root を追加する。

- `p3_s4_loop_trigger_gating.py:811-820`
  - `run_campaign()` へ
  ```python
  output_root=campaign_output_root
  result_evidence_context=result_evidence_context
  ```
  を context 非 `None` 時だけ渡す。

- `p3_s4_loop_trigger_gating.py:984-1002`
  - `drive_iteration()` に同じ optional 引数を追加する。

- `p3_s4_loop_trigger_gating.py:1029-1043, 1118-1127`
  - physical cfg/layout の identity を outer root 込みで照合し、resolved runner へ context を素通しする。
  - trigger CLI の既存 caller は既定値で不変。

- `p3_autonomous_workload_trial.py:5355-5504`
  - 既存 `main()` に `--origin-fixture-inputs PATH` の明示 opt-in を追加する。
  - exact fixture input document を読み、次の公開 API だけを使う:
    - `OriginLedgerClient.for_fixture_repository()`
    - `validate_source_closure()`
    - `run_origin_trial()`
  - `_fixture_store_for_test()`、`_prepare_origin_trial_runtime()`、ledger `_locked()` などの private seam を CLI から呼ばない。
  - option なしは現在の `run_trial()` call `:5475` をそのまま維持する。
  - option ありだけ `run_origin_trial()` を呼び、`OriginCompletedTrialReport` を exit 0、preflight/partial を exit 2 とする。

## 設計択一の答え

### 1. ordered WAL projection producer の module

`reflux_result_evidence.py` に置く。新 module は作らない。

15-file pin の実体は `orchestrator/tests/test_reflux_formal_consumer.py:32-48` の `WAVE_PRODUCTION_FILES` である。`test_reflux_formal_consumer.py:2285-2309` が `len == 15`、exact set、各 file の存在を固定し、その15 fileだけを source scan する。

新 module を追加しても、この test は directory discovery をしないので自動では赤にならない。新 file が検査対象外になるため、閉集合という保証を実質的に破る。S2 は record/evidence bytes の producer であり `reflux_result_evidence.py` が契約所有者なので、D1809 の却下理由は当たる。

ただし `wal.py:258-272` の `OrderedAttemptFrame` と `wal.py:1671-1710` の `ordered_attempt_frames()` は既に存在する。新設するのは physical offset reader ではなく、それを projection/source blobへ凍結する producer である。

### 2. content-addressed artifact の置き場

`evidence_root` は `OriginProducerInputs.evidence_root`、すなわち origin trial の outer `run_root` とする。`OriginTrialRuntime.campaign_output_root` と同じ実 path に固定する。

3 file は前記の physical campaign subtree 下へ置く。これにより formal consumer の `reflux_formal_consumer.py:974-982` が要求する projection/source の physical campaign root 内配置を満たす。一方、result record は既存 core APIにより:

```text
<evidence_root>/reports/reflux-result-evidence/<origin>/<batch>/<q>.json
```

へ置かれる。

resolver の根拠は以下。

- `reflux_result_evidence.py:617-623`: ref は exact `{path,sha256}`、backslash 不可。
- `:920-934`: absolute、空、`.`、root 脱出を拒否し、root/target の全 symlink component を拒否。
- `:937-969`: `O_NOFOLLOW`、regular file、read 前後の device/inode 一致。
- `:978-1001`: raw SHA-256 の一致。
- `:1107-1129`: source ref と指定 byte interval の実 bytes が projection records と一致。

fixture builder の初期 seed path `wal/source/*.json`、`wal/projections/*.json`、`provenance/*.json` (`reflux_origin_fixture_builder.py:467-552, 688-711`) は literal には踏襲しない。ordinal 名で content-addressed ではなく、テストが後から書換えるためである。

一方、outer evidence root を共有し、physical source/projection/provenance を campaign subtree へ置く構造は `test_reflux_formal_consumer.py:245-316` の `_materialize_physical_evidence()` を踏襲する。

### 3. `EvalResult` の typed `VerifyResult`

accepted の最終 `EvalResult` には保持しない。`verify_result=None` が正しい。

D1809 の accepted 条件は projection terminal commit と ordered `verify_configs` の exact 一致で閉じており、実装も `reflux_result_evidence.py:549-567` で `verify_result` 無しを受理する。複数 pass/repetition のどれか一つを選ぶ規則を新設すると、全 pass 成功という事実を単一 pass に誤縮約する。

経路は次とする。

- local verifier の戻り値は `_RepetitionExecutionOutcome.verify_result` に一時保持。
- rejected なら `_project_repetition_outcome()` -> `_abort(..., verify_result=...)` -> `EvalResult.verify_result`。
- accepted repetition は capability を積んだ後、typed 値を破棄。
- 最初に失敗した local repetition は即 return されるので、rejected の値は一意。
- remote fan-out rejected は typed 値なしで、issuer は拒否する。

### 4. issue の発火条件と署名

発火点は `loop.py:655` 相当、`evaluate()` の既存 catch が終わった後、summary 集計より前である。`loop.py:690-692` ではない。

必要条件は:

- exact `ResultEvidenceIssuanceContext` が提示済み
- one genome、非 balanced
- physical campaign ID/layout が query ordinal と一致
- terminal WAL と non-empty build attempt ID が存在
- capability、evidence root、batch/query/member、p6/trial/origin binding が相互一致
- verifier-policy bytes の digest/order が capability と一致
- actual execution receipt が存在
- actual environment contract digest が capability と一致

推奨 signature は:

```python
def run_campaign(
    ...,
    *,
    ...,
    result_evidence_context: Optional[
        reflux_result_evidence.ResultEvidenceIssuanceContext
    ] = None,
) -> CampaignSummary:
```

7 入力の実経路は:

```text
run_trial:4826 _prepare_origin_trial_runtime
  -> OriginTrialRuntime:475
  -> _finish_trial:3608-3610
  -> _run_workload:3938-3950
  -> _drive_s8c_generation:2323-2362
  -> p3_s4_loop_trigger_gating.drive_iteration:984
  -> _run_one_iteration_resolved:734
  -> run_campaign:811
```

現在届いていないため、編集が必要な全 production file は:

- `p3_autonomous_workload_trial.py:461-491`
- `p3_autonomous_workload_trial.py:1644-1796`
- `p3_autonomous_workload_trial.py:2323-2362`
- `p3_autonomous_workload_trial.py:3938-4043`
- `p3_autonomous_workload_trial.py:4340-4405`
- `p3_s4_loop_trigger_gating.py:644-662`
- `p3_s4_loop_trigger_gating.py:734-820`
- `p3_s4_loop_trigger_gating.py:984-1127`
- `loop.py:240-270`
- `loop.py:655-667`

### 5. `run_origin_trial` の production 呼び手

`p3_autonomous_workload_trial.py:5355` の既存 `main()` に置く。

静的棚卸しでは、非 test の `run_origin_trial(...)` caller はゼロだった。関連 CLI は:

- `p3_autonomous_workload_trial.py:5355-5508`: trial admission、provider、worktree、build authorityを既に所有する入口。現在は `:5475` で `run_trial()` を呼ぶ。
- `p3_s4_loop_trigger_gating.py:1181-1393`: 単一 iteration 用で、origin launch/client/runtime を所有しない。
- `layer3_report.py:1067-1089`: read-only renderer。
- `tools/` 配下: `run_trial` / `run_origin_trial` caller なし。

したがって新しい `tools/` wrapperや campaign moduleを作るより、既存 main の明示 fixture-origin modeから public `run_origin_trial()` を呼ぶのが最小である。これが設計 §12 要件1の「private 直呼びにしない公開経路」の正例になる。

## 正例・負例

### S1 typed 保持

- 正例: synthetic Silo source付き `r9_dense_cycle4` を実 verifierへ通し、local non-serializable outcome の `EvalResult.verify_result` が exact `VerifyResult`、terminal wire snapshot が `result_to_dict()` と同値。
- 負例: `_admit_verify_fanout_result()` の authenticated remote abort。wire payloadがあっても `EvalResult.verify_result is None` で、rejected issuance は拒否。

### S2 projection/provenance

- 正例: 実 `wal.log()` が作った `trigger_binding -> build_start -> build_done -> verify_done -> abort` の連続 framesを `wal.ordered_attempt_frames()` で読み、実 resolverが source interval一致まで通す。
- 負例: attempt A の途中へ attempt B frameを挟む。選択 frameが非連続なので、source/projection/provenance/recordを一件も正常発行しない。

### S3 campaign issuer

- 正例: origin context付き one-genome campaignの local `r9_dense_cycle4` terminal abort。実 `derive_physical_result -> assemble_result_evidence_record -> issue_result_evidence_record` を通り、fresh recordを formal consumer入力へ差し替える。
- 負例: execution receipt欠落、remote rejected、複数 witness class `r8_silo_broken_norw` のいずれか。`run_campaign()` は summaryを返さず、既存 terminalを成功扱いにしない。

### S4 public route

- 正例: `p3_autonomous_workload_trial.main --origin-fixture-inputs ...` -> `run_origin_trial()` -> `OriginLedgerClient.for_fixture_repository()` -> actual drive -> actual `run_campaign()`。fixture ledgerのactive member digestがfresh record bytesと一致する固定 fixtureでは formal consumerが FC04/FC07/FC09を通過し `P6Unavailable` に達する。
- 負例: production client、queryとphysical campaign identityの不一致、またはfixture ledgerのactive evidence digestとfresh record bytesの不一致。public wrapperは preflight/partial resultを返し、`P6Unavailable` やcampaign成功を返さない。

fixture ledgerをfresh recordの将来 digestへ合わせる正例は synthetic到達性に限る。ledger batch producer topologyを本 waveで新設した証拠にはしない。

## 波及する既存 consumer

- `pipeline.EvalResult`
  - `loop.py:58-75, 537-539, 653-665`
  - `p3_s4_loop_trigger_gating.py:830-858`
  - `s1_direct_comparison.py:956`
  - `screening_driver.py:521,638`
  - `backoff_repro.py:167-177`
  - 多数の `test_campaign.py` / `test_screening_driver.py` constructor。追加 field は末尾既定値なので既存 keyword/positional callerを壊さない。

- `run_campaign()`
  - `p2_2.py:376`
  - `sanity_silo.py:59`
  - `backoff_sweep.py:408`
  - `s6_sort_sweep.py:413`
  - `backoff_repro.py:167`
  - `paper_story_a1_paired.py:6962,7209`
  - `p3_s4_loop_trigger_gating.py:811`
  - 全既存 caller は context未指定で byte不変。

- evidence/consumer
  - `reflux_formal_consumer.py:829-843, 846-883, 886-982, 1041-1052, 1133-1264`
  - `test_reflux_formal_consumer.py` の FC01〜FC10 全 conjunct。
  - `test_reflux_formal_consumer.py:32-48,2285-2309` の15-file source closure。
  - consumer式、reason code、受理集合は編集しない。

- shared fixture
  - `reflux_origin_fixture_builder.py:467-556,668-766`
  - 既存 golden seed pathは維持し、production path検査用 helperを別関数として追加する。

- report
  - `layer3_report.py:208-231` は physical campaign root全 fileを走査する。
  - origin-bound時、3 content artifactsは `run_campaign()` return前に置かれるため、`p3_autonomous_workload_trial.py:3045-3077` の Layer3 renderに決定的に含まれる。
  - originless時は一件も置かない。

- autonomous report schema
  - `p3_autonomous_workload_trial.py:3902-3927` の completeness / Layer3 chain。
  - issued pathはruntime内部だけに保持し、report/harnessへ新 keyを足さない。

## 親 brief の誤り

1. `brief-t2437.md:20` は low-level producer部品を落としている。完成した ordered projection artifact producerは無いが、physical frame/offset APIは既に `wal.py:258-272,1671-1710` にあり、`test_reflux_result_evidence.py:524-556` で検査済みである。再実装してはならない。

2. `brief-t2437.md:21` の「最終化点 `loop.py:686-692`」と、同 brief `:54-55` の「次 variant開始前」は、一般の複数 genome campaignでは両立しない。正しい発火点は per-result の `loop.py:655-667` である。

3. `brief-t2437.md:71-72,80-81` の編集面から `p3_s4_loop_trigger_gating.py` が欠落している。実際の `run_campaign()` call は同 file `:811` にあり、追加引数を通すには同 fileの signature chain編集が必須。

4. `brief-t2437.md:101-102` の「record群が physical campaignの `artifact_refs` に載る」は現 fixture/consumer配置と食い違う。`test_reflux_formal_consumer.py:245-316` は source/projection/provenanceだけをphysical campaignへ置き、record自体は outer evidence rootに残す。既存 `issue_result_evidence_record(evidence_root=...)` と単一 evidence root consumerを変えない限り、physical Layer3 reportに載るのは3 content artifactsでありrecord本体ではない。

5. `brief-t2437.md:43-46` の fixture pathは capability到達性としては正しいが、それだけではfresh recordをformal consumerが受理しない。current p3 origin pathは `p3_autonomous_workload_trial.py:1859-1897` で既存 sealed batchesを読むだけで、batch reserve/commit/results/seal producerを実行していない。fixture ledger memberのevidence digestがfresh record bytesと一致する固定 fixtureが必要であり、これはproduction ledger topologyの証明ではない。

## 総括

実装方針は、acceptedで曖昧なtyped resultを保持せず、rejected local resultだけを保持し、既存 WAL offset APIからcontent-addressedな3 artifactを作り、`run_campaign()` のper-attempt terminal直後に実 issuerを発火させる形である。

originless経路は追加 keywordの既定 `None` で、WAL bytes、report bytes、file集合を一切変えない。origin-bound経路では3 artifactをLayer3構築前に確定し、issue失敗をcampaign成功へ変換しない。

`run_origin_trial` の公開 callerは既存 autonomous trial CLIへ置く。ただし本 waveが示せるのは、production package内のissuer配線とfixture scopeの到達性までであり、33件のledger producer topologyやproduction authorityの成立ではない。

read-only条件のため、コード編集、pytest、静的checkerの実行は行っていない。