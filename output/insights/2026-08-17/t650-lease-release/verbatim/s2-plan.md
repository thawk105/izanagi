## 総括

- 変更面は `tools/dev_wave_land.py` と `orchestrator/tests/test_dev_wave_land.py` に限定し、`tools/wave_land_window.py` は既存 `release()` の呼び出し先として使うだけにする。`brief.md:63-74`
- 終端性は `RC_LOCK_BUSY=11` と `RC_CONTROL_PLANE=21` だけを retryable とする allowlist で実装し、それ以外と未知 rc は terminal に倒す。`tools/dev_wave_land.py:42-55`
- release は `land()` 内ではなく、全結果が確定して lock と repository が閉じた後の `main()` に置く。`tools/dev_wave_land.py:3052-3065,3087-3099`
- `release()` へ渡すのは receipt の holder digest ではなく `--acceptance-wave` の wave slug である。`tools/wave_land_window.py:784-805`
- lease directory は既存の `IZANAGI_WAVE_LEASE_DIR` を採用し、未設定・利用不能・release 例外を JSON に残すが land rc は変えない。`tools/wave_land_window.py:27,786-817,887-893`
- JSON は既存 field を変えず `terminal` と `lease_release` を加える。確認できた consumer はいずれも必要 field だけを読むため、追加 field を受理する。`tools/wave_land_window.py:856-884`
- 実装・書き込み・pytest 実走は行っていない。以下は静的確認に基づく段 2 プランである。

## 1. 終端性分類器

配置は `LandResult` と `as_json()` の直近とする。`tools/dev_wave_land.py:140-167`

- `RC_LOCK_BUSY` と `RC_CONTROL_PLANE` だけを入れた `_RETRYABLE_LAND_RCS` を rc 定数群の直後に置く。`tools/dev_wave_land.py:42-55`
- `LandResult.terminal` を「`self.rc not in _RETRYABLE_LAND_RCS`」で計算する。terminal 側の列挙ではなく、retryable の明示 allowlist とすることで未知 rc を必ず terminal に倒す。これは P1 の既定をコード構造で強制する。`brief.md:49-57`
- `as_json()` に `"terminal": self.terminal` を追加する。dataclass の保存 field は増やさず計算 property にすれば、既存の `LandResult(...)` 構築箇所と dataclass equality を変更せずに済む。`tools/dev_wave_land.py:140-167`
- 分類は status 文字列ではなく rc を権威にする。現在の一般 `_Reject` は最終的に `status="rejected"` へ畳まれるため、status だけでは rc=21 と rc=29を区別できない。`tools/dev_wave_land.py:3054-3062`

| 現行 rc | 現行 status / 経路 | 分類 | 根拠 |
|---:|---|---|---|
| 0 `RC_OK` | `landed` / `already-landed` | terminal | 成功経路。`tools/dev_wave_land.py:2403-2411,2526-2534,2620-2627,2861-2868,2955-2964` |
| 10 `RC_STALE_MAIN` | `stale-main` | terminal | 同じ tested main では再受入が必要という P2。`tools/dev_wave_land.py:1716-1726`; `brief.md:56-57` |
| 11 `RC_LOCK_BUSY` | `lock-busy` | retryable | 共通 lock の一時競合。`tools/dev_wave_land.py:2630-2648,2681-2687,2708-2714` |
| 20 `RC_DIRT` | `rejected` | terminal | P1 の「明示 retryable 以外」に含める。定数は `tools/dev_wave_land.py:45`、結果化は `tools/dev_wave_land.py:3054-3062` |
| 21 `RC_CONTROL_PLANE` | `rejected` | retryable | P1 の制御面 churn。実経路例は provenance 中の binding 変化と mutation 直前の変化。`tools/dev_wave_land.py:2715-2721,2998-3002` |
| 22 `RC_IDENTITY` | `rejected` | terminal | P1 の既定。`tools/dev_wave_land.py:47,3054-3062` |
| 23 `RC_AUDIT` | `rejected` | terminal | receipt/audit 不成立は同じ入力の再試行では直らない。`tools/dev_wave_land.py:48,486-520,3054-3062` |
| 24 `RC_NOT_LANDED` | `not-landed` | terminal | ff-only 実行後も tip に到達しなかった結果。`tools/dev_wave_land.py:2580-2587` |
| 25 `RC_LANDED_POSTCONDITION_FAILED` | `landed-postcondition-failed` | terminal | main が既に動いた可能性を含み、再試行させない。`tools/dev_wave_land.py:2546-2579,2611-2619` |
| 26 `RC_FOLD_FAILED` | `fold-failed` | terminal | rollback 後を含む fold 失敗。`tools/dev_wave_land.py:2326-2333,2412-2445` |
| 27 `RC_FOLD_RECOVERY_FAILED` | `fold-recovery-failed` | terminal | recovery には別の修復判断が必要。`tools/dev_wave_land.py:1690-1698,2781-2822` |
| 28 `RC_FOLD_ROLLBACK_FAILED` | `fold-rollback-failed` | terminal | 不完全 rollback を再 land で扱わない。`tools/dev_wave_land.py:2412-2445` |
| 29 `RC_PROVENANCE` | `rejected` | terminal | tip 自体の決定的違反。F2 は同一 tip で42回空転した。`tools/dev_wave_land.py:2733-2757,3054-3062`; `handoff.md:40-56,128-130` |
| 30 `RC_FOLD_FINALIZE_FAILED` | `fold-finalize-failed` | terminal | 検証済み fold commit 後の失敗を含む。`tools/dev_wave_land.py:2452-2464,2514-2525` |
| 未知の整数 rc | 任意 | terminal | retryable allowlist に不在なら自動的に terminal。`brief.md:51-55` |
| `land()` 内の予期しない例外 | 現状は JSON 無し | terminal | 現状は `_Reject` 以外が `main()` まで抜ける。`tools/dev_wave_land.py:3054-3065,3087-3099` |

