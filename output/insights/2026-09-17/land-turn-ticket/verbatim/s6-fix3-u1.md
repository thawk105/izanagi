## 所見対応表 (closed / partial / regressed)

**指定2ファイルに実装済みです。pytestはdispatch障害で起動できず、実走を要する項目はpartialとします。**

| 所見 | 状態 | 対応 |
|---|---|---|
| R2 | partial | registry lock内で最新の完全recordを再読。観測recordと異なれば追記せず選出結果を採用。二者回収テスト追加 |
| R3 | partial | ticket作成前に空registryを原子的に永続化。rename直前の実process死亡テスト追加 |
| R4 | partial | gate後のreceipt拒否についてrc・retryable分類を伝播。その他の例外・割込み分類は維持 |
| N1 | partial | 同keyの完了観測を`done`・seq削除・`already-landed`で終端 |
| R1再確認 | partial | rc16／-9／-15のretryable分類を静的確認。既存テストにseq保持確認を追加。違反rcではseq削除も確認 |
| B1 | partial | 両8本テストにgrant順、独立waveテストに終了順のassertion追加 |
| B2 | partial | `applied`再入のmark前にticket差替え／FD喪失を注入。既存finalize前parameter維持 |
| B3 | partial | 元key・seq、後続の通常grant不取得、復旧planのorigin・transaction・採番・FOLDEDを確認 |
| B4 | closed | 静的再照準完了。指定候補では固有検出入力なし。M7はSURVIVED期待、実測未 |
| B5 | partial | `Popen`のownerをSIGKILLし、FD解放→後続grant→landを確認する別node追加 |
| 残1件 | partial | missing／leafのrc29維持。ancestorだけrc23期待へ変更し、直接bindingテスト追加 |
| 焦点走の赤 | partial | `focus-u1-land-2.log`の赤は上記1件のみ。修正済み・再実走未 |
| B6 | partial | 下記19件のexact置換を登録可能な形で提示。KILLED／SURVIVED実測は未了 |

新たなregressedの実測はありません。review Bのscheduler交代点・時刻表示・復旧待ちメトリクスに関するnitは変更していません。

## 変更の要約 (関数・行)

以下、`L`＝[tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/tools/dev_wave_land.py)、`T`＝[orchestrator/tests/test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/land-turn-ticket-u1/orchestrator/tests/test_dev_wave_land.py)です。

| 箇所 | 変更 |
|---|---|
| L:317 `_LandTurnHandle` | 完了観測時のmain SHAを保持 |
| L:2736 `_turn_registry` | registry不在時、ticket作成前に既存のfsync・rename・directory fsync経路で空registryを保存 |
| L:3014 `_observe_dead_land_turn` | digest検証済み最新recordを全体比較。二重追記防止と自己完了終端 |
| L:3098 `_wait_land_turn` | 自己完了を通常grant待ちへ戻さず返す |
| L:5632 `land` | 完了観測をmain不変の`already-landed`として返す |
| L:6107 `land` | receipt再検証の`_Reject`をfold gateの汎用例外変換から分離 |

壊れた既存registryの初期化は許していません。commit・docs編集は行っていません。所有外callerの`acceptance_shards.py`、`check_docs.py`、`dev_wave_wait.py`、`test_run_tests_shards.py`は未変更で、consumer実走は残っています。

## 追加・変更した test と理由

nodeidの`T::`は上記テストファイルへ展開してください。**すべて今回の実走結果は未取得です。**

| nodeid | 行 | 理由 |
|---|---:|---|
| `T::test_land_turn_dead_mutating_two_observers_do_not_duplicate_records` | 3942 | B・Cが同じ死亡recordを観測してから順に回収し、追記1回・番号連続を確認 |
| `T::test_land_turn_initial_registry_crash_before_rename` | 3734 | 初回rename直前でSIGKILL。journal未作成と次requestの成功を確認 |
| `T::test_land_turn_post_gate_receipt_io_retains_sequence` | 4022 | 実gate後にreceiptを退避し、rc23・retryable・seq保持を確認 |
| `T::test_land_turn_completed_same_key_reentry_is_done[ff-done]` | 3986 | ff完了後死亡の自己再入を終端 |
| `T::test_land_turn_completed_same_key_reentry_is_done[finalized]` | 3986 | finalize後死亡の自己再入を終端 |
| `T::test_land_turn_independent_waves_one_lands_rest_stale` | 4474 | grant順・終了順をseq順に固定 |
| `T::test_land_turn_eight_requests_complete_in_sequence` | 4492 | grant順を追加確認 |
| `T::test_land_turn_mutation_rechecks_owner[shape-b-mark-ticket]` | 4125 | `applied`再入のmark前ticket差替え |
| `T::test_land_turn_mutation_rechecks_owner[shape-b-mark-fd]` | 4125 | 同境界のFD喪失 |
| `T::test_land_turn_mutation_rechecks_owner[shape-b]` | 4125 | 既存finalize前確認を維持 |
| `T::test_land_turn_mutation_rechecks_owner[ff-wave]` | 4125 | M9用にmutation直前の自wave差替えを追加 |
| `T::test_land_turn_recovery_precedes_successor` | 4048 | 元票・grant・復旧対象・採番を直接観測 |
| `T::test_land_turn_subprocess_death_releases_successor` | 3711 | thread harnessとは別に実process死亡を確認 |
| `T::test_land_turn_live_owner_is_not_expired` | 3640 | mtimeも古くし、M3のTTL変異を照準 |
| `T::test_provenance_checker_missing_and_symlink_components_are_rejected_clean` | 5649 | missing／leafには有効receipt。ancestorだけrc23・ticket未作成・監査未起動へ変更 |
| `T::test_provenance_checker_binding_rejects_ancestor_symlink_clean` | 5719 | cleanな祖先symlinkを直接bindingしてrc29を確認 |
| `T::test_provenance_checker_violation_rc_is_release_safe_and_releases` | 9677 | 違反rcでregistryのseq削除を追加確認 |
| `T::test_provenance_checker_infrastructure_rc_is_retryable_and_retains` | 9740 | rc16で元seq保持を追加確認 |
| `T::test_provenance_checker_signal_returncode_is_retryable_and_retains` | 9746 | -9／-15で元seq保持を追加確認 |

