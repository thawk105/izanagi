# T-403 実装プラン

前提として、brief は読取可能、対象 3 テストは実在し、worktree は clean だった。以下の行番号は現 HEAD 基準である。read-only のためテストは実走していない。

## 1. hold record の schema・格納・create-only

対象は [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:81)。

### 格納 path

`_dispatch_impl` が決める dispatch root `root`（`dispatch_compute.py:1323-1326`）の直下に固定する。

```text
<repo>/output/pegasus-dispatch/orphan-hold.json
```

submission nonce 配下には置かない。次回 invocation、mutation harness、mutation worktree のすべてが nonce を知らずに同じ file を検査でき、`_stash_dispatch_evidence` が dispatch root 全体を退避すると hold も一緒に保全される。

### schema

`dispatch_compute.py:81-86` 付近に次を追加する。

```python
_ORPHAN_HOLD_NAME = "orphan-hold.json"
_ORPHAN_HOLD_SCHEMA = "pegasus-orphan-hold/v1"
```

JSON の exact schema は次とする。

| key | 型 | 値・由来 |
|---|---|---|
| `schema_version` | `str` | exact `"pegasus-orphan-hold/v1"` |
| `reason` | `str` | exact `"job-may-remain-without-terminal-evidence"` |
| `submission_dir` | `str` | 当該 dispatch の絶対 path |
| `request_id` | `str \| null` | receipt の `request_id`。discovery 不能なら `null` |
| `job_name` | `str` | receipt `request.job_name` と同じ値 |
| `qdel` | `object` | 下記の固定 projection |
| `recovery` | `str` | 「qstat で不在または終端を確認 → dirty path を `git checkout --` で復元 → hold を手動削除」の順序を明記 |

`qdel` object は次の exact keys とする。

| key | 型 | receipt 由来 |
|---|---|---|
| `job_may_remain` | `bool` | 常に `true` |
| `attempted` | `bool` | `receipt.qdel.attempted` |
| `returncode` | `int \| null` | qdel 未実行・例外なら `null` |
| `exception` | `str \| null` | `receipt.qdel.exception` |
| `gate` | `object` | 下記 |
| `gate.reason` | `str \| null` | `receipt.qdel.gate.reason` |
| `gate.request_present` | `bool \| null` | `receipt.qdel.gate.request_present` |

`qstat` stdout、scheduler state、分類文字列全体は複製しない。判定に不要であり、hold に新しい scheduler 語彙も導入しない。

### create-only

`_write_json_x`（`dispatch_compute.py:370-382`）は `O_CREAT | O_EXCL`、file `fsync` 済みなので再利用できる。新 helper を F47 helper 群の近く（`dispatch_compute.py:957-986`）へ置く。

```python
def _latch_orphan_hold(
    output_root: Path,
    *,
    qdel: Mapping[str, Any],
    submission_dir: Path,
    request_id: Optional[str],
    job_name: str,
) -> Optional[Path]:
    ...
```

- hold 不成立なら `None`。
- 新規作成時は `_write_json_x` の後に `_fsync_dir(output_root)`（`dispatch_compute.py:399-404`）を呼ぶ。
- `FileExistsError` だけを握り、既存 bytes を変更せず既存 path を返す。
- その他の `OSError` は握り潰さず INFRA 経路へ送る。
- 削除・上書き・自動解除は実装しない。
- 検査側は `path.exists() or path.is_symlink()` を「hold あり」とする。malformed JSON、directory、symlink でも fail-closed に止め、内容検証を投入許可条件にしない。

既に hold がある場合、最初の原因 record を保持する。後続 invocation は新しい submission directory、`qstat`、`qsub` のいずれも作らない。

## 2. hold 判定署名と全 gate reason の分類

### 判定署名

入力は完成した in-memory receipt の次の 3 fieldだけである。

- `receipt.qdel.job_may_remain`
- `receipt.qdel.gate.request_present`
- `receipt.qdel.gate.reason`

署名は次で固定する。

```text
H(qdel) :=
    (qdel.job_may_remain is True)
    and not (
        qdel.gate.request_present is False
        or qdel.gate.reason == "terminal-history-conflict"
    )
```

実装では `gate` が `Mapping` でなければ両方を「実証なし」と扱う。`True` / `False` は truthy 判定でなく identity 判定にする。

全体表は次のとおり。