例外を構造化するため、既存定数に意味を偽装せず `RC_INTERNAL=1` と `RC_INTERRUPTED=130` を `tools/dev_wave_land.py:42-55` に追加する。後者は待ち手の既存規約とも一致する。`tools/dev_wave_wait.py:215-217`。CLI の argparse rc=2 は `land()` の結果ではなく、holder 権限を確立できないため release 対象外とする。`tools/dev_wave_land.py:3068-3088`

## 2. release の呼び出し位置と I1〜I4

呼び出し位置は `main()` の `result = land(...)` と JSON print の間、現在の `tools/dev_wave_land.py:3087-3099` とする。

処理順は次の一方向に固定する。

1. 引数を parse し、receipt から release 用 holder 権限だけを読み取りで準備する。`tools/dev_wave_land.py:3068-3097`
2. `land()` を完走させ、通常結果または構造化した例外結果を得る。
3. `result.terminal` を確定する。
4. retryable なら lease を保持し、terminal かつ holder 権限成立時だけ `wave_land_window.release()` を呼ぶ。
5. `lease_release` を JSON payload に追加して一度だけ print し、常に元の `result.rc` を返す。`tools/dev_wave_land.py:3098-3099`

この配置による保証は以下のとおり。

- I1: `land()` の判定が返る前には release 呼び出しへ到達しない。また land lock は内側 `finally` で閉じ、repository も外側 `finally` で閉じてから `main()` へ戻る。`tools/dev_wave_land.py:3052-3065`
- I2: receipt の wave/holder 対応を release 権限として確認し、さらに `release()` 自身が現在の lease holder と再照合する。`tools/dev_wave_land.py:549-568`; `tools/wave_land_window.py:784-814`
- I3: release の戻り値や例外は `LandResult.rc/status/reason` に書き戻さない。`released`、`free`、`not-owner`、`unavailable` のいずれでも最後は元の land rc を返す。`tools/wave_land_window.py:784-817`; `tools/dev_wave_land.py:3098-3099`
- I4: 1回目が `released`、既に無ければ2回目は `free` となる現行挙動をそのまま利用する。`tools/wave_land_window.py:793-814`

`release()` は direct call すると構造化 dict を返す。一方、その CLI wrapper は `not-owner` や `unavailable` でも dict を出して rc=0 を返すため、subprocess rc だけを成功判定に使ってはならない。`tools/wave_land_window.py:946-965`。したがって `dev_wave_land.py` から関数を直接 import し、`state` と `source.reason` を記録する。

出力する `lease_release` は小さい固定形にする。

- retryable: `attempted=false / state=retained / reason=retryable-land-result`
- holder 未確認: `attempted=false / state=unavailable / reason=holder-unverified`
- lease dir 未解決: `attempted=false / state=unavailable / reason=lease-dir-required`
- direct call: `attempted=true` と、返却 dict の `state` および `source.reason`
- release 内部例外: `attempted=true / state=unavailable / reason=internal-error`

予期しない `land()` 例外も `main()` で terminal `LandResult` に変換してから同じ epilogue を通す。例外メッセージ全文は出さず型名だけを reason に含め、release 失敗が元の rc=1または130を上書きしない構造にする。`handoff.md:91-95`

