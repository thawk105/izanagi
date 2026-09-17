## 所見対応表

**static への移動と追加テストは実装済み・未実走です。既存2テストの lookup 回数 assertion との不整合が残るため、完了・全緑とは申告しません。**

変更前は、不正な runner digest が登録・採番を通過し、完全 verifier で拒否されていました。

| 所見 | 状態 | 対応 |
|---|---|---|
| must-fix 2／h′ | partial | runner の固定 object の shape・main bytes digest 照合を登録前 static へ移動 |
| locked 側の検査 | partial | bootstrap の現在 `locked_main` 検査だけを残した。前進 merge runner 検査は従来の lock 内呼出しを維持 |
| 登録前の permanent 拒否 | partial | 既存の rc23／reason／`release_safe=True`／`retryable_same_request=False` 変換を維持 |
| child-green の受理集合 | partial | tip と main の runner 一致は要求せず、main digest を照合。実走未確認 |
| 既存 A 群の全緑 | **未了** | 下記2本の lookup 列 assertion が移動後の呼出し数と衝突 |
| M11 射程拡張 | partial | runner digest だけを変える parameter を追加。変異未実走 |
| exact 表 | closed | 全20置換の一致数1・置換後構文を確認 |

現物には以下の固定 assertion が残っています。

- `test_land_accepts_child_green_tip_runner_change_with_main_digest`：`lookups == [tip, repo.base]`
- `test_d987_rejects_final_runner_change_before_provenance_rc16`：`lookups == [locked_main, tested_main]`

今回の移動により、どちらも登録前の `[tested_tip, tested_main]` が追加されます。これは静的に確認した不整合で、pytest の失敗実測ではありません。既存期待値は変更せず、検査を省略する修正も行っていません。

## 変更の要約 (関数・行)

以下、L＝[tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/tools/dev_wave_land.py)、T＝[orchestrator/tests/test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/orchestrator/tests/test_dev_wave_land.py)。

| 箇所 | 変更 |
|---|---|
| L:970 `_verify_acceptance_static`、追加位置1081 | tested-tip／tested-main の runner entry、blob shape、main 実行 bytes digest を照合 |
| L:1192 `_verify_acceptance_locked_authority` | runner 検査を移出。不要になった raw／tested SHA 引数を削除 |
| L:1203 `_verify_acceptance_receipt` | locked helper の引数を更新。static と locked の両検証を維持 |
| T:3805 登録前拒否テスト | digest 改変 parameter、拒否分類の assertion を追加 |
| T:3847 `_plain_cases` | 両 parameter を登録 |

launcher・waiter の既存 static 検査、登録時 raw digest 束縛、完全再検証は維持しています。

所有外の `acceptance_shards.py`、`check_docs.py`、`dev_wave_wait.py`、`test_run_tests_shards.py`、共有 fixture、docs は編集していません。外向け CLI・結果 JSON の変更もありません。consumer 側の実走確認は未了です。

## 追加 test

`T::test_land_turn_rejects_invalid_acceptance_before_registration[runner_executed_sha256]`

有効 receipt の runner digest の先頭1桁だけを別の16進数字へ変更し、64桁を維持します。確認内容は次のとおりです。

- rc23／`rejected`／`acceptance-receipt-rejected`
- `release_safe=True`、`retryable_same_request=False`
- registry directory 不在による ticket 未作成・seq 未消費
- initial lock 未取得・provenance 未起動
- main 不変

既存 `child_rc` ケースと assertion は維持し、拒否分類の確認を追加しました。

## 変異 exact 登録表 (id / file / old / new / 期待 node)

`old`／`new` は JSON文字列です。decode 後に逐語置換してください。全20件で一致数1・置換後構文OK。**KILLED／SURVIVED は期待値で、実測ではありません。**

全対象 file は L。期待 node は `T::` を補ってください。M11 の逐語は不変、位置は L:5612 です。

