## 所見対応表 (closed / partial / regressed)

**指定2ファイルを修正しました。実装済み・pytest 未実走です。**

| 所見 | 状態 | 対応 |
|---|---|---|
| seq と order の分離 | partial | 初回 `order=seq`、再入時は保持、最小 order で選出 |
| grant 消費後の再入による飢餓 | partial | seq 保持の終端で、grant 保持中または mutating 後なら `order=next_seq-1` |
| grant 前の終端 | partial | order 不変を確認する assertion を追加 |
| registry schema | partial | order の存在・int型・正数・`order>=seq` を検査 |
| 既存期待値の維持 | partial | 既存 assertion は変更せず維持。実走確認は未了 |
| exact 変異登録 | closed | M14 を含む20件で一致数1・置換後構文OK |

変更前は stale-main を拒否して seq を保持する一方、同じ seq で再選出するため後続が飢餓になっていました。今回の変更は選出順の分離です。既存の拒否判定、common lock、mutation 前検査、死亡回収の判定は維持しています。

## 変更の要約 (関数・行)

以下、`L`＝[tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/tools/dev_wave_land.py)、`T`＝[orchestrator/tests/test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/orchestrator/tests/test_dev_wave_land.py)。

| 箇所 | 変更 |
|---|---|
| L:2704 `_turn_bytes`、L:2717 `_turn_save_registry` | registry は entry 順を保持して保存。journal・digest の正規化は従来どおり |
| L:2735 `_turn_registry` | order の schema 検査を追加。変更検知にも entry 順を含める |
| L:2860 `_turn_select` | 最小 order を選出。同値なら保存された entry 順 |
| L:2886 `_register_land_turn` | 新規は `order=seq`、同 key 再入は既存 order を保持 |
| L:2982 `_finish_land_turn` | 対象終端で order 更新。等しい order の既存票にも譲るため entry を末尾へ移動。同じ transaction で引渡し |
| L:3106 `_wait_land_turn` | `ahead` を order と同値時の待ち順から算出 |

`order=next_seq-1` は既存票と同値になり得るため、同値の順序も永続化しています。

所有外の `acceptance_shards.py`、`check_docs.py`、`dev_wave_wait.py`、`test_run_tests_shards.py`、共有 fixture、docs は未変更です。外向け CLI・結果 JSON は変更していません。旧 registry の order 欠落は指定どおり拒否します。

## 変更した test と理由

| node／箇所 | 行 | 内容 |
|---|---:|---|
| `test_land_turn_stale_head_rotates_behind_waiters` | T:4551 | 新設。A/B/C 同時到着、B 再入後に D 到着。grant 順 `A→B→C→B→D`、B の seq 不変、order `2→3→3`、結果・main・FD 解放を検査 |
| `test_land_turn_retry_preserves_sequence` | T:3616 | grant 前の B を lock-busy で終端・再入させ、entry と order の保持を追加検査。既存 assertion は維持 |
| `test_land_turn_registry_rejects_invalid_order` | T:3580 | 新設。order 欠落、bool、文字列、0、負数、seq 未満を拒否 |
| `_LandTurnScheduler.run` 内の保存観測 | T:4453 | registry の `(seq, order)` を trace に記録 |

新 scheduler テストは `locked_seconds=20`、`retry_delay=5`。実 flock・実 preflight・実 receipt 検証・実 Git mutation を使う既存 harness に接続しています。

`test_land_turn_independent_waves_one_lands_rest_stale` の grant 順・終了順・seq の期待値は無変更です。

## 変異 exact 登録表 (id / file / old / new / 期待 node)

`old`／`new` は **JSON文字列**です。decode 後に逐語置換してください。全20件で一致数1・置換後構文OK。**KILLED／SURVIVED は期待値で、実測ではありません。**

全行の file は `L`、node は `T::` を接頭辞として補ってください。M10 は U2 所有で対象外です。