`finish()` へ release を入れる案は採らない。`finish()` は acceptance verification の付加だけを担い、初期 lock-busy などは `finish()` を通らない経路もある。さらに land lock 内で sidecar release を行うことになる。`tools/dev_wave_land.py:2651-2661,2681-2687`

## 3. holder の求め方

release に渡す値は `request.acceptance_wave`、すなわち wave slug である。

- receipt 側は `sha256(acceptance_wave.encode("utf-8"))[:12]` を expected holder とし、`acceptance_wave` と `lease_holder` の両方を照合している。`tools/dev_wave_land.py:539-568`
- `wave_land_window.release(lease_dir, wave)` の第2引数名は `wave` で、関数冒頭で `_holder_for(wave)` を呼ぶ。`tools/wave_land_window.py:784-785`
- `_holder_for()` が wave slug を digest に変換する。`tools/wave_land_window.py:101-105`
- unlink 前に live lease の `lease.holder == self_holder` を要求する。`tools/wave_land_window.py:801-814`

したがって receipt の12文字 digest を `release()` へ渡してはならない。digest がもう一度 hash され、所有者不一致になる。

RC_PROVENANCE は acceptance receipt の完全検証より前に発生しうる。provenance は `tools/dev_wave_land.py:2701-2759`、receipt 検証は `tools/dev_wave_land.py:2761-2767` である。このため F2 を解消するには、release 権限確認を land 成功経路の `acceptance_verification` だけへ依存させてはいけない。

具体的には `tools/dev_wave_land.py:490-520` の安全な receipt 読み取りと duplicate-key/exact-object parserを再利用し、`main()` の land 前に次だけを確認する。

- receipt の `acceptance_wave == args.acceptance_wave`
- receipt の `lease_holder == sha256(args.acceptance_wave)[:12]`

これは release 権限の snapshot であり、受入 receipt の完全検証や land の rc を変更しない。完全検証は従来どおり `tools/dev_wave_land.py:539-681,2761-2767` に残す。snapshot が失敗しても land は従来どおり実行し、terminal 後の release だけを安全側で見送って JSON に記録する。

## 4. lease directory の解決

現状の land は lease dir を知らない。

- `LandRequest` に lease dir field は無い。`tools/dev_wave_land.py:128-137`
- CLI にも `--lease-dir` は無い。`tools/dev_wave_land.py:3068-3084`
- `dev_wave_land.py` 内に `IZANAGI_WAVE_LEASE_DIR` の参照は存在しない。
- 標準運用は同環境変数を export してから待ち手を起動する。`docs/pegasus-runbook.md:801-808`

択一は次のとおり。

| 案 | 実装・失敗様式 | 判断 |
|---|---|---|
| `IZANAGI_WAVE_LEASE_DIR` | `main()` の terminal 判定後に読む。未設定なら `lease-dir-required`、不在・権限不足・symlink 等なら `release()` が `directory-unavailable` を返す。いずれも land rc は維持する。`tools/wave_land_window.py:259-265,786-800,887-893` | 採用 |
| 新 `--lease-dir` | 明示的だが、parser、`_land_cli_argv`、全 land 呼び出し、runbook の同時更新が必要。required にすると既存 caller を壊し、optional にすると env との優先順位が増える。`tools/dev_wave_land.py:3068-3084`; `orchestrator/tests/test_dev_wave_land.py:329-341`; `docs/pegasus-runbook.md:1050-1055` | 本 wave では不採用 |
| receipt から導出 | 現行 v3 receipt の exact field 集合に lease dir は無い。未知 field は拒否される。receipt の親 directory は wave job dir で、共有 `land-lease/` ではない。`tools/dev_wave_land.py:68-94,510-520`; `brief.md:102-107` | 導出不能。schema/producer変更になるため不採用 |

環境変数が誤った既存 directory を指しても、live holder guard により別 holder の lease は `not-owner` になる。`tools/wave_land_window.py:801-805`。ただし同じ wave slug の別実行を区別する fencing token は現行にも無く、本 wave では変更しない。`handoff.md:103-108`; `brief.md:60-61`

runbook の「親が release」記述は実装後に事実と食い違うため、段4の裁定候補に残す。`docs/pegasus-runbook.md:1044-1048,1067-1069`; `brief.md:90-94`。TTL、heartbeat、FIFO、通知意味論の変更案は出さない。

## 5. 結果 JSON の後方互換

