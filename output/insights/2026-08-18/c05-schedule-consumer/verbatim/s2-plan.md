## 1. 実装プラン

### 単位 A: schedule consumer と単体テスト

#### `orchestrator/campaign/s8c_schedule.py:1-約350` 新設

予定する骨格:

- `1-30`: モジュール docstring、既存の `_canonical_json_bytes` と `_sha256` の import、`__all__`、schema 定数。
- `31-70`: `ScheduleError(ValueError)`、`ScheduleCell`、`Schedule` の frozen dataclass。
- `71-125`: `DESIGNATED_SOURCE_CONTEXT`、role payload allowlist、`ARMS`、`HOLDOUTS`、`HOLDOUT_BINDINGS` から search-space preimage を作る内部関数。世代 0 state の preimage もここで作る。
- `126-185`: `master_seed` から canonical JSON bytes と SHA-256 で cell の順序を決める `regenerate(master_seed) -> bytes`。
- `186-275`: duplicate key、UTF-8、非有限数、exact key、型、hash、cell 集合を検査する strict decoder。
- `276-350`: 次の API。

| API | 戻り値 | 失敗時 |
|---|---|---|
| `regenerate(master_seed: str) -> bytes` | canonical schedule artifact bytes | `ScheduleError` |
| `verify_exact_schedule_bytes(artifact_bytes: bytes, *, master_seed: str) -> None` | `None` | `ScheduleError` |
| `verify_shared_search_space_and_initial_state(schedule: Mapping[str, object]) -> None` | `None` | `ScheduleError` |
| `verify_schedule(artifact_bytes: bytes, *, master_seed: str) -> Schedule` | immutable `Schedule` | `ScheduleError` |
| `consume_schedule(artifact_bytes: bytes, *, master_seed: str, schedule_index: int) -> ScheduleCell` | immutable `ScheduleCell` | `ScheduleError` |

`consume_schedule` はファイルを再読せず、呼び出し元が一度読んだ同一 bytes を `verify_schedule` と共有する。

#### `orchestrator/tests/test_s8c_schedule.py:1-約300` 新設

次を検査する。

- 同一 `master_seed` の再生成が byte-exact に一致する。
- 異なる seed が artifact bytes と deterministic order に反映される。
- top-level key、schema version、master seed、末尾 LF を検査する。
- `cells` が6件、`schedule_index == 0..5`、重複なし、`HOLDOUTS × ARMS` と完全一致する。
- `ARMS == ("on", "off", "swapped")` の順序を candidate tuple と tie-break に使用する。
- `verify_exact_schedule_bytes` が seed 不一致、余剰 bytes、canonical JSON でない bytes を拒否する。
- `verify_shared_search_space_and_initial_state` が欠落、余剰、型違反、hash 不一致をすべて拒否する。
- search-space または initial-state の元定数を変更した後、旧 artifact を拒否する。
- `consume_schedule` が範囲外、bool、重複 index を拒否し、正しい `ScheduleCell` だけを返す。

### 単位 B: C05 evaluator と負の対照

#### `orchestrator/campaign/s8c_preregistration_evidence.py:67-69`

`ReasonCode.SCHEDULE_CONSUMER_UNREACHABLE` を `SCHEDULE_CONSUMER_UNDEFINED` の直後に追加する。

#### `orchestrator/campaign/s8c_preregistration_evidence.py:1629`

`_evaluate_c09` の直前へ `_evaluate_c05` を挿入する。

- `probe.read_kind("schedule_artifact")` が `None` なら `EVIDENCE_UNDEFINED / SCHEDULE_SCHEMA_ABSENT`。
- `probe.python_kind("schedule_consumer")` が `None` なら `EVIDENCE_UNDEFINED / SCHEDULE_CONSUMER_UNDEFINED`。
- `regenerate`、`verify_exact_schedule_bytes`、`verify_shared_search_space_and_initial_state`、
  `verify_schedule`、`consume_schedule` の関数定義と schema field literal を `_functions`、`_strings`、
  `_live_called_names` で確認する。
- `verify_schedule` から exact bytes 検証と shared hash 検証が live に呼ばれることを確認する。
- `consume_schedule` が `verify_schedule` を live に呼ぶことを確認する。
- `_ReachabilityExplorer` で `run_trial` から `verify_schedule` と `consume_schedule` が到達可能か確認する。
- production 配線が無い場合は `UNSATISFIED / SCHEDULE_CONSUMER_UNREACHABLE`。
- 全静的条件を通過しても、戻り値は必ず `EVIDENCE_UNDEFINED / COMPLETION_PROOF_NOT_MACHINE_CHECKABLE`。

AST と commit blob だけを使い、module import、関数実行、artifact の実行評価は行わない。

#### `orchestrator/campaign/s8c_preregistration_evidence.py:1806-1818`