| id | file・行 | old | new | 期待 node／結果 |
|---|---|---|---|---|
| M0 | L:2627 | `"def _land_lock_now() -> float:\n    return time.monotonic()"` | `"def _land_lock_now() -> float:\n    # Equivalent comment-only control.\n    return time.monotonic()"` | `test_land_turn_eight_requests_complete_in_sequence`／SURVIVED |
| M1 | L:5640 | `"        granted, waited, ahead = _wait_land_turn(repository, lock)"` | `"        granted, waited, ahead = True, 0.0, 0"` | `test_land_turn_eight_requests_complete_in_sequence`／KILLED |
| M2 | L:2922 | `"                turn.seq = entry[\"seq\"]"` | `"                turn.seq = registry[\"next_seq\"]\n                registry[\"next_seq\"] += 1"` | `test_land_turn_retry_preserves_sequence`／KILLED |
| M3 | L:2805 | `"        except BlockingIOError:\n            return True\n        return False"` | `"        except BlockingIOError:\n            return time.time() - os.fstat(fd).st_mtime < _LAND_TURN_WAIT_SECONDS\n        return False"` | `test_land_turn_live_owner_is_not_expired`／KILLED |
| M4a | L:6259 | `"            _land_turn_mutating(\n                repository, plan=plan, main_before=locked_main, landing_tip=landing_tip,"` | `"            None if True else _land_turn_mutating(\n                repository, plan=plan, main_before=locked_main, landing_tip=landing_tip,"` | `test_land_turn_mutation_rechecks_owner[ff]`／KILLED |
| M4b | L:5170 | `"        _land_turn_mutating(\n            repository, plan=plan, main_before=rollback_ref, landing_tip=tested_tip,"` | `"        None if True else _land_turn_mutating(\n            repository, plan=plan, main_before=rollback_ref, landing_tip=tested_tip,"` | `test_land_turn_mutation_rechecks_owner[fold]`／KILLED |
| M4c1 | L:5354 | `"        if phase == \"applied\":\n            before_mutation()\n            plan = fold.mark_fold_committed("` | `"        if phase == \"applied\":\n            plan = fold.mark_fold_committed("` | `test_land_turn_mutation_rechecks_owner[shape-b-mark-ticket]`／KILLED |
| M4c2 | L:5383 | `"    try:\n        before_mutation()\n        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)"` | `"    try:\n        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)"` | `test_land_turn_mutation_rechecks_owner[shape-b]`／KILLED |
| M5a | L:2867 | `"        if record[\"phase\"] == \"mutating\":\n            recovery.append(key)"` | `"        if record[\"phase\"] == \"mutating\":\n            del registry[\"requests\"][key]\n            continue"` | `test_land_turn_recovery_precedes_successor`／KILLED |
| M5b | L:3029 | `"    state = repository.common / _FOLD_STATE_NAME\n    if os.path.lexists(state):"` | `"    with _turn_registry(repository, turn) as registry:\n        registry[\"requests\"].pop(key, None)\n        if registry[\"grant\"] == key:\n            registry[\"grant\"] = None\n        _turn_select(turn, registry)\n    return\n    state = repository.common / _FOLD_STATE_NAME\n    if os.path.lexists(state):"` | `test_land_turn_recovery_precedes_successor`／KILLED |
| M6a | L:4678 | `"    acquired, waited = _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)"` | `"    acquired, waited = (\n        _acquire_land_lock(repository, lock, _land_lock_now() + max(0.0, remaining_wait_s))\n        if isinstance(payload, _ProvenanceReceipt)\n        else _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)\n    )"` | `test_land_turn_preserves_evidence_after_lock_budget[provenance]`／KILLED |
| M6b | L:4678 | `"    acquired, waited = _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)"` | `"    acquired, waited = (\n        _acquire_land_lock(repository, lock, _land_lock_now() + max(0.0, remaining_wait_s))\n        if not isinstance(payload, _ProvenanceReceipt)\n        else _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)\n    )"` | `test_land_turn_preserves_evidence_after_lock_budget[fold]`／KILLED |
| M7a | L:5747 | `"                if refreshed_fingerprint != initial_fingerprint:"` | `"                if False and refreshed_fingerprint != initial_fingerprint:"` | `test_land_turn_invalidates_changed_inputs[main]`／SURVIVED |
| M7b | L:6031 | `"                    if refreshed_fingerprint != initial_gate_fingerprint:"` | `"                    if False and refreshed_fingerprint != initial_gate_fingerprint:"` | `test_land_turn_preserves_evidence_after_lock_budget[fold]`／SURVIVED |
| M8 | L:1734 | `"                if not protected:\n                    continue"` | `"                if not protected:\n                    pass"` | `test_land_ignores_unrelated_child_cleanup_race`／KILLED |
| M9 | L:3225 | `"        if not _same_inode(os.fstat(repository.wave_fd), os.fstat(wave_fd)):"` | `"        if False and not _same_inode(os.fstat(repository.wave_fd), os.fstat(wave_fd)):"` | `test_land_turn_mutation_rechecks_owner[ff-wave]`／KILLED |
| M10 | U2所有 | — | — | 対象外 |
| M11 | L:5617 | `"        except _Reject as exc:\n            raise _Reject(\n                exc.rc, exc.reason,\n                release_safe=not exc.retryable_same_request,\n                retryable_same_request=exc.retryable_same_request,\n            ) from exc"` | `"        except _Reject:\n            registered_verification = _AcceptanceVerification(\n                hashlib.sha256(_read_acceptance_receipt(request.acceptance_receipt)).hexdigest(),\n                \"child-green\", (), (),\n            )"` | `test_land_turn_rejects_invalid_acceptance_before_registration`／KILLED |
| M12 | L:3019 | `"        _turn_select(turn, registry)  # Release and handoff are one registry update."` | `"        _turn_save_registry(turn, registry)\n        _turn_select(turn, registry)"` | `test_land_turn_red_head_hands_over_atomically[timeout]`／KILLED |
| M13 | L:4676 | `"    if isinstance(payload, _ProvenanceReceipt) and payload.returncode != 0:"` | `"    if False and isinstance(payload, _ProvenanceReceipt) and payload.returncode != 0:"` | `test_land_turn_red_provenance_fails_fast`／KILLED |
| M14 | L:3014 | `"            entry[\"order\"] = registry[\"next_seq\"] - 1"` | `"            pass  # M14: retain pre-grant scheduling order."` | `test_land_turn_stale_head_rotates_behind_waiters`／KILLED |

M2／M12 の逐語は変更不要で、行番号を更新しました。M7a／b は継承契約の SURVIVED 対照を維持しています。

## 実走結果

次の範囲を `tools/run_tests.py` 経由で2回試行しました。2回目は最終編集後です。

```text
orchestrator/tests/test_dev_wave_land.py
orchestrator/tests/test_plain_runner_coverage.py
orchestrator/tests/test_pytest_collection_config.py
orchestrator/tests/test_flaky_test_holds_contract.py
-q
```

**両方とも runner rc16、`qstat -Q preflight rc=1`、`child_started=false`。pytest は起動していません。** queue 状態も観測不能でした。

成功した検査：

- 変更2ファイルの Python 構文解析
- exact 変異20件の一致数1・置換後構文解析
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`（違反なし）
- `git diff --check`

変更後の storm-e probe と変異実走は未実施です。

## 総括

order 分離、grant 消費後の順番更新、回帰テスト、M14 を含む exact 表を実装・更新しました。**実装済み・pytest 未実走**です。指定2ファイル以外の tracked file は編集せず、commit は作成していません。