| `job_may_remain` | `request_present` | `gate.reason` | hold |
|---|---:|---|---:|
| `True` | `False` | 任意 | 立てない |
| `True` | `True` / `None` / 不在 | `terminal-history-conflict` | 立てない |
| `True` | `True` / `None` / 不在 | その他 | 立てる |
| `False` / 不在 / 非 bool | 任意 | 任意 | 立てない |

### 全 reason の分類

| `qdel.gate.reason` | 通常生成時の実証 | hold | 理由 |
|---|---|---:|---|
| `request-id-unavailable` | `request_present=None` | 立てる | ID 不明は不在実証ではない |
| `malformed-request-id` | `None` | 立てる | qstat 未実行 |
| `qstat-attempt-limit-invalid` | `None` | 立てる | qstat 未実行 |
| `cleanup-budget-exhausted` | 通常 `None` | 立てる | 不在・終端を確定していない |
| `qstat-exception` | `None` | 立てる | 観測不能 |
| `qstat-transient-retries-exhausted` | `None` | 立てる | 観測不能 |
| `qstat-permission` | `None` | 立てる | 観測不能 |
| `request-absent` | `False` | 立てない | qstat rc=0 の不在実証 |
| `target-state-unknown` | `True` | 立てる | request は存在し、取消不能 |
| `state-not-cancellable` | `True` | 立てる | RUN/STG/EXT 等で残り得る |
| `terminal-history-conflict` | 通常 `True` | 立てない | 監視ループで END 観測済み |
| `gate-exception` | `None` または `True` | 立てる | 不在・終端実証なし。ただし独立に `request_present=False` なら不成立 |
| `fresh-cancellable-snapshot` | `True` | 条件付き | qdel 成功で `job_may_remain=False` なら不成立。qdel rc非0・例外なら成立 |
| `cleanup-claimed` | field 不在 | 立てる | cleanup の完成を実証していない初期 claim |

`gate-not-evaluated`（`dispatch_compute.py:1064`）は helper 内の過渡的初期値で、正常 return 前に上表の値へ置換される。万一そのまま残っても署名上は hold 側になる。

### 通る正例

通常 dispatch が child rcを回収する経路（`dispatch_compute.py:1466-1779`）では `claim_cleanup_once` 自体が呼ばれず hold は作られない。次回 invocation は従来どおり `qstat -Q`、`qsub` へ進む。

cleanup 経路でも、`fresh-cancellable-snapshot` から qdel rc=0 を得て `job_may_remain=False` になれば hold は作られず、次回投入を妨げない。

## 3. `_dispatch_impl` の投入遮断と F47 順序

### hold 発行位置

`claim_cleanup_once`（`dispatch_compute.py:1430-1456`）を次の順へ変える。

1. 現行どおり `_fresh_qstat_gated_qdel` を exactly once 呼ぶ。
2. 返された同一 `qdel_record` に上記署名を適用する。
3. 成立時だけ `_latch_orphan_hold` を呼ぶ。
4. hold pathを stderr へ出し、その後既存 callerへ `qdel_record` を返す。

これで F47 3経路（`1546-1585`, `1700-1730`）と例外経路（`1780-1822`）を1箇所で覆う。`_best_effort_qdel` の呼出しは現状の `dispatch_compute.py:1234` だけを維持する。新しい qdel call、gate 条件、受理集合は一切追加しない。

### 次回投入検査

`root.mkdir` 後、現在の F47 検査（`dispatch_compute.py:1350-1354`）の直後に置く。

```text
root.mkdir
→ submission-disabled.json 検査
→ orphan-hold.json 検査
→ nonce/submission directory 作成
→ qstat -Q
→ qsub
```

F47 を先にする理由は、既存 F47 の handoff 文言と優先順位を変えないためである。

両方がある場合は次の挙動になる。

1. F47 を表示して `INFRA_RC=16`。
2. scheduler command は0件。
3. F47 を人手解除して再試行しても orphan hold が残るため、そこで再度 rc=16。
4. orphan hold は孤児の終端確認と source 復元後にのみ人手削除する。

hold 分岐は `qsub`（現在 `dispatch_compute.py:1479-1492`）だけでなく、preflight `qstat -Q`、nonce作成、signal handler設置より前で戻る。したがって「invocation 開始時に既に hold がある」テストでは `run_command` の呼出しを空リストで固定できる。

なお、同じ root の2 invocation が同時に hold 不在検査を通過する race は、この単純な file gateだけでは原子的に閉じない。少なくとも qsub 直前にも再検査して窓を縮めるが、完全な同時投入排他には別の submission claim/lock が必要であり、本 scope 外として明記する。

