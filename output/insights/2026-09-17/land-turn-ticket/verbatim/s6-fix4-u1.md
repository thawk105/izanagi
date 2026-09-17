## 所見対応表 (closed / partial / regressed)

**指定2ファイルを修正しました。pytest は dispatch 障害で起動できず、実装済み・未実走です。**

| 所見 | 状態 | 対応 |
|---|---|---|
| fix-3 の D16 退行4件 | partial | 完了観測からの早期成功 return を削除。既存 preflight・postcondition 経路へ戻した。既存4テストは無変更 |
| 同 key 再入の完了処理 | partial | ticket の `done`・seq 削除・grant 引渡しを維持。通常 grant を再要求せず既存判定へ進む |
| 読取り poll の不要保存 | partial | yield 前後の `_turn_bytes` が異なる場合だけ保存。回帰テスト追加 |
| exact 変異表 | closed | 19件すべて現物との一致数1・置換後構文OK。変異実走は未実施 |

今回の変更後に新たな退行を実測した結果はありません。未実走のため、退行解消も実測済みとは申告しません。

## 変更の要約 (関数・行)

以下、`L`＝[tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/tools/dev_wave_land.py)、`T`＝[orchestrator/tests/test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/orchestrator/tests/test_dev_wave_land.py)。

| 箇所 | 変更 |
|---|---|
| L:305 `_LandTurnHandle` | 早期成功専用の `completed_main` を削除 |
| L:2735 `_turn_registry`、比較箇所2782 | yield 前後の正規化 bytes を比較し、変更時だけ保存。初回の空 registry 永続化、lock、binding 検査は維持 |
| L:3015 `_observe_dead_land_turn` | 不要になった `completed_main` 代入を削除。ticket 完了処理は維持 |
| L:5532 `land`、修正箇所5632 | `completed land turn verified by observation` の早期 return を削除。既存 `_locked_preflight` 以降へ接続 |

所有外 caller（`acceptance_shards.py`、`check_docs.py`、`dev_wave_wait.py`、`test_run_tests_shards.py`）、共有 fixture、docs は変更していません。commit も作成していません。

## 変更した test と理由

| nodeid（`T::`省略） | 行 | 変更・理由 |
|---|---:|---|
| `test_land_turn_completed_same_key_reentry_is_done[ff-done]` | 4006 | ticket 完了と結果判定を区別する説明を追加。既存経路の `RC_OK / already-landed` を期待 |
| `test_land_turn_completed_same_key_reentry_is_done[finalized]` | 4006 | 既存 preflight の `RC_STALE_MAIN / stale-main` を期待。finalize 後の main は tested tip の次の fold commit にあるため |
| `test_land_turn_registry_read_preserves_published_inode` | 3560 | 新設。読取り2回で inode・bytes 不変、内容変更時に inode 置換と永続化を確認 |

同 key 再入テストの **ticket が done・seq 削除・main 不変・FD 解放**の assertion は維持しています。期待値変更は指示対象の fix-3 新設テストだけで、既存 D16 テスト4件は変更していません。

## 変異 exact 登録表 (id / file / old / new / 期待 node)

`old`／`new` は **JSON文字列**です。JSON decode 後に逐語置換してください。全19件について一致数1と置換後の Python 構文を再確認しました。変異は実ファイルに適用していません。

全行の file は `L`。期待 node の `T::` は上記テストファイルに展開してください。**KILLED／SURVIVED は期待値であり、実測結果ではありません。**