`_MACHINE_EVALUATORS` に 5 を追加しない。`SATISFIABLE_CONDITION_IDS` も変更しない。

#### `orchestrator/tests/test_s8c_preregistration_predicates.py:21-24`

`s8c_schedule` をテスト用に import する。

#### `orchestrator/tests/test_s8c_preregistration_predicates.py:746` 付近

既存の `NEGATIVE_CONTROL_CASES` には追加せず、次の別集合を置く。

```python
NON_MACHINE_CHECKABLE_NEGATIVE_CONTROL_CASES = {
    "nc_c05_initial_state_hash_bitflip": "C05",
}
```

これは `test_satisfiable_predicate_requires_negative_control:1974-1995` の exact 集合に入れない。

同 file の末尾付近へ専用テストを追加する。

1. `regenerate(seed)` の baseline が `verify_schedule` と `verify_shared_search_space_and_initial_state` を通ることを確認。
2. 1 cell の `initial_state_sha256` の1 bitだけを反転。
3. 変更されたのがその field だけで、artifact bytes が baseline と異なることを assert。
4. shared hash verifier と `verify_schedule` の両方が `ScheduleError` を raise することを assert。
5. したがって常に通る対照ではなく、baseline の通過と bitflip の拒否を同じテストで固定する。

## 2. 設計判断と根拠

### 1. schedule API、再生成、schema

`schema_version` は `"s8c-schedule/v1"` とする。artifact の top-level key は次の3つだけ。

```text
schema_version
master_seed
cells
```

cell の key も次の5つだけ。

```text
schedule_index
holdout
arm
search_space_sha256
initial_state_sha256
```

`HOLDOUTS` を外側、`ARMS` を内側にした candidate tuple を作り、各 tuple の順序 key を次で計算する。

```text
sha256(
  canonical_json_bytes({
    "domain": "s8c-schedule/order/v1",
    "master_seed": master_seed,
    "holdout": holdout,
    "arm": arm
  })
)
```

この digest bytes、holdout index、arm index の順で安定 sort し、sorted 結果へ `schedule_index` 0〜5 を付ける。Python の `random` 実装や hash iteration 順に依存しないため、同じ source、seed、定数から同じ bytes になる。

`verify_exact_schedule_bytes` の判定式は次の通り。

```text
artifact_bytes == regenerate(master_seed)
```

`verify_shared_search_space_and_initial_state` は全6 cell について次を要求する。

```text
cell.search_space_sha256 == current_search_space_sha256()
cell.initial_state_sha256 == current_initial_state_sha256()
```

さらに strict decoder が、欠落、余剰、型違反、範囲外 index、重複 index、重複 cell、未知 arm、未知 holdout をすべて `ScheduleError` にする。

### 2. hash の束縛先

canonical JSON は既存の `orchestrator/campaign/s8b_prediction_runner.py:195-204` の `_canonical_json_bytes` を再利用する。新しい canonicalization 規約は作らない。

search-space hash の preimage は次の object の canonical JSON bytes とする。

```text
{
  "domain": "s8c-schedule/search-space/v1",
  "designated_source_context": p3.DESIGNATED_SOURCE_CONTEXT,
  "role_payload_allowlist_sha256": p3.ROLE_PAYLOAD_ALLOWLIST_SHA256,
  "arms": list(trial_registry.ARMS),
  "holdouts": list(trial_registry.HOLDOUTS),
  "holdout_bindings": canonicalized HOLDOUT_BINDINGS
}
```

このため `DESIGNATED_SOURCE_CONTEXT`、role payload allowlist、holdout の workload binding のいずれかが変われば digest も変わる。

initial-state hash の preimage は次の canonical JSON bytes とする。

```text
{
  "domain": "s8c-schedule/initial-state/v1",
  "role_metrics": dict(p3._INITIAL_ROLE_METRICS),
  "whiteboard": [],
  "whiteboard_source_sha256": sha256(
      inspect.getsource(p3._whiteboard).encode("utf-8")
  ),
  "load_loop_state_source_sha256": sha256(
      inspect.getsource(p3.loop_core.load_loop_state).encode("utf-8")
  )
}
```

`_INITIAL_ROLE_METRICS` は `p3_autonomous_workload_trial.py:127-133`、世代 0 の empty whiteboard は同 `:1242-1244` に束縛する。whiteboard の実装または absent-state の loader が変わっても hash が変わる。source を取得できない場合も `ScheduleError` とし、既定値へ縮退しない。

(P1) は同意する。`_evaluate_c05` は置くが登録しない。

(P2) は同意する。artifact bytes は単体テストの一時値またはメモリ上だけで扱い、repo へ置かない。

(P3) は同意する。production `run_trial` への配線が無い状態を維持するため、C05 の到達性検査は未配線を拒否する。