## 4. `mutation_harness` の停止、復元抑止、ledger

対象は [mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:29)。

### 検査時点

`runner_mode == "dispatch"` の場合だけ、次の各 dispatch の直前と、子 process を完全に停止・回収した直後に検査する。

| phase | pre-check | post-check |
|---|---|---|
| collection | `_collect_expected_nodes` の `_run_tests` 前（`1103-1123`） | collection stdout の解析前 |
| baseline | `_baseline` の `_run_tests` 前（`1453-1475`） | status 導出前 |
| mutation | `_apply_mutation` の source 書換え前（`1514-1540`） | `_run_tests` 後、failed node解析前 |

さらに mutation だけは `finally`（`1602-1604`）で再検査し、これを復元可否の権威にする。既存 hold がある場合、collection/baseline は subprocess を起動せず、mutation は source 書換え前に止まる。

### `_apply_mutation` の finally

具体的には次の二分岐へ変える。

```python
finally:
    hold = _dispatch_orphan_hold_path(repo)
    if runner_mode == "dispatch" and _path_present(hold):
        # _restore_targets は呼ばない
        _assert_only_expected_dirt(repo, head, touched)
        _assert_head(repo, head)
        # touched の bytes が注入した mutated bytes のままか再確認
    else:
        _restore_targets(repo, {rel: originals[rel] for rel in touched})
        _assert_head(repo, head)
```

- hold ありでは `_restore_targets`、`_purge_pycache`、`_verify_originals` を一切呼ばない。
- `_assert_head` は commit identity の検査なので、tracked fileが dirtyでも成立する。
- `_assert_only_expected_dirt` は `touched` 以外の tracked dirtを拒否する。`output/pegasus-dispatch/` は `.gitignore:26` で除外される。
- `_defer_cleanup_signals`（`892-922`）は復元を行う分岐だけで従来どおり使う。hold 分岐へ入ってから signal を理由に復元しない。

### 構造化停止 ledger

通常の `LEDGER_SCHEMA = izanagi-dev-wave-mutation/v4` は変えない。正常・通常の失敗 ledger と fan-out exact consumer を壊さないため、hold 時だけ `--out` に専用の非終端停止 ledger を書く。

```json
{
  "schema": "izanagi-dev-wave-mutation-orphan-stop/v1",
  "updated_at": "<UTC ISO-8601 string>",
  "repo_head": "<full object id>",
  "spec_sha256": "<64 hex>",
  "reason": {
    "code": "orphan-hold",
    "phase": "collection | baseline | mutation",
    "mutation_id": null,
    "hold_path": "<absolute path>",
    "source_state": "unchanged | mutation-left-in-place",
    "dirty_paths": [],
    "recovery": "<string>"
  },
  "partial_ledger": null,
  "active_record": null
}
```

型は次のとおり。

- `reason.code`: exact `"orphan-hold"`
- `reason.phase`: `str` enum
- `reason.mutation_id`: mutation phaseだけ `str`、他は `null`
- `reason.hold_path`: `str`
- `reason.source_state`: collection/baseline は `"unchanged"`、mutation は `"mutation-left-in-place"`
- `reason.dirty_paths`: `list[str]`。mutation の `touched` をソートして格納
- `reason.recovery`: `str`。`qstat` 終端確認 → `git checkout -- <dirty_paths>` → clean/HEAD確認 → hold手動削除、の順
- `partial_ledger`: 既に collection/baseline/完了 mutation があればその時点の通常 ledger、collection 中なら `null`
- `active_record`: 現在の runner resultを構造化できた場合の record、起動前 holdなら `null`

書込みは `_write_ledger` / `_write_json_atomic`（`mutation_harness.py:2062-2087`）を再利用する。この schema は terminal ledger ではなく、fan-out mergeへ渡さない。

### 終了コードと進行停止

`main`（`2159-2398`）で専用 `OrphanHoldStop` を捕捉し、停止 ledgerを atomic writeして stderrへ同じ `reason` を表示し、`2` を返す。

- mutation loopは即座に抜け、次の mutationを呼ばない。
- stderrには `mutation-left-in-place`、dirty path、hold path、復旧順序を必ず出す。
- 通常の signal は従来どおり `128 + signum` を保つ。
- signal unwind中に hold が見つかった場合は `SignalAbort` に `restore_skipped=True` と hold pathを運び、停止 ledgerを書いた後に signalを再送出する。`__main__` の既存 `"active mutation restore attempted"` は holdなしの場合だけ維持し、hold時は「復元を意図的に見送り、変異を残した」と出す。

