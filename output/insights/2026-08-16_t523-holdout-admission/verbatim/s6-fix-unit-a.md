# fix Unit A 報告

## 1. 所見ごとの対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F-A1 | partial | 公開 issuer を削除し、private な durable-consumption receipt 経路だけに限定。Unit B 結線と pytest は未完。 |
| F-A2 | partial | token を `attempt_id` と `permitted_run_once_calls` に束縛し、各 `run_once` で原子的に残数を消費。 |
| F-A3 | partial | `run_once` 冒頭で `gflags` を tuple 化し、同一 snapshot を gate と `_build_cmd` に使用。 |
| F-A4 | partial | `ycsb_rratio` を canonical ASCII uint64 decimal に限定。別名・空白・記号・範囲外を拒否。 |
| F-A5 | partial | `backoff_profile.profile_point` の build 前に保護比率を runtime 拒否。 |
| F-A6 | partial | 再帰的な process-launch 全件 inventory へ反転し、非 CCBench site を明示除外。 |

すべて実装済みですが、pytest が infrastructure rc=16 で collection 前停止したため `closed` とはしていません。`regressed` はありません。

## 2. 変更した file と要点

- [holdout_observation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/holdout_observation.py:2)
  - `issue_holdout_observation_admission` を `__all__` と module attribute から削除。
  - private receipt を一度だけ消費する private issuer を実装。
  - token に `attempt_id`、`permitted_run_once_calls` を追加。
  - `run_once` 許可残数を lock 内で消費し、超過を拒否。
  - Python private import まで封鎖しない限界を module/private hook の docstring に明記。
  - canonical ASCII uint64 decimal 以外の比率を fail-closed に変更。
- [runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/calibrator/runner.py:397)
  - `gflags_snapshot = tuple(gflags)` を冒頭で一度だけ作成。
  - gate と `_build_cmd` の双方に同じ snapshot を使用。
- [backoff_profile.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/backoff_profile.py:140)
  - workload を snapshot 化。
  - build、single-tenant probe、直接 spawn より前に rr20/rr80 を拒否。
- [test_holdout_observation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_holdout_observation.py:1)
  - 公開 issuer 不在、receipt 再利用、attempt binding、許可回数超過を追加。
  - `measure_point(reps=5)` の一式だけを許可する境界を追加。
  - stateful `Sequence`、exact-str、数値別名、空白、記号、uint64 境界を追加。
- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_ccbench_spawn_sites.py:1)
  - `rglob("*.py")` による再帰走査へ変更。
  - executable 変数名に依存せず、92 個の process launch を先に列挙。
  - 非 CCBench launch を site 単位で明示除外。
  - `exe`、attribute、hardcoded path、module alias の nested fixture を追加。
  - 「閉集合」「every throughput」という過剰な test 名・主張を、実際の reviewed inventory の範囲へ縮小。

skip、xfail、期待値反転、テスト削除は行っていません。

## 3. Unit B へ渡す公開 API と呼び出し規約

公開 raw issuer は廃止しました。Unit B が使う橋渡しは、意図的に private API です。

```python
receipt = _new_durable_attempt_consumption_receipt(
    attempt_id=attempt_id,
    permitted_run_once_calls=fixed_protocol["reps"],
)
token = _issue_holdout_observation_admission_from_receipt(
    receipt=receipt,
    verified_freeze_document=verified_freeze,
    freeze_holdout_key=freeze_holdout_key,
)
```

呼び出し規約は次のとおりです。

1. `receipt` 作成は、attempt marker の `_write_exclusive` と attempt ledger append が成功した後だけ行う。
2. `permitted_run_once_calls` は caller 任意値ではなく、検証済み canonical protocol の `reps` と exact 一致させる。
3. 現行 protocol は `reps=5`。実コードでは 1 attempt が 1 回の `measure_point` session を表し、その内部で `run_once` を5回呼ぶため、許可数は5。
4. receipt は issuer 呼び出し時に消費され、再発行には使えない。
5. token は各 `run_once` gate で1回分を消費し、6回目を拒否する。
6. Unit B は `finalize_floor_holdout_admissions` で observation token を先行発行・保存してはならない。`consume_attempt_ticket` 内の durable 消費成功後に、その attempt 専用 token を発行する。
7. `_CellState` には verified freeze と canonical `reps`、またはそれらへ到達できる検証済み state を保持する必要がある。

公開側は引き続き `HoldoutObservationAdmission`、`assert_issued_holdout_observation`、`assert_holdout_observation_admitted` を提供します。Python private import 権限を持つコードによる偽造まで防ぐものではありません。

## 4. 実走したテスト / 実走できなかったもの

以下を `tools/run_tests.py` 経由で投入しました。

- `orchestrator/tests/test_holdout_observation.py`
- `test_run_once_snapshots_stateful_gflags_exactly_once`
- `test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `test_holdout_observation.py` と `test_ccbench_spawn_sites.py` の2 file 結合範囲

すべて collection 前に次で停止しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
runner exit_code=16
```