| id | file・行 | old | new | 期待 node／結果 |
|---|---|---|---|---|
| M0 | L:2627 | `"def _land_lock_now() -> float:\n    return time.monotonic()"` | `"def _land_lock_now() -> float:\n    # Equivalent comment-only control.\n    return time.monotonic()"` | `T::test_land_turn_eight_requests_complete_in_sequence`／SURVIVED |
| M1 | L:5630 | `"        granted, waited, ahead = _wait_land_turn(repository, lock)"` | `"        granted, waited, ahead = True, 0.0, 0"` | `T::test_land_turn_eight_requests_complete_in_sequence`／KILLED |
| M2 | L:2920 | `"                turn.seq = entry[\"seq\"]"` | `"                turn.seq = registry[\"next_seq\"]\n                registry[\"next_seq\"] += 1"` | `T::test_land_turn_retry_preserves_sequence`／KILLED |
| M3 | L:2803 | `"        except BlockingIOError:\n            return True\n        return False"` | `"        except BlockingIOError:\n            return time.time() - os.fstat(fd).st_mtime < _LAND_TURN_WAIT_SECONDS\n        return False"` | `T::test_land_turn_live_owner_is_not_expired`／KILLED |
| M4a | L:6249 | `"            _land_turn_mutating(\n                repository, plan=plan, main_before=locked_main, landing_tip=landing_tip,"` | `"            None if True else _land_turn_mutating(\n                repository, plan=plan, main_before=locked_main, landing_tip=landing_tip,"` | `T::test_land_turn_mutation_rechecks_owner[ff]`／KILLED |
| M4b | L:5160 | `"        _land_turn_mutating(\n            repository, plan=plan, main_before=rollback_ref, landing_tip=tested_tip,"` | `"        None if True else _land_turn_mutating(\n            repository, plan=plan, main_before=rollback_ref, landing_tip=tested_tip,"` | `T::test_land_turn_mutation_rechecks_owner[fold]`／KILLED |
| M4c1 | L:5344 | `"        if phase == \"applied\":\n            before_mutation()\n            plan = fold.mark_fold_committed("` | `"        if phase == \"applied\":\n            plan = fold.mark_fold_committed("` | `T::test_land_turn_mutation_rechecks_owner[shape-b-mark-ticket]`／KILLED |
| M4c2 | L:5373 | `"    try:\n        before_mutation()\n        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)"` | `"    try:\n        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)"` | `T::test_land_turn_mutation_rechecks_owner[shape-b]`／KILLED |
| M5a | L:2865 | `"        if record[\"phase\"] == \"mutating\":\n            recovery.append(key)"` | `"        if record[\"phase\"] == \"mutating\":\n            del registry[\"requests\"][key]\n            continue"` | `T::test_land_turn_recovery_precedes_successor`／KILLED |
| M5b | L:3021 | `"    state = repository.common / _FOLD_STATE_NAME\n    if os.path.lexists(state):"` | `"    with _turn_registry(repository, turn) as registry:\n        registry[\"requests\"].pop(key, None)\n        if registry[\"grant\"] == key:\n            registry[\"grant\"] = None\n        _turn_select(turn, registry)\n    return\n    state = repository.common / _FOLD_STATE_NAME\n    if os.path.lexists(state):"` | `T::test_land_turn_recovery_precedes_successor`／KILLED |
| M6a | L:4668 | `"    acquired, waited = _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)"` | `"    acquired, waited = (\n        _acquire_land_lock(repository, lock, _land_lock_now() + max(0.0, remaining_wait_s))\n        if isinstance(payload, _ProvenanceReceipt)\n        else _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)\n    )"` | `T::test_land_turn_preserves_evidence_after_lock_budget[provenance]`／KILLED |
| M6b | L:4668 | `"    acquired, waited = _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)"` | `"    acquired, waited = (\n        _acquire_land_lock(repository, lock, _land_lock_now() + max(0.0, remaining_wait_s))\n        if not isinstance(payload, _ProvenanceReceipt)\n        else _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)\n    )"` | `T::test_land_turn_preserves_evidence_after_lock_budget[fold]`／KILLED |
| M7a | L:5737 | `"                if refreshed_fingerprint != initial_fingerprint:"` | `"                if False and refreshed_fingerprint != initial_fingerprint:"` | `T::test_land_turn_invalidates_changed_inputs[main]`／SURVIVED |
| M7b | L:6021 | `"                    if refreshed_fingerprint != initial_gate_fingerprint:"` | `"                    if False and refreshed_fingerprint != initial_gate_fingerprint:"` | `T::test_land_turn_preserves_evidence_after_lock_budget[fold]`／SURVIVED |
| M8 | L:1734 | `"                if not protected:\n                    continue"` | `"                if not protected:\n                    pass"` | `T::test_land_ignores_unrelated_child_cleanup_race`／KILLED |
| M9 | L:3215 | `"        if not _same_inode(os.fstat(repository.wave_fd), os.fstat(wave_fd)):"` | `"        if False and not _same_inode(os.fstat(repository.wave_fd), os.fstat(wave_fd)):"` | `T::test_land_turn_mutation_rechecks_owner[ff-wave]`／KILLED |
| M10 | U2所有 | — | — | 継承契約どおり本登録の対象外 |
| M11 | L:5607 | `"        except _Reject as exc:\n            raise _Reject(\n                exc.rc, exc.reason,\n                release_safe=not exc.retryable_same_request,\n                retryable_same_request=exc.retryable_same_request,\n            ) from exc"` | `"        except _Reject:\n            registered_verification = _AcceptanceVerification(\n                hashlib.sha256(_read_acceptance_receipt(request.acceptance_receipt)).hexdigest(),\n                \"child-green\", (), (),\n            )"` | `T::test_land_turn_rejects_invalid_acceptance_before_registration`／KILLED |
| M12 | L:3011 | `"        _turn_select(turn, registry)  # Release and handoff are one registry update."` | `"        _turn_save_registry(turn, registry)\n        _turn_select(turn, registry)"` | `T::test_land_turn_red_head_hands_over_atomically[timeout]`／KILLED |
| M13 | L:4666 | `"    if isinstance(payload, _ProvenanceReceipt) and payload.returncode != 0:"` | `"    if False and isinstance(payload, _ProvenanceReceipt) and payload.returncode != 0:"` | `T::test_land_turn_red_provenance_fails_fast`／KILLED |

M5b／M12 とも逐語は変更不要で、行番号を更新しました。M12 は引渡し前の状態を明示保存するため、今回の「変更時だけ保存」の下でも原子的引渡しを破る変異です。M7a／b は指定どおり SURVIVED 対照を維持します。

## 実走結果

`tools/run_tests.py` 経由で次の2回を試行しました。

- `orchestrator/tests/test_dev_wave_land.py -q`
- 同ファイル＋`test_plain_runner_coverage.py`＋`test_pytest_collection_config.py`＋`test_flaky_test_holds_contract.py -q`

**両方とも `qstat -Q preflight rc=1`、runner rc16、`child_started=false`。pytest は未起動です。** 親ログの `4 failed / 352 passed / 1 skipped` は変更前の結果であり、今回の結果には算入していません。

成功した検査：

- 最終2ファイルの構文解析
- exact 変異19件の一致数1・置換後構文解析
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`（違反なし）
- `git diff --check`

## 総括

早期成功 return の撤去、registry の変更時保存、テスト更新、全 exact 変異表の再確認を完了しました。**実装済み・pytest 未実走**です。指定2ファイル以外の tracked file は編集せず、commit は作成していません。