専用停止 ledgerの自動 resume、holdの自動解除、古い停止 ledgerの削除は本 waveに含めない。mutation worktreeの handoffも、hold時は直ちに `--resume` する案内ではなく、まず上記の人手復旧を要求する。

## 5. `mutation_worktree` の teardown 遮断

対象は [mutation_worktree.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:612)。

### 検査 path

検査対象は次である。

```text
_dispatch_root(preflight) / "orphan-hold.json"
= <container>/repo/output/pegasus-dispatch/orphan-hold.json
```

`_should_teardown` が呼ばれる `mutation_worktree.py:1131-1135` の時点では、fresh runの evidence はまだ container 内にあり、resume時も `1107-1110` で退避先から containerへ再実体化済みである。退避後の `<ledger>.dispatch-evidence/orphan-hold.json` を見るのではない。

hold があると `_teardown` 自体を呼ばないので、`_stash_dispatch_evidence`（`637-653`）も `rmtree`（`905`, `919`）も起動しない。

### signature

`mutation_worktree.py:932-933` を次へ変える。

```python
def _should_teardown(
    *,
    plan_only: bool,
    child_rc: int | None,
    terminal: bool,
    orphan_hold: bool,
) -> bool:
    return not orphan_hold and (
        plan_only or (child_rc in {0, 1} and terminal)
    )
```

呼出し元 `1131-1135` で、child終了後かつ `_teardown` 前に計算した strict bool を渡す。holdありは plan-only、child rc 0/1、terminal ledgerの組合せでも常に `False`。

### wrapper receipt

wrapper schemaは変えず、既存 fieldを次の値にする。

| field | hold時の値 |
|---|---|
| `failure` | exact `"orphan-hold"` |
| `container_preserved` | `true` |
| `teardown_attempted` | `false` |
| `teardown_completed` | `false` |
| `dispatch_evidence.relocated` | `false` |
| `terminal_ledger` | 通常 `false`。実際の検査結果を改ざんしない |
| `child_rc` | harnessの実値。通常 `2` |

holdがあるのに childが誤って `0/1` を返した場合は wrapper failureとして rc=125へ倒す。実際の `child_rc` 自体は receipt内で保持する。

holdなしの正例は現状どおりである。plan-only、または `child_rc in {0,1} and terminal=True` なら evidence退避後に container/admin dirを teardownする。

## 6. 新規テストと既存期待値

### `orchestrator/tests/test_pegasus_dispatch_compute.py`

- `test_orphan_hold_signature_classifies_every_gate_reason`
  - 上表の13 reasonを1件も省かず固定。
  - `fresh-cancellable-snapshot` は qdel成功/失敗の両方を固定。
  - `request_present=False` と terminal-historyの優先を固定。

- `test_qdel_receipt_latches_orphan_hold_only_without_absence_or_terminal_evidence`
  - gate見送り/qdel失敗から exact schemaの holdが立つ。
  - `request-absent` と `terminal-history-conflict` では立たない。
  - 検出力 (a)。

- `test_orphan_hold_record_is_create_only`
  - 2回目の原因で bytesが変わらない。
  - malformedな既存 entryも上書きしない。

- `test_existing_orphan_hold_blocks_before_any_scheduler_command`
  - rc=16、scheduler command `[]`、nonce directoryなし。
  - 検出力 (b)。

- `test_f47_latch_precedes_orphan_hold_when_both_exist`
  - 最初は既存F47文言、F47だけ除去後もholdでqsub 0回。

### `orchestrator/tests/test_mutation_harness.py`

- `test_dispatch_orphan_hold_during_collection_writes_stop_ledger_before_baseline`
- `test_dispatch_orphan_hold_during_baseline_writes_stop_ledger_before_mutation`
- `test_dispatch_orphan_hold_after_mutation_skips_restore_and_stops_next_mutation`
  - 2変異を登録し、1個目dispatch後にholdを作る。
  - 1個目の注入bytesが残り、2個目runnerが0回。
  - `reason.code == "orphan-hold"`、`phase == "mutation"`、
    `source_state == "mutation-left-in-place"`、dirty path、process rc=2を固定。
  - 検出力 (c)。

- `test_signal_with_orphan_hold_reports_restore_skipped_and_preserves_mutation`
  - holdなしの既存 signal復元契約を変えず、holdありだけ復元しない。

### `orchestrator/tests/test_mutation_worktree.py`