既存結果の期待値変更は、裁定されたancestor-symlink分岐のrc29→rc23だけです。fix-1の時間期待は維持しました。

## M7 の再照準結果

| 候補 | 静的結論 |
|---|---|
| wave HEADが別commitへ動いて戻る | 比較時のSHA・collision集合が同じならfingerprint自体も同値。固有検出にならない |
| ignored ancestorが増える | fingerprintを外しても、後段の`_verify_target_collisions`が同じancestor検査で拒否 |
| mainが動いて同SHAへ戻る | 残存dirt等がなければfingerprint同値。残れば後段検査の対象 |

**M7a／M7bは指定候補に対する受理・拒否の冗長gateとして、SURVIVED期待とします。** rc・reasonまで同一という主張や、全入力についての等価証明ではありません。指示に従い追加テストは作っていません。

## 変異 exact 登録表 (id / file / old / new / 期待 node)

`old`／`new`は**JSON文字列**です。JSON decode後に逐語置換してください。各`old`の一致数1と置換後のPython構文を確認しました。変異は実ファイルへ適用していません。

全行のfileは`L`。M10はU2所有のため除外します。期待nodeは単独実行対象であり、**KILLED実測の申告ではありません**。

| id | file・行 | old | new | 期待node／結果 |
|---|---|---|---|---|
| M0 | L:2628 | `"def _land_lock_now() -> float:\n    return time.monotonic()"` | `"def _land_lock_now() -> float:\n    # Equivalent comment-only control.\n    return time.monotonic()"` | `T::test_land_turn_eight_requests_complete_in_sequence`／SURVIVED |
| M1 | L:5630 | `"        granted, waited, ahead = _wait_land_turn(repository, lock)"` | `"        granted, waited, ahead = True, 0.0, 0"` | `T::test_land_turn_eight_requests_complete_in_sequence`／KILLED期待 |
| M2 | L:2919 | `"                turn.seq = entry[\"seq\"]"` | `"                turn.seq = registry[\"next_seq\"]\n                registry[\"next_seq\"] += 1"` | `T::test_land_turn_retry_preserves_sequence`／KILLED期待 |
| M3 | L:2802 | `"        except BlockingIOError:\n            return True\n        return False"` | `"        except BlockingIOError:\n            return time.time() - os.fstat(fd).st_mtime < _LAND_TURN_WAIT_SECONDS\n        return False"` | `T::test_land_turn_live_owner_is_not_expired`／KILLED期待 |
| M4a | L:6254 | `"            _land_turn_mutating(\n                repository, plan=plan, main_before=locked_main, landing_tip=landing_tip,"` | `"            None if True else _land_turn_mutating(\n                repository, plan=plan, main_before=locked_main, landing_tip=landing_tip,"` | `T::test_land_turn_mutation_rechecks_owner[ff]`／KILLED期待 |
| M4b | L:5160 | `"        _land_turn_mutating(\n            repository, plan=plan, main_before=rollback_ref, landing_tip=tested_tip,"` | `"        None if True else _land_turn_mutating(\n            repository, plan=plan, main_before=rollback_ref, landing_tip=tested_tip,"` | `T::test_land_turn_mutation_rechecks_owner[fold]`／KILLED期待 |
| M4c1 | L:5344 | `"        if phase == \"applied\":\n            before_mutation()\n            plan = fold.mark_fold_committed("` | `"        if phase == \"applied\":\n            plan = fold.mark_fold_committed("` | `T::test_land_turn_mutation_rechecks_owner[shape-b-mark-ticket]`／KILLED期待 |
| M4c2 | L:5373 | `"    try:\n        before_mutation()\n        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)"` | `"    try:\n        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)"` | `T::test_land_turn_mutation_rechecks_owner[shape-b]`／KILLED期待 |
| M5a | L:2864 | `"        if record[\"phase\"] == \"mutating\":\n            recovery.append(key)"` | `"        if record[\"phase\"] == \"mutating\":\n            del registry[\"requests\"][key]\n            continue"` | `T::test_land_turn_recovery_precedes_successor`／KILLED期待 |
| M5b | L:3020 | `"    state = repository.common / _FOLD_STATE_NAME\n    if os.path.lexists(state):"` | `"    with _turn_registry(repository, turn) as registry:\n        registry[\"requests\"].pop(key, None)\n        if registry[\"grant\"] == key:\n            registry[\"grant\"] = None\n        _turn_select(turn, registry)\n    return\n    state = repository.common / _FOLD_STATE_NAME\n    if os.path.lexists(state):"` | `T::test_land_turn_recovery_precedes_successor`／KILLED期待 |
| M6a | L:4668 | `"    acquired, waited = _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)"` | `"    acquired, waited = (\n        _acquire_land_lock(repository, lock, _land_lock_now() + max(0.0, remaining_wait_s))\n        if isinstance(payload, _ProvenanceReceipt)\n        else _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)\n    )"` | `T::test_land_turn_preserves_evidence_after_lock_budget[provenance]`／KILLED期待 |
| M6b | L:4668 | `"    acquired, waited = _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)"` | `"    acquired, waited = (\n        _acquire_land_lock(repository, lock, _land_lock_now() + max(0.0, remaining_wait_s))\n        if not isinstance(payload, _ProvenanceReceipt)\n        else _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)\n    )"` | `T::test_land_turn_preserves_evidence_after_lock_budget[fold]`／KILLED期待 |
| M7a | L:5742 | `"                if refreshed_fingerprint != initial_fingerprint:"` | `"                if False and refreshed_fingerprint != initial_fingerprint:"` | `T::test_land_turn_invalidates_changed_inputs[main]`／SURVIVED期待 |
| M7b | L:6026 | `"                    if refreshed_fingerprint != initial_gate_fingerprint:"` | `"                    if False and refreshed_fingerprint != initial_gate_fingerprint:"` | `T::test_land_turn_preserves_evidence_after_lock_budget[fold]`／SURVIVED期待 |
| M8 | L:1735 | `"                if not protected:\n                    continue"` | `"                if not protected:\n                    pass"` | `T::test_land_ignores_unrelated_child_cleanup_race`／KILLED期待 |
| M9 | L:3215 | `"        if not _same_inode(os.fstat(repository.wave_fd), os.fstat(wave_fd)):"` | `"        if False and not _same_inode(os.fstat(repository.wave_fd), os.fstat(wave_fd)):"` | `T::test_land_turn_mutation_rechecks_owner[ff-wave]`／KILLED期待 |
| M11 | L:5607 | `"        except _Reject as exc:\n            raise _Reject(\n                exc.rc, exc.reason,\n                release_safe=not exc.retryable_same_request,\n                retryable_same_request=exc.retryable_same_request,\n            ) from exc"` | `"        except _Reject:\n            registered_verification = _AcceptanceVerification(\n                hashlib.sha256(_read_acceptance_receipt(request.acceptance_receipt)).hexdigest(),\n                \"child-green\", (), (),\n            )"` | `T::test_land_turn_rejects_invalid_acceptance_before_registration`／KILLED期待 |
| M12 | L:3010 | `"        _turn_select(turn, registry)  # Release and handoff are one registry update."` | `"        _turn_save_registry(turn, registry)\n        _turn_select(turn, registry)"` | `T::test_land_turn_red_head_hands_over_atomically[timeout]`／KILLED期待 |
| M13 | L:4666 | `"    if isinstance(payload, _ProvenanceReceipt) and payload.returncode != 0:"` | `"    if False and isinstance(payload, _ProvenanceReceipt) and payload.returncode != 0:"` | `T::test_land_turn_red_provenance_fails_fast`／KILLED期待 |