| id | file・行 | old | new | 期待 node／結果 |
|---|---|---|---|---|
| M0 | L:2622 | `"def _land_lock_now() -> float:\n    return time.monotonic()"` | `"def _land_lock_now() -> float:\n    # Equivalent comment-only control.\n    return time.monotonic()"` | `test_land_turn_eight_requests_complete_in_sequence`／SURVIVED |
| M1 | L:5635 | `"        granted, waited, ahead = _wait_land_turn(repository, lock)"` | `"        granted, waited, ahead = True, 0.0, 0"` | `test_land_turn_eight_requests_complete_in_sequence`／KILLED |
| M2 | L:2917 | `"                turn.seq = entry[\"seq\"]"` | `"                turn.seq = registry[\"next_seq\"]\n                registry[\"next_seq\"] += 1"` | `test_land_turn_retry_preserves_sequence`／KILLED |
| M3 | L:2800 | `"        except BlockingIOError:\n            return True\n        return False"` | `"        except BlockingIOError:\n            return time.time() - os.fstat(fd).st_mtime < _LAND_TURN_WAIT_SECONDS\n        return False"` | `test_land_turn_live_owner_is_not_expired`／KILLED |
| M4a | L:6254 | `"            _land_turn_mutating(\n                repository, plan=plan, main_before=locked_main, landing_tip=landing_tip,"` | `"            None if True else _land_turn_mutating(\n                repository, plan=plan, main_before=locked_main, landing_tip=landing_tip,"` | `test_land_turn_mutation_rechecks_owner[ff]`／KILLED |
| M4b | L:5165 | `"        _land_turn_mutating(\n            repository, plan=plan, main_before=rollback_ref, landing_tip=tested_tip,"` | `"        None if True else _land_turn_mutating(\n            repository, plan=plan, main_before=rollback_ref, landing_tip=landing_tip,"` | 下記訂正参照 |
| M4c1 | L:5349 | `"        if phase == \"applied\":\n            before_mutation()\n            plan = fold.mark_fold_committed("` | `"        if phase == \"applied\":\n            plan = fold.mark_fold_committed("` | `test_land_turn_mutation_rechecks_owner[shape-b-mark-ticket]`／KILLED |
| M4c2 | L:5378 | `"    try:\n        before_mutation()\n        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)"` | `"    try:\n        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)"` | `test_land_turn_mutation_rechecks_owner[shape-b]`／KILLED |
| M5a | L:2862 | `"        if record[\"phase\"] == \"mutating\":\n            recovery.append(key)"` | `"        if record[\"phase\"] == \"mutating\":\n            del registry[\"requests\"][key]\n            continue"` | `test_land_turn_recovery_precedes_successor`／KILLED |
| M5b | L:3024 | `"    state = repository.common / _FOLD_STATE_NAME\n    if os.path.lexists(state):"` | `"    with _turn_registry(repository, turn) as registry:\n        registry[\"requests\"].pop(key, None)\n        if registry[\"grant\"] == key:\n            registry[\"grant\"] = None\n        _turn_select(turn, registry)\n    return\n    state = repository.common / _FOLD_STATE_NAME\n    if os.path.lexists(state):"` | `test_land_turn_recovery_precedes_successor`／KILLED |
| M6a | L:4673 | `"    acquired, waited = _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)"` | `"    acquired, waited = (\n        _acquire_land_lock(repository, lock, _land_lock_now() + max(0.0, remaining_wait_s))\n        if isinstance(payload, _ProvenanceReceipt)\n        else _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)\n    )"` | `test_land_turn_preserves_evidence_after_lock_budget[provenance]`／KILLED |
| M6b | L:4673 | `"    acquired, waited = _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)"` | `"    acquired, waited = (\n        _acquire_land_lock(repository, lock, _land_lock_now() + max(0.0, remaining_wait_s))\n        if not isinstance(payload, _ProvenanceReceipt)\n        else _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)\n    )"` | `test_land_turn_preserves_evidence_after_lock_budget[fold]`／KILLED |
| M7a | L:5742 | `"                if refreshed_fingerprint != initial_fingerprint:"` | `"                if False and refreshed_fingerprint != initial_fingerprint:"` | `test_land_turn_invalidates_changed_inputs[main]`／SURVIVED |
| M7b | L:6026 | `"                    if refreshed_fingerprint != initial_gate_fingerprint:"` | `"                    if False and refreshed_fingerprint != initial_gate_fingerprint:"` | `test_land_turn_preserves_evidence_after_lock_budget[fold]`／SURVIVED |
| M8 | L:1729 | `"                if not protected:\n                    continue"` | `"                if not protected:\n                    pass"` | `test_land_ignores_unrelated_child_cleanup_race`／KILLED |
| M9 | L:3220 | `"        if not _same_inode(os.fstat(repository.wave_fd), os.fstat(wave_fd)):"` | `"        if False and not _same_inode(os.fstat(repository.wave_fd), os.fstat(wave_fd)):"` | `test_land_turn_mutation_rechecks_owner[ff-wave]`／KILLED |
| M10 | U2所有 | — | — | 対象外 |
| M11 | L:5612 | `"        except _Reject as exc:\n            raise _Reject(\n                exc.rc, exc.reason,\n                release_safe=not exc.retryable_same_request,\n                retryable_same_request=exc.retryable_same_request,\n            ) from exc"` | `"        except _Reject:\n            registered_verification = _AcceptanceVerification(\n                hashlib.sha256(_read_acceptance_receipt(request.acceptance_receipt)).hexdigest(),\n                \"child-green\", (), (),\n            )"` | `test_land_turn_rejects_invalid_acceptance_before_registration[runner_executed_sha256]`／KILLED |
| M12 | L:3014 | `"        _turn_select(turn, registry)  # Release and handoff are one registry update."` | `"        _turn_save_registry(turn, registry)\n        _turn_select(turn, registry)"` | `test_land_turn_red_head_hands_over_atomically[timeout]`／KILLED |
| M13 | L:4671 | `"    if isinstance(payload, _ProvenanceReceipt) and payload.returncode != 0:"` | `"    if False and isinstance(payload, _ProvenanceReceipt) and payload.returncode != 0:"` | `test_land_turn_red_provenance_fails_fast`／KILLED |
| M14 | L:3009 | `"            entry[\"order\"] = registry[\"next_seq\"] - 1"` | `"            pass  # M14: retain pre-grant scheduling order."` | `test_land_turn_stale_head_rotates_behind_waiters`／KILLED |

M4b の正しい `new` は次です。期待 node は `test_land_turn_mutation_rechecks_owner[fold]`／KILLED。検査した逐語もこちらです。

```json
"        None if True else _land_turn_mutating(\n            repository, plan=plan, main_before=rollback_ref, landing_tip=tested_tip,"
```

## 実走結果

次の範囲を `tools/run_tests.py` 経由で試行しました。

```text
orchestrator/tests/test_dev_wave_land.py
orchestrator/tests/test_plain_runner_coverage.py
orchestrator/tests/test_pytest_collection_config.py
orchestrator/tests/test_flaky_test_holds_contract.py
-q
```

**runner rc16、`qstat -Q preflight rc=1`、`child_started=false`。pytest は未起動です。**

成功した検査：

- 編集2ファイルの Python 構文解析
- exact 変異20件の一致数1・置換後構文解析
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`（違反なし）
- `git diff --check`

変異の実走は未実施です。

## 総括

指定2ファイルに static 検査への移動と digest 改変テストを実装しました。commit・報告ファイルは作成していません。

**実装済み・未実走。既存2テストの lookup 列 assertion と新しい登録前検証の不整合が残っており、A 群の全緑を満たした修正としては未完了です。**