追加は次の2 fieldに限定する。

- `terminal: bool`: `LandResult.as_json()` が常に出す。`tools/dev_wave_land.py:152-167`
- `lease_release: object`: 実際に epilogue を実行した CLI `main()` が payload へ追加する。直接 `land()` を呼んだだけの `LandResult` に release 済みと誤記しない。`tools/dev_wave_land.py:3087-3099`

既存 field の名前・型・意味は変更しない。`brief.md:58-59`

確認できた consumer は以下のとおり。

- production consumer は `wave_land_window.message()` だけで、JSON object の exact key 集合を検査せず、`status` と `main_after` だけを読む。未知 field は無視される。`tools/wave_land_window.py:856-884`
- 運用例は stdout を `land-result.json` へ保存し、そのまま上記 message へ渡す。`docs/pegasus-runbook.md:1050-1056`
- `test_dev_wave_land.py` の直接 consumer は特定 key を lookup しており、exact key set 比較ではない。`orchestrator/tests/test_dev_wave_land.py:621-638,830-847,5627-5629`
- `test_wave_land_window.py` も `status` / `main_after` のみを作って message を検査する。`orchestrator/tests/test_wave_land_window.py:1712-1775`
- repo 内検索で land result 専用 schema 名は見つからなかった。`tools/dev_waves/schema_v2.json` 等の `fold_commit_sha` は別の supervised receipt schema であり、`LandResult` consumer ではない。
- `tools/dev_wave_wait.py:2618` の `as_json()` は環境 projection の別メソッドであり、land result consumer ではない。

repo 外の既存 job scriptも検索した。JSONを読むものは次の5本で、全て `status` だけを key lookup するため追加 field で壊れない。

