## 総括

- 判定は **blocker**。この差分を現状のまま land してはならない。
- provenance の全非 0 rc を決定的拒否としており、実測済みの infra rc=16 と signal 終了の負 rc でも lease を解放する。
- fold / fold preflight 内の `KeyboardInterrupt` が `release_safe=True` に変換され、JSON 出力後に release される経路がある。
- rollback 成功判定は最終 ref SHA しか再観測せず、index・worktree・journal・symbolic ref の完了を検証していない。
- receipt 読取の一時 I/O 失敗は `(True, False)` となり、直後の再読成功で lease が解放される。同じ request で回復可能という述語に反する。
- receipt digest、compare-and-delete、stdout flush 順序、既存 caller 互換、land の受理集合不変は成立した。
- M0、M4、M5 は検出できる。一方 M3 は実制御流を通らず、M6 の expected node 集合は不完全、M12 は片側の分岐しか固定していない。
- pytest は制約どおり未実行。I/O seam による `release()` と main epilogue の独立実行だけ行った。

## Must-fix 1 — infra rc と signal 終了を「決定的非 0」と誤認する

根拠は [tools/dev_wave_land.py:1998](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1998) と [tools/check_ai_provenance.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/check_ai_provenance.py:38)。`receipt.returncode != 0` の全値が `(True, False)` になる。

成立順序:

1. provenance checker が dispatch infra failure で rc=16を返す。または子が SIGKILL / SIGTERM で終了し、`CompletedProcess.returncode` が `-9` / `-15` になる。
2. `_verify_provenance_receipt()` はいずれも「checker が決定的に拒否した」として `release_safe=True` を立てる。
3. result には完全 receipt digest がないため、epilogue が receipt を再読する。
4. digest が不変なら `release()` が走る。

I/O seam 実行でも rc `1, 16, -9, -15` のすべてが `(True, False)` になった。handoff が明記する「rc=16 は測れなかっただけ」と矛盾する。新テストは rc=1 と timeout しか扱っていない。[test_dev_wave_land.py:6018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6018)

**成果物影響:** 有効な監査結果がない wave の lease が消え、別 wave の受入が開始される。元 wave の retry は lease 外となり、receipt の `tested_main` 参照と受入試行集合が stale になり、レポート・試行台帳の完全性が変わる。

## Must-fix 2 — 内部の中断が release-safe 結果へ変換される

根拠は以下。

- fold 本体: [tools/dev_wave_land.py:2482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2482)
- fold rollback 成功後の宣言: [tools/dev_wave_land.py:2508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2508)
- plan 失敗: [tools/dev_wave_land.py:2991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2991)
- snapshot 失敗: [tools/dev_wave_land.py:3054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3054)、[tools/dev_wave_land.py:3097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3097)

成立順序:

1. `apply_fold()`、rollback 前後、plan、snapshot のいずれかで `KeyboardInterrupt` が発生する。
2. 各 `except (Exception, KeyboardInterrupt)` が中断を伝播させず、通常の `LandResult` に変換する。
3. plan / snapshot は即 `release_safe=True`。fold 本体も rollback が空リストなら `release_safe=True`。
4. `main()` は JSON を print/flush し、receipt 条件成立後に lease を解放する。

`test_main_unexpected_exception_or_interrupt_never_releases` は [test_dev_wave_land.py:5972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:5972) で `land()` 自体を mock しているため、これらの内部 catch を一度も通らない。

外側 `land()` から直接伝播する `RuntimeError`、`KeyboardInterrupt`、`SystemExit` は、独立 seam 実行で JSON なし・stderr なし・release なしを確認した。一方、provenance 内の `BaseException` は rc=29へ畳まれて JSON が出るため、「すべての中断で JSON も出ない」という性質自体は成立していない。新 rc 定数は追加されていない。

**成果物影響:** fold 中断後に排他が外れ、次 wave が不完全な canonical 台帳状態を基準に受入を始めうる。worklog・decisions・failures の値と fold commit、certified レポートが参照する main SHA の対応が崩れる。

## Must-fix 3 — rollback 成功判定が4状態を再検証していない

根拠は [tools/dev_wave_land.py:2211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2211) と [tools/dev_wave_land.py:2515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2515)。

現在の判定は次のとおり。

| 状態 | 操作 | 最終再検証 |
|---|---|---|
| main ref SHA | `update-ref` | `main_after == rollback_ref` のみあり |
| symbolic HEAD / main ref binding | 操作なし | なし |
| index | `read-tree --reset -u` の rc | tree 一致検証なし |
| worktree | snapshot を復元 | clean・bytes・mode の最終検証なし |
| journal | `unlink` と親 directory fsync | 最終不在・inode の再検証なし |

成立順序:

1. fold が失敗する。
2. rollback 操作が rc=0を返すが、index/worktree の一部が期待状態でない、または journal が競合で再出現する。
3. `failures` は空のままになる。
4. main HEAD だけが `rollback_ref` と一致する。
5. `(True, False)` が返り、lease が解放される。

これはユーザー指定の「ref・index・worktree・journal のすべてを見る」を満たさない。

**成果物影響:** main ref だけ戻り canonical bytes・index・journal が食い違った状態に別 wave が重なり、台帳内容と fold transaction ID、後続 certified レポートが参照する commit の対応が変わる。

## Must-fix 4 — receipt の一時 I/O 失敗を非 retryable として解放する

根拠は [tools/dev_wave_land.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:504)、[tools/dev_wave_land.py:2842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2842)、[tools/dev_wave_land.py:3153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3153)、[tools/dev_wave_land.py:3221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3221)。

成立順序:

1. land 前の authority snapshot は成功する。
2. active plan がないため `quiescent_rejection=True` になる。
3. 完全 receipt 検証時だけ一時的な open/read/stat failure が発生する。
4. `_read_acceptance_receipt()` は原因を `RC_AUDIT` の `_Reject(False, False)` へ畳む。
5. outer handler がこれを `(True, False)` に変更する。
6. epilogue の再読は成功し、snapshot digest と一致する。
7. 同じ request が再試行可能なのに release が走る。

receipt が不成立でも mutation 前なので `release_safe=True` 自体は成立しうる。しかし一時 I/O failure まで `retryable_same_request=False` とするのは述語の定義と合わない。locked preflight 内の Git/status I/O `_Reject` にも同じ一般化がある。

**成果物影響:** そのまま再試行できた wave が lease を失い、旧 caller は lease 外で同じ receipt を使う。並行 wave の receipt を stale にし、レポートの有効 receipt 集合と試行台帳の試行数が変わる。

## Must-fix 5 — rc=21 の一経路が終端でも retryable でもないまま残る

根拠は [tools/dev_wave_land.py:2793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2793) と [tools/dev_wave_land.py:3145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3145)。

provenance 後の control snapshot 変更は、`quiescent_rejection` を設定する前に `RC_CONTROL_PLANE` を投げるため `(False, False)` になる。既存テストもこの値を固定している。[test_dev_wave_land.py:2406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:2406)

成立順序:

1. provenance 中に handoff/worktree control snapshot が変わる。
2. lock 再取得後、rc=21 `(False, False)` で返る。
3. release 条件を満たさず、同一 request の retryable 宣言もない。
4. status-only loop または再 claim が続けば lease 保持が更新され、B-3 の無期限占有を再現できる。

active transaction が増えた可能性をまだ再検査していないので、現在位置で単純に `release_safe=True` にするのも危険である。active plan を再観測してから分類する必要がある。

**成果物影響:** 後続 wave の受入試行が台帳へ追加されず、certified 選択とレポートの完了集合が無期限に欠落しうる。

## Must-fix 6 — 変異対応表が実制御流を固定していない

判定は次のとおり。

| 変異 | 判定 |
|---|---|
| M0 | KILL する。成功 node は実 lease の消失を要求し、release 全削除で落ちる |
| M1 | KILL する。既定値を直接固定 |
| M2 | KILL する。両 bool=True の synthetic result で release 呼出しを禁止 |
| M3 | **SURVIVE しうる**。mock `land()` の伝播しか見ず、内部 catch を通らない |
| M4 | KILL する。rc=28 の tuple だけが変わるため単一理由 |
| M5 | KILL する。rc=30 の tuple だけが変わるため単一理由 |
| M6 | **対応表不完全**。foreign-handoff node は代表変異を殺すが、global rc=21 変異なら post-provenance node も失敗する |
| M7 | KILL する。timeout 側を実行 |
| M8 | KILL する。checker rc=1 側を実行 |
| M9 | KILL する。wave slug を直接検査 |
| M10 | KILL する。既存 foreign-holder node が unlink 不在を固定 |
| M11 | KILL する。同一 slug・異なる main を実 lease で固定 |
| M12 | **部分的**。digest 未到達後の再読だけ。完全検証 digest と事前 snapshot の不一致分岐は未固定 |
| M13 | KILL する。release seam 内で stdout flush 済みを検査 |
| M14 | KILL する。release 例外後も元 rc を固定 |
| M15 | KILL する。JSON の両 field を固定 |

M6 の author 対応は完全な誤りではない。`test_foreign_handoff_of_any_shape_is_protected_from_target_collision` は `(True, False)` を期待するため、中央で rc=21 を retryable に戻す変異を殺す。ただし `DW-M08` の expected node は完全集合なので、`test_post_provenance_reacquire_rejects_control_directory_replacement` も含める必要がある。単一 anchor が未定義なら `DW-M04` 上も実行不能である。

M4/M5 は既存 node の他 assertion が変異後も同じで、追加された tuple assertion だけが落ちる。過剰決定は成立しなかった。

**成果物影響:** M3、M12片側、infra/signal、rollback false-success が生存すると、変異 matrix は KILLED を誤記し、監査済み成果物として land されたコードが stale receipt・不完全 fold 台帳を許す。

## Should-fix — rc=24 / rc=25 の保持終端

[tools/dev_wave_land.py:2622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2622) では rc=25、[tools/dev_wave_land.py:2655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2655) では rc=24 がともに `(False, False)`。

- rc=25 は mutation outcome 不明を含むため保持が正しい。自動 recovery はなく、手動介入または TTL が必要。
- rc=24 は main SHA 不変かつ tracked/index dirt なしまで確認しているため、追加 postcondition を満たせば release-safe にできる余地がある。
- どちらも lease 自体に TTL があるため「必ず永久」ではない。ただし caller が `held-self` claim を繰り返せば更新され、無期限化できる。

**成果物影響:** 値の誤採用より可用性の問題だが、後続の受入試行が欠落し、certified 選択・レポート・台帳の完了時刻と完了集合が変わる。

## 19 到達点の独立判定

| # | 到達点 | 判定 |
|---:|---|---|
| 1 | fold state 読取失敗 | `(False, True)`。active state 不明を保持。成立 |
| 2 | locked preflight 拒否 | active plan 無しなら `(True, False)`。一時 I/O の retryability 欠落あり |
| 3 | stale-main | `(True, False)`。merge 前・active plan 無し。成立 |
| 4 | checker 完走非 0 | rc=1 は成立。rc=16・負 rc まで含めるため不成立 |
| 5 | provenance timeout・例外・binding | `(False, True)`。通常 exception は成立 |
| 6 | successful land に `main_after` 無し | 既定 `(False, False)`。fail-closed |
| 7 | fold 成功 | postcondition 後・finalize 後のみ `(True, False)`。成立 |
| 8 | fold 失敗・rollback 成功 | ref 以外の完了再検証なし。中断も含む。不成立 |
| 9 | rollback 不完了 rc=28 | `(False, False)`。成立 |
| 10 | finalize 失敗 rc=30 | `(False, True)`。journal を保持。成立 |
| 11 | active recovery 失敗 rc=27 | `(False, True)`。成立 |
| 12 | active recovery 成功 | postcondition・finalize 後 `(True, False)`。成立 |
| 13 | merge postcondition 失敗 rc=25 | `(False, False)`。安全側だが手動 recovery 必須 |
| 14 | not-landed rc=24 | `(False, False)`。安全側だが保持時間の穴あり |
| 15 | 通常 land 成功 | full postcondition 後 `(True, False)`。成立 |
| 16 | lock-busy | lock 未取得で `(False, True)`。成立 |
| 17 | active transaction preflight 失敗 | `(False, True)`。open journal を保持。成立 |
| 18 | fold 計画・no-fold・snapshot 失敗 | merge 前。ただし `KeyboardInterrupt` まで release-safe にするため一部不成立 |
| 19 | already-landed no-op | receipt 完全検証後・active plan 無しで `(True, False)`。成立 |

catch-all `_Reject` は別枠。`quiescent_rejection` と exception の retry flag に依存しており、rc=23一時 I/O と post-provenance rc=21 の誤分類源になっている。

## 成立しなかった攻撃

- receipt digest 束縛の実装自体は成立した。完全検証到達時は result digest と snapshot を比較し、未到達時は release 直前に再読して不変を確認する。[tools/dev_wave_land.py:3214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3214)
- compare-and-delete は成立した。I/O seam 実行結果は以下だった。

  - `expected_main_sha=None`: 旧挙動どおり unlink 1回
  - 同一 slug・異なる main: `not-owner`、unlink 0回
  - 同一 slug・同じ main: `released`、unlink 1回
  - 異なる slug: `not-owner`、unlink 0回

- CLI wrapper、`dev_wave_wait.py::_release_once`、test helper はいずれも optional 引数を渡さず、旧挙動のまま。[wave_land_window.py:969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/wave_land_window.py:969)、[dev_wave_wait.py:2333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_wait.py:2333)
- core JSON は release 前に `flush=True` で出力される。`lease_release` は JSON に入らず、結果は stderr 1行。[tools/dev_wave_land.py:3202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3202)
- active plan が明確に open の recovery/finalize failure はすべて保持される。rollback false-success を除き、明示的 open transaction から `release_safe=True` へ落ちる点は見つからなかった。
- land の acceptance receipt、audit closure、ff-only、fold postcondition の gate は変更されていない。受理・拒否集合の 1 bit 変更とリワードハックは成立しなかった。

## 既存テスト期待値の変更

既存 node への変更は次の23件。すべて bool assertion の追加、または新 field を含めるための dataclass equality 拡張で、既存 assertion の削除・反転・緩和はない。

`test_colliding_untracked_rejected_without_main_or_foreign_artifact_change`、`test_noncolliding_foreign_session_untracked_does_not_block_land`、`test_foreign_handoff_of_any_shape_is_protected_from_target_collision`、`test_common_lock_timeout_does_not_start_provenance_checker`、`test_provenance_gate_rejects_tip_nonzero_before_ff`、`test_post_provenance_reacquire_rejects_control_directory_replacement`、`test_waited_initial_lock_rechecks_main_and_reports_stale`、`test_provenance_audit_detects_removed_ignored_collision`、`test_provenance_receipt_rejects_each_bound_field`、`test_provenance_audit_rejects_executed_bytes_mismatch`、`test_provenance_subprocess_contract_and_exception_mapping`、`test_zero_fragment_preserves_land_result_and_commit_graph_bit_for_bit`、`test_zero_fragment_still_rejects_missing_spool_layout_before_ff`、`test_candidate_fold_plan_failure_happens_before_ff`、`test_finalize_failure_keeps_verified_fold_commit_and_never_rolls_back`、`test_n35_supervised_branch_rejects_fragment_from_another_slug_before_ff`、`test_fold_failure_rolls_back_ff_and_never_returns_landed`、`test_fold_rollback_failure_reason_reports_preserved_state`、`test_active_transaction_recovery_completes_with_provenance_red`、`test_shape_b_finalizes_without_reapply_recommit_or_provenance_audit`、`test_shape_b_rejects_active_origin_from_different_existing_wave_ref`、`test_not_landed_is_distinct_from_postcondition_failure`、`test_partial_merge_mutation_is_nonretryable_postcondition_failure`。

`_claim_acceptance_lease()` が request の現行 `tested_main_sha` を使うのは新規正例の lease を一致させるためで、既存 fixture の期待値変更ではない。異なる main の負例は固定 SHA A/B を使う別 node がある。揮発 payload の焼き込み、skip、xfail、assert 緩和は見つからなかった。

## 分類一覧

must-fix:

- provenance rc=16・signal returncode の決定的拒否誤分類
- fold / preflight 内 `KeyboardInterrupt` の release-safe 化
- rollback の index・worktree・journal・symbolic ref 最終検証欠落
- receipt 一時 I/O failure の非 retryable 誤分類
- post-provenance rc=21 の無期限保持経路
- M3 / M6 / M12 を中心とする変異 matrix の検出力不足

should-fix:

- rc=24 の release-safe 再評価と、rc=24/25 の recovery・保持終端の明文化

nit:

- `expected_main_sha` 不一致時に state が `not-owner` なのに `holder_self=True` になる。安全性は壊さないが、stderr telemetry の語義が紛らわしい。