M4の呼出し省略は、wrapper内の故障注入も消します。KILLED時には「無傷のままmutationへ進んだ」結果も検出理由になります。M7bの指定nodeはgate到達の対照で、入力変更による固有検出の証拠ではありません。

M11はstatic検証を実行したうえで拒否結果を無視して登録へ進む変異、M12は引渡し前のregistryを先に公開する変異です。

## 実走結果

`tools/run_tests.py`経由で次を試行しました。

- `test_dev_wave_land.py -q`
- 同ファイル＋`test_plain_runner_coverage.py`＋`test_pytest_collection_config.py`＋`test_flaky_test_holds_contract.py -q`

**両方とも`qstat -Q preflight rc=1`、runner rc16、`child_started=false`。pytestは開始されていません。**

成功した検査：

- 最終2ファイルとsubprocess driverの構文解析
- 追加parameterのpytest／plain runner対応確認
- exact変異19件の一意性・置換後構文確認
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 最終`git diff --check`

親の焦点走ログにある`345 passed / 1 failed / 1 skipped`はfix-1時点の結果で、今回の成功数には算入していません。

## 総括

各項目の実装修正・テスト追加・exact変異表を用意しました。**実装済み・pytest未実走です。** 指定2ファイル以外のtracked fileは変更せず、commitも作成していません。全件closed・受入完了とは申告しません。