(P4) は部分同意する。`DESIGNATED_SOURCE_CONTEXT` を主束縛先とする判断は正しいが、source context の literal だけでは workload binding と payload admission の変更を見逃すため、上記の allowlist と `HOLDOUT_BINDINGS` を含める。

### 3. `_evaluate_c05` の判定

新設 reason code は `SCHEDULE_CONSUMER_UNREACHABLE` とする。既存の `SCHEDULE_SCHEMA_ABSENT` は artifact 欠落、`SCHEDULE_CONSUMER_UNDEFINED` は consumer/API 欠落に限定する。

`_MACHINE_EVALUATORS` へは登録しないため、現行 dispatch の C05 は引き続き `schedule-schema-absent` になる。これは gap ledger の `test_current_repository_gap_reason_snapshot_requires_cross_wave_review:139-166` と整合する。

`_evaluate_c05` の terminal は必ず `COMPLETION_PROOF_NOT_MACHINE_CHECKABLE` であり、`SATISFIED` を返す branch は作らない。

### 4. 負の対照の配置

`NEGATIVE_CONTROL_CASES:735-743` は machine-checkable 7条件と完全一致するため変更しない。C05 をそこへ足すと `test_satisfiable_predicate_requires_negative_control:1974-1995` が意図どおり赤になる。

C05 は `NON_MACHINE_CHECKABLE_NEGATIVE_CONTROL_CASES` へ分離し、専用テストからのみ参照する。bijective meta-test `:2229-2239` の集合も変更しない。

### 5. 新 module の単体テスト

配置は `orchestrator/tests/test_s8c_schedule.py` とする。テスト対象は次の通り。

- byte-exact regeneration。
- deterministic cell order。
- schema、型、欠落、余剰、重複の fail-closed 検査。
- search-space hash と initial-state hash の再導出。
- hash source mutation の検出。
- `verify_exact_schedule_bytes` と `verify_schedule` の seed binding。
- `consume_schedule` の index 選択と範囲検査。
- initial-state hash bitflip の reject。

## 3. 恒真にならないことの論証

全 cell が同じ hash かを見るだけにはしない。各 cell の値を live な source、定数、binding から再導出した expected value と比較する。

```text
search_hash = H(CJ(search_space_binding))
initial_hash = H(CJ(initial_state_binding))
```

ここで `CJ` は既存 helper、`H` は SHA-256。したがって全 cell を同じ任意文字列へ書き換えても通らない。

initial-state negative control は、baseline が通ることを先に確認してから1 bitだけ反転した cell を検査する。反転後は shared verifier の

```text
cell.initial_state_sha256 != current_initial_state_sha256()
```

に必ず該当する。さらに exact bytes verifier も `mutated_bytes != regenerate(seed)` で拒否する。

単体テストでは source constant を変更して旧 artifact を検査するため、module が生成時の hash を固定キャッシュしていても検出できる。

## 4. 波及

- 新規 module は `orchestrator/campaign/s8c_schedule.py` のみ。現 wave では production caller は追加しない。
- 新規単体テストは `orchestrator/tests/test_s8c_schedule.py`。
- `s8c_preregistration_evidence.py` は ReasonCode と未登録 evaluator を追加するが、現行 registry の C01〜C12 の結果は変わらない。
- gap ledger の C05 期待値 `schedule-schema-absent` は変更しない。
- 既存 `NEGATIVE_CONTROL_CASES`、satisfiable meta-test、bijective meta-test の期待集合は変更しない。
- `trial_registry.py`、`p3_autonomous_workload_trial.py`、契約 JSON、凍結成果物、docs、実 schedule artifact は編集しない。
- brief が示すとおり、`test_s8c_preregistration_predicates.py` は t1333 と共有 ownership なので、実装前に concurrent worktree の land 状態を再確認する必要がある。

## 5. 残るリスクと未確認点

- `inspect.getsource` は source loader や改行形式に依存するため、取得不能時の fail-closed と単体テストが必要。
- AST reachability は実行時の例外経路や動的 dispatch の意味までは証明しない。C05 は static-only かつ未登録のため、この wave では許容範囲。
- production 配線が無いため、現行 commit の C05 は `schedule-schema-absent` のままであり、正式系列を起動可能にはしない。
- sandbox が read-only のため、pytest、build、mutation matrix は未実行。親が `tools/run_tests.py` 経由で確認する必要がある。
- 新規 module の import が p3 supervisor の依存 import を伴うため、親環境での import-only 確認が必要。

## 総括

単位 A は、既存 canonical JSON helper と live source から6 cell scheduleを再生成する新 moduleと単体テストを追加する。  
単位 B は C05 evaluator を未登録のまま実装し、未配線を `SCHEDULE_CONSUMER_UNREACHABLE` として拒否する。  
C05 の負の対照は既存 machine-checkable 集合から分離し、initial-state hash の1 bit反転を実際に拒否させる。  
契約 JSON、凍結成果物、production 配線、実 artifact、既存期待値は変更しない。