- `test_orphan_hold_blocks_teardown_even_for_terminal_child`
  - child rc=0かつ terminal ledgerでも `_teardown` を呼ばず container/holdを保全。
  - 検出力 (d)。

- `test_orphan_hold_preservation_is_recorded_in_wrapper_receipt`
  - 上記 receipt fieldを固定し、stderrにhold pathと復旧順序があることを確認。

- `test_should_teardown_positive_paths_without_hold`
  - holdなしの plan-only と terminal rc 0/1 が従来どおり `True`。

### 既存期待値

変更不要と判断する。

特に以下はそのまま通すべきである。

- `test_best_effort_qdel_production_caller_is_only_fresh_gate`
- `test_m6_qstat_success_without_request_skips_qdel_and_create_only_latches`
- `test_missing_compute_marker_latches_only_after_visible_job_terminates`
- `test_normal_run_uses_cumulative_replacements_and_full_failed_line`
- `test_signal_arriving_during_restore_is_deferred_until_all_targets_verified`
- `test_dispatch_evidence_is_relocated_before_delete_between_observation_points`

通常の mutation ledger v4、wrapper receipt v1、dispatch receipt v2を変えない設計なので、既存 fixtureの schema期待値変更も不要である。

テストは親が `tools/run_tests.py` 経由で実測する。本段では実走しておらず、緑とは報告しない。

## 7. docs・consumer・`output/` への静的波及

| 対象 | 静的結論 |
|---|---|
| `tools/check_docs.py:2107-2345` | 検査対象は `TASKS[*].child_script` と runbook §7.0 の exact task表。`TASKS` を変えないため inventory変更不要。 |
| `docs/pegasus-runbook.md:1081-1096` | 更新が必要。mutation dispatchのhold検査、sourceを残す理由、停止 ledger、復旧順序を追記する。 |
| `docs/pegasus-runbook.md:1239-1242` | 更新が必要。qdel gate見送り時は新規qdelを足さずholdで止め、自動解除しないことを追記する。docs編集は段7の親担当。 |
| `tools/mutation_harness.py:1266-1279` | `_dispatch_submission_inventory` はroot直下のdirectoryだけを数える。`orphan-hold.json` はfileなので候補数へ混入しない。 |
| `tools/mutation_fanout.py:966-1060` | orphan evidence scannerはsubmission directoryと `receipt-fallback-*` だけを見る。hold fileはreceiptと誤認されない。 |
| `tools/mutation_fanout.py:1692-1730` | wrapper rc非終端ならmerge前に停止し、通常は `cancel=False` で既存 requestを観測する。holdを理由とする新規qdel経路は足さない。 |
| `tools/mutation_fanout_contract.py:19-23,76-80,805-1050` | 通常 ledger v4とwrapper v1は不変。専用停止 ledgerはmerge対象外なので変更不要。誤って渡せばschema gateでfail-closedに拒否される。 |
| `tools/check_acceptance_reds.py:189-279,288-380` | 成功receiptだけを読むためschema変更不要。既存holdならdispatcherがreceipt公告前にrc=16となり安全に拒否される。 |
| `tools/check_acceptance_reds.py:383-407` | 成功run中に並行してholdが現れた場合、root `rmdir` が失敗してInvalidInputになる。holdを削除しない点で正しい。 |
| `.gitignore:26` | `output/pegasus-dispatch/` 全体がignore済み。git dirt検査には出ない。 |
| `mutation_worktree._stash_dispatch_evidence:637-653` | holdなしの完走だけroot全体をrenameする。hold時は呼ばないのでholdと変異sourceはcontainer内に残る。 |

`output/` 全体を走査する受入との並走は既に runbook `1136-1147` が禁止している。hold fileを例外扱いして検査から隠す変更はしない。

## 総括

- `dispatch_compute.py` で既存 qdel receiptの3 fieldだけから `orphan-hold.json` をcreate-only発行する。
- F47検査の直後、qstat/qsubより前にholdを検査し、両方ある場合はF47を先に表示する。
- `mutation_harness.py` は全dispatch phaseの前後とmutation finallyでholdを見て、変異sourceを復元せず停止 ledgerを残してrc=2にする。
- `mutation_worktree.py` はcontainer内holdを `_should_teardown` へ渡し、evidence退避と両方の `rmtree` を止める。
- 最大の未解決点は、同一dispatch rootで並行 invocationがhold検査を同時通過するTOCTOUであり、完全排他には本scope外のsubmission claim/lockが必要なことである。