実走 nodeid は0件です。緑は主張しません。

非 pytest 診断では次を確認しました。

- attempt token の2回許可と3回目拒否。
- `measure_point(reps=5)` 後の6回目拒否。
- 数値別名と uint64 範囲外の拒否。
- stateful gflags の単一 snapshot。
- process inventory 92件の exact 一致。
- nested `exe` / attribute / hardcoded path fixture の検出。
- 5 file の AST parse、`git diff --check`、NFC、結合文字不在。
- `python3 tools/check_codex_agents.py`: 成功。
- `python3 tools/check_docs.py`: 違反なし。

これらの直接診断は pytest 結果には数えていません。

## 5. 事前登録変異の位置・old 逐語・前後層確認

- M1: [holdout_observation.py:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/holdout_observation.py:140)
  - old: `return frozenset(signatures)`
  - 空集合へ変えると `_NEUTRAL_BY_RATIO` も空になり、direct `run_once` の rr80 は snapshot 後に非保護扱いとなります。前層はなく、後層も subprocess spy まで拒否しません。
- M2: [runner.py:418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/calibrator/runner.py:418)
  - old:
    ```python
    assert_holdout_observation_admitted(
        gflags=gflags_snapshot,
        admission=holdout_observation_admission,
    )
    ```
  - direct `run_once` 入力なので前層なし。削除後は tempdir、`_build_cmd`、subprocess まで別 gate がありません。
- M3: [holdout_observation.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/holdout_observation.py:87)
  - old: `_INDIRECT_GFLAGS = frozenset({"flagfile", "fromenv", "tryfromenv"})`
  - `flagfile` を集合から外すと ratio 未指定として subprocess へ到達します。snapshot/type gate と `FLAGS_*` env 除去は argv の `--flagfile` を拒否しません。
- M6: [holdout_observation.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/holdout_observation.py:163)
  - old: `if derived != _NEUTRAL_PROTECTED_SIGNATURES:`
  - H3 追加 fixture は純関数へ直接入力され、この exact 一致検査以外に前後の拒否層はありません。
- M7: [holdout_observation.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/holdout_observation.py:350)
  - old:
    ```python
    _consume_holdout_observation_run_once(
        admission,
        expected_signature=signature,
    )
    ```
  - この最終 identity/use gate を `isinstance` のみに緩和する変異が対象です。caller 構築 token は protected ratio 分類を通り、以後 subprocess 前に別の identity gate はありません。
- P1: [test_holdout_observation.py:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_holdout_observation.py:410)
  - rr5、rr50、rr95 は token 無しで subprocess spy へ到達し、既存3-tupleを維持する正例です。

正式な mutation harness は未実走です。

## 6. 所有外への波及可能性

- 最重要: `s8b_holdout_admission.py` は削除済み公開 issuer を import しているため、Unit B fix 前は import 不成立です。
- `s8b_holdout_admission.py` の `_CellState.observation`、finalize 時発行、`consume_attempt_ticket` の再利用 token 返却は再構成が必要です。
- `s8b_floor_campaign.py` は ticket 消費結果を `measure_point` へ渡す形を維持できますが、返る token の許可数が canonical `protocol["reps"]` と一致する必要があります。
- consumer test:
  - `test_s8b_holdout_admission.py`
  - `test_s8b_floor_campaign.py`
  - `test_s8b_freeze_io.py`
  - `test_s8b_oracle_driver.py`
- runner の共有 caller:
  - `calibrator/sweep.py`
  - `campaign/pipeline.py`
  - `campaign/pegasus_floor_scoping.py`
  - `campaign/between_run_floor.py`
  - `backoff_overthrottle.py`
- 共有 fixture/test:
  - `test_calibrator.py`
  - `test_calibrator_certify.py`
  - `test_campaign.py`
  - `test_between_run_floor.py`
  - `test_plain_runner_coverage.py`
- spawn inventory は `orchestrator/calibrator/**` と `orchestrator/campaign/**` の process launch 追加・移動・件数変更を検出します。ただし既存 site 内の command 意味を完全解析するものとは主張しません。

## 7. 未完・申し送り

- Unit B による private receipt 結線が必須です。
- pytest と mutation harness は Pegasus preflight rc=16 のため未実走です。
- focus review 後の統合受入は親で再走が必要です。
- docs、所有外 file、commit は変更していません。
- 最終差分は指定された所有5 fileだけです。

## 総括

F-A1〜F-A6 のコードと境界テストを所有範囲内へ実装しました。  
公開 issuer は消え、attempt ID と凍結 reps に束縛された回数制 token へ変更しました。  
gflags TOCTOU、数値別名、backoff 公開迂回、再帰 spawn inventory を是正しました。  
Unit B の結線変更が必要で、現時点では統合状態ではありません。  
pytest は rc=16 で未実走のため、全所見を partial として報告します。