- `/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/land-retry-loop.sh:124`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/finish2.sh:74`
- `/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/land-retry-loop.sh:121`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/land-retry.sh:23`
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/hold-and-land.sh:87`

t1142 の loop は JSON consumer ではなく shell rc を自前分類している。`/work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/land2-loop.sh:19-28`。新 field はこの履歴 artifactを書き換えないが、最初の rc=29 で lease 自体は自動解放される。

唯一の具体的な互換リスクは message 側の64 KiB上限である。`tools/wave_land_window.py:34,856-869`。`lease_release` は state/reasonだけの小さい固定 object とし、新しい実 CLI JSONを `message()` に渡す回帰テストを追加する。外部の未検索 ad-hoc byte比較 consumer は未確認であり、存在しないとは断定しない。

## 6. テスト設計

fixture は再利用できる。

- `_Repo` は temp repository と linked worktree を作る。`orchestrator/tests/test_dev_wave_land.py:92-170`
- `_acceptance_receipt()` は `acceptance_wave` と対応する `lease_holder` を既に作る。`orchestrator/tests/test_dev_wave_land.py:215-272`
- lease directory の作成方法は既存 E2E の `repo.root / "lease"` をそのまま使える。`orchestrator/tests/test_dev_wave_land.py:995-996`
- ただし既存 `_land()` は core `land()` だけを呼ぶため、新しい release epilogue は通らない。新テストは `LAND.main()` または `_land_cli_argv()` 経由にする。`orchestrator/tests/test_dev_wave_land.py:284-286,329-341`
- 既存 real waiter テストは未 claim の lease を waiter 自身が解放する形なので、そのままでは残留 lease 検査に使えない。新テストは canonical `wave_land_window.claim()` で先に lease を作ってから land を呼ぶ。`orchestrator/tests/test_dev_wave_land.py:975-1048`

追加位置は result JSON の既存検査直後 `orchestrator/tests/test_dev_wave_land.py:621-639` と、lease E2E の直後 `orchestrator/tests/test_dev_wave_land.py:975-1048` とする。

| 予定 node | 検出内容 |
|---|---|
| `test_land_result_terminality_uses_retryable_allowlist` | 全実在 rc と未知 rc を parametrizeし、11/21だけ `terminal=false`、他はtrue。`landed` と `already-landed` の双方も固定する。 |
| `test_main_does_not_release_before_land_returns` | fake `land()` 内から lease がまだ存在することを確認し、return 後だけ消えることを確認する。I1専用。 |
| `test_main_releases_owned_lease_after_land_success` | 実 repoで成功後に `acceptance.lease` が無い、JSONが `terminal=true` / `lease_release.state=released`、rc=0、mainがtipへ進んだことを確認する。純増検出力1。 |
| `test_main_releases_owned_lease_after_terminal_provenance_failure` | provenance seamを rc=29へ固定し、main不変、rc=29、lease消滅、`terminal=true` を確認する。純増検出力2。 |
| `test_main_never_releases_foreign_holder` | valid receiptの waveとは別waveでclaimし、land終端後もlease bytes/inodeが残り、`lease_release.state=not-owner` であることを確認する。純増検出力3。 |
| `test_terminal_rejection_with_unverified_receipt_holder_keeps_lease` | receipt holderを改変し、rc=23かつterminalでも release authority不成立として自 leaseを残す。receipt側I2を固定する。 |
| `test_main_retains_lease_for_retryable_result` | rc=11と21をparametrizeし、release未呼出し、lease残存、`state=retained` を確認する。 |
| `test_release_failure_never_overwrites_land_result` | env未設定、存在しないdir、release例外をparametrizeし、元の0/29/130が不変で `state=unavailable` がJSONに残ることを確認する。I3専用。 |
| `test_main_releases_after_unexpected_land_exception` | `land()` が `RuntimeError` / `KeyboardInterrupt` を送出しても rc=1/130、terminal JSON、lease解放になることを確認する。 |
| `test_second_explicit_release_after_land_is_free` | automatic release後に既存 `release()` をもう一度呼び、`state=free` を確認する。I4専用。 |
| `test_full_new_land_json_remains_message_compatible` | 新しい2 fieldを含む実stdoutを `wave_land_window.message()` に渡し、従来通知文が生成されることを固定する。 |

`tools/wave_land_window.py` 自体の既存安全性テストも維持する。特に non-owner 不削除は `orchestrator/tests/test_wave_land_window.py:1235-1244`、lease不在の冪等 free は `orchestrator/tests/test_wave_land_window.py:892-906` に既存被覆がある。

## 7. 変異事前登録候補

| 変異 | KILLする予定 node |
|---|---|
| M0: automatic release 呼び出しを丸ごと削除する。wave前コードそのもの。 | `test_main_releases_owned_lease_after_land_success`; `test_main_releases_owned_lease_after_terminal_provenance_failure` |
| M1: rc=29を retryable allowlistへ入れる。 | `test_land_result_terminality_uses_retryable_allowlist[29]`; `test_main_releases_owned_lease_after_terminal_provenance_failure` |
| M2: rc=10を retryableへ反転する。 | `test_land_result_terminality_uses_retryable_allowlist[10]` |
| M3: rc=11または21を terminalへ反転する。 | `test_land_result_terminality_uses_retryable_allowlist[11/21]`; `test_main_retains_lease_for_retryable_result` |
| M4: 未知 rc の既定を retryableへ反転する、または terminal rc の denylist方式へ変える。 | `test_land_result_terminality_uses_retryable_allowlist[unknown]` |
| M5: terminal 判定より前に release を移動する。 | `test_main_does_not_release_before_land_returns` |
| M6: `release()` へ wave slugでなく holder digestを渡す。 | `test_main_releases_owned_lease_after_land_success` |
| M7: receipt の `acceptance_wave` / `lease_holder` release権限照合を外す。 | `test_terminal_rejection_with_unverified_receipt_holder_keeps_lease` |
| M8: `wave_land_window.release()` の `lease.holder != self_holder` guardを外す。`tools/wave_land_window.py:802-805` | `test_main_never_releases_foreign_holder`; 既存 `test_non_owner_release_never_removes_lease` |
| M9: release失敗時に rcを2または0へ上書きする、あるいは例外を再送出する。 | `test_release_failure_never_overwrites_land_result` |
| M10: release対象を rc=0だけに狭める。 | `test_main_releases_owned_lease_after_terminal_provenance_failure` |
| M11: retryableでも無条件に releaseする。 | `test_main_retains_lease_for_retryable_result` |
| M12: 予期しない例外経路から epilogueを外す。 | `test_main_releases_after_unexpected_land_exception` |
| M13: `free` を失敗扱いにする、または二度目のreleaseで例外にする。 | `test_second_explicit_release_after_land_is_free`; 既存 `test_release_without_lease_drops_own_ticket` |
| M14: `terminal` fieldまたは `lease_release` fieldをJSONから削除する。 | `test_land_result_terminality_uses_retryable_allowlist`; 各CLI JSON検査 node |

変更対象外は `tools/dev_wave_wait.py`、`tools/check_acceptance_reds.py`、`docs/dev-wave/**` とする。`brief.md:70-74,90-94`。受理条件、全史 provenance、ff-only、fold、lock、TTL、FIFO、通知の意味論を変更する案は